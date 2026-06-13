import os, csv, io, secrets, string, hashlib, json
from datetime import datetime, timedelta, date
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
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
    'BASE': {'name':'Pacchetto Base', 'modules':'App focus, QR docente, dashboard, report CSV', 'price':'€ 990/anno'},
    'PRO': {'name':'Pacchetto Pro', 'modules':'AI analytics, gamification, ranking scuole, benessere digitale', 'price':'€ 2.490/anno'},
    'ENTERPRISE': {'name':'Enterprise/PNRR', 'modules':'Armadietti smart, blockchain badge, report ministeriali, registro elettronico, API', 'price':'su preventivo'}
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
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
    school = db.relationship('School', backref='users')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
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


def current_user():
    uid = session.get('uid')
    return User.query.get(uid) if uid else None

@app.context_processor
def inject_user():
    return {'me': current_user(), 'plans': PLANS, 'APP_NAME': APP_NAME}

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

def plan_enabled(school, feature):
    matrix={
        'BASE': {'qr','dashboard','csv'},
        'PRO': {'qr','dashboard','csv','ai','gamification','wellbeing','ranking'},
        'ENTERPRISE': {'qr','dashboard','csv','ai','gamification','wellbeing','ranking','blockchain','lockers','api','registro'}
    }
    return feature in matrix.get((school.plan if school else 'BASE'), set())

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
            session['uid']=u.id; return redirect(url_for('index'))
        flash('Credenziali non valide','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/superadmin', methods=['GET','POST'])
@login_required('superadmin')
def dashboard_superadmin():
    if request.method=='POST':
        school=School(name=request.form['name'], codice_meccanografico=request.form.get('codice'), city=request.form.get('city'), address=request.form.get('address'), fiscal_code=request.form.get('fiscal_code'), pec=request.form.get('pec'), billing_email=request.form.get('billing_email'), plan=request.form.get('plan','BASE'), payment_status=request.form.get('payment_status','in_attesa'), payment_method=request.form.get('payment_method','bonifico'))
        db.session.add(school); db.session.commit()
        pwd=random_password()
        dirigente=User(school_id=school.id, role='dirigente', surname=request.form.get('ds_surname','Dirigente'), name=request.form.get('ds_name','Scolastico'), email=request.form['ds_email'].lower(), password_hash=generate_password_hash(pwd))
        db.session.add(dirigente); db.session.commit()
        flash(f'Istituto creato. Credenziali dirigente: {dirigente.email} / {pwd}','success')
    schools=School.query.order_by(School.id.desc()).all()
    return render_template('superadmin.html', schools=schools, payments=PaymentRecord.query.order_by(PaymentRecord.id.desc()).limit(10).all())

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
    return render_template('dirigente.html', teachers=teachers, students=students, records=records, total_tokens=total_tokens, violations=violations, class_stats=class_stats, ai_risk=ai_risk, att_index=att_index, wellbeing_rows=wellbeing_rows, wellness_school=wellness_school)

@app.route('/upload/<kind>', methods=['GET','POST'])
@login_required(['dirigente','docente'])
def upload(kind):
    me=current_user()
    if kind=='docenti' and me.role!='dirigente':
        flash('Solo il dirigente può caricare docenti','danger'); return redirect(url_for('index'))
    created=[]
    if request.method=='POST':
        f=request.files.get('csvfile')
        text=f.read().decode('utf-8-sig')
        reader=csv.DictReader(io.StringIO(text), delimiter=';')
        for row in reader:
            email=(row.get('mail') or row.get('email') or '').strip().lower()
            if not email or User.query.filter_by(email=email).first(): continue
            pwd=random_password()
            role='docente' if kind=='docenti' else 'studente'
            u=User(school_id=me.school_id, role=role, surname=row.get('cognome',''), name=row.get('nome',''), email=email, phone=row.get('telefono',''), password_hash=generate_password_hash(pwd), discipline=row.get('disciplina',''), class_name=row.get('classe',''), birthdate=row.get('data di nascita',''))
            db.session.add(u); db.session.flush(); created.append((u.email,pwd,u.role,u.class_name))
            if role=='studente':
                p_email=f"genitore.{u.email}"
                if not User.query.filter_by(email=p_email).first():
                    g=User(school_id=me.school_id, role='genitore', surname='Genitore', name=f'{u.name} {u.surname}', email=p_email, password_hash=generate_password_hash(pwd), class_name=u.class_name)
                    db.session.add(g)
        db.session.commit()
        return render_template('upload_result.html', created=created)
    return render_template('upload.html', kind=kind)

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

