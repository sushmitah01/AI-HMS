from tests.conftest import auth_header


def test_register_patient_success(client):
    resp = client.post('/api/auth/register', json={
        'username': 'Jane Doe',
        'email': 'jane@test.com',
        'password': 'StrongPass1!',
        'mobile': '+15551234567',
        'role': 'Patient',
    })
    assert resp.status_code == 201


def test_register_weak_password_rejected(client):
    resp = client.post('/api/auth/register', json={
        'username': 'Jane Doe',
        'email': 'jane2@test.com',
        'password': 'weak',
        'mobile': '+15551234567',
        'role': 'Patient',
    })
    assert resp.status_code == 400


def test_register_staff_without_whitelist_is_rejected(client):
    """A Doctor/Receptionist/Admin signup must be pre-approved via the
    staff whitelist; anonymous self-registration as staff must fail."""
    resp = client.post('/api/auth/register', json={
        'username': 'Fake Doctor',
        'email': 'fakedoc@test.com',
        'password': 'StrongPass1!',
        'mobile': '+15551234567',
        'role': 'Doctor',
    })
    assert resp.status_code == 403


def test_login_wrong_password_rejected(client):
    client.post('/api/auth/register', json={
        'username': 'Jane Doe',
        'email': 'jane3@test.com',
        'password': 'StrongPass1!',
        'mobile': '+15551234567',
        'role': 'Patient',
    })
    resp = client.post('/api/auth/login', json={'email': 'jane3@test.com', 'password': 'WrongPass1!'})
    assert resp.status_code == 401


def test_users_list_requires_auth(client):
    """Regression test: this endpoint used to have no auth check at all."""
    resp = client.get('/api/users')
    assert resp.status_code == 401


def test_users_list_requires_admin_role(client, patient_token):
    resp = client.get('/api/users', headers=auth_header(patient_token))
    assert resp.status_code == 403


def test_users_list_allowed_for_admin(client, admin_token):
    resp = client.get('/api/users', headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_delete_user_requires_auth(client, patient_token):
    """Regression test: DELETE /users/<id> used to have no auth check."""
    resp = client.delete('/api/users/1')
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get('/api/auth/me')
    assert resp.status_code == 401


def test_me_returns_profile_for_valid_token(client, patient_token):
    resp = client.get('/api/auth/me', headers=auth_header(patient_token))
    assert resp.status_code == 200
    assert resp.get_json()['role'] == 'Patient'
