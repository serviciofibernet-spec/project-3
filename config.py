import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'tr069_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'tr069_acs')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # ACS Configuration
    ACS_URL = os.getenv('ACS_URL', 'http://localhost:7547')
    ACS_USERNAME = os.getenv('ACS_USERNAME', 'admin')
    ACS_PASSWORD = os.getenv('ACS_PASSWORD', 'admin123')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 7547))
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    
    # TR-069 Settings
    CWMP_VERSION = '1.4'
    CONNECTION_REQUEST_TIMEOUT = 30
    INFORM_INTERVAL = 300  # 5 minutes
    
    # Auto-provisioning
    AUTO_PROVISION_ENABLED = True
    DEFAULT_WIFI_PASSWORD_LENGTH = 12
