from flask import Blueprint, request, jsonify
from models import db
from models.user import User
import jwt
import datetime
import re
from flask import current_app
from utils.auth import token_required, roles_required
from utils.limiter import limiter

auth_bp = Blueprint('auth_bp', __name__)

def validate_registration(data):
    # 1. Email Validation
    email = data.get('email', '')
    if '@' not in email or '.' not in email:
        return "Invalid email address format"

    # 2. Password Validation
    password = data.get('password', '')
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character"

    # 3. Mobile Validation
    mobile = data.get('mobile', '')
    # Check for country code (starts with +) and then digits
    if not re.match(r'^\+\d{1,4}\d{7,15}$', mobile):
        return "Mobile number must include country code (e.g., +1234567890)"

    return None

@auth_bp.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    
    # Validation logic
    error = validate_registration(data)
    if error:
        return jsonify({'error': error}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_role = data.get('role', 'Patient')
    whitelist_entry = None
    if new_role in ['Doctor', 'Receptionist', 'Admin']:
        from models.staff_whitelist import StaffWhitelist
        # Check by email or staff_id if provided
        whitelist_entry = StaffWhitelist.query.filter_by(email=data['email'], role=new_role).first()
        if not whitelist_entry and 'staff_id' in data:
            whitelist_entry = StaffWhitelist.query.filter_by(staff_id=data['staff_id'], role=new_role).first()
        
        if not whitelist_entry:
            return jsonify({'error': 'You are not authorized to register as hospital staff. Please contact the hospital administration.'}), 403
        
        if whitelist_entry.is_registered:
            return jsonify({'error': 'This staff record has already been used for registration.'}), 400

    try:
        new_user = User(
            username=data['username'],
            email=data['email'],
            mobile=data['mobile'],
            role=new_role
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.flush() # Flush to get new_user.id

        if whitelist_entry:
            whitelist_entry.is_registered = True

        if new_user.role == 'Patient':
            names = data['username'].strip().split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            from models.patient import Patient
            new_patient = Patient(
                user_id=new_user.id,
                first_name=first_name,
                last_name=last_name,
                dob=datetime.datetime.strptime('2000-01-01', '%Y-%m-%d').date(),
                gender=data.get('gender', 'Other'),
                contact_number=data['mobile'],
                email=data['email']
            )
            db.session.add(new_patient)
        elif new_user.role == 'Doctor':
            from models.doctor import Doctor
            new_doctor = Doctor(
                user_id=new_user.id,
                name=data['username'],
                specialization=data.get('specialization', 'General Practitioner'),
                gender=data.get('gender', 'Other'),
                contact=data['mobile']
            )
            db.session.add(new_doctor)

        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        user_data = user.to_dict()
        if user.role == 'Patient':
            from models.patient import Patient
            patient = Patient.query.filter_by(user_id=user.id).first()
            if patient:
                user_data['patient_id'] = patient.id
                user_data['first_name'] = patient.first_name
                user_data['last_name'] = patient.last_name
                user_data['gender'] = patient.gender
        elif user.role == 'Doctor':
            from models.doctor import Doctor
            doctor = Doctor.query.filter_by(user_id=user.id).first()
            if doctor:
                user_data['doctor_id'] = doctor.id
                user_data['first_name'] = doctor.name.split(' ')[0]
                user_data['last_name'] = ' '.join(doctor.name.split(' ')[1:]) if ' ' in doctor.name else ''
                user_data['gender'] = doctor.gender

        response_data = {
            'token': token,
            'user': user_data
        }

        return jsonify(response_data), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/auth/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json()

    try:
        user = User.query.get(request.current_user['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if 'username' in data:
            user.username = data['username']
        if 'mobile' in data:
            # Basic validation for mobile
            if not re.match(r'^\+\d{1,4}\d{7,15}$', data['mobile']):
                return jsonify({'error': 'Mobile number must include country code'}), 400
            user.mobile = data['mobile']
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    try:
        user = User.query.get(request.current_user['user_id'])
        if not user:
             return jsonify({'error': 'User not found'}), 404
        
        user_data = user.to_dict()
        if user.role == 'Patient':
            from models.patient import Patient
            patient = Patient.query.filter_by(user_id=user.id).first()
            if patient:
                user_data['patient_id'] = patient.id
                user_data['first_name'] = patient.first_name
                user_data['last_name'] = patient.last_name
                user_data['gender'] = patient.gender
        elif user.role == 'Doctor':
            from models.doctor import Doctor
            doctor = Doctor.query.filter_by(user_id=user.id).first()
            if doctor:
                user_data['doctor_id'] = doctor.id
                user_data['first_name'] = doctor.name.split(' ')[0]
                user_data['last_name'] = ' '.join(doctor.name.split(' ')[1:]) if ' ' in doctor.name else ''
                user_data['gender'] = doctor.gender

        return jsonify(user_data), 200
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

@auth_bp.route('/users', methods=['GET'])
@token_required
@roles_required('Admin')
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@auth_bp.route('/users/<int:id>', methods=['DELETE'])
@token_required
@roles_required('Admin')
def delete_user(id):
    user = User.query.get_or_404(id)
    try:
        # Also handle related records if necessary, but keep it simple for now
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
