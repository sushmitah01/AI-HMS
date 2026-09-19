from flask import Blueprint, request, jsonify
from models import db
from models.doctor import Doctor
from utils.auth import token_required, roles_required

doctor_bp = Blueprint('doctor_bp', __name__)

@doctor_bp.route('/doctors', methods=['POST'])
@token_required
@roles_required('Admin')
def add_doctor():
    data = request.get_json()
    new_doctor = Doctor(
        name=data['name'],
        specialization=data['specialization'],
        contact=data.get('contact'),
        availability=data.get('availability'),
        consultation_fee=data.get('consultation_fee', 500.0)
    )

    db.session.add(new_doctor)
    db.session.commit()
    return jsonify(new_doctor.to_dict()), 201

@doctor_bp.route('/doctors', methods=['GET'])
@token_required
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([d.to_dict() for d in doctors]), 200

@doctor_bp.route('/doctors/<int:id>', methods=['GET'])
@token_required
def get_doctor(id):
    from models.user import User
    # Join with User table to get email and registration mobile
    result = db.session.query(Doctor, User).outerjoin(User, Doctor.user_id == User.id).filter(Doctor.id == id).first()
    
    if not result:
        return jsonify({'error': 'Doctor not found'}), 404
        
    doctor, user = result
    data = doctor.to_dict()
    
    if user:
        data['email'] = user.email
        # If doctor.contact is empty, use user.mobile
        if not data.get('contact'):
            data['contact'] = user.mobile
            
    return jsonify(data), 200

@doctor_bp.route('/doctors/<int:id>', methods=['PUT'])
@token_required
@roles_required('Admin', 'Doctor')
def update_doctor(id):
    doctor = Doctor.query.get_or_404(id)

    # A Doctor may only edit their own profile; Admins may edit any.
    if request.current_user.get('role') == 'Doctor' and doctor.user_id != request.current_user.get('user_id'):
        return jsonify({'error': 'You can only update your own doctor profile'}), 403

    data = request.get_json()

    # Validation
    if 'email' in data:
        email = data['email']
        allowed_domains = ['gmail.com', 'ymail.com', 'outlook.com', 'yahoo.com', 'icloud.com']
        domain = email.split('@')[-1] if '@' in email else ''
        if domain not in allowed_domains:
            return jsonify({'error': 'Email must be one of: ' + ", ".join(allowed_domains)}), 400
            
    if 'contact' in data:
        contact = data['contact']
        import re
        if not re.match(r'^\+\d{1,4}\d{7,15}$', contact):
            return jsonify({'error': 'Mobile number must include country code (e.g., +1234567890)'}), 400

    try:
        doctor.name = data.get('name', doctor.name)
        doctor.specialization = data.get('specialization', doctor.specialization)
        doctor.contact = data.get('contact', doctor.contact)
        doctor.gender = data.get('gender', doctor.gender)
        doctor.availability = data.get('availability', doctor.availability)
        doctor.consultation_fee = data.get('consultation_fee', doctor.consultation_fee)
        
        db.session.commit()

        return jsonify({'message': 'Doctor updated successfully', 'doctor': doctor.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@doctor_bp.route('/doctors/<int:id>', methods=['DELETE'])
@token_required
@roles_required('Admin')
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    try:
        db.session.delete(doctor)
        db.session.commit()
        return jsonify({'message': 'Doctor deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
