const db = require('../database/connection');
const logger = require('../utils/logger');

class DeviceManager {
    constructor() {
        this.db = db;
    }

    async initialize() {
        await this.db.initialize();
        logger.info('Device Manager initialized');
    }

    async registerDevice(deviceInfo) {
        try {
            // Check if device already exists
            let device = await this.getDeviceBySerial(deviceInfo.serialNumber);
            
            if (device) {
                // Update existing device
                await this.updateDevice(device.id, {
                    ip_address: deviceInfo.ipAddress,
                    last_inform: deviceInfo.lastInform,
                    status: 'online'
                });
                
                // Update parameters
                if (deviceInfo.parameters) {
                    await this.updateDeviceParameters(device.id, deviceInfo.parameters);
                }
                
                device.status = 'online';
                logger.info(`Device updated: ${deviceInfo.serialNumber}`);
            } else {
                // Create new device
                const result = await this.db.query(`
                    INSERT INTO devices (
                        serial_number, manufacturer, model, 
                        ip_address, last_inform, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                `, [
                    deviceInfo.serialNumber,
                    deviceInfo.manufacturer,
                    deviceInfo.productClass,
                    deviceInfo.ipAddress,
                    deviceInfo.lastInform,
                    'online'
                ]);

                device = {
                    id: result.insertId,
                    serial_number: deviceInfo.serialNumber,
                    manufacturer: deviceInfo.manufacturer,
                    model: deviceInfo.productClass,
                    status: 'online'
                };

                // Insert initial parameters
                if (deviceInfo.parameters) {
                    await this.updateDeviceParameters(device.id, deviceInfo.parameters);
                }

                // Auto-assign profile if available
                await this.autoAssignProfile(device);

                // Trigger auto-assignment service for new devices
                this.triggerAutoAssignment(device);

                logger.info(`New device registered: ${deviceInfo.serialNumber}`);
            }

            return device;

        } catch (error) {
            logger.error('Error registering device:', error);
            throw error;
        }
    }

    async getDeviceBySerial(serialNumber) {
        try {
            const devices = await this.db.query(
                'SELECT * FROM devices WHERE serial_number = ?',
                [serialNumber]
            );
            return devices[0] || null;
        } catch (error) {
            logger.error('Error getting device by serial:', error);
            throw error;
        }
    }

    async getDeviceById(deviceId) {
        try {
            const devices = await this.db.query(
                'SELECT * FROM devices WHERE id = ?',
                [deviceId]
            );
            return devices[0] || null;
        } catch (error) {
            logger.error('Error getting device by ID:', error);
            throw error;
        }
    }

    async updateDevice(deviceId, updates) {
        try {
            const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
            const values = Object.values(updates);
            values.push(deviceId);

            await this.db.query(
                `UPDATE devices SET ${fields} WHERE id = ?`,
                values
            );

            logger.debug(`Device ${deviceId} updated`);
        } catch (error) {
            logger.error('Error updating device:', error);
            throw error;
        }
    }

    async updateDeviceStatus(deviceId, status) {
        try {
            await this.db.query(
                'UPDATE devices SET status = ?, updated_at = NOW() WHERE id = ?',
                [status, deviceId]
            );
            logger.debug(`Device ${deviceId} status updated to ${status}`);
        } catch (error) {
            logger.error('Error updating device status:', error);
            throw error;
        }
    }

    async updateDeviceParameters(deviceId, parameters) {
        try {
            for (const [paramName, paramValue] of Object.entries(parameters)) {
                await this.db.query(`
                    INSERT INTO device_configurations (device_id, parameter_name, parameter_value)
                    VALUES (?, ?, ?)
                    ON DUPLICATE KEY UPDATE 
                        parameter_value = VALUES(parameter_value),
                        last_updated = NOW()
                `, [deviceId, paramName, String(paramValue)]);
            }

            // Extract and update specific configurations
            await this.extractWiFiConfig(deviceId, parameters);
            await this.extractNetworkConfig(deviceId, parameters);
            await this.updateMonitoringData(deviceId, parameters);

            logger.debug(`Parameters updated for device ${deviceId}`);
        } catch (error) {
            logger.error('Error updating device parameters:', error);
            throw error;
        }
    }

