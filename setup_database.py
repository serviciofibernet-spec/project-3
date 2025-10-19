#!/usr/bin/env python3
"""
Script para configurar la base de datos MySQL del servidor TR-069
"""

import os
import sys
import pymysql
from config import Config

def create_database():
    """Crear la base de datos MySQL"""
    config = Config()
    
    # Extraer información de conexión de la URL de la base de datos
    # Formato: mysql+pymysql://user:password@host:port/database
    db_url = config.SQLALCHEMY_DATABASE_URI
    if db_url.startswith('mysql+pymysql://'):
        db_url = db_url[16:]  # Remover 'mysql+pymysql://'
    
    # Parsear la URL
    if '@' in db_url:
        auth_part, host_part = db_url.split('@', 1)
        if ':' in auth_part:
            username, password = auth_part.split(':', 1)
        else:
            username = auth_part
            password = ''
        
        if '/' in host_part:
            host_port, database = host_part.split('/', 1)
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 3306
        else:
            host = host_part
            port = 3306
            database = 'tr069_onts'
    else:
        # Valores por defecto
        username = 'tr069'
        password = 'tr069pass'
        host = 'localhost'
        port = 3306
        database = 'tr069_onts'
    
    print(f"Conectando a MySQL en {host}:{port} como {username}")
    
    try:
        # Conectar sin especificar base de datos para crearla
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Crear base de datos si no existe
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Base de datos '{database}' creada o ya existe")
            
            # Usar la base de datos
            cursor.execute(f"USE `{database}`")
            
            # Crear usuario si no existe (solo si es diferente al usuario actual)
            if username != 'root':
                try:
                    cursor.execute(f"CREATE USER IF NOT EXISTS '{username}'@'%' IDENTIFIED BY '{password}'")
                    cursor.execute(f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{username}'@'%'")
                    cursor.execute("FLUSH PRIVILEGES")
                    print(f"Usuario '{username}' creado y privilegios otorgados")
                except Exception as e:
                    print(f"Advertencia: No se pudo crear usuario: {e}")
        
        connection.close()
        print("Base de datos configurada correctamente")
        return True
        
    except Exception as e:
        print(f"Error al configurar la base de datos: {e}")
        return False

def create_tables():
    """Crear las tablas de la base de datos"""
    from app import create_app
    from database_models import db
    
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            print("Tablas creadas correctamente")
            
            # Crear usuario administrador por defecto
            from database_models import Customer
            from werkzeug.security import generate_password_hash
            
            admin = Customer.query.filter_by(username='admin').first()
            if not admin:
                admin = Customer(
                    username='admin',
                    email='admin@tr069.local',
                    password_hash=generate_password_hash('admin123'),
                    full_name='Administrador',
                    is_admin=True,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Usuario administrador creado: admin/admin123")
            else:
                print("Usuario administrador ya existe")
            
            # Crear perfiles de configuración por defecto
            from database_models import ConfigurationProfile, WiFiTemplate, NetworkTemplate
            
            # Perfil para HG8240H
            hg8240h_profile = ConfigurationProfile.query.filter_by(ont_model='HG8240H').first()
            if not hg8240h_profile:
                hg8240h_profile = ConfigurationProfile(
                    name='Huawei HG8240H - Configuración Estándar',
                    ont_model='HG8240H',
                    description='Configuración automática para ONTs Huawei HG8240H'
                )
                db.session.add(hg8240h_profile)
                db.session.flush()  # Para obtener el ID
                
                # Plantilla WiFi
                wifi_template = WiFiTemplate(
                    configuration_profile_id=hg8240h_profile.id,
                    wifi_2_4_enabled=True,
                    wifi_2_4_ssid_template='WiFi-{customer_name}-2.4G',
                    wifi_2_4_password_template='{customer_name}2024',
                    wifi_2_4_channel=6,
                    wifi_2_4_security='WPA2-PSK',
                    wifi_5_enabled=True,
                    wifi_5_ssid_template='WiFi-{customer_name}-5G',
                    wifi_5_password_template='{customer_name}2024',
                    wifi_5_channel=36,
                    wifi_5_security='WPA2-PSK'
                )
                db.session.add(wifi_template)
                
                # Plantilla de red
                network_template = NetworkTemplate(
                    configuration_profile_id=hg8240h_profile.id,
                    ip_mode='DHCP',
                    vlan_id=100,
                    vlan_priority=0,
                    dns_primary='8.8.8.8',
                    dns_secondary='8.8.4.4'
                )
                db.session.add(network_template)
                
                print("Perfil de configuración HG8240H creado")
            
            # Perfil para HG8245H
            hg8245h_profile = ConfigurationProfile.query.filter_by(ont_model='HG8245H').first()
            if not hg8245h_profile:
                hg8245h_profile = ConfigurationProfile(
                    name='Huawei HG8245H - Configuración Estándar',
                    ont_model='HG8245H',
                    description='Configuración automática para ONTs Huawei HG8245H'
                )
                db.session.add(hg8245h_profile)
                db.session.flush()
                
                # Plantilla WiFi
                wifi_template = WiFiTemplate(
                    configuration_profile_id=hg8245h_profile.id,
                    wifi_2_4_enabled=True,
                    wifi_2_4_ssid_template='WiFi-{customer_name}-2.4G',
                    wifi_2_4_password_template='{customer_name}2024',
                    wifi_2_4_channel=6,
                    wifi_2_4_security='WPA2-PSK',
                    wifi_5_enabled=True,
                    wifi_5_ssid_template='WiFi-{customer_name}-5G',
                    wifi_5_password_template='{customer_name}2024',
                    wifi_5_channel=36,
                    wifi_5_security='WPA2-PSK'
                )
                db.session.add(wifi_template)
                
                # Plantilla de red
                network_template = NetworkTemplate(
                    configuration_profile_id=hg8245h_profile.id,
                    ip_mode='DHCP',
                    vlan_id=100,
                    vlan_priority=0,
                    dns_primary='8.8.8.8',
                    dns_secondary='8.8.4.4'
                )
                db.session.add(network_template)
                
                print("Perfil de configuración HG8245H creado")
            
            db.session.commit()
            print("Configuración inicial completada")
            return True
            
        except Exception as e:
            print(f"Error al crear tablas: {e}")
            db.session.rollback()
            return False

def main():
    """Función principal"""
    print("=== Configuración del Servidor TR-069 ===")
    print()
    
    # Crear base de datos
    print("1. Configurando base de datos MySQL...")
    if not create_database():
        print("Error: No se pudo configurar la base de datos")
        sys.exit(1)
    
    print()
    
    # Crear tablas
    print("2. Creando tablas y datos iniciales...")
    if not create_tables():
        print("Error: No se pudieron crear las tablas")
        sys.exit(1)
    
    print()
    print("=== Configuración completada ===")
    print()
    print("Para iniciar el servidor:")
    print("  python app.py")
    print()
    print("Acceso web:")
    print("  http://localhost:5000")
    print()
    print("Credenciales por defecto:")
    print("  Usuario: admin")
    print("  Contraseña: admin123")
    print()
    print("Servidor TR-069 ACS:")
    print(f"  Puerto: 7547")
    print(f"  URL: http://localhost:5000/acs")

if __name__ == '__main__':
    main()