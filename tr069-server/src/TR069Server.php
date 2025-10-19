<?php
/**
 * Servidor TR-069/CWMP Principal
 * Maneja las comunicaciones SOAP con dispositivos CPE
 */

namespace TR069;

use PDO;
use PDOException;
use Exception;
use SoapServer;
use SoapFault;

class TR069Server {
    private $db;
    private $config;
    private $sessionId;
    private $deviceId;
    private $soapServer;
    private $logger;
    
    // Namespaces CWMP
    const CWMP_URN = 'urn:dslforum-org:cwmp-1-2';
    const SOAP_ENV = 'http://schemas.xmlsoap.org/soap/envelope/';
    const SOAP_ENC = 'http://schemas.xmlsoap.org/soap/encoding/';
    const XSD = 'http://www.w3.org/2001/XMLSchema';
    const XSI = 'http://www.w3.org/2001/XMLSchema-instance';
    
    // Métodos RPC soportados
    private $rpcMethods = [
        'Inform',
        'GetRPCMethods',
        'TransferComplete',
        'RequestDownload',
        'Kicked',
        'DUStateChangeComplete',
        'AutonomousTransferComplete',
        'AutonomousDUStateChangeComplete'
    ];
    
    public function __construct($config = null) {
        // Cargar configuración
        if ($config) {
            $this->config = $config;
        } else {
            $this->loadConfig();
        }
        
        // Inicializar base de datos
        $this->initDatabase();
        
        // Inicializar logger
        $this->logger = new Logger($this->db, $this->config);
        
        // Generar ID de sesión
        $this->sessionId = $this->generateSessionId();
    }
    
    /**
     * Cargar configuración desde archivo
     */
    private function loadConfig() {
        $configFile = __DIR__ . '/../config/config.php';
        if (file_exists($configFile)) {
            require_once $configFile;
            $this->config = [
                'db_host' => DB_HOST,
                'db_port' => DB_PORT,
                'db_name' => DB_NAME,
                'db_user' => DB_USER,
                'db_pass' => DB_PASS,
                'server_url' => SERVER_URL,
                'server_port' => SERVER_PORT,
                'acs_path' => ACS_PATH,
                'auth_enabled' => AUTH_ENABLED,
                'auth_user' => AUTH_USER,
                'auth_pass' => AUTH_PASS,
                'session_timeout' => SESSION_TIMEOUT,
                'log_level' => LOG_LEVEL
            ];
        } else {
            throw new Exception("Archivo de configuración no encontrado. Ejecute install.php primero.");
        }
    }
    
