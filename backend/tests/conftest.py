import os
import tempfile

import pytest

# Point the app at a fresh temp sqlite file *before* importing app.py,
# since Config reads DATABASE_URL at import time.
_db_fd, _db_path = tempfile.mkstemp(suffix='.db')
os.environ['DATABASE_URL'] = f'sqlite:///{_db_path}'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ.setdefault('GEMINI_API_KEY', '')

from app import create_app  # noqa: E402
from models import db  # noqa: E402
from models.user import User  # noqa: E402
from models.doctor import Doctor  # noqa: E402
from models.patient import Patient  # noqa: E402


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register_and_login(client, role, email, password="Password1!", extra=None):
    """Create a user directly in the DB (bypassing whitelist rules, since
    that's its own tested flow) and return a valid JWT for them."""
    from app import db as _db  # already bound

    with client.application.app_context():
        user = User(username=f"{role} Test", email=email, mobile="+10000000000", role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        if role == 'Patient':
            patient = Patient(
                user_id=user_id,
                first_name="Test",
                last_name="Patient",
                dob=__import__("datetime").date(1990, 1, 1),
                gender="Other",
                contact_number="+10000000000",
                email=email,
            )
            db.session.add(patient)
        elif role == 'Doctor':
            doctor = Doctor(
                user_id=user_id,
                name=f"Dr. {role}",
                specialization="General Practitioner",
                gender="Other",
            )
            db.session.add(doctor)

        db.session.commit()

    resp = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()['token']


@pytest.fixture()
def admin_token(client):
    return _register_and_login(client, 'Admin', 'admin@test.com')


@pytest.fixture()
def doctor_token(client):
    return _register_and_login(client, 'Doctor', 'doctor@test.com')


@pytest.fixture()
def receptionist_token(client):
    return _register_and_login(client, 'Receptionist', 'reception@test.com')


@pytest.fixture()
def patient_token(client):
    return _register_and_login(client, 'Patient', 'patient@test.com')


def auth_header(token):
    return {'Authorization': f'Bearer {token}'}
