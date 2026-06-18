
from flask import Flask, jsonify, request
import os, requests
app=Flask(__name__)
SERVICES={
 'auth':os.getenv('AUTH_URL','http://auth-service:8000'),
 'tenant':os.getenv('TENANT_URL','http://tenant-service:8000'),
 'focus':os.getenv('FOCUS_URL','http://focus-service:8000'),
 'wellness':os.getenv('WELLNESS_URL','http://wellness-service:8000'),
 'passport':os.getenv('PASSPORT_URL','http://passport-service:8000'),
 'locker':os.getenv('LOCKER_URL','http://locker-service:8000'),
 'registry':os.getenv('REGISTRY_URL','http://registry-service:8000'),
 'billing':os.getenv('BILLING_URL','http://billing-service:8000'),
 'compliance':os.getenv('COMPLIANCE_URL','http://compliance-service:8000')
}
@app.get('/health')
def health(): return jsonify({'gateway':'ok','services':SERVICES})
@app.route('/api/<service>/<path:path>', methods=['GET','POST','PUT','DELETE'])
def proxy(service,path):
    if service not in SERVICES: return jsonify({'error':'unknown service'}),404
    url=f"{SERVICES[service]}/{path}"
    r=requests.request(request.method,url,json=request.get_json(silent=True),headers={'X-Internal-API-Key':os.getenv('INTERNAL_API_KEY','dev-internal-key-change-me')})
    return (r.content,r.status_code,r.headers.items())
