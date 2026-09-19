from tests.conftest import auth_header


def test_predict_risk_requires_auth(client):
    resp = client.post('/api/predict/risk', json={'age': 65, 'sys_bp': 150, 'dia_bp': 95, 'heart_rate': 88})
    assert resp.status_code == 401


def test_predict_risk_forbidden_for_patient_role(client, patient_token):
    resp = client.post(
        '/api/predict/risk',
        json={'age': 65, 'sys_bp': 150, 'dia_bp': 95, 'heart_rate': 88},
        headers=auth_header(patient_token),
    )
    assert resp.status_code == 403


def test_predict_risk_succeeds_for_doctor(client, doctor_token):
    """This hits the local scikit-learn model only (no external API call),
    so it's safe to run for real in CI."""
    resp = client.post(
        '/api/predict/risk',
        json={'age': 72, 'sys_bp': 160, 'dia_bp': 100, 'heart_rate': 105},
        headers=auth_header(doctor_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()['risk_level'] in ('Low', 'Medium', 'High')


def test_predict_readmission_succeeds_for_admin(client, admin_token):
    resp = client.post(
        '/api/predict/readmission',
        json={'age': 75, 'prev_visits': 8, 'chronic': 1, 'days_since': 10},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert 0.0 <= resp.get_json()['readmission_probability'] <= 100.0


def test_predict_disease_requires_auth(client):
    """Gemini-backed route: only checking the auth gate here, since actually
    calling out to the Gemini API requires a real key and network access."""
    resp = client.post('/api/predict/disease', json={'symptoms': 'fever, cough'})
    assert resp.status_code == 401


def test_predict_disease_forbidden_for_receptionist(client, receptionist_token):
    resp = client.post(
        '/api/predict/disease',
        json={'symptoms': 'fever, cough'},
        headers=auth_header(receptionist_token),
    )
    assert resp.status_code == 403


def test_system_report_requires_admin(client, doctor_token):
    """Regression test: /ai/system-report leaks hospital-wide counts and
    must be Admin-only."""
    resp = client.get('/api/ai/system-report', headers=auth_header(doctor_token))
    assert resp.status_code == 403


def test_patient_chat_requires_auth(client):
    """Regression test: this endpoint used to hardcode user_id=1 for every
    caller and had no auth check."""
    resp = client.post('/api/chat', json={'message': 'hello'})
    assert resp.status_code == 401


def test_patient_chat_uses_real_caller_identity(client, patient_token):
    resp = client.post('/api/chat', json={'message': 'hello'}, headers=auth_header(patient_token))
    assert resp.status_code == 200
