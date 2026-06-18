
from flask import request, jsonify
from shared.app_factory import create_service_app
from shared.models import db, User
from shared.security import hash_password, verify_password, generate_token
app=create_service_app('auth-service')
@app.post('/auth/login')
def login():
    data=request.json or {}; u=User.query.filter_by(email=data.get('email')).first()
    if not u or not verify_password(u.password_hash, data.get('password','')) or not u.active: return jsonify({'error':'invalid credentials'}),401
    return jsonify({'user_id':u.id,'role':u.role,'tenant_id':u.tenant_id,'must_change_password':u.must_change_password})
@app.post('/auth/users')
def create_user():
    data=request.json or {}; pwd=data.get('password') or generate_token('TMP')
    u=User(role=data['role'],surname=data['surname'],name=data['name'],email=data['email'],tenant_id=data.get('tenant_id'),phone=data.get('phone'),class_name=data.get('class_name'),plesso_code=data.get('plesso_code'),parent_student_id=data.get('parent_student_id'),password_hash=hash_password(pwd),must_change_password=True)
    db.session.add(u); db.session.commit(); return jsonify({'id':u.id,'email':u.email,'temporary_password':pwd}),201
@app.put('/auth/users/<int:user_id>')
def edit_user(user_id):
    u=User.query.get_or_404(user_id); data=request.json or {}
    for k in ['surname','name','phone','class_name','plesso_code','active']:
        if k in data: setattr(u,k,data[k])
    db.session.commit(); return jsonify({'status':'updated'})
