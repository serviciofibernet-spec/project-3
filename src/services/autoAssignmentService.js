const db = require('../database/connection');
const DeviceManager = require('../tr069/deviceManager');
const logger = require('../utils/logger');

class AutoAssignmentService {
    constructor() {
        this.db = db;
        this.deviceManager = new DeviceManager();
        this.assignmentRules = [];
    }

    async initialize() {
        await this.db.initialize();
        await this.deviceManager.initialize();
        await this.loadAssignmentRules();
        logger.info('Auto Assignment Service initialized');
    }

    async loadAssignmentRules() {
        try {
            // Load assignment rules from database
            this.assignmentRules = await this.db.query(`
                SELECT * FROM assignment_rules 
                WHERE is_active = TRUE 
                ORDER BY priority DESC
            `);
            
            logger.info(`Loaded ${this.assignmentRules.length} assignment rules`);
        } catch (error) {
            logger.error('Error loading assignment rules:', error);
            this.assignmentRules = [];
        }
    }

    async processNewDevice(device) {
        try {
            logger.info(`Processing new device for auto-assignment: ${device.serial_number}`);

            // Check if device is already assigned
            if (device.client_id) {
                logger.info(`Device ${device.serial_number} already assigned to client ${device.client_id}`);
                return;
            }

            // Try to find matching client based on rules
            const matchedClient = await this.findMatchingClient(device);
            
            if (matchedClient) {
                await this.assignDeviceToClient(device.id, matchedClient.id);
                logger.info(`Auto-assigned device ${device.serial_number} to client ${matchedClient.name}`);
                
                // Apply client-specific profile if available
                await this.applyClientProfile(device.id, matchedClient.id);
            } else {
                logger.info(`No matching client found for device ${device.serial_number}`);
                
                // Create notification for admin
                await this.createAssignmentNotification(device);
            }

        } catch (error) {
            logger.error('Error processing new device for auto-assignment:', error);
        }
    }

    async findMatchingClient(device) {
        try {
            // Apply assignment rules in priority order
            for (const rule of this.assignmentRules) {
                const client = await this.applyAssignmentRule(device, rule);
                if (client) {
                    return client;
                }
            }

            // If no rules match, try pattern-based assignment
            return await this.patternBasedAssignment(device);

        } catch (error) {
            logger.error('Error finding matching client:', error);
            return null;
        }
    }

    async applyAssignmentRule(device, rule) {
        try {
            const ruleConfig = JSON.parse(rule.rule_config);
            
            switch (rule.rule_type) {
                case 'serial_pattern':
                    return await this.applySerialPatternRule(device, ruleConfig);
                
                case 'mac_pattern':
                    return await this.applyMacPatternRule(device, ruleConfig);
                
                case 'location_based':
                    return await this.applyLocationBasedRule(device, ruleConfig);
                
                case 'service_area':
                    return await this.applyServiceAreaRule(device, ruleConfig);
                
                default:
                    logger.warn(`Unknown rule type: ${rule.rule_type}`);
                    return null;
            }

        } catch (error) {
            logger.error('Error applying assignment rule:', error);
            return null;
        }
    }

    async applySerialPatternRule(device, ruleConfig) {
        try {
            const { pattern, client_id } = ruleConfig;
            const regex = new RegExp(pattern, 'i');
            
            if (regex.test(device.serial_number)) {
                const clients = await this.db.query(
                    'SELECT * FROM clients WHERE id = ? AND is_active = TRUE',
                    [client_id]
                );
                return clients[0] || null;
            }
            
            return null;
        } catch (error) {
            logger.error('Error applying serial pattern rule:', error);
            return null;
        }
    }

    async applyMacPatternRule(device, ruleConfig) {
        try {
            const { pattern, client_id } = ruleConfig;
            
            if (!device.mac_address) return null;
            
            const regex = new RegExp(pattern, 'i');
            
            if (regex.test(device.mac_address)) {
                const clients = await this.db.query(
                    'SELECT * FROM clients WHERE id = ? AND is_active = TRUE',
                    [client_id]
                );
                return clients[0] || null;
            }
            
            return null;
        } catch (error) {
            logger.error('Error applying MAC pattern rule:', error);
            return null;
        }
    }

