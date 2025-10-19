"""
Rutas del panel de administración
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database_models import db, ONT, Customer, ConfigurationProfile, WiFiSettings, NetworkSettings, MonitoringData
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('No tienes permisos de administrador', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Panel principal de administración"""
    # Estadísticas generales
    total_onts = ONT.query.count()
    online_onts = ONT.query.filter_by(is_online=True).count()
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(is_active=True).count()
    
    # ONTs recientes
    recent_onts = ONT.query.order_by(ONT.created_at.desc()).limit(10).all()
    
    # ONTs con problemas (sin conexión reciente)
    problem_onts = ONT.query.filter(
        ONT.last_seen < datetime.utcnow() - timedelta(hours=1)
    ).limit(10).all()
    
    # Estadísticas de monitoreo
    monitoring_stats = {
        'low_power_onts': db.session.query(ONT).join(MonitoringData).filter(
            MonitoringData.optical_power_rx < -25.0
        ).count(),
        'high_traffic_onts': db.session.query(ONT).join(MonitoringData).filter(
            MonitoringData.bytes_sent + MonitoringData.bytes_received > 1000000000  # 1GB
        ).count()
    }
    
    return render_template('admin/dashboard.html',
                         total_onts=total_onts,
                         online_onts=online_onts,
                         total_customers=total_customers,
                         active_customers=active_customers,
                         recent_onts=recent_onts,
                         problem_onts=problem_onts,
                         monitoring_stats=monitoring_stats)

@admin_bp.route('/onts')
@admin_required
def onts():
    """Lista de ONTs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtros
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    model = request.args.get('model', 'all')
    
    query = ONT.query
    
    if search:
        query = query.filter(
            (ONT.serial_number.contains(search)) |
            (ONT.mac_address.contains(search)) |
            (ONT.ip_address.contains(search))
        )
    
    if status == 'online':
        query = query.filter_by(is_online=True)
    elif status == 'offline':
        query = query.filter_by(is_online=False)
    
    if model != 'all':
        query = query.filter_by(model=model)
    
    onts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtener modelos únicos para el filtro
    models = db.session.query(ONT.model).distinct().all()
    models = [m[0] for m in models]
    
    return render_template('admin/onts.html', onts=onts, models=models)

@admin_bp.route('/onts/<int:ont_id>')
@admin_required
def ont_detail(ont_id):
    """Detalle de una ONT específica"""
    ont = ONT.query.get_or_404(ont_id)
    
    # Obtener datos de monitoreo recientes
    monitoring_data = MonitoringData.query.filter_by(ont_id=ont_id)\
        .order_by(MonitoringData.timestamp.desc()).limit(100).all()
    
    # Obtener configuración actual
    wifi_settings = ont.wifi_settings
    network_settings = ont.network_settings
    
    return render_template('admin/ont_detail.html',
                         ont=ont,
                         monitoring_data=monitoring_data,
                         wifi_settings=wifi_settings,
                         network_settings=network_settings)

@admin_bp.route('/onts/<int:ont_id>/configure', methods=['GET', 'POST'])
@admin_required
def configure_ont(ont_id):
    """Configurar ONT"""
    ont = ONT.query.get_or_404(ont_id)
    
    if request.method == 'POST':
        config_type = request.form.get('config_type')
        
        if config_type == 'wifi':
            # Configurar WiFi
            wifi_data = {
                'wifi_2_4_enabled': bool(request.form.get('wifi_2_4_enabled')),
                'wifi_2_4_ssid': request.form.get('wifi_2_4_ssid'),
                'wifi_2_4_password': request.form.get('wifi_2_4_password'),
                'wifi_2_4_channel': int(request.form.get('wifi_2_4_channel', 6)),
                'wifi_2_4_security': request.form.get('wifi_2_4_security', 'WPA2-PSK'),
                'wifi_5_enabled': bool(request.form.get('wifi_5_enabled')),
                'wifi_5_ssid': request.form.get('wifi_5_ssid'),
                'wifi_5_password': request.form.get('wifi_5_password'),
                'wifi_5_channel': int(request.form.get('wifi_5_channel', 36)),
                'wifi_5_security': request.form.get('wifi_5_security', 'WPA2-PSK'),
                'wifi_guest_enabled': bool(request.form.get('wifi_guest_enabled')),
                'wifi_guest_ssid': request.form.get('wifi_guest_ssid'),
                'wifi_guest_password': request.form.get('wifi_guest_password'),
                'wifi_guest_vlan': int(request.form.get('wifi_guest_vlan', 0)) or None
            }
            
            # Actualizar configuración WiFi
            from tr069_server import TR069Server
            tr069_server = TR069Server()
            success = tr069_server.update_wifi_settings(ont_id, wifi_data)
            
            if success:
                flash('Configuración WiFi actualizada correctamente', 'success')
            else:
                flash('Error al actualizar configuración WiFi', 'error')
        
        elif config_type == 'network':
            # Configurar red
            network_data = {
                'ip_mode': request.form.get('ip_mode', 'DHCP'),
                'static_ip': request.form.get('static_ip') or None,
                'static_gateway': request.form.get('static_gateway') or None,
                'static_netmask': request.form.get('static_netmask', '255.255.255.0'),
                'pppoe_username': request.form.get('pppoe_username') or None,
                'pppoe_password': request.form.get('pppoe_password') or None,
                'pppoe_service_name': request.form.get('pppoe_service_name') or None,
                'vlan_id': int(request.form.get('vlan_id', 0)) or None,
                'vlan_priority': int(request.form.get('vlan_priority', 0)),
                'dns_primary': request.form.get('dns_primary') or None,
                'dns_secondary': request.form.get('dns_secondary') or None
            }
            
            # Actualizar configuración de red
            from tr069_server import TR069Server
            tr069_server = TR069Server()
            success = tr069_server.update_network_settings(ont_id, network_data)
            
            if success:
                flash('Configuración de red actualizada correctamente', 'success')
            else:
                flash('Error al actualizar configuración de red', 'error')
        
        return redirect(url_for('admin.ont_detail', ont_id=ont_id))
    
    # Obtener configuración actual
    wifi_settings = ont.wifi_settings
    network_settings = ont.network_settings
    
    return render_template('admin/configure_ont.html',
                         ont=ont,
                         wifi_settings=wifi_settings,
                         network_settings=network_settings)

@admin_bp.route('/onts/<int:ont_id>/reboot', methods=['POST'])
@admin_required
def reboot_ont(ont_id):
    """Reiniciar ONT"""
    ont = ONT.query.get_or_404(ont_id)
    
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.reboot_ont(ont_id)
    
    if success:
        flash('Comando de reinicio enviado correctamente', 'success')
    else:
        flash('Error al enviar comando de reinicio', 'error')
    
    return redirect(url_for('admin.ont_detail', ont_id=ont_id))

@admin_bp.route('/onts/<int:ont_id>/update_firmware', methods=['POST'])
@admin_required
def update_firmware(ont_id):
    """Actualizar firmware de ONT"""
    ont = ONT.query.get_or_404(ont_id)
    firmware_url = request.form.get('firmware_url')
    
    if not firmware_url:
        flash('URL de firmware requerida', 'error')
        return redirect(url_for('admin.ont_detail', ont_id=ont_id))
    
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.update_firmware(ont_id, firmware_url)
    
    if success:
        flash('Actualización de firmware iniciada', 'success')
    else:
        flash('Error al iniciar actualización de firmware', 'error')
    
    return redirect(url_for('admin.ont_detail', ont_id=ont_id))

@admin_bp.route('/customers')
@admin_required
def customers():
    """Lista de clientes"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '')
    query = Customer.query
    
    if search:
        query = query.filter(
            (Customer.username.contains(search)) |
            (Customer.email.contains(search)) |
            (Customer.full_name.contains(search))
        )
    
    customers = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/customers.html', customers=customers)

