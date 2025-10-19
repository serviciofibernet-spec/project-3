const express = require('express');
const db = require('../database/connection');
const auth = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// Get all configuration profiles
router.get('/', auth, async (req, res) => {
    try {
        const profiles = await db.query(`
            SELECT p.*, COUNT(d.id) as device_count
            FROM configuration_profiles p
            LEFT JOIN devices d ON p.id = d.profile_id
            WHERE p.is_active = TRUE
            GROUP BY p.id
            ORDER BY p.name
        `);

        res.json({
            success: true,
            data: profiles.map(profile => ({
                ...profile,
                default_config: JSON.parse(profile.default_config || '{}'),
                wifi_config: JSON.parse(profile.wifi_config || '{}'),
                network_config: JSON.parse(profile.network_config || '{}')
            }))
        });

    } catch (error) {
        logger.error('Error getting profiles:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve profiles'
        });
    }
});

// Get profile by ID
router.get('/:id', auth, async (req, res) => {
    try {
        const { id } = req.params;

        const profiles = await db.query(
            'SELECT * FROM configuration_profiles WHERE id = ? AND is_active = TRUE',
            [id]
        );

        if (profiles.length === 0) {
            return res.status(404).json({
                success: false,
                error: 'Profile not found'
            });
        }

        const profile = profiles[0];
        
        res.json({
            success: true,
            data: {
                ...profile,
                default_config: JSON.parse(profile.default_config || '{}'),
                wifi_config: JSON.parse(profile.wifi_config || '{}'),
                network_config: JSON.parse(profile.network_config || '{}')
            }
        });

    } catch (error) {
        logger.error('Error getting profile by ID:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve profile'
        });
    }
});

// Create new profile
router.post('/', auth, async (req, res) => {
    try {
        const { name, description, ont_model, default_config, wifi_config, network_config } = req.body;

        if (!name || !ont_model) {
            return res.status(400).json({
                success: false,
                error: 'Name and ONT model are required'
            });
        }

        const result = await db.query(`
            INSERT INTO configuration_profiles 
            (name, description, ont_model, default_config, wifi_config, network_config)
            VALUES (?, ?, ?, ?, ?, ?)
        `, [
            name,
            description,
            ont_model,
            JSON.stringify(default_config || {}),
            JSON.stringify(wifi_config || {}),
            JSON.stringify(network_config || {})
        ]);

        logger.info(`New profile created: ${name} for ${ont_model}`);

        res.status(201).json({
            success: true,
            data: {
                id: result.insertId,
                name,
                description,
                ont_model,
                default_config,
                wifi_config,
                network_config
            }
        });

    } catch (error) {
        logger.error('Error creating profile:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to create profile'
        });
    }
});

// Update profile
router.put('/:id', auth, async (req, res) => {
    try {
        const { id } = req.params;
        const updates = req.body;

        // Remove fields that shouldn't be updated directly
        delete updates.id;
        delete updates.created_at;
        delete updates.updated_at;

        // Convert config objects to JSON strings
        if (updates.default_config) {
            updates.default_config = JSON.stringify(updates.default_config);
        }
        if (updates.wifi_config) {
            updates.wifi_config = JSON.stringify(updates.wifi_config);
        }
        if (updates.network_config) {
            updates.network_config = JSON.stringify(updates.network_config);
        }

        if (Object.keys(updates).length === 0) {
            return res.status(400).json({
                success: false,
                error: 'No valid fields to update'
            });
        }

        // Check if profile exists
        const existingProfiles = await db.query(
            'SELECT id FROM configuration_profiles WHERE id = ? AND is_active = TRUE',
            [id]
        );

        if (existingProfiles.length === 0) {
            return res.status(404).json({
                success: false,
                error: 'Profile not found'
            });
        }

        // Update profile
        const fields = Object.keys(updates).map(key => `${key} = ?`).join(', ');
        const values = Object.values(updates);
        values.push(id);

        await db.query(
            `UPDATE configuration_profiles SET ${fields}, updated_at = NOW() WHERE id = ?`,
            values
        );

        logger.info(`Profile ${id} updated`);

        res.json({
            success: true,
            message: 'Profile updated successfully'
        });

    } catch (error) {
        logger.error('Error updating profile:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to update profile'
        });
    }
});

// Delete profile (soft delete)
router.delete('/:id', auth, async (req, res) => {
    try {
        const { id } = req.params;

        // Check if profile exists
        const existingProfiles = await db.query(
            'SELECT id, name FROM configuration_profiles WHERE id = ? AND is_active = TRUE',
            [id]
        );

        if (existingProfiles.length === 0) {
            return res.status(404).json({
                success: false,
                error: 'Profile not found'
            });
        }

        // Check if profile is in use
        const devicesUsingProfile = await db.query(
            'SELECT COUNT(*) as count FROM devices WHERE profile_id = ?',
            [id]
        );

        if (devicesUsingProfile[0].count > 0) {
            return res.status(400).json({
                success: false,
                error: 'Cannot delete profile that is currently in use by devices'
            });
        }

        // Soft delete profile
        await db.query(
            'UPDATE configuration_profiles SET is_active = FALSE, updated_at = NOW() WHERE id = ?',
            [id]
        );

        logger.info(`Profile ${id} (${existingProfiles[0].name}) deleted`);

        res.json({
            success: true,
            message: 'Profile deleted successfully'
        });

    } catch (error) {
        logger.error('Error deleting profile:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete profile'
        });
    }
});

// Apply profile to device
router.post('/:id/apply/:deviceId', auth, async (req, res) => {
    try {
        const { id, deviceId } = req.params;

        // Get profile
        const profiles = await db.query(
            'SELECT * FROM configuration_profiles WHERE id = ? AND is_active = TRUE',
            [id]
        );

        if (profiles.length === 0) {
            return res.status(404).json({
                success: false,
                error: 'Profile not found'
            });
        }

        // Get device
        const DeviceManager = require('../tr069/deviceManager');
        const deviceManager = new DeviceManager();
        await deviceManager.initialize();

        const device = await deviceManager.getDeviceById(deviceId);
        if (!device) {
            return res.status(404).json({
                success: false,
                error: 'Device not found'
            });
        }

        const profile = profiles[0];

        // Update device profile
        await deviceManager.updateDevice(deviceId, {
            profile_id: id
        });

        // Apply profile configuration
        await deviceManager.applyProfile(deviceId, profile);

        logger.info(`Profile ${profile.name} applied to device ${device.serial_number}`);

        res.json({
            success: true,
            message: 'Profile applied successfully'
        });

    } catch (error) {
        logger.error('Error applying profile:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to apply profile'
        });
    }
});

module.exports = router;