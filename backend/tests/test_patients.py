from tests.conftest import auth_header


PATIENT_PAYLOAD = {
    'first_name': 'Alice',
    'last_name': 'Smith',
    'dob': '1985-05-20',
    'gender': 'Female',
    'contact_number': '+15559990000',
    'email': 'alice.smith@gmail.com',
}


def test_get_patients_requires_auth(client):
    """Regression test: GET /patients used to have no auth check at all,
    exposing every patient's PII to anyone."""
    resp = client.get('/api/patients')
    assert resp.status_code == 401


def test_get_patients_allowed_for_any_logged_in_role(client, receptionist_token):
    resp = client.get('/api/patients', headers=auth_header(receptionist_token))
    assert resp.status_code == 200


def test_add_patient_requires_auth(client):
    resp = client.post('/api/patients', json=PATIENT_PAYLOAD)
    assert resp.status_code == 401


def test_add_patient_forbidden_for_patient_role(client, patient_token):
    """A plain Patient account should not be able to create arbitrary
    patient records for other people."""
    resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(patient_token))
    assert resp.status_code == 403


def test_add_patient_allowed_for_receptionist(client, receptionist_token):
    resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(receptionist_token))
    assert resp.status_code == 201


def test_delete_patient_requires_auth(client, receptionist_token):
    create_resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(receptionist_token))
    patient_id = create_resp.get_json()['patient']['id']

    resp = client.delete(f'/api/patients/{patient_id}')
    assert resp.status_code == 401


def test_delete_patient_forbidden_for_doctor(client, receptionist_token, doctor_token):
    """Regression test: previously any Admin/Receptionist could delete via an
    inline check, but Doctor was (correctly) never allowed - keep that rule."""
    create_resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(receptionist_token))
    patient_id = create_resp.get_json()['patient']['id']

    resp = client.delete(f'/api/patients/{patient_id}', headers=auth_header(doctor_token))
    assert resp.status_code == 403


def test_delete_patient_allowed_for_admin(client, receptionist_token, admin_token):
    create_resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(receptionist_token))
    patient_id = create_resp.get_json()['patient']['id']

    resp = client.delete(f'/api/patients/{patient_id}', headers=auth_header(admin_token))
    assert resp.status_code == 200


def test_update_patient_requires_auth(client, receptionist_token):
    create_resp = client.post('/api/patients', json=PATIENT_PAYLOAD, headers=auth_header(receptionist_token))
    patient_id = create_resp.get_json()['patient']['id']

    resp = client.put(f'/api/patients/{patient_id}', json={'first_name': 'Changed'})
    assert resp.status_code == 401
