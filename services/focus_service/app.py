
from flask import request, jsonify
from shared.app_factory import create_service_app
from shared.models import db, FocusSession, FocusEvent
from shared.security import generate_token
app=create_service_app('focus-service')
@app.post('/focus/sessions')
def start_session():
    d=request.json or {}; s=FocusSession(tenant_id=d['tenant_id'],teacher_id=d['teacher_id'],class_name=d['class_name'],subject=d['subject'],qr_token=generate_token('QR'))
    db.session.add(s); db.session.commit(); return jsonify({'session_id':s.id,'qr_token':s.qr_token}),201
@app.post('/focus/join')
def join():
    d=request.json or {}; s=FocusSession.query.filter_by(qr_token=d.get('qr_token'),active=True).first_or_404()
    e=FocusEvent(session_id=s.id,student_id=d['student_id'],event_type='focus_started',points=0)
    db.session.add(e); db.session.commit(); return jsonify({'status':'focus_ready','session_id':s.id})
@app.post('/focus/complete')
def complete():
    d=request.json or {}; e=FocusEvent(session_id=d['session_id'],student_id=d['student_id'],event_type='focus_completed',minutes=d.get('minutes',60),points=10)
    db.session.add(e); db.session.commit(); return jsonify({'points':10,'token':1})
