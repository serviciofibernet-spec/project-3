const CWMPProcessor = require('./cwmp');
const DeviceManager = require('./deviceManager');
const TaskQueue = require('./taskQueue');
const logger = require('../utils/logger');

class ACSServer {
    constructor() {
        this.cwmp = new CWMPProcessor();
        this.deviceManager = new DeviceManager();
        this.taskQueue = new TaskQueue();
        this.sessions = new Map(); // Store active sessions
    }

    async initialize() {
        await this.deviceManager.initialize();
        await this.taskQueue.initialize();
        logger.info('ACS Server initialized successfully');
    }

    async handleCWMPRequest(req, res) {
        const sessionId = req.headers['cookie'] || this.generateSessionId();
        const clientIP = req.ip || req.connection.remoteAddress;
        
        try {
            // Set CWMP headers
            res.set({
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': '',
                'Set-Cookie': `sessionid=${sessionId}; Path=/acs`
            });

            if (req.method === 'POST') {
                const xmlData = req.body;
                logger.info(`Received CWMP message from ${clientIP}`, { sessionId });

                // Parse CWMP message
                const cwmpMessage = await this.cwmp.parseSOAPMessage(xmlData);
                logger.debug('Parsed CWMP message:', { method: cwmpMessage.method, sessionId });

                // Process the message based on method
                const response = await this.processCWMPMessage(cwmpMessage, sessionId, clientIP);
                
                res.send(response);
            } else if (req.method === 'GET') {
                // Handle empty GET request (session continuation)
                const response = await this.handleEmptyRequest(sessionId);
                res.send(response);
            } else {
                res.status(405).send('Method Not Allowed');
            }

        } catch (error) {
            logger.error('Error handling CWMP request:', { error: error.message, sessionId, clientIP });
            res.status(500).send(this.createSOAPFault('Server', error.message));
        }
    }

    async processCWMPMessage(cwmpMessage, sessionId, clientIP) {
        switch (cwmpMessage.method) {
            case 'Inform':
                return await this.handleInform(cwmpMessage.data, sessionId, clientIP);
            
            case 'GetRPCMethodsResponse':
                return await this.handleGetRPCMethodsResponse(cwmpMessage.data, sessionId);
            
            case 'GetParameterValuesResponse':
                return await this.handleGetParameterValuesResponse(cwmpMessage.data, sessionId);
            
            case 'SetParameterValuesResponse':
                return await this.handleSetParameterValuesResponse(cwmpMessage.data, sessionId);
            
            case 'RebootResponse':
                return await this.handleRebootResponse(cwmpMessage.data, sessionId);
            
            case 'DownloadResponse':
                return await this.handleDownloadResponse(cwmpMessage.data, sessionId);
            
            case 'TransferCompleteResponse':
                return await this.handleTransferCompleteResponse(cwmpMessage.data, sessionId);
            
            default:
                logger.warn(`Unhandled CWMP method: ${cwmpMessage.method}`, { sessionId });
                return this.cwmp.createEmptyResponse();
        }
    }

    async handleInform(informData, sessionId, clientIP) {
        try {
            const parsedInform = this.cwmp.parseInformMessage(informData);
            logger.info('Device Inform received:', { 
                serialNumber: parsedInform.deviceId.serialNumber,
                events: parsedInform.events,
                sessionId 
            });

            // Register or update device
            const device = await this.deviceManager.registerDevice({
                serialNumber: parsedInform.deviceId.serialNumber,
                manufacturer: parsedInform.deviceId.manufacturer,
                oui: parsedInform.deviceId.oui,
                productClass: parsedInform.deviceId.productClass,
                parameters: parsedInform.parameters,
                ipAddress: clientIP,
                lastInform: new Date()
            });

            // Store session information
            this.sessions.set(sessionId, {
                deviceId: device.id,
                serialNumber: parsedInform.deviceId.serialNumber,
                lastActivity: new Date(),
                pendingTasks: []
            });

            // Check for pending tasks
            const pendingTasks = await this.taskQueue.getPendingTasks(device.id);
            if (pendingTasks.length > 0) {
                // Store tasks in session for processing
                this.sessions.get(sessionId).pendingTasks = pendingTasks;
                
                // Process first task
                const firstTask = pendingTasks[0];
                return await this.processTask(firstTask, sessionId);
            }

            // Send InformResponse
            return this.cwmp.createSOAPResponse('InformResponse', { id: sessionId });

        } catch (error) {
            logger.error('Error handling Inform:', error);
            throw error;
        }
    }

    async handleGetParameterValuesResponse(responseData, sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                throw new Error('Session not found');
            }

            const parameters = this.cwmp.parseParameterValuesResponse(responseData);
            
            // Update device parameters in database
            await this.deviceManager.updateDeviceParameters(session.deviceId, parameters);
            
            // Complete current task
            if (session.pendingTasks.length > 0) {
                const currentTask = session.pendingTasks.shift();
                await this.taskQueue.completeTask(currentTask.id, { parameters });
            }

