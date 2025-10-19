#!/usr/bin/env python3
"""
Servidor TR-069 en Python
Servidor simple para gestión de dispositivos CPE
"""

import json
import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import xml.etree.ElementTree as ET

# Configuración
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080
DB_FILE = 'data/tr069.db'
LOG_FILE = 'logs/tr069.log'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class Database:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Inicializar base de datos SQLite"""
        import os
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Crear tablas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                hardware_version TEXT,
                software_version TEXT,
                connection_request_url TEXT,
                last_inform_time DATETIME,
                last_inform_data TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value TEXT,
                parameter_type TEXT DEFAULT 'string',
                writable BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id),
                UNIQUE(device_id, parameter_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Base de datos inicializada")
    
    def get_device(self, device_id):
        """Obtener dispositivo por ID"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        device = cursor.fetchone()
        conn.close()
        return device
    
    def create_device(self, device_data):
        """Crear nuevo dispositivo"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO devices 
            (device_id, manufacturer, model, serial_number, hardware_version, software_version, connection_request_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_data.get('device_id'),
            device_data.get('manufacturer', ''),
            device_data.get('model', ''),
            device_data.get('serial_number', ''),
            device_data.get('hardware_version', ''),
            device_data.get('software_version', ''),
            device_data.get('connection_request_url', '')
        ))
        conn.commit()
        conn.close()
        logging.info(f"Dispositivo creado/actualizado: {device_data.get('device_id')}")
    
    def get_all_devices(self):
        """Obtener todos los dispositivos"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices ORDER BY created_at DESC")
        devices = cursor.fetchall()
        conn.close()
        return devices
    
    def log_action(self, device_id, action, details=''):
        """Registrar acción en logs"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (device_id, action, details)
            VALUES (?, ?, ?)
        ''', (device_id, action, details))
        conn.commit()
        conn.close()

class TR069Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = Database()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Manejar solicitudes GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/devices':
            self.serve_devices()
        elif parsed_path.path == '/admin':
            self.serve_admin()
        else:
            self.send_error(404, "Página no encontrada")
    
    def do_POST(self):
        """Manejar solicitudes POST"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/tr069':
            self.handle_tr069_request()
        else:
            self.send_error(404, "Endpoint no encontrado")
    
    def serve_dashboard(self):
        """Servir página principal"""
        devices = self.db.get_all_devices()
        total_devices = len(devices)
        active_devices = len([d for d in devices if d[10] == 'active'])  # status column
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Servidor TR-069</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ background: #007cba; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007cba; }}
                .table {{ width: 100%; border-collapse: collapse; }}
                .table th, .table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                .table th {{ background: #f8f9fa; }}
                .btn {{ background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .btn:hover {{ background: #005a87; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Servidor TR-069</h1>
                    <p>Gestión remota de dispositivos CPE</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{total_devices}</div>
                        <div>Total Dispositivos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{active_devices}</div>
                        <div>Dispositivos Activos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">TR-069</div>
                        <div>Protocolo</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">Python</div>
                        <div>Servidor</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📱 Dispositivos Registrados</h3>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Fabricante</th>
                                <th>Modelo</th>
                                <th>Estado</th>
                                <th>Última Conexión</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for device in devices[:10]:  # Mostrar solo los primeros 10
            html += f"""
                            <tr>
                                <td>{device[1]}</td>
                                <td>{device[2] or 'N/A'}</td>
                                <td>{device[3] or 'N/A'}</td>
                                <td>{device[10]}</td>
                                <td>{device[8] or 'Nunca'}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h3>🔗 Endpoints del Servidor</h3>
                    <p><strong>Web Interface:</strong> <a href="/">http://localhost:8080/</a></p>
                    <p><strong>TR-069 SOAP:</strong> <a href="/tr069">http://localhost:8080/tr069</a></p>
                    <p><strong>Dispositivos API:</strong> <a href="/devices">http://localhost:8080/devices</a></p>
                    <p><strong>Panel Admin:</strong> <a href="/admin">http://localhost:8080/admin</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_devices(self):
        """Servir API de dispositivos en JSON"""
        devices = self.db.get_all_devices()
        devices_json = []
        
        for device in devices:
            devices_json.append({
                'id': device[0],
                'device_id': device[1],
                'manufacturer': device[2],
                'model': device[3],
                'serial_number': device[4],
                'hardware_version': device[5],
                'software_version': device[6],
                'status': device[10],
                'last_inform_time': device[8],
                'created_at': device[11]
            })
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(devices_json, indent=2, ensure_ascii=False).encode('utf-8'))
    
    def serve_admin(self):
        """Servir panel de administración"""
        devices = self.db.get_all_devices()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Panel de Administración - TR-069</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: #007cba; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .table {{ width: 100%; border-collapse: collapse; }}
                .table th, .table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                .table th {{ background: #f8f9fa; }}
                .btn {{ background: #007cba; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .btn:hover {{ background: #005a87; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛠️ Panel de Administración TR-069</h1>
                    <p>Gestión de dispositivos y monitoreo del servidor</p>
                </div>
                
                <div class="card">
                    <h3>📱 Dispositivos Registrados ({len(devices)})</h3>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Fabricante</th>
                                <th>Modelo</th>
                                <th>Número de Serie</th>
                                <th>Versión HW</th>
                                <th>Versión SW</th>
                                <th>Estado</th>
                                <th>Última Conexión</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for device in devices:
            html += f"""
                            <tr>
                                <td>{device[1]}</td>
                                <td>{device[2] or 'N/A'}</td>
                                <td>{device[3] or 'N/A'}</td>
                                <td>{device[4] or 'N/A'}</td>
                                <td>{device[5] or 'N/A'}</td>
                                <td>{device[6] or 'N/A'}</td>
                                <td>{device[10]}</td>
                                <td>{device[8] or 'Nunca'}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h3>🔧 Información del Servidor</h3>
                    <p><strong>Host:</strong> localhost:8080</p>
                    <p><strong>Protocolo:</strong> TR-069 (CWMP)</p>
                    <p><strong>Base de Datos:</strong> SQLite</p>
                    <p><strong>Estado:</strong> Activo</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_tr069_request(self):
        """Manejar solicitudes TR-069 SOAP"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        logging.info(f"TR-069 Request recibida: {len(post_data)} bytes")
        
        # Simular respuesta TR-069
        soap_response = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <cwmp:InformResponse xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
            <MaxEnvelopes>1</MaxEnvelopes>
            <CurrentTime>''' + datetime.now().isoformat() + '''</CurrentTime>
            <RetryAfter>0</RetryAfter>
        </cwmp:InformResponse>
    </soap:Body>
</soap:Envelope>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/xml; charset=utf-8')
        self.end_headers()
        self.wfile.write(soap_response.encode('utf-8'))
        
        # Registrar en logs
        self.db.log_action('unknown', 'TR069_REQUEST', f'Request de {len(post_data)} bytes')

def main():
    """Función principal"""
    print("=" * 50)
    print("   Servidor TR-069 en Python")
    print("=" * 50)
    print(f"Iniciando servidor en http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Base de datos: {DB_FILE}")
    print(f"Logs: {LOG_FILE}")
    print("=" * 50)
    
    try:
        server = HTTPServer((SERVER_HOST, SERVER_PORT), TR069Handler)
        print(f"✅ Servidor iniciado correctamente")
        print(f"🌐 Web Interface: http://localhost:{SERVER_PORT}/")
        print(f"📡 TR-069 SOAP: http://localhost:{SERVER_PORT}/tr069")
        print(f"📱 Dispositivos API: http://localhost:{SERVER_PORT}/devices")
        print(f"🛠️ Panel Admin: http://localhost:{SERVER_PORT}/admin")
        print("\nPresiona Ctrl+C para detener el servidor")
        print("=" * 50)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
    finally:
        server.server_close()

if __name__ == '__main__':
    main()