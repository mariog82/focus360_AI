import os, csv, io, secrets, string, hashlib, json, random, smtplib
from datetime import datetime, timedelta, date
from functools import wraps
from urllib.parse import urlparse, quote

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-me')
raw_db = os.environ.get('DATABASE_URL', 'sqlite:///focus360_ai.db')
if raw_db.startswith('postgres://'):
    raw_db = raw_db.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = raw_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

APP_NAME = 'Focus360 AI'
PLANS = {
    'BASE': {
        'name':'Pacchetto Base',
        'modules':'QR docente, Focus Mode studente, dashboard docente/dirigente, upload CSV docenti/studenti, credenziali, report CSV base, gamification essenziale.',
        'price':'€ 1.200/anno + IVA',
        'features':['qr','dashboard','csv','report_csv','gamification_base']
    },
    'PRO': {
        'name':'Pacchetto Pro',
        'modules':'Tutto Base + AI Analytics, Digital Wellness Score, Educational Passport, gamification completa, ranking classi, report famiglie, piani di intervento.',
        'price':'€ 2.900/anno + IVA',
        'features':['qr','dashboard','csv','report_csv','gamification_base','ai','gamification','wellbeing','ranking','passport','interventi','report_famiglie']
    },
    'ENTERPRISE': {
        'name':'Enterprise/PNRR',
        'modules':'Tutto Pro + multi-plesso, blockchain badge, report ministeriali, Smart Locker/Phone Box, API integrazioni e connettore Registro elettronico in modalità Alpha.',
        'price':'€ 6.900/anno + IVA; hardware e integrazioni da preventivare',
        'features':['qr','dashboard','csv','report_csv','gamification_base','ai','gamification','wellbeing','ranking','passport','interventi','report_famiglie','blockchain','lockers','api','registro','ministeriale','multi_plesso','supporto_prioritario']
    }
}
ROLES = ['superadmin','dirigente','docente','studente','genitore']
BANNED_APPS = ['Instagram','TikTok','WhatsApp','Giochi','Browser non autorizzato']

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    codice_meccanografico = db.Column(db.String(30))
    city = db.Column(db.String(120))
    address = db.Column(db.String(220))
    fiscal_code = db.Column(db.String(50))
    pec = db.Column(db.String(120))
    billing_email = db.Column(db.String(120))
    plan = db.Column(db.String(20), default='BASE')
    license_start = db.Column(db.Date, default=date.today)
    license_end = db.Column(db.Date, default=lambda: date.today()+timedelta(days=365))
    payment_status = db.Column(db.String(30), default='in_attesa')
    payment_method = db.Column(db.String(60), default='bonifico')
    active = db.Column(db.Boolean, default=True)
    tenant_slug = db.Column(db.String(80))
    notes = db.Column(db.Text)
    modules_enabled = db.Column(db.Text, default='')  # CSV features abilitate/override dal SuperAdmin
    modules_disabled = db.Column(db.Text, default='')  # moduli disabilitati dal SuperAdmin, es. api,registro
    smart_locker_enabled = db.Column(db.Boolean, default=True)
    last_expiry_notice_at = db.Column(db.DateTime, nullable=True)

class Plesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(180), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(120))
    address = db.Column(db.String(220))
    referent = db.Column(db.String(160))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(60))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    school = db.relationship('School', backref='plessi')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    plesso_id = db.Column(db.Integer, db.ForeignKey('plesso.id'), nullable=True)
    parent_student_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(20), nullable=False)
    surname = db.Column(db.String(80))
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(60))
    password_hash = db.Column(db.String(255), nullable=False)
    discipline = db.Column(db.String(120))
    class_name = db.Column(db.String(60))
    birthdate = db.Column(db.String(20))
    active = db.Column(db.Boolean, default=True)
    temporary_password = db.Column(db.String(80))  # solo prototipo/demo: in produzione mostrarla una sola volta e poi cancellarla
    must_change_password = db.Column(db.Boolean, default=True)
    school = db.relationship('School', backref='users')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    plesso_id = db.Column(db.Integer, db.ForeignKey('plesso.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_name = db.Column(db.String(60), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer, default=60)
    qr_token_hash = db.Column(db.String(128), nullable=False)
    qr_expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='attiva')

class FocusRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    minutes_focus = db.Column(db.Integer, default=0)
    focus_active = db.Column(db.Boolean, default=True)
    violations = db.Column(db.Integer, default=0)
    opened_social = db.Column(db.Integer, default=0)
    exited_app = db.Column(db.Integer, default=0)
    screen_minutes = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(128))
    lesson = db.relationship('Lesson', backref='records')
    student = db.relationship('User')

class WellbeingSurvey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stress_level = db.Column(db.Integer, default=3)
    perceived_attention = db.Column(db.Integer, default=3)
    sleep_quality = db.Column(db.Integer, default=3)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User')

class SmartLocker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    class_name = db.Column(db.String(60))
    box_code = db.Column(db.String(40))
    status = db.Column(db.String(30), default='libero')
    last_student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User')

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    class_name = db.Column(db.String(60))
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    nft_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PortfolioItem(db.Model):
    """Elementi del Focus360 AI Educational Passport: competenze, PCTO, educazione civica, badge validati."""
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(80), default='Digital Citizenship')
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    hours = db.Column(db.Float, default=0)
    score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(40), default='validato')
    validator = db.Column(db.String(160))
    evidence_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User')

class BlockchainEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer)
    event_type = db.Column(db.String(60))
    payload = db.Column(db.Text)
    previous_hash = db.Column(db.String(128))
    current_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PaymentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    invoice_number = db.Column(db.String(40))
    amount = db.Column(db.Float, default=0)
    method = db.Column(db.String(60), default='bonifico')
    status = db.Column(db.String(30), default='in_attesa')
    due_date = db.Column(db.Date)
    paid_at = db.Column(db.DateTime)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    school = db.relationship('School')

class ParentConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    consent_focus = db.Column(db.Boolean, default=True)
    consent_analytics = db.Column(db.Boolean, default=True)
    consent_badge = db.Column(db.Boolean, default=True)
    signed_by = db.Column(db.String(160))
    signed_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User')

class DeviceEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    event_type = db.Column(db.String(80))
    value = db.Column(db.String(160))
    risk_weight = db.Column(db.Integer, default=0)
    source = db.Column(db.String(80), default='web_prototype')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User')
    lesson = db.relationship('Lesson')

class InterventionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer)
    class_name = db.Column(db.String(60))
    title = db.Column(db.String(180))
    owner = db.Column(db.String(120))
    status = db.Column(db.String(40), default='aperto')
    action = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RegistroIntegration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    provider = db.Column(db.String(80), default='Argo/Spaggiari/Axios/Nuvola')
    endpoint_url = db.Column(db.String(255))
    api_key_hint = db.Column(db.String(120))
    sync_students = db.Column(db.Boolean, default=True)
    sync_teachers = db.Column(db.Boolean, default=True)
    sync_lessons = db.Column(db.Boolean, default=True)
    sync_focus_reports = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(40), default='configurazione')
    last_sync_at = db.Column(db.DateTime)
    note = db.Column(db.Text)
    school = db.relationship('School')


def current_user():
    uid = session.get('uid')
    return User.query.get(uid) if uid else None

@app.context_processor
def inject_user():
    return {'me': current_user(), 'plans': PLANS, 'APP_NAME': APP_NAME, 'plan_enabled': plan_enabled if 'plan_enabled' in globals() else None, 'module_matrix_for_school': module_matrix_for_school if 'module_matrix_for_school' in globals() else None, 'today': date.today()}

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            me=current_user()
            if not me: return redirect(url_for('login'))
            allowed = [role] if isinstance(role,str) else role
            if allowed and me.role not in allowed:
                flash('Accesso non autorizzato','danger'); return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return wrapper
    return deco

def random_password(n=10):
    alphabet=string.ascii_letters+string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))

def sha(data): return hashlib.sha256(data.encode()).hexdigest()

def write_chain(school_id, event_type, payload):
    last = BlockchainEvent.query.order_by(BlockchainEvent.id.desc()).first()
    prev = last.current_hash if last else 'GENESIS'
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)+prev+datetime.utcnow().isoformat()
    ev = BlockchainEvent(school_id=school_id, event_type=event_type, payload=json.dumps(payload, ensure_ascii=False), previous_hash=prev, current_hash=sha(raw))
    db.session.add(ev); db.session.commit(); return ev.current_hash

def calc_points(minutes, duration, exited, social, screen):
    p = 0
    if minutes >= duration: p += 10
    if exited == 0 and social == 0: p += 5
    p -= exited*15
    p -= social*25
    if screen > duration*0.25: p -= 10
    return max(p, -50)



def focus_risk_score(records):
    """AI prototipo: stima rischio distrazione 0-100 da violazioni, screen time e continuità focus."""
    if not records:
        return 0
    n=len(records)
    violations=sum(r.violations for r in records)
    screen=sum(r.screen_minutes for r in records)
    minutes=sum(r.minutes_focus for r in records)
    expected=sum(r.lesson.duration_minutes for r in records if r.lesson) or 1
    focus_ratio=minutes/expected
    raw=(violations*18)+(screen/max(1,n)*0.8)+((1-focus_ratio)*60)
    return int(max(0,min(100,raw)))

def attention_index(records):
    if not records: return 0
    good=sum(1 for r in records if r.focus_active)
    avg_points=sum(r.points for r in records)/max(1,len(records))
    return round(max(0,min(100,(good/len(records))*75 + max(0,avg_points)*2)),1)


def digital_wellness_score(records, surveys=None, citizenship_items=None):
    """Calcola il Digital Wellness Score 0-100 con componenti trasparenti.
    Non è una diagnosi: è un indicatore educativo per benessere digitale, attenzione e cittadinanza digitale.
    """
    surveys = surveys or []
    citizenship_items = citizenship_items or []
    if not records:
        components = {
            'focus_continuity': 0,
            'digital_discipline': 100,
            'consistency': 0,
            'collaborative_focus': 0,
            'digital_citizenship': min(100, len(citizenship_items)*12)
        }
    else:
        expected = sum((r.lesson.duration_minutes if r.lesson else 60) for r in records) or 1
        focus_minutes = sum(r.minutes_focus for r in records)
        focus_continuity = min(100, round((focus_minutes/expected)*100, 1))
        violations = sum(r.violations for r in records)
        social = sum(r.opened_social for r in records)
        exits = sum(r.exited_app for r in records)
        digital_discipline = max(0, 100 - violations*12 - social*8 - exits*6)
        active_days = len({r.created_at.date() for r in records})
        consistency = min(100, active_days*12)
        # stima del contributo al focus collettivo: punti positivi + assenza violazioni
        positive = sum(1 for r in records if r.points > 0 and r.violations == 0)
        collaborative_focus = round((positive/max(1,len(records)))*100, 1)
        digital_citizenship = min(100, 20 + len(citizenship_items)*12 + sum(1 for r in records if r.tokens)*2)
    if surveys:
        avg_attention = sum(s.perceived_attention for s in surveys)/len(surveys)
        avg_sleep = sum(s.sleep_quality for s in surveys)/len(surveys)
        avg_stress = sum(s.stress_level for s in surveys)/len(surveys)
        wellbeing_adjustment = ((avg_attention + avg_sleep + (6-avg_stress))/15)*10 - 5
    else:
        wellbeing_adjustment = 0
    components = locals().get('components') or {
        'focus_continuity': focus_continuity,
        'digital_discipline': digital_discipline,
        'consistency': consistency,
        'collaborative_focus': collaborative_focus,
        'digital_citizenship': digital_citizenship
    }
    score = (
        components['focus_continuity']*0.30 +
        components['digital_discipline']*0.25 +
        components['consistency']*0.15 +
        components['collaborative_focus']*0.15 +
        components['digital_citizenship']*0.15 + wellbeing_adjustment
    )
    score = int(max(0, min(100, round(score))))
    if score < 40: level='Critico'
    elif score < 60: level='Da migliorare'
    elif score < 80: level='Buono'
    else: level='Eccellente'
    return {'score': score, 'level': level, 'components': components, 'adjustment': round(wellbeing_adjustment,1)}

