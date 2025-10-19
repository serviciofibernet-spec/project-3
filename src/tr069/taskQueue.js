const db = require('../database/connection');
const logger = require('../utils/logger');

class TaskQueue {
    constructor() {
        this.db = db;
    }

    async initialize() {
        await this.db.initialize();
        logger.info('Task Queue initialized');
    }

    async addTask(deviceId, taskType, parameters = {}, priority = 5, scheduledAt = null) {
        try {
            const result = await this.db.query(`
                INSERT INTO task_queue (
                    device_id, task_type, parameters, priority, scheduled_at
                ) VALUES (?, ?, ?, ?, ?)
            `, [
                deviceId,
                taskType,
                JSON.stringify(parameters),
                priority,
                scheduledAt || new Date()
            ]);

            logger.info(`Task added: ${taskType} for device ${deviceId}`, { taskId: result.insertId });
            return result.insertId;

        } catch (error) {
            logger.error('Error adding task:', error);
            throw error;
        }
    }

    async getPendingTasks(deviceId, limit = 10) {
        try {
            const tasks = await this.db.query(`
                SELECT * FROM task_queue 
                WHERE device_id = ? AND status = 'pending' 
                    AND scheduled_at <= NOW()
                ORDER BY priority DESC, scheduled_at ASC
                LIMIT ?
            `, [deviceId, limit]);

            // Parse parameters JSON for each task
            return tasks.map(task => ({
                ...task,
                parameters: JSON.parse(task.parameters || '{}')
            }));

        } catch (error) {
            logger.error('Error getting pending tasks:', error);
            throw error;
        }
    }

    async getTasksByType(deviceId, taskType) {
        try {
            const tasks = await this.db.query(`
                SELECT * FROM task_queue 
                WHERE device_id = ? AND task_type = ?
                ORDER BY created_at DESC
            `, [deviceId, taskType]);

            return tasks.map(task => ({
                ...task,
                parameters: JSON.parse(task.parameters || '{}')
            }));

        } catch (error) {
            logger.error('Error getting tasks by type:', error);
            throw error;
        }
    }

    async startTask(taskId) {
        try {
            await this.db.query(`
                UPDATE task_queue 
                SET status = 'in_progress', started_at = NOW()
                WHERE id = ?
            `, [taskId]);

            logger.debug(`Task ${taskId} started`);

        } catch (error) {
            logger.error('Error starting task:', error);
            throw error;
        }
    }

    async completeTask(taskId, result = {}) {
        try {
            await this.db.query(`
                UPDATE task_queue 
                SET status = 'completed', completed_at = NOW()
                WHERE id = ?
            `, [taskId]);

            logger.info(`Task ${taskId} completed`);

        } catch (error) {
            logger.error('Error completing task:', error);
            throw error;
        }
    }

    async failTask(taskId, errorMessage) {
        try {
            const task = await this.getTaskById(taskId);
            if (!task) {
                throw new Error(`Task ${taskId} not found`);
            }

            const newRetryCount = task.retry_count + 1;
            
            if (newRetryCount < task.max_retries) {
                // Retry the task
                await this.db.query(`
                    UPDATE task_queue 
                    SET status = 'pending', retry_count = ?, error_message = ?,
                        scheduled_at = DATE_ADD(NOW(), INTERVAL ? MINUTE)
                    WHERE id = ?
                `, [newRetryCount, errorMessage, Math.pow(2, newRetryCount), taskId]);

                logger.warn(`Task ${taskId} failed, retry ${newRetryCount}/${task.max_retries}`);
            } else {
                // Mark as failed permanently
                await this.db.query(`
                    UPDATE task_queue 
                    SET status = 'failed', error_message = ?
                    WHERE id = ?
                `, [errorMessage, taskId]);

                logger.error(`Task ${taskId} failed permanently: ${errorMessage}`);
            }

        } catch (error) {
            logger.error('Error failing task:', error);
            throw error;
        }
    }

    async updateTask(taskId, updates) {
        try {
            const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
            const values = Object.values(updates);
            values.push(taskId);

            await this.db.query(
                `UPDATE task_queue SET ${fields} WHERE id = ?`,
                values
            );

            logger.debug(`Task ${taskId} updated`);

        } catch (error) {
            logger.error('Error updating task:', error);
            throw error;
        }
    }

    async getTaskById(taskId) {
        try {
            const tasks = await this.db.query(
                'SELECT * FROM task_queue WHERE id = ?',
                [taskId]
            );

            if (tasks.length === 0) {
                return null;
            }

            const task = tasks[0];
            return {
                ...task,
                parameters: JSON.parse(task.parameters || '{}')
            };

        } catch (error) {
            logger.error('Error getting task by ID:', error);
            throw error;
        }
    }

