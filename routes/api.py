"""
API REST para el servidor TR-069
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database_models import db, ONT, Customer, MonitoringData
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/onts')
@login_required
def get_onts():
    """API para obtener lista de ONTs"""
    if current_user.is_admin:
        # Administradores ven todas las ONTs
        onts = ONT.query.all()
    else:
        # Clientes ven solo sus ONTs
        onts = ONT.query.filter_by(customer_id=current_user.id).all()
    
    result = []
    for ont in onts:
        result.append({
            'id': ont.id,
            'serial_number': ont.serial_number,
            'mac_address': ont.mac_address,
            'model': ont.model,
            'firmware_version': ont.firmware_version,
            'ip_address': ont.ip_address,
            'is_online': ont.is_online,
            'last_seen': ont.last_seen.isoformat() if ont.last_seen else None,
            'customer_id': ont.customer_id,
            'customer_name': ont.customer.full_name if ont.customer else None
        })
    
    return jsonify(result)

@api_bp.route('/onts/<int:ont_id>')
@login_required
def get_ont(ont_id):
    """API para obtener detalles de una ONT específica"""
    if current_user.is_admin:
        ont = ONT.query.get(ont_id)
    else:
        ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first()
    
    if not ont:
        return jsonify({'error': 'ONT no encontrada'}), 404
    
    # Obtener configuración WiFi
    wifi_settings = None
    if ont.wifi_settings:
        wifi_settings = {
            'wifi_2_4_enabled': ont.wifi_settings.wifi_2_4_enabled,
            'wifi_2_4_ssid': ont.wifi_settings.wifi_2_4_ssid,
            'wifi_2_4_channel': ont.wifi_settings.wifi_2_4_channel,
            'wifi_2_4_security': ont.wifi_settings.wifi_2_4_security,
            'wifi_5_enabled': ont.wifi_settings.wifi_5_enabled,
            'wifi_5_ssid': ont.wifi_settings.wifi_5_ssid,
            'wifi_5_channel': ont.wifi_settings.wifi_5_channel,
            'wifi_5_security': ont.wifi_settings.wifi_5_security,
            'wifi_guest_enabled': ont.wifi_settings.wifi_guest_enabled,
            'wifi_guest_ssid': ont.wifi_settings.wifi_guest_ssid,
            'wifi_guest_vlan': ont.wifi_settings.wifi_guest_vlan
        }
    
    # Obtener configuración de red
    network_settings = None
    if ont.network_settings:
        network_settings = {
            'ip_mode': ont.network_settings.ip_mode,
            'static_ip': ont.network_settings.static_ip,
            'static_gateway': ont.network_settings.static_gateway,
            'static_netmask': ont.network_settings.static_netmask,
            'pppoe_username': ont.network_settings.pppoe_username,
            'pppoe_service_name': ont.network_settings.pppoe_service_name,
            'vlan_id': ont.network_settings.vlan_id,
            'vlan_priority': ont.network_settings.vlan_priority,
            'dns_primary': ont.network_settings.dns_primary,
            'dns_secondary': ont.network_settings.dns_secondary
        }
    
    # Obtener último dato de monitoreo
    latest_monitoring = MonitoringData.query.filter_by(ont_id=ont_id)\
        .order_by(MonitoringData.timestamp.desc()).first()
    
    monitoring_data = None
    if latest_monitoring:
        monitoring_data = {
            'optical_power_rx': latest_monitoring.optical_power_rx,
            'optical_power_tx': latest_monitoring.optical_power_tx,
            'optical_temperature': latest_monitoring.optical_temperature,
            'connection_status': latest_monitoring.connection_status,
            'uptime': latest_monitoring.uptime,
            'wifi_devices_2_4': latest_monitoring.wifi_devices_2_4,
            'wifi_devices_5': latest_monitoring.wifi_devices_5,
            'wifi_devices_guest': latest_monitoring.wifi_devices_guest,
            'bytes_sent': latest_monitoring.bytes_sent,
            'bytes_received': latest_monitoring.bytes_received,
            'packets_sent': latest_monitoring.packets_sent,
            'packets_received': latest_monitoring.packets_received,
            'timestamp': latest_monitoring.timestamp.isoformat()
        }
    
    result = {
        'id': ont.id,
        'serial_number': ont.serial_number,
        'mac_address': ont.mac_address,
        'model': ont.model,
        'firmware_version': ont.firmware_version,
        'hardware_version': ont.hardware_version,
        'ip_address': ont.ip_address,
        'connection_id': ont.connection_id,
        'is_online': ont.is_online,
        'last_seen': ont.last_seen.isoformat() if ont.last_seen else None,
        'registration_time': ont.registration_time.isoformat() if ont.registration_time else None,
        'customer_id': ont.customer_id,
        'customer_name': ont.customer.full_name if ont.customer else None,
        'wifi_settings': wifi_settings,
        'network_settings': network_settings,
        'monitoring_data': monitoring_data
    }
    
    return jsonify(result)

@api_bp.route('/onts/<int:ont_id>/wifi', methods=['PUT'])
@login_required
def update_wifi_settings(ont_id):
    """API para actualizar configuración WiFi de una ONT"""
    if current_user.is_admin:
        ont = ONT.query.get(ont_id)
    else:
        ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first()
    
    if not ont:
        return jsonify({'error': 'ONT no encontrada'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos JSON requeridos'}), 400
    
    # Validar datos
    if 'wifi_2_4_ssid' in data and len(data['wifi_2_4_ssid']) > 32:
        return jsonify({'error': 'SSID 2.4GHz demasiado largo (máximo 32 caracteres)'}), 400
    
    if 'wifi_5_ssid' in data and len(data['wifi_5_ssid']) > 32:
        return jsonify({'error': 'SSID 5GHz demasiado largo (máximo 32 caracteres)'}), 400
    
    if 'wifi_2_4_password' in data and len(data['wifi_2_4_password']) < 8:
        return jsonify({'error': 'Contraseña 2.4GHz debe tener al menos 8 caracteres'}), 400
    
    if 'wifi_5_password' in data and len(data['wifi_5_password']) < 8:
        return jsonify({'error': 'Contraseña 5GHz debe tener al menos 8 caracteres'}), 400
    
    # Actualizar configuración WiFi
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.update_wifi_settings(ont_id, data)
    
    if success:
        return jsonify({'message': 'Configuración WiFi actualizada correctamente'})
    else:
        return jsonify({'error': 'Error al actualizar configuración WiFi'}), 500

@api_bp.route('/onts/<int:ont_id>/network', methods=['PUT'])
@login_required
def update_network_settings(ont_id):
    """API para actualizar configuración de red de una ONT"""
    if not current_user.is_admin:
        return jsonify({'error': 'Solo administradores pueden modificar configuración de red'}), 403
    
    ont = ONT.query.get(ont_id)
    if not ont:
        return jsonify({'error': 'ONT no encontrada'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos JSON requeridos'}), 400
    
    # Actualizar configuración de red
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.update_network_settings(ont_id, data)
    
    if success:
        return jsonify({'message': 'Configuración de red actualizada correctamente'})
    else:
        return jsonify({'error': 'Error al actualizar configuración de red'}), 500

@api_bp.route('/onts/<int:ont_id>/reboot', methods=['POST'])
@login_required
def reboot_ont(ont_id):
    """API para reiniciar una ONT"""
    if current_user.is_admin:
        ont = ONT.query.get(ont_id)
    else:
        ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first()
    
    if not ont:
        return jsonify({'error': 'ONT no encontrada'}), 404
    
    from tr069_server import TR069Server
    tr069_server = TR069Server()
    success = tr069_server.reboot_ont(ont_id)
    
    if success:
        return jsonify({'message': 'Comando de reinicio enviado correctamente'})
    else:
        return jsonify({'error': 'Error al enviar comando de reinicio'}), 500

@api_bp.route('/onts/<int:ont_id>/monitoring')
@login_required
def get_ont_monitoring(ont_id):
    """API para obtener datos de monitoreo de una ONT"""
    if current_user.is_admin:
        ont = ONT.query.get(ont_id)
    else:
        ont = ONT.query.filter_by(id=ont_id, customer_id=current_user.id).first()
    
    if not ont:
        return jsonify({'error': 'ONT no encontrada'}), 404
    
    # Obtener parámetros de consulta
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Obtener datos de monitoreo
    data = MonitoringData.query.filter(
        MonitoringData.ont_id == ont_id,
        MonitoringData.timestamp >= since
    ).order_by(MonitoringData.timestamp.desc()).limit(limit).all()
    
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

@api_bp.route('/stats')
@login_required
def get_stats():
    """API para obtener estadísticas generales"""
    if not current_user.is_admin:
        return jsonify({'error': 'Solo administradores pueden acceder a estadísticas'}), 403
    
    # Estadísticas generales
    total_onts = ONT.query.count()
    online_onts = ONT.query.filter_by(is_online=True).count()
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(is_active=True).count()
    
    # ONTs por modelo
    ont_models = db.session.query(
        ONT.model,
        db.func.count(ONT.id).label('count')
    ).group_by(ONT.model).all()
    
    # ONTs con problemas de potencia óptica
    low_power_onts = db.session.query(ONT).join(MonitoringData).filter(
        MonitoringData.optical_power_rx < -25.0
    ).count()
    
    # Estadísticas de tráfico
    traffic_stats = db.session.query(
        db.func.sum(MonitoringData.bytes_sent + MonitoringData.bytes_received).label('total_bytes'),
        db.func.avg(MonitoringData.bytes_sent + MonitoringData.bytes_received).label('avg_bytes')
    ).join(ONT).first()
    
    result = {
        'total_onts': total_onts,
        'online_onts': online_onts,
        'offline_onts': total_onts - online_onts,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'ont_models': [{'model': m[0], 'count': m[1]} for m in ont_models],
        'low_power_onts': low_power_onts,
        'total_traffic_bytes': int(traffic_stats.total_bytes) if traffic_stats.total_bytes else 0,
        'avg_traffic_bytes': int(traffic_stats.avg_bytes) if traffic_stats.avg_bytes else 0
    }
    
    return jsonify(result)

@api_bp.route('/onts/search')
@login_required
def search_onts():
    """API para buscar ONTs"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    if current_user.is_admin:
        onts = ONT.query.filter(
            (ONT.serial_number.contains(query)) |
            (ONT.mac_address.contains(query)) |
            (ONT.ip_address.contains(query)) |
            (ONT.model.contains(query))
        ).limit(10).all()
    else:
        onts = ONT.query.filter(
            ONT.customer_id == current_user.id,
            ((ONT.serial_number.contains(query)) |
             (ONT.mac_address.contains(query)) |
             (ONT.ip_address.contains(query)) |
             (ONT.model.contains(query)))
        ).limit(10).all()
    
    result = []
    for ont in onts:
        result.append({
            'id': ont.id,
            'serial_number': ont.serial_number,
            'mac_address': ont.mac_address,
            'model': ont.model,
            'is_online': ont.is_online,
            'customer_name': ont.customer.full_name if ont.customer else None
        })
    
    return jsonify(result)