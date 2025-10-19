"""
Monitoring API - Device diagnostics and monitoring
"""
from flask import Blueprint, request, jsonify
from database.models import db, Device, DeviceDiagnostics, ConnectedDevice, EventLog
from tr069.device_manager import DeviceManager
from datetime import datetime, timedelta
from sqlalchemy import func

monitoring_api = Blueprint('monitoring_api', __name__, url_prefix='/api/monitoring')

@monitoring_api.route('/devices/<int:device_id>/diagnostics', methods=['GET'])
def get_device_diagnostics(device_id):
    """Get device diagnostics data"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get time range
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get diagnostics history
        diagnostics = DeviceDiagnostics.query.filter(
            DeviceDiagnostics.device_id == device_id,
            DeviceDiagnostics.collected_at >= since
        ).order_by(DeviceDiagnostics.collected_at).all()
        
        return jsonify({
            'device_id': device_id,
            'diagnostics': [d.to_dict() for d in diagnostics]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/diagnostics/latest', methods=['GET'])
def get_latest_diagnostics(device_id):
    """Get latest diagnostics for a device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        latest = DeviceDiagnostics.query.filter_by(device_id=device_id).order_by(
            DeviceDiagnostics.collected_at.desc()
        ).first()
        
        if not latest:
            return jsonify({'error': 'No diagnostics data available'}), 404
        
        return jsonify({
            'diagnostics': latest.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/collect', methods=['POST'])
def collect_diagnostics(device_id):
    """Trigger diagnostics collection for a device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get diagnostic parameters
        diagnostic_params = [
            DeviceManager.HUAWEI_PARAMS['optical_power_rx'],
            DeviceManager.HUAWEI_PARAMS['optical_power_tx'],
            DeviceManager.HUAWEI_PARAMS['temperature'],
            DeviceManager.HUAWEI_PARAMS['uptime'],
            DeviceManager.HUAWEI_PARAMS['wan_ip'],
            DeviceManager.HUAWEI_PARAMS['hosts_count'],
        ]
        
        # Create task to get parameters
        from database.models import ConfigurationTask
        task = ConfigurationTask(
            device_id=device_id,
            task_type='get_parameters',
            parameters={'parameters': diagnostic_params},
            status='pending'
        )
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Diagnostics collection scheduled',
            'task_id': task.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/connected', methods=['GET'])
def get_connected_devices(device_id):
    """Get devices connected to WiFi"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get active connections
        connected = ConnectedDevice.query.filter_by(
            device_id=device_id,
            is_active=True
        ).all()
        
        return jsonify({
            'device_id': device_id,
            'connected_count': len(connected),
            'connected_devices': [cd.to_dict() for cd in connected]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/optical-power', methods=['GET'])
def get_optical_power(device_id):
    """Get optical power readings"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get time range
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get optical power history
        readings = db.session.query(
            DeviceDiagnostics.collected_at,
            DeviceDiagnostics.optical_power_rx,
            DeviceDiagnostics.optical_power_tx
        ).filter(
            DeviceDiagnostics.device_id == device_id,
            DeviceDiagnostics.collected_at >= since
        ).order_by(DeviceDiagnostics.collected_at).all()
        
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.collected_at.isoformat(),
                'rx_power': float(reading.optical_power_rx) if reading.optical_power_rx else None,
                'tx_power': float(reading.optical_power_tx) if reading.optical_power_tx else None
            })
        
        return jsonify({
            'device_id': device_id,
            'readings': data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/signal-quality', methods=['GET'])
def get_signal_quality(device_id):
    """Get signal quality assessment"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get latest diagnostics
        latest = DeviceDiagnostics.query.filter_by(device_id=device_id).order_by(
            DeviceDiagnostics.collected_at.desc()
        ).first()
        
        if not latest:
            return jsonify({'error': 'No diagnostics data available'}), 404
        
        # Assess signal quality based on optical power
        # Typical ranges for GPON:
        # Excellent: > -20 dBm
        # Good: -20 to -25 dBm
        # Fair: -25 to -28 dBm
        # Poor: < -28 dBm
        
        quality = 'unknown'
        rx_power = float(latest.optical_power_rx) if latest.optical_power_rx else None
        
        if rx_power:
            if rx_power > -20:
                quality = 'excellent'
            elif rx_power > -25:
                quality = 'good'
            elif rx_power > -28:
                quality = 'fair'
            else:
                quality = 'poor'
        
        return jsonify({
            'device_id': device_id,
            'signal_quality': quality,
            'optical_power_rx': rx_power,
            'optical_power_tx': float(latest.optical_power_tx) if latest.optical_power_tx else None,
            'temperature': float(latest.temperature) if latest.temperature else None,
            'wan_status': latest.wan_status,
            'collected_at': latest.collected_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/events', methods=['GET'])
def get_device_events(device_id):
    """Get device event history"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        limit = int(request.args.get('limit', 50))
        event_type = request.args.get('type')
        
        query = EventLog.query.filter_by(device_id=device_id)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(EventLog.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'device_id': device_id,
            'events': [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/devices/<int:device_id>/uptime', methods=['GET'])
def get_device_uptime(device_id):
    """Get device uptime statistics"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get latest uptime
        latest = DeviceDiagnostics.query.filter_by(device_id=device_id).order_by(
            DeviceDiagnostics.collected_at.desc()
        ).first()
        
        if not latest or not latest.uptime:
            return jsonify({'error': 'No uptime data available'}), 404
        
        # Convert seconds to human readable format
        uptime_seconds = latest.uptime
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        return jsonify({
            'device_id': device_id,
            'uptime_seconds': uptime_seconds,
            'uptime_formatted': f'{days}d {hours}h {minutes}m',
            'collected_at': latest.collected_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/stats/devices', methods=['GET'])
def get_device_statistics():
    """Get overall device statistics"""
    try:
        total = Device.query.count()
        online = Device.query.filter_by(status='online').count()
        offline = Device.query.filter_by(status='offline').count()
        
        # Get devices by manufacturer
        by_manufacturer = db.session.query(
            Device.manufacturer,
            func.count(Device.id)
        ).group_by(Device.manufacturer).all()
        
        # Get devices by model
        by_model = db.session.query(
            Device.model,
            func.count(Device.id)
        ).group_by(Device.model).all()
        
        return jsonify({
            'total_devices': total,
            'online_devices': online,
            'offline_devices': offline,
            'by_manufacturer': [{'manufacturer': m[0], 'count': m[1]} for m in by_manufacturer],
            'by_model': [{'model': m[0], 'count': m[1]} for m in by_model]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@monitoring_api.route('/stats/alerts', methods=['GET'])
def get_alerts():
    """Get alerts for devices with issues"""
    try:
        alerts = []
        
        # Check for offline devices
        offline_devices = Device.query.filter_by(status='offline').all()
        for device in offline_devices:
            alerts.append({
                'severity': 'warning',
                'device_id': device.id,
                'serial_number': device.serial_number,
                'message': 'Device is offline',
                'timestamp': device.last_inform.isoformat() if device.last_inform else None
            })
        
        # Check for poor signal quality
        poor_signal = db.session.query(Device, DeviceDiagnostics).join(
            DeviceDiagnostics,
            Device.id == DeviceDiagnostics.device_id
        ).filter(
            DeviceDiagnostics.optical_power_rx < -28,
            DeviceDiagnostics.collected_at >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        for device, diag in poor_signal:
            alerts.append({
                'severity': 'critical',
                'device_id': device.id,
                'serial_number': device.serial_number,
                'message': f'Poor signal quality: {diag.optical_power_rx} dBm',
                'timestamp': diag.collected_at.isoformat()
            })
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
