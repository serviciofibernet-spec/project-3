#!/usr/bin/env python3
"""
TR-069 (CWMP) Server Implementation
A complete TR-069 ACS (Auto Configuration Server) implementation in Python
"""

import asyncio
import logging
import ssl
import argparse
from datetime import datetime
from typing import Dict, Optional, List
from aiohttp import web, web_request
from aiohttp.web_response import Response
import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import hashlib
import secrets
import json
import os

# Import our modules
from config import ConfigManager, setup_logging
from device_manager import DeviceManager
from auth_security import AuthManager, SecurityManager
from cwmp_handlers import CWMPHandlers
from web_interface import WebInterface

logger = logging.getLogger(__name__)

class TR069Server:
    """Main TR-069 ACS Server class"""
    
    def __init__(self, config_file='config/server_config.json'):
        # Load configuration
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.load_config()
        
        # Setup logging
        setup_logging(self.config.logging)
        
        # Initialize components
        self.device_manager = DeviceManager(self.config.database.devices_db)
        self.auth_manager = AuthManager(self.config.database.auth_db)
        self.security_manager = SecurityManager()
        self.cwmp_handlers = CWMPHandlers()
        
        # Create web application
        self.app = web.Application()
        self.app['device_manager'] = self.device_manager
        self.app['auth_manager'] = self.auth_manager
        self.app['security_manager'] = self.security_manager
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup HTTP routes for TR-069 communication"""
        # CWMP endpoints
        self.app.router.add_post('/', self.handle_cwmp_request)
        self.app.router.add_get('/', self.handle_info_request)
        
        # API endpoints
        self.app.router.add_get('/status', self.handle_status_request)
        self.app.router.add_get('/devices', self.handle_devices_request)
        
        # Web interface routes
        self.web_interface.setup_routes(self.app)
        
    async def handle_cwmp_request(self, request: web_request.Request) -> Response:
        """Handle CWMP requests from CPE devices"""
        try:
            # Get request body
            body = await request.read()
            content_type = request.headers.get('Content-Type', '')
            
            logger.info(f"Received CWMP request from {request.remote}")
            logger.debug(f"Content-Type: {content_type}")
            logger.debug(f"Body length: {len(body)}")
            
            # Parse SOAP envelope
            if body:
                try:
                    root = ET.fromstring(body)
                    response = await self.process_cwmp_message(root, request)
                except ET.ParseError as e:
                    logger.error(f"XML parsing error: {e}")
                    return web.Response(status=400, text="Invalid XML")
            else:
                # Empty request - send Inform response
                response = self.create_empty_response()
            
            return web.Response(
                body=response,
                content_type='text/xml; charset=utf-8',
                headers={'SOAPAction': ''}
            )
            
        except Exception as e:
            logger.error(f"Error handling CWMP request: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def process_cwmp_message(self, root: ET.Element, request: web_request.Request) -> str:
        """Process CWMP SOAP message"""
        # Extract SOAP body
        soap_body = self.find_soap_body(root)
        if soap_body is None:
            return self.create_fault_response("Invalid SOAP envelope")
        
        # Determine message type
        for child in soap_body:
            tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag_name == 'Inform':
                return await self.handle_inform(child, request)
            elif tag_name == 'GetRPCMethodsResponse':
                return self.handle_get_rpc_methods_response(child)
            elif tag_name == 'GetParameterValuesResponse':
                return self.handle_get_parameter_values_response(child)
            elif tag_name == 'SetParameterValuesResponse':
                return self.handle_set_parameter_values_response(child)
            elif tag_name == 'TransferCompleteResponse':
                return self.handle_transfer_complete_response(child)
            else:
                logger.warning(f"Unknown CWMP message type: {tag_name}")
        
        return self.create_empty_response()
    
    def find_soap_body(self, root: ET.Element) -> Optional[ET.Element]:
        """Find SOAP Body element in the XML"""
        # Handle different namespace prefixes
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name.lower() == 'body':
                return elem
        return None
    
    async def handle_inform(self, inform_elem: ET.Element, request: web_request.Request) -> str:
        """Handle Inform message from CPE"""
        try:
            # Extract device information
            device_id = self.extract_device_id(inform_elem)
            event_codes = self.extract_event_codes(inform_elem)
            parameters = self.extract_parameters(inform_elem)
            
            logger.info(f"Inform received from device: {device_id}")
            logger.info(f"Event codes: {event_codes}")
            
            # Register device with device manager
            device_info = {
                'serial_number': device_id,
                'ip_address': request.remote,
                'parameters': parameters,
                'events': event_codes,
                'manufacturer': parameters.get('Device.DeviceInfo.Manufacturer', ''),
                'model': parameters.get('Device.DeviceInfo.ModelName', ''),
                'software_version': parameters.get('Device.DeviceInfo.SoftwareVersion', ''),
                'hardware_version': parameters.get('Device.DeviceInfo.HardwareVersion', ''),
                'connection_request_url': parameters.get('Device.ManagementServer.ConnectionRequestURL', '')
            }
            
            self.device_manager.register_device(device_info)
            
            # Create InformResponse
            return self.create_inform_response()
            
        except Exception as e:
            logger.error(f"Error handling Inform: {e}")
            return self.create_fault_response("Error processing Inform")
    
    def extract_device_id(self, inform_elem: ET.Element) -> str:
        """Extract device ID from Inform message"""
        for elem in inform_elem.iter():
            if 'DeviceId' in elem.tag:
                for child in elem:
                    if 'SerialNumber' in child.tag:
                        return child.text or "unknown"
        return "unknown"
    
    def extract_event_codes(self, inform_elem: ET.Element) -> List[str]:
        """Extract event codes from Inform message"""
        events = []
        for elem in inform_elem.iter():
            if 'Event' in elem.tag and elem.text:
                events.append(elem.text)
        return events
    
    def extract_parameters(self, inform_elem: ET.Element) -> Dict[str, str]:
        """Extract parameters from Inform message"""
        parameters = {}
        for elem in inform_elem.iter():
            if 'ParameterValueStruct' in elem.tag:
                name = None
                value = None
                for child in elem:
                    if 'Name' in child.tag:
                        name = child.text
                    elif 'Value' in child.tag:
                        value = child.text
                if name and value is not None:
                    parameters[name] = value
        return parameters
    
    def create_inform_response(self) -> str:
        """Create InformResponse SOAP message"""
        soap_env = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:InformResponse>
            <MaxEnvelopes>1</MaxEnvelopes>
        </cwmp:InformResponse>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_empty_response(self) -> str:
        """Create empty SOAP response"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header/>
    <soap:Body/>
