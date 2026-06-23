from flask import Blueprint, request, jsonify
from models import db
from models.bill import Bill
from models.payment import Payment
from models.appointment import Appointment
from models.notification import Notification
from datetime import datetime


billing_bp = Blueprint('billing_bp', __name__)

@billing_bp.route('/bills', methods=['GET'])
def get_bills():
    status_filter = request.args.get('status')
    patient_id = request.args.get('patient_id')
    
    query = Bill.query.join(Appointment)
    
    if status_filter:
        query = query.filter(Bill.status == status_filter)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
        
    bills = query.order_by(Bill.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bills]), 200

@billing_bp.route('/bills/<int:id>/pay', methods=['POST'])
def record_payment(id):
    bill = Bill.query.get_or_404(id)
    data = request.get_json()
    
    if bill.status == 'PAID':
        return jsonify({'error': 'Bill is already paid'}), 400
        
    try:
        new_payment = Payment(
            bill_id=bill.id,
            amount=bill.amount,
            method=data['method'], # Cash, Online
            reference_number=data.get('reference_number'),
            recorded_by=data['recorded_by'], # Receptionist User ID
            extra_info=data.get('metadata')
        )
        db.session.add(new_payment)

        
        bill.status = 'PAID'
        # Close the appointment
        bill.appointment.status = 'CLOSED'
        
        # Notify Patient
        notif = Notification(
            patient_id=bill.appointment.patient_id,
            message=f"Payment of ৳{bill.amount} for appointment with Dr. {bill.appointment.doctor.name} was successful. Status: CLOSED."
        )
        db.session.add(notif)
        
        db.session.commit()

        return jsonify({'message': 'Payment recorded successfully', 'payment': new_payment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/payments/<int:id>/refund', methods=['PUT'])
def refund_payment(id):
    payment = Payment.query.get_or_404(id)
    data = request.get_json()
    
    # Check if user is Admin (should be handled by middleware, but simple check here)
    # user_role = data.get('role')
    # if user_role != 'Admin':
    #     return jsonify({'error': 'Unauthorized'}), 403
        
    payment.status = 'REFUNDED'
    payment.bill.status = 'UNPAID'
    # Optionally reopen appointment? Requirements say "status change only" for refunds.
    
    db.session.commit()
    return jsonify({'message': 'Payment refunded', 'payment': payment.to_dict()}), 200

@billing_bp.route('/bills/<int:id>', methods=['GET'])
def get_bill(id):
    bill = Bill.query.get_or_404(id)
    data = bill.to_dict()
    # Include payment history
    data['payments'] = [p.to_dict() for p in bill.payments]
    return jsonify(data), 200
