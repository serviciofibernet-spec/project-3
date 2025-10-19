#!/usr/bin/env python3
"""
TR-069 (CWMP) ACS Server Implementation
Copyright (c) 2025
"""

import logging
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import hashlib
import secrets
import json
import os

# Configuración del servidor
CONFIG_FILE = "tr069_config.json"

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tr069_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TR069Config:
    """Gestión de configuración del servidor TR-069"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Carga configuración desde archivo JSON"""
        default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 7547,
                "ssl_enabled": False
            },
            "auth": {
                "enabled": True,
                "username": "admin",
                "password": "admin123"
            },
            "database": {
                "type": "json",
                "path": "tr069_devices.json"
            },
            "cwmp": {
                "soap_namespace": "http://schemas.xmlsoap.org/soap/envelope/",
                "cwmp_namespace": "urn:dslforum-org:cwmp-1-0"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    logger.info(f"Configuración cargada desde {self.config_file}")
            except Exception as e:
                logger.error(f"Error al cargar configuración: {e}")
        else:
            self.save_config(default_config)
        
        return default_config
    
    def save_config(self, config=None):
        """Guarda configuración en archivo JSON"""
        if config:
            self.config = config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
    
    def get(self, *keys):
        """Obtiene valor de configuración usando claves anidadas"""
        value = self.config
        for key in keys:
            value = value.get(key, {})
        return value


class DeviceDatabase:
    """Base de datos simple de dispositivos"""
    
    def __init__(self, db_path="tr069_devices.json"):
        self.db_path = db_path
        self.devices = self.load_devices()
    
    def load_devices(self):
        """Carga dispositivos desde archivo JSON"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar dispositivos: {e}")
                return {}
        return {}
    
    def save_devices(self):
        """Guarda dispositivos en archivo JSON"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.devices, f, indent=4)
            logger.info("Dispositivos guardados")
        except Exception as e:
            logger.error(f"Error al guardar dispositivos: {e}")
    
    def add_or_update_device(self, device_id, device_info):
        """Añade o actualiza información de dispositivo"""
        if device_id not in self.devices:
            device_info['first_seen'] = datetime.now().isoformat()
            logger.info(f"Nuevo dispositivo registrado: {device_id}")
        
        device_info['last_seen'] = datetime.now().isoformat()
        self.devices[device_id] = device_info
        self.save_devices()
    
    def get_device(self, device_id):
        """Obtiene información de dispositivo"""
        return self.devices.get(device_id)
    
    def list_devices(self):
        """Lista todos los dispositivos"""
        return self.devices


class TR069RequestHandler(BaseHTTPRequestHandler):
    """Manejador de peticiones TR-069/CWMP"""
    
    config = None
    database = None
    
    def log_message(self, format, *args):
        """Override para usar el logger personalizado"""
        logger.info("%s - - %s" % (self.client_address[0], format % args))
    
    def do_GET(self):
        """Maneja peticiones GET - información del servidor"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>TR-069 ACS Server</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h1 {{ color: #333; }}
                    .status {{ color: green; font-weight: bold; }}
                    .info {{ margin: 20px 0; padding: 15px; background: #f0f0f0; border-radius: 4px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #4CAF50; color: white; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🌐 TR-069 ACS Server</h1>
                    <p class="status">✓ Servidor activo y funcionando</p>
                    
                    <div class="info">
                        <h2>Información del Servidor</h2>
                        <p><strong>Puerto:</strong> {self.config.get('server', 'port')}</p>
                        <p><strong>Hora del servidor:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Dispositivos registrados:</strong> {len(self.database.devices)}</p>
                    </div>
                    
                    <h2>Dispositivos Conectados</h2>
                    <table>
                        <tr>
                            <th>Device ID</th>
                            <th>Manufacturer</th>
                            <th>Model</th>
                            <th>Serial Number</th>
                            <th>Last Seen</th>
                        </tr>
                        {''.join([f"<tr><td>{dev_id}</td><td>{info.get('Manufacturer', 'N/A')}</td><td>{info.get('Model', 'N/A')}</td><td>{info.get('SerialNumber', 'N/A')}</td><td>{info.get('last_seen', 'N/A')}</td></tr>" for dev_id, info in self.database.devices.items()])}
                    </table>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Maneja peticiones POST - mensajes CWMP"""
        # Verificar autenticación
        if self.config.get('auth', 'enabled'):
            auth_header = self.headers.get('Authorization')
            if not self.check_auth(auth_header):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="TR-069 ACS"')
                self.end_headers()
                return
        
        # Leer contenido
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        logger.info(f"Petición recibida de {self.client_address[0]}")
        logger.debug(f"Datos recibidos: {post_data.decode('utf-8', errors='ignore')}")
        
        try:
            # Parsear mensaje SOAP
            root = ET.fromstring(post_data)
            
            # Extraer método CWMP
            cwmp_method = self.extract_cwmp_method(root)
            logger.info(f"Método CWMP: {cwmp_method}")
            
            # Procesar según el método
            if cwmp_method == 'Inform':
                response = self.handle_inform(root)
            elif cwmp_method == 'GetRPCMethods':
                response = self.handle_get_rpc_methods()
            elif cwmp_method == 'TransferComplete':
                response = self.handle_transfer_complete(root)
            else:
                logger.warning(f"Método no implementado: {cwmp_method}")
                response = self.create_empty_response()
            
            # Enviar respuesta
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.send_header('Content-Length', str(len(response)))
            self.send_header('SOAPAction', '')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except ET.ParseError as e:
            logger.error(f"Error al parsear XML: {e}")
            self.send_error(400, "Invalid XML")
        except Exception as e:
            logger.error(f"Error al procesar petición: {e}", exc_info=True)
            self.send_error(500, "Internal Server Error")
    
    def check_auth(self, auth_header):
        """Verifica autenticación básica"""
        if not auth_header:
            return False
        
        try:
            auth_type, auth_string = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return False
            
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            expected_user = self.config.get('auth', 'username')
            expected_pass = self.config.get('auth', 'password')
            
            return username == expected_user and password == expected_pass
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return False
    
    def extract_cwmp_method(self, root):
        """Extrae el método CWMP del mensaje SOAP"""
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'cwmp': 'urn:dslforum-org:cwmp-1-0',
            'soap-env': 'http://schemas.xmlsoap.org/soap/envelope/'
        }
        
        # Buscar en el Body
        for ns_prefix in ['soap', 'soap-env']:
            body = root.find(f'{{{namespaces.get(ns_prefix)}}}Body')
            if body is not None:
                for child in body:
                    # Extraer nombre del método
                    tag = child.tag
                    if '}' in tag:
                        return tag.split('}')[1]
                    return tag
        
        return None
    
    def handle_inform(self, root):
        """Maneja mensaje Inform"""
        # Extraer información del dispositivo
        device_info = self.extract_device_info(root)
        
        # Guardar en base de datos
        device_id = device_info.get('SerialNumber', 'unknown')
        self.database.add_or_update_device(device_id, device_info)
        
        logger.info(f"Inform recibido de dispositivo: {device_id}")
        
        # Crear respuesta InformResponse
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{secrets.token_hex(8)}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:InformResponse>
            <MaxEnvelopes>1</MaxEnvelopes>
        </cwmp:InformResponse>
    </soap:Body>
