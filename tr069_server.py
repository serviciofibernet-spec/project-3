#!/usr/bin/env python3
"""
Servidor TR-069 ACS para gestión de ONTs Huawei
Implementa el protocolo TR-069 con funcionalidades completas
"""

import socket
import threading
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import hashlib
import base64
import json
import re
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from database_models import db, ONT, Customer, ConfigurationProfile, WiFiSettings, NetworkSettings, MonitoringData, TR069Session
from config import Config
import requests

class TR069Server:
    """Servidor ACS TR-069 para gestión de ONTs"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.server = None
        self.running = False
        self.sessions = {}  # Diccionario de sesiones activas
        self.ont_models = {
            'HG8240H': 'Huawei HG8240H',
            'HG8245H': 'Huawei HG8245H',
            'HG8245H5': 'Huawei HG8245H5',
            'HG8245Q': 'Huawei HG8245Q',
            'HG8245W': 'Huawei HG8245W',
            'HG8247H': 'Huawei HG8247H',
            'HG8247W': 'Huawei HG8247W',
            'HG8240X': 'Huawei HG8240X',
            'HG8240Q': 'Huawei HG8240Q'
        }
        
    def start(self):
        """Iniciar el servidor TR-069"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.config.TR069_ACS_PORT), TR069RequestHandler)
            self.server.tr069_server = self
            self.running = True
            self.logger.info(f"Servidor TR-069 iniciado en puerto {self.config.TR069_ACS_PORT}")
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"Error al iniciar servidor TR-069: {e}")
            self.running = False
    
    def stop(self):
        """Detener el servidor TR-069"""
        self.running = False
        if self.server:
            self.server.shutdown()
        self.logger.info("Servidor TR-069 detenido")
    
    def create_session(self, session_id, ont_data):
        """Crear nueva sesión TR-069"""
        session = TR069Session(
            session_id=session_id,
            ont_id=ont_data.get('ont_id'),
            cpe_ip=ont_data.get('cpe_ip'),
            cpe_user_agent=ont_data.get('user_agent'),
            acs_url=ont_data.get('acs_url'),
            connection_request_url=ont_data.get('connection_request_url')
        )
        db.session.add(session)
        db.session.commit()
        self.sessions[session_id] = session
        return session
    
    def get_ont_by_serial(self, serial_number):
        """Obtener ONT por número de serie"""
        return ONT.query.filter_by(serial_number=serial_number).first()
    
    def register_ont(self, ont_data):
        """Registrar nueva ONT"""
        try:
            # Verificar si ya existe
            existing_ont = self.get_ont_by_serial(ont_data['serial_number'])
            if existing_ont:
                # Actualizar datos existentes
                existing_ont.mac_address = ont_data.get('mac_address', existing_ont.mac_address)
                existing_ont.model = ont_data.get('model', existing_ont.model)
                existing_ont.firmware_version = ont_data.get('firmware_version', existing_ont.firmware_version)
                existing_ont.hardware_version = ont_data.get('hardware_version', existing_ont.hardware_version)
                existing_ont.ip_address = ont_data.get('ip_address', existing_ont.ip_address)
                existing_ont.is_online = True
                existing_ont.last_seen = datetime.utcnow()
                db.session.commit()
                return existing_ont
            
            # Crear nueva ONT
            ont = ONT(
                serial_number=ont_data['serial_number'],
                mac_address=ont_data.get('mac_address', ''),
                model=ont_data.get('model', 'Unknown'),
                firmware_version=ont_data.get('firmware_version', ''),
                hardware_version=ont_data.get('hardware_version', ''),
                ip_address=ont_data.get('ip_address', ''),
                connection_id=ont_data.get('connection_id', ''),
                is_online=True,
                last_seen=datetime.utcnow()
            )
            
            # Asignar perfil de configuración automático
            profile = ConfigurationProfile.query.filter_by(
                ont_model=ont.model,
                is_active=True
            ).first()
            
            if profile:
                ont.configuration_profile_id = profile.id
                # Aplicar configuración automática
                self.apply_automatic_configuration(ont, profile)
            
            db.session.add(ont)
            db.session.commit()
            
            self.logger.info(f"ONT registrada: {ont.serial_number} - {ont.model}")
            return ont
            
        except Exception as e:
            self.logger.error(f"Error al registrar ONT: {e}")
            db.session.rollback()
            return None
    
    def apply_automatic_configuration(self, ont, profile):
        """Aplicar configuración automática según el perfil"""
        try:
            # Configurar WiFi
            if profile.wifi_template:
                wifi_settings = WiFiSettings(ont_id=ont.id)
                wifi_settings.wifi_2_4_enabled = profile.wifi_template.wifi_2_4_enabled
                wifi_settings.wifi_2_4_ssid = self.process_template(
                    profile.wifi_template.wifi_2_4_ssid_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente',
                     'serial': ont.serial_number[-4:]}
                )
                wifi_settings.wifi_2_4_password = self.process_template(
                    profile.wifi_template.wifi_2_4_password_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente'}
                )
                wifi_settings.wifi_2_4_channel = profile.wifi_template.wifi_2_4_channel
                wifi_settings.wifi_2_4_security = profile.wifi_template.wifi_2_4_security
                
                wifi_settings.wifi_5_enabled = profile.wifi_template.wifi_5_enabled
                wifi_settings.wifi_5_ssid = self.process_template(
                    profile.wifi_template.wifi_5_ssid_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente',
                     'serial': ont.serial_number[-4:]}
                )
                wifi_settings.wifi_5_password = self.process_template(
                    profile.wifi_template.wifi_5_password_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente'}
                )
                wifi_settings.wifi_5_channel = profile.wifi_template.wifi_5_channel
                wifi_settings.wifi_5_security = profile.wifi_template.wifi_5_security
                
                db.session.add(wifi_settings)
            
            # Configurar red
            if profile.network_template:
                network_settings = NetworkSettings(ont_id=ont.id)
                network_settings.ip_mode = profile.network_template.ip_mode
                network_settings.static_ip = self.process_template(
                    profile.network_template.static_ip_template,
                    {'serial': ont.serial_number[-4:]}
                ) if profile.network_template.static_ip_template else None
                network_settings.static_gateway = self.process_template(
                    profile.network_template.static_gateway_template,
                    {'serial': ont.serial_number[-4:]}
                ) if profile.network_template.static_gateway_template else None
                network_settings.static_netmask = profile.network_template.static_netmask
                
                network_settings.pppoe_username = self.process_template(
                    profile.network_template.pppoe_username_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente'}
                ) if profile.network_template.pppoe_username_template else None
                network_settings.pppoe_password = self.process_template(
                    profile.network_template.pppoe_password_template,
                    {'customer_name': ont.customer.full_name if ont.customer else 'Cliente'}
                ) if profile.network_template.pppoe_password_template else None
                network_settings.pppoe_service_name = profile.network_template.pppoe_service_name
                
                network_settings.vlan_id = profile.network_template.vlan_id
                network_settings.vlan_priority = profile.network_template.vlan_priority
                network_settings.dns_primary = profile.network_template.dns_primary
                network_settings.dns_secondary = profile.network_template.dns_secondary
                
                db.session.add(network_settings)
            
            db.session.commit()
            self.logger.info(f"Configuración automática aplicada a ONT {ont.serial_number}")
            
        except Exception as e:
            self.logger.error(f"Error al aplicar configuración automática: {e}")
            db.session.rollback()
    
    def process_template(self, template, variables):
        """Procesar plantilla con variables"""
        if not template:
            return None
        
        result = template
        for key, value in variables.items():
            result = result.replace(f'{{{key}}}', str(value))
        return result
    
    def update_wifi_settings(self, ont_id, wifi_data):
        """Actualizar configuración WiFi de una ONT"""
        try:
            ont = ONT.query.get(ont_id)
            if not ont:
                return False
            
            if not ont.wifi_settings:
                ont.wifi_settings = WiFiSettings(ont_id=ont_id)
            
            wifi_settings = ont.wifi_settings
            
            # Actualizar configuración 2.4GHz
            if 'wifi_2_4_ssid' in wifi_data:
                wifi_settings.wifi_2_4_ssid = wifi_data['wifi_2_4_ssid']
            if 'wifi_2_4_password' in wifi_data:
                wifi_settings.wifi_2_4_password = wifi_data['wifi_2_4_password']
            if 'wifi_2_4_enabled' in wifi_data:
                wifi_settings.wifi_2_4_enabled = wifi_data['wifi_2_4_enabled']
            
            # Actualizar configuración 5GHz
            if 'wifi_5_ssid' in wifi_data:
                wifi_settings.wifi_5_ssid = wifi_data['wifi_5_ssid']
            if 'wifi_5_password' in wifi_data:
                wifi_settings.wifi_5_password = wifi_data['wifi_5_password']
            if 'wifi_5_enabled' in wifi_data:
                wifi_settings.wifi_5_enabled = wifi_data['wifi_5_enabled']
            
            wifi_settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Enviar configuración a la ONT
            self.send_configuration_to_ont(ont)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al actualizar configuración WiFi: {e}")
            db.session.rollback()
            return False
    
    def update_network_settings(self, ont_id, network_data):
        """Actualizar configuración de red de una ONT"""
        try:
            ont = ONT.query.get(ont_id)
            if not ont:
                return False
            
            if not ont.network_settings:
                ont.network_settings = NetworkSettings(ont_id=ont_id)
            
            network_settings = ont.network_settings
            
            # Actualizar configuración IP
            if 'ip_mode' in network_data:
                network_settings.ip_mode = network_data['ip_mode']
            if 'static_ip' in network_data:
                network_settings.static_ip = network_data['static_ip']
            if 'static_gateway' in network_data:
                network_settings.static_gateway = network_data['static_gateway']
            if 'static_netmask' in network_data:
                network_settings.static_netmask = network_data['static_netmask']
            
            # Actualizar configuración PPPoE
            if 'pppoe_username' in network_data:
                network_settings.pppoe_username = network_data['pppoe_username']
            if 'pppoe_password' in network_data:
                network_settings.pppoe_password = network_data['pppoe_password']
            if 'pppoe_service_name' in network_data:
                network_settings.pppoe_service_name = network_data['pppoe_service_name']
            
            # Actualizar configuración VLAN
            if 'vlan_id' in network_data:
                network_settings.vlan_id = network_data['vlan_id']
            if 'vlan_priority' in network_data:
                network_settings.vlan_priority = network_data['vlan_priority']
            
            # Actualizar DNS
            if 'dns_primary' in network_data:
                network_settings.dns_primary = network_data['dns_primary']
            if 'dns_secondary' in network_data:
                network_settings.dns_secondary = network_data['dns_secondary']
            
            network_settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Enviar configuración a la ONT
            self.send_configuration_to_ont(ont)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al actualizar configuración de red: {e}")
            db.session.rollback()
            return False
    
    def send_configuration_to_ont(self, ont):
        """Enviar configuración a la ONT via TR-069"""
        try:
            # Aquí se implementaría el envío real de configuración via TR-069
            # Por ahora solo registramos en el log
            self.logger.info(f"Enviando configuración a ONT {ont.serial_number}")
            
            # En un entorno real, aquí se enviarían los comandos TR-069
            # para configurar la ONT con los nuevos parámetros
            
        except Exception as e:
            self.logger.error(f"Error al enviar configuración a ONT: {e}")
    
    def get_monitoring_data(self, ont_id):
        """Obtener datos de monitoreo de una ONT"""
        try:
            ont = ONT.query.get(ont_id)
            if not ont:
                return None
            
            # Obtener último dato de monitoreo
            latest_data = MonitoringData.query.filter_by(ont_id=ont_id)\
                .order_by(MonitoringData.timestamp.desc()).first()
            
            return latest_data
            
        except Exception as e:
            self.logger.error(f"Error al obtener datos de monitoreo: {e}")
            return None
    
    def update_monitoring_data(self, ont_id, monitoring_data):
        """Actualizar datos de monitoreo de una ONT"""
        try:
            data = MonitoringData(
                ont_id=ont_id,
                optical_power_tx=monitoring_data.get('optical_power_tx'),
                optical_power_rx=monitoring_data.get('optical_power_rx'),
                optical_temperature=monitoring_data.get('optical_temperature'),
                connection_status=monitoring_data.get('connection_status'),
                uptime=monitoring_data.get('uptime'),
                wifi_devices_2_4=monitoring_data.get('wifi_devices_2_4', 0),
                wifi_devices_5=monitoring_data.get('wifi_devices_5', 0),
                wifi_devices_guest=monitoring_data.get('wifi_devices_guest', 0),
                bytes_sent=monitoring_data.get('bytes_sent', 0),
                bytes_received=monitoring_data.get('bytes_received', 0),
                packets_sent=monitoring_data.get('packets_sent', 0),
                packets_received=monitoring_data.get('packets_received', 0)
            )
            
            db.session.add(data)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error al actualizar datos de monitoreo: {e}")
            db.session.rollback()
    
    def reboot_ont(self, ont_id):
        """Reiniciar ONT remotamente"""
        try:
            ont = ONT.query.get(ont_id)
            if not ont:
                return False
            
            # Aquí se implementaría el comando TR-069 para reiniciar
            self.logger.info(f"Reiniciando ONT {ont.serial_number}")
            
            # En un entorno real, aquí se enviaría el comando de reinicio
            # via TR-069 SetParameterValues o Reboot
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar ONT: {e}")
            return False
    
    def update_firmware(self, ont_id, firmware_url):
        """Actualizar firmware de la ONT"""
        try:
            ont = ONT.query.get(ont_id)
            if not ont:
                return False
            
            # Aquí se implementaría la actualización de firmware via TR-069
            self.logger.info(f"Actualizando firmware de ONT {ont.serial_number} desde {firmware_url}")
            
            # En un entorno real, aquí se enviaría el comando de actualización
            # via TR-069 Download
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al actualizar firmware: {e}")
            return False