    async extractWiFiConfig(deviceId, parameters) {
        try {
            const wifiConfig = {};
            
            // Extract WiFi 2.4GHz parameters
            if (parameters['Device.WiFi.SSID.1.SSID']) {
                wifiConfig.ssid_2_4ghz = parameters['Device.WiFi.SSID.1.SSID'];
            }
            if (parameters['Device.WiFi.AccessPoint.1.Security.KeyPassphrase']) {
                wifiConfig.password_2_4ghz = parameters['Device.WiFi.AccessPoint.1.Security.KeyPassphrase'];
            }
            if (parameters['Device.WiFi.Radio.1.Channel']) {
                wifiConfig.channel_2_4ghz = parseInt(parameters['Device.WiFi.Radio.1.Channel']);
            }
            if (parameters['Device.WiFi.SSID.1.Enable']) {
                wifiConfig.enabled_2_4ghz = parameters['Device.WiFi.SSID.1.Enable'] === 'true';
            }

            // Extract WiFi 5GHz parameters
            if (parameters['Device.WiFi.SSID.2.SSID']) {
                wifiConfig.ssid_5ghz = parameters['Device.WiFi.SSID.2.SSID'];
            }
            if (parameters['Device.WiFi.AccessPoint.2.Security.KeyPassphrase']) {
                wifiConfig.password_5ghz = parameters['Device.WiFi.AccessPoint.2.Security.KeyPassphrase'];
            }
            if (parameters['Device.WiFi.Radio.2.Channel']) {
                wifiConfig.channel_5ghz = parseInt(parameters['Device.WiFi.Radio.2.Channel']);
            }
            if (parameters['Device.WiFi.SSID.2.Enable']) {
                wifiConfig.enabled_5ghz = parameters['Device.WiFi.SSID.2.Enable'] === 'true';
            }

            if (Object.keys(wifiConfig).length > 0) {
                await this.db.query(`
                    INSERT INTO wifi_configurations (device_id, ${Object.keys(wifiConfig).join(', ')})
                    VALUES (?, ${Object.keys(wifiConfig).map(() => '?').join(', ')})
                    ON DUPLICATE KEY UPDATE 
                        ${Object.keys(wifiConfig).map(key => `${key} = VALUES(${key})`).join(', ')},
                        updated_at = NOW()
                `, [deviceId, ...Object.values(wifiConfig)]);
            }

        } catch (error) {
            logger.error('Error extracting WiFi config:', error);
        }
    }

    async extractNetworkConfig(deviceId, parameters) {
        try {
            const networkConfig = {};
            
            // Extract WAN configuration
            if (parameters['Device.PPP.Interface.1.Username']) {
                networkConfig.wan_type = 'PPPoE';
                networkConfig.pppoe_username = parameters['Device.PPP.Interface.1.Username'];
            }
            if (parameters['Device.PPP.Interface.1.Password']) {
                networkConfig.pppoe_password = parameters['Device.PPP.Interface.1.Password'];
            }
            if (parameters['Device.DNS.Client.Server.1']) {
                networkConfig.primary_dns = parameters['Device.DNS.Client.Server.1'];
            }
            if (parameters['Device.DNS.Client.Server.2']) {
                networkConfig.secondary_dns = parameters['Device.DNS.Client.Server.2'];
            }
            if (parameters['Device.Ethernet.VLANTermination.1.VLANID']) {
                networkConfig.vlan_id = parseInt(parameters['Device.Ethernet.VLANTermination.1.VLANID']);
            }

            if (Object.keys(networkConfig).length > 0) {
                await this.db.query(`
                    INSERT INTO network_configurations (device_id, ${Object.keys(networkConfig).join(', ')})
                    VALUES (?, ${Object.keys(networkConfig).map(() => '?').join(', ')})
                    ON DUPLICATE KEY UPDATE 
                        ${Object.keys(networkConfig).map(key => `${key} = VALUES(${key})`).join(', ')},
                        updated_at = NOW()
                `, [deviceId, ...Object.values(networkConfig)]);
            }

        } catch (error) {
            logger.error('Error extracting network config:', error);
        }
    }

