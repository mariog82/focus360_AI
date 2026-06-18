
from flask import request, jsonify
from datetime import date, datetime
from shared.app_factory import create_service_app
from shared.models import Tenant
app=create_service_app('billing-service')
@app.get('/billing/expiring')
def expiring():
    out=[]
    for t in Tenant.query.all():
        out.append({'tenant_id':t.id,'name':t.name,'expiry':str(t.subscription_expiry),'status':t.status})
    return jsonify(out)
@app.post('/billing/send-expiry-email')
def send_expiry_email():
    d=request.json or {}; return jsonify({'status':'email_queued_prototype','tenant_id':d.get('tenant_id')})
