from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    role = db.Column(db.Enum('admin', 'technician', 'client'), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(255), nullable=False)
    document = db.Column(db.String(50))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='clients')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'document': self.document,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    oui = db.Column(db.String(10))
    product_class = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    hardware_version = db.Column(db.String(50))
    software_version = db.Column(db.String(50))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    connection_request_url = db.Column(db.String(500))
    connection_request_username = db.Column(db.String(100))
    connection_request_password = db.Column(db.String(100))
    last_inform = db.Column(db.DateTime)
    ip_address = db.Column(db.String(50))
    mac_address = db.Column(db.String(50))
    status = db.Column(db.Enum('online', 'offline', 'pending', 'error'), default='pending')
    provisioning_status = db.Column(db.Enum('not_provisioned', 'provisioning', 'provisioned', 'failed'), default='not_provisioned')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = db.relationship('Client', backref='devices')
    
    def to_dict(self, include_parameters=False):
        data = {
            'id': self.id,
            'serial_number': self.serial_number,
            'oui': self.oui,
            'product_class': self.product_class,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'hardware_version': self.hardware_version,
            'software_version': self.software_version,
            'client_id': self.client_id,
            'last_inform': self.last_inform.isoformat() if self.last_inform else None,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'status': self.status,
            'provisioning_status': self.provisioning_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_parameters:
            data['parameters'] = {p.parameter_name: p.parameter_value for p in self.parameters}
        return data

class DeviceParameter(db.Model):
    __tablename__ = 'device_parameters'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    parameter_name = db.Column(db.String(500), nullable=False)
    parameter_value = db.Column(db.Text)
    parameter_type = db.Column(db.String(50))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device = db.relationship('Device', backref='parameters')
    
    def to_dict(self):
        return {
            'parameter_name': self.parameter_name,
            'parameter_value': self.parameter_value,
            'parameter_type': self.parameter_type,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class ConfigurationProfile(db.Model):
    __tablename__ = 'configuration_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    model_filter = db.Column(db.String(255))
    configuration = db.Column(db.JSON, nullable=False)
    priority = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_filter': self.model_filter,
            'configuration': self.configuration,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ConfigurationTask(db.Model):
    __tablename__ = 'configuration_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    task_type = db.Column(db.Enum('set_parameters', 'get_parameters', 'reboot', 'firmware_upgrade', 'factory_reset', 'add_object', 'delete_object'), nullable=False)
    parameters = db.Column(db.JSON)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'failed', 'timeout'), default='pending')
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    device = db.relationship('Device', backref='tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'task_type': self.task_type,
            'parameters': self.parameters,
            'status': self.status,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class EventLog(db.Model):
    __tablename__ = 'event_log'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'))
    event_code = db.Column(db.String(50))
    event_type = db.Column(db.String(100))
    event_data = db.Column(db.JSON)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref='events')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'event_code': self.event_code,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DeviceDiagnostics(db.Model):
    __tablename__ = 'device_diagnostics'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    optical_power_rx = db.Column(db.Numeric(10, 2))
    optical_power_tx = db.Column(db.Numeric(10, 2))
    temperature = db.Column(db.Numeric(10, 2))
    cpu_usage = db.Column(db.Numeric(5, 2))
    memory_usage = db.Column(db.Numeric(5, 2))
    uptime = db.Column(db.Integer)
    wan_status = db.Column(db.String(50))
    connected_devices_count = db.Column(db.Integer, default=0)
    wifi_24ghz_status = db.Column(db.String(50))
    wifi_5ghz_status = db.Column(db.String(50))
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref='diagnostics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'optical_power_rx': float(self.optical_power_rx) if self.optical_power_rx else None,
            'optical_power_tx': float(self.optical_power_tx) if self.optical_power_tx else None,
            'temperature': float(self.temperature) if self.temperature else None,
            'cpu_usage': float(self.cpu_usage) if self.cpu_usage else None,
            'memory_usage': float(self.memory_usage) if self.memory_usage else None,
            'uptime': self.uptime,
            'wan_status': self.wan_status,
            'connected_devices_count': self.connected_devices_count,
            'wifi_24ghz_status': self.wifi_24ghz_status,
            'wifi_5ghz_status': self.wifi_5ghz_status,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None
        }

class ConnectedDevice(db.Model):
    __tablename__ = 'connected_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    mac_address = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(50))
    hostname = db.Column(db.String(255))
    interface_type = db.Column(db.String(50))
    connection_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    device = db.relationship('Device', backref='connected_devices')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mac_address': self.mac_address,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'interface_type': self.interface_type,
            'connection_time': self.connection_time.isoformat() if self.connection_time else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active
        }

class FirmwareVersion(db.Model):
    __tablename__ = 'firmware_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    version = db.Column(db.String(50))
    file_url = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    checksum = db.Column(db.String(100))
    release_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'version': self.version,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'notes': self.notes,
            'is_active': self.is_active
        }
