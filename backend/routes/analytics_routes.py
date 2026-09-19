from flask import Blueprint, jsonify
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from utils.auth import token_required, roles_required

analytics_bp = Blueprint('analytics_bp', __name__)

@analytics_bp.route('/analytics/stats', methods=['GET'])
@token_required
@roles_required('Admin', 'Doctor', 'Receptionist')
def get_stats():
    from flask import request
    doctor_id = request.args.get('doctor_id')
    
    if doctor_id:
        try:
            d_id = int(doctor_id)
            # Doctor specific stats
            # Count unique patients who have appointments with this doctor
            total_patients = db.session.query(func.count(func.distinct(Appointment.patient_id)))\
                .filter(Appointment.doctor_id == d_id).scalar()
            
            today = datetime.utcnow().date()
            appointments_today = Appointment.query.filter_by(doctor_id=d_id, date=today).count()
            
            total_records = MedicalRecord.query.filter_by(doctor_id=d_id).count()
            
            return jsonify({
                'total_patients': total_patients or 0,
                'total_doctors': Doctor.query.count(),
                'total_records': total_records or 0,
                'appointments_today': appointments_today or 0
            }), 200
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid doctor_id format'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_records = MedicalRecord.query.count()
    
    today = datetime.utcnow().date()
    appointments_today = Appointment.query.filter_by(date=today).count()
    
    return jsonify({
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_records': total_records,
        'appointments_today': appointments_today
    }), 200

@analytics_bp.route('/analytics/trends', methods=['GET'])
@token_required
@roles_required('Admin', 'Doctor', 'Receptionist')
def get_trends():
    # Last 7 days appointment counts
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    
    data = db.session.query(Appointment.date, func.count(Appointment.id))\
        .filter(Appointment.date >= start_date)\
        .group_by(Appointment.date)\
        .order_by(Appointment.date).all()
        
    # Format for frontend
    result = []
    current = start_date
    data_dict = {d[0]: d[1] for d in data}
    
    while current <= end_date:
        result.append({
            'name': current.strftime('%a'), # Mon, Tue...
            'date': current.strftime('%Y-%m-%d'),
            'appointments': data_dict.get(current, 0)
        })
        current += timedelta(days=1)
        
    return jsonify(result), 200
