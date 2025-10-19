require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');

const logger = require('./utils/logger');
const db = require('./database/connection');

// Import routes
const acsRoutes = require('./routes/acs');
const authRoutes = require('./routes/auth');
const deviceRoutes = require('./routes/devices');
const clientRoutes = require('./routes/clients');
const profileRoutes = require('./routes/profiles');
const assignmentRoutes = require('./routes/assignment');

const app = express();
const PORT = process.env.PORT || 7547;

// Security middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            scriptSrc: ["'self'", "https://cdn.jsdelivr.net"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: (process.env.RATE_LIMIT_WINDOW || 15) * 60 * 1000, // 15 minutes
    max: process.env.RATE_LIMIT_MAX || 100, // limit each IP to 100 requests per windowMs
    message: {
        success: false,
        error: 'Too many requests from this IP, please try again later.'
    }
});

// Apply rate limiting to all routes except ACS
app.use('/api', limiter);

// CORS configuration
app.use(cors({
    origin: process.env.NODE_ENV === 'production' 
        ? ['https://yourdomain.com'] 
        : ['http://localhost:3000', 'http://localhost:8080'],
    credentials: true
}));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Raw body parser for TR069 CWMP (XML)
app.use('/acs', express.raw({ type: 'text/xml', limit: '1mb' }));
app.use('/acs', (req, res, next) => {
    if (req.body && Buffer.isBuffer(req.body)) {
        req.body = req.body.toString();
    }
    next();
});

// Logging middleware
app.use((req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
        const duration = Date.now() - start;
        logger.info(`${req.method} ${req.originalUrl} - ${res.statusCode} - ${duration}ms`, {
            method: req.method,
            url: req.originalUrl,
            status: res.statusCode,
            duration,
            ip: req.ip,
            userAgent: req.get('User-Agent')
        });
    });
    
    next();
});

// Serve static files
app.use(express.static(path.join(__dirname, '../public')));

// API Routes
app.use('/acs', acsRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/devices', deviceRoutes);
app.use('/api/clients', clientRoutes);
app.use('/api/profiles', profileRoutes);
app.use('/api/assignment', assignmentRoutes);

// Health check endpoint
app.get('/api/health', async (req, res) => {
    try {
        // Check database connection
        await db.query('SELECT 1');
        
        res.json({
            success: true,
            status: 'healthy',
            timestamp: new Date().toISOString(),
            version: require('../package.json').version
        });
    } catch (error) {
        logger.error('Health check failed:', error);
        res.status(503).json({
            success: false,
            status: 'unhealthy',
            error: 'Database connection failed'
        });
    }
});

// API documentation endpoint
app.get('/api/docs', (req, res) => {
    res.json({
        success: true,
        endpoints: {
            auth: {
                'POST /api/auth/login': 'User login',
                'POST /api/auth/register': 'User registration (admin only)',
                'POST /api/auth/change-password': 'Change password',
                'GET /api/auth/profile': 'Get user profile',
                'GET /api/auth/verify': 'Verify token'
            },
            devices: {
                'GET /api/devices': 'Get all devices',
                'GET /api/devices/:id': 'Get device by ID',
                'PUT /api/devices/:id/wifi': 'Update WiFi settings',
                'PUT /api/devices/:id/network': 'Update network settings',
                'POST /api/devices/:id/reboot': 'Reboot device',
                'POST /api/devices/:id/factory-reset': 'Factory reset device',
                'POST /api/devices/:id/firmware-upgrade': 'Upgrade firmware',
                'POST /api/devices/:id/parameters': 'Get device parameters',
                'GET /api/devices/:id/monitoring': 'Get monitoring data',
                'GET /api/devices/:id/connected-devices': 'Get connected devices'
            },
            clients: {
                'GET /api/clients': 'Get all clients (admin)',
                'POST /api/clients': 'Create client (admin)',
                'GET /api/clients/:id': 'Get client by ID',
                'PUT /api/clients/:id': 'Update client',
                'GET /api/clients/:id/dashboard': 'Client dashboard',
                'PUT /api/clients/:id/wifi': 'Client update WiFi',
                'POST /api/clients/:id/assign-device': 'Assign device to client',
                'POST /api/clients/:id/unassign-device': 'Unassign device from client'
            },
            profiles: {
                'GET /api/profiles': 'Get all profiles',
                'POST /api/profiles': 'Create profile',
                'GET /api/profiles/:id': 'Get profile by ID',
                'PUT /api/profiles/:id': 'Update profile',
                'DELETE /api/profiles/:id': 'Delete profile',
                'POST /api/profiles/:id/apply/:deviceId': 'Apply profile to device'
            },
            tr069: {
                'POST /acs': 'TR069 CWMP endpoint'
            }
        }
    });
});

// Serve admin panel
app.get('/admin*', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/admin.html'));
});

// Serve client portal
app.get('/client*', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/client.html'));
});

// Default route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    logger.error('Unhandled error:', err);
    
    res.status(err.status || 500).json({
        success: false,
        error: process.env.NODE_ENV === 'production' 
            ? 'Internal server error' 
            : err.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found'
    });
});

// Initialize database and start server
async function startServer() {
    try {
        await db.initialize();
        logger.info('Database connected successfully');
        
        app.listen(PORT, () => {
            logger.info(`TR069 ACS Server running on port ${PORT}`);
            logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
            logger.info(`ACS URL: http://localhost:${PORT}/acs`);
            logger.info(`Admin Panel: http://localhost:${PORT}/admin`);
            logger.info(`Client Portal: http://localhost:${PORT}/client`);
            logger.info(`API Documentation: http://localhost:${PORT}/api/docs`);
        });
        
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    logger.info('SIGTERM received, shutting down gracefully');
    await db.close();
    process.exit(0);
});

process.on('SIGINT', async () => {
    logger.info('SIGINT received, shutting down gracefully');
    await db.close();
    process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    logger.error('Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

startServer();