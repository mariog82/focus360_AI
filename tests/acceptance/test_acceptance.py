
def test_acceptance_superadmin_creates_school_and_student_focus():
    from services.tenant_service.app import app as tenant_app
    from services.auth_service.app import app as auth_app
    tc=tenant_app.test_client(); ac=auth_app.test_client()
    school=tc.post('/tenants', json={'name':'IIS Demo','codice_meccanografico':'MEIS000001','city':'Messina','province':'ME','legal_email':'scuola@example.it','plan':'enterprise'}).json
    assert school['id']
    user=ac.post('/auth/users', json={'role':'studente','surname':'Bianchi','name':'Anna','email':'anna@example.it','tenant_id':school['id']}).json
    assert user['temporary_password']