    async cancelTask(taskId) {
        try {
            await this.db.query(`
                UPDATE task_queue 
                SET status = 'cancelled'
                WHERE id = ? AND status IN ('pending', 'in_progress')
            `, [taskId]);

            logger.info(`Task ${taskId} cancelled`);

        } catch (error) {
            logger.error('Error cancelling task:', error);
            throw error;
        }
    }

    async getTaskHistory(deviceId, limit = 50) {
        try {
            const tasks = await this.db.query(`
                SELECT tq.*, u.username as created_by_username
                FROM task_queue tq
                LEFT JOIN users u ON tq.created_by = u.id
                WHERE tq.device_id = ?
                ORDER BY tq.created_at DESC
                LIMIT ?
            `, [deviceId, limit]);

            return tasks.map(task => ({
                ...task,
                parameters: JSON.parse(task.parameters || '{}')
            }));

        } catch (error) {
            logger.error('Error getting task history:', error);
            throw error;
        }
    }

    async getQueueStats() {
        try {
            const stats = await this.db.query(`
                SELECT 
                    status,
                    COUNT(*) as count
                FROM task_queue 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY status
            `);

            const result = {
                pending: 0,
                in_progress: 0,
                completed: 0,
                failed: 0,
                cancelled: 0
            };

            stats.forEach(stat => {
                result[stat.status] = stat.count;
            });

            return result;

        } catch (error) {
            logger.error('Error getting queue stats:', error);
            throw error;
        }
    }

    // Convenience methods for common tasks
    async rebootDevice(deviceId, userId = null) {
        return await this.addTask(deviceId, 'reboot', {}, 8, null);
    }

    async factoryResetDevice(deviceId, userId = null) {
        return await this.addTask(deviceId, 'factory_reset', {}, 9, null);
    }

    async updateWiFiSettings(deviceId, wifiSettings, userId = null) {
        const parameters = [];
        
        if (wifiSettings.ssid_2_4ghz) {
            parameters.push({
                name: 'Device.WiFi.SSID.1.SSID',
                value: wifiSettings.ssid_2_4ghz,
                type: 'xsd:string'
            });
        }
        
        if (wifiSettings.password_2_4ghz) {
            parameters.push({
                name: 'Device.WiFi.AccessPoint.1.Security.KeyPassphrase',
                value: wifiSettings.password_2_4ghz,
                type: 'xsd:string'
            });
        }
        
        if (wifiSettings.ssid_5ghz) {
            parameters.push({
                name: 'Device.WiFi.SSID.2.SSID',
                value: wifiSettings.ssid_5ghz,
                type: 'xsd:string'
            });
        }
        
        if (wifiSettings.password_5ghz) {
            parameters.push({
                name: 'Device.WiFi.AccessPoint.2.Security.KeyPassphrase',
                value: wifiSettings.password_5ghz,
                type: 'xsd:string'
            });
        }

        if (parameters.length > 0) {
            return await this.addTask(deviceId, 'set_parameters', {
                parameters: parameters,
                parameterKey: 'wifi_update_' + Date.now()
            }, 7, null);
        }

        return null;
    }

    async updateNetworkSettings(deviceId, networkSettings, userId = null) {
        const parameters = [];
        
        if (networkSettings.primary_dns) {
            parameters.push({
                name: 'Device.DNS.Client.Server.1',
                value: networkSettings.primary_dns,
                type: 'xsd:string'
            });
        }
        
        if (networkSettings.secondary_dns) {
            parameters.push({
                name: 'Device.DNS.Client.Server.2',
                value: networkSettings.secondary_dns,
                type: 'xsd:string'
            });
        }
        
        if (networkSettings.vlan_id) {
            parameters.push({
                name: 'Device.Ethernet.VLANTermination.1.VLANID',
                value: networkSettings.vlan_id.toString(),
                type: 'xsd:unsignedInt'
            });
        }

        if (parameters.length > 0) {
            return await this.addTask(deviceId, 'set_parameters', {
                parameters: parameters,
                parameterKey: 'network_update_' + Date.now()
            }, 6, null);
        }

        return null;
    }

    async upgradeFirmware(deviceId, firmwareUrl, fileSize = 0, userId = null) {
        return await this.addTask(deviceId, 'firmware_upgrade', {
            url: firmwareUrl,
            fileSize: fileSize,
            username: '',
            password: ''
        }, 9, null);
    }

    async getDeviceParameters(deviceId, parameterNames, userId = null) {
        return await this.addTask(deviceId, 'get_parameters', {
            parameterNames: parameterNames
        }, 3, null);
    }
}

module.exports = TaskQueue;