
from flask import request, jsonify
from shared.app_factory import create_service_app
from shared.models import db, Tenant
app=create_service_app('tenant-service')
REQUIRED=['name','codice_meccanografico','city','province','legal_email']
@app.post('/tenants')
def create_tenant():
    data=request.json or {}; missing=[x for x in REQUIRED if not data.get(x)]
    if missing: return jsonify({'error':'missing required fields','fields':missing}),400
    t=Tenant(name=data['name'],codice_meccanografico=data['codice_meccanografico'],city=data['city'],province=data['province'],legal_email=data['legal_email'],plan=data.get('plan','base'),subscription_expiry=data.get('subscription_expiry'))
    db.session.add(t); db.session.commit(); return jsonify({'id':t.id}),201
@app.get('/tenants')
def list_tenants():
    return jsonify([{'id':t.id,'name':t.name,'code':t.codice_meccanografico,'plan':t.plan,'status':t.status} for t in Tenant.query.distinct(Tenant.codice_meccanografico).all()])
@app.put('/tenants/<int:tenant_id>')
def edit_tenant(tenant_id):
    t=Tenant.query.get_or_404(tenant_id); data=request.json or {}
    for k in ['name','city','province','legal_email','plan','status','subscription_expiry','modules_json']:
        if k in data: setattr(t,k,data[k])
    db.session.commit(); return jsonify({'status':'updated'})