            // Process next task if available
            if (session.pendingTasks.length > 0) {
                const nextTask = session.pendingTasks[0];
                return await this.processTask(nextTask, sessionId);
            }

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling GetParameterValuesResponse:', error);
            throw error;
        }
    }

    async handleSetParameterValuesResponse(responseData, sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                throw new Error('Session not found');
            }

            const status = responseData.Status || '0';
            
            // Complete current task
            if (session.pendingTasks.length > 0) {
                const currentTask = session.pendingTasks.shift();
                await this.taskQueue.completeTask(currentTask.id, { 
                    status: status === '0' ? 'completed' : 'failed',
                    response: responseData 
                });
            }

            // Process next task if available
            if (session.pendingTasks.length > 0) {
                const nextTask = session.pendingTasks[0];
                return await this.processTask(nextTask, sessionId);
            }

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling SetParameterValuesResponse:', error);
            throw error;
        }
    }

    async handleRebootResponse(responseData, sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                throw new Error('Session not found');
            }

            // Complete reboot task
            if (session.pendingTasks.length > 0) {
                const currentTask = session.pendingTasks.shift();
                await this.taskQueue.completeTask(currentTask.id, { response: responseData });
            }

            // Update device status
            await this.deviceManager.updateDeviceStatus(session.deviceId, 'rebooting');

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling RebootResponse:', error);
            throw error;
        }
    }

    async handleDownloadResponse(responseData, sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                throw new Error('Session not found');
            }

            const status = responseData.Status || '0';
            const startTime = responseData.StartTime;
            const completeTime = responseData.CompleteTime;

            // Update task status
            if (session.pendingTasks.length > 0) {
                const currentTask = session.pendingTasks.shift();
                await this.taskQueue.updateTask(currentTask.id, {
                    status: status === '0' ? 'in_progress' : 'failed',
                    started_at: startTime,
                    completed_at: completeTime
                });
            }

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling DownloadResponse:', error);
            throw error;
        }
    }

    async handleTransferCompleteResponse(responseData, sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                throw new Error('Session not found');
            }

            const faultCode = responseData.FaultStruct ? responseData.FaultStruct.FaultCode : '0';
            const isSuccess = faultCode === '0';

            // Find and complete the download task
            const downloadTasks = await this.taskQueue.getTasksByType(session.deviceId, 'firmware_upgrade');
            for (const task of downloadTasks) {
                if (task.status === 'in_progress') {
                    await this.taskQueue.completeTask(task.id, {
                        status: isSuccess ? 'completed' : 'failed',
                        response: responseData
                    });
                    break;
                }
            }

            // If firmware upgrade was successful, update device firmware version
            if (isSuccess && responseData.CommandKey && responseData.CommandKey.includes('firmware')) {
                // Extract firmware version from task parameters if available
                // This would be implementation specific
            }

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling TransferCompleteResponse:', error);
            throw error;
        }
    }

    async handleEmptyRequest(sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (!session) {
                return this.cwmp.createEmptyResponse();
            }

            // Check for pending tasks
            if (session.pendingTasks.length > 0) {
                const nextTask = session.pendingTasks[0];
                return await this.processTask(nextTask, sessionId);
            }

            // Check for new tasks from queue
            const newTasks = await this.taskQueue.getPendingTasks(session.deviceId);
            if (newTasks.length > 0) {
                session.pendingTasks = newTasks;
                const firstTask = newTasks[0];
                return await this.processTask(firstTask, sessionId);
            }

            return this.cwmp.createEmptyResponse();

        } catch (error) {
            logger.error('Error handling empty request:', error);
            return this.cwmp.createEmptyResponse();
        }
    }

    async processTask(task, sessionId) {
        try {
            await this.taskQueue.startTask(task.id);

            switch (task.task_type) {
                case 'get_parameters':
                    return this.cwmp.createSOAPResponse('GetParameterValues', {
                        parameters: task.parameters.parameterNames || [],
                        id: sessionId
                    });

                case 'set_parameters':
                    return this.cwmp.createSOAPResponse('SetParameterValues', {
                        parameters: task.parameters.parameters || [],
                        parameterKey: task.parameters.parameterKey,
                        id: sessionId
                    });

                case 'reboot':
                    return this.cwmp.createSOAPResponse('Reboot', {
                        commandKey: `reboot_${task.id}`,
                        id: sessionId
                    });

                case 'factory_reset':
                    return this.cwmp.createSOAPResponse('FactoryReset', {
                        id: sessionId
                    });

                case 'firmware_upgrade':
                    return this.cwmp.createSOAPResponse('Download', {
                        commandKey: `firmware_${task.id}`,
                        fileType: '1 Firmware Upgrade Image',
                        url: task.parameters.url,
                        username: task.parameters.username || '',
                        password: task.parameters.password || '',
                        fileSize: task.parameters.fileSize || 0,
                        id: sessionId
                    });

                default:
                    throw new Error(`Unsupported task type: ${task.task_type}`);
            }

        } catch (error) {
            logger.error('Error processing task:', { taskId: task.id, error: error.message });
            await this.taskQueue.failTask(task.id, error.message);
            throw error;
        }
    }

    createSOAPFault(faultCode, faultString) {
        return `<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>${faultCode}</faultcode>
            <faultstring>${faultString}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>`;
    }

    generateSessionId() {
        return 'acs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Clean up expired sessions
    cleanupSessions() {
        const now = new Date();
        const timeout = 5 * 60 * 1000; // 5 minutes

        for (const [sessionId, session] of this.sessions.entries()) {
            if (now - session.lastActivity > timeout) {
                this.sessions.delete(sessionId);
                logger.debug(`Cleaned up expired session: ${sessionId}`);
            }
        }
    }
}

module.exports = ACSServer;