    async updateMonitoringData(deviceId, parameters) {
        try {
            const monitoringData = {};
            
            // Extract monitoring parameters
            if (parameters['Device.Optical.Interface.1.OpticalSignalLevel']) {
                monitoringData.optical_power = parseFloat(parameters['Device.Optical.Interface.1.OpticalSignalLevel']);
            }
            if (parameters['Device.Optical.Interface.1.ReceiveOpticalPower']) {
                monitoringData.optical_rx_power = parseFloat(parameters['Device.Optical.Interface.1.ReceiveOpticalPower']);
            }
            if (parameters['Device.Optical.Interface.1.TransmitOpticalPower']) {
                monitoringData.optical_tx_power = parseFloat(parameters['Device.Optical.Interface.1.TransmitOpticalPower']);
            }
            if (parameters['Device.DeviceInfo.TemperatureStatus.TemperatureSensor.1.Value']) {
                monitoringData.temperature = parseFloat(parameters['Device.DeviceInfo.TemperatureStatus.TemperatureSensor.1.Value']);
            }
            if (parameters['Device.DeviceInfo.ProcessStatus.CPUUsage']) {
                monitoringData.cpu_usage = parseFloat(parameters['Device.DeviceInfo.ProcessStatus.CPUUsage']);
            }
            if (parameters['Device.DeviceInfo.MemoryStatus.Total']) {
                const total = parseInt(parameters['Device.DeviceInfo.MemoryStatus.Total']);
                const free = parseInt(parameters['Device.DeviceInfo.MemoryStatus.Free'] || '0');
                monitoringData.memory_usage = ((total - free) / total * 100).toFixed(2);
            }
            if (parameters['Device.DeviceInfo.UpTime']) {
                monitoringData.uptime = parseInt(parameters['Device.DeviceInfo.UpTime']);
            }

            // Count WiFi clients
            let wifiClients24 = 0, wifiClients5 = 0;
            Object.keys(parameters).forEach(key => {
                if (key.includes('Device.WiFi.AccessPoint.1.AssociatedDevice') && key.includes('MACAddress')) {
                    wifiClients24++;
                } else if (key.includes('Device.WiFi.AccessPoint.2.AssociatedDevice') && key.includes('MACAddress')) {
                    wifiClients5++;
                }
            });
            
            monitoringData.wifi_clients_2_4ghz = wifiClients24;
            monitoringData.wifi_clients_5ghz = wifiClients5;
            monitoringData.total_wifi_clients = wifiClients24 + wifiClients5;

            if (Object.keys(monitoringData).length > 0) {
                await this.db.query(`
                    INSERT INTO monitoring_data (device_id, ${Object.keys(monitoringData).join(', ')})
                    VALUES (?, ${Object.keys(monitoringData).map(() => '?').join(', ')})
                `, [deviceId, ...Object.values(monitoringData)]);
            }

        } catch (error) {
            logger.error('Error updating monitoring data:', error);
        }
    }

    async autoAssignProfile(device) {
        try {
            // Find matching profile based on model
            const profiles = await this.db.query(
                'SELECT * FROM configuration_profiles WHERE ont_model = ? AND is_active = TRUE',
                [device.model]
            );

            if (profiles.length > 0) {
                const profile = profiles[0];
                await this.db.query(
                    'UPDATE devices SET profile_id = ? WHERE id = ?',
                    [profile.id, device.id]
                );
                
                logger.info(`Auto-assigned profile ${profile.name} to device ${device.serial_number}`);
                
                // Apply profile configuration
                await this.applyProfile(device.id, profile);
            }

        } catch (error) {
            logger.error('Error auto-assigning profile:', error);
        }
    }

    async applyProfile(deviceId, profile) {
        try {
            const TaskQueue = require('./taskQueue');
            const taskQueue = new TaskQueue();
            await taskQueue.initialize();

            // Apply default configuration
            if (profile.default_config) {
                const config = JSON.parse(profile.default_config);
                const parameters = this.convertConfigToParameters(config);
                
                if (parameters.length > 0) {
                    await taskQueue.addTask(deviceId, 'set_parameters', {
                        parameters: parameters,
                        parameterKey: `profile_${profile.id}_default`
                    });
                }
            }

            // Apply WiFi configuration
            if (profile.wifi_config) {
                const wifiConfig = JSON.parse(profile.wifi_config);
                const wifiParameters = this.convertWiFiConfigToParameters(wifiConfig, deviceId);
                
                if (wifiParameters.length > 0) {
                    await taskQueue.addTask(deviceId, 'set_parameters', {
                        parameters: wifiParameters,
                        parameterKey: `profile_${profile.id}_wifi`
                    });
                }
            }

            // Apply network configuration
            if (profile.network_config) {
                const networkConfig = JSON.parse(profile.network_config);
                const networkParameters = this.convertNetworkConfigToParameters(networkConfig);
                
                if (networkParameters.length > 0) {
                    await taskQueue.addTask(deviceId, 'set_parameters', {
                        parameters: networkParameters,
                        parameterKey: `profile_${profile.id}_network`
                    });
                }
            }

            logger.info(`Profile ${profile.name} applied to device ${deviceId}`);

        } catch (error) {
            logger.error('Error applying profile:', error);
        }
    }

