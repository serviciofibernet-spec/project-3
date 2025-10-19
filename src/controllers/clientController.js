const db = require('../database/connection');
const DeviceManager = require('../tr069/deviceManager');
const TaskQueue = require('../tr069/taskQueue');
const logger = require('../utils/logger');

class ClientController {
    constructor() {
        this.db = db;
        this.deviceManager = new DeviceManager();
        this.taskQueue = new TaskQueue();
    }

    async initialize() {
        await this.db.initialize();
        await this.deviceManager.initialize();
        await this.taskQueue.initialize();
    }

    // Get all clients
    async getAllClients(req, res) {
        try {
            const clients = await this.db.query(`
                SELECT c.*, u.username, u.email as user_email,
                       COUNT(d.id) as device_count
                FROM clients c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN devices d ON c.id = d.client_id
                WHERE c.is_active = TRUE
                GROUP BY c.id
                ORDER BY c.name
            `);

            res.json({
                success: true,
                data: clients
            });

        } catch (error) {
            logger.error('Error getting all clients:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve clients'
            });
        }
    }

    // Get client by ID
    async getClientById(req, res) {
        try {
            const { id } = req.params;

            const clients = await this.db.query(
                'SELECT * FROM clients WHERE id = ? AND is_active = TRUE',
                [id]
            );

            if (clients.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'Client not found'
                });
            }

            const client = clients[0];

            // Get client's devices
            const devices = await this.deviceManager.getDevicesByClient(id);

            // Get device monitoring data
            const devicesWithMonitoring = await Promise.all(
                devices.map(async (device) => {
                    const monitoring = await this.getLatestMonitoringData(device.id);
                    return {
                        ...device,
                        monitoring
                    };
                })
            );

            res.json({
                success: true,
                data: {
                    ...client,
                    devices: devicesWithMonitoring
                }
            });

        } catch (error) {
            logger.error('Error getting client by ID:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve client'
            });
        }
    }

    // Create new client
    async createClient(req, res) {
        try {
            const { name, address, phone, email, service_plan, client_code } = req.body;

            // Validate required fields
            if (!name || !client_code) {
                return res.status(400).json({
                    success: false,
                    error: 'Name and client code are required'
                });
            }

            // Check if client code already exists
            const existingClients = await this.db.query(
                'SELECT id FROM clients WHERE client_code = ?',
                [client_code]
            );

            if (existingClients.length > 0) {
                return res.status(400).json({
                    success: false,
                    error: 'Client code already exists'
                });
            }

            // Create client
            const result = await this.db.query(`
                INSERT INTO clients (name, address, phone, email, service_plan, client_code)
                VALUES (?, ?, ?, ?, ?, ?)
            `, [name, address, phone, email, service_plan, client_code]);

            const newClient = {
                id: result.insertId,
                name,
                address,
                phone,
                email,
                service_plan,
                client_code
            };

            logger.info(`New client created: ${name} (${client_code})`);

            res.status(201).json({
                success: true,
                data: newClient
            });

        } catch (error) {
            logger.error('Error creating client:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to create client'
            });
        }
    }

    // Update client
    async updateClient(req, res) {
        try {
            const { id } = req.params;
            const updates = req.body;

            // Remove fields that shouldn't be updated directly
            delete updates.id;
            delete updates.created_at;
            delete updates.updated_at;

            if (Object.keys(updates).length === 0) {
                return res.status(400).json({
                    success: false,
                    error: 'No valid fields to update'
                });
            }

            // Check if client exists
            const existingClients = await this.db.query(
                'SELECT id FROM clients WHERE id = ? AND is_active = TRUE',
                [id]
            );

            if (existingClients.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'Client not found'
                });
            }

            // Update client
            const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
            const values = Object.values(updates);
            values.push(id);

            await this.db.query(
                `UPDATE clients SET ${fields}, updated_at = NOW() WHERE id = ?`,
                values
            );

            logger.info(`Client ${id} updated`);

            res.json({
                success: true,
                message: 'Client updated successfully'
            });

        } catch (error) {
            logger.error('Error updating client:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to update client'
            });
        }
    }

    // Assign device to client
    async assignDevice(req, res) {
        try {
            const { id } = req.params; // client ID
            const { deviceId, serialNumber } = req.body;

            let device;

            if (deviceId) {
                device = await this.deviceManager.getDeviceById(deviceId);
            } else if (serialNumber) {
                device = await this.deviceManager.getDeviceBySerial(serialNumber);
            } else {
                return res.status(400).json({
                    success: false,
                    error: 'Device ID or serial number is required'
                });
            }

            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            // Check if client exists
            const clients = await this.db.query(
                'SELECT id FROM clients WHERE id = ? AND is_active = TRUE',
                [id]
            );

            if (clients.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'Client not found'
                });
            }

            // Assign device to client
            await this.deviceManager.updateDevice(device.id, {
                client_id: id
            });

            logger.info(`Device ${device.serial_number} assigned to client ${id}`);

            res.json({
                success: true,
                message: 'Device assigned successfully'
            });

        } catch (error) {
            logger.error('Error assigning device:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to assign device'
            });
        }
    }

    // Unassign device from client
    async unassignDevice(req, res) {
        try {
            const { id } = req.params; // client ID
            const { deviceId } = req.body;

            const device = await this.deviceManager.getDeviceById(deviceId);
            if (!device) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found'
                });
            }

            if (device.client_id !== parseInt(id)) {
                return res.status(400).json({
                    success: false,
                    error: 'Device is not assigned to this client'
                });
            }

            // Unassign device
            await this.deviceManager.updateDevice(device.id, {
                client_id: null
            });

            logger.info(`Device ${device.serial_number} unassigned from client ${id}`);

            res.json({
                success: true,
                message: 'Device unassigned successfully'
            });

        } catch (error) {
            logger.error('Error unassigning device:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to unassign device'
            });
        }
    }

    // Client self-service: Update WiFi settings
    async updateClientWiFi(req, res) {
        try {
            const { id } = req.params; // client ID
            const { deviceId, wifiSettings } = req.body;

            // Verify device belongs to client
            const device = await this.deviceManager.getDeviceById(deviceId);
            if (!device || device.client_id !== parseInt(id)) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found or not assigned to this client'
                });
            }

            // Validate WiFi settings
            const validation = this.validateWiFiSettings(wifiSettings);
            if (!validation.valid) {
                return res.status(400).json({
                    success: false,
                    error: validation.error
                });
            }

            // Add task to queue
            const taskId = await this.taskQueue.updateWiFiSettings(deviceId, wifiSettings);

            // Log the change
            await this.logClientAction(id, 'wifi_update', {
                deviceId,
                settings: wifiSettings
            });

            res.json({
                success: true,
                message: 'WiFi settings update queued',
                taskId: taskId
            });

        } catch (error) {
            logger.error('Error updating client WiFi:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to update WiFi settings'
            });
        }
    }

    // Get client device status
    async getClientDeviceStatus(req, res) {
        try {
            const { id, deviceId } = req.params;

            // Verify device belongs to client
            const device = await this.deviceManager.getDeviceById(deviceId);
            if (!device || device.client_id !== parseInt(id)) {
                return res.status(404).json({
                    success: false,
                    error: 'Device not found or not assigned to this client'
                });
            }

            // Get device status and monitoring data
            const monitoring = await this.getLatestMonitoringData(deviceId);
            const connectedDevices = await this.getConnectedDevices(deviceId);
            const wifiConfig = await this.getWiFiConfiguration(deviceId);

            res.json({
                success: true,
                data: {
                    device: {
                        id: device.id,
                        serial_number: device.serial_number,
                        model: device.model,
                        status: device.status,
                        last_inform: device.last_inform
                    },
                    monitoring,
                    connectedDevices,
                    wifiConfig
                }
            });

        } catch (error) {
            logger.error('Error getting client device status:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve device status'
            });
        }
    }

    // Get client dashboard data
    async getClientDashboard(req, res) {
        try {
            const { id } = req.params;

            // Get client info
            const clients = await this.db.query(
                'SELECT * FROM clients WHERE id = ? AND is_active = TRUE',
                [id]
            );

            if (clients.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'Client not found'
                });
            }

            const client = clients[0];

            // Get client's devices with monitoring data
            const devices = await this.deviceManager.getDevicesByClient(id);
            const devicesWithData = await Promise.all(
                devices.map(async (device) => {
                    const monitoring = await this.getLatestMonitoringData(device.id);
                    const connectedDevices = await this.getConnectedDevices(device.id);
                    
                    return {
                        ...device,
                        monitoring,
                        connectedDevicesCount: connectedDevices.length
                    };
                })
            );

            // Get recent tasks
            const recentTasks = await this.getClientRecentTasks(id);

            res.json({
                success: true,
                data: {
                    client,
                    devices: devicesWithData,
                    recentTasks,
                    summary: {
                        totalDevices: devices.length,
                        onlineDevices: devices.filter(d => d.status === 'online').length,
                        totalConnectedDevices: devicesWithData.reduce((sum, d) => sum + d.connectedDevicesCount, 0)
                    }
                }
            });

        } catch (error) {
            logger.error('Error getting client dashboard:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to retrieve dashboard data'
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

        return {
            valid: errors.length === 0,
            error: errors.join(', ')
        };
    }

    async getLatestMonitoringData(deviceId) {
        try {
            const monitoringData = await this.db.query(`
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

    async getConnectedDevices(deviceId) {
        try {
            const connectedDevices = await this.db.query(`
                SELECT * FROM connected_devices 
                WHERE ont_device_id = ? AND is_active = TRUE
                ORDER BY connected_at DESC
            `, [deviceId]);

            return connectedDevices;
        } catch (error) {
            logger.error('Error getting connected devices:', error);
            return [];
        }
    }

    async getWiFiConfiguration(deviceId) {
        try {
            const wifiConfig = await this.db.query(
                'SELECT * FROM wifi_configurations WHERE device_id = ?',
                [deviceId]
            );

            return wifiConfig[0] || null;
        } catch (error) {
            logger.error('Error getting WiFi configuration:', error);
            return null;
        }
    }

    async getClientRecentTasks(clientId) {
        try {
            const tasks = await this.db.query(`
                SELECT tq.*, d.serial_number
                FROM task_queue tq
                JOIN devices d ON tq.device_id = d.id
                WHERE d.client_id = ?
                ORDER BY tq.created_at DESC
                LIMIT 10
            `, [clientId]);

            return tasks.map(task => ({
                ...task,
                parameters: JSON.parse(task.parameters || '{}')
            }));
        } catch (error) {
            logger.error('Error getting client recent tasks:', error);
            return [];
        }
    }

    async logClientAction(clientId, action, data) {
        try {
            await this.db.query(`
                INSERT INTO system_logs (level, message, additional_data, created_at)
                VALUES ('info', ?, ?, NOW())
            `, [
                `Client ${clientId} performed action: ${action}`,
                JSON.stringify({ clientId, action, data })
            ]);
        } catch (error) {
            logger.error('Error logging client action:', error);
        }
    }
}

module.exports = ClientController;