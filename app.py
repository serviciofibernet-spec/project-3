#!/usr/bin/env python3
"""
Servidor TR-069 para gestión automatizada de ONTs Huawei
ACS (Auto Configuration Server) con funcionalidades completas
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import threading
import time
from tr069_server import TR069Server
from database_models import db, ONT, Customer, ConfigurationProfile, WiFiSettings, NetworkSettings, MonitoringData
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Customer.query.get(int(user_id))
    
    # Configurar logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/tr069_server.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Servidor TR-069 iniciado')
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.customer import customer_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Inicializar servidor TR-069
    tr069_server = TR069Server()
    tr069_thread = threading.Thread(target=tr069_server.start, daemon=True)
    tr069_thread.start()
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        # Crear usuario administrador por defecto
        admin = Customer.query.filter_by(username='admin').first()
        if not admin:
            admin = Customer(
                username='admin',
                email='admin@tr069.local',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado: admin/admin123")
    
    app.run(host='0.0.0.0', port=5000, debug=True)