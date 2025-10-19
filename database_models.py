"""
Modelos de base de datos para el servidor TR-069
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class Customer(UserMixin, db.Model):
    """Modelo de cliente/usuario"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    onts = db.relationship('ONT', backref='customer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Customer {self.username}>'

class ONT(db.Model):
    """Modelo de ONT (Optical Network Terminal)"""
    __tablename__ = 'onts'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    model = db.Column(db.String(50), nullable=False)
    firmware_version = db.Column(db.String(50))
    hardware_version = db.Column(db.String(50))
    ip_address = db.Column(db.String(15))
    connection_id = db.Column(db.String(50))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    configuration_profile_id = db.Column(db.Integer, db.ForeignKey('configuration_profiles.id'))
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    wifi_settings = db.relationship('WiFiSettings', backref='ont', uselist=False, cascade='all, delete-orphan')
    network_settings = db.relationship('NetworkSettings', backref='ont', uselist=False, cascade='all, delete-orphan')
    monitoring_data = db.relationship('MonitoringData', backref='ont', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ONT {self.serial_number}>'

class ConfigurationProfile(db.Model):
    """Perfil de configuración automática por modelo de ONT"""
    __tablename__ = 'configuration_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ont_model = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    onts = db.relationship('ONT', backref='configuration_profile', lazy=True)
    wifi_template = db.relationship('WiFiTemplate', backref='configuration_profile', uselist=False, cascade='all, delete-orphan')
    network_template = db.relationship('NetworkTemplate', backref='configuration_profile', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ConfigurationProfile {self.name}>'

class WiFiSettings(db.Model):
    """Configuración WiFi de una ONT"""
    __tablename__ = 'wifi_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    ont_id = db.Column(db.Integer, db.ForeignKey('onts.id'), nullable=False)
    
    # WiFi 2.4GHz
    wifi_2_4_enabled = db.Column(db.Boolean, default=True)
    wifi_2_4_ssid = db.Column(db.String(32))
    wifi_2_4_password = db.Column(db.String(64))
    wifi_2_4_channel = db.Column(db.Integer, default=6)
    wifi_2_4_security = db.Column(db.String(20), default='WPA2-PSK')
    
    # WiFi 5GHz
    wifi_5_enabled = db.Column(db.Boolean, default=True)
    wifi_5_ssid = db.Column(db.String(32))
    wifi_5_password = db.Column(db.String(64))
    wifi_5_channel = db.Column(db.Integer, default=36)
    wifi_5_security = db.Column(db.String(20), default='WPA2-PSK')
    
    # Configuración general
    wifi_guest_enabled = db.Column(db.Boolean, default=False)
    wifi_guest_ssid = db.Column(db.String(32))
    wifi_guest_password = db.Column(db.String(64))
    wifi_guest_vlan = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WiFiSettings ONT {self.ont_id}>'

class NetworkSettings(db.Model):
    """Configuración de red de una ONT"""
    __tablename__ = 'network_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    ont_id = db.Column(db.Integer, db.ForeignKey('onts.id'), nullable=False)
    
    # Configuración IP
    ip_mode = db.Column(db.String(20), default='DHCP')  # DHCP, Static, PPPoE
    static_ip = db.Column(db.String(15))
    static_gateway = db.Column(db.String(15))
    static_netmask = db.Column(db.String(15))
    
    # Configuración PPPoE
    pppoe_username = db.Column(db.String(100))
    pppoe_password = db.Column(db.String(100))
    pppoe_service_name = db.Column(db.String(100))
    
    # Configuración VLAN
    vlan_id = db.Column(db.Integer)
    vlan_priority = db.Column(db.Integer, default=0)
    
    # Configuración DNS
    dns_primary = db.Column(db.String(15))
    dns_secondary = db.Column(db.String(15))
    
    # Configuración de puertos
    port_1_enabled = db.Column(db.Boolean, default=True)
    port_2_enabled = db.Column(db.Boolean, default=True)
    port_3_enabled = db.Column(db.Boolean, default=True)
    port_4_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NetworkSettings ONT {self.ont_id}>'

class WiFiTemplate(db.Model):
    """Plantilla WiFi para perfiles de configuración"""
    __tablename__ = 'wifi_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    configuration_profile_id = db.Column(db.Integer, db.ForeignKey('configuration_profiles.id'), nullable=False)
    
    # WiFi 2.4GHz
    wifi_2_4_enabled = db.Column(db.Boolean, default=True)
    wifi_2_4_ssid_template = db.Column(db.String(100))  # Puede usar variables como {customer_name}
    wifi_2_4_password_template = db.Column(db.String(100))
    wifi_2_4_channel = db.Column(db.Integer, default=6)
    wifi_2_4_security = db.Column(db.String(20), default='WPA2-PSK')
    
    # WiFi 5GHz
    wifi_5_enabled = db.Column(db.Boolean, default=True)
    wifi_5_ssid_template = db.Column(db.String(100))
    wifi_5_password_template = db.Column(db.String(100))
    wifi_5_channel = db.Column(db.Integer, default=36)
    wifi_5_security = db.Column(db.String(20), default='WPA2-PSK')
    
    def __repr__(self):
        return f'<WiFiTemplate Profile {self.configuration_profile_id}>'

class NetworkTemplate(db.Model):
    """Plantilla de red para perfiles de configuración"""
    __tablename__ = 'network_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    configuration_profile_id = db.Column(db.Integer, db.ForeignKey('configuration_profiles.id'), nullable=False)
    
    # Configuración IP
    ip_mode = db.Column(db.String(20), default='DHCP')
    static_ip_template = db.Column(db.String(100))
    static_gateway_template = db.Column(db.String(100))
    static_netmask = db.Column(db.String(15), default='255.255.255.0')
    
    # Configuración PPPoE
    pppoe_username_template = db.Column(db.String(100))
    pppoe_password_template = db.Column(db.String(100))
    pppoe_service_name = db.Column(db.String(100))
    
    # Configuración VLAN
    vlan_id = db.Column(db.Integer)
    vlan_priority = db.Column(db.Integer, default=0)
    
    # Configuración DNS
    dns_primary = db.Column(db.String(15))
    dns_secondary = db.Column(db.String(15))
    
    def __repr__(self):
        return f'<NetworkTemplate Profile {self.configuration_profile_id}>'

class MonitoringData(db.Model):
    """Datos de monitoreo de ONTs"""
    __tablename__ = 'monitoring_data'
    
    id = db.Column(db.Integer, primary_key=True)
    ont_id = db.Column(db.Integer, db.ForeignKey('onts.id'), nullable=False)
    
    # Datos ópticos
    optical_power_tx = db.Column(db.Float)  # Potencia de transmisión (dBm)
    optical_power_rx = db.Column(db.Float)  # Potencia de recepción (dBm)
    optical_temperature = db.Column(db.Float)  # Temperatura del módulo óptico
    
    # Estado de la conexión
    connection_status = db.Column(db.String(20))  # Up, Down, Error
    uptime = db.Column(db.Integer)  # Tiempo activo en segundos
    
    # Dispositivos WiFi conectados
    wifi_devices_2_4 = db.Column(db.Integer, default=0)
    wifi_devices_5 = db.Column(db.Integer, default=0)
    wifi_devices_guest = db.Column(db.Integer, default=0)
    
    # Estadísticas de red
    bytes_sent = db.Column(db.BigInteger, default=0)
    bytes_received = db.Column(db.BigInteger, default=0)
    packets_sent = db.Column(db.BigInteger, default=0)
    packets_received = db.Column(db.BigInteger, default=0)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MonitoringData ONT {self.ont_id} at {self.timestamp}>'

class TR069Session(db.Model):
    """Sesiones TR-069 activas"""
    __tablename__ = 'tr069_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    ont_id = db.Column(db.Integer, db.ForeignKey('onts.id'))
    cpe_ip = db.Column(db.String(15))
    cpe_user_agent = db.Column(db.String(200))
    acs_url = db.Column(db.String(200))
    connection_request_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TR069Session {self.session_id}>'