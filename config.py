"""
Configuración del servidor TR-069
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tr069-secret-key-change-in-production'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://tr069:tr069pass@localhost/tr069_onts'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración TR-069
    TR069_ACS_URL = os.environ.get('TR069_ACS_URL') or 'http://localhost:5000/acs'
    TR069_ACS_USERNAME = os.environ.get('TR069_ACS_USERNAME') or 'acs'
    TR069_ACS_PASSWORD = os.environ.get('TR069_ACS_PASSWORD') or 'acspass'
    TR069_ACS_PORT = int(os.environ.get('TR069_ACS_PORT') or 7547)
    
    # Configuración de red
    DEFAULT_VLAN_ID = int(os.environ.get('DEFAULT_VLAN_ID') or 100)
    DEFAULT_PPPOE_USERNAME = os.environ.get('DEFAULT_PPPOE_USERNAME') or 'user'
    DEFAULT_PPPOE_PASSWORD = os.environ.get('DEFAULT_PPPOE_PASSWORD') or 'pass'
    DEFAULT_DNS_PRIMARY = os.environ.get('DEFAULT_DNS_PRIMARY') or '8.8.8.8'
    DEFAULT_DNS_SECONDARY = os.environ.get('DEFAULT_DNS_SECONDARY') or '8.8.4.4'
    
    # Configuración WiFi por defecto
    DEFAULT_WIFI_2_4_SSID = os.environ.get('DEFAULT_WIFI_2_4_SSID') or 'Huawei-ONT-2.4G'
    DEFAULT_WIFI_5_SSID = os.environ.get('DEFAULT_WIFI_5_SSID') or 'Huawei-ONT-5G'
    DEFAULT_WIFI_PASSWORD = os.environ.get('DEFAULT_WIFI_PASSWORD') or 'Huawei123456'
    
    # Configuración de monitoreo
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL') or 300)  # 5 minutos
    OPTICAL_POWER_THRESHOLD = float(os.environ.get('OPTICAL_POWER_THRESHOLD') or -25.0)  # dBm
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/tr069_server.log'