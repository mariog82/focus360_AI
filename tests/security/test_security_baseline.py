
def test_locker_requires_internal_key():
    from services.locker_service.app import app
    c=app.test_client()
    r=c.post('/lockers/event', json={'event':'deposit','student_email':'s@test.it'})
    assert r.status_code==401

def test_password_is_hashed_not_plaintext():
    from shared.security import hash_password
    h=hash_password('Password123!')
    assert h != 'Password123!'
    assert 'Password123!' not in h