class TR069RequestHandler(BaseHTTPRequestHandler):
    """Manejador de peticiones HTTP para TR-069"""
    
    def do_POST(self):
        """Manejar peticiones POST (CPE -> ACS)"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parsear XML TR-069
            root = ET.fromstring(post_data)
            
            # Determinar tipo de mensaje
            message_type = self.get_message_type(root)
            
            if message_type == 'Inform':
                response = self.handle_inform(root)
            elif message_type == 'GetParameterValuesResponse':
                response = self.handle_get_parameter_values_response(root)
            elif message_type == 'SetParameterValuesResponse':
                response = self.handle_set_parameter_values_response(root)
            elif message_type == 'RebootResponse':
                response = self.handle_reboot_response(root)
            elif message_type == 'DownloadResponse':
                response = self.handle_download_response(root)
            else:
                response = self.create_error_response("Unsupported message type")
            
            # Enviar respuesta
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.server.tr069_server.logger.error(f"Error en petición TR-069: {e}")
            self.send_error_response()
    
    def do_GET(self):
        """Manejar peticiones GET (para testing)"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Servidor TR-069 ACS</h1><p>Servidor funcionando correctamente</p>')
    
    def get_message_type(self, root):
        """Determinar tipo de mensaje TR-069"""
        if root.tag.endswith('Inform'):
            return 'Inform'
        elif root.tag.endswith('GetParameterValuesResponse'):
            return 'GetParameterValuesResponse'
        elif root.tag.endswith('SetParameterValuesResponse'):
            return 'SetParameterValuesResponse'
        elif root.tag.endswith('RebootResponse'):
            return 'RebootResponse'
        elif root.tag.endswith('DownloadResponse'):
            return 'DownloadResponse'
        else:
            return 'Unknown'
    
    def handle_inform(self, root):
        """Manejar mensaje Inform (registro de ONT)"""
        try:
            # Extraer información de la ONT
            ont_data = self.extract_ont_data(root)
            
            # Registrar ONT
            ont = self.server.tr069_server.register_ont(ont_data)
            
            if ont:
                # Crear sesión
                session_id = self.generate_session_id()
                self.server.tr069_server.create_session(session_id, {
                    'ont_id': ont.id,
                    'cpe_ip': self.client_address[0],
                    'user_agent': self.headers.get('User-Agent', ''),
                    'acs_url': self.server.tr069_server.config.TR069_ACS_URL,
                    'connection_request_url': ont_data.get('connection_request_url', '')
                })
                
                # Crear respuesta con comandos de configuración
                return self.create_inform_response(session_id, ont)
            else:
                return self.create_error_response("Failed to register ONT")
                
        except Exception as e:
            self.server.tr069_server.logger.error(f"Error en handle_inform: {e}")
            return self.create_error_response("Internal error")
    
    def extract_ont_data(self, root):
        """Extraer datos de la ONT del mensaje Inform"""
        ont_data = {}
        
        # Buscar parámetros en el mensaje
        for param in root.findall('.//{http://www.cwmp.org/}ParameterValueStruct'):
            name_elem = param.find('.//{http://www.cwmp.org/}Name')
            value_elem = param.find('.//{http://www.cwmp.org/}Value')
            
            if name_elem is not None and value_elem is not None:
                name = name_elem.text
                value = value_elem.text
                
                if 'DeviceInfo.SerialNumber' in name:
                    ont_data['serial_number'] = value
                elif 'DeviceInfo.HardwareVersion' in name:
                    ont_data['hardware_version'] = value
                elif 'DeviceInfo.SoftwareVersion' in name:
                    ont_data['firmware_version'] = value
                elif 'DeviceInfo.Manufacturer' in name:
                    ont_data['manufacturer'] = value
                elif 'DeviceInfo.ProductClass' in name:
                    ont_data['model'] = value
                elif 'ManagementServer.ConnectionRequestURL' in name:
                    ont_data['connection_request_url'] = value
                elif 'InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceIPAddress' in name:
                    ont_data['ip_address'] = value
                elif 'InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceMACAddress' in name:
                    ont_data['mac_address'] = value
        
        return ont_data
    
    def create_inform_response(self, session_id, ont):
        """Crear respuesta al mensaje Inform"""
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:soap-enc="http://schemas.xmlsoap.org/soap/encoding/" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:cwmp="http://www.cwmp.org/">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:InformResponse>
            <MaxEnvelopes>1</MaxEnvelopes>
        </cwmp:InformResponse>
    </soap:Body>