def educational_passport(student):
    records = FocusRecord.query.filter_by(student_id=student.id).all()
    badges = Badge.query.filter_by(user_id=student.id).all()
    surveys = WellbeingSurvey.query.filter_by(student_id=student.id).all()
    items = PortfolioItem.query.filter_by(student_id=student.id).order_by(PortfolioItem.created_at.desc()).all()
    wellness = digital_wellness_score(records, surveys, items)
    total_focus_hours = round(sum(r.minutes_focus for r in records)/60, 1)
    total_tokens = sum(r.tokens for r in records)
    categories = {}
    for it in items:
        categories.setdefault(it.category, {'count':0,'hours':0,'score':0})
        categories[it.category]['count'] += 1
        categories[it.category]['hours'] += it.hours or 0
        categories[it.category]['score'] += it.score or 0
    payload = {
        'student': student.email,
        'focus_hours': total_focus_hours,
        'tokens': total_tokens,
        'badges': [b.name for b in badges],
        'wellness_score': wellness['score'],
        'items': [i.title for i in items],
    }
    passport_hash = sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return {'student':student,'records':records,'badges':badges,'items':items,'wellness':wellness,'focus_hours':total_focus_hours,'tokens':total_tokens,'categories':categories,'passport_hash':passport_hash}


def pdf_escape(txt):
    return str(txt).replace('\\','\\\\').replace('(','\\(').replace(')','\\)')