    async applyLocationBasedRule(device, ruleConfig) {
        try {
            // This would require additional location data in the device parameters
            // For now, return null as location data is not available
            return null;
        } catch (error) {
            logger.error('Error applying location-based rule:', error);
            return null;
        }
    }

    async applyServiceAreaRule(device, ruleConfig) {
        try {
            const { service_area, client_query } = ruleConfig;
            
            // This is a more complex rule that would match based on service area
            // Implementation would depend on how service areas are defined
            return null;
        } catch (error) {
            logger.error('Error applying service area rule:', error);
            return null;
        }
    }

    async patternBasedAssignment(device) {
        try {
            // Try to match based on common patterns
            
            // Pattern 1: Serial number contains client code
            const serialPattern = device.serial_number.substring(0, 6); // First 6 characters
            let clients = await this.db.query(
                'SELECT * FROM clients WHERE client_code LIKE ? AND is_active = TRUE',
                [`%${serialPattern}%`]
            );
            
            if (clients.length === 1) {
                return clients[0];
            }

            // Pattern 2: Look for clients with similar naming patterns
            const serialSuffix = device.serial_number.slice(-4); // Last 4 characters
            clients = await this.db.query(
                'SELECT * FROM clients WHERE client_code LIKE ? AND is_active = TRUE',
                [`%${serialSuffix}`]
            );
            
            if (clients.length === 1) {
                return clients[0];
            }

            // Pattern 3: Check for pre-registered devices
            const preRegistered = await this.db.query(`
                SELECT c.* FROM clients c
                JOIN pre_registered_devices prd ON c.id = prd.client_id
                WHERE prd.serial_number = ? AND prd.is_active = TRUE
            `, [device.serial_number]);
            
            if (preRegistered.length > 0) {
                return preRegistered[0];
            }

            return null;

        } catch (error) {
            logger.error('Error in pattern-based assignment:', error);
            return null;
        }
    }

    async assignDeviceToClient(deviceId, clientId) {
        try {
            await this.deviceManager.updateDevice(deviceId, {
                client_id: clientId
            });

            // Log the assignment
            await this.db.query(`
                INSERT INTO system_logs (level, message, additional_data)
                VALUES ('info', ?, ?)
            `, [
                'Device auto-assigned to client',
                JSON.stringify({ deviceId, clientId, timestamp: new Date() })
            ]);

        } catch (error) {
            logger.error('Error assigning device to client:', error);
            throw error;
        }
    }

    async applyClientProfile(deviceId, clientId) {
        try {
            // Get client's preferred profile
            const clientProfiles = await this.db.query(`
                SELECT cp.* FROM configuration_profiles cp
                JOIN client_profiles clp ON cp.id = clp.profile_id
                WHERE clp.client_id = ? AND cp.is_active = TRUE
                ORDER BY clp.priority DESC
                LIMIT 1
            `, [clientId]);

            if (clientProfiles.length > 0) {
                const profile = clientProfiles[0];
                await this.deviceManager.applyProfile(deviceId, profile);
                logger.info(`Applied profile ${profile.name} to device ${deviceId}`);
            } else {
                // Apply default profile based on device model
                const device = await this.deviceManager.getDeviceById(deviceId);
                if (device && device.model) {
                    const defaultProfiles = await this.db.query(`
                        SELECT * FROM configuration_profiles 
                        WHERE ont_model = ? AND is_active = TRUE
                        ORDER BY created_at DESC
                        LIMIT 1
                    `, [device.model]);

                    if (defaultProfiles.length > 0) {
                        await this.deviceManager.applyProfile(deviceId, defaultProfiles[0]);
                        logger.info(`Applied default profile for model ${device.model} to device ${deviceId}`);
                    }
                }
            }

        } catch (error) {
            logger.error('Error applying client profile:', error);
        }
    }

