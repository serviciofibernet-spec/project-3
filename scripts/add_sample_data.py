#!/usr/bin/env python3
"""
Script to add sample data for testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.models import db, User, Client, Device, ConfigurationProfile
from datetime import datetime

def add_sample_data():
    app = create_app()
    
    with app.app_context():
        print("=== Adding Sample Data ===\n")
        
        # Create admin user
        print("1. Creating admin user...")
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@tr069.local', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("   ✅ Admin user created (username: admin, password: admin123)")
        else:
            print("   ℹ️  Admin user already exists")
        
        # Create client user
        print("2. Creating client user...")
        client_user = User.query.filter_by(username='cliente1').first()
        if not client_user:
            client_user = User(username='cliente1', email='cliente1@example.com', role='client')
            client_user.set_password('cliente123')
            db.session.add(client_user)
            db.session.commit()
            print("   ✅ Client user created (username: cliente1, password: cliente123)")
        else:
            print("   ℹ️  Client user already exists")
        
        # Create client profile
        print("3. Creating client profile...")
        client = Client.query.filter_by(user_id=client_user.id).first()
        if not client:
            client = Client(
                user_id=client_user.id,
                name='Juan Pérez',
                document='12345678',
                phone='+34 600 123 456',
                email='juan.perez@example.com',
                address='Calle Principal 123, Madrid'
            )
            db.session.add(client)
            db.session.commit()
            print("   ✅ Client profile created")
        else:
            print("   ℹ️  Client profile already exists")
        
        # Create sample device
        print("4. Creating sample device...")
        device = Device.query.filter_by(serial_number='48575443B1C82E44').first()
        if not device:
            device = Device(
                serial_number='48575443B1C82E44',
                oui='48575443',
                product_class='HG8245H',
                manufacturer='Huawei',
                model='HG8245H',
                hardware_version='V3',
                software_version='V3R017C10S115',
                client_id=client.id,
                ip_address='192.168.1.100',
                mac_address='48:57:54:43:B1:C8',
                status='online',
                provisioning_status='provisioned',
                last_inform=datetime.utcnow()
            )
            db.session.add(device)
            db.session.commit()
            print("   ✅ Sample device created")
        else:
            print("   ℹ️  Sample device already exists")
        
        # Create configuration profile
        print("5. Creating configuration profile...")
        profile = ConfigurationProfile.query.filter_by(name='Perfil Huawei Estándar').first()
        if not profile:
            profile = ConfigurationProfile(
                name='Perfil Huawei Estándar',
                description='Configuración estándar para ONTs Huawei HG8245H',
                model_filter='HG8245H',
                priority=10,
                is_active=True,
                configuration={
                    'wifi_24': {
                        'enabled': True
                    },
                    'wifi_5': {
                        'enabled': True
                    },
                    'dns': {
                        'primary': '8.8.8.8',
                        'secondary': '8.8.4.4'
                    }
                }
            )
            db.session.add(profile)
            db.session.commit()
            print("   ✅ Configuration profile created")
        else:
            print("   ℹ️  Configuration profile already exists")
        
        print("\n=== Sample Data Added Successfully ===")
        print("\nLogin credentials:")
        print("  Admin:")
        print("    Username: admin")
        print("    Password: admin123")
        print("\n  Client:")
        print("    Username: cliente1")
        print("    Password: cliente123")

if __name__ == '__main__':
    add_sample_data()
