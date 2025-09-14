import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # External API keys
    GOOGLE_MAPS_API_KEY = os.getenv('MAPS_API_KEY')
    
    # File paths
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, 'screenshots')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    TEMP_IMG_FOLDER = os.path.join(BASE_DIR, 'temp_imgs')
    CROPPED_RECEIPTS_FOLDER = os.path.join(BASE_DIR, 'cropped_receipts')
    
    # File upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
    
    # API configuration
    API_TIMEOUT = 30
    RATE_LIMIT = "100 per hour"
    
    # OCR configuration
    OCR_DPI = 300
    OCR_CONTOUR_AREA_THRESHOLD = 5000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig
}

def get_config():
    """Get configuration based on environment"""
    config_name = os.getenv('FLASK_ENV', 'dev')
    return config_by_name.get(config_name, DevelopmentConfig)