    convertConfigToParameters(config) {
        const parameters = [];
        // Convert configuration object to TR069 parameters
        // This would be specific to the device model and configuration structure
        return parameters;
    }

    convertWiFiConfigToParameters(wifiConfig, deviceId) {
        const parameters = [];
        
        if (wifiConfig.ssid_2_4ghz) {
            // Replace placeholders
            let ssid = wifiConfig.ssid_2_4ghz.replace('{SERIAL_LAST_4}', deviceId.toString().slice(-4));
            parameters.push({
                name: 'Device.WiFi.SSID.1.SSID',
                value: ssid,
                type: 'xsd:string'
            });
        }
        
        if (wifiConfig.password_2_4ghz) {
            let password = wifiConfig.password_2_4ghz.replace('{SERIAL_LAST_6}', deviceId.toString().slice(-6));
            parameters.push({
                name: 'Device.WiFi.AccessPoint.1.Security.KeyPassphrase',
                value: password,
                type: 'xsd:string'
            });
        }
        
        if (wifiConfig.channel_2_4ghz) {
            parameters.push({
                name: 'Device.WiFi.Radio.1.Channel',
                value: wifiConfig.channel_2_4ghz.toString(),
                type: 'xsd:unsignedInt'
            });
        }

        // 5GHz configuration
        if (wifiConfig.ssid_5ghz) {
            let ssid = wifiConfig.ssid_5ghz.replace('{SERIAL_LAST_4}', deviceId.toString().slice(-4));
            parameters.push({
                name: 'Device.WiFi.SSID.2.SSID',
                value: ssid,
                type: 'xsd:string'
            });
        }
        
        if (wifiConfig.password_5ghz) {
            let password = wifiConfig.password_5ghz.replace('{SERIAL_LAST_6}', deviceId.toString().slice(-6));
            parameters.push({
                name: 'Device.WiFi.AccessPoint.2.Security.KeyPassphrase',
                value: password,
                type: 'xsd:string'
            });
        }
        
        if (wifiConfig.channel_5ghz) {
            parameters.push({
                name: 'Device.WiFi.Radio.2.Channel',
                value: wifiConfig.channel_5ghz.toString(),
                type: 'xsd:unsignedInt'
            });
        }

        return parameters;
    }

    convertNetworkConfigToParameters(networkConfig) {
        const parameters = [];
        
        if (networkConfig.primary_dns) {
            parameters.push({
                name: 'Device.DNS.Client.Server.1',
                value: networkConfig.primary_dns,
                type: 'xsd:string'
            });
        }
        
        if (networkConfig.secondary_dns) {
            parameters.push({
                name: 'Device.DNS.Client.Server.2',
                value: networkConfig.secondary_dns,
                type: 'xsd:string'
            });
        }
        
        if (networkConfig.mtu) {
            parameters.push({
                name: 'Device.IP.Interface.1.MaxMTUSize',
                value: networkConfig.mtu.toString(),
                type: 'xsd:unsignedInt'
            });
        }

        return parameters;
    }

    async getAllDevices() {
        try {
            return await this.db.query(`
                SELECT d.*, c.name as client_name, p.name as profile_name
                FROM devices d
                LEFT JOIN clients c ON d.client_id = c.id
                LEFT JOIN configuration_profiles p ON d.profile_id = p.id
                ORDER BY d.last_inform DESC
            `);
        } catch (error) {
            logger.error('Error getting all devices:', error);
            throw error;
        }
    }

    async getDevicesByClient(clientId) {
        try {
            return await this.db.query(
                'SELECT * FROM devices WHERE client_id = ? ORDER BY last_inform DESC',
                [clientId]
            );
        } catch (error) {
            logger.error('Error getting devices by client:', error);
            throw error;
        }
    }

    async triggerAutoAssignment(device) {
        try {
            // Import here to avoid circular dependency
            const AutoAssignmentService = require('../services/autoAssignmentService');
            const autoAssignmentService = new AutoAssignmentService();
            await autoAssignmentService.initialize();
            
            // Process device for auto-assignment in background
            setImmediate(async () => {
                try {
                    await autoAssignmentService.processNewDevice(device);
                } catch (error) {
                    logger.error('Error in auto-assignment:', error);
                }
            });
        } catch (error) {
            logger.error('Error triggering auto-assignment:', error);
        }
    }
}

module.exports = DeviceManager;