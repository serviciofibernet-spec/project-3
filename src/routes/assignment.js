const express = require('express');
const AutoAssignmentService = require('../services/autoAssignmentService');
const auth = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();
const autoAssignmentService = new AutoAssignmentService();

// Initialize service
autoAssignmentService.initialize().catch(console.error);

// Get all assignment rules
router.get('/rules', auth, async (req, res) => {
    try {
        const rules = await autoAssignmentService.getAssignmentRules();
        res.json({
            success: true,
            data: rules
        });
    } catch (error) {
        logger.error('Error getting assignment rules:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve assignment rules'
        });
    }
});

// Create assignment rule
router.post('/rules', auth, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Admin role required'
            });
        }

        const ruleId = await autoAssignmentService.createAssignmentRule(req.body);
        res.status(201).json({
            success: true,
            data: { id: ruleId }
        });
    } catch (error) {
        logger.error('Error creating assignment rule:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to create assignment rule'
        });
    }
});

// Update assignment rule
router.put('/rules/:id', auth, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Admin role required'
            });
        }

        const { id } = req.params;
        await autoAssignmentService.updateAssignmentRule(id, req.body);
        res.json({
            success: true,
            message: 'Assignment rule updated successfully'
        });
    } catch (error) {
        logger.error('Error updating assignment rule:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to update assignment rule'
        });
    }
});

// Delete assignment rule
router.delete('/rules/:id', auth, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Admin role required'
            });
        }

        const { id } = req.params;
        await autoAssignmentService.deleteAssignmentRule(id);
        res.json({
            success: true,
            message: 'Assignment rule deleted successfully'
        });
    } catch (error) {
        logger.error('Error deleting assignment rule:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete assignment rule'
        });
    }
});

// Get pending assignments
router.get('/pending', auth, async (req, res) => {
    try {
        const pendingAssignments = await autoAssignmentService.getPendingAssignments();
        res.json({
            success: true,
            data: pendingAssignments
        });
    } catch (error) {
        logger.error('Error getting pending assignments:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to retrieve pending assignments'
        });
    }
});

// Manual assignment
router.post('/manual', auth, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Admin role required'
            });
        }

        const { deviceId, clientId } = req.body;
        
        if (!deviceId || !clientId) {
            return res.status(400).json({
                success: false,
                error: 'Device ID and Client ID are required'
            });
        }

        await autoAssignmentService.manualAssignment(deviceId, clientId, req.user.id);
        res.json({
            success: true,
            message: 'Device assigned successfully'
        });
    } catch (error) {
        logger.error('Error in manual assignment:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to assign device'
        });
    }
});

// Pre-register device
router.post('/pre-register', auth, async (req, res) => {
    try {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Admin role required'
            });
        }

        const { serialNumber, clientId } = req.body;
        
        if (!serialNumber || !clientId) {
            return res.status(400).json({
                success: false,
                error: 'Serial number and Client ID are required'
            });
        }

        await autoAssignmentService.preRegisterDevice(serialNumber, clientId, req.user.id);
        res.json({
            success: true,
            message: 'Device pre-registered successfully'
        });
    } catch (error) {
        logger.error('Error pre-registering device:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to pre-register device'
        });
    }
});

// Process device for auto-assignment (internal endpoint)
router.post('/process-device', async (req, res) => {
    try {
        // This endpoint should be called internally when a new device connects
        const device = req.body;
        await autoAssignmentService.processNewDevice(device);
        res.json({
            success: true,
            message: 'Device processed for auto-assignment'
        });
    } catch (error) {
        logger.error('Error processing device for auto-assignment:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to process device'
        });
    }
});

module.exports = router;