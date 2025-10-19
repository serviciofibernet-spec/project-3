#!/usr/bin/env python3
"""
TR069/CWMP Server Core Implementation
Handles SOAP/HTTP communications and RPC method dispatching
"""

import logging
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import os
import uuid
import hashlib
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SOAP namespaces
SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
SOAP_ENC = "http://schemas.xmlsoap.org/soap/encoding/"
CWMP_URN = "urn:dslforum-org:cwmp-1-2"
XSD = "http://www.w3.org/2001/XMLSchema"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

class DeviceManager:
    """Manages connected CPE devices"""
    
    def __init__(self):
        self.devices = {}
        self.lock = threading.Lock()
        self.data_dir = "data/devices"
        os.makedirs(self.data_dir, exist_ok=True)
        self.load_devices()
    
    def load_devices(self):
        """Load devices from persistent storage"""
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    device_id = filename[:-5]
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        self.devices[device_id] = json.load(f)
                        logger.info(f"Loaded device: {device_id}")
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
    
    def save_device(self, device_id):
        """Save device to persistent storage"""
        try:
            with self.lock:
                if device_id in self.devices:
                    filepath = os.path.join(self.data_dir, f"{device_id}.json")
                    with open(filepath, 'w') as f:
                        json.dump(self.devices[device_id], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving device {device_id}: {e}")
    
    def register_device(self, device_id, info):
        """Register or update a device"""
        with self.lock:
            if device_id not in self.devices:
                self.devices[device_id] = {
                    'id': device_id,
                    'first_seen': datetime.now().isoformat(),
                    'parameters': {},
                    'rpc_methods': [],
                    'connection_requests': []
                }
            
            self.devices[device_id].update({
                'last_seen': datetime.now().isoformat(),
                'info': info
            })
            self.save_device(device_id)
            logger.info(f"Device registered/updated: {device_id}")
    
    def get_device(self, device_id):
        """Get device information"""
        return self.devices.get(device_id)
    
    def update_parameters(self, device_id, parameters):
        """Update device parameters"""
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id]['parameters'].update(parameters)
                self.save_device(device_id)
    
    def list_devices(self):
        """List all registered devices"""
        return list(self.devices.keys())

class SessionManager:
    """Manages TR069 sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
    
    def create_session(self, device_id):
        """Create a new session for a device"""
        session_id = str(uuid.uuid4())
        with self.lock:
            self.sessions[session_id] = {
                'device_id': device_id,
                'created': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        return session_id
    
    def get_session(self, session_id):
        """Get session information"""
        return self.sessions.get(session_id)
    
    def update_activity(self, session_id):
        """Update last activity time for session"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id]['last_activity'] = datetime.now().isoformat()
    
    def cleanup_sessions(self, timeout_seconds=3600):
        """Remove expired sessions"""
        with self.lock:
            current_time = datetime.now()
            expired = []
            for sid, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session['last_activity'])
                if (current_time - last_activity).total_seconds() > timeout_seconds:
                    expired.append(sid)
            
            for sid in expired:
                del self.sessions[sid]
                logger.info(f"Session expired: {sid}")

