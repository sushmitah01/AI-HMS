import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Comma-separated list of allowed frontend origins, e.g.
    # "https://ai-hms.example.com,https://staging.ai-hms.example.com"
    # Defaults to "*" for local development only — lock this down before
    # deploying anywhere reachable from the public internet.
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
