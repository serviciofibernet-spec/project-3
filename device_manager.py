"""
Device Management Module for TR-069 Server
Handles device registration, configuration, and monitoring
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import os

logger = logging.getLogger(__name__)

@dataclass
class Device:
    """Device information structure"""
    serial_number: str
    manufacturer: str = ""
    model: str = ""
    software_version: str = ""
    hardware_version: str = ""
    ip_address: str = ""
    last_contact: str = ""
    connection_request_url: str = ""
    parameters: Dict[str, Any] = None
    events: List[str] = None
    status: str = "online"  # online, offline, unknown
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.events is None:
            self.events = []

class DeviceManager:
    """Manages TR-069 devices and their configurations"""
    
    def __init__(self, db_path: str = "tr069_devices.db"):
        self.db_path = db_path
        self.devices: Dict[str, Device] = {}
        self.lock = threading.RLock()
        self.init_database()
        self.load_devices()
    
    def init_database(self):
        """Initialize SQLite database for device storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    serial_number TEXT PRIMARY KEY,
                    manufacturer TEXT,
                    model TEXT,
                    software_version TEXT,
                    hardware_version TEXT,
                    ip_address TEXT,
                    last_contact TEXT,
                    connection_request_url TEXT,
                    parameters TEXT,
                    events TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Create device_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial_number TEXT,
                    timestamp TEXT,
                    event_type TEXT,
                    message TEXT,
                    FOREIGN KEY (serial_number) REFERENCES devices (serial_number)
                )
            ''')
            
            # Create configurations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial_number TEXT,
                    parameter_name TEXT,
                    parameter_value TEXT,
                    applied_at TEXT,
                    status TEXT,
                    FOREIGN KEY (serial_number) REFERENCES devices (serial_number)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def load_devices(self):
        """Load devices from database"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM devices')
                rows = cursor.fetchall()
                
                for row in rows:
                    device = Device(
                        serial_number=row[0],
                        manufacturer=row[1] or "",
                        model=row[2] or "",
                        software_version=row[3] or "",
                        hardware_version=row[4] or "",
                        ip_address=row[5] or "",
                        last_contact=row[6] or "",
                        connection_request_url=row[7] or "",
                        parameters=json.loads(row[8]) if row[8] else {},
                        events=json.loads(row[9]) if row[9] else [],
                        status=row[10] or "unknown"
                    )
                    self.devices[device.serial_number] = device
                
                conn.close()
                logger.info(f"Loaded {len(self.devices)} devices from database")
                
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
    
    def register_device(self, device_info: Dict[str, Any]) -> bool:
        """Register a new device or update existing one"""
        try:
            with self.lock:
                serial_number = device_info.get('serial_number', '')
                if not serial_number:
                    logger.error("Device registration failed: No serial number")
                    return False
                
                # Create or update device
                if serial_number in self.devices:
                    device = self.devices[serial_number]
                    # Update existing device
                    device.manufacturer = device_info.get('manufacturer', device.manufacturer)
                    device.model = device_info.get('model', device.model)
                    device.software_version = device_info.get('software_version', device.software_version)
                    device.hardware_version = device_info.get('hardware_version', device.hardware_version)
                    device.ip_address = device_info.get('ip_address', device.ip_address)
                    device.connection_request_url = device_info.get('connection_request_url', device.connection_request_url)
                    device.last_contact = datetime.now().isoformat()
                    device.status = "online"
                    
                    # Update parameters
                    if 'parameters' in device_info:
                        device.parameters.update(device_info['parameters'])
                    
                    # Update events
                    if 'events' in device_info:
                        device.events = device_info['events']
                else:
                    # Create new device
                    device = Device(
                        serial_number=serial_number,
                        manufacturer=device_info.get('manufacturer', ''),
                        model=device_info.get('model', ''),
                        software_version=device_info.get('software_version', ''),
                        hardware_version=device_info.get('hardware_version', ''),
                        ip_address=device_info.get('ip_address', ''),
                        last_contact=datetime.now().isoformat(),
                        connection_request_url=device_info.get('connection_request_url', ''),
                        parameters=device_info.get('parameters', {}),
                        events=device_info.get('events', []),
                        status="online"
                    )
                    self.devices[serial_number] = device
                
                # Save to database
                self.save_device(device)
                
                # Log the registration
                self.log_device_event(serial_number, "registration", "Device registered/updated")
                
                logger.info(f"Device registered: {serial_number}")
                return True
                
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return False
    
    def save_device(self, device: Device):
        """Save device to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (serial_number, manufacturer, model, software_version, hardware_version,
                 ip_address, last_contact, connection_request_url, parameters, events,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT created_at FROM devices WHERE serial_number = ?), ?), ?)
            ''', (
                device.serial_number, device.manufacturer, device.model,
                device.software_version, device.hardware_version, device.ip_address,
                device.last_contact, device.connection_request_url,
                json.dumps(device.parameters), json.dumps(device.events),
                device.status, device.serial_number, now, now
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving device: {e}")
    
    def get_device(self, serial_number: str) -> Optional[Device]:
        """Get device by serial number"""
        with self.lock:
            return self.devices.get(serial_number)
    
    def get_all_devices(self) -> Dict[str, Device]:
        """Get all registered devices"""
        with self.lock:
            return self.devices.copy()
    
    def update_device_parameters(self, serial_number: str, parameters: Dict[str, Any]) -> bool:
        """Update device parameters"""
        try:
            with self.lock:
                device = self.devices.get(serial_number)
                if not device:
                    logger.error(f"Device not found: {serial_number}")
                    return False
                
                device.parameters.update(parameters)
                device.last_contact = datetime.now().isoformat()
                self.save_device(device)
                
                # Log parameter updates
                for param, value in parameters.items():
                    self.log_device_event(
                        serial_number, 
                        "parameter_update", 
                        f"Parameter {param} updated to {value}"
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating device parameters: {e}")
            return False
    
    def set_device_offline(self, serial_number: str):
        """Mark device as offline"""
        with self.lock:
            device = self.devices.get(serial_number)
            if device:
                device.status = "offline"
                self.save_device(device)
                self.log_device_event(serial_number, "status_change", "Device marked as offline")
    
    def check_device_status(self):
        """Check and update device status based on last contact"""
        try:
            with self.lock:
                now = datetime.now()
                offline_threshold = timedelta(minutes=10)  # Consider offline after 10 minutes
                
                for serial_number, device in self.devices.items():
                    if device.last_contact:
                        last_contact = datetime.fromisoformat(device.last_contact)
                        if now - last_contact > offline_threshold and device.status == "online":
                            device.status = "offline"
                            self.save_device(device)
                            self.log_device_event(serial_number, "status_change", "Device timed out")
                            logger.info(f"Device {serial_number} marked as offline due to timeout")
                            
        except Exception as e:
            logger.error(f"Error checking device status: {e}")
    
    def log_device_event(self, serial_number: str, event_type: str, message: str):
        """Log device event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO device_logs (serial_number, timestamp, event_type, message)
                VALUES (?, ?, ?, ?)
            ''', (serial_number, datetime.now().isoformat(), event_type, message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging device event: {e}")
    
    def get_device_logs(self, serial_number: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get device logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, event_type, message
                FROM device_logs
                WHERE serial_number = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (serial_number, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'timestamp': row[0],
                    'event_type': row[1],
                    'message': row[2]
                })
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting device logs: {e}")
            return []
    
    def get_device_statistics(self) -> Dict[str, Any]:
        """Get device statistics"""
        with self.lock:
            total_devices = len(self.devices)
            online_devices = sum(1 for d in self.devices.values() if d.status == "online")
            offline_devices = sum(1 for d in self.devices.values() if d.status == "offline")
            
            manufacturers = {}
            models = {}
            
            for device in self.devices.values():
                if device.manufacturer:
                    manufacturers[device.manufacturer] = manufacturers.get(device.manufacturer, 0) + 1
                if device.model:
                    models[device.model] = models.get(device.model, 0) + 1
            
            return {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': offline_devices,
                'manufacturers': manufacturers,
                'models': models
            }
    
    def export_devices(self, file_path: str) -> bool:
        """Export devices to JSON file"""
        try:
            with self.lock:
                devices_data = {}
                for serial_number, device in self.devices.items():
                    devices_data[serial_number] = asdict(device)
                
                with open(file_path, 'w') as f:
                    json.dump(devices_data, f, indent=2)
                
                logger.info(f"Devices exported to {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting devices: {e}")
            return False
    
    def import_devices(self, file_path: str) -> bool:
        """Import devices from JSON file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Import file not found: {file_path}")
                return False
            
            with open(file_path, 'r') as f:
                devices_data = json.load(f)
            
            imported_count = 0
            for serial_number, device_data in devices_data.items():
                device = Device(**device_data)
                with self.lock:
                    self.devices[serial_number] = device
                    self.save_device(device)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} devices from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing devices: {e}")
            return False