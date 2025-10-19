const jwt = require('jsonwebtoken');
const db = require('../database/connection');
const logger = require('../utils/logger');

const clientAuth = async (req, res, next) => {
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
            'SELECT u.id, u.username, u.email, u.role, u.is_active, c.id as client_id FROM users u LEFT JOIN clients c ON u.id = c.user_id WHERE u.id = ?',
            [decoded.id]
        );

        if (users.length === 0 || !users[0].is_active) {
            return res.status(401).json({
                success: false,
                error: 'Invalid token.'
            });
        }

        const user = users[0];

        // Check if user is admin or the client owner
        const clientId = parseInt(req.params.id);
        
        if (user.role === 'admin' || user.client_id === clientId) {
            req.user = user;
            next();
        } else {
            return res.status(403).json({
                success: false,
                error: 'Access denied. You can only access your own data.'
            });
        }

    } catch (error) {
        logger.error('Client authentication error:', error);
        res.status(401).json({
            success: false,
            error: 'Invalid token.'
        });
    }
};

module.exports = clientAuth;