    /**
     * Inicializar conexión a base de datos
     */
    private function initDatabase() {
        try {
            $dsn = "mysql:host={$this->config['db_host']};port={$this->config['db_port']};dbname={$this->config['db_name']};charset=utf8mb4";
            $this->db = new PDO($dsn, $this->config['db_user'], $this->config['db_pass']);
            $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch (PDOException $e) {
            throw new Exception("Error de conexión a base de datos: " . $e->getMessage());
        }
    }
    
    /**
     * Generar ID de sesión único
     */
    private function generateSessionId() {
        return uniqid('cwmp_', true);
    }
    
    /**
     * Procesar solicitud HTTP
     */
    public function handleRequest() {
        try {
            // Verificar autenticación HTTP si está habilitada
            if ($this->config['auth_enabled']) {
                $this->checkAuthentication();
            }
            
            // Obtener contenido de la solicitud
            $input = file_get_contents('php://input');
            
            // Log de la solicitud
            $this->logger->debug("Solicitud recibida", ['body' => $input]);
            
            // Si es una solicitud vacía, enviar InformResponse vacío
            if (empty($input)) {
                $this->sendEmptyResponse();
                return;
            }
            
            // Parsear SOAP
            $soapRequest = $this->parseSoapRequest($input);
            
            // Procesar según el tipo de mensaje
            $response = $this->processMessage($soapRequest);
            
            // Enviar respuesta
            $this->sendSoapResponse($response);
            
        } catch (Exception $e) {
            $this->logger->error("Error procesando solicitud: " . $e->getMessage());
            $this->sendSoapFault($e->getMessage());
        }
    }
    
    /**
     * Verificar autenticación HTTP básica
     */
    private function checkAuthentication() {
        if (!isset($_SERVER['PHP_AUTH_USER']) || !isset($_SERVER['PHP_AUTH_PW'])) {
            $this->requireAuthentication();
        }
        
        if ($_SERVER['PHP_AUTH_USER'] !== $this->config['auth_user'] || 
            $_SERVER['PHP_AUTH_PW'] !== $this->config['auth_pass']) {
            $this->requireAuthentication();
        }
    }
    
    /**
     * Solicitar autenticación HTTP
     */
    private function requireAuthentication() {
        header('WWW-Authenticate: Basic realm="TR-069 ACS"');
        header('HTTP/1.0 401 Unauthorized');
        echo 'Authentication required';
        exit;
    }
    
    /**
     * Parsear solicitud SOAP
     */
    private function parseSoapRequest($xml) {
        try {
            $dom = new \DOMDocument();
            $dom->loadXML($xml);
            
            // Obtener el body del SOAP
            $body = $dom->getElementsByTagNameNS(self::SOAP_ENV, 'Body')->item(0);
            if (!$body) {
                throw new Exception("SOAP Body no encontrado");
            }
            
            // Obtener el método RPC
            $method = null;
            $params = [];
            
            foreach ($body->childNodes as $child) {
                if ($child->nodeType === XML_ELEMENT_NODE) {
                    $method = $child->localName;
                    
                    // Extraer parámetros
                    foreach ($child->childNodes as $param) {
                        if ($param->nodeType === XML_ELEMENT_NODE) {
                            $params[$param->localName] = $param->nodeValue;
                        }
                    }
                    break;
                }
            }
            
            // Guardar mensaje en base de datos
            $this->saveMessage($xml, 'request', $method);
            
            return [
                'method' => $method,
                'params' => $params,
                'raw' => $xml
            ];
            
        } catch (Exception $e) {
            throw new Exception("Error parseando SOAP: " . $e->getMessage());
        }
    }
    
    /**
     * Procesar mensaje según el método RPC
     */
    private function processMessage($soapRequest) {
        $method = $soapRequest['method'];
        $params = $soapRequest['params'];
        
        $this->logger->info("Procesando método: $method");
        
        switch ($method) {
            case 'Inform':
                return $this->handleInform($params);
                
            case 'GetRPCMethods':
                return $this->handleGetRPCMethods($params);
                
            case 'TransferComplete':
                return $this->handleTransferComplete($params);
                
            case 'RequestDownload':
                return $this->handleRequestDownload($params);
                
            case 'Kicked':
                return $this->handleKicked($params);
                
            default:
                // Método no implementado, devolver respuesta vacía
                return $this->createEmptyResponse();
        }
    }
    
    /**
     * Manejar mensaje Inform
     */
    private function handleInform($params) {
        try {
            // Extraer información del dispositivo
            $deviceId = $params['DeviceId'] ?? null;
            $manufacturer = $params['Manufacturer'] ?? '';
            $oui = $params['OUI'] ?? '';
            $productClass = $params['ProductClass'] ?? '';
            $serialNumber = $params['SerialNumber'] ?? '';
            
            // Crear identificador único
            $uniqueId = $oui . '-' . $serialNumber;
            
            // Buscar o crear dispositivo
            $device = $this->findOrCreateDevice($uniqueId, [
                'manufacturer' => $manufacturer,
                'oui' => $oui,
                'product_class' => $productClass,
                'serial_number' => $serialNumber
            ]);
            
            $this->deviceId = $device['id'];
            
            // Actualizar última conexión
            $stmt = $this->db->prepare("UPDATE devices SET last_inform = NOW(), status = 'online', ip_address = ? WHERE id = ?");
            $stmt->execute([$_SERVER['REMOTE_ADDR'] ?? '', $this->deviceId]);
            
            // Crear sesión CWMP
            $this->createSession($this->deviceId);
            
            // Log del evento
            $this->logger->info("Inform recibido de dispositivo $uniqueId");
            
            // Crear respuesta InformResponse
            return $this->createInformResponse();
            
        } catch (Exception $e) {
            $this->logger->error("Error en Inform: " . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Buscar o crear dispositivo
     */
    private function findOrCreateDevice($deviceId, $info) {
        // Buscar dispositivo existente
        $stmt = $this->db->prepare("SELECT * FROM devices WHERE device_id = ?");
        $stmt->execute([$deviceId]);
        $device = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($device) {
            // Actualizar información
            $stmt = $this->db->prepare("
                UPDATE devices SET 
                    manufacturer = ?, 
                    oui = ?, 
                    product_class = ?, 
                    serial_number = ?,
                    updated_at = NOW()
                WHERE id = ?
            ");
            $stmt->execute([
                $info['manufacturer'],
                $info['oui'],
                $info['product_class'],
                $info['serial_number'],
                $device['id']
            ]);
            
            return $device;
        } else {
            // Crear nuevo dispositivo
            $stmt = $this->db->prepare("
                INSERT INTO devices (device_id, manufacturer, oui, product_class, serial_number, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'online', NOW())
            ");
            $stmt->execute([
                $deviceId,
                $info['manufacturer'],
                $info['oui'],
                $info['product_class'],
                $info['serial_number']
            ]);
            
            return [
                'id' => $this->db->lastInsertId(),
                'device_id' => $deviceId
            ];
        }
    }
    
    /**
     * Crear sesión CWMP
     */
    private function createSession($deviceId) {
        $stmt = $this->db->prepare("
            INSERT INTO cwmp_sessions (session_id, device_id, start_time, status)
            VALUES (?, ?, NOW(), 'active')
        ");
        $stmt->execute([$this->sessionId, $deviceId]);
    }
    
    /**
     * Crear respuesta Inform
     */
    private function createInformResponse() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:InformResponse>';
        $response .= '<MaxEnvelopes>1</MaxEnvelopes>';
        $response .= '</cwmp:InformResponse>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Manejar GetRPCMethods
     */
    private function handleGetRPCMethods($params) {
        $methods = [
            'GetRPCMethods',
            'SetParameterValues',
            'GetParameterValues',
            'GetParameterNames',
            'SetParameterAttributes',
            'GetParameterAttributes',
            'AddObject',
            'DeleteObject',
            'Reboot',
            'FactoryReset',
            'Download',
            'Upload',
            'GetQueuedTransfers',
            'ScheduleInform',
            'SetVouchers',
            'GetOptions'
        ];
        
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:GetRPCMethodsResponse>';
        $response .= '<MethodList>';
        
        foreach ($methods as $method) {
            $response .= '<string>' . $method . '</string>';
        }
        
        $response .= '</MethodList>';
        $response .= '</cwmp:GetRPCMethodsResponse>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Manejar TransferComplete
     */
    private function handleTransferComplete($params) {
        $this->logger->info("TransferComplete recibido", $params);
        
        // Actualizar estado de la tarea si existe
        if (isset($params['CommandKey'])) {
            $stmt = $this->db->prepare("
                UPDATE tasks SET 
                    status = 'completed',
                    completed_at = NOW()
                WHERE device_id = ? AND task_data->>'$.CommandKey' = ?
            ");
            $stmt->execute([$this->deviceId, $params['CommandKey']]);
        }
        
        return $this->createTransferCompleteResponse();
    }
    
    /**
     * Crear respuesta TransferComplete
     */
    private function createTransferCompleteResponse() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:TransferCompleteResponse/>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Manejar RequestDownload
     */
    private function handleRequestDownload($params) {
        $this->logger->info("RequestDownload recibido", $params);
        
        // Aquí se puede implementar lógica para aprobar/rechazar descargas
        // Por ahora, aprobar todas
        
        return $this->createRequestDownloadResponse();
    }
    
    /**
     * Crear respuesta RequestDownload
     */
    private function createRequestDownloadResponse() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:RequestDownloadResponse/>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Manejar Kicked
     */
    private function handleKicked($params) {
        $this->logger->info("Kicked recibido", $params);
        return $this->createKickedResponse();
    }
    
    /**
     * Crear respuesta Kicked
     */
    private function createKickedResponse() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:KickedResponse>';
        $response .= '<NextURL>http://' . $this->config['server_url'] . ':' . $this->config['server_port'] . $this->config['acs_path'] . '</NextURL>';
        $response .= '</cwmp:KickedResponse>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Crear respuesta vacía
     */
    private function createEmptyResponse() {
        return '<?xml version="1.0" encoding="UTF-8"?>' .
               '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '">' .
               '<soap:Body/>' .
               '</soap:Envelope>';
    }
    
    /**
     * Enviar respuesta SOAP
     */
    private function sendSoapResponse($response) {
        // Headers HTTP
        header('Content-Type: text/xml; charset=utf-8');
        header('Content-Length: ' . strlen($response));
        header('SOAPAction: ""');
        
        // Guardar respuesta en base de datos
        $this->saveMessage($response, 'response', '');
        
        // Log
        $this->logger->debug("Respuesta enviada", ['body' => $response]);
        
        // Enviar respuesta
        echo $response;
    }
    
    /**
     * Enviar respuesta vacía
     */
    private function sendEmptyResponse() {
        header('Content-Type: text/xml; charset=utf-8');
        header('Content-Length: 0');
        header('SOAPAction: ""');
    }
    
    /**
     * Enviar SOAP Fault
     */
    private function sendSoapFault($message, $code = 'Server') {
        $fault = '<?xml version="1.0" encoding="UTF-8"?>';
        $fault .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '">';
        $fault .= '<soap:Body>';
        $fault .= '<soap:Fault>';
        $fault .= '<faultcode>' . $code . '</faultcode>';
        $fault .= '<faultstring>' . htmlspecialchars($message) . '</faultstring>';
        $fault .= '</soap:Fault>';
        $fault .= '</soap:Body>';
        $fault .= '</soap:Envelope>';
        
        header('Content-Type: text/xml; charset=utf-8');
        header('Content-Length: ' . strlen($fault));
        header('HTTP/1.1 500 Internal Server Error');
        
        echo $fault;
    }
    
    /**
     * Guardar mensaje SOAP en base de datos
     */
    private function saveMessage($xml, $type, $action) {
        try {
            if ($this->deviceId) {
                $stmt = $this->db->prepare("
                    INSERT INTO soap_messages (device_id, message_type, soap_action, soap_envelope, timestamp)
                    VALUES (?, ?, ?, ?, NOW())
                ");
                $stmt->execute([$this->deviceId, $type, $action, $xml]);
            }
        } catch (Exception $e) {
            $this->logger->error("Error guardando mensaje: " . $e->getMessage());
        }
    }
    
    /**
     * Verificar tareas pendientes para el dispositivo
     */
    public function checkPendingTasks() {
        if (!$this->deviceId) {
            return null;
        }
        
        $stmt = $this->db->prepare("
            SELECT * FROM tasks 
            WHERE device_id = ? 
            AND status IN ('pending', 'queued')
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        ");
        $stmt->execute([$this->deviceId]);
        
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
    
    /**
     * Ejecutar tarea pendiente
     */
    public function executeTask($task) {
        $taskData = json_decode($task['task_data'], true);
        
        switch ($task['task_type']) {
            case 'GetParameterValues':
                return $this->createGetParameterValues($taskData);
                
            case 'SetParameterValues':
                return $this->createSetParameterValues($taskData);
                
            case 'Reboot':
                return $this->createReboot();
                
            case 'FactoryReset':
                return $this->createFactoryReset();
                
            case 'Download':
                return $this->createDownload($taskData);
                
            default:
                return null;
        }
    }
    
    /**
     * Crear mensaje GetParameterValues
     */
    private function createGetParameterValues($params) {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:GetParameterValues>';
        $response .= '<ParameterNames>';
        
        foreach ($params['parameters'] as $param) {
            $response .= '<string>' . $param . '</string>';
        }
        
        $response .= '</ParameterNames>';
        $response .= '</cwmp:GetParameterValues>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Crear mensaje SetParameterValues
     */
    private function createSetParameterValues($params) {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:SetParameterValues>';
        $response .= '<ParameterList>';
        
        foreach ($params['parameters'] as $name => $value) {
            $response .= '<ParameterValueStruct>';
            $response .= '<Name>' . $name . '</Name>';
            $response .= '<Value>' . $value . '</Value>';
            $response .= '</ParameterValueStruct>';
        }
        
        $response .= '</ParameterList>';
        $response .= '<ParameterKey>' . ($params['parameter_key'] ?? '') . '</ParameterKey>';
        $response .= '</cwmp:SetParameterValues>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Crear mensaje Reboot
     */
    private function createReboot() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:Reboot>';
        $response .= '<CommandKey></CommandKey>';
        $response .= '</cwmp:Reboot>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Crear mensaje FactoryReset
     */
    private function createFactoryReset() {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:FactoryReset/>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
    
    /**
     * Crear mensaje Download
     */
    private function createDownload($params) {
        $response = '<?xml version="1.0" encoding="UTF-8"?>';
        $response .= '<soap:Envelope xmlns:soap="' . self::SOAP_ENV . '" ';
        $response .= 'xmlns:cwmp="' . self::CWMP_URN . '">';
        $response .= '<soap:Header><cwmp:ID>1</cwmp:ID></soap:Header>';
        $response .= '<soap:Body>';
        $response .= '<cwmp:Download>';
        $response .= '<CommandKey>' . ($params['command_key'] ?? '') . '</CommandKey>';
        $response .= '<FileType>' . ($params['file_type'] ?? '1 Firmware Upgrade Image') . '</FileType>';
        $response .= '<URL>' . $params['url'] . '</URL>';
        $response .= '<Username>' . ($params['username'] ?? '') . '</Username>';
        $response .= '<Password>' . ($params['password'] ?? '') . '</Password>';
        $response .= '<FileSize>' . ($params['file_size'] ?? '0') . '</FileSize>';
        $response .= '<TargetFileName>' . ($params['target_filename'] ?? '') . '</TargetFileName>';
        $response .= '<DelaySeconds>' . ($params['delay_seconds'] ?? '0') . '</DelaySeconds>';
        $response .= '<SuccessURL>' . ($params['success_url'] ?? '') . '</SuccessURL>';
        $response .= '<FailureURL>' . ($params['failure_url'] ?? '') . '</FailureURL>';
        $response .= '</cwmp:Download>';
        $response .= '</soap:Body>';
        $response .= '</soap:Envelope>';
        
        return $response;
    }
}

/**
 * Clase Logger simplificada
 */
class Logger {
    private $db;
    private $config;
    
    public function __construct($db, $config) {
        $this->db = $db;
        $this->config = $config;
    }
    
    public function log($level, $message, $context = []) {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO logs (log_level, message, context, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, NOW())
            ");
            
            $stmt->execute([
                strtoupper($level),
                $message,
                json_encode($context),
                $_SERVER['REMOTE_ADDR'] ?? '',
                $_SERVER['HTTP_USER_AGENT'] ?? ''
            ]);
        } catch (Exception $e) {
            error_log("Error escribiendo log: " . $e->getMessage());
        }
    }
    
    public function debug($message, $context = []) {
        if (in_array($this->config['log_level'], ['DEBUG'])) {
            $this->log('debug', $message, $context);
        }
    }
    
    public function info($message, $context = []) {
        if (in_array($this->config['log_level'], ['DEBUG', 'INFO'])) {
            $this->log('info', $message, $context);
        }
    }
    
    public function warning($message, $context = []) {
        if (in_array($this->config['log_level'], ['DEBUG', 'INFO', 'WARNING'])) {
            $this->log('warning', $message, $context);
        }
    }
    
    public function error($message, $context = []) {
        $this->log('error', $message, $context);
    }
}