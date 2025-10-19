#!/usr/bin/env python3
"""
REST API for TR069 Server Management
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from functools import wraps
from datetime import datetime
import logging
from .auth import AuthManager
from .datamodel import TR069DataModel

# Configure Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tr069-secret-key-change-in-production')
CORS(app)

# Initialize managers
auth_manager = AuthManager()
data_model = TR069DataModel()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        session = auth_manager.validate_session(token)
        if not session:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add session info to request
        request.session = session
        return f(*args, **kwargs)
    
    return decorated_function

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    result = auth_manager.authenticate_user(username, password)
    if result:
        return jsonify({
            'success': True,
            'token': result['token'],
            'user': {
                'username': result['username'],
                'name': result['name'],
                'roles': result['roles']
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout"""
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        auth_manager.revoke_session(token)
    
    return jsonify({'success': True})

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords required'}), 400
    
    username = request.session['identifier']
    if auth_manager.change_password(username, old_password, new_password):
        return jsonify({'success': True})
    
    return jsonify({'error': 'Failed to change password'}), 400

# User management endpoints
@app.route('/api/users', methods=['GET'])
@require_auth
def list_users():
    """List all users"""
    users = auth_manager.list_users()
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@require_auth
def create_user():
    """Create new user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name', username)
    roles = data.get('roles', ['viewer'])
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if auth_manager.create_user(username, password, name, roles):
        return jsonify({'success': True})
    
    return jsonify({'error': 'User already exists'}), 400

@app.route('/api/users/<username>', methods=['DELETE'])
@require_auth
def delete_user(username):
    """Delete user"""
    if auth_manager.delete_user(username):
        return jsonify({'success': True})
    
    return jsonify({'error': 'User not found'}), 404

# Device management endpoints
@app.route('/api/devices', methods=['GET'])
@require_auth
def list_devices():
    """List all devices"""
    try:
        # Import here to avoid circular dependency
        from .server import TR069Handler
        devices = []
        for device_id in TR069Handler.device_manager.list_devices():
            device = TR069Handler.device_manager.get_device(device_id)
            if device:
                devices.append({
                    'id': device_id,
                    'info': device.get('info', {}),
                    'last_seen': device.get('last_seen'),
                    'first_seen': device.get('first_seen'),
                    'parameters_count': len(device.get('parameters', {}))
                })
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return jsonify({'error': 'Failed to list devices'}), 500

@app.route('/api/devices/<device_id>', methods=['GET'])
@require_auth
def get_device(device_id):
    """Get device details"""
    try:
        from .server import TR069Handler
        device = TR069Handler.device_manager.get_device(device_id)
        if device:
            return jsonify(device)
        return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        return jsonify({'error': 'Failed to get device'}), 500

@app.route('/api/devices/<device_id>/parameters', methods=['GET'])
@require_auth
def get_device_parameters(device_id):
    """Get device parameters"""
    try:
        from .server import TR069Handler
        device = TR069Handler.device_manager.get_device(device_id)
        if device:
            return jsonify(device.get('parameters', {}))
        return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error getting parameters: {e}")
        return jsonify({'error': 'Failed to get parameters'}), 500

@app.route('/api/devices/<device_id>/parameters', methods=['POST'])
@require_auth
def set_device_parameters(device_id):
    """Set device parameters (queue for next connection)"""
    try:
        from .server import TR069Handler
        device = TR069Handler.device_manager.get_device(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.get_json()
        parameters = data.get('parameters', {})
        
        # Queue parameter changes for next device connection
        if 'pending_changes' not in device:
            device['pending_changes'] = {}
        device['pending_changes'].update(parameters)
        TR069Handler.device_manager.save_device(device_id)
        
        return jsonify({'success': True, 'queued': len(parameters)})
    except Exception as e:
        logger.error(f"Error setting parameters: {e}")
        return jsonify({'error': 'Failed to set parameters'}), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
@require_auth
def delete_device(device_id):
    """Delete device"""
    try:
        from .server import TR069Handler
        with TR069Handler.device_manager.lock:
            if device_id in TR069Handler.device_manager.devices:
                del TR069Handler.device_manager.devices[device_id]
                # Delete file
                filepath = os.path.join(TR069Handler.device_manager.data_dir, f"{device_id}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'success': True})
        return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return jsonify({'error': 'Failed to delete device'}), 500

# Data model endpoints
@app.route('/api/datamodel', methods=['GET'])
@require_auth
def get_data_model():
    """Get TR069 data model structure"""
    try:
        return jsonify(data_model.root.to_dict())
    except Exception as e:
        logger.error(f"Error getting data model: {e}")
        return jsonify({'error': 'Failed to get data model'}), 500

@app.route('/api/datamodel/parameters', methods=['GET'])
@require_auth
def get_parameter_names():
    """Get parameter names"""
    path = request.args.get('path', '')
    next_level = request.args.get('nextLevel', 'false').lower() == 'true'
    
    try:
        names = data_model.get_parameter_names(path, next_level)
        return jsonify(names)
    except Exception as e:
        logger.error(f"Error getting parameter names: {e}")
        return jsonify({'error': 'Failed to get parameter names'}), 500

# Server status endpoints
@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server status"""
    try:
        from .server import TR069Handler
        
        return jsonify({
            'status': 'running',
            'devices_count': len(TR069Handler.device_manager.devices),
            'active_sessions': len(TR069Handler.session_manager.sessions),
            'server_time': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    """Get server logs"""
    limit = int(request.args.get('limit', 100))
    
    # Read log file
    log_file = 'logs/server.log'
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()[-limit:]
        return jsonify({'logs': lines})
    
    return jsonify({'logs': []})

# Configuration endpoints
@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Get server configuration"""
    config_file = 'config/server.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    
    return jsonify({'error': 'Configuration not found'}), 404

@app.route('/api/config', methods=['POST'])
@require_auth
def update_config():
    """Update server configuration"""
    data = request.get_json()
    config_file = 'config/server.json'
    
    try:
        # Load existing config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Update config
        config.update(data)
        
        # Save config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': 'Failed to update configuration'}), 500

# Static files (for web UI if needed)
@app.route('/')
def index():
    """Serve index page"""
    return jsonify({
        'name': 'TR069 ACS Server API',
        'version': '1.0.0',
        'endpoints': [
            '/api/status',
            '/api/auth/login',
            '/api/devices',
            '/api/datamodel',
            '/api/users',
            '/api/config'
        ]
    })

def run_api(host='0.0.0.0', port=8080, debug=False):
    """Run the API server"""
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api(debug=True)