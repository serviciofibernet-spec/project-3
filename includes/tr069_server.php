<?php
/**
 * Servidor TR-069 SOAP
 * Implementa el protocolo TR-069 para gestión remota de dispositivos CPE
 */

class TR069Server {
    private $db;
    private $soapServer;
    
    public function __construct($database) {
        $this->db = $database;
        $this->initializeSoapServer();
    }
    
    private function initializeSoapServer() {
        // Configurar SOAP server
        $options = [
            'soap_version' => SOAP_1_2,
            'encoding' => 'UTF-8',
            'uri' => 'urn:dslforum-org:cwmp-1-0',
            'location' => getConfig('server_url', 'http://localhost'),
            'trace' => 1,
            'exceptions' => true
        ];
        
        $this->soapServer = new SoapServer(null, $options);
        $this->soapServer->setClass('TR069Methods', $this->db);
    }
    
    public function handleRequest() {
        try {
            // Obtener contenido SOAP
            $soapRequest = file_get_contents('php://input');
            
            logMessage('DEBUG', 'SOAP Request: ' . $soapRequest);
            
            // Procesar solicitud SOAP
            $this->soapServer->handle($soapRequest);
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en servidor SOAP: ' . $e->getMessage());
            
            // Enviar respuesta de error
            http_response_code(500);
            echo $this->createSoapFault('Server', 'Error interno del servidor');
        }
    }
    
    private function createSoapFault($code, $message) {
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>' . htmlspecialchars($code) . '</faultcode>
            <faultstring>' . htmlspecialchars($message) . '</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>';
    }
}

/**
 * Métodos TR-069 implementados
 */
class TR069Methods {
    private $db;
    
    public function __construct($database) {
        $this->db = $database;
    }
    
    /**
     * Inform - Método principal para recibir información del dispositivo
     */
    public function Inform($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $manufacturer = $parameters['DeviceId']['Manufacturer'] ?? '';
            $model = $parameters['DeviceId']['OUI'] ?? '';
            $serialNumber = $parameters['DeviceId']['SerialNumber'] ?? '';
            $hardwareVersion = $parameters['DeviceId']['ProductClass'] ?? '';
            $softwareVersion = $parameters['Event']['EventStruct'][0]['EventCode'] ?? '';
            
            // Obtener o crear dispositivo
            $device = $this->db->getDevice($deviceId);
            if (!$device) {
                $deviceData = [
                    'device_id' => $deviceId,
                    'manufacturer' => $manufacturer,
                    'model' => $model,
                    'serial_number' => $serialNumber,
                    'hardware_version' => $hardwareVersion,
                    'software_version' => $softwareVersion,
                    'connection_request_url' => $parameters['Retry'] ?? ''
                ];
                $this->db->createDevice($deviceData);
                logMessage('INFO', "Nuevo dispositivo registrado: $deviceId");
            } else {
                // Actualizar información del dispositivo
                $updateData = [
                    'manufacturer' => $manufacturer,
                    'model' => $model,
                    'hardware_version' => $hardwareVersion,
                    'software_version' => $softwareVersion,
                    'last_inform_time' => date('Y-m-d H:i:s'),
                    'last_inform_data' => json_encode($parameters)
                ];
                $this->db->updateDevice($deviceId, $updateData);
            }
            
            // Registrar parámetros si están presentes
            if (isset($parameters['ParameterList']['ParameterValueStruct'])) {
                $this->processParameters($deviceId, $parameters['ParameterList']['ParameterValueStruct']);
            }
            
            // Crear sesión
            $sessionId = uniqid('sess_', true);
            $expiresAt = date('Y-m-d H:i:s', time() + SESSION_TIMEOUT);
            $this->db->createSession($deviceId, $sessionId, $expiresAt);
            
            // Log de la acción
            $this->db->logAction($deviceId, 'Inform', 'Dispositivo informó al servidor');
            
            // Respuesta InformResponse
            return [
                'MaxEnvelopes' => 1,
                'CurrentTime' => date('c'),
                'RetryAfter' => 0
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en Inform: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error procesando Inform');
        }
    }
    
    /**
     * GetParameterNames - Obtener nombres de parámetros
     */
    public function GetParameterNames($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $parameterPath = $parameters['ParameterPath'] ?? '';
            $nextLevel = $parameters['NextLevel'] ?? false;
            
            // Obtener parámetros de la base de datos
            $dbParameters = $this->db->getParameters($deviceId);
            
            $parameterNames = [];
            foreach ($dbParameters as $param) {
                if (empty($parameterPath) || strpos($param['parameter_name'], $parameterPath) === 0) {
                    $parameterNames[] = [
                        'Name' => $param['parameter_name'],
                        'Writable' => (bool)$param['writable']
                    ];
                }
            }
            
            $this->db->logAction($deviceId, 'GetParameterNames', "Path: $parameterPath");
            
            return [
                'ParameterList' => [
                    'ParameterInfoStruct' => $parameterNames
                ]
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en GetParameterNames: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error obteniendo nombres de parámetros');
        }
    }
    
