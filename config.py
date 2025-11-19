import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # Database (Railway MySQL)
    DB_HOST = os.getenv('DB_HOST', 'mysql.railway.internal')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME', 'railway')

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    
    # Storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    USE_S3 = os.getenv('USE_S3', 'False') == 'True'
    
    # Google Cloud API Keys
    GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY')
    GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
    
    # OCR
    OCR_LANGUAGES = ['en', 'hi']
    OCR_CONFIDENCE_THRESHOLD = 0.6
    
    # Crawler
    CRAWLER_USER_AGENT = 'LegalMetrologyBot/1.0'
    CRAWLER_DELAY = 2
    MAX_IMAGES_PER_PRODUCT = 5
    
    # Compliance
    COMPLIANCE_THRESHOLD = 80
