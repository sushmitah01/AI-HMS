from . import db

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    availability = db.Column(db.String(200), nullable=True) # e.g., "Mon-Fri 09:00-17:00"
    consultation_fee = db.Column(db.Float, default=500.0)


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'specialization': self.specialization,
            'contact': self.contact,
            'gender': self.gender,
            'availability': self.availability,
            'consultation_fee': self.consultation_fee
        }

