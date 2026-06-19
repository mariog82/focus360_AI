
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    codice_meccanografico = db.Column(db.String(32), unique=True, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(20), nullable=False)
    legal_email = db.Column(db.String(160), nullable=False)
    plan = db.Column(db.String(30), default='base')
    status = db.Column(db.String(30), default='active')
    subscription_expiry = db.Column(db.Date, nullable=True)
    modules_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(30), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    must_change_password = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(40))
    class_name = db.Column(db.String(30))
    plesso_code = db.Column(db.String(50))
    parent_student_id = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=True)

class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, nullable=False)
    class_name = db.Column(db.String(30), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    qr_token = db.Column(db.String(120), unique=True, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)

class FocusEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(40), nullable=False)
    minutes = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WellnessScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default=70)
    focus_continuity = db.Column(db.Integer, default=70)
    digital_discipline = db.Column(db.Integer, default=70)
    consistency = db.Column(db.Integer, default=70)
    collaborative_focus = db.Column(db.Integer, default=70)
    digital_citizenship = db.Column(db.Integer, default=70)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PassportItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    hours = db.Column(db.Integer, default=0)
    validator = db.Column(db.String(120), default='Focus360 AI')
    evidence_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=True)
    actor = db.Column(db.String(160))
    action = db.Column(db.String(120), nullable=False)
    target = db.Column(db.String(160))
    record_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
