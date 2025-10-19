"""
TR-069 ACS Server Main Application
"""
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from config import Config
from database.models import db
from tr069.cwmp_server import cwmp_bp
from api.admin_api import admin_api
from api.client_api import client_api
from api.monitoring_api import monitoring_api
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(cwmp_bp)
    app.register_blueprint(admin_api)
    app.register_blueprint(client_api)
    app.register_blueprint(monitoring_api)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'TR-069 ACS Server'}, 200
    
    # Root endpoint
    @app.route('/')
    def index():
        return {
            'service': 'TR-069 ACS Server',
            'version': '1.0.0',
            'endpoints': {
                'cwmp': '/cwmp',
                'admin_api': '/api/admin',
                'client_api': '/api/client',
                'monitoring_api': '/api/monitoring',
                'health': '/health'
            }
        }, 200
    
    # Static files for web interface
    @app.route('/admin')
    def admin_panel():
        return {'message': 'Admin web interface - implement frontend here'}, 200
    
    @app.route('/client')
    def client_panel():
        return {'message': 'Client web interface - implement frontend here'}, 200
    
    return app

def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database
    init_database(app)
    
    print(f"Starting TR-069 ACS Server on port {Config.PORT}")
    print(f"CWMP endpoint: http://localhost:{Config.PORT}/cwmp")
    print(f"Admin API: http://localhost:{Config.PORT}/api/admin")
    print(f"Client API: http://localhost:{Config.PORT}/api/client")
    print(f"Monitoring API: http://localhost:{Config.PORT}/api/monitoring")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