    /**
     * GetParameterValues - Obtener valores de parámetros
     */
    public function GetParameterValues($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $parameterNames = $parameters['ParameterNames']['string'] ?? [];
            
            $parameterValues = [];
            foreach ($parameterNames as $paramName) {
                $param = $this->db->getParameter($deviceId, $paramName);
                if ($param) {
                    $parameterValues[] = [
                        'Name' => $param['parameter_name'],
                        'Value' => $param['parameter_value']
                    ];
                }
            }
            
            $this->db->logAction($deviceId, 'GetParameterValues', 'Parámetros solicitados: ' . implode(', ', $parameterNames));
            
            return [
                'ParameterList' => [
                    'ParameterValueStruct' => $parameterValues
                ]
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en GetParameterValues: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error obteniendo valores de parámetros');
        }
    }
    
    /**
     * SetParameterValues - Establecer valores de parámetros
     */
    public function SetParameterValues($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $parameterList = $parameters['ParameterList']['ParameterValueStruct'] ?? [];
            
            $status = 0; // 0 = success
            $parameterNames = [];
            
            foreach ($parameterList as $param) {
                $paramName = $param['Name'];
                $paramValue = $param['Value'];
                
                // Verificar si el parámetro es escribible
                $existingParam = $this->db->getParameter($deviceId, $paramName);
                if ($existingParam && !$existingParam['writable']) {
                    $status = 1; // Error: parámetro no escribible
                    break;
                }
                
                // Guardar parámetro
                $this->db->setParameter($deviceId, $paramName, $paramValue, 'string', true);
                $parameterNames[] = $paramName;
            }
            
            $this->db->logAction($deviceId, 'SetParameterValues', 'Parámetros modificados: ' . implode(', ', $parameterNames));
            
            return [
                'Status' => $status,
                'ParameterNames' => [
                    'string' => $parameterNames
                ]
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en SetParameterValues: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error estableciendo valores de parámetros');
        }
    }
    
    /**
     * Download - Descargar archivo al dispositivo
     */
    public function Download($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $fileType = $parameters['FileType'] ?? '';
            $url = $parameters['URL'] ?? '';
            $username = $parameters['Username'] ?? '';
            $password = $parameters['Password'] ?? '';
            $fileSize = $parameters['FileSize'] ?? 0;
            $targetFileName = $parameters['TargetFileName'] ?? '';
            $delaySeconds = $parameters['DelaySeconds'] ?? 0;
            $successURL = $parameters['SuccessURL'] ?? '';
            $failureURL = $parameters['FailureURL'] ?? '';
            
            $this->db->logAction($deviceId, 'Download', "URL: $url, FileType: $fileType");
            
            return [
                'Status' => 0, // 0 = success
                'StartTime' => date('c', time() + $delaySeconds),
                'CompleteTime' => date('c', time() + $delaySeconds + 300) // 5 minutos después
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en Download: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error en descarga');
        }
    }
    
    /**
     * Reboot - Reiniciar dispositivo
     */
    public function Reboot($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            $commandKey = $parameters['CommandKey'] ?? '';
            
            $this->db->logAction($deviceId, 'Reboot', "CommandKey: $commandKey");
            
            return [
                'Status' => 0 // 0 = success
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en Reboot: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error en reinicio');
        }
    }
    
    /**
     * FactoryReset - Restaurar configuración de fábrica
     */
    public function FactoryReset($parameters) {
        try {
            $deviceId = $parameters['DeviceId']['SerialNumber'] ?? 'unknown';
            
            $this->db->logAction($deviceId, 'FactoryReset', 'Restauración de fábrica solicitada');
            
            return [
                'Status' => 0 // 0 = success
            ];
            
        } catch (Exception $e) {
            logMessage('ERROR', 'Error en FactoryReset: ' . $e->getMessage());
            throw new SoapFault('Server', 'Error en restauración de fábrica');
        }
    }
    
    /**
     * Procesar parámetros del dispositivo
     */
    private function processParameters($deviceId, $parameters) {
        if (!is_array($parameters)) {
            return;
        }
        
        foreach ($parameters as $param) {
            if (isset($param['Name']) && isset($param['Value'])) {
                $this->db->setParameter(
                    $deviceId,
                    $param['Name'],
                    $param['Value'],
                    'string',
                    false
                );
            }
        }
    }
}
?>