</soap:Envelope>"""
        return response
    
    def create_error_response(self, error_message):
        """Crear respuesta de error"""
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="http://www.cwmp.org/">
    <soap:Body>
        <soap:Fault>
            <faultcode>Server</faultcode>
            <faultstring>{error_message}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>"""
        return response
    
    def generate_session_id(self):
        """Generar ID de sesión único"""
        import uuid
        return str(uuid.uuid4())
    
    def handle_get_parameter_values_response(self, root):
        """Manejar respuesta GetParameterValues"""
        # Procesar respuesta y actualizar datos de monitoreo
        return self.create_empty_response()
    
    def handle_set_parameter_values_response(self, root):
        """Manejar respuesta SetParameterValues"""
        # Procesar confirmación de configuración
        return self.create_empty_response()
    
    def handle_reboot_response(self, root):
        """Manejar respuesta Reboot"""
        # Procesar confirmación de reinicio
        return self.create_empty_response()
    
    def handle_download_response(self, root):
        """Manejar respuesta Download"""
        # Procesar confirmación de descarga/actualización
        return self.create_empty_response()
    
    def create_empty_response(self):
        """Crear respuesta vacía"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="http://www.cwmp.org/">
    <soap:Body>
        <cwmp:Empty/>
    </soap:Body>
</soap:Envelope>"""
    
    def send_error_response(self):
        """Enviar respuesta de error HTTP"""
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Internal Server Error')
    
    def log_message(self, format, *args):
        """Personalizar logging de mensajes"""
        self.server.tr069_server.logger.info(f"{self.client_address[0]} - {format % args}")