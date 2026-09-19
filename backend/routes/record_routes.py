from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db
from models.medical_record import MedicalRecord
from utils.auth import token_required, roles_required

record_bp = Blueprint('record_bp', __name__)

@record_bp.route('/medical_records', methods=['POST'])
@token_required
@roles_required('Admin', 'Doctor')
def create_record():
    import json
    data = request.get_json()
    try:
        # Serialize prescription to JSON string if it's a list/dict
        prescription_val = data.get('prescription')
        if isinstance(prescription_val, (list, dict)):
            prescription_val = json.dumps(prescription_val)

        visit_date_val = datetime.utcnow()
        if data.get('visit_date'):
            try:
                visit_date_val = datetime.strptime(data['visit_date'], '%Y-%m-%d')
            except ValueError:
                pass

        new_record = MedicalRecord(
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            diagnosis=data['diagnosis'],
            prescription=prescription_val,
            tests=data.get('tests'),
            notes=data.get('notes'),
            symptoms=data.get('symptoms'),
            visit_date=visit_date_val
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@record_bp.route('/medical_records', methods=['GET'])
@token_required
def get_records():
    patient_filter = request.args.get('patient_id')
    query = MedicalRecord.query
    
    if patient_filter:
        query = query.filter_by(patient_id=patient_filter)
        
    records = query.order_by(MedicalRecord.visit_date.desc()).all()
    return jsonify([r.to_dict() for r in records]), 200

@record_bp.route('/medical_records/<int:id>', methods=['DELETE'])
@token_required
@roles_required('Admin', 'Doctor')
def delete_record(id):
    record = MedicalRecord.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Record deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@record_bp.route('/medical_records/<int:id>', methods=['PUT'])
@token_required
@roles_required('Admin', 'Doctor')
def update_record(id):
    import json
    record = MedicalRecord.query.get_or_404(id)
    data = request.get_json()
    try:
        if 'diagnosis' in data:
            record.diagnosis = data['diagnosis']
        if 'prescription' in data:
            prescription_val = data['prescription']
            if isinstance(prescription_val, (list, dict)):
                prescription_val = json.dumps(prescription_val)
            record.prescription = prescription_val
        if 'tests' in data:
            record.tests = data.get('tests')
        if 'notes' in data:
            record.notes = data.get('notes')
        if 'symptoms' in data:
            record.symptoms = data.get('symptoms')
        if 'visit_date' in data:
            try:
                record.visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d')
            except ValueError:
                pass
        
        db.session.commit()
        return jsonify(record.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
