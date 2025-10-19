"""
Rutas del panel de cliente
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database_models import db, ONT, WiFiSettings, NetworkSettings, MonitoringData
from datetime import datetime, timedelta

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
@login_required
def dashboard():
    """Panel principal del cliente"""
    # Obtener ONTs del cliente
    onts = ONT.query.filter_by(customer_id=current_user.id).all()
    
    # Estadísticas del cliente
    total_onts = len(onts)
    online_onts = len([ont for ont in onts if ont.is_online])
    
    # ONTs con problemas
    problem_onts = []
    for ont in onts:
        if ont.is_online:
            latest_data = MonitoringData.query.filter_by(ont_id=ont.id)\
                .order_by(MonitoringData.timestamp.desc()).first()
            if latest_data and latest_data.optical_power_rx and latest_data.optical_power_rx < -25.0:
                problem_onts.append(ont)
    
    return render_template('customer/dashboard.html',
                         onts=onts,
                         total_onts=total_onts,
                         online_onts=online_onts,
                         problem_onts=problem_onts)

@customer_bp.route('/onts')
@login_required
def onts():
    """Lista de ONTs del cliente"""
    onts = ONT.query.filter_by(customer_id=current_user.id).all()
    return render_template('customer/onts.html', onts=onts)

@customer_bp.route('/onts/<int:ont_id>')
@login_required
def ont_detail(ont_id):
    """Detalle de una ONT del cliente"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Obtener datos de monitoreo recientes
    monitoring_data = MonitoringData.query.filter_by(ont_id=ont_id)\
        .order_by(MonitoringData.timestamp.desc()).limit(50).all()
    
    # Obtener configuración actual
    wifi_settings = ont.wifi_settings
    network_settings = ont.network_settings
    
    return render_template('customer/ont_detail.html',
                         ont=ont,
                         monitoring_data=monitoring_data,
                         wifi_settings=wifi_settings,
                         network_settings=network_settings)

@customer_bp.route('/onts/<int:ont_id>/wifi', methods=['GET', 'POST'])
@login_required
def configure_wifi(ont_id):
    """Configurar WiFi de una ONT"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        # Validar datos
        wifi_2_4_ssid = request.form.get('wifi_2_4_ssid', '').strip()
        wifi_2_4_password = request.form.get('wifi_2_4_password', '').strip()
        wifi_5_ssid = request.form.get('wifi_5_ssid', '').strip()
        wifi_5_password = request.form.get('wifi_5_password', '').strip()
        
        if not wifi_2_4_ssid and not wifi_5_ssid:
            flash('Debe configurar al menos un SSID', 'error')
            return render_template('customer/configure_wifi.html', ont=ont)
        
        if len(wifi_2_4_password) < 8 and wifi_2_4_ssid:
            flash('La contraseña WiFi 2.4GHz debe tener al menos 8 caracteres', 'error')
            return render_template('customer/configure_wifi.html', ont=ont)
        
        if len(wifi_5_password) < 8 and wifi_5_ssid:
            flash('La contraseña WiFi 5GHz debe tener al menos 8 caracteres', 'error')
            return render_template('customer/configure_wifi.html', ont=ont)
        
        # Preparar datos de configuración
        wifi_data = {
            'wifi_2_4_enabled': bool(wifi_2_4_ssid),
            'wifi_2_4_ssid': wifi_2_4_ssid,
            'wifi_2_4_password': wifi_2_4_password,
            'wifi_5_enabled': bool(wifi_5_ssid),
            'wifi_5_ssid': wifi_5_ssid,
            'wifi_5_password': wifi_5_password
        }
        
        # Actualizar configuración WiFi
        from tr069_server import TR069Server
        tr069_server = TR069Server()
        success = tr069_server.update_wifi_settings(ont_id, wifi_data)
        
        if success:
            flash('Configuración WiFi actualizada correctamente', 'success')
            return redirect(url_for('customer.ont_detail', ont_id=ont_id))
        else:
            flash('Error al actualizar configuración WiFi', 'error')
    
    # Obtener configuración actual
    wifi_settings = ont.wifi_settings
    
    return render_template('customer/configure_wifi.html', ont=ont, wifi_settings=wifi_settings)

@customer_bp.route('/onts/<int:ont_id>/monitoring')
@login_required
def ont_monitoring(ont_id):
    """Monitoreo de una ONT específica"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Obtener datos de monitoreo de las últimas 24 horas
    since = datetime.utcnow() - timedelta(hours=24)
    monitoring_data = MonitoringData.query.filter(
        MonitoringData.ont_id == ont_id,
        MonitoringData.timestamp >= since
    ).order_by(MonitoringData.timestamp.asc()).all()
    
    return render_template('customer/ont_monitoring.html',
                         ont=ont,
                         monitoring_data=monitoring_data)

