"""
Admin API - Management interface for administrators
"""
from flask import Blueprint, request, jsonify
from database.models import db, Device, Client, User, ConfigurationProfile, ConfigurationTask, EventLog, FirmwareVersion
from tr069.device_manager import DeviceManager
from functools import wraps

admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# Simple authentication decorator (in production, use proper JWT/OAuth)
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_api.route('/devices', methods=['GET'])
@require_admin
def get_devices():
    """Get all devices"""
    try:
        status_filter = request.args.get('status')
        client_id = request.args.get('client_id')
        
        query = Device.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        devices = query.all()
        
        return jsonify({
            'devices': [device.to_dict() for device in devices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>', methods=['GET'])
@require_admin
def get_device(device_id):
    """Get device details"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get latest diagnostics
        diagnostics = None
        if device.diagnostics:
            diagnostics = device.diagnostics[-1].to_dict()
        
        # Get recent events
        events = EventLog.query.filter_by(device_id=device_id).order_by(
            EventLog.created_at.desc()
        ).limit(10).all()
        
        # Get connected devices
        connected_devices = [cd.to_dict() for cd in device.connected_devices if cd.is_active]
        
        return jsonify({
            'device': device.to_dict(include_parameters=True),
            'diagnostics': diagnostics,
            'events': [event.to_dict() for event in events],
            'connected_devices': connected_devices
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>/wifi', methods=['PUT'])
@require_admin
def update_wifi(device_id):
    """Update WiFi settings"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.json
        config = {}
        
        if 'wifi_24' in data:
            config['wifi_24'] = data['wifi_24']
        
        if 'wifi_5' in data:
            config['wifi_5'] = data['wifi_5']
        
        # Apply configuration
        task_id = DeviceManager.apply_configuration(device_id, config)
        
        if task_id:
            return jsonify({
                'message': 'WiFi configuration task created',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create configuration task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>/configure', methods=['POST'])
@require_admin
def configure_device(device_id):
    """Apply full configuration to device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        config = request.json
        
        # Apply configuration
        task_id = DeviceManager.apply_configuration(device_id, config)
        
        if task_id:
            return jsonify({
                'message': 'Configuration task created',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create configuration task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>/reboot', methods=['POST'])
@require_admin
def reboot_device(device_id):
    """Reboot a device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        task_id = DeviceManager.create_reboot_task(device_id)
        
        if task_id:
            return jsonify({
                'message': 'Reboot task created',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create reboot task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>/firmware', methods=['POST'])
@require_admin
def upgrade_firmware(device_id):
    """Upgrade device firmware"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        data = request.json
        firmware_url = data.get('firmware_url')
        file_size = data.get('file_size', 0)
        
        if not firmware_url:
            return jsonify({'error': 'firmware_url is required'}), 400
        
        task_id = DeviceManager.create_firmware_upgrade_task(device_id, firmware_url, file_size)
        
        if task_id:
            return jsonify({
                'message': 'Firmware upgrade task created',
                'task_id': task_id
            }), 200
        else:
            return jsonify({'error': 'Failed to create firmware upgrade task'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/devices/<int:device_id>/assign', methods=['POST'])
@require_admin
def assign_device(device_id):
    """Assign device to a client"""
    try:
        data = request.json
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'error': 'client_id is required'}), 400
        
        success = DeviceManager.assign_device_to_client(device_id, client_id)
        
        if success:
            return jsonify({'message': 'Device assigned successfully'}), 200
        else:
            return jsonify({'error': 'Failed to assign device'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/clients', methods=['GET', 'POST'])
@require_admin
def clients():
    """Get all clients or create new client"""
    if request.method == 'GET':
        try:
            clients = Client.query.all()
            return jsonify({
                'clients': [client.to_dict() for client in clients]
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            client = Client(
                name=data.get('name'),
                document=data.get('document'),
                phone=data.get('phone'),
                email=data.get('email'),
                address=data.get('address'),
                notes=data.get('notes')
            )
            
            db.session.add(client)
            db.session.commit()
            
            return jsonify({
                'message': 'Client created successfully',
                'client': client.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_api.route('/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
@require_admin
def client_detail(client_id):
    """Get, update or delete a client"""
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    if request.method == 'GET':
        try:
            devices = Device.query.filter_by(client_id=client_id).all()
            return jsonify({
                'client': client.to_dict(),
                'devices': [device.to_dict() for device in devices]
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            if 'name' in data:
                client.name = data['name']
            if 'document' in data:
                client.document = data['document']
            if 'phone' in data:
                client.phone = data['phone']
            if 'email' in data:
                client.email = data['email']
            if 'address' in data:
                client.address = data['address']
            if 'notes' in data:
                client.notes = data['notes']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Client updated successfully',
                'client': client.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(client)
            db.session.commit()
            return jsonify({'message': 'Client deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_api.route('/profiles', methods=['GET', 'POST'])
@require_admin
def configuration_profiles():
    """Get all configuration profiles or create new one"""
    if request.method == 'GET':
        try:
            profiles = ConfigurationProfile.query.all()
            return jsonify({
                'profiles': [profile.to_dict() for profile in profiles]
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            profile = ConfigurationProfile(
                name=data.get('name'),
                description=data.get('description'),
                model_filter=data.get('model_filter'),
                configuration=data.get('configuration'),
                priority=data.get('priority', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(profile)
            db.session.commit()
            
            return jsonify({
                'message': 'Configuration profile created successfully',
                'profile': profile.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_api.route('/profiles/<int:profile_id>', methods=['GET', 'PUT', 'DELETE'])
@require_admin
def profile_detail(profile_id):
    """Get, update or delete a configuration profile"""
    profile = ConfigurationProfile.query.get(profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    if request.method == 'GET':
        return jsonify(profile.to_dict()), 200
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            if 'name' in data:
                profile.name = data['name']
            if 'description' in data:
                profile.description = data['description']
            if 'model_filter' in data:
                profile.model_filter = data['model_filter']
            if 'configuration' in data:
                profile.configuration = data['configuration']
            if 'priority' in data:
                profile.priority = data['priority']
            if 'is_active' in data:
                profile.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Profile updated successfully',
                'profile': profile.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(profile)
            db.session.commit()
            return jsonify({'message': 'Profile deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_api.route('/tasks', methods=['GET'])
@require_admin
def get_tasks():
    """Get all configuration tasks"""
    try:
        status_filter = request.args.get('status')
        device_id = request.args.get('device_id')
        
        query = ConfigurationTask.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        tasks = query.order_by(ConfigurationTask.created_at.desc()).limit(100).all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/events', methods=['GET'])
@require_admin
def get_events():
    """Get event log"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 100))
        
        query = EventLog.query
        
        if device_id:
            query = query.filter_by(device_id=device_id)
        
        events = query.order_by(EventLog.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'events': [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_api.route('/firmware', methods=['GET', 'POST'])
@require_admin
def firmware_versions():
    """Get all firmware versions or add new one"""
    if request.method == 'GET':
        try:
            firmware = FirmwareVersion.query.filter_by(is_active=True).all()
            return jsonify({
                'firmware': [fw.to_dict() for fw in firmware]
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            firmware = FirmwareVersion(
                manufacturer=data.get('manufacturer'),
                model=data.get('model'),
                version=data.get('version'),
                file_url=data.get('file_url'),
                file_size=data.get('file_size'),
                checksum=data.get('checksum'),
                release_date=data.get('release_date'),
                notes=data.get('notes')
            )
            
            db.session.add(firmware)
            db.session.commit()
            
            return jsonify({
                'message': 'Firmware version added successfully',
                'firmware': firmware.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_api.route('/dashboard/stats', methods=['GET'])
@require_admin
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status='online').count()
        offline_devices = Device.query.filter_by(status='offline').count()
        pending_devices = Device.query.filter_by(provisioning_status='not_provisioned').count()
        total_clients = Client.query.count()
        pending_tasks = ConfigurationTask.query.filter_by(status='pending').count()
        
        return jsonify({
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'pending_devices': pending_devices,
            'total_clients': total_clients,
            'pending_tasks': pending_tasks
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
