const jwt = require('jsonwebtoken');
const db = require('../database/connection');
const logger = require('../utils/logger');

const auth = async (req, res, next) => {
    try {
        const token = req.header('Authorization')?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({
                success: false,
                error: 'Access denied. No token provided.'
            });
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // Get user from database
        const users = await db.query(
            'SELECT id, username, email, role, is_active FROM users WHERE id = ?',
            [decoded.id]
        );

        if (users.length === 0 || !users[0].is_active) {
            return res.status(401).json({
                success: false,
                error: 'Invalid token.'
            });
        }

        req.user = users[0];
        next();

    } catch (error) {
        logger.error('Authentication error:', error);
        res.status(401).json({
            success: false,
            error: 'Invalid token.'
        });
    }
};

const adminAuth = async (req, res, next) => {
    await auth(req, res, () => {
        if (req.user.role !== 'admin') {
            return res.status(403).json({
                success: false,
                error: 'Access denied. Admin role required.'
            });
        }
        next();
    });
};

module.exports = auth;
module.exports.adminAuth = adminAuth;