@customer_bp.route('/onts/<int:ont_id>/devices')
@login_required
def wifi_devices(ont_id):
    """Dispositivos conectados al WiFi"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Obtener último dato de monitoreo
    latest_data = MonitoringData.query.filter_by(ont_id=ont_id)\
        .order_by(MonitoringData.timestamp.desc()).first()
    
    if not latest_data:
        latest_data = MonitoringData(
            wifi_devices_2_4=0,
            wifi_devices_5=0,
            wifi_devices_guest=0
        )
    
    return render_template('customer/wifi_devices.html',
                         ont=ont,
                         monitoring_data=latest_data)

@customer_bp.route('/onts/<int:ont_id>/reboot', methods=['POST'])
@login_required
def reboot_ont(ont_id):
    """Solicitar reinicio de ONT"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Verificar si el cliente puede reiniciar (ej: solo una vez por día)
    last_reboot = request.cookies.get(f'last_reboot_{ont_id}')
    if last_reboot:
        try:
            last_reboot_time = datetime.fromisoformat(last_reboot)
            if datetime.utcnow() - last_reboot_time < timedelta(hours=24):
                flash('Solo puedes reiniciar la ONT una vez cada 24 horas', 'error')
                return redirect(url_for('customer.ont_detail', ont_id=ont_id))
        except:
            pass
    
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.reboot_ont(ont_id)
    
    if success:
        flash('Comando de reinicio enviado. La ONT se reiniciará en unos minutos.', 'success')
        response = redirect(url_for('customer.ont_detail', ont_id=ont_id))
        response.set_cookie(f'last_reboot_{ont_id}', datetime.utcnow().isoformat())
        return response
    else:
        flash('Error al enviar comando de reinicio', 'error')
        return redirect(url_for('customer.ont_detail', ont_id=ont_id))

@customer_bp.route('/api/onts/<int:ont_id>/status')
@login_required
def get_ont_status(ont_id):
    """API para obtener estado actual de una ONT"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Obtener último dato de monitoreo
    latest_data = MonitoringData.query.filter_by(ont_id=ont_id)\
        .order_by(MonitoringData.timestamp.desc()).first()
    
    status = {
        'ont_id': ont.id,
        'serial_number': ont.serial_number,
        'model': ont.model,
        'is_online': ont.is_online,
        'last_seen': ont.last_seen.isoformat() if ont.last_seen else None,
        'ip_address': ont.ip_address,
        'monitoring': {
            'optical_power_rx': latest_data.optical_power_rx if latest_data else None,
            'optical_power_tx': latest_data.optical_power_tx if latest_data else None,
            'connection_status': latest_data.connection_status if latest_data else None,
            'wifi_devices_2_4': latest_data.wifi_devices_2_4 if latest_data else 0,
            'wifi_devices_5': latest_data.wifi_devices_5 if latest_data else 0,
            'wifi_devices_guest': latest_data.wifi_devices_guest if latest_data else 0,
            'timestamp': latest_data.timestamp.isoformat() if latest_data else None
        }
    }
    
    return jsonify(status)

@customer_bp.route('/api/onts/<int:ont_id>/monitoring_data')
@login_required
def get_monitoring_data(ont_id):
    """API para obtener datos de monitoreo de una ONT"""
    ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first_or_404()
    
    # Obtener parámetros de consulta
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Obtener datos de monitoreo
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
            'optical_temperature': d.optical_temperature,
            'connection_status': d.connection_status,
            'uptime': d.uptime,
            'wifi_devices_2_4': d.wifi_devices_2_4,
            'wifi_devices_5': d.wifi_devices_5,
            'wifi_devices_guest': d.wifi_devices_guest,
            'bytes_sent': d.bytes_sent,
            'bytes_received': d.bytes_received,
            'packets_sent': d.packets_sent,
            'packets_received': d.packets_received
        })
    
    return jsonify(result)