from datetime import datetime
from . import db

class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='UNPAID') # UNPAID, PAID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship('Appointment', backref=db.backref('bill', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'patient_name': f"{self.appointment.patient.first_name} {self.appointment.patient.last_name}" if self.appointment and self.appointment.patient else "Unknown",
            'doctor_name': self.appointment.doctor.name if self.appointment and self.appointment.doctor else "Unknown",
            'date': self.appointment.date.isoformat() if self.appointment else None,
            'payments': [p.to_dict() for p in self.payments] if hasattr(self, 'payments') else []
        }

