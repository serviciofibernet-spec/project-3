"""
Client API - Self-service interface for end users
"""
from flask import Blueprint, request, jsonify, session
from database.models import db, Device, Client, User, ConnectedDevice, DeviceDiagnostics
from tr069.device_manager import DeviceManager
from functools import wraps

client_api = Blueprint('client_api', __name__, url_prefix='/api/client')

def require_client_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        
        # For now, extract client_id from session/token
        # In production, decode JWT and get client_id
        client_id = session.get('client_id')
        if not client_id:
            return jsonify({'error': 'Client ID not found'}), 401
        
        return f(client_id, *args, **kwargs)
    return decorated_function

@client_api.route('/devices', methods=['GET'])
@require_client_auth
def get_my_devices(client_id):
    """Get all devices for authenticated client"""
    try:
        devices = Device.query.filter_by(client_id=client_id).all()
        
        devices_data = []
        for device in devices:
            device_data = device.to_dict()
            
            # Add latest diagnostics
            if device.diagnostics:
                device_data['latest_diagnostics'] = device.diagnostics[-1].to_dict()
            
            # Add connected devices count
            active_connections = ConnectedDevice.query.filter_by(
                device_id=device.id, 
                is_active=True
            ).count()
            device_data['connected_devices_count'] = active_connections
            
            devices_data.append(device_data)
        
        return jsonify({
            'devices': devices_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_api.route('/devices/<int:device_id>', methods=['GET'])
@require_client_auth
def get_my_device(client_id, device_id):
    """Get specific device details"""
    try:
        device = Device.query.filter_by(id=device_id, client_id=client_id).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get WiFi info from parameters
        wifi_info = {}
        for param in device.parameters:
            if 'SSID' in param.parameter_name and 'WLANConfiguration.1' in param.parameter_name:
                wifi_info['ssid_24'] = param.parameter_value
            elif 'SSID' in param.parameter_name and 'WLANConfiguration.2' in param.parameter_name:
                wifi_info['ssid_5'] = param.parameter_value
            elif 'Enable' in param.parameter_name and 'WLANConfiguration.1' in param.parameter_name:
                wifi_info['enabled_24'] = param.parameter_value == '1'
            elif 'Enable' in param.parameter_name and 'WLANConfiguration.2' in param.parameter_name:
                wifi_info['enabled_5'] = param.parameter_value == '1'
        
        # Get latest diagnostics
        diagnostics = None
        if device.diagnostics:
            diagnostics = device.diagnostics[-1].to_dict()
        
        # Get connected devices
        connected_devices = ConnectedDevice.query.filter_by(
            device_id=device_id, 
            is_active=True
        ).all()
        
        return jsonify({
            'device': device.to_dict(),
            'wifi_info': wifi_info,
            'diagnostics': diagnostics,
            'connected_devices': [cd.to_dict() for cd in connected_devices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_api.route('/devices/<int:device_id>/wifi', methods=['PUT'])
@require_client_auth
def update_my_wifi(client_id, device_id):
    """Update WiFi settings for own device"""
    try:
        device = Device.query.filter_by(id=device_id, client_id=client_id).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.json
        
        # Validate password length
        if 'wifi_24' in data and 'password' in data['wifi_24']:
            password = data['wifi_24']['password']
            if len(password) < 8:
                return jsonify({'error': 'WiFi password must be at least 8 characters'}), 400
        
        if 'wifi_5' in data and 'password' in data['wifi_5']:
            password = data['wifi_5']['password']
            if len(password) < 8:
                return jsonify({'error': 'WiFi password must be at least 8 characters'}), 400
        
        config = {}
        
        if 'wifi_24' in data:
            config['wifi_24'] = data['wifi_24']
        
        if 'wifi_5' in data:
            config['wifi_5'] = data['wifi_5']
        
        # Apply configuration
        task_id = DeviceManager.apply_configuration(device_id, config)
        
        if task_id:
            return jsonify({
                'message': 'WiFi configuration will be applied shortly',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create configuration task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_api.route('/devices/<int:device_id>/reboot', methods=['POST'])
@require_client_auth
def reboot_my_device(client_id, device_id):
    """Reboot own device"""
    try:
        device = Device.query.filter_by(id=device_id, client_id=client_id).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        task_id = DeviceManager.create_reboot_task(device_id)
        
        if task_id:
            return jsonify({
                'message': 'Device will reboot shortly',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create reboot task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_api.route('/profile', methods=['GET'])
@require_client_auth
def get_my_profile(client_id):
    """Get client profile information"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        return jsonify({
            'client': client.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_api.route('/profile', methods=['PUT'])
@require_client_auth
def update_my_profile(client_id):
    """Update client profile"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        data = request.json
        
        # Only allow updating certain fields
        if 'phone' in data:
            client.phone = data['phone']
        if 'email' in data:
            client.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'client': client.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Public endpoint for login (no auth required)
@client_api.route('/login', methods=['POST'])
def client_login():
    """Client login endpoint"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username, role='client').first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Get client info
        client = Client.query.filter_by(user_id=user.id).first()
        
        if not client:
            return jsonify({'error': 'Client profile not found'}), 404
        
        # In production, generate JWT token here
        session['client_id'] = client.id
        session['user_id'] = user.id
        
        return jsonify({
            'message': 'Login successful',
            'client': client.to_dict(),
            'token': 'dummy-token'  # Replace with actual JWT
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
