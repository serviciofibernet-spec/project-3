const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../database/connection');
const logger = require('../utils/logger');

class AuthController {
    constructor() {
        this.db = db;
    }

    async initialize() {
        await this.db.initialize();
    }

    // User login
    async login(req, res) {
        try {
            const { username, password } = req.body;

            if (!username || !password) {
                return res.status(400).json({
                    success: false,
                    error: 'Username and password are required'
                });
            }

            // Get user from database
            const users = await this.db.query(
                'SELECT * FROM users WHERE username = ? AND is_active = TRUE',
                [username]
            );

            if (users.length === 0) {
                return res.status(401).json({
                    success: false,
                    error: 'Invalid credentials'
                });
            }

            const user = users[0];

            // Verify password
            const isValidPassword = await bcrypt.compare(password, user.password_hash);
            if (!isValidPassword) {
                return res.status(401).json({
                    success: false,
                    error: 'Invalid credentials'
                });
            }

            // Generate JWT token
            const token = jwt.sign(
                { 
                    id: user.id, 
                    username: user.username, 
                    role: user.role 
                },
                process.env.JWT_SECRET,
                { expiresIn: '24h' }
            );

            // Log successful login
            logger.info(`User ${username} logged in successfully`);

            res.json({
                success: true,
                data: {
                    token,
                    user: {
                        id: user.id,
                        username: user.username,
                        email: user.email,
                        role: user.role
                    }
                }
            });

        } catch (error) {
            logger.error('Login error:', error);
            res.status(500).json({
                success: false,
                error: 'Login failed'
            });
        }
    }

    // User registration (admin only)
    async register(req, res) {
        try {
            const { username, email, password, role = 'client' } = req.body;

            if (!username || !email || !password) {
                return res.status(400).json({
                    success: false,
                    error: 'Username, email, and password are required'
                });
            }

            // Check if user already exists
            const existingUsers = await this.db.query(
                'SELECT id FROM users WHERE username = ? OR email = ?',
                [username, email]
            );

            if (existingUsers.length > 0) {
                return res.status(400).json({
                    success: false,
                    error: 'Username or email already exists'
                });
            }

            // Hash password
            const saltRounds = parseInt(process.env.BCRYPT_ROUNDS) || 12;
            const passwordHash = await bcrypt.hash(password, saltRounds);

            // Create user
            const result = await this.db.query(`
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            `, [username, email, passwordHash, role]);

            logger.info(`New user registered: ${username} (${role})`);

            res.status(201).json({
                success: true,
                data: {
                    id: result.insertId,
                    username,
                    email,
                    role
                }
            });

        } catch (error) {
            logger.error('Registration error:', error);
            res.status(500).json({
                success: false,
                error: 'Registration failed'
            });
        }
    }

    // Change password
    async changePassword(req, res) {
        try {
            const { currentPassword, newPassword } = req.body;
            const userId = req.user.id;

            if (!currentPassword || !newPassword) {
                return res.status(400).json({
                    success: false,
                    error: 'Current password and new password are required'
                });
            }

            if (newPassword.length < 8) {
                return res.status(400).json({
                    success: false,
                    error: 'New password must be at least 8 characters long'
                });
            }

            // Get current user
            const users = await this.db.query(
                'SELECT password_hash FROM users WHERE id = ?',
                [userId]
            );

            if (users.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'User not found'
                });
            }

            // Verify current password
            const isValidPassword = await bcrypt.compare(currentPassword, users[0].password_hash);
            if (!isValidPassword) {
                return res.status(401).json({
                    success: false,
                    error: 'Current password is incorrect'
                });
            }

            // Hash new password
            const saltRounds = parseInt(process.env.BCRYPT_ROUNDS) || 12;
            const newPasswordHash = await bcrypt.hash(newPassword, saltRounds);

            // Update password
            await this.db.query(
                'UPDATE users SET password_hash = ?, updated_at = NOW() WHERE id = ?',
                [newPasswordHash, userId]
            );

            logger.info(`User ${req.user.username} changed password`);

            res.json({
                success: true,
                message: 'Password changed successfully'
            });

        } catch (error) {
            logger.error('Change password error:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to change password'
            });
        }
    }

    // Get current user profile
    async getProfile(req, res) {
        try {
            const userId = req.user.id;

            const users = await this.db.query(`
                SELECT u.id, u.username, u.email, u.role, u.created_at, c.id as client_id, c.name as client_name
                FROM users u
                LEFT JOIN clients c ON u.id = c.user_id
                WHERE u.id = ?
            `, [userId]);

            if (users.length === 0) {
                return res.status(404).json({
                    success: false,
                    error: 'User not found'
                });
            }

            const user = users[0];

            res.json({
                success: true,
                data: user
            });

        } catch (error) {
            logger.error('Get profile error:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to get profile'
            });
        }
    }

    // Verify token
    async verifyToken(req, res) {
        try {
            // If we reach here, the token is valid (middleware already verified it)
            res.json({
                success: true,
                data: {
                    user: req.user
                }
            });

        } catch (error) {
            logger.error('Token verification error:', error);
            res.status(500).json({
                success: false,
                error: 'Token verification failed'
            });
        }
    }
}

module.exports = AuthController;