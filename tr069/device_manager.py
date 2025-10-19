"""
Device Manager - Handles device operations and auto-provisioning
"""
from database.models import db, Device, DeviceParameter, ConfigurationProfile, ConfigurationTask, EventLog, Client
from datetime import datetime
import string
import secrets

class DeviceManager:
    
    # Common TR-069 parameter paths for Huawei ONTs
    HUAWEI_PARAMS = {
        'wifi_ssid_24': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.SSID',
        'wifi_password_24': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.PreSharedKey.1.KeyPassphrase',
        'wifi_enable_24': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.Enable',
        'wifi_ssid_5': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.SSID',
        'wifi_password_5': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.PreSharedKey.1.KeyPassphrase',
        'wifi_enable_5': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.Enable',
        'wan_pppoe_username': 'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Username',
        'wan_pppoe_password': 'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.Password',
        'wan_vlan_id': 'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.X_CT-COM_VLANIDMark',
        'dns_primary': 'InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.DNSServers',
        'optical_power_rx': 'InternetGatewayDevice.WANDevice.1.X_CT-COM_EponInterfaceConfig.RXPower',
        'optical_power_tx': 'InternetGatewayDevice.WANDevice.1.X_CT-COM_EponInterfaceConfig.TXPower',
        'temperature': 'InternetGatewayDevice.DeviceInfo.TemperatureStatus.TemperatureValue',
        'uptime': 'InternetGatewayDevice.DeviceInfo.UpTime',
        'wan_ip': 'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress',
        'lan_ip': 'InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceIPAddress',
        'mac_address': 'InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.1.MACAddress',
        'hosts_count': 'InternetGatewayDevice.LANDevice.1.Hosts.HostNumberOfEntries',
    }
    
    @staticmethod
    def register_device(device_info, parameters):
        """Register or update a device from Inform message"""
        try:
            serial_number = device_info.get('SerialNumber')
            if not serial_number:
                return None
            
            device = Device.query.filter_by(serial_number=serial_number).first()
            
            if not device:
                device = Device(
                    serial_number=serial_number,
                    status='online'
                )
                db.session.add(device)
            
            # Update device info
            device.oui = device_info.get('OUI')
            device.product_class = device_info.get('ProductClass')
            device.manufacturer = device_info.get('Manufacturer')
            device.model = device_info.get('Model', device_info.get('ProductClass'))
            device.hardware_version = device_info.get('HardwareVersion')
            device.software_version = device_info.get('SoftwareVersion')
            device.last_inform = datetime.utcnow()
            device.status = 'online'
            
            # Store connection request info
            for param_name, param_value in parameters.items():
                if 'ManagementServer.ConnectionRequestURL' in param_name:
                    device.connection_request_url = param_value
                elif 'ManagementServer.ConnectionRequestUsername' in param_name:
                    device.connection_request_username = param_value
                elif 'ManagementServer.ConnectionRequestPassword' in param_name:
                    device.connection_request_password = param_value
                elif 'ExternalIPAddress' in param_name or 'WANIPAddress' in param_name:
                    device.ip_address = param_value
                elif 'MACAddress' in param_name and not device.mac_address:
                    device.mac_address = param_value
            
            db.session.commit()
            
            # Store all parameters
            DeviceManager.update_device_parameters(device.id, parameters)
            
            # Log event
            event = EventLog(
                device_id=device.id,
                event_code='1 BOOT' if device.provisioning_status == 'not_provisioned' else '2 PERIODIC',
                event_type='Inform',
                description='Device connected to ACS'
            )
            db.session.add(event)
            db.session.commit()
            
            # Check if auto-provisioning is needed
            if device.provisioning_status == 'not_provisioned':
                DeviceManager.auto_provision_device(device)
            
            return device
            
        except Exception as e:
            db.session.rollback()
            print(f"Error registering device: {e}")
            return None
    
    @staticmethod
    def update_device_parameters(device_id, parameters):
        """Update device parameters in database"""
        try:
            for param_name, param_value in parameters.items():
                param = DeviceParameter.query.filter_by(
                    device_id=device_id,
                    parameter_name=param_name
                ).first()
                
                if param:
                    param.parameter_value = str(param_value)
                    param.last_updated = datetime.utcnow()
                else:
                    param = DeviceParameter(
                        device_id=device_id,
                        parameter_name=param_name,
                        parameter_value=str(param_value),
                        parameter_type='string'
                    )
                    db.session.add(param)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating parameters: {e}")
    
    @staticmethod
    def auto_provision_device(device):
        """Auto-provision device based on configuration profiles"""
        try:
            # Find matching configuration profile
            profiles = ConfigurationProfile.query.filter_by(is_active=True).order_by(
                ConfigurationProfile.priority.desc()
            ).all()
            
            matching_profile = None
            for profile in profiles:
                if not profile.model_filter or profile.model_filter in device.model:
                    matching_profile = profile
                    break
            
            if not matching_profile:
                # Create default configuration
                config = DeviceManager.generate_default_config(device)
            else:
                config = matching_profile.configuration
            
            # Update provisioning status
            device.provisioning_status = 'provisioning'
            db.session.commit()
            
            # Create configuration tasks
            DeviceManager.apply_configuration(device.id, config)
            
            # Log event
            event = EventLog(
                device_id=device.id,
                event_code='AUTO_PROVISION',
                event_type='Provisioning',
                description=f'Auto-provisioning started with profile: {matching_profile.name if matching_profile else "Default"}'
            )
            db.session.add(event)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error auto-provisioning device: {e}")
    
    @staticmethod
    def generate_default_config(device):
        """Generate default configuration for a device"""
        # Generate random WiFi password
        password = DeviceManager.generate_wifi_password()
        
        config = {
            'wifi_24': {
                'ssid': f'WIFI-{device.serial_number[-6:]}',
                'password': password,
                'enabled': True
            },
            'wifi_5': {
                'ssid': f'WIFI-{device.serial_number[-6:]}-5G',
                'password': password,
                'enabled': True
            },
            'dns': {
                'primary': '8.8.8.8',
                'secondary': '8.8.4.4'
            }
        }
        
        return config
    
    @staticmethod
    def generate_wifi_password(length=12):
        """Generate secure random WiFi password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))
    
    @staticmethod
    def apply_configuration(device_id, config):
        """Apply configuration to device by creating tasks"""
        try:
            parameters = {}
            
            # WiFi 2.4 GHz
            if 'wifi_24' in config:
                wifi24 = config['wifi_24']
                if 'ssid' in wifi24:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_ssid_24']] = wifi24['ssid']
                if 'password' in wifi24:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_password_24']] = wifi24['password']
                if 'enabled' in wifi24:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_enable_24']] = '1' if wifi24['enabled'] else '0'
            
            # WiFi 5 GHz
            if 'wifi_5' in config:
                wifi5 = config['wifi_5']
                if 'ssid' in wifi5:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_ssid_5']] = wifi5['ssid']
                if 'password' in wifi5:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_password_5']] = wifi5['password']
                if 'enabled' in wifi5:
                    parameters[DeviceManager.HUAWEI_PARAMS['wifi_enable_5']] = '1' if wifi5['enabled'] else '0'
            
            # DNS
            if 'dns' in config:
                dns = config['dns']
                if 'primary' in dns:
                    dns_value = dns['primary']
                    if 'secondary' in dns:
                        dns_value += f",{dns['secondary']}"
                    parameters[DeviceManager.HUAWEI_PARAMS['dns_primary']] = dns_value
            
            # PPPoE
            if 'pppoe' in config:
                pppoe = config['pppoe']
                if 'username' in pppoe:
                    parameters[DeviceManager.HUAWEI_PARAMS['wan_pppoe_username']] = pppoe['username']
                if 'password' in pppoe:
                    parameters[DeviceManager.HUAWEI_PARAMS['wan_pppoe_password']] = pppoe['password']
            
            # VLAN
            if 'vlan' in config:
                parameters[DeviceManager.HUAWEI_PARAMS['wan_vlan_id']] = str(config['vlan'])
            
            # Create task
            if parameters:
                task = ConfigurationTask(
                    device_id=device_id,
                    task_type='set_parameters',
                    parameters={'parameters': parameters},
                    status='pending'
                )
                db.session.add(task)
                db.session.commit()
                
                return task.id
            
            return None
            
        except Exception as e:
            db.session.rollback()
            print(f"Error applying configuration: {e}")
            return None
    
    @staticmethod
    def create_reboot_task(device_id):
        """Create a reboot task for a device"""
        try:
            task = ConfigurationTask(
                device_id=device_id,
                task_type='reboot',
                status='pending'
            )
            db.session.add(task)
            db.session.commit()
            return task.id
        except Exception as e:
            db.session.rollback()
            print(f"Error creating reboot task: {e}")
            return None
    
    @staticmethod
    def create_firmware_upgrade_task(device_id, firmware_url, file_size=0):
        """Create a firmware upgrade task"""
        try:
            task = ConfigurationTask(
                device_id=device_id,
                task_type='firmware_upgrade',
                parameters={'url': firmware_url, 'file_size': file_size},
                status='pending'
            )
            db.session.add(task)
            db.session.commit()
            return task.id
        except Exception as e:
            db.session.rollback()
            print(f"Error creating firmware upgrade task: {e}")
            return None
    
    @staticmethod
    def get_pending_tasks(device_id):
        """Get pending tasks for a device"""
        return ConfigurationTask.query.filter_by(
            device_id=device_id,
            status='pending'
        ).order_by(ConfigurationTask.created_at).all()
    
    @staticmethod
    def update_task_status(task_id, status, error_message=None):
        """Update task status"""
        try:
            task = ConfigurationTask.query.get(task_id)
            if task:
                task.status = status
                if error_message:
                    task.error_message = error_message
                if status == 'in_progress':
                    task.started_at = datetime.utcnow()
                elif status in ['completed', 'failed', 'timeout']:
                    task.completed_at = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating task status: {e}")
    
    @staticmethod
    def assign_device_to_client(device_id, client_id):
        """Assign a device to a client"""
        try:
            device = Device.query.get(device_id)
            if device:
                device.client_id = client_id
                db.session.commit()
                
                # Log event
                event = EventLog(
                    device_id=device_id,
                    event_code='CLIENT_ASSIGNED',
                    event_type='Assignment',
                    description=f'Device assigned to client {client_id}'
                )
                db.session.add(event)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error assigning device to client: {e}")
            return False