@app.route('/scan/<int:lesson_id>/<token>')
@login_required(['studente'])
def scan_focus(lesson_id, token):
    me=current_user(); l=Lesson.query.get_or_404(lesson_id)
    if datetime.utcnow()>l.qr_expires_at or sha(token)!=l.qr_token_hash:
        flash('QR scaduto o non valido','danger'); return redirect(url_for('dashboard_studente'))
    if me.class_name != l.class_name:
        flash('QR non associato alla tua classe','danger'); return redirect(url_for('dashboard_studente'))
    r=FocusRecord.query.filter_by(lesson_id=l.id, student_id=me.id).first()
    if not r:
        r=FocusRecord(lesson_id=l.id, student_id=me.id, minutes_focus=0)
        db.session.add(r); db.session.commit()
    flash('Modalità Focus attivata. In prototipo il blocco app è simulato; su mobile richiede integrazione nativa Android/iOS.','success')
    return redirect(url_for('focus_session', record_id=r.id))

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
    risk=focus_risk_score(records); att_index=attention_index(records); surveys=WellbeingSurvey.query.filter_by(student_id=me.id).order_by(WellbeingSurvey.id.desc()).limit(3).all(); passport=educational_passport(me)
    return render_template('studente.html', records=records, badges=badges, risk=risk, att_index=att_index, surveys=surveys, passport=passport, wellness=passport['wellness'])

@app.route('/genitore')
@login_required('genitore')
def dashboard_genitore():
    me=current_user(); child_email=me.email.replace('genitore.','',1)
    child=User.query.filter_by(email=child_email).first()
    records=FocusRecord.query.filter_by(student_id=child.id).order_by(FocusRecord.id.desc()).all() if child else []
    return render_template('genitore.html', child=child, records=records)



@app.route('/wellness-score')
@login_required(['dirigente','docente','studente','genitore'])
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
def my_passport():
    me=current_user()
    student=me if me.role=='studente' else User.query.filter_by(email=me.email.replace('genitore.','',1)).first()
    if not student:
        flash('Studente non trovato','warning'); return redirect(url_for('index'))
    return render_template('passport.html', data=educational_passport(student), can_add=False)

@app.route('/passport/<int:student_id>', methods=['GET','POST'])
@login_required(['dirigente','docente'])
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
def lockers():
    me=current_user()
    if request.method=='POST':
        box=SmartLocker(school_id=me.school_id, class_name=request.form.get('class_name'), box_code=request.form.get('box_code'), status=request.form.get('status','libero'))
        db.session.add(box); db.session.commit(); flash('Phone box / locker registrato','success')
    boxes=SmartLocker.query.filter_by(school_id=me.school_id).order_by(SmartLocker.class_name, SmartLocker.box_code).all()
    return render_template('lockers.html', boxes=boxes)

@app.route('/blockchain')
@login_required(['superadmin','dirigente'])
def blockchain():
    me=current_user()
    q=BlockchainEvent.query
    if me.role!='superadmin': q=q.filter_by(school_id=me.school_id)
    events=q.order_by(BlockchainEvent.id.desc()).limit(100).all()
    return render_template('blockchain.html', events=events)

@app.route('/api/v1/focus-summary')
@login_required(['dirigente','docente'])
def api_focus_summary():
    me=current_user(); q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    records=q.all()
    return jsonify({'app':APP_NAME,'records':len(records),'attention_index':attention_index(records),'risk_score':focus_risk_score(records),'tokens':sum(r.tokens for r in records),'violations':sum(r.violations for r in records)})

@app.route('/report.csv')
@login_required(['dirigente','docente'])
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
def api_analytics():
    me=current_user(); q=FocusRecord.query.join(Lesson)
    q=q.filter(Lesson.school_id==me.school_id) if me.role=='dirigente' else q.filter(Lesson.teacher_id==me.id)
    data={}
    for r in q.all():
        key=r.lesson.subject
        data.setdefault(key, {'points':0,'violations':0,'minutes':0,'n':0})
        data[key]['points']+=r.points; data[key]['violations']+=r.violations; data[key]['minutes']+=r.minutes_focus; data[key]['n']+=1
    return jsonify(data)


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
def interventi():
    me=current_user()
    if request.method=='POST':
        p=InterventionPlan(school_id=me.school_id, class_name=request.form.get('class_name'), title=request.form.get('title'), owner=f'{me.name} {me.surname}'.strip(), status=request.form.get('status','aperto'), action=request.form.get('action'))
        db.session.add(p); db.session.commit(); flash('Piano di intervento salvato','success')
    plans=InterventionPlan.query.filter_by(school_id=me.school_id).order_by(InterventionPlan.id.desc()).all()
    return render_template('interventi.html', plans=plans)

@app.route('/api/v1/device-event', methods=['POST'])
@login_required('studente')
def api_device_event():
    me=current_user(); data=request.get_json(silent=True) or {}
    weights={'exit_app':15,'social_open':25,'screen_on':5,'screenshot':10,'multitasking':15,'wifi_checkin':0,'nfc_checkin':0}
    ev_type=data.get('event_type','generic')
    ev=DeviceEvent(school_id=me.school_id, student_id=me.id, lesson_id=data.get('lesson_id'), event_type=ev_type, value=str(data.get('value','')), risk_weight=weights.get(ev_type,3), source=data.get('source','mobile_api'))
    db.session.add(ev); db.session.commit()
    return jsonify({'ok':True,'event_id':ev.id,'risk_weight':ev.risk_weight})

@app.cli.command('init-db')
def init_db_cmd():
    init_db(); print('Database inizializzato')

def init_db():
    db.create_all()
    if not User.query.filter_by(email='superadmin@focus360.ai').first():
        su=User(role='superadmin', surname='Super', name='Admin', email='superadmin@focus360.ai', password_hash=generate_password_hash('admin123'))
        db.session.add(su)
    db.session.commit()

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
