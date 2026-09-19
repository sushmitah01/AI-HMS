from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .patient import Patient
from .doctor import Doctor
from .appointment import Appointment
from .medical_record import MedicalRecord
from .notification import Notification
from .bill import Bill
from .payment import Payment
from .staff_whitelist import StaffWhitelist

