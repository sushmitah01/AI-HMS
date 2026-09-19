from flask import Flask
import os
from flask_cors import CORS
from config import Config
from models import db
from utils.limiter import limiter
from routes.patient_routes import patient_bp
from routes.doctor_routes import doctor_bp
from routes.appointment_routes import appointment_bp
from routes.record_routes import record_bp
from routes.ai_routes import ai_bp
from routes.analytics_routes import analytics_bp
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.notification_routes import notification_bp
from routes.billing_routes import billing_bp
from routes.staff_routes import staff_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS origin(s) come from CORS_ORIGINS env var; "*" (dev default) allows any origin.
    origins = app.config['CORS_ORIGINS']
    origins = origins.split(',') if origins != '*' else '*'
    CORS(app, resources={r"/api/*": {"origins": origins}})

    db.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(patient_bp, url_prefix='/api')
    app.register_blueprint(doctor_bp, url_prefix='/api')
    app.register_blueprint(appointment_bp, url_prefix='/api')
    app.register_blueprint(record_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(notification_bp, url_prefix='/api')
    app.register_blueprint(billing_bp, url_prefix='/api')
    app.register_blueprint(staff_bp, url_prefix='/api')


    with app.app_context():
        db.create_all()
        
    @app.route('/')
    def home():
        return "AI-HMS Backend is Running! 🚀", 200

    return app

app = create_app()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)
