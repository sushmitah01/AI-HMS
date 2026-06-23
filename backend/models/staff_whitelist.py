from . import db
from datetime import datetime

class StaffWhitelist(db.Model):
    __tablename__ = 'staff_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # Doctor, Receptionist
    is_registered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'staff_id': self.staff_id,
            'role': self.role,
            'is_registered': self.is_registered,
            'created_at': self.created_at.isoformat()
        }