    async createAssignmentNotification(device) {
        try {
            await this.db.query(`
                INSERT INTO assignment_notifications (
                    device_id, serial_number, model, ip_address, 
                    status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', NOW())
            `, [
                device.id,
                device.serial_number,
                device.model,
                device.ip_address
            ]);

            logger.info(`Created assignment notification for device ${device.serial_number}`);

        } catch (error) {
            logger.error('Error creating assignment notification:', error);
        }
    }

    // Admin methods for managing assignment rules
    async createAssignmentRule(ruleData) {
        try {
            const { name, description, rule_type, rule_config, priority = 5 } = ruleData;
            
            const result = await this.db.query(`
                INSERT INTO assignment_rules (
                    name, description, rule_type, rule_config, priority
                ) VALUES (?, ?, ?, ?, ?)
            `, [
                name,
                description,
                rule_type,
                JSON.stringify(rule_config),
                priority
            ]);

            await this.loadAssignmentRules(); // Reload rules
            
            logger.info(`Created assignment rule: ${name}`);
            return result.insertId;

        } catch (error) {
            logger.error('Error creating assignment rule:', error);
            throw error;
        }
    }

    async updateAssignmentRule(ruleId, updates) {
        try {
            if (updates.rule_config) {
                updates.rule_config = JSON.stringify(updates.rule_config);
            }

            const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
            const values = Object.values(updates);
            values.push(ruleId);

            await this.db.query(
                `UPDATE assignment_rules SET ${fields}, updated_at = NOW() WHERE id = ?`,
                values
            );

            await this.loadAssignmentRules(); // Reload rules
            
            logger.info(`Updated assignment rule: ${ruleId}`);

        } catch (error) {
            logger.error('Error updating assignment rule:', error);
            throw error;
        }
    }

    async deleteAssignmentRule(ruleId) {
        try {
            await this.db.query(
                'UPDATE assignment_rules SET is_active = FALSE WHERE id = ?',
                [ruleId]
            );

            await this.loadAssignmentRules(); // Reload rules
            
            logger.info(`Deleted assignment rule: ${ruleId}`);

        } catch (error) {
            logger.error('Error deleting assignment rule:', error);
            throw error;
        }
    }

    async getAssignmentRules() {
        return this.assignmentRules;
    }

    async getPendingAssignments() {
        try {
            return await this.db.query(`
                SELECT an.*, d.serial_number, d.model, d.ip_address, d.status
                FROM assignment_notifications an
                JOIN devices d ON an.device_id = d.id
                WHERE an.status = 'pending'
                ORDER BY an.created_at DESC
            `);

        } catch (error) {
            logger.error('Error getting pending assignments:', error);
            return [];
        }
    }

    async manualAssignment(deviceId, clientId, userId) {
        try {
            await this.assignDeviceToClient(deviceId, clientId);
            
            // Mark notification as resolved
            await this.db.query(`
                UPDATE assignment_notifications 
                SET status = 'resolved', resolved_by = ?, resolved_at = NOW()
                WHERE device_id = ?
            `, [userId, deviceId]);

            // Apply client profile
            await this.applyClientProfile(deviceId, clientId);

            logger.info(`Manual assignment completed: device ${deviceId} to client ${clientId} by user ${userId}`);

        } catch (error) {
            logger.error('Error in manual assignment:', error);
            throw error;
        }
    }

    async preRegisterDevice(serialNumber, clientId, userId) {
        try {
            await this.db.query(`
                INSERT INTO pre_registered_devices (
                    serial_number, client_id, registered_by, registered_at
                ) VALUES (?, ?, ?, NOW())
                ON DUPLICATE KEY UPDATE
                    client_id = VALUES(client_id),
                    registered_by = VALUES(registered_by),
                    registered_at = VALUES(registered_at),
                    is_active = TRUE
            `, [serialNumber, clientId, userId]);

            logger.info(`Pre-registered device ${serialNumber} for client ${clientId}`);

        } catch (error) {
            logger.error('Error pre-registering device:', error);
            throw error;
        }
    }
}

module.exports = AutoAssignmentService;