class TR069Handler(BaseHTTPRequestHandler):
    """HTTP request handler for TR069 SOAP messages"""
    
    device_manager = DeviceManager()
    session_manager = SessionManager()
    
    def do_POST(self):
        """Handle POST requests (SOAP messages)"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Log incoming request
            logger.info(f"Incoming request from {self.client_address[0]}")
            logger.debug(f"Headers: {self.headers}")
            logger.debug(f"Body: {post_data.decode('utf-8', errors='ignore')[:500]}")
            
            # Parse SOAP envelope
            root = ET.fromstring(post_data)
            
            # Extract SOAP body
            body = root.find(f".//{{{SOAP_ENV}}}Body")
            if body is None:
                self.send_error(400, "Invalid SOAP message")
                return
            
            # Process the message
            response = self.process_soap_message(body, self.headers)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            self.send_error(400, "Invalid XML")
        except Exception as e:
            logger.error(f"Request handling error: {e}", exc_info=True)
            self.send_error(500, "Internal server error")
    
    def process_soap_message(self, body, headers):
        """Process SOAP message and return response"""
        # Find the RPC method
        for child in body:
            method_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            # Dispatch to appropriate handler
            handler_method = f"handle_{method_name}"
            if hasattr(self, handler_method):
                return getattr(self, handler_method)(child, headers)
            else:
                logger.warning(f"Unknown RPC method: {method_name}")
                return self.create_soap_fault("Server", f"Unknown method: {method_name}")
        
        # Empty body - send InformResponse
        return self.create_inform_response()
    
    def handle_Inform(self, element, headers):
        """Handle Inform RPC method"""
        logger.info("Processing Inform message")
        
        # Extract device information
        device_id = None
        manufacturer = None
        oui = None
        product_class = None
        serial_number = None
        
        # Parse DeviceId
        device_id_elem = element.find(".//DeviceId")
        if device_id_elem is not None:
            manufacturer = self.get_element_text(device_id_elem, "Manufacturer")
            oui = self.get_element_text(device_id_elem, "OUI")
            product_class = self.get_element_text(device_id_elem, "ProductClass")
            serial_number = self.get_element_text(device_id_elem, "SerialNumber")
            
            device_id = f"{oui}-{serial_number}"
        
        # Parse parameters
        parameters = {}
        param_list = element.find(".//ParameterList")
        if param_list is not None:
            for param in param_list.findall(".//ParameterValueStruct"):
                name = self.get_element_text(param, "Name")
                value = self.get_element_text(param, "Value")
                if name:
                    parameters[name] = value
        
        # Register device
        if device_id:
            device_info = {
                'manufacturer': manufacturer,
                'oui': oui,
                'product_class': product_class,
                'serial_number': serial_number
            }
            self.device_manager.register_device(device_id, device_info)
            self.device_manager.update_parameters(device_id, parameters)
            
            # Create session
            session_id = self.session_manager.create_session(device_id)
            logger.info(f"Created session {session_id} for device {device_id}")
        
        return self.create_inform_response()
    
    def handle_GetRPCMethods(self, element, headers):
        """Handle GetRPCMethods RPC method"""
        logger.info("Processing GetRPCMethods")
        
        methods = [
            "GetRPCMethods",
            "SetParameterValues",
            "GetParameterValues",
            "GetParameterNames",
            "SetParameterAttributes",
            "GetParameterAttributes",
            "AddObject",
            "DeleteObject",
            "Download",
            "Upload",
            "Reboot",
            "FactoryReset",
            "GetQueuedTransfers",
            "ScheduleInform",
            "SetVouchers",
            "GetOptions"
        ]
        
        return self.create_get_rpc_methods_response(methods)
    
    def handle_GetParameterValues(self, element, headers):
        """Handle GetParameterValues RPC method"""
        logger.info("Processing GetParameterValues")
        
        # Extract parameter names
        param_names = []
        param_names_elem = element.find(".//ParameterNames")
        if param_names_elem is not None:
            for string_elem in param_names_elem.findall(".//string"):
                if string_elem.text:
                    param_names.append(string_elem.text)
        
        # For now, return empty response
        return self.create_get_parameter_values_response({})
    
    def handle_SetParameterValues(self, element, headers):
        """Handle SetParameterValues RPC method"""
        logger.info("Processing SetParameterValues")
        
        # Extract parameters
        parameters = {}
        param_list = element.find(".//ParameterList")
        if param_list is not None:
            for param in param_list.findall(".//ParameterValueStruct"):
                name = self.get_element_text(param, "Name")
                value = self.get_element_text(param, "Value")
                if name:
                    parameters[name] = value
        
        logger.info(f"Setting parameters: {parameters}")
        
        return self.create_set_parameter_values_response(0)
    
    def handle_TransferComplete(self, element, headers):
        """Handle TransferComplete RPC method"""
        logger.info("Processing TransferComplete")
        
        command_key = self.get_element_text(element, "CommandKey")
        fault_struct = element.find(".//FaultStruct")
        
        if fault_struct is not None:
            fault_code = self.get_element_text(fault_struct, "FaultCode")
            fault_string = self.get_element_text(fault_struct, "FaultString")
            logger.info(f"Transfer failed - CommandKey: {command_key}, Fault: {fault_code} - {fault_string}")
        else:
            logger.info(f"Transfer completed successfully - CommandKey: {command_key}")
        
        return self.create_transfer_complete_response()
    
    def get_element_text(self, parent, tag_name):
        """Helper to get text from child element"""
        elem = parent.find(f".//{tag_name}")
        if elem is not None and elem.text:
            return elem.text.strip()
        return None
    
    def create_soap_envelope(self, body_content):
        """Create SOAP envelope with body content"""
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{SOAP_ENV}" xmlns:cwmp="{CWMP_URN}" xmlns:xsd="{XSD}" xmlns:xsi="{XSI}">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        {body_content}
    </soap:Body>
</soap:Envelope>'''
        return envelope
    
    def create_inform_response(self):
        """Create InformResponse message"""
        body = '''<cwmp:InformResponse>
            <MaxEnvelopes>1</MaxEnvelopes>
        </cwmp:InformResponse>'''
        return self.create_soap_envelope(body)
    
    def create_get_rpc_methods_response(self, methods):
        """Create GetRPCMethodsResponse message"""
        method_list = '\n'.join([f'            <string>{method}</string>' for method in methods])
        body = f'''<cwmp:GetRPCMethodsResponse>
            <MethodList soap:arrayType="xsd:string[{len(methods)}]">
{method_list}
            </MethodList>
        </cwmp:GetRPCMethodsResponse>'''
        return self.create_soap_envelope(body)
    
    def create_get_parameter_values_response(self, parameters):
        """Create GetParameterValuesResponse message"""
        param_list = []
        for name, value in parameters.items():
            param_list.append(f'''            <ParameterValueStruct>
                <Name>{name}</Name>
                <Value xsi:type="xsd:string">{value}</Value>
            </ParameterValueStruct>''')
        
        params_xml = '\n'.join(param_list) if param_list else ''
        body = f'''<cwmp:GetParameterValuesResponse>
            <ParameterList soap:arrayType="cwmp:ParameterValueStruct[{len(parameters)}]">
{params_xml}
            </ParameterList>
        </cwmp:GetParameterValuesResponse>'''
        return self.create_soap_envelope(body)
    
    def create_set_parameter_values_response(self, status):
        """Create SetParameterValuesResponse message"""
        body = f'''<cwmp:SetParameterValuesResponse>
            <Status>{status}</Status>
        </cwmp:SetParameterValuesResponse>'''
        return self.create_soap_envelope(body)
    
    def create_transfer_complete_response(self):
        """Create TransferCompleteResponse message"""
        body = '<cwmp:TransferCompleteResponse/>'
        return self.create_soap_envelope(body)
    
    def create_soap_fault(self, code, string):
        """Create SOAP Fault message"""
        body = f'''<soap:Fault>
            <faultcode>{code}</faultcode>
            <faultstring>{string}</faultstring>
        </soap:Fault>'''
        return self.create_soap_envelope(body)
    
    def log_message(self, format, *args):
        """Override to use custom logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

