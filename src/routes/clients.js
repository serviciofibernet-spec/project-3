const express = require('express');
const ClientController = require('../controllers/clientController');
const auth = require('../middleware/auth');
const clientAuth = require('../middleware/clientAuth');

const router = express.Router();
const clientController = new ClientController();

// Initialize controller
clientController.initialize().catch(console.error);

// Admin routes (require admin authentication)
router.get('/', auth, async (req, res) => {
    await clientController.getAllClients(req, res);
});

router.post('/', auth, async (req, res) => {
    await clientController.createClient(req, res);
});

router.get('/:id', auth, async (req, res) => {
    await clientController.getClientById(req, res);
});

router.put('/:id', auth, async (req, res) => {
    await clientController.updateClient(req, res);
});

router.post('/:id/assign-device', auth, async (req, res) => {
    await clientController.assignDevice(req, res);
});

router.post('/:id/unassign-device', auth, async (req, res) => {
    await clientController.unassignDevice(req, res);
});

// Client self-service routes (require client authentication)
router.get('/:id/dashboard', clientAuth, async (req, res) => {
    await clientController.getClientDashboard(req, res);
});

router.put('/:id/wifi', clientAuth, async (req, res) => {
    await clientController.updateClientWiFi(req, res);
});

router.get('/:id/devices/:deviceId/status', clientAuth, async (req, res) => {
    await clientController.getClientDeviceStatus(req, res);
});

module.exports = router;