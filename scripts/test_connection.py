#!/usr/bin/env python3
"""
Script to test database connection and server setup
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.models import db, Device, Client, User
from config import Config

def test_connection():
    print("=== TR-069 ACS Server Test ===\n")
    
    # Test configuration
    print("1. Configuration:")
    print(f"   Database: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"   ACS URL: {Config.ACS_URL}")
    print(f"   Port: {Config.PORT}")
    print()
    
    # Test database connection
    print("2. Database Connection:")
    try:
        app = create_app()
        with app.app_context():
            # Try to query database
            device_count = Device.query.count()
            client_count = Client.query.count()
            user_count = User.query.count()
            
            print(f"   ✅ Connected successfully")
            print(f"   Devices: {device_count}")
            print(f"   Clients: {client_count}")
            print(f"   Users: {user_count}")
            print()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        return False
    
    # Test tables
    print("3. Database Tables:")
    try:
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'clients', 'devices', 'device_parameters',
                'configuration_profiles', 'configuration_tasks',
                'event_log', 'device_diagnostics', 'connected_devices',
                'firmware_versions'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"   ⚠️  Missing tables: {', '.join(missing_tables)}")
                print(f"   Run database/schema.sql to create tables")
            else:
                print(f"   ✅ All required tables exist")
            print()
    except Exception as e:
        print(f"   ❌ Error checking tables: {e}")
        print()
    
    print("4. Server Endpoints:")
    print(f"   CWMP: {Config.ACS_URL}/cwmp")
    print(f"   Admin API: {Config.ACS_URL}/api/admin")
    print(f"   Client API: {Config.ACS_URL}/api/client")
    print(f"   Monitoring: {Config.ACS_URL}/api/monitoring")
    print()
    
    print("=== Test Complete ===")
    print("\nTo start the server, run: python app.py")
    
    return True

if __name__ == '__main__':
    test_connection()
