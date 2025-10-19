const express = require('express');
const ACSServer = require('../tr069/acs');
const logger = require('../utils/logger');

const router = express.Router();
const acsServer = new ACSServer();

// Initialize ACS server
acsServer.initialize().catch(error => {
    logger.error('Failed to initialize ACS server:', error);
});

// TR069 CWMP endpoint
router.all('/', async (req, res) => {
    await acsServer.handleCWMPRequest(req, res);
});

// Clean up expired sessions every 5 minutes
setInterval(() => {
    acsServer.cleanupSessions();
}, 5 * 60 * 1000);

module.exports = router;