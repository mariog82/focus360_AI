
def test_focus_session_flow():
    from services.focus_service.app import app
    c=app.test_client()
    r=c.post('/focus/sessions', json={'tenant_id':1,'teacher_id':2,'class_name':'3A','subject':'Informatica'})
    assert r.status_code==201
    token=r.json['qr_token']
    r2=c.post('/focus/join', json={'qr_token':token,'student_id':3})
    assert r2.status_code==200
    r3=c.post('/focus/complete', json={'session_id':r.json['session_id'],'student_id':3,'minutes':60})
    assert r3.json['points']==10

def test_passport_export():
    from services.auth_service.app import app as auth_app
    from services.passport_service.app import app as pass_app
    a=auth_app.test_client(); p=pass_app.test_client()
    u=a.post('/auth/users', json={'role':'studente','surname':'Rossi','name':'Luca','email':'luca@test.it','password':'x'}).json
    r=p.post(f"/passport/{u['id']}/items", json={'category':'Educazione Civica','title':'Benessere digitale','hours':2})
    assert r.status_code==201
    dl=p.get(f"/passport/{u['id']}/download")
    assert dl.status_code==200