def simple_passport_pdf(data):
    """Genera un PDF minimale senza dipendenze esterne, adatto a Render."""
    st=data['student']
    lines=[
        'FOCUS360 AI - EDUCATIONAL PASSPORT',
        f"Studente: {st.surname} {st.name}",
        f"Classe: {st.class_name or ''}",
        f"Email: {st.email}",
        f"Digital Wellness Score: {data['wellness']['score']}/100 - {data['wellness']['level']}",
        f"Ore Focus certificate: {data['focus_hours']}",
        f"FocusToken: {data['tokens']}",
        f"Hash Passport: {data['passport_hash']}",
        '', 'BADGE:'
    ]
    lines += [f"- {b.name}" for b in data['badges']] or ['- Nessun badge']
    lines += ['', 'COMPETENZE E PORTFOLIO:']
    for it in data['items'][:30]:
        lines.append(f"- {it.category}: {it.title} | ore {it.hours} | score {it.score} | validatore {it.validator or ''}")
        if it.evidence_hash:
            lines.append(f"  hash evidenza: {it.evidence_hash[:32]}...")
    lines += ['', 'Documento dimostrativo generato da Focus360 AI Enterprise.']
    content=['BT','/F1 12 Tf','50 790 Td']
    first=True
    for line in lines:
        if first:
            first=False
        else:
            content.append('0 -18 Td')
        content.append(f"({pdf_escape(line[:95])}) Tj")
    content.append('ET')
    stream='\n'.join(content).encode('latin-1','replace')
    objects=[]
    objects.append(b'1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n')
    objects.append(b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n')
    objects.append(b'3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n')
    objects.append(b'4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n')
    objects.append(f'5 0 obj << /Length {len(stream)} >> stream\n'.encode()+stream+b'\nendstream endobj\n')
    pdf=b'%PDF-1.4\n'
    offsets=[0]
    for obj in objects:
        offsets.append(len(pdf)); pdf+=obj
    xref=len(pdf)
    pdf+=f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
    for off in offsets[1:]:
        pdf+=f'{off:010d} 00000 n \n'.encode()
    pdf+=f'trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
    return pdf

def default_features_for_plan(plan):
    return set(PLANS.get(plan or 'BASE', PLANS['BASE']).get('features', []))

ENTERPRISE_ONLY_TOGGLES = {'lockers', 'api', 'registro'}
HARD_DISABLED_MODULES = set()
ALLOWED_MODULES = {'qr','dashboard','csv','report_csv','gamification_base','ai','gamification','wellbeing','ranking','passport','interventi','report_famiglie','blockchain','lockers','api','registro','ministeriale','multi_plesso','supporto_prioritario'}

def sanitize_modules_enabled(plan, raw):
    values = {x.strip() for x in (raw or '').split(',') if x.strip()}
    values = (values & ALLOWED_MODULES) - HARD_DISABLED_MODULES
    # API e integrazione registro sono moduli solo Enterprise: non si possono forzare su Base/Pro.
    if plan != 'ENTERPRISE':
        values -= ENTERPRISE_ONLY_TOGGLES
        values.discard('lockers')
        values.discard('blockchain')
        values.discard('ministeriale')
        values.discard('multi_plesso')
    return ','.join(sorted(values))

def sanitize_modules_disabled(plan, raw):
    values = {x.strip() for x in (raw or '').split(',') if x.strip()}
    # In Alpha lockers, API e registro sono moduli Enterprise disattivabili dal SuperAdmin.
    if plan == 'ENTERPRISE':
        values = values & ENTERPRISE_ONLY_TOGGLES
    else:
        values = set()
    return ','.join(sorted(values))

def enabled_features(school):
    if not school:
        return default_features_for_plan('BASE')
    base = default_features_for_plan(school.plan)
    extra = {x.strip() for x in (school.modules_enabled or '').split(',') if x.strip()}
    disabled = {x.strip() for x in (getattr(school, 'modules_disabled', '') or '').split(',') if x.strip()}
    return ((base | extra) - disabled) - HARD_DISABLED_MODULES

def plan_enabled(school, feature):
    if feature in HARD_DISABLED_MODULES:
        return False
    if feature == 'lockers' and school and not getattr(school, 'smart_locker_enabled', True):
        return False
    return feature in enabled_features(school)

def require_feature(feature):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            me = current_user()
            if me and me.school_id and not plan_enabled(me.school, feature):
                flash(f'Modulo non attivo per il piano {me.school.plan}. Passa a un piano superiore o abilita il modulo dal SuperAdmin.', 'warning')
                return redirect(url_for('modules_page'))
            return fn(*args, **kwargs)
        return wrapper
    return deco

def plan_badge(school):
    if not school:
        return 'BASE'
    return school.plan or 'BASE'

def module_matrix_for_school(school):
    plan = plan_badge(school)
    enabled = enabled_features(school)
    definitions = [
        ('qr','QR docente e Focus Mode','Avvio lezione con QR temporaneo, scansione studente, timer Focus e registro base.'),
        ('dashboard','Dashboard operative','Cruscotti docente, dirigente, studente e genitore.'),
        ('csv','Upload CSV e credenziali','Importazione docenti/studenti/genitori e password temporanee.'),
        ('report_csv','Report CSV','Esportazione dati lezione per consiglio di classe e monitoraggio interno.'),
        ('gamification_base','Gamification base','Punti Focus e FocusToken essenziali.'),
        ('gamification','Gamification completa','Badge, ranking classi, premi educativi e obiettivi collettivi.'),
        ('ai','AI Analytics','Rischio distrazione, fasce critiche e analisi per classe/materia.'),
        ('wellbeing','Digital Wellness Score','Indicatore 0-100 per studente, classe e istituto.'),
        ('passport','Educational Passport','Portfolio PDF con competenze digitali, PCTO, Educazione civica e badge.'),
        ('interventi','Piani di intervento','Azioni educative per classi o studenti con criticità digitali.'),
        ('report_famiglie','Report famiglie','Lettura semplificata per genitori e consensi.'),
        ('lockers','Smart Locker / Phone Box','Gestione armadietti smart, NFC e deposito telefono.'),
        ('blockchain','Blockchain badge','Registro immutabile prototipo per badge e certificazioni.'),
        ('ministeriale','Report ministeriali','Report PTOF, Educazione Civica, PNRR e consiglio di classe.'),
        ('multi_plesso','Multi-plesso','Gestione sedi/plessi, assegnazione utenti e statistiche aggregate per sede.'),
        ('api','API integrazioni','Endpoint JSON per mobile app, device IoT, phone box e registro.'),
        ('registro','Integrazione registro elettronico','Modulo predisposto per Argo, Spaggiari, Axios, Nuvola o API scuola.'),
    ]
    return [{'key':k,'name':n,'description':d,'enabled':k in enabled} for k,n,d in definitions]

def child_for_parent(parent):
    if not parent or parent.role != 'genitore':
        return None
    if getattr(parent, 'parent_student_id', None):
        st = User.query.get(parent.parent_student_id)
        if st and st.school_id == parent.school_id and st.role == 'studente':
            return st
    child_email = parent.email.replace('genitore.', '', 1)
    child = User.query.filter_by(email=child_email, school_id=parent.school_id, role='studente').first()
    if child:
        return child
    # fallback demo/commerciale: primo studente della stessa scuola associabile al genitore demo
    return User.query.filter_by(school_id=parent.school_id, role='studente').order_by(User.id).first()

def days_to_expiry(school):
    if not school or not school.license_end:
        return None
    return (school.license_end - date.today()).days

def school_scope_query(model):
    me=current_user()
    q=model.query
    if me and me.role!='superadmin' and hasattr(model,'school_id'):
        q=q.filter_by(school_id=me.school_id)
    return q

@app.route('/')
def index():
    me=current_user()
    if not me: return redirect(url_for('login'))
    return redirect(url_for(f"dashboard_{me.role}"))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(email=request.form['email'].strip().lower()).first()
        if u and u.active and check_password_hash(u.password_hash, request.form['password']):
            if u.school_id and u.school and not u.school.active:
                flash('Istituto disattivato: contattare la segreteria o il fornitore Focus360 AI.','danger')
                return render_template('login.html')
            session['uid']=u.id
            if getattr(u, 'must_change_password', False):
                return redirect(url_for('change_password'))
            return redirect(url_for('index'))
        flash('Credenziali non valide','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/change-password', methods=['GET','POST'])
@login_required()
def change_password():
    me=current_user()
    if request.method=='POST':
        new_pwd=request.form.get('new_password','')
        confirm=request.form.get('confirm_password','')
        if len(new_pwd) < 8:
            flash('La password deve contenere almeno 8 caratteri','danger')
        elif new_pwd != confirm:
            flash('Le password non coincidono','danger')
        else:
            me.password_hash=generate_password_hash(new_pwd)
            me.must_change_password=False
            me.temporary_password=''
            db.session.commit()
            flash('Password aggiornata correttamente','success')
            return redirect(url_for('index'))
    return render_template('change_password.html')



def school_identity_key(school):
    """Chiave logica per evitare duplicazioni nella vista SuperAdmin.
    Priorità: tenant_slug, codice meccanografico, nome+comune.
    L'ambiente demo resta sempre visibile una sola volta.
    """
    if (school.tenant_slug or '') == 'demo-focus360-enterprise' or 'demo' in (school.name or '').lower():
        return 'DEMO_FOCUS360'
    if school.codice_meccanografico:
        return 'CODICE:' + school.codice_meccanografico.strip().upper()
    return 'NAME:' + ((school.name or '').strip().lower() + '|' + (school.city or '').strip().lower())

def visible_schools_for_superadmin():
    """Restituisce solo istituti realmente distinti: una Demo + istituti creati.
    Evita righe duplicate causate da seed/demo ripetuti o database di test.
    """
    rows = School.query.order_by(School.id.asc()).all()
    seen = set()
    result = []
    for school in rows:
        key = school_identity_key(school)
        if key in seen:
            continue
        seen.add(key)
        result.append(school)
    # Demo sempre in alto; poi istituti creati più recenti prima.
    result.sort(key=lambda s: (0 if school_identity_key(s) == 'DEMO_FOCUS360' else 1, -s.id))
    return result

@app.route('/superadmin', methods=['GET','POST'])
@login_required('superadmin')
def dashboard_superadmin():
    if request.method=='POST':
        required=['name','codice','city','address','fiscal_code','pec','billing_email','license_end','ds_email','ds_surname','ds_name']
        missing=[x for x in required if not request.form.get(x)]
        if missing:
            flash('Tutte le informazioni dell’istituto e del dirigente sono obbligatorie: ' + ', '.join(missing), 'danger')
            return redirect(url_for('dashboard_superadmin'))
        lic_end = request.form.get('license_end')
        license_end = datetime.strptime(lic_end, '%Y-%m-%d').date()
        codice_clean = request.form.get('codice','').strip().upper()
        existing_school = School.query.filter_by(codice_meccanografico=codice_clean).first()
        if existing_school:
            flash('Esiste già un istituto con questo codice meccanografico. Apri la scheda esistente e modifica i dati invece di crearne una duplicata.', 'warning')
            return redirect(url_for('dashboard_superadmin'))
        tenant_slug = codice_clean.lower().replace(' ', '-')
        selected_plan = request.form.get('plan','BASE')
        disabled_modules = sanitize_modules_disabled(selected_plan, ','.join(request.form.getlist('modules_disabled')))
        school=School(
            name=request.form['name'], codice_meccanografico=codice_clean, city=request.form.get('city'),
            address=request.form.get('address'), fiscal_code=request.form.get('fiscal_code'), pec=request.form.get('pec'),
            billing_email=request.form.get('billing_email'), plan=selected_plan,
            payment_status=request.form.get('payment_status','in_attesa'), payment_method=request.form.get('payment_method','bonifico'),
            license_end=license_end, tenant_slug=tenant_slug, modules_enabled=sanitize_modules_enabled(selected_plan, request.form.get('modules_enabled','')),
            modules_disabled=disabled_modules,
            smart_locker_enabled=(selected_plan == 'ENTERPRISE' and 'lockers' not in disabled_modules), active=True
        )
        db.session.add(school); db.session.commit()
        pwd=random_password()
        dirigente=User(school_id=school.id, role='dirigente', surname=request.form.get('ds_surname'), name=request.form.get('ds_name'), email=request.form['ds_email'].lower(), password_hash=generate_password_hash(pwd), temporary_password=pwd, must_change_password=True)
        db.session.add(dirigente); db.session.commit()
        flash(f'Istituto creato. Credenziali dirigente: {dirigente.email} / {pwd}','success')
    schools=visible_schools_for_superadmin()
    expiring=[s for s in schools if days_to_expiry(s) is not None and days_to_expiry(s) <= 30]
    return render_template('superadmin.html', schools=schools, expiring=expiring, payments=PaymentRecord.query.order_by(PaymentRecord.id.desc()).limit(10).all())

@app.route('/superadmin/school/<int:school_id>/update', methods=['POST'])
@login_required('superadmin')
def superadmin_update_school(school_id):
    school=School.query.get_or_404(school_id)
    # Modifica completa del tenant scolastico da SuperAdmin
    for field, form_name in [
        ('name','name'), ('codice_meccanografico','codice'), ('city','city'), ('address','address'),
        ('fiscal_code','fiscal_code'), ('pec','pec'), ('billing_email','billing_email'), ('notes','notes')
    ]:
        if form_name in request.form:
            setattr(school, field, request.form.get(form_name))
    school.plan=request.form.get('plan', school.plan)
    school.payment_status=request.form.get('payment_status', school.payment_status)
    school.payment_method=request.form.get('payment_method', school.payment_method)
    school.modules_enabled=sanitize_modules_enabled(school.plan, request.form.get('modules_enabled', school.modules_enabled or ''))
    school.modules_disabled=sanitize_modules_disabled(school.plan, ','.join(request.form.getlist('modules_disabled')))
    school.smart_locker_enabled=bool(request.form.get('smart_locker_enabled'))
    school.active = bool(request.form.get('active'))
    lic_end=request.form.get('license_end')
    if lic_end:
        try:
            school.license_end=datetime.strptime(lic_end, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato scadenza non valido','danger')
            return redirect(url_for('dashboard_superadmin'))
    school.notes=request.form.get('notes', school.notes)
    db.session.commit()
    flash('Istituto aggiornato: anagrafica, piano, moduli, smart locker, pagamento, stato e scadenza licenza modificati.','success')
    return redirect(url_for('dashboard_superadmin'))

@app.route('/superadmin/school/<int:school_id>/toggle', methods=['POST'])
@login_required('superadmin')
def superadmin_toggle_school(school_id):
    school=School.query.get_or_404(school_id)
    school.active = not school.active
    User.query.filter_by(school_id=school.id).update({'active': school.active}, synchronize_session=False)
    db.session.commit()
    flash(('Istituto riattivato.' if school.active else 'Istituto disattivato. Anche gli utenti del tenant sono stati disattivati.'),'warning')
    return redirect(url_for('dashboard_superadmin'))

@app.route('/superadmin/school/<int:school_id>/delete', methods=['POST'])
@login_required('superadmin')
def superadmin_delete_school(school_id):
    school=School.query.get_or_404(school_id)
    sid=school.id
    # Eliminazione fisica per prototipo. In produzione preferire soft delete e conservazione fiscale/log.
    for model in [InterventionPlan, DeviceEvent, ParentConsent, PaymentRecord, PortfolioItem, Badge, SmartLocker, WellbeingSurvey, FocusRecord, Lesson, BlockchainEvent, User, Plesso]:
        if hasattr(model, 'school_id'):
            model.query.filter_by(school_id=sid).delete(synchronize_session=False)
    db.session.delete(school)
    db.session.commit()
    flash('Istituto eliminato dal prototipo.','danger')
    return redirect(url_for('dashboard_superadmin'))

@app.route('/credentials/export')
@login_required(['superadmin','dirigente'])
def export_credentials():
    me=current_user()
    school_id=request.args.get('school_id', type=int) if me.role=='superadmin' else me.school_id
    if not school_id:
        flash('Seleziona un istituto per esportare le credenziali','danger')
        return redirect(url_for('dashboard_superadmin'))
    users=User.query.filter(User.school_id==school_id, User.role.in_(['dirigente','docente','studente','genitore'])).order_by(User.role, User.class_name, User.surname).all()
    out=io.StringIO()
    w=csv.writer(out, delimiter=';')
    w.writerow(['ruolo','cognome','nome','email_username','password_temporanea','classe','deve_cambiare_password','attivo'])
    for u in users:
        w.writerow([u.role,u.surname or '',u.name or '',u.email,u.temporary_password or '',u.class_name or '', 'SI' if u.must_change_password else 'NO', 'SI' if u.active else 'NO'])
    data=io.BytesIO(out.getvalue().encode('utf-8-sig'))
    return send_file(data, mimetype='text/csv', as_attachment=True, download_name=f'focus360_credenziali_istituto_{school_id}.csv')


@app.route('/dirigente/users')
@login_required('dirigente')
def dirigente_users():
    me=current_user()
    users=User.query.filter(User.school_id==me.school_id, User.role.in_(['docente','studente','genitore'])).order_by(User.role, User.class_name, User.surname).all()
    return render_template('users_manage.html', users=users)

@app.route('/dirigente/users/<int:user_id>/edit', methods=['GET','POST'])
@login_required('dirigente')
def dirigente_edit_user(user_id):
    me=current_user(); u=User.query.get_or_404(user_id)
    if u.school_id != me.school_id or u.role not in ['docente','studente','genitore']:
        flash('Utente non modificabile', 'danger'); return redirect(url_for('dirigente_users'))
    if request.method=='POST':
        new_email=(request.form.get('email') or '').strip().lower()
        if new_email != u.email and User.query.filter_by(email=new_email).first():
            flash('Email già presente nel sistema', 'danger'); return redirect(url_for('dirigente_edit_user', user_id=u.id))
        u.surname=request.form.get('surname','')
        u.name=request.form.get('name','')
        u.email=new_email
        u.phone=request.form.get('phone','')
        u.discipline=request.form.get('discipline','')
        u.class_name=request.form.get('class_name','')
        u.birthdate=request.form.get('birthdate','')
        if plan_enabled(me.school, 'multi_plesso'):
            u.plesso_id = int(request.form.get('plesso_id') or 0) or None
        u.active=bool(request.form.get('active'))
        db.session.commit(); flash('Utente aggiornato', 'success')
        return redirect(url_for('dirigente_users'))
    plessi = Plesso.query.filter_by(school_id=me.school_id, active=True).order_by(Plesso.name).all() if plan_enabled(me.school, 'multi_plesso') else []
    return render_template('user_edit.html', u=u, plessi=plessi)

@app.route('/dirigente/users/<int:user_id>/reset-password', methods=['POST'])
@login_required('dirigente')
def dirigente_reset_user_password(user_id):
    me=current_user(); u=User.query.get_or_404(user_id)
    if u.school_id != me.school_id or u.role not in ['docente','studente','genitore']:
        flash('Utente non modificabile', 'danger'); return redirect(url_for('dirigente_users'))
    pwd=random_password()
    u.password_hash=generate_password_hash(pwd)
    u.temporary_password=pwd
    u.must_change_password=True
    db.session.commit()
    flash(f'Password temporanea generata per {u.email}: {pwd}', 'warning')
    return redirect(url_for('dirigente_users'))

@app.route('/superadmin/school/<int:school_id>/notify-expiry', methods=['POST'])
@login_required('superadmin')
def notify_expiry(school_id):
    school=School.query.get_or_404(school_id)
    days=days_to_expiry(school)
    subject=f'Focus360 AI - scadenza abbonamento {school.name}'
    body=(f'Gentile Istituto {school.name},\n\n'
          f'la licenza Focus360 AI associata al piano {school.plan} risulta in scadenza il {school.license_end}.\n'
          f'Giorni residui: {days}.\n\n'
          'Per evitare l’interruzione dei servizi, si invita a procedere al rinnovo o a contattare il referente commerciale.\n\n'
          'Cordiali saluti,\nFocus360 AI')
    sent=False; error=''
    smtp_host=os.environ.get('SMTP_HOST')
    if smtp_host and school.billing_email:
        try:
            from email.mime.text import MIMEText
            msg=MIMEText(body, 'plain', 'utf-8')
            msg['Subject']=subject
            msg['From']=os.environ.get('SMTP_FROM','noreply@focus360.ai')
            msg['To']=school.billing_email
            with smtplib.SMTP(smtp_host, int(os.environ.get('SMTP_PORT','587'))) as server:
                if os.environ.get('SMTP_TLS','1') == '1': server.starttls()
                if os.environ.get('SMTP_USER'): server.login(os.environ['SMTP_USER'], os.environ.get('SMTP_PASSWORD',''))
                server.send_message(msg)
            sent=True
        except Exception as exc:
            error=str(exc)
    school.last_expiry_notice_at=datetime.utcnow()
    db.session.commit()
    mailto=f"mailto:{school.billing_email}?subject={quote(subject)}&body={quote(body)}" if school.billing_email else ''
    if sent:
        flash('Email automatica di scadenza inviata all’istituto.', 'success')
    else:
        flash('SMTP non configurato o invio non riuscito. Puoi usare il link mail manuale generato.' + (f' Errore: {error}' if error else ''), 'warning')
    return render_template('expiry_email.html', school=school, subject=subject, body=body, mailto=mailto, sent=sent, error=error)

@app.route('/dirigente')
@login_required('dirigente')
def dashboard_dirigente():
    me=current_user(); teachers=User.query.filter_by(school_id=me.school_id, role='docente').count(); students=User.query.filter_by(school_id=me.school_id, role='studente').count()
    records=FocusRecord.query.join(Lesson).filter(Lesson.school_id==me.school_id).all()
    total_tokens=sum(r.tokens for r in records); violations=sum(r.violations for r in records)
    class_stats={}
    for r in records:
        c=r.student.class_name or 'N/D'; class_stats.setdefault(c, {'points':0,'tokens':0,'violations':0,'count':0})
        class_stats[c]['points']+=r.points; class_stats[c]['tokens']+=r.tokens; class_stats[c]['violations']+=r.violations; class_stats[c]['count']+=1
    ai_risk=focus_risk_score(records); att_index=attention_index(records); wellbeing_rows=WellbeingSurvey.query.filter_by(school_id=me.school_id).order_by(WellbeingSurvey.id.desc()).limit(10).all()
    wellness_school=digital_wellness_score(records, wellbeing_rows, PortfolioItem.query.filter_by(school_id=me.school_id).all())
    first_student=User.query.filter_by(school_id=me.school_id, role='studente').order_by(User.id).first()
    return render_template('dirigente.html', teachers=teachers, students=students, records=records, total_tokens=total_tokens, violations=violations, class_stats=class_stats, ai_risk=ai_risk, att_index=att_index, wellbeing_rows=wellbeing_rows, wellness_school=wellness_school, first_student_id=(first_student.id if first_student else None))

@app.route('/upload/<kind>', methods=['GET','POST'])
@login_required(['dirigente','docente'])
def upload(kind):
    me=current_user()
    if kind=='docenti' and me.role!='dirigente':
        flash('Solo il dirigente può caricare docenti','danger'); return redirect(url_for('index'))
    created=[]
    plessi = Plesso.query.filter_by(school_id=me.school_id, active=True).order_by(Plesso.name).all() if plan_enabled(me.school, 'multi_plesso') else []
    if request.method=='POST':
        f=request.files.get('csvfile')
        default_plesso_id = int(request.form.get('plesso_id') or 0) or None
        text=f.read().decode('utf-8-sig')
        reader=csv.DictReader(io.StringIO(text), delimiter=';')
        for row in reader:
            email=(row.get('mail') or row.get('email') or '').strip().lower()
            if not email or User.query.filter_by(email=email).first(): continue
            pwd=random_password()
            role='docente' if kind=='docenti' else 'studente'
            row_plesso_id = default_plesso_id
            row_plesso_code = (row.get('plesso') or row.get('codice_plesso') or row.get('sede') or '').strip()
            if row_plesso_code and plan_enabled(me.school, 'multi_plesso'):
                pl = Plesso.query.filter_by(school_id=me.school_id, code=row_plesso_code).first()
                if pl: row_plesso_id = pl.id
            u=User(school_id=me.school_id, plesso_id=row_plesso_id, role=role, surname=row.get('cognome',''), name=row.get('nome',''), email=email, phone=row.get('telefono',''), password_hash=generate_password_hash(pwd), temporary_password=pwd, must_change_password=True, discipline=row.get('disciplina',''), class_name=row.get('classe',''), birthdate=row.get('data di nascita',''))
            db.session.add(u); db.session.flush(); created.append((u.email,pwd,u.role,u.class_name))
            if role=='studente':
                parent_csv=(row.get('email_genitore') or row.get('mail_genitore') or row.get('genitore_email') or '').strip().lower()
                p_email=parent_csv or f"genitore.{u.email}"
                if not User.query.filter_by(email=p_email).first():
                    gpwd=random_password()
                    g=User(school_id=me.school_id, plesso_id=row_plesso_id, parent_student_id=u.id, role='genitore', surname='Genitore', name=f'{u.name} {u.surname}', email=p_email, password_hash=generate_password_hash(gpwd), temporary_password=gpwd, must_change_password=True, class_name=u.class_name)
                    db.session.add(g); created.append((g.email,gpwd,g.role,g.class_name))
        db.session.commit()
        return render_template('upload_result.html', created=created)
    return render_template('upload.html', kind=kind, plessi=plessi)

@app.route('/docente', methods=['GET','POST'])
@login_required('docente')
def dashboard_docente():
    me=current_user()
    if request.method=='POST':
        raw=secrets.token_urlsafe(24)
        l=Lesson(school_id=me.school_id, teacher_id=me.id, class_name=request.form['class_name'], subject=request.form['subject'], duration_minutes=int(request.form.get('duration',60)), qr_token_hash=sha(raw), qr_expires_at=datetime.utcnow()+timedelta(minutes=10))
        db.session.add(l); db.session.commit()
        return redirect(url_for('lesson', lesson_id=l.id, token=raw))
    lessons=Lesson.query.filter_by(teacher_id=me.id).order_by(Lesson.id.desc()).limit(10).all()
    classes=sorted({u.class_name for u in User.query.filter_by(school_id=me.school_id, role='studente').all() if u.class_name})
    return render_template('docente.html', lessons=lessons, classes=classes)

@app.route('/lesson/<int:lesson_id>')
@login_required(['docente','dirigente'])
def lesson(lesson_id):
    l=Lesson.query.get_or_404(lesson_id)
    token=request.args.get('token','')
    qr_url=url_for('scan_focus', lesson_id=l.id, token=token, _external=True) if token else ''
    records=FocusRecord.query.filter_by(lesson_id=l.id).all()
    active=sum(1 for r in records if r.focus_active); perc=round((active/max(1,len(records)))*100,1)
    return render_template('lesson.html', l=l, qr_url=qr_url, records=records, perc=perc)

@app.route('/qr/<int:lesson_id>')
@login_required(['docente','dirigente'])
def qr_png(lesson_id):
    token=request.args.get('token','')
    img=qrcode.make(url_for('scan_focus', lesson_id=lesson_id, token=token, _external=True))
    buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/join-lesson', methods=['GET','POST'])
@login_required(['studente'])
def join_lesson():
    """Pagina studente per partecipare alla lezione tramite QR o link incollato.
    Nel prototipo web la scansione usa la fotocamera del browser; in produzione può essere sostituita da app mobile nativa.
    """
    me=current_user()
    if request.method == 'POST':
        qr_value=(request.form.get('qr_value') or '').strip()
        if not qr_value:
            flash('Inserisci o scansiona il link QR generato dal docente.','warning')
            return redirect(url_for('join_lesson'))
        # Accetta sia URL completo sia percorso /scan/<lesson_id>/<token>
        try:
            from urllib.parse import urlparse, quote
            parsed=urlparse(qr_value)
            path=parsed.path if parsed.scheme else qr_value
            parts=[x for x in path.split('/') if x]
            if len(parts)>=3 and parts[0]=='scan':
                lesson_id=int(parts[1]); token=parts[2]
                return redirect(url_for('scan_focus', lesson_id=lesson_id, token=token))
        except Exception:
            pass
        flash('QR non riconosciuto. Usa il QR temporaneo proiettato dal docente.','danger')
        return redirect(url_for('join_lesson'))
    active_lessons=Lesson.query.filter_by(school_id=me.school_id, class_name=me.class_name).filter(Lesson.qr_expires_at>=datetime.utcnow()).order_by(Lesson.id.desc()).all()
    return render_template('join_lesson.html', active_lessons=active_lessons)

@app.route('/scan/<int:lesson_id>/<token>', methods=['GET','POST'])
@login_required(['studente'])
def scan_focus(lesson_id, token):
    me=current_user(); l=Lesson.query.get_or_404(lesson_id)
    if datetime.utcnow()>l.qr_expires_at or sha(token)!=l.qr_token_hash:
        flash('QR scaduto o non valido','danger'); return redirect(url_for('dashboard_studente'))
    if me.class_name != l.class_name:
        flash('QR non associato alla tua classe','danger'); return redirect(url_for('dashboard_studente'))
    r=FocusRecord.query.filter_by(lesson_id=l.id, student_id=me.id).first()
    if request.method == 'POST':
        if not r:
            r=FocusRecord(lesson_id=l.id, student_id=me.id, minutes_focus=0)
            db.session.add(r); db.session.flush()
        db.session.add(DeviceEvent(school_id=me.school_id, student_id=me.id, lesson_id=l.id, event_type='focus_started', value='QR confermato dallo studente', risk_weight=0, source='qr_web'))
        db.session.commit()
        flash('Modalità Focus attivata. In prototipo il blocco app è simulato; su mobile richiede integrazione nativa Android/iOS.','success')
        return redirect(url_for('focus_session', record_id=r.id))
    return render_template('scan_focus.html', l=l, token=token, existing_record=r)

@app.route('/focus/<int:record_id>', methods=['GET','POST'])
@login_required('studente')
def focus_session(record_id):
    r=FocusRecord.query.get_or_404(record_id)
    if r.student_id != current_user().id: return redirect(url_for('index'))
    if request.method=='POST':
        l=r.lesson
        r.minutes_focus=int(request.form.get('minutes_focus', l.duration_minutes))
        r.exited_app=int(request.form.get('exited_app',0)); r.opened_social=int(request.form.get('opened_social',0)); r.screen_minutes=int(request.form.get('screen_minutes',0))
        r.violations=r.exited_app+r.opened_social
        r.focus_active=(r.violations==0 and r.minutes_focus>=l.duration_minutes)
        r.points=calc_points(r.minutes_focus,l.duration_minutes,r.exited_app,r.opened_social,r.screen_minutes)
        r.tokens=1 if r.minutes_focus>=l.duration_minutes and r.violations==0 else 0
        payload={'record':r.id,'student':r.student.email,'lesson':l.id,'points':r.points,'tokens':r.tokens,'minutes':r.minutes_focus}
        r.blockchain_hash=write_chain(l.school_id,'FOCUS_RECORD',payload)
        award_badges(r.student)
        db.session.commit(); flash('Sessione chiusa e registrata nel registro focus','success')
        return redirect(url_for('dashboard_studente'))
    return render_template('focus.html', r=r)

def award_badges(student):
    total_tokens=sum(x.tokens for x in FocusRecord.query.filter_by(student_id=student.id).all())
    existing={b.name for b in Badge.query.filter_by(user_id=student.id).all()}
    for threshold, name in [(20,'Badge digitale Focus 20'),(100,'Certificato di cittadinanza digitale 100')]:
        if total_tokens>=threshold and name not in existing:
            payload={'student':student.email,'badge':name,'tokens':total_tokens}
            nft=write_chain(student.school_id,'BADGE_NFT',payload)
            db.session.add(Badge(school_id=student.school_id,user_id=student.id,class_name=student.class_name,name=name,description='Badge NFT educativo non speculativo',nft_hash=nft))

@app.route('/studente')
@login_required('studente')
def dashboard_studente():
    me=current_user(); records=FocusRecord.query.filter_by(student_id=me.id).order_by(FocusRecord.id.desc()).all(); badges=Badge.query.filter_by(user_id=me.id).all()
    risk=focus_risk_score(records); att_index=attention_index(records); surveys=WellbeingSurvey.query.filter_by(student_id=me.id).order_by(WellbeingSurvey.id.desc()).limit(3).all()
    passport=educational_passport(me) if plan_enabled(me.school, 'passport') or plan_enabled(me.school, 'wellbeing') else None
    wellness=passport['wellness'] if passport else digital_wellness_score(records, surveys, [])
    return render_template('studente.html', records=records, badges=badges, risk=risk, att_index=att_index, surveys=surveys, passport=passport, wellness=wellness)

@app.route('/genitore')
@login_required('genitore')
def dashboard_genitore():
    me=current_user(); child=child_for_parent(me)
    records=FocusRecord.query.filter_by(student_id=child.id).order_by(FocusRecord.id.desc()).all() if child else []
    return render_template('genitore.html', child=child, records=records)



@app.route('/wellness-score')
@login_required(['dirigente','docente','studente','genitore'])
@require_feature('wellbeing')
def wellness_score_page():
    me=current_user()
    if me.role=='studente':
        students=[me]
    elif me.role=='genitore':
        child=User.query.filter_by(email=me.email.replace('genitore.','',1)).first()
        students=[child] if child else []
    else:
        students=User.query.filter_by(school_id=me.school_id, role='studente').order_by(User.class_name, User.surname).all()
    rows=[]
    all_records=[]
    for st in students:
        records=FocusRecord.query.filter_by(student_id=st.id).all()
        surveys=WellbeingSurvey.query.filter_by(student_id=st.id).all()
        items=PortfolioItem.query.filter_by(student_id=st.id).all()
        w=digital_wellness_score(records, surveys, items)
        rows.append({'student':st,'wellness':w,'tokens':sum(r.tokens for r in records),'violations':sum(r.violations for r in records),'hours':round(sum(r.minutes_focus for r in records)/60,1)})
        all_records.extend(records)
    school_wellness=digital_wellness_score(all_records, WellbeingSurvey.query.filter_by(school_id=me.school_id).all() if me.school_id else [], PortfolioItem.query.filter_by(school_id=me.school_id).all() if me.school_id else [])
    return render_template('wellness_score.html', rows=rows, school_wellness=school_wellness)

@app.route('/passport')
@login_required(['studente','genitore'])
@require_feature('passport')
def my_passport():
    me=current_user()
    student=me if me.role=='studente' else child_for_parent(me)
    if not student:
        flash('Studente non trovato','warning'); return redirect(url_for('index'))
    return render_template('passport.html', data=educational_passport(student), can_add=False)

@app.route('/passport/download')
@login_required(['studente','genitore'])
@require_feature('passport')
def my_passport_download():
    me=current_user()
    student=me if me.role=='studente' else child_for_parent(me)
    if not student:
        flash('Studente non trovato','warning'); return redirect(url_for('index'))
    pdf=simple_passport_pdf(educational_passport(student))
    return send_file(io.BytesIO(pdf), as_attachment=True, download_name=f'Focus360_Educational_Passport_{student.surname}_{student.name}.pdf', mimetype='application/pdf')

@app.route('/passport/<int:student_id>/download')
@login_required(['dirigente','docente'])
@require_feature('passport')
def student_passport_download(student_id):
    me=current_user(); student=User.query.get_or_404(student_id)
    if student.school_id != me.school_id or student.role!='studente':
        flash('Studente non accessibile','danger'); return redirect(url_for('index'))
    pdf=simple_passport_pdf(educational_passport(student))
    return send_file(io.BytesIO(pdf), as_attachment=True, download_name=f'Focus360_Educational_Passport_{student.surname}_{student.name}.pdf', mimetype='application/pdf')

@app.route('/passport/<int:student_id>', methods=['GET','POST'])
@login_required(['dirigente','docente'])
@require_feature('passport')
def student_passport(student_id):
    me=current_user(); student=User.query.get_or_404(student_id)
    if student.school_id != me.school_id or student.role!='studente':
        flash('Studente non accessibile','danger'); return redirect(url_for('index'))
    if request.method=='POST':
        item=PortfolioItem(school_id=me.school_id, student_id=student.id, category=request.form.get('category','Digital Citizenship'), title=request.form.get('title'), description=request.form.get('description'), hours=float(request.form.get('hours') or 0), score=int(request.form.get('score') or 0), validator=f'{me.name} {me.surname}'.strip() or me.email)
        payload={'student':student.email,'category':item.category,'title':item.title,'validator':item.validator,'hours':item.hours,'score':item.score}
        item.evidence_hash=write_chain(me.school_id,'EDUCATIONAL_PASSPORT_ITEM',payload)
        db.session.add(item); db.session.commit(); flash('Elemento aggiunto al Focus360 AI Educational Passport','success')
    return render_template('passport.html', data=educational_passport(student), can_add=True)

@app.route('/wellbeing', methods=['GET','POST'])
@login_required('studente')
@require_feature('wellbeing')
def wellbeing():
    me=current_user()
    if request.method=='POST':
        w=WellbeingSurvey(school_id=me.school_id, student_id=me.id, stress_level=int(request.form.get('stress_level',3)), perceived_attention=int(request.form.get('perceived_attention',3)), sleep_quality=int(request.form.get('sleep_quality',3)), note=request.form.get('note',''))
        db.session.add(w); db.session.commit(); flash('Check-in benessere digitale salvato','success')
        return redirect(url_for('dashboard_studente'))
    surveys=WellbeingSurvey.query.filter_by(student_id=me.id).order_by(WellbeingSurvey.id.desc()).limit(10).all()
    return render_template('wellbeing.html', surveys=surveys)

@app.route('/ai')
@login_required(['dirigente','docente'])
@require_feature('ai')
def ai_dashboard():
    me=current_user()
    q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    records=q.all()
    by_class={}
    for r in records:
        c=r.student.class_name or 'N/D'; by_class.setdefault(c, []).append(r)
    rows=[]
    for c,rs in by_class.items():
        rows.append({'classe':c,'indice':attention_index(rs),'rischio':focus_risk_score(rs),'violazioni':sum(x.violations for x in rs),'tokens':sum(x.tokens for x in rs),'ore_recuperate':round(sum(x.minutes_focus for x in rs)/60,1)})
    rows=sorted(rows, key=lambda x: x['indice'], reverse=True)
    return render_template('ai.html', rows=rows, records=records)

@app.route('/lockers', methods=['GET','POST'])
@login_required(['dirigente','docente'])
@require_feature('lockers')
def lockers():
    me=current_user()
    if request.method=='POST':
        box=SmartLocker(school_id=me.school_id, class_name=request.form.get('class_name'), box_code=request.form.get('box_code'), status=request.form.get('status','libero'))
        db.session.add(box); db.session.commit(); flash('Phone box / locker registrato','success')
    boxes=SmartLocker.query.filter_by(school_id=me.school_id).order_by(SmartLocker.class_name, SmartLocker.box_code).all()
    students=User.query.filter_by(school_id=me.school_id, role='studente').order_by(User.class_name, User.surname).all()
    return render_template('lockers.html', boxes=boxes, students=students)

@app.route('/lockers/<int:box_id>/event', methods=['POST'])
@login_required(['dirigente','docente'])
@require_feature('lockers')
def locker_event(box_id):
    me=current_user(); box=SmartLocker.query.get_or_404(box_id)
    if box.school_id != me.school_id:
        flash('Box non accessibile','danger'); return redirect(url_for('lockers'))
    action=request.form.get('action','deposit')
    student_id=int(request.form.get('student_id') or 0) if request.form.get('student_id') else None
    student=User.query.get(student_id) if student_id else None
    if action == 'deposit' and student:
        box.status='occupato'; box.last_student_id=student.id; box.updated_at=datetime.utcnow()
        db.session.add(DeviceEvent(school_id=me.school_id, student_id=student.id, event_type='phonebox_deposit', value=box.box_code, risk_weight=-2, source='smart_locker_demo'))
        flash(f'Telefono depositato nella Phone Box {box.box_code} per {student.surname} {student.name}. Bonus focus attivabile.', 'success')
    elif action == 'withdraw':
        sid=box.last_student_id
        box.status='libero'; box.last_student_id=None; box.updated_at=datetime.utcnow()
        if sid:
            db.session.add(DeviceEvent(school_id=me.school_id, student_id=sid, event_type='phonebox_withdraw', value=box.box_code, risk_weight=0, source='smart_locker_demo'))
        flash(f'Phone Box {box.box_code} liberata.', 'info')
    elif action == 'maintenance':
        box.status='manutenzione'; box.updated_at=datetime.utcnow(); flash(f'Phone Box {box.box_code} in manutenzione.', 'warning')
    db.session.commit(); return redirect(url_for('lockers'))

@app.route('/api/v1/phonebox/event', methods=['POST'])
def api_phonebox_event():
    """Endpoint prototipo per ESP32/Raspberry: JSON con api_key, box_code, event, student_email."""
    data=request.get_json(silent=True) or {}
    api_key=os.environ.get('PHONEBOX_API_KEY','demo-phonebox-key')
    if data.get('api_key') != api_key:
        return jsonify({'ok':False,'error':'api_key non valida'}), 401
    box=SmartLocker.query.filter_by(box_code=data.get('box_code')).first()
    if not box:
        return jsonify({'ok':False,'error':'box non trovato'}), 404
    school = School.query.get(box.school_id)
    if not plan_enabled(school, 'lockers'):
        return jsonify({'ok':False,'error':'Modulo Smart Locker non attivo per questo istituto'}), 403
    student=User.query.filter_by(email=(data.get('student_email') or '').lower()).first() if data.get('student_email') else None
    event=data.get('event','heartbeat')
    if event == 'deposit' and student:
        box.status='occupato'; box.last_student_id=student.id
        db.session.add(DeviceEvent(school_id=box.school_id, student_id=student.id, event_type='phonebox_deposit', value=box.box_code, risk_weight=-2, source='phonebox_hardware'))
    elif event == 'withdraw':
        sid=box.last_student_id
        box.status='libero'; box.last_student_id=None
        if sid: db.session.add(DeviceEvent(school_id=box.school_id, student_id=sid, event_type='phonebox_withdraw', value=box.box_code, source='phonebox_hardware'))
    elif event == 'maintenance':
        box.status='manutenzione'
    box.updated_at=datetime.utcnow(); db.session.commit()
    return jsonify({'ok':True,'box':box.box_code,'status':box.status})

@app.route('/blockchain')
@login_required(['superadmin','dirigente'])
@require_feature('blockchain')
def blockchain():
    me=current_user()
    q=BlockchainEvent.query
    if me.role!='superadmin': q=q.filter_by(school_id=me.school_id)
    events=q.order_by(BlockchainEvent.id.desc()).limit(100).all()
    return render_template('blockchain.html', events=events)

@app.route('/api/v1/focus-summary')
@login_required(['dirigente','docente'])
@require_feature('api')
def api_focus_summary():
    me=current_user(); q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    records=q.all()
    return jsonify({'app':APP_NAME,'records':len(records),'attention_index':attention_index(records),'risk_score':focus_risk_score(records),'tokens':sum(r.tokens for r in records),'violations':sum(r.violations for r in records)})

@app.route('/report.csv')
@login_required(['dirigente','docente'])
@require_feature('report_csv')
def report_csv():
    me=current_user()
    rows=[]
    q=FocusRecord.query.join(Lesson)
    if me.role=='docente': q=q.filter(Lesson.teacher_id==me.id)
    else: q=q.filter(Lesson.school_id==me.school_id)
    for r in q.all():
        rows.append({'data':r.created_at.strftime('%Y-%m-%d'), 'classe':r.student.class_name, 'studente':f'{r.student.surname} {r.student.name}', 'materia':r.lesson.subject, 'minuti_focus':r.minutes_focus, 'violazioni':r.violations, 'punti':r.points, 'token':r.tokens, 'hash':r.blockchain_hash})
    buf = io.StringIO()
    fieldnames = ['data','classe','studente','materia','minuti_focus','violazioni','punti','token','hash']
    writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    writer.writerows(rows)
    mem = io.BytesIO(buf.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name='focus_report.csv', mimetype='text/csv; charset=utf-8')

@app.route('/api/analytics')
@login_required(['dirigente','docente'])
@require_feature('api')
def api_analytics():
    me=current_user(); q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    data={}
    for r in q.all():
        key=r.lesson.subject
        data.setdefault(key, {'points':0,'violations':0,'minutes':0,'n':0})
        data[key]['points']+=r.points; data[key]['violations']+=r.violations; data[key]['minutes']+=r.minutes_focus; data[key]['n']+=1
    return jsonify(data)




@app.route('/api-console')
@login_required(['superadmin','dirigente','docente'])
@require_feature('api')
def api_console():
    me=current_user()
    return render_template('api_console.html', phonebox_key=os.environ.get('PHONEBOX_API_KEY','demo-phonebox-key'))

@app.route('/registro', methods=['GET','POST'])
@login_required(['dirigente','superadmin'])
@require_feature('registro')
def registro():
    me=current_user()
    school_id = request.args.get('school_id', type=int) if me.role=='superadmin' else me.school_id
    if not school_id and me.role=='superadmin':
        school_id = (School.query.filter_by(plan='ENTERPRISE').first() or School.query.first()).id
    school=School.query.get_or_404(school_id)
    if me.role!='superadmin' and school.id != me.school_id:
        flash('Registro non accessibile','danger'); return redirect(url_for('index'))
    cfg=RegistroIntegration.query.filter_by(school_id=school.id).first()
    if request.method=='POST':
        if not cfg:
            cfg=RegistroIntegration(school_id=school.id); db.session.add(cfg)
        cfg.provider=request.form.get('provider') or 'Registro elettronico'
        cfg.endpoint_url=request.form.get('endpoint_url')
        cfg.api_key_hint=request.form.get('api_key_hint')
        cfg.sync_students=bool(request.form.get('sync_students'))
        cfg.sync_teachers=bool(request.form.get('sync_teachers'))
        cfg.sync_lessons=bool(request.form.get('sync_lessons'))
        cfg.sync_focus_reports=bool(request.form.get('sync_focus_reports'))
        cfg.status=request.form.get('status','configurazione')
        cfg.note=request.form.get('note')
        if request.form.get('simulate_sync'):
            cfg.last_sync_at=datetime.utcnow(); cfg.status='sincronizzazione demo completata'
            write_chain(school.id, 'REGISTRO_SYNC_ALPHA', {'provider':cfg.provider,'school':school.name,'status':cfg.status})
        db.session.commit(); flash('Configurazione registro elettronico aggiornata','success')
        return redirect(url_for('registro', school_id=school.id))
    return render_template('registro.html', school=school, cfg=cfg, schools=School.query.filter_by(plan='ENTERPRISE').all())

@app.route('/modules')
@login_required(['dirigente','docente','studente','genitore','superadmin'])
def modules_page():
    me=current_user()
    school = me.school if me and me.school_id else None
    if me.role == 'superadmin':
        schools = School.query.order_by(School.name).all()
        return render_template('modules.html', school=school, schools=schools, matrix=None)
    return render_template('modules.html', school=school, schools=[], matrix=module_matrix_for_school(school))

@app.route('/plans')
@login_required(['superadmin','dirigente'])
def plans_page():
    return render_template('plans.html')


@app.route('/plessi', methods=['GET','POST'])
@login_required(['dirigente','superadmin'])
@require_feature('multi_plesso')
def plessi():
    me=current_user()
    school = me.school
    if me.role == 'superadmin':
        sid = request.args.get('school_id') or request.form.get('school_id')
        school = School.query.get(int(sid)) if sid else School.query.filter_by(tenant_slug='demo-focus360-enterprise').first()
    if not school:
        flash('Nessun istituto selezionato.', 'warning')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        required = ['name','code','city','address']
        missing = [x for x in required if not request.form.get(x)]
        if missing:
            flash('Completa tutti i campi obbligatori del plesso.', 'danger')
        else:
            pl = Plesso(
                school_id=school.id,
                name=request.form.get('name'),
                code=request.form.get('code'),
                city=request.form.get('city'),
                address=request.form.get('address'),
                referent=request.form.get('referent'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                active=True
            )
            db.session.add(pl); db.session.commit()
            flash('Plesso creato correttamente.', 'success')
        return redirect(url_for('plessi', school_id=school.id) if me.role=='superadmin' else url_for('plessi'))
    plessi = Plesso.query.filter_by(school_id=school.id).order_by(Plesso.active.desc(), Plesso.name).all()
    stats = {}
    for pl in plessi:
        stats[pl.id] = {
            'docenti': User.query.filter_by(school_id=school.id, plesso_id=pl.id, role='docente').count(),
            'studenti': User.query.filter_by(school_id=school.id, plesso_id=pl.id, role='studente').count(),
            'lezioni': Lesson.query.filter_by(school_id=school.id, plesso_id=pl.id).count()
        }
    schools = School.query.order_by(School.name).all() if me.role=='superadmin' else []
    return render_template('plessi.html', school=school, plessi=plessi, stats=stats, schools=schools)

@app.route('/plessi/<int:plesso_id>/edit', methods=['GET','POST'])
@login_required(['dirigente','superadmin'])
@require_feature('multi_plesso')
def plesso_edit(plesso_id):
    me=current_user(); pl=Plesso.query.get_or_404(plesso_id)
    if me.role != 'superadmin' and pl.school_id != me.school_id:
        flash('Plesso non accessibile.', 'danger'); return redirect(url_for('dashboard'))
    if request.method == 'POST':
        for field in ['name','code','city','address','referent','email','phone']:
            setattr(pl, field, request.form.get(field))
        pl.active = bool(request.form.get('active'))
        db.session.commit(); flash('Plesso aggiornato.', 'success')
        return redirect(url_for('plessi', school_id=pl.school_id) if me.role=='superadmin' else url_for('plessi'))
    return render_template('plesso_edit.html', plesso=pl)

@app.route('/plessi/<int:plesso_id>/users', methods=['GET','POST'])
@login_required(['dirigente','superadmin'])
@require_feature('multi_plesso')
def plesso_users(plesso_id):
    me=current_user(); pl=Plesso.query.get_or_404(plesso_id)
    if me.role != 'superadmin' and pl.school_id != me.school_id:
        flash('Plesso non accessibile.', 'danger'); return redirect(url_for('dashboard'))
    if request.method == 'POST':
        selected = [int(x) for x in request.form.getlist('user_ids')]
        action = request.form.get('action','assign')
        if action == 'assign':
            User.query.filter(User.school_id==pl.school_id, User.id.in_(selected), User.role.in_(['docente','studente','genitore'])).update({User.plesso_id: pl.id}, synchronize_session=False)
            flash('Utenti associati al plesso.', 'success')
        elif action == 'remove':
            User.query.filter(User.school_id==pl.school_id, User.id.in_(selected), User.plesso_id==pl.id).update({User.plesso_id: None}, synchronize_session=False)
            flash('Utenti rimossi dal plesso.', 'warning')
        db.session.commit()
        return redirect(url_for('plesso_users', plesso_id=pl.id))
    users = User.query.filter(User.school_id==pl.school_id, User.role.in_(['docente','studente','genitore'])).order_by(User.role, User.class_name, User.surname).all()
    return render_template('plesso_users.html', plesso=pl, users=users)

@app.route('/plessi/<int:plesso_id>/delete', methods=['POST'])
@login_required(['dirigente','superadmin'])
@require_feature('multi_plesso')
def plesso_delete(plesso_id):
    me=current_user(); pl=Plesso.query.get_or_404(plesso_id)
    if me.role != 'superadmin' and pl.school_id != me.school_id:
        flash('Plesso non accessibile.', 'danger'); return redirect(url_for('dashboard'))
    if User.query.filter_by(plesso_id=pl.id).count() or Lesson.query.filter_by(plesso_id=pl.id).count():
        pl.active=False; db.session.commit(); flash('Il plesso contiene utenti/lezioni: è stato disattivato.', 'warning')
    else:
        db.session.delete(pl); db.session.commit(); flash('Plesso eliminato.', 'success')
    return redirect(url_for('plessi', school_id=pl.school_id) if me.role=='superadmin' else url_for('plessi'))

@app.route('/payments', methods=['GET','POST'])
@login_required('superadmin')
def payments():
    schools=School.query.order_by(School.name).all()
    if request.method=='POST':
        rec=PaymentRecord(school_id=int(request.form['school_id']), invoice_number=request.form.get('invoice_number'), amount=float(request.form.get('amount') or 0), method=request.form.get('method','bonifico'), status=request.form.get('status','in_attesa'), due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else None, note=request.form.get('note',''))
        db.session.add(rec); db.session.commit(); flash('Pagamento/fattura registrato','success')
        return redirect(url_for('payments'))
    records=PaymentRecord.query.order_by(PaymentRecord.id.desc()).all()
    return render_template('payments.html', schools=schools, records=records)

@app.route('/consensi', methods=['GET','POST'])
@login_required(['dirigente','genitore'])
def consensi():
    me=current_user()
    students=[]
    if me.role=='dirigente':
        students=User.query.filter_by(school_id=me.school_id, role='studente').order_by(User.class_name,User.surname).all()
    elif me.role=='genitore':
        child_email=me.email.replace('genitore.','',1)
        child=User.query.filter_by(email=child_email).first()
        students=[child] if child else []
    if request.method=='POST':
        sid=int(request.form['student_id'])
        old=ParentConsent.query.filter_by(student_id=sid).first()
        if not old:
            old=ParentConsent(school_id=me.school_id, student_id=sid)
            db.session.add(old)
        old.consent_focus=bool(request.form.get('consent_focus'))
        old.consent_analytics=bool(request.form.get('consent_analytics'))
        old.consent_badge=bool(request.form.get('consent_badge'))
        old.signed_by=f'{me.name} {me.surname}'.strip() or me.email
        old.signed_at=datetime.utcnow()
        db.session.commit(); flash('Consensi aggiornati','success')
    consents={c.student_id:c for c in ParentConsent.query.filter_by(school_id=me.school_id).all()}
    return render_template('consensi.html', students=students, consents=consents)

@app.route('/ministeriale')
@login_required(['dirigente','docente'])
@require_feature('ministeriale')
def ministeriale():
    me=current_user(); q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    records=q.all()
    by_class={}
    by_subject={}
    for r in records:
        c=r.student.class_name or 'N/D'; by_class.setdefault(c, []).append(r)
        by_subject.setdefault(r.lesson.subject, []).append(r)
    payload={
        'app':APP_NAME,
        'data_generazione':datetime.now().strftime('%d/%m/%Y %H:%M'),
        'records':len(records),
        'ore_focus':round(sum(r.minutes_focus for r in records)/60,1),
        'violazioni':sum(r.violations for r in records),
        'tokens':sum(r.tokens for r in records),
        'indice_attenzione':attention_index(records),
        'rischio_ai':focus_risk_score(records),
        'digital_wellness':digital_wellness_score(records, WellbeingSurvey.query.filter_by(school_id=me.school_id).all(), PortfolioItem.query.filter_by(school_id=me.school_id).all()),
        'classi':[(k, attention_index(v), sum(x.violations for x in v), sum(x.tokens for x in v)) for k,v in by_class.items()],
        'materie':[(k, attention_index(v), sum(x.violations for x in v), round(sum(x.minutes_focus for x in v)/60,1)) for k,v in by_subject.items()]
    }
    return render_template('ministeriale.html', data=payload)

@app.route('/interventi', methods=['GET','POST'])
@login_required(['dirigente','docente'])
@require_feature('interventi')
def interventi():
    me=current_user()
    if request.method=='POST':
        p=InterventionPlan(school_id=me.school_id, class_name=request.form.get('class_name'), title=request.form.get('title'), owner=f'{me.name} {me.surname}'.strip(), status=request.form.get('status','aperto'), action=request.form.get('action'))
        db.session.add(p); db.session.commit(); flash('Piano di intervento salvato','success')
    plans=InterventionPlan.query.filter_by(school_id=me.school_id).order_by(InterventionPlan.id.desc()).all()
    return render_template('interventi.html', plans=plans)

@app.route('/api/v1/device-event', methods=['POST'])
@login_required('studente')
@require_feature('api')
def api_device_event():
    me=current_user(); data=request.get_json(silent=True) or {}
    weights={'exit_app':15,'social_open':25,'screen_on':5,'screenshot':10,'multitasking':15,'wifi_checkin':0,'nfc_checkin':0}
    ev_type=data.get('event_type','generic')
    ev=DeviceEvent(school_id=me.school_id, student_id=me.id, lesson_id=data.get('lesson_id'), event_type=ev_type, value=str(data.get('value','')), risk_weight=weights.get(ev_type,3), source=data.get('source','mobile_api'))
    db.session.add(ev); db.session.commit()
    return jsonify({'ok':True,'event_id':ev.id,'risk_weight':ev.risk_weight})



DEMO_USERS = {
    'dirigente@demo.focus360.ai': 'dirigente123',
    'docente@demo.focus360.ai': 'docente123',
    'studente@demo.focus360.ai': 'studente123',
    'genitore@demo.focus360.ai': 'genitore123',
}

def upsert_user(email, password, **kwargs):
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, password_hash=generate_password_hash(password), temporary_password=password, must_change_password=True, **kwargs)
        db.session.add(u)
        db.session.flush()
    else:
        for k, v in kwargs.items():
            setattr(u, k, v)
        u.password_hash = generate_password_hash(password)
        u.temporary_password = password
        u.must_change_password = True
        u.active = True
    return u

def create_demo_environment(reset=False):
    """Genera un tenant dimostrativo Enterprise con dati realistici.
    Pensato per demo commerciali: dashboard già popolate, utenti demo, classi, lezioni,
    FocusRecord, badge, consensi, smart locker, pagamenti, interventi e Educational Passport.
    """
    existing = School.query.filter_by(tenant_slug='demo-focus360-enterprise').first()
    if existing and not reset:
        return existing, 'already_exists'
    if existing and reset:
        sid = existing.id
        # Elimina dati demo in ordine semplice. Le tabelle non hanno cascade esplicito.
        for model in [InterventionPlan, DeviceEvent, ParentConsent, PaymentRecord, PortfolioItem, Badge, SmartLocker, WellbeingSurvey, FocusRecord, Lesson, BlockchainEvent, User, Plesso]:
            q = model.query
            if hasattr(model, 'school_id'):
                q = q.filter_by(school_id=sid)
            elif model is User:
                q = q.filter_by(school_id=sid)
            else:
                continue
            q.delete(synchronize_session=False)
        db.session.delete(existing)
        db.session.commit()

    school = School(
        name='IIS Demo Focus360 AI Enterprise',
        codice_meccanografico='MEIS000360',
        city='Barcellona Pozzo di Gotto',
        address='Via Innovazione Digitale 1',
        fiscal_code='00000000000',
        pec='meis000360@pec.istruzione.it',
        billing_email='amministrazione@demo.focus360.ai',
        plan='ENTERPRISE',
        payment_status='pagato',
        payment_method='bonifico / MEPA',
        tenant_slug='demo-focus360-enterprise',
        notes='Ambiente demo generato automaticamente per presentazioni commerciali Focus360 AI Enterprise.', modules_enabled='', modules_disabled='', smart_locker_enabled=True
    )
    db.session.add(school); db.session.flush()

    plesso_centrale = Plesso(school_id=school.id, name='Sede centrale', code='CENTRALE', city='Barcellona Pozzo di Gotto', address='Via Innovazione Digitale 1', referent='Dirigente Demo', email='centrale@demo.focus360.ai', phone='0900000000')
    plesso_succursale = Plesso(school_id=school.id, name='Succursale Tecnologica', code='SUCC-TECH', city='Barcellona Pozzo di Gotto', address='Via Laboratori 12', referent='Prof. Marco Rossi', email='succursale@demo.focus360.ai', phone='0900000002')
    db.session.add_all([plesso_centrale, plesso_succursale]); db.session.flush()

    dirigente = upsert_user('dirigente@demo.focus360.ai', 'dirigente123', school_id=school.id, plesso_id=plesso_centrale.id, role='dirigente', surname='Verdi', name='Laura', phone='0900000001')
    docenti = [
        upsert_user('docente@demo.focus360.ai', 'docente123', school_id=school.id, plesso_id=plesso_centrale.id, role='docente', surname='Rossi', name='Marco', discipline='Informatica', class_name='3A INF', phone='0900000100'),
        upsert_user('docente.matematica@demo.focus360.ai', 'docente123', school_id=school.id, plesso_id=plesso_centrale.id, role='docente', surname='Bianchi', name='Anna', discipline='Matematica', class_name='4A INF', phone='0900000101'),
        upsert_user('docente.sistemi@demo.focus360.ai', 'docente123', school_id=school.id, plesso_id=plesso_centrale.id, role='docente', surname='Costa', name='Giuseppe', discipline='Sistemi e reti', class_name='5A INF', phone='0900000102'),
        upsert_user('docente.inglese@demo.focus360.ai', 'docente123', school_id=school.id, plesso_id=plesso_succursale.id, role='docente', surname='Greco', name='Elena', discipline='Inglese', class_name='3B INF', phone='0900000103'),
        upsert_user('docente.civica@demo.focus360.ai', 'docente123', school_id=school.id, plesso_id=plesso_succursale.id, role='docente', surname='Arena', name='Francesca', discipline='Educazione civica', class_name='4B INF', phone='0900000104'),
    ]

    classes = ['3A INF','3B INF','4A INF','4B INF','5A INF']
    nomi = ['Luca','Giulia','Alessandro','Martina','Salvatore','Chiara','Davide','Sofia','Andrea','Elisa','Gabriele','Sara','Francesco','Noemi','Matteo','Aurora','Simone','Alessia','Marco','Federica']
    cognomi = ['Rizzo','Messina','Conti','Lombardo','Grasso','Ferrara','Marino','Caruso','De Luca','Costa','Russo','Parisi','Foti','Amato','Longo','Puglisi','Vitale','Romano','Giordano','Barresi']
    studenti=[]
    idx=1
    for c in classes:
        for i in range(8):
            name = nomi[(idx+i) % len(nomi)]
            surname = cognomi[(idx*2+i) % len(cognomi)]
            email = 'studente@demo.focus360.ai' if idx == 1 else f'studente{idx:03d}@demo.focus360.ai'
            pwd = 'studente123' if idx == 1 else 'studenti123'
            st = upsert_user(email, pwd, school_id=school.id, plesso_id=(plesso_centrale.id if c in ['3A INF','4A INF','5A INF'] else plesso_succursale.id), role='studente', surname=surname, name=name, class_name=c, birthdate=f'200{random.randint(7,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}', phone=f'333000{idx:04d}')
            studenti.append(st)
            parent_email = 'genitore@demo.focus360.ai' if idx == 1 else f'genitore.studente{idx:03d}@demo.focus360.ai'
            parent_pwd = 'genitore123' if idx == 1 else 'genitori123'
            upsert_user(parent_email, parent_pwd, school_id=school.id, plesso_id=st.plesso_id, parent_student_id=st.id, role='genitore', surname='Genitore', name=f'{name} {surname}', class_name=c, phone=f'333900{idx:04d}')
            idx += 1
    db.session.flush()

    # Smart locker / phone box demo
    for c in classes:
        for n in range(1, 7):
            db.session.add(SmartLocker(school_id=school.id, class_name=c, box_code=f'{c.replace(" ","")}-BOX-{n:02d}', status=random.choice(['libero','occupato','libero','manutenzione'])))

    # Lezioni e record focus ultimi 7 giorni
    subjects = ['Informatica','Sistemi e reti','Matematica','Inglese','Educazione civica']
    for day in range(7):
        lesson_date = datetime.utcnow() - timedelta(days=day)
        for ci, c in enumerate(classes):
            teacher = docenti[ci % len(docenti)]
            subject = subjects[ci % len(subjects)]
            raw = secrets.token_urlsafe(16)
            lesson = Lesson(school_id=school.id, plesso_id=(plesso_centrale.id if c in ['3A INF','4A INF','5A INF'] else plesso_succursale.id), teacher_id=teacher.id, class_name=c, subject=subject, started_at=lesson_date.replace(hour=8+(ci%5), minute=0, second=0, microsecond=0), duration_minutes=60, qr_token_hash=sha(raw), qr_expires_at=lesson_date+timedelta(minutes=10), status='chiusa')
            db.session.add(lesson); db.session.flush()
            class_students=[s for s in studenti if s.class_name==c]
            for st in class_students:
                # andamento realistico: molte sessioni positive, alcune violazioni
                exited = 1 if random.random() < (0.04 + ci*0.01) else 0
                social = 1 if random.random() < (0.06 + ci*0.015) else 0
                screen = random.randint(0, 8) if not (exited or social) else random.randint(12, 42)
                minutes = 60 if not (exited or social) else random.randint(25, 55)
                rec = FocusRecord(lesson_id=lesson.id, student_id=st.id, minutes_focus=minutes, focus_active=(minutes>=60 and exited==0 and social==0), violations=exited+social, opened_social=social, exited_app=exited, screen_minutes=screen)
                rec.points=calc_points(rec.minutes_focus,60,rec.exited_app,rec.opened_social,rec.screen_minutes)
                rec.tokens=1 if rec.focus_active else 0
                payload={'demo':True,'student':st.email,'lesson':lesson.id,'points':rec.points,'tokens':rec.tokens,'minutes':rec.minutes_focus}
                rec.blockchain_hash=write_chain(school.id,'DEMO_FOCUS_RECORD',payload)
                db.session.add(rec)

    db.session.flush()
    # Badge, consensi, wellbeing, passport
    categories = [
        ('Digital Citizenship','Uso consapevole dello smartphone e netiquette',2,85),
        ('Cybersecurity','Password sicure, phishing e protezione account',3,88),
        ('AI Literacy','Uso responsabile dell’intelligenza artificiale generativa',3,90),
        ('Educazione Civica','Benessere digitale, diritti e doveri online',4,86),
        ('PCTO','Laboratorio Focus360: progettazione dashboard e dati',10,92),
        ('Soft Skills','Collaborazione, responsabilità e leadership positiva',2,84),
    ]
    for st in studenti:
        # consensi
        db.session.add(ParentConsent(school_id=school.id, student_id=st.id, signed_by='Genitore demo', consent_focus=True, consent_analytics=True, consent_badge=True))
        # check-in benessere
        for _ in range(3):
            db.session.add(WellbeingSurvey(school_id=school.id, student_id=st.id, stress_level=random.randint(1,4), perceived_attention=random.randint(3,5), sleep_quality=random.randint(3,5), note='Check-in demo benessere digitale.'))
        # passport items
        for cat, title, hours, score in random.sample(categories, k=random.randint(3,6)):
            payload={'demo':True,'student':st.email,'category':cat,'title':title,'score':score}
            h=write_chain(school.id,'DEMO_PASSPORT_ITEM',payload)
            db.session.add(PortfolioItem(school_id=school.id, student_id=st.id, category=cat, title=title, description='Attività validata nell’ambiente demo Focus360 AI Enterprise.', hours=hours, score=score, validator='Portfolio Manager Demo', evidence_hash=h))
        # badge per i più virtuosi
        if random.random() < 0.65:
            for badge_name in random.sample(['Digital Citizen Bronze','Focus Champion','AI Innovator','Cybersecurity Explorer','Classe 100% Focus'], k=random.randint(1,3)):
                payload={'demo':True,'student':st.email,'badge':badge_name}
                nft=write_chain(school.id,'DEMO_BADGE_NFT',payload)
                db.session.add(Badge(school_id=school.id, user_id=st.id, class_name=st.class_name, name=badge_name, description='Badge NFT educativo non speculativo generato per demo commerciale.', nft_hash=nft))

    db.session.add(PaymentRecord(school_id=school.id, invoice_number='F360-DEMO-001', amount=7490, method='MEPA / bonifico', status='pagato', due_date=date.today()+timedelta(days=30), paid_at=datetime.utcnow(), note='Licenza Enterprise/PNRR demo annuale.'))
    db.session.add(InterventionPlan(school_id=school.id, class_name='4B INF', title='Riduzione distrazione fascia 11:00-12:00', owner='Dirigente Demo', status='aperto', action='Attivare micro-pause, attività cooperative e monitoraggio Focus collettivo al 90%.'))
    db.session.add(InterventionPlan(school_id=school.id, class_name='3A INF', title='Educazione civica digitale', owner='Docente Demo', status='in corso', action='Percorso su notifiche, attenzione, dipendenza digitale e gestione consapevole dello smartphone.'))
    db.session.commit()
    return school, 'created'

@app.route('/superadmin/create-demo', methods=['POST'])
@login_required('superadmin')
def create_demo_route():
    reset = bool(request.form.get('reset'))
    school, status = create_demo_environment(reset=reset)
    if status == 'already_exists':
        flash('Ambiente demo già presente. Usa “Rigenera demo” per ricrearlo da zero.', 'info')
    else:
        flash('Ambiente demo Enterprise creato con utenti, classi, report, Wellness Score ed Educational Passport.', 'success')
    return redirect(url_for('dashboard_superadmin'))


def ensure_demo_plessi():
    demo = School.query.filter_by(tenant_slug='demo-focus360-enterprise').first()
    if not demo:
        return
    # Versione Alpha: Demo Enterprise con lockers, API e registro attivi di default.
    demo.modules_disabled = ''
    demo.smart_locker_enabled = True
    if not Plesso.query.filter_by(school_id=demo.id).first():
        centrale = Plesso(school_id=demo.id, name='Sede centrale', code='CENTRALE', city=demo.city or 'Barcellona Pozzo di Gotto', address=demo.address or 'Via Innovazione Digitale 1', referent='Dirigente Demo', email='centrale@demo.focus360.ai', phone='0900000000')
        succ = Plesso(school_id=demo.id, name='Succursale Tecnologica', code='SUCC-TECH', city=demo.city or 'Barcellona Pozzo di Gotto', address='Via Laboratori 12', referent='Prof. Marco Rossi', email='succursale@demo.focus360.ai', phone='0900000002')
        db.session.add_all([centrale, succ]); db.session.flush()
        for u in User.query.filter_by(school_id=demo.id).all():
            u.plesso_id = centrale.id if (u.class_name in [None,'','3A INF','4A INF','5A INF'] or u.role=='dirigente') else succ.id
        for l in Lesson.query.filter_by(school_id=demo.id).all():
            l.plesso_id = centrale.id if l.class_name in ['3A INF','4A INF','5A INF'] else succ.id
    db.session.commit()

@app.cli.command('init-db')
def init_db_cmd():
    init_db(); print('Database inizializzato')

def ensure_runtime_columns():
    # Piccola migrazione prototipo per database SQLite/PostgreSQL già esistenti.
    engine_name = db.engine.url.get_backend_name()
    stmts = []
    if engine_name.startswith('sqlite'):
        stmts = [
            "ALTER TABLE user ADD COLUMN temporary_password VARCHAR(80)",
            "ALTER TABLE user ADD COLUMN must_change_password BOOLEAN DEFAULT 1",
            "ALTER TABLE user ADD COLUMN parent_student_id INTEGER",
            "ALTER TABLE user ADD COLUMN plesso_id INTEGER",
            "ALTER TABLE lesson ADD COLUMN plesso_id INTEGER",
            "ALTER TABLE school ADD COLUMN modules_enabled TEXT DEFAULT ''",
            "ALTER TABLE school ADD COLUMN modules_disabled TEXT DEFAULT ''",
            "ALTER TABLE school ADD COLUMN smart_locker_enabled BOOLEAN DEFAULT 1",
            "ALTER TABLE school ADD COLUMN last_expiry_notice_at DATETIME"
        ]
    else:
        stmts = [
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS temporary_password VARCHAR(80)',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT TRUE',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS parent_student_id INTEGER',
            'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS plesso_id INTEGER',
            'ALTER TABLE lesson ADD COLUMN IF NOT EXISTS plesso_id INTEGER',
            "ALTER TABLE school ADD COLUMN IF NOT EXISTS modules_enabled TEXT DEFAULT ''",
            "ALTER TABLE school ADD COLUMN IF NOT EXISTS modules_disabled TEXT DEFAULT ''",
            'ALTER TABLE school ADD COLUMN IF NOT EXISTS smart_locker_enabled BOOLEAN DEFAULT TRUE',
            'ALTER TABLE school ADD COLUMN IF NOT EXISTS last_expiry_notice_at TIMESTAMP'
        ]
    for stmt in stmts:
        try:
            db.session.execute(text(stmt))
            db.session.commit()
        except Exception:
            db.session.rollback()

def init_db():
    db.create_all()
    ensure_runtime_columns()
    if not User.query.filter_by(email='superadmin@focus360.ai').first():
        su=User(role='superadmin', surname='Super', name='Admin', email='superadmin@focus360.ai', password_hash=generate_password_hash('admin123'), temporary_password='', must_change_password=False)
        db.session.add(su)
        db.session.commit()
    else:
        db.session.commit()
    # Mantiene sempre una sola scuola Demo visibile nella console SuperAdmin.
    if not School.query.filter_by(tenant_slug='demo-focus360-enterprise').first():
        create_demo_environment(reset=False)
    ensure_demo_plessi()

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
