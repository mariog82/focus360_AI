
def test_auth_health():
    from services.auth_service.app import app
    c=app.test_client(); r=c.get('/health')
    assert r.status_code==200
    assert r.json['status']=='ok'

def test_tenant_required_fields():
    from services.tenant_service.app import app
    c=app.test_client(); r=c.post('/tenants', json={'name':'Istituto incompleto'})
    assert r.status_code==400
    assert 'fields' in r.json
