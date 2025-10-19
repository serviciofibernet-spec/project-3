const xml2js = require('xml2js');
const logger = require('../utils/logger');

class CWMPProcessor {
    constructor() {
        this.parser = new xml2js.Parser({ 
            explicitArray: false,
            ignoreAttrs: false,
            mergeAttrs: true
        });
        this.builder = new xml2js.Builder({
            rootName: 'soap:Envelope',
            xmldec: { version: '1.0', encoding: 'UTF-8' },
            renderOpts: { pretty: true }
        });
    }

    async parseSOAPMessage(xmlData) {
        try {
            const result = await this.parser.parseStringPromise(xmlData);
            return this.extractCWMPMessage(result);
        } catch (error) {
            logger.error('Failed to parse SOAP message:', error);
            throw new Error('Invalid SOAP message format');
        }
    }

    extractCWMPMessage(soapEnvelope) {
        const body = soapEnvelope['soap:Envelope']['soap:Body'] || 
                    soapEnvelope['soapenv:Envelope']['soapenv:Body'] ||
                    soapEnvelope.Envelope.Body;

        if (!body) {
            throw new Error('No SOAP body found');
        }

        // Extract CWMP method and parameters
        const methods = Object.keys(body).filter(key => 
            key.includes('Inform') || 
            key.includes('GetRPCMethodsResponse') ||
            key.includes('GetParameterValuesResponse') ||
            key.includes('SetParameterValuesResponse') ||
            key.includes('RebootResponse') ||
            key.includes('FactoryResetResponse') ||
            key.includes('DownloadResponse') ||
            key.includes('TransferCompleteResponse')
        );

        if (methods.length === 0) {
            throw new Error('No recognized CWMP method found');
        }

        const method = methods[0];
        const methodName = method.replace('Response', '');
        
        return {
            method: methodName,
            data: body[method],
            headers: soapEnvelope['soap:Envelope']['soap:Header'] || {}
        };
    }

    createSOAPResponse(cwmpMethod, data = {}) {
        const soapEnvelope = {
            '$': {
                'xmlns:soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xmlns:cwmp': 'urn:dslforum-org:cwmp-1-0'
            },
            'soap:Header': {
                'cwmp:ID': {
                    '$': { 'soap:mustUnderstand': '1' },
                    '_': data.id || this.generateMessageId()
                }
            },
            'soap:Body': {}
        };

        switch (cwmpMethod) {
            case 'InformResponse':
                soapEnvelope['soap:Body']['cwmp:InformResponse'] = {
                    MaxEnvelopes: 1
                };
                break;

            case 'GetParameterValues':
                soapEnvelope['soap:Body']['cwmp:GetParameterValues'] = {
                    ParameterNames: {
                        'soap:arrayType': `xsd:string[${data.parameters.length}]`,
                        string: data.parameters
                    }
                };
                break;

            case 'SetParameterValues':
                soapEnvelope['soap:Body']['cwmp:SetParameterValues'] = {
                    ParameterList: {
                        'soap:arrayType': `cwmp:ParameterValueStruct[${data.parameters.length}]`,
                        ParameterValueStruct: data.parameters.map(param => ({
                            Name: param.name,
                            Value: {
                                '$': { 'xsi:type': param.type || 'xsd:string' },
                                '_': param.value
                            }
                        }))
                    },
                    ParameterKey: data.parameterKey || ''
                };
                break;

            case 'Reboot':
                soapEnvelope['soap:Body']['cwmp:Reboot'] = {
                    CommandKey: data.commandKey || 'reboot_' + Date.now()
                };
                break;

            case 'FactoryReset':
                soapEnvelope['soap:Body']['cwmp:FactoryReset'] = {};
                break;

            case 'Download':
                soapEnvelope['soap:Body']['cwmp:Download'] = {
                    CommandKey: data.commandKey || 'download_' + Date.now(),
                    FileType: data.fileType || '1 Firmware Upgrade Image',
                    URL: data.url,
                    Username: data.username || '',
                    Password: data.password || '',
                    FileSize: data.fileSize || 0,
                    TargetFileName: data.targetFileName || '',
                    DelaySeconds: data.delaySeconds || 0,
                    SuccessURL: data.successURL || '',
                    FailureURL: data.failureURL || ''
                };
                break;

            case 'GetRPCMethods':
                soapEnvelope['soap:Body']['cwmp:GetRPCMethods'] = {};
                break;

            default:
                throw new Error(`Unsupported CWMP method: ${cwmpMethod}`);
        }

        return this.builder.buildObject(soapEnvelope);
    }

    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    parseInformMessage(informData) {
        const deviceId = informData.DeviceId || {};
        const events = informData.Event ? (Array.isArray(informData.Event.EventStruct) ? 
            informData.Event.EventStruct : [informData.Event.EventStruct]) : [];
        
        const parameters = {};
        if (informData.ParameterList && informData.ParameterList.ParameterValueStruct) {
            const paramList = Array.isArray(informData.ParameterList.ParameterValueStruct) ?
                informData.ParameterList.ParameterValueStruct : [informData.ParameterList.ParameterValueStruct];
            
            paramList.forEach(param => {
                if (param.Name && param.Value !== undefined) {
                    parameters[param.Name] = param.Value._ || param.Value;
                }
            });
        }

        return {
            deviceId: {
                manufacturer: deviceId.Manufacturer || '',
                oui: deviceId.OUI || '',
                productClass: deviceId.ProductClass || '',
                serialNumber: deviceId.SerialNumber || ''
            },
            events: events.map(event => ({
                eventCode: event.EventCode,
                commandKey: event.CommandKey || ''
            })),
            parameters,
            maxEnvelopes: informData.MaxEnvelopes || 1,
            currentTime: informData.CurrentTime,
            retryCount: informData.RetryCount || 0
        };
    }

    parseParameterValuesResponse(responseData) {
        const parameters = {};
        if (responseData.ParameterList && responseData.ParameterList.ParameterValueStruct) {
            const paramList = Array.isArray(responseData.ParameterList.ParameterValueStruct) ?
                responseData.ParameterList.ParameterValueStruct : [responseData.ParameterList.ParameterValueStruct];
            
            paramList.forEach(param => {
                if (param.Name && param.Value !== undefined) {
                    parameters[param.Name] = param.Value._ || param.Value;
                }
            });
        }
        return parameters;
    }

    createEmptyResponse() {
        const soapEnvelope = {
            '$': {
                'xmlns:soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xmlns:cwmp': 'urn:dslforum-org:cwmp-1-0'
            },
            'soap:Header': {
                'cwmp:ID': {
                    '$': { 'soap:mustUnderstand': '1' },
                    '_': this.generateMessageId()
                }
            },
            'soap:Body': {}
        };

        return this.builder.buildObject(soapEnvelope);
    }
}

module.exports = CWMPProcessor;