class TR069Server:
    """Main TR069 ACS Server"""
    
    def __init__(self, host='0.0.0.0', port=7547):
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self.thread = None
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load server configuration"""
        self.config_file = "config/server.json"
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.host = config.get('host', self.host)
                    self.port = config.get('port', self.port)
                    logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            # Create default config
            os.makedirs("config", exist_ok=True)
            self.save_config()
    
    def save_config(self):
        """Save server configuration"""
        config = {
            'host': self.host,
            'port': self.port,
            'description': 'TR069/CWMP ACS Server Configuration'
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def start(self):
        """Start the TR069 server"""
        try:
            self.server = HTTPServer((self.host, self.port), TR069Handler)
            self.running = True
            
            # Get actual IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            logger.info(f"TR069 ACS Server starting...")
            logger.info(f"Listening on {self.host}:{self.port}")
            logger.info(f"Local IP: {local_ip}:{self.port}")
            logger.info(f"ACS URL: http://{local_ip}:{self.port}/")
            
            # Start session cleanup thread
            cleanup_thread = threading.Thread(target=self.session_cleanup_worker)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            # Serve forever
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            self.stop()
    
    def stop(self):
        """Stop the TR069 server"""
        self.running = False
        if self.server:
            logger.info("Shutting down server...")
            self.server.shutdown()
            self.server.server_close()
            logger.info("Server stopped")
    
    def session_cleanup_worker(self):
        """Background worker to cleanup expired sessions"""
        while self.running:
            try:
                TR069Handler.session_manager.cleanup_sessions()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TR069/CWMP ACS Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=7547, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    server = TR069Server(host=args.host, port=args.port)
    server.start()

if __name__ == '__main__':
    main()