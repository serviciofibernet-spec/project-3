const express = require('express');
const AuthController = require('../controllers/authController');
const auth = require('../middleware/auth');

const router = express.Router();
const authController = new AuthController();

// Initialize controller
authController.initialize().catch(console.error);

// Login
router.post('/login', async (req, res) => {
    await authController.login(req, res);
});

// Register (admin only)
router.post('/register', auth, async (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({
            success: false,
            error: 'Access denied. Admin role required.'
        });
    }
    await authController.register(req, res);
});

// Change password
router.post('/change-password', auth, async (req, res) => {
    await authController.changePassword(req, res);
});

// Get profile
router.get('/profile', auth, async (req, res) => {
    await authController.getProfile(req, res);
});

// Verify token
router.get('/verify', auth, async (req, res) => {
    await authController.verifyToken(req, res);
});

module.exports = router;