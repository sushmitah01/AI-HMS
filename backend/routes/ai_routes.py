from flask import Blueprint, request, jsonify
from services.ml_service import ml_service
from services.gemini_service import gemini_service
from utils.auth import token_required, roles_required
from utils.limiter import limiter
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai_bp', __name__)


@ai_bp.route('/predict/risk', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
def predict_risk():
    data = request.get_json()
    # Expects: age, sys_bp, dia_bp, heart_rate
    try:
        prediction = ml_service.predict_health_risk(data)
        return jsonify({'risk_level': prediction}), 200
    except Exception as e:
        logger.exception('predict_risk failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/predict/readmission', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
def predict_readmission():
    data = request.get_json()
    # Expects: age, prev_visits, chronic (0/1), days_since
    try:
        probability = ml_service.predict_readmission(data)
        return jsonify({'readmission_probability': probability}), 200
    except Exception as e:
        logger.exception('predict_readmission failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/predict/disease', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
@limiter.limit("10 per minute")
def predict_disease():
    data = request.get_json()
    try:
        symptoms = data.get('symptoms', '')
        if not symptoms:
            return jsonify({'error': 'Symptoms required'}), 400

        predictions = gemini_service.predict_diagnosis(symptoms)
        return jsonify(predictions), 200
    except Exception as e:
        logger.exception('predict_disease failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/ai/patient/diagnose', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def patient_diagnose():
    data = request.get_json()
    symptoms = data.get('symptoms', '')
    if not symptoms:
        return jsonify({'error': 'Symptoms required'}), 400

    try:
        results = gemini_service.patient_ai_diagnosis(symptoms)
        return jsonify(results), 200
    except Exception as e:
        logger.exception('patient_diagnose failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/predict/prescription', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
@limiter.limit("10 per minute")
def suggest_prescription():
    data = request.get_json()
    diagnosis = data.get('diagnosis')
    patient_id = data.get('patient_id')

    if not diagnosis:
        return jsonify({'error': 'Diagnosis required'}), 400

    patient_context = None
    if patient_id:
        from models.patient import Patient
        patient = Patient.query.get(patient_id)
        if patient:
            # Calculate age, accounting for whether this year's birthday has passed
            from datetime import date
            if patient.dob:
                today = date.today()
                age = today.year - patient.dob.year - (
                    (today.month, today.day) < (patient.dob.month, patient.dob.day)
                )
            else:
                age = "unknown"
            patient_context = f"{age} year old {patient.gender} patient"
            if patient.blood_group:
                patient_context += f" with blood group {patient.blood_group}"

    try:
        prescriptions = gemini_service.suggest_prescription(diagnosis, patient_context)
        return jsonify(prescriptions), 200
    except Exception as e:
        logger.exception('suggest_prescription failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/generate/notes', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
@limiter.limit("10 per minute")
def generate_notes():
    data = request.get_json()
    clinical_data = data.get('data')
    try:
        notes = gemini_service.generate_notes(clinical_data)
        return jsonify({'notes': notes}), 200
    except Exception as e:
        logger.exception('generate_notes failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/predict/interactions', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
@limiter.limit("10 per minute")
def check_interactions():
    data = request.get_json()
    medicines = data.get('medicines', [])
    if not medicines:
        return jsonify({'error': 'Medicines list required'}), 400

    try:
        interactions = gemini_service.check_interactions(medicines)
        return jsonify({'interactions': interactions}), 200
    except Exception as e:
        logger.exception('check_interactions failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/ai/patient/chat', methods=['POST'])
@token_required
@limiter.limit("10 per minute")
def patient_chat():
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'Message required'}), 400

    try:
        # Simple keyword routing for the "Patient Assistant"
        if any(k in message.lower() for k in ['prescription', 'medicine', 'meds']):
            response = gemini_service.explain_prescription(message)
        elif any(k in message.lower() for k in ['report', 'lab', 'test', 'result']):
            response = gemini_service.explain_lab_report(message)
        elif any(k in message.lower() for k in ['symptom', 'pain', 'feel', 'hurt']):
            response = gemini_service.symptom_pre_check(message)
        else:
            response = gemini_service.hospital_faq(message)

        return jsonify({'response': response}), 200
    except Exception as e:
        logger.exception('patient_chat failed')
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/ai/system-report', methods=['GET'])
@token_required
@roles_required('Admin')
@limiter.limit("10 per minute")
def system_report():
    # Fetch global stats
    from models.patient import Patient
    from models.doctor import Doctor
    from models.appointment import Appointment
    from models.medical_record import MedicalRecord

    stats = {
        'total_patients': Patient.query.count(),
        'total_doctors': Doctor.query.count(),
        'total_appointments': Appointment.query.count(),
        'total_records': MedicalRecord.query.count()
    }

    try:
        report = gemini_service.generate_system_report(stats)
        return jsonify({'report': report}), 200
    except Exception as e:
        logger.exception('system_report failed')
        return jsonify({'error': str(e)}), 500
