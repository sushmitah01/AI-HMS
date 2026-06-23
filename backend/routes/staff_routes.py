from flask import Blueprint, request, jsonify
from models import db
from models.staff_whitelist import StaffWhitelist

staff_bp = Blueprint('staff_bp', __name__)

@staff_bp.route('/staff/whitelist', methods=['GET'])
def get_whitelist():
    # Admin check should be added here
    whitelist = StaffWhitelist.query.all()
    return jsonify([s.to_dict() for s in whitelist]), 200

@staff_bp.route('/staff/whitelist', methods=['POST'])
def add_to_whitelist():
    data = request.get_json()
    try:
        if StaffWhitelist.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already in whitelist'}), 400
        if StaffWhitelist.query.filter_by(staff_id=data['staff_id']).first():
            return jsonify({'error': 'Staff ID already in whitelist'}), 400

        new_record = StaffWhitelist(
            email=data['email'],
            staff_id=data['staff_id'],
            role=data['role']
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@staff_bp.route('/staff/whitelist/<int:id>', methods=['DELETE'])
def delete_from_whitelist(id):
    record = StaffWhitelist.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Record deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
