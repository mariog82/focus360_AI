
from flask import jsonify
from shared.app_factory import create_service_app
app=create_service_app('compliance-service')
@app.get('/compliance/checklist')
def checklist():
    return jsonify({'GDPR':['data minimization','access control','audit logging','export/erasure workflow to implement in production'],'CAD_AGID':['digital service availability','auditability','cloud qualification checklist'],'NIS2':['risk management','incident reporting process','supply-chain security'],'DevSecOps':['SAST','dependency check','container scan','DAST/pentest']})
