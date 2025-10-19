const express = require('express');
const DeviceController = require('../controllers/deviceController');
const auth = require('../middleware/auth');

const router = express.Router();
const deviceController = new DeviceController();

// Initialize controller
deviceController.initialize().catch(console.error);

// Get all devices
router.get('/', auth, async (req, res) => {
    await deviceController.getAllDevices(req, res);
});

// Get device by ID
router.get('/:id', auth, async (req, res) => {
    await deviceController.getDeviceById(req, res);
});

// Update WiFi settings
router.put('/:id/wifi', auth, async (req, res) => {
    await deviceController.updateWiFiSettings(req, res);
});

// Update network settings
router.put('/:id/network', auth, async (req, res) => {
    await deviceController.updateNetworkSettings(req, res);
});

// Reboot device
router.post('/:id/reboot', auth, async (req, res) => {
    await deviceController.rebootDevice(req, res);
});

// Factory reset device
router.post('/:id/factory-reset', auth, async (req, res) => {
    await deviceController.factoryResetDevice(req, res);
});

// Upgrade firmware
router.post('/:id/firmware-upgrade', auth, async (req, res) => {
    await deviceController.upgradeFirmware(req, res);
});

// Get device parameters
router.post('/:id/parameters', auth, async (req, res) => {
    await deviceController.getDeviceParameters(req, res);
});

// Get monitoring data
router.get('/:id/monitoring', auth, async (req, res) => {
    await deviceController.getMonitoringData(req, res);
});

// Get connected devices
router.get('/:id/connected-devices', auth, async (req, res) => {
    await deviceController.getConnectedDevices(req, res);
});

// Get task status
router.get('/tasks/:taskId', auth, async (req, res) => {
    await deviceController.getTaskStatus(req, res);
});

module.exports = router;