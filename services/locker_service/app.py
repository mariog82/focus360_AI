
from flask import request, jsonify
from shared.app_factory import create_service_app
from shared.models import db, AuditLog
from shared.security import require_internal_api_key, sha256_record
app=create_service_app('locker-service')
@app.post('/lockers/event')
@require_internal_api_key
def locker_event():
    d=request.json or {}; h=sha256_record(str(d)); log=AuditLog(tenant_id=d.get('tenant_id'),actor=d.get('student_email'),action='locker_'+d.get('event','unknown'),target=d.get('box_code'),record_hash=h)
    db.session.add(log); db.session.commit(); return jsonify({'status':'accepted','hash':h})