</soap:Envelope>"""
        
        return response
    
    def handle_get_rpc_methods(self):
        """Maneja mensaje GetRPCMethods"""
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{secrets.token_hex(8)}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:GetRPCMethodsResponse>
            <MethodList soap:arrayType="xsd:string[9]">
                <string>GetRPCMethods</string>
                <string>SetParameterValues</string>
                <string>GetParameterValues</string>
                <string>GetParameterNames</string>
                <string>SetParameterAttributes</string>
                <string>GetParameterAttributes</string>
                <string>AddObject</string>
                <string>DeleteObject</string>
                <string>Reboot</string>
            </MethodList>
        </cwmp:GetRPCMethodsResponse>
    </soap:Body>
</soap:Envelope>"""
        
        return response
    
    def handle_transfer_complete(self, root):
        """Maneja mensaje TransferComplete"""
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{secrets.token_hex(8)}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:TransferCompleteResponse/>
    </soap:Body>
</soap:Envelope>"""
        
        return response
    
    def create_empty_response(self):
        """Crea una respuesta vacía"""
        response = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{secrets.token_hex(8)}</cwmp:ID>
    </soap:Header>
    <soap:Body>
    </soap:Body>
</soap:Envelope>"""
        
        return response
    
    def extract_device_info(self, root):
        """Extrae información del dispositivo del mensaje Inform"""
        device_info = {}
        
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'cwmp': 'urn:dslforum-org:cwmp-1-0'
        }
        
        # Buscar DeviceId
        device_id_elem = root.find('.//cwmp:DeviceId', namespaces)
        if device_id_elem is None:
            # Intentar sin namespace
            device_id_elem = root.find('.//DeviceId')
        
        if device_id_elem is not None:
            for child in device_id_elem:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                device_info[tag] = child.text
        
        return device_info


class TR069Server:
    """Servidor TR-069 principal"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config = TR069Config(config_file)
        self.database = DeviceDatabase(self.config.get('database', 'path'))
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Inicia el servidor"""
        host = self.config.get('server', 'host')
        port = self.config.get('server', 'port')
        
        # Configurar el handler con config y database
        TR069RequestHandler.config = self.config
        TR069RequestHandler.database = self.database
        
        try:
            self.server = HTTPServer((host, port), TR069RequestHandler)
            logger.info(f"🚀 Servidor TR-069 iniciado en {host}:{port}")
            logger.info(f"📊 Panel de control disponible en http://localhost:{port}/")
            logger.info("Presiona Ctrl+C para detener el servidor")
            
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("\n⏹ Deteniendo servidor...")
            self.stop()
        except Exception as e:
            logger.error(f"Error al iniciar servidor: {e}", exc_info=True)
    
    def stop(self):
        """Detiene el servidor"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("✓ Servidor detenido correctamente")


def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════╗
║         TR-069 (CWMP) ACS Server v1.0               ║
║         Servidor de gestión de dispositivos CPE      ║
╚══════════════════════════════════════════════════════╝
    """)
    
    server = TR069Server()
    server.start()


if __name__ == '__main__':
    main()
