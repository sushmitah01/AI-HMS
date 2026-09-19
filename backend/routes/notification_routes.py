from flask import Blueprint, request, jsonify
from models import db
from models.notification import Notification
from utils.auth import token_required

notification_bp = Blueprint('notification_bp', __name__)

@notification_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications():
    doctor_id = request.args.get('doctor_id')
    patient_id = request.args.get('patient_id')
    
    query = Notification.query
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    elif patient_id:
        query = query.filter_by(patient_id=patient_id)
    else:
        return jsonify({'error': 'Doctor ID or Patient ID is required'}), 400

    notifications = query.order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifications]), 200

@notification_bp.route('/notifications/<int:id>/read', methods=['PUT'])
@token_required
def mark_as_read(id):
    notification = Notification.query.get_or_404(id)
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict()), 200
