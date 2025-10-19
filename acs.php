<?php
/**
 * TR-069 ACS Server (Auto Configuration Server)
 * Handles SOAP requests from CPE devices
 */

// Load configuration
if (!file_exists(__DIR__ . '/config.php')) {
    http_response_code(503);
    die('ACS not configured. Please run install.php first.');
}

$config = require __DIR__ . '/config.php';

// Set timezone
date_default_timezone_set($config['app']['timezone']);

// Error handling
if ($config['app']['debug']) {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}

// Database connection
try {
    $dsn = sprintf(
        "mysql:host=%s;port=%d;dbname=%s;charset=%s",
        $config['db']['host'],
        $config['db']['port'],
        $config['db']['database'],
        $config['db']['charset']
    );
    $pdo = new PDO($dsn, $config['db']['username'], $config['db']['password']);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (PDOException $e) {
    error_log("TR-069 ACS Database Error: " . $e->getMessage());
    http_response_code(500);
    die('Database connection failed');
}

// Logging function
function log_message($level, $message, $context = []) {
    global $config;
    if (!$config['logging']['enabled']) return;
    
    $log_levels = ['debug' => 0, 'info' => 1, 'warning' => 2, 'error' => 3];
    $current_level = $log_levels[$config['logging']['log_level']] ?? 1;
    
    if ($log_levels[$level] < $current_level) return;
    
    $log_file = $config['logging']['log_path'] . '/acs_' . date('Y-m-d') . '.log';
    $timestamp = date('Y-m-d H:i:s');
    $context_str = !empty($context) ? ' ' . json_encode($context) : '';
    $log_entry = "[$timestamp] [$level] $message$context_str\n";
    
    @file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
}

// Check authentication
function check_auth() {
    global $config;
    
    if (!$config['security']['require_device_auth']) {
        return true;
    }
    
    if (!isset($_SERVER['PHP_AUTH_USER']) || !isset($_SERVER['PHP_AUTH_PW'])) {
        return false;
    }
    
    return $_SERVER['PHP_AUTH_USER'] === $config['acs']['username'] &&
           $_SERVER['PHP_AUTH_PW'] === $config['acs']['password'];
}

// Require authentication
if (!check_auth()) {
    header('WWW-Authenticate: Basic realm="TR-069 ACS"');
    header('HTTP/1.0 401 Unauthorized');
    log_message('warning', 'Authentication failed', ['ip' => $_SERVER['REMOTE_ADDR']]);
    die('Authentication required');
}

// Get request body
$request_body = file_get_contents('php://input');
$client_ip = $_SERVER['REMOTE_ADDR'];

log_message('info', 'Received request from CPE', [
    'ip' => $client_ip,
    'method' => $_SERVER['REQUEST_METHOD']
]);

if ($config['logging']['log_requests']) {
    log_message('debug', 'Request body', ['body' => $request_body]);
}

// Parse SOAP envelope
class TR069Handler {
    private $pdo;
    private $config;
    private $device_id = null;
    private $session_id = null;
    
    public function __construct($pdo, $config) {
        $this->pdo = $pdo;
        $this->config = $config;
    }
    
    public function handleRequest($soap_request) {
        try {
            // Parse SOAP request
            $xml = @simplexml_load_string($soap_request);
            if ($xml === false) {
                log_message('error', 'Invalid SOAP XML');
                return $this->generateEmptyResponse();
            }
            
            // Register namespaces
            $xml->registerXPathNamespace('soap', 'http://schemas.xmlsoap.org/soap/envelope/');
            $xml->registerXPathNamespace('cwmp', 'urn:dslforum-org:cwmp-1-0');
            
            // Check for Inform message
            $inform = $xml->xpath('//cwmp:Inform');
            if (!empty($inform)) {
                return $this->handleInform($xml);
            }
            
            // Check for TransferComplete
            $transfer = $xml->xpath('//cwmp:TransferComplete');
            if (!empty($transfer)) {
                return $this->handleTransferComplete($xml);
            }
            
            // Check for GetParameterValuesResponse
            $getParamResp = $xml->xpath('//cwmp:GetParameterValuesResponse');
            if (!empty($getParamResp)) {
                return $this->handleGetParameterValuesResponse($xml);
            }
            
            // Check for SetParameterValuesResponse
            $setParamResp = $xml->xpath('//cwmp:SetParameterValuesResponse');
            if (!empty($setParamResp)) {
                return $this->handleSetParameterValuesResponse($xml);
            }
            
            // Empty request (CPE waiting for commands)
            return $this->checkPendingTasks();
            
        } catch (Exception $e) {
            log_message('error', 'Error handling request: ' . $e->getMessage());
            return $this->generateEmptyResponse();
        }
    }
    
    private function handleInform($xml) {
        global $client_ip;
        
        $xml->registerXPathNamespace('cwmp', 'urn:dslforum-org:cwmp-1-0');
        
        // Extract device info
        $deviceId = (string)$xml->xpath('//DeviceId')[0];
        $deviceIdXml = simplexml_load_string('<DeviceId>' . $deviceId . '</DeviceId>');
        
        $manufacturer = (string)($deviceIdXml->Manufacturer ?? '');
        $oui = (string)($deviceIdXml->OUI ?? '');
        $productClass = (string)($deviceIdXml->ProductClass ?? '');
        $serialNumber = (string)($deviceIdXml->SerialNumber ?? '');
        
        // Extract event codes
        $events = $xml->xpath('//EventStruct');
        $eventCodes = [];
        foreach ($events as $event) {
            $eventCodes[] = (string)$event->EventCode;
        }
        
        // Extract parameter list
        $parameterList = $xml->xpath('//ParameterValueStruct');
        $parameters = [];
        foreach ($parameterList as $param) {
            $name = (string)$param->Name;
            $value = (string)$param->Value;
            $parameters[$name] = $value;
        }
        
        log_message('info', 'Received Inform', [
            'serial' => $serialNumber,
            'oui' => $oui,
            'events' => $eventCodes
        ]);
        
        // Check if device exists
        $stmt = $this->pdo->prepare("SELECT id FROM devices WHERE serial_number = ? AND oui = ?");
        $stmt->execute([$serialNumber, $oui]);
        $device = $stmt->fetch();
        
        if ($device) {
            // Update existing device
            $this->device_id = $device['id'];
            $stmt = $this->pdo->prepare("
                UPDATE devices SET 
                    manufacturer = ?,
                    product_class = ?,
                    hardware_version = ?,
                    software_version = ?,
                    connection_request_url = ?,
                    last_inform = NOW(),
                    ip_address = ?,
                    status = 'online'
                WHERE id = ?
            ");
            $stmt->execute([
                $manufacturer,
                $productClass,
                $parameters['InternetGatewayDevice.DeviceInfo.HardwareVersion'] ?? '',
                $parameters['InternetGatewayDevice.DeviceInfo.SoftwareVersion'] ?? '',
                $parameters['InternetGatewayDevice.ManagementServer.ConnectionRequestURL'] ?? '',
                $client_ip,
                $this->device_id
            ]);
        } else {
            // Insert new device
            $stmt = $this->pdo->prepare("
                INSERT INTO devices (serial_number, oui, manufacturer, product_class, model,
                    hardware_version, software_version, connection_request_url, 
                    last_inform, ip_address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), ?, 'online')
            ");
            $stmt->execute([
                $serialNumber,
                $oui,
                $manufacturer,
                $productClass,
                $parameters['InternetGatewayDevice.DeviceInfo.ModelName'] ?? '',
                $parameters['InternetGatewayDevice.DeviceInfo.HardwareVersion'] ?? '',
                $parameters['InternetGatewayDevice.DeviceInfo.SoftwareVersion'] ?? '',
                $parameters['InternetGatewayDevice.ManagementServer.ConnectionRequestURL'] ?? '',
                $client_ip
            ]);
            $this->device_id = $this->pdo->lastInsertId();
        }
        
        // Store parameters
        foreach ($parameters as $name => $value) {
            $stmt = $this->pdo->prepare("
                INSERT INTO parameters (device_id, parameter_name, parameter_value, parameter_type)
                VALUES (?, ?, ?, 'string')
                ON DUPLICATE KEY UPDATE parameter_value = VALUES(parameter_value)
            ");
            $stmt->execute([$this->device_id, $name, $value]);
        }
        
        // Log inform
        $stmt = $this->pdo->prepare("
            INSERT INTO inform_log (device_id, serial_number, event_code, request_data, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            $this->device_id,
            $serialNumber,
            implode(',', $eventCodes),
            $xml->asXML(),
            $client_ip
        ]);
        
        // Generate InformResponse
        return $this->generateInformResponse();
    }
    
    private function handleGetParameterValuesResponse($xml) {
        $xml->registerXPathNamespace('cwmp', 'urn:dslforum-org:cwmp-1-0');
        
        $parameterList = $xml->xpath('//ParameterValueStruct');
        $parameters = [];
        foreach ($parameterList as $param) {
            $name = (string)$param->Name;
            $value = (string)$param->Value;
            $parameters[$name] = $value;
            
            // Update in database if we have device_id
            if ($this->device_id) {
                $stmt = $this->pdo->prepare("
                    INSERT INTO parameters (device_id, parameter_name, parameter_value, parameter_type)
                    VALUES (?, ?, ?, 'string')
                    ON DUPLICATE KEY UPDATE parameter_value = VALUES(parameter_value)
                ");
                $stmt->execute([$this->device_id, $name, $value]);
            }
        }
        
        log_message('info', 'Received GetParameterValuesResponse', [
            'device_id' => $this->device_id,
            'count' => count($parameters)
        ]);
        
        return $this->checkPendingTasks();
    }
    
    private function handleSetParameterValuesResponse($xml) {
        $xml->registerXPathNamespace('cwmp', 'urn:dslforum-org:cwmp-1-0');
        
        $status = $xml->xpath('//cwmp:Status');
        $statusCode = !empty($status) ? (string)$status[0] : '0';
        
        log_message('info', 'Received SetParameterValuesResponse', [
            'device_id' => $this->device_id,
            'status' => $statusCode
        ]);
        
        return $this->checkPendingTasks();
    }
    
    private function handleTransferComplete($xml) {
        log_message('info', 'Received TransferComplete', [
            'device_id' => $this->device_id
        ]);
        
        return $this->generateTransferCompleteResponse();
    }
    
    private function checkPendingTasks() {
        if (!$this->device_id) {
            return $this->generateEmptyResponse();
        }
        
        // Check for pending tasks
        $stmt = $this->pdo->prepare("
            SELECT * FROM tasks 
            WHERE device_id = ? AND status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT 1
        ");
        $stmt->execute([$this->device_id]);
        $task = $stmt->fetch();
        
        if ($task) {
            // Mark task as sent
            $stmt = $this->pdo->prepare("UPDATE tasks SET status = 'sent' WHERE id = ?");
            $stmt->execute([$task['id']]);
            
            // Generate appropriate request
            switch ($task['task_type']) {
                case 'GetParameterValues':
                    return $this->generateGetParameterValues($task);
                case 'SetParameterValues':
                    return $this->generateSetParameterValues($task);
                case 'Reboot':
                    return $this->generateReboot();
                default:
                    return $this->generateEmptyResponse();
            }
        }
        
        return $this->generateEmptyResponse();
    }
    
    private function generateInformResponse() {
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:InformResponse>
            <MaxEnvelopes>1</MaxEnvelopes>
        </cwmp:InformResponse>
    </soap:Body>
</soap:Envelope>';
    }
    
    private function generateTransferCompleteResponse() {
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:TransferCompleteResponse/>
    </soap:Body>
</soap:Envelope>';
    }
    
    private function generateGetParameterValues($task) {
        $params = json_decode($task['parameters'], true);
        $parameterNames = $params['parameters'] ?? [];
        
        $parameterList = '';
        foreach ($parameterNames as $param) {
            $parameterList .= "<string>$param</string>\n";
        }
        
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:GetParameterValues>
            <ParameterNames>' . $parameterList . '</ParameterNames>
        </cwmp:GetParameterValues>
    </soap:Body>
</soap:Envelope>';
    }
    
    private function generateSetParameterValues($task) {
        $params = json_decode($task['parameters'], true);
        $parameters = $params['parameters'] ?? [];
        
        $parameterList = '';
        foreach ($parameters as $name => $value) {
            $parameterList .= "
            <ParameterValueStruct>
                <Name>$name</Name>
                <Value>$value</Value>
            </ParameterValueStruct>";
        }
        
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:SetParameterValues>
            <ParameterList>' . $parameterList . '</ParameterList>
            <ParameterKey>key_' . time() . '</ParameterKey>
        </cwmp:SetParameterValues>
    </soap:Body>
</soap:Envelope>';
    }
    
    private function generateReboot() {
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:Reboot>
            <CommandKey>reboot_' . time() . '</CommandKey>
        </cwmp:Reboot>
    </soap:Body>
</soap:Envelope>';
    }
    
    private function generateEmptyResponse() {
        return '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">1</cwmp:ID>
    </soap:Header>
    <soap:Body>
    </soap:Body>
</soap:Envelope>';
    }
}

// Process request
$handler = new TR069Handler($pdo, $config);
$response = $handler->handleRequest($request_body);

// Send response
header('Content-Type: text/xml; charset=utf-8');
header('SOAPAction: ""');

if ($config['logging']['log_requests']) {
    log_message('debug', 'Response body', ['body' => $response]);
}

echo $response;
