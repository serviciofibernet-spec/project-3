const DeviceManager = require('../tr069/deviceManager');
const TaskQueue = require('../tr069/taskQueue');
const logger = require('../utils/logger');

class DeviceController {
    constructor() {
        this.deviceManager = new DeviceManager();
        this.taskQueue = new TaskQueue();
    }

    async initialize() {
        await this.deviceManager.initialize();
        await this.taskQueue.initialize();
    }

    // Get all devices
    async getAllDevices(req, res) {
        try {
            const devices = await this.deviceManager.getAllDevices();
            res.json({
                success: true,
                data: devices
            });
        } catch (error) {
            logger.error('Error getting all devices:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve devices'
            });
        }
    }

    // Get device by ID
    async getDeviceById(req, res) {
        try {
            const { id } = req.params;
            const device = await this.deviceManager.getDeviceById(id);
            
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Get device configurations
            const configurations = await this.getDeviceConfigurations(id);
            const monitoringData = await this.getLatestMonitoringData(id);
            const taskHistory = await this.taskQueue.getTaskHistory(id, 10);

            res.json({
                success: true,
                data: {
                    ...device,
                    configurations,
                    monitoring: monitoringData,
                    recentTasks: taskHistory
                }
            });

        } catch (error) {
            logger.error('Error getting device by ID:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve device'
            });
        }
    }

    // Update WiFi settings
    async updateWiFiSettings(req, res) {
        try {
            const { id } = req.params;
            const wifiSettings = req.body;

            // Validate input
            const validation = this.validateWiFiSettings(wifiSettings);
            if (!validation.valid) {
                return res.status(400).json({
                    success: false,
                    error: validation.error
                });
            }

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add task to queue
            const taskId = await this.taskQueue.updateWiFiSettings(id, wifiSettings, req.user?.id);

            res.json({
                success: true,
                message: 'WiFi settings update queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error updating WiFi settings:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to update WiFi settings'
            });
        }
    }

    // Update network settings
    async updateNetworkSettings(req, res) {
        try {
            const { id } = req.params;
            const networkSettings = req.body;

            // Validate input
            const validation = this.validateNetworkSettings(networkSettings);
            if (!validation.valid) {
                return res.status(400).json({
                    success: false,
                    error: validation.error
                });
            }

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add task to queue
            const taskId = await this.taskQueue.updateNetworkSettings(id, networkSettings, req.user?.id);

            res.json({
                success: true,
                message: 'Network settings update queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error updating network settings:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to update network settings'
            });
        }
    }

    // Reboot device
    async rebootDevice(req, res) {
        try {
            const { id } = req.params;

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add reboot task to queue
            const taskId = await this.taskQueue.rebootDevice(id, req.user?.id);

            res.json({
                success: true,
                message: 'Device reboot queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error rebooting device:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to reboot device'
            });
        }
    }

    // Factory reset device
    async factoryResetDevice(req, res) {
        try {
            const { id } = req.params;

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add factory reset task to queue
            const taskId = await this.taskQueue.factoryResetDevice(id, req.user?.id);

            res.json({
                success: true,
                message: 'Factory reset queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error factory resetting device:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to factory reset device'
            });
        }
    }

    // Upgrade firmware
    async upgradeFirmware(req, res) {
        try {
            const { id } = req.params;
            const { firmwareUrl, fileSize } = req.body;

            if (!firmwareUrl) {
                return res.status(400).json({
                    success: false,
                    error: 'Firmware URL is required'
                });
            }

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add firmware upgrade task to queue
            const taskId = await this.taskQueue.upgradeFirmware(id, firmwareUrl, fileSize, req.user?.id);

            res.json({
                success: true,
                message: 'Firmware upgrade queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error upgrading firmware:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to upgrade firmware'
            });
        }
    }

    // Get device parameters
    async getDeviceParameters(req, res) {
        try {
            const { id } = req.params;
            const { parameters } = req.body;

            if (!parameters || !Array.isArray(parameters)) {
                return res.status(400).json({
                    success: false,
                    error: 'Parameters array is required'
                });
            }

            // Check if device exists
            const device = await this.deviceManager.getDeviceById(id);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Add get parameters task to queue
            const taskId = await this.taskQueue.getDeviceParameters(id, parameters, req.user?.id);

            res.json({
                success: true,
                message: 'Parameter retrieval queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error getting device parameters:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to get device parameters'
            });
        }
    }

    // Get device monitoring data
    async getMonitoringData(req, res) {
        try {
            const { id } = req.params;
            const { hours = 24 } = req.query;

            const monitoringData = await this.getMonitoringDataHistory(id, hours);

            res.json({
                success: true,
                data: monitoringData
            });

        } catch (error) {
            logger.error('Error getting monitoring data:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve monitoring data'
            });
        }
    }

    // Get connected devices (WiFi clients)
    async getConnectedDevices(req, res) {
        try {
            const { id } = req.params;

            const connectedDevices = await this.getDeviceWiFiClients(id);

            res.json({
                success: true,
                data: connectedDevices
            });

        } catch (error) {
            logger.error('Error getting connected devices:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve connected devices'
            });
        }
    }

    // Get task status
    async getTaskStatus(req, res) {
        try {
            const { taskId } = req.params;

            const task = await this.taskQueue.getTaskById(taskId);
            if (!task) {
                return res.status(404).json({
                    success: false,
                    error: 'Task not found'
                });
            }

            res.json({
                success: true,
                data: task
            });

        } catch (error) {
            logger.error('Error getting task status:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve task status'
            });
        }
    }

    // Helper methods
    validateWiFiSettings(settings) {
        const errors = [];

        if (settings.ssid_2_4ghz && (settings.ssid_2_4ghz.length < 1 || settings.ssid_2_4ghz.length > 32)) {
            errors.push('2.4GHz SSID must be between 1 and 32 characters');
        }

        if (settings.password_2_4ghz && (settings.password_2_4ghz.length < 8 || settings.password_2_4ghz.length > 64)) {
            errors.push('2.4GHz password must be between 8 and 64 characters');
        }

        if (settings.ssid_5ghz && (settings.ssid_5ghz.length < 1 || settings.ssid_5ghz.length > 32)) {
            errors.push('5GHz SSID must be between 1 and 32 characters');
        }

        if (settings.password_5ghz && (settings.password_5ghz.length < 8 || settings.password_5ghz.length > 64)) {
            errors.push('5GHz password must be between 8 and 64 characters');
        }

        if (settings.channel_2_4ghz && (settings.channel_2_4ghz < 1 || settings.channel_2_4ghz > 14)) {
            errors.push('2.4GHz channel must be between 1 and 14');
        }

        if (settings.channel_5ghz && ![36, 40, 44, 48, 149, 153, 157, 161].includes(settings.channel_5ghz)) {
            errors.push('5GHz channel must be a valid channel (36, 40, 44, 48, 149, 153, 157, 161)');
        }

        return {
            valid: errors.length === 0,
            error: errors.join(', ')
        };
    }

    validateNetworkSettings(settings) {
        const errors = [];

        if (settings.primary_dns && !this.isValidIP(settings.primary_dns)) {
            errors.push('Primary DNS must be a valid IP address');
        }

        if (settings.secondary_dns && !this.isValidIP(settings.secondary_dns)) {
            errors.push('Secondary DNS must be a valid IP address');
        }

        if (settings.vlan_id && (settings.vlan_id < 1 || settings.vlan_id > 4094)) {
            errors.push('VLAN ID must be between 1 and 4094');
        }

        if (settings.mtu && (settings.mtu < 576 || settings.mtu > 1500)) {
            errors.push('MTU must be between 576 and 1500');
        }

        return {
            valid: errors.length === 0,
            error: errors.join(', ')
        };
    }

    isValidIP(ip) {
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }

    async getDeviceConfigurations(deviceId) {
        try {
            const db = this.deviceManager.db;
            
            const [wifiConfig, networkConfig, portConfig] = await Promise.all([
                db.query('SELECT * FROM wifi_configurations WHERE device_id = ?', [deviceId]),
                db.query('SELECT * FROM network_configurations WHERE device_id = ?', [deviceId]),
                db.query('SELECT * FROM port_configurations WHERE device_id = ?', [deviceId])
            ]);

            return {
                wifi: wifiConfig[0] || null,
                network: networkConfig[0] || null,
                ports: portConfig
            };

        } catch (error) {
            logger.error('Error getting device configurations:', error);
            return null;
        }
    }

    async getLatestMonitoringData(deviceId) {
        try {
            const db = this.deviceManager.db;
            
            const monitoringData = await db.query(`
                SELECT * FROM monitoring_data 
                WHERE device_id = ? 
                ORDER BY recorded_at DESC 
                LIMIT 1
            `, [deviceId]);

            return monitoringData[0] || null;

        } catch (error) {
            logger.error('Error getting latest monitoring data:', error);
            return null;
        }
    }

    async getMonitoringDataHistory(deviceId, hours) {
        try {
            const db = this.deviceManager.db;
            
            const monitoringData = await db.query(`
                SELECT * FROM monitoring_data 
                WHERE device_id = ? AND recorded_at >= DATE_SUB(NOW(), INTERVAL ? HOUR)
                ORDER BY recorded_at DESC
            `, [deviceId, hours]);

            return monitoringData;

        } catch (error) {
            logger.error('Error getting monitoring data history:', error);
            return [];
        }
    }

    async getDeviceWiFiClients(deviceId) {
        try {
            const db = this.deviceManager.db;
            
            const connectedDevices = await db.query(`
                SELECT * FROM connected_devices 
                WHERE ont_device_id = ? AND is_active = TRUE
                ORDER BY connected_at DESC
            `, [deviceId]);

            return connectedDevices;

        } catch (error) {
            logger.error('Error getting WiFi clients:', error);
            return [];
        }
    }
}

module.exports = DeviceController;