</soap:Envelope>'''
    
    def create_fault_response(self, fault_string: str) -> str:
        """Create SOAP fault response"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>Server</faultcode>
            <faultstring>{fault_string}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
    
    def handle_get_rpc_methods_response(self, elem: ET.Element) -> str:
        """Handle GetRPCMethodsResponse"""
        logger.info("Received GetRPCMethodsResponse")
        return self.create_empty_response()
    
    def handle_get_parameter_values_response(self, elem: ET.Element) -> str:
        """Handle GetParameterValuesResponse"""
        logger.info("Received GetParameterValuesResponse")
        return self.create_empty_response()
    
    def handle_set_parameter_values_response(self, elem: ET.Element) -> str:
        """Handle SetParameterValuesResponse"""
        logger.info("Received SetParameterValuesResponse")
        return self.create_empty_response()
    
    def handle_transfer_complete_response(self, elem: ET.Element) -> str:
        """Handle TransferCompleteResponse"""
        logger.info("Received TransferCompleteResponse")
        return self.create_empty_response()
    
    async def handle_info_request(self, request: web_request.Request) -> Response:
        """Handle HTTP GET requests for server info"""
        info = {
            'server': 'TR-069 ACS Server',
            'version': '1.0',
            'status': 'running',
            'connected_devices': len(self.devices),
            'uptime': 'N/A'
        }
        return web.json_response(info)
    
    async def handle_status_request(self, request: web_request.Request) -> Response:
        """Handle status requests"""
        devices = self.device_manager.get_all_devices()
        stats = self.device_manager.get_device_statistics()
        
        status = {
            'server_status': 'running',
            'connected_devices': stats['total_devices'],
            'online_devices': stats['online_devices'],
            'offline_devices': stats['offline_devices'],
            'manufacturers': stats['manufacturers'],
            'models': stats['models'],
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        return web.json_response(status)
    
    async def handle_devices_request(self, request: web_request.Request) -> Response:
        """Handle devices list requests"""
        devices = self.device_manager.get_all_devices()
        devices_info = {}
        
        for serial_number, device in devices.items():
            devices_info[serial_number] = {
                'serial_number': device.serial_number,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'software_version': device.software_version,
                'last_contact': device.last_contact,
                'ip_address': device.ip_address,
                'status': device.status,
                'parameter_count': len(device.parameters),
                'events': device.events
            }
        
        return web.json_response(devices_info)
    
    async def start_server(self):
        """Start the TR-069 server"""
        try:
            # Setup SSL context if enabled
            ssl_context = None
            if self.config.server.ssl_enabled:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(
                    self.config.server.ssl_cert_path,
                    self.config.server.ssl_key_path
                )
            
            # Create and start server
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(
                runner,
                self.config.server.host,
                self.config.server.port,
                ssl_context=ssl_context
            )
            
            await site.start()
            
            protocol = "HTTPS" if self.config.server.ssl_enabled else "HTTP"
            logger.info(f"TR-069 server started on {self.config.server.host}:{self.config.server.port}")
            logger.info(f"Protocol: {protocol}")
            logger.info(f"Access URLs:")
            logger.info(f"  - Server info: {protocol.lower()}://{self.config.server.host}:{self.config.server.port}/")
            logger.info(f"  - Status: {protocol.lower()}://{self.config.server.host}:{self.config.server.port}/status")
            logger.info(f"  - Devices: {protocol.lower()}://{self.config.server.host}:{self.config.server.port}/devices")
            
            # Start background tasks
            asyncio.create_task(self.background_tasks())
            
            # Keep the server running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise
    
    async def background_tasks(self):
        """Background maintenance tasks"""
        while True:
            try:
                # Check device status every 5 minutes
                self.device_manager.check_device_status()
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Error in background tasks: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

def main():
    """Main function to start the TR-069 server"""
    parser = argparse.ArgumentParser(description='TR-069 ACS Server')
    parser.add_argument('--config', default='config/server_config.json', help='Configuration file path')
    parser.add_argument('--host', help='Host to bind to (overrides config)')
    parser.add_argument('--port', type=int, help='Port to bind to (overrides config)')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL/TLS (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    try:
        # Create server with configuration
        server = TR069Server(config_file=args.config)
        
        # Override configuration with command line arguments
        if args.host:
            server.config.server.host = args.host
        if args.port:
            server.config.server.port = args.port
        if args.ssl:
            server.config.server.ssl_enabled = True
        if args.debug:
            server.config.logging.level = 'DEBUG'
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Print startup information
        print("=" * 50)
        print("    TR-069 ACS Server Starting")
        print("=" * 50)
        print(f"Configuration: {args.config}")
        print(f"Host: {server.config.server.host}")
        print(f"Port: {server.config.server.port}")
        print(f"SSL: {'Enabled' if server.config.server.ssl_enabled else 'Disabled'}")
        print(f"Log Level: {server.config.logging.level}")
        print("=" * 50)
        
        # Start server
        asyncio.run(server.start_server())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"Server error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    main()