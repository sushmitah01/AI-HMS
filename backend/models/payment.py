from datetime import datetime
from . import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False) # Cash, Online
    reference_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='SUCCESS') # SUCCESS, REFUNDED
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    extra_info = db.Column(db.JSON, nullable=True) # Mobile number, card last4 etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    bill = db.relationship('Bill', backref='payments')
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'amount': self.amount,
            'method': self.method,
            'reference_number': self.reference_number,
            'status': self.status,
            'recorded_by': self.recorded_by,
            'recorder_name': self.recorder.username if self.recorder else "Unknown",
            'extra_info': self.extra_info,
            'created_at': self.created_at.isoformat()
        }

