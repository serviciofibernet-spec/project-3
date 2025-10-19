#!/usr/bin/env python3
"""
TR-069 Server Implementation
A complete TR-069 (CWMP) server for device management
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import uuid
import hashlib
import base64
import configparser
import sqlite3
import os
from dataclasses import dataclass
from aiohttp import web, ClientSession
import aiohttp_cors
from aiohttp.web import Request, Response
import ssl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tr069_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Device:
    """Represents a TR-069 device"""
    device_id: str
    serial_number: str
    manufacturer: str
    model: str
    software_version: str
    hardware_version: str
    connection_request_url: str
    last_inform: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

class TR069Server:
    """Main TR-069 server implementation"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.host = self.config.get('server', 'host', fallback='0.0.0.0')
        self.port = self.config.getint('server', 'port', fallback=8080)
        self.ssl_port = self.config.getint('server', 'ssl_port', fallback=8443)
        self.cleanup_hours = self.config.getint('device_management', 'cleanup_hours', fallback=24)
        self.max_devices = self.config.getint('device_management', 'max_devices', fallback=1000)
        
        self.devices: Dict[str, Device] = {}
        self.app = web.Application()
        self.db_file = self.config.get('database', 'file', fallback='tr069_devices.db')
        
        self.setup_database()
        self.setup_routes()
        self.setup_cors()
        self.load_devices_from_db()
        
        # Start cleanup task
        asyncio.create_task(self.cleanup_task())
        
    def setup_cors(self):
        """Setup CORS for web interface"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def setup_database(self):
        """Setup SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                serial_number TEXT,
                manufacturer TEXT,
                model TEXT,
                software_version TEXT,
                hardware_version TEXT,
                connection_request_url TEXT,
                last_inform TEXT,
                parameters TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_device_to_db(self, device: Device):
        """Save device to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO devices 
            (device_id, serial_number, manufacturer, model, software_version, 
             hardware_version, connection_request_url, last_inform, parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device.device_id,
            device.serial_number,
            device.manufacturer,
            device.model,
            device.software_version,
            device.hardware_version,
            device.connection_request_url,
            device.last_inform.isoformat() if device.last_inform else None,
            json.dumps(device.parameters)
        ))
        
        conn.commit()
        conn.close()
    
    def load_devices_from_db(self):
        """Load devices from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM devices')
        rows = cursor.fetchall()
        
        for row in rows:
            device = Device(
                device_id=row[0],
                serial_number=row[1],
                manufacturer=row[2],
                model=row[3],
                software_version=row[4],
                hardware_version=row[5],
                connection_request_url=row[6],
                last_inform=datetime.fromisoformat(row[7]) if row[7] else None,
                parameters=json.loads(row[8]) if row[8] else {}
            )
            self.devices[device.device_id] = device
        
        conn.close()
        logger.info(f"Loaded {len(self.devices)} devices from database")
    
    async def cleanup_task(self):
        """Background task to clean up old devices"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                cutoff_time = datetime.now() - timedelta(hours=self.cleanup_hours)
                
                devices_to_remove = []
                for device_id, device in self.devices.items():
                    if device.last_inform and device.last_inform < cutoff_time:
                        devices_to_remove.append(device_id)
                
                for device_id in devices_to_remove:
                    del self.devices[device_id]
                    # Remove from database
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
                    conn.commit()
                    conn.close()
                    logger.info(f"Cleaned up old device: {device_id}")
                
                if devices_to_remove:
                    logger.info(f"Cleaned up {len(devices_to_remove)} old devices")
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_post('/tr069', self.handle_tr069_request)
        self.app.router.add_get('/devices', self.get_devices)
        self.app.router.add_get('/devices/{device_id}', self.get_device)
        self.app.router.add_post('/devices/{device_id}/parameters', self.set_device_parameters)
        self.app.router.add_get('/devices/{device_id}/parameters', self.get_device_parameters)
        self.app.router.add_get('/', self.web_interface)
        self.app.router.add_static('/static', 'static')
    
    async def handle_tr069_request(self, request: Request) -> Response:
        """Handle TR-069 SOAP requests"""
        try:
            body = await request.text()
            logger.info(f"Received TR-069 request: {body[:200]}...")
            
            # Parse SOAP envelope
            root = ET.fromstring(body)
            
            # Extract SOAP body
            soap_body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            if soap_body is None:
                return self.create_soap_fault("Invalid SOAP envelope")
            
            # Get the first child (the actual method)
            method_element = soap_body[0]
            method_name = method_element.tag.split('}')[-1] if '}' in method_element.tag else method_element.tag
            
            logger.info(f"Processing method: {method_name}")
            
            # Route to appropriate handler
            handler = getattr(self, f'handle_{method_name.lower()}', None)
            if handler:
                response = await handler(method_element)
                return Response(text=response, content_type='text/xml; charset=utf-8')
            else:
                return self.create_soap_fault(f"Unknown method: {method_name}")
                
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return self.create_soap_fault("Invalid XML")
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return self.create_soap_fault("Internal server error")
    
    def create_soap_fault(self, fault_string: str, fault_code: str = "Server") -> Response:
        """Create SOAP fault response"""
        fault_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>{fault_code}</faultcode>
            <faultstring>{fault_string}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""
        return Response(text=fault_xml, content_type='text/xml; charset=utf-8')
    
    def create_soap_response(self, method_name: str, response_data: Dict[str, Any]) -> str:
        """Create SOAP response"""
        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Body>
        <cwmp:{method_name}Response>
"""
        
        for key, value in response_data.items():
            if isinstance(value, dict):
                response_xml += f"            <{key}>\n"
                for sub_key, sub_value in value.items():
                    response_xml += f"                <{sub_key}>{sub_value}</{sub_key}>\n"
                response_xml += f"            </{key}>\n"
            else:
                response_xml += f"            <{key}>{value}</{key}>\n"
        
        response_xml += f"""        </cwmp:{method_name}Response>
    </soap:Body>
</soap:Envelope>"""
        return response_xml
    
    async def handle_inform(self, element: ET.Element) -> str:
        """Handle Inform method"""
        try:
            # Extract device information
            device_id = element.find('.//DeviceId/SerialNumber').text
            manufacturer = element.find('.//DeviceId/Manufacturer').text
            model = element.find('.//DeviceId/ModelName').text
            software_version = element.find('.//SoftwareVersion').text
            hardware_version = element.find('.//HardwareVersion').text
            
            # Extract connection request URL
            connection_request_url = element.find('.//ConnectionRequestURL').text
            
            # Create or update device
            device = Device(
                device_id=device_id,
                serial_number=device_id,
                manufacturer=manufacturer,
                model=model,
                software_version=software_version,
                hardware_version=hardware_version,
                connection_request_url=connection_request_url,
                last_inform=datetime.now()
            )
            
            self.devices[device_id] = device
            self.save_device_to_db(device)
            logger.info(f"Device registered/updated: {device_id}")
            
            # Create response
            response_data = {
                "MaxEnvelopes": "1"
            }
            
            return self.create_soap_response("Inform", response_data)
            
        except Exception as e:
            logger.error(f"Error in Inform handler: {e}")
            return self.create_soap_fault("Error processing Inform")
    
    async def handle_getparametervalues(self, element: ET.Element) -> str:
        """Handle GetParameterValues method"""
        try:
            device_id = element.find('.//DeviceId/SerialNumber').text
            parameter_names = [param.text for param in element.findall('.//ParameterNames/string')]
            
            device = self.devices.get(device_id)
            if not device:
                return self.create_soap_fault("Device not found")
            
            # Get parameter values
            parameter_values = []
            for param_name in parameter_names:
                value = device.parameters.get(param_name, "")
                parameter_values.append({
                    "Name": param_name,
                    "Value": value
                })
            
            response_data = {
                "ParameterList": {
                    "ParameterValueStruct": parameter_values
                }
            }
            
            return self.create_soap_response("GetParameterValues", response_data)
            
        except Exception as e:
            logger.error(f"Error in GetParameterValues handler: {e}")
            return self.create_soap_fault("Error processing GetParameterValues")
    
    async def handle_setparametervalues(self, element: ET.Element) -> str:
        """Handle SetParameterValues method"""
        try:
            device_id = element.find('.//DeviceId/SerialNumber').text
            parameter_list = element.find('.//ParameterList')
            
            device = self.devices.get(device_id)
            if not device:
                return self.create_soap_fault("Device not found")
            
            # Update parameter values
            for param in parameter_list.findall('ParameterValueStruct'):
                name = param.find('Name').text
                value = param.find('Value').text
                device.parameters[name] = value
                logger.info(f"Set parameter {name} = {value} for device {device_id}")
            
            # Save updated device to database
            self.save_device_to_db(device)
            
            response_data = {
                "Status": "0"  # 0 = success
            }
            
            return self.create_soap_response("SetParameterValues", response_data)
            
        except Exception as e:
            logger.error(f"Error in SetParameterValues handler: {e}")
            return self.create_soap_fault("Error processing SetParameterValues")
    
    async def handle_getparameternames(self, element: ET.Element) -> str:
        """Handle GetParameterNames method"""
        try:
            device_id = element.find('.//DeviceId/SerialNumber').text
            next_level = element.find('.//NextLevel').text == 'true'
            parameter_path = element.find('.//ParameterPath').text
            
            device = self.devices.get(device_id)
            if not device:
                return self.create_soap_fault("Device not found")
            
            # Generate parameter names based on path
            parameter_names = self.generate_parameter_names(parameter_path, next_level)
            
            response_data = {
                "ParameterList": {
                    "ParameterInfoStruct": parameter_names
                }
            }
            
            return self.create_soap_response("GetParameterNames", response_data)
            
        except Exception as e:
            logger.error(f"Error in GetParameterNames handler: {e}")
            return self.create_soap_fault("Error processing GetParameterNames")
    
    def generate_parameter_names(self, path: str, next_level: bool) -> List[Dict[str, Any]]:
        """Generate parameter names based on path"""
        parameters = []
        
        if path == "." or path == "":
            # Root level parameters
            parameters.extend([
                {"Name": "Device.DeviceInfo.Manufacturer", "Writable": "false"},
                {"Name": "Device.DeviceInfo.ModelName", "Writable": "false"},
                {"Name": "Device.DeviceInfo.SoftwareVersion", "Writable": "false"},
                {"Name": "Device.DeviceInfo.HardwareVersion", "Writable": "false"},
                {"Name": "Device.DeviceInfo.SerialNumber", "Writable": "false"},
                {"Name": "Device.ManagementServer.URL", "Writable": "true"},
                {"Name": "Device.ManagementServer.Username", "Writable": "true"},
                {"Name": "Device.ManagementServer.Password", "Writable": "true"},
                {"Name": "Device.ManagementServer.PeriodicInformInterval", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.Enable", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.SSID", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.Password", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.Channel", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.ChannelWidth", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.SecurityMode", "Writable": "true"},
            ])
        elif path.startswith("Device.WiFi.Radio.1."):
            # WiFi radio parameters
            parameters.extend([
                {"Name": "Device.WiFi.Radio.1.Enable", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.SSID", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.Password", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.Channel", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.ChannelWidth", "Writable": "true"},
                {"Name": "Device.WiFi.Radio.1.SecurityMode", "Writable": "true"},
            ])
        
        return parameters
    
    async def get_devices(self, request: Request) -> Response:
        """Get all registered devices (REST API)"""
        devices_data = []
        for device_id, device in self.devices.items():
            devices_data.append({
                "device_id": device_id,
                "serial_number": device.serial_number,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "software_version": device.software_version,
                "hardware_version": device.hardware_version,
                "last_inform": device.last_inform.isoformat() if device.last_inform else None,
                "parameters": device.parameters
            })
        
        return web.json_response(devices_data)
    
    async def get_device(self, request: Request) -> Response:
        """Get specific device (REST API)"""
        device_id = request.match_info['device_id']
        device = self.devices.get(device_id)
        
        if not device:
            return web.json_response({"error": "Device not found"}, status=404)
        
        device_data = {
            "device_id": device_id,
            "serial_number": device.serial_number,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "software_version": device.software_version,
            "hardware_version": device.hardware_version,
            "last_inform": device.last_inform.isoformat() if device.last_inform else None,
            "parameters": device.parameters
        }
        
        return web.json_response(device_data)
    
    async def set_device_parameters(self, request: Request) -> Response:
        """Set device parameters (REST API)"""
        device_id = request.match_info['device_id']
        device = self.devices.get(device_id)
        
        if not device:
            return web.json_response({"error": "Device not found"}, status=404)
        
        try:
            data = await request.json()
            device.parameters.update(data)
            logger.info(f"Updated parameters for device {device_id}: {data}")
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Error setting parameters: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def get_device_parameters(self, request: Request) -> Response:
        """Get device parameters (REST API)"""
        device_id = request.match_info['device_id']
        device = self.devices.get(device_id)
        
        if not device:
            return web.json_response({"error": "Device not found"}, status=404)
        
        return web.json_response(device.parameters)
    
    async def web_interface(self, request: Request) -> Response:
        """Simple web interface for device management"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>TR-069 Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .device { border: 1px solid #ccc; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .device h3 { margin-top: 0; }
        .parameter { margin: 5px 0; }
        .parameter input { width: 200px; margin-left: 10px; }
        button { background: #007cba; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; }
        button:hover { background: #005a87; }
        .status { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>TR-069 Server - Device Management</h1>
    <div id="devices"></div>
    
    <script>
        async function loadDevices() {
            try {
                const response = await fetch('/devices');
                const devices = await response.json();
                const container = document.getElementById('devices');
                
                if (devices.length === 0) {
                    container.innerHTML = '<p>No devices registered yet.</p>';
                    return;
                }
                
                container.innerHTML = devices.map(device => `
                    <div class="device">
                        <h3>${device.manufacturer} ${device.model}</h3>
                        <p><strong>Serial:</strong> ${device.serial_number}</p>
                        <p><strong>Software Version:</strong> ${device.software_version}</p>
                        <p><strong>Last Inform:</strong> ${device.last_inform || 'Never'}</p>
                        <div>
                            <h4>Parameters:</h4>
                            <div class="parameter">
                                <label>WiFi Enable:</label>
                                <input type="checkbox" id="wifi_enable_${device.device_id}" 
                                       ${device.parameters['Device.WiFi.Radio.1.Enable'] === 'true' ? 'checked' : ''}>
                            </div>
                            <div class="parameter">
                                <label>WiFi SSID:</label>
                                <input type="text" id="wifi_ssid_${device.device_id}" 
                                       value="${device.parameters['Device.WiFi.Radio.1.SSID'] || ''}">
                            </div>
                            <div class="parameter">
                                <label>WiFi Password:</label>
                                <input type="password" id="wifi_password_${device.device_id}" 
                                       value="${device.parameters['Device.WiFi.Radio.1.Password'] || ''}">
                            </div>
                            <div class="parameter">
                                <label>WiFi Channel:</label>
                                <input type="number" id="wifi_channel_${device.device_id}" 
                                       value="${device.parameters['Device.WiFi.Radio.1.Channel'] || '6'}">
                            </div>
                            <button onclick="updateDevice('${device.device_id}')">Update Device</button>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading devices:', error);
            }
        }
        
        async function updateDevice(deviceId) {
            const parameters = {
                'Device.WiFi.Radio.1.Enable': document.getElementById(`wifi_enable_${deviceId}`).checked.toString(),
                'Device.WiFi.Radio.1.SSID': document.getElementById(`wifi_ssid_${deviceId}`).value,
                'Device.WiFi.Radio.1.Password': document.getElementById(`wifi_password_${deviceId}`).value,
                'Device.WiFi.Radio.1.Channel': document.getElementById(`wifi_channel_${deviceId}`).value
            };
            
            try {
                const response = await fetch(`/devices/${deviceId}/parameters`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(parameters)
                });
                
                if (response.ok) {
                    alert('Device updated successfully!');
                    loadDevices();
                } else {
                    alert('Error updating device');
                }
            } catch (error) {
                console.error('Error updating device:', error);
                alert('Error updating device');
            }
        }
        
        // Load devices on page load
        loadDevices();
        
        // Refresh every 30 seconds
        setInterval(loadDevices, 30000);
    </script>
</body>
</html>
        """
        return Response(text=html, content_type='text/html')
    
    async def start_server(self):
        """Start the TR-069 server"""
        logger.info(f"Starting TR-069 server on {self.host}:{self.port}")
        
        # Start HTTP server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"TR-069 server started successfully!")
        logger.info(f"HTTP server running on http://{self.host}:{self.port}")
        logger.info(f"Web interface available at http://{self.host}:{self.port}/")
        logger.info(f"TR-069 endpoint: http://{self.host}:{self.port}/tr069")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()

async def main():
    """Main entry point"""
    server = TR069Server()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())