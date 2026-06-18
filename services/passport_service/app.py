
from flask import request, jsonify, Response
from shared.app_factory import create_service_app
from shared.models import db, PassportItem, User
from shared.security import sha256_record
app=create_service_app('passport-service')
@app.post('/passport/<int:student_id>/items')
def add_item(student_id):
    d=request.json or {}; evidence=sha256_record(str(d)); item=PassportItem(student_id=student_id,category=d['category'],title=d['title'],hours=d.get('hours',0),validator=d.get('validator','Focus360 AI'),evidence_hash=evidence)
    db.session.add(item); db.session.commit(); return jsonify({'id':item.id,'hash':evidence}),201
@app.get('/passport/<int:student_id>')
def passport(student_id):
    u=User.query.get_or_404(student_id); items=PassportItem.query.filter_by(student_id=student_id).all()
    return jsonify({'student':u.email,'items':[{'category':i.category,'title':i.title,'hours':i.hours,'hash':i.evidence_hash} for i in items]})
@app.get('/passport/<int:student_id>/download')
def download(student_id):
    payload=f'Focus360 AI Educational Passport - studente {student_id}\nDocumento prototipo esportabile.'
    return Response(payload, mimetype='text/plain', headers={'Content-Disposition':f'attachment; filename=passport_{student_id}.txt'})