@admin_bp.route('/customers/<int:customer_id>')
@admin_required
def customer_detail(customer_id):
    """Detalle de un cliente"""
    customer = Customer.query.get_or_404(customer_id)
    onts = ONT.query.filter_by(customer_id=customer_id).all()
    
    return render_template('admin/customer_detail.html', customer=customer, onts=onts)

@admin_bp.route('/profiles')
@admin_required
def profiles():
    """Gestión de perfiles de configuración"""
    profiles = ConfigurationProfile.query.all()
    return render_template('admin/profiles.html', profiles=profiles)

@admin_bp.route('/profiles/create', methods=['GET', 'POST'])
@admin_required
def create_profile():
    """Crear nuevo perfil de configuración"""
    if request.method == 'POST':
        name = request.form.get('name')
        ont_model = request.form.get('ont_model')
        description = request.form.get('description')
        
        profile = ConfigurationProfile(
            name=name,
            ont_model=ont_model,
            description=description
        )
        
        try:
            db.session.add(profile)
            db.session.commit()
            flash('Perfil creado correctamente', 'success')
            return redirect(url_for('admin.profiles'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear perfil', 'error')
    
    return render_template('admin/create_profile.html')

@admin_bp.route('/monitoring')
@admin_required
def monitoring():
    """Panel de monitoreo"""
    # ONTs con problemas de potencia óptica
    low_power_onts = db.session.query(ONT, MonitoringData).join(MonitoringData).filter(
        MonitoringData.optical_power_rx < -25.0
    ).order_by(MonitoringData.timestamp.desc()).limit(20).all()
    
    # Estadísticas de tráfico
    traffic_stats = db.session.query(
        db.func.sum(MonitoringData.bytes_sent + MonitoringData.bytes_received).label('total_bytes'),
        db.func.count(ONT.id).label('total_onts')
    ).join(ONT).first()
    
    return render_template('admin/monitoring.html',
                         low_power_onts=low_power_onts,
                         traffic_stats=traffic_stats)

@admin_bp.route('/api/onts/<int:ont_id>/monitoring')
@admin_required
def get_ont_monitoring(ont_id):
    """API para obtener datos de monitoreo de una ONT"""
    ont = ONT.query.get_or_404(ont_id)
    
    # Obtener datos de las últimas 24 horas
    since = datetime.utcnow() - timedelta(hours=24)
    data = MonitoringData.query.filter(
        MonitoringData.ont_id == ont_id,
        MonitoringData.timestamp >= since
    ).order_by(MonitoringData.timestamp.asc()).all()
    
    result = {
        'ont_id': ont_id,
        'serial_number': ont.serial_number,
        'data': []
    }
    
    for d in data:
        result['data'].append({
            'timestamp': d.timestamp.isoformat(),
            'optical_power_rx': d.optical_power_rx,
            'optical_power_tx': d.optical_power_tx,
            'connection_status': d.connection_status,
            'wifi_devices_2_4': d.wifi_devices_2_4,
            'wifi_devices_5': d.wifi_devices_5,
            'bytes_sent': d.bytes_sent,
            'bytes_received': d.bytes_received
        })
    
    return jsonify(result)