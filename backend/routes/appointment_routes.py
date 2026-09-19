from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db
from models.appointment import Appointment
from sqlalchemy import  and_
from utils.auth import token_required, roles_required
import logging

logger = logging.getLogger(__name__)

appointment_bp = Blueprint('appointment_bp', __name__)

@appointment_bp.route('/appointments', methods=['POST'])
@token_required
def create_appointment():
    data = request.get_json()
    try:
        doctor_id = data['doctor_id']
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        time_obj = datetime.strptime(data['time'], '%H:%M').time()

        # Conflict Detection: Check if doctor has an appointment at the same slot
        # Assuming 30 min slots for simplicity, but for now exact time match
        conflict = Appointment.query.filter_by(
            doctor_id=doctor_id, 
            date=date_obj,
            time=time_obj,
            status='Scheduled'
        ).first()

        if conflict:
            return jsonify({'error': 'Slot not available'}), 409

        new_appointment = Appointment(
            patient_id=data['patient_id'],
            doctor_id=doctor_id,
            date=date_obj,
            time=time_obj,
            reason=data.get('reason'),
            status='Requested'
        )
        db.session.add(new_appointment)
        
        # Create Notification for the Doctor
        from models.notification import Notification
        patient_name = new_appointment.patient.first_name + " " + new_appointment.patient.last_name if new_appointment.patient else "A patient"
        notification_message = f"New appointment booked by {patient_name} for {date_obj} at {time_obj}"
        
        # We need to commit appointment first to ensure we have the patient data if we were querying it, 
        # but here we might rely on the relationship which might need the object to be in session. 
        # Actually safer to flush or commit.
        
        # Determine patient name for message. 
        # Since patient_id is in data, we can just use that, or query it.
        # Let's simple say "A new appointment..." or fetch patient.
        try:
           from models.patient import Patient
           pat = Patient.query.get(data['patient_id'])
           pat_name = f"{pat.first_name} {pat.last_name}" if pat else "Unknown Patient"
        except:
           pat_name = "Unknown Patient"

        notification_message = f"New appointment: {pat_name} on {date_obj} at {time_obj}"
        
        new_notification = Notification(
            doctor_id=doctor_id,
            message=notification_message
        )
        db.session.add(new_notification)

        db.session.commit()
        return jsonify(new_appointment.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments', methods=['GET'])
@token_required
def get_appointments():
    date_filter = request.args.get('date')
    doctor_filter = request.args.get('doctor_id')
    patient_filter = request.args.get('patient_id')
    
    query = Appointment.query
    
    if date_filter:
        query = query.filter(Appointment.date == datetime.strptime(date_filter, '%Y-%m-%d').date())
    if doctor_filter:
        query = query.filter(Appointment.doctor_id == doctor_filter)
    if patient_filter:
        query = query.filter(Appointment.patient_id == patient_filter)
        
    appointments = query.order_by(Appointment.date, Appointment.time).all()
    return jsonify([a.to_dict() for a in appointments]), 200

@appointment_bp.route('/appointments/<int:id>/status', methods=['PUT'])
@token_required
@roles_required('Admin', 'Doctor', 'Receptionist')
def update_status(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json()
    new_status = data['status']
    
    if new_status == 'Completed' and appointment.status != 'Completed':
        # Auto-generate Bill
        from models.bill import Bill
        # Check if bill already exists to avoid duplicates
        existing_bill = Bill.query.filter_by(appointment_id=appointment.id).first()
        if not existing_bill:
            amount = appointment.doctor.consultation_fee if appointment.doctor else 500.0
            new_bill = Bill(appointment_id=appointment.id, amount=amount)
            db.session.add(new_bill)
            
            # Notify Patient
            from models.notification import Notification
            notif = Notification(
                patient_id=appointment.patient_id,
                message=f"Consultation completed. Your bill of ৳{amount} is ready. You can pay now online through 'My Payments'."
            )
            db.session.add(notif)
    appointment.status = new_status
    db.session.commit()
    return jsonify(appointment.to_dict()), 200


@appointment_bp.route('/appointments/<int:id>/confirm', methods=['PUT'])
@token_required
@roles_required('Admin', 'Receptionist')
def confirm_appointment(id):
    try:
        appointment = Appointment.query.get_or_404(id)
        
        # Generate Serial Number
        existing_count = Appointment.query.filter_by(
            doctor_id=appointment.doctor_id,
            date=appointment.date,
            status='Scheduled' # Count only confirmed/scheduled ones
        ).count()
        
        appointment.serial_number = existing_count + 1
        appointment.status = 'Scheduled'
        
        # Create Notification for Patient
        from models.notification import Notification
        try:
            notification_message = f"Your appointment has been confirmed! Serial No: {appointment.serial_number} for {appointment.date} at {appointment.time}"
            new_notification = Notification(
                patient_id=appointment.patient_id,
                doctor_id=appointment.doctor_id, # REQUIRED by DB schema
                message=notification_message
            )
            db.session.add(new_notification)
        except Exception as e:
            logger.warning("Notification creation failed (suppressed): %s", e)
        
        db.session.commit()
        return jsonify({'message': 'Appointment confirmed', 'appointment': appointment.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/<int:id>/cancel', methods=['PUT'])
@token_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)

    # Staff can cancel any appointment; a Patient may only cancel their own.
    role = request.current_user.get('role')
    if role == 'Patient':
        from models.patient import Patient
        patient = Patient.query.filter_by(user_id=request.current_user.get('user_id')).first()
        if not patient or patient.id != appointment.patient_id:
            return jsonify({'error': 'You can only cancel your own appointments'}), 403
    elif role not in ('Admin', 'Receptionist', 'Doctor'):
        return jsonify({'error': 'Unauthorized'}), 403

    appointment.status = 'Cancelled'
    
    # If an Appointment is cancelled before payment, the Bill is deleted automatically.
    from models.bill import Bill
    bill = Bill.query.filter_by(appointment_id=appointment.id, status='UNPAID').first()
    if bill:
        db.session.delete(bill)
        
    db.session.commit()
    return jsonify(appointment.to_dict()), 200


@appointment_bp.route('/appointments/<int:id>/reschedule', methods=['PUT'])
@token_required
@roles_required('Admin', 'Receptionist', 'Patient')
def reschedule_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json()
    try:
        if 'date' in data:
            appointment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'time' in data:
            appointment.time = datetime.strptime(data['time'], '%H:%M').time()
        
        # Reset status to Requested if it was Scheduled or Completed? 
        # Usually rescheduling means it needs a new serial number if it was scheduled.
        appointment.status = 'Requested'
        appointment.serial_number = None 
        
        db.session.commit()
        return jsonify(appointment.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/<int:id>', methods=['DELETE'])
@token_required
@roles_required('Admin', 'Receptionist')
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    try:
        # If a Payment exists with status PAID (via Bill status), the related Appointment must not be deletable.
        from models.bill import Bill
        bill = Bill.query.filter_by(appointment_id=appointment.id).first()
        if bill and bill.status == 'PAID':
            return jsonify({'error': 'Cannot delete an appointment that has been paid for.'}), 400
            
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'message': 'Appointment deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

