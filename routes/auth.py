"""
Rutas de autenticación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database_models import db, Customer
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = Customer.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            if not next_page or not next_page.startswith('/'):
                if user.is_admin:
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('customer.dashboard')
            
            return redirect(next_page)
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios (solo administradores)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        is_admin = bool(request.form.get('is_admin'))
        
        # Verificar si el usuario ya existe
        if Customer.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return render_template('auth/register.html')
        
        if Customer.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('auth/register.html')
        
        # Crear nuevo usuario
        user = Customer(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            is_admin=is_admin
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuario registrado correctamente', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar usuario', 'error')
    
    return render_template('auth/register.html')