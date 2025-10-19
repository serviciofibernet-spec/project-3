<?php
/**
 * TR-069 Server Implementation
 * Handles CWMP (CPE WAN Management Protocol) communication
 */
class TR069Server {
    private $db;
    private $logger;
    private $sessionId;
    private $deviceId;
    
    public function __construct($database, $logger) {
        $this->db = $database;
        $this->logger = $logger;
    }
    
    public function handleRequest() {
        // Get request method
        $method = $_SERVER['REQUEST_METHOD'];
        
        if ($method === 'POST') {
            $this->handleSOAPRequest();
        } else {
            $this->sendError(405, 'Method Not Allowed');
        }
    }
    
    private function handleSOAPRequest() {
        // Read SOAP request
        $soapRequest = file_get_contents('php://input');
        
        if (empty($soapRequest)) {
            $this->logger->warning("Empty SOAP request received");
            $this->sendError(400, 'Bad Request');
            return;
        }
        
        $this->logger->debug("SOAP Request: " . $soapRequest);
        
        try {
            // Parse SOAP XML
            $xml = new SimpleXMLElement($soapRequest);
            $xml->registerXPathNamespace('soap', 'http://schemas.xmlsoap.org/soap/envelope/');
            $xml->registerXPathNamespace('cwmp', 'urn:dslforum-org:cwmp-1-0');
            
            // Extract SOAP body
            $body = $xml->xpath('//soap:Body/*')[0];
            
            if (!$body) {
                throw new Exception("Invalid SOAP message");
            }
            
            $methodName = $body->getName();
            $this->logger->info("Processing CWMP method: $methodName");
            
            // Route to appropriate handler
            switch ($methodName) {
                case 'Inform':
                    $this->handleInform($body);
                    break;
                case 'GetRPCMethodsResponse':
                    $this->handleGetRPCMethodsResponse($body);
                    break;
                case 'GetParameterValuesResponse':
                    $this->handleGetParameterValuesResponse($body);
                    break;
                case 'SetParameterValuesResponse':
                    $this->handleSetParameterValuesResponse($body);
                    break;
                case 'TransferCompleteResponse':
                    $this->handleTransferCompleteResponse($body);
                    break;
                default:
                    $this->logger->warning("Unknown CWMP method: $methodName");
                    $this->sendInformResponse();
            }
            
        } catch (Exception $e) {
            $this->logger->error("SOAP parsing error: " . $e->getMessage());
            $this->sendSOAPFault('Client', 'Invalid SOAP message');
        }
    }
    
    private function handleInform($inform) {
        try {
            // Extract device information
            $deviceInfo = $inform->DeviceId;
            $serialNumber = (string)$deviceInfo->SerialNumber;
            $oui = (string)$deviceInfo->OUI;
            $productClass = (string)$deviceInfo->ProductClass;
            $manufacturer = (string)$deviceInfo->Manufacturer;
            
            $this->logger->info("Inform from device: $oui-$serialNumber");
            
            // Find or create device
            $stmt = $this->db->prepare("
                SELECT id FROM devices 
                WHERE serial_number = ? AND oui = ?
            ");
            $stmt->execute([$serialNumber, $oui]);
            $device = $stmt->fetch();
            
            if (!$device) {
                // Create new device
                $stmt = $this->db->prepare("
                    INSERT INTO devices (serial_number, oui, product_class, manufacturer, last_inform, ip_address, status)
                    VALUES (?, ?, ?, ?, NOW(), ?, 'online')
                ");
                $stmt->execute([$serialNumber, $oui, $productClass, $manufacturer, $_SERVER['REMOTE_ADDR']]);
                $this->deviceId = $this->db->lastInsertId();
                $this->logger->info("Created new device with ID: {$this->deviceId}");
            } else {
                // Update existing device
                $this->deviceId = $device['id'];
                $stmt = $this->db->prepare("
                    UPDATE devices 
                    SET last_inform = NOW(), ip_address = ?, status = 'online'
                    WHERE id = ?
                ");
                $stmt->execute([$_SERVER['REMOTE_ADDR'], $this->deviceId]);
                $this->logger->info("Updated device ID: {$this->deviceId}");
            }
            
            // Create session
            $this->sessionId = uniqid('tr069_', true);
            $stmt = $this->db->prepare("
                INSERT INTO sessions (device_id, session_id, state, inform_data)
                VALUES (?, ?, 'active', ?)
            ");
            $stmt->execute([$this->deviceId, $this->sessionId, $inform->asXML()]);
            
            // Process events
            if (isset($inform->Event)) {
                foreach ($inform->Event as $event) {
                    $eventCode = (string)$event->EventCode;
                    $commandKey = (string)$event->CommandKey;
                    
                    $stmt = $this->db->prepare("
                        INSERT INTO events (device_id, event_type, event_code, command_key, message)
                        VALUES (?, 'inform', ?, ?, ?)
                    ");
                    $stmt->execute([$this->deviceId, $eventCode, $commandKey, "Device inform event"]);
                }
            }
            
            // Process parameters
            if (isset($inform->ParameterList)) {
                foreach ($inform->ParameterList->ParameterValueStruct as $param) {
                    $name = (string)$param->Name;
                    $value = (string)$param->Value;
                    
                    $stmt = $this->db->prepare("
                        INSERT INTO parameters (device_id, name, value, last_updated)
                        VALUES (?, ?, ?, NOW())
                        ON DUPLICATE KEY UPDATE value = VALUES(value), last_updated = NOW()
                    ");
                    $stmt->execute([$this->deviceId, $name, $value]);
                }
            }
            
            // Check for pending tasks
            $nextTask = $this->getNextTask();
            
            if ($nextTask) {
                $this->sendTaskResponse($nextTask);
            } else {
                $this->sendInformResponse();
            }
            
        } catch (Exception $e) {
            $this->logger->error("Error handling Inform: " . $e->getMessage());
            $this->sendSOAPFault('Server', 'Internal error processing Inform');
        }
    }
    
    private function getNextTask() {
        if (!$this->deviceId) return null;
        
        $stmt = $this->db->prepare("
            SELECT * FROM tasks 
            WHERE device_id = ? AND status = 'pending'
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
        ");
        $stmt->execute([$this->deviceId]);
        return $stmt->fetch();
    }
    
    private function sendTaskResponse($task) {
        // Mark task as in progress
        $stmt = $this->db->prepare("
            UPDATE tasks SET status = 'in_progress', started_at = NOW() WHERE id = ?
        ");
        $stmt->execute([$task['id']]);
        
        switch ($task['type']) {
            case 'GetParameterValues':
                $this->sendGetParameterValues($task);
                break;
            case 'SetParameterValues':
                $this->sendSetParameterValues($task);
                break;
            case 'Reboot':
                $this->sendReboot($task);
                break;
            default:
                $this->sendInformResponse();
        }
    }
    
    private function sendGetParameterValues($task) {
        $parameters = json_decode($task['parameters'], true);
        $parameterNames = $parameters['names'] ?? [];
        
        header('Content-Type: text/xml; charset=utf-8');
        header('SOAPAction: ""');
        
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">';
        echo '<soap:Header><cwmp:ID soap:mustUnderstand="1">' . $this->sessionId . '</cwmp:ID></soap:Header>';
        echo '<soap:Body>';
        echo '<cwmp:GetParameterValues>';
        echo '<ParameterNames soap:arrayType="xsd:string[' . count($parameterNames) . ']">';
        
        foreach ($parameterNames as $name) {
            echo '<string>' . htmlspecialchars($name) . '</string>';
        }
        
        echo '</ParameterNames>';
        echo '</cwmp:GetParameterValues>';
        echo '</soap:Body>';
        echo '</soap:Envelope>';
    }
    
    private function sendSetParameterValues($task) {
        $parameters = json_decode($task['parameters'], true);
        $parameterList = $parameters['values'] ?? [];
        
        header('Content-Type: text/xml; charset=utf-8');
        header('SOAPAction: ""');
        
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">';
        echo '<soap:Header><cwmp:ID soap:mustUnderstand="1">' . $this->sessionId . '</cwmp:ID></soap:Header>';
        echo '<soap:Body>';
        echo '<cwmp:SetParameterValues>';
        echo '<ParameterList soap:arrayType="cwmp:ParameterValueStruct[' . count($parameterList) . ']">';
        
        foreach ($parameterList as $name => $value) {
            echo '<ParameterValueStruct>';
            echo '<Name>' . htmlspecialchars($name) . '</Name>';
            echo '<Value xsi:type="xsd:string">' . htmlspecialchars($value) . '</Value>';
            echo '</ParameterValueStruct>';
        }
        
        echo '</ParameterList>';
        echo '<ParameterKey>' . uniqid() . '</ParameterKey>';
        echo '</cwmp:SetParameterValues>';
        echo '</soap:Body>';
        echo '</soap:Envelope>';
    }
    
    private function sendReboot($task) {
        header('Content-Type: text/xml; charset=utf-8');
        header('SOAPAction: ""');
        
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">';
        echo '<soap:Header><cwmp:ID soap:mustUnderstand="1">' . $this->sessionId . '</cwmp:ID></soap:Header>';
        echo '<soap:Body>';
        echo '<cwmp:Reboot>';
        echo '<CommandKey>' . uniqid() . '</CommandKey>';
        echo '</cwmp:Reboot>';
        echo '</soap:Body>';
        echo '</soap:Envelope>';
    }
    
    private function sendInformResponse() {
        header('Content-Type: text/xml; charset=utf-8');
        header('SOAPAction: ""');
        
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cwmp="urn:dslforum-org:cwmp-1-0">';
        echo '<soap:Header><cwmp:ID soap:mustUnderstand="1">' . $this->sessionId . '</cwmp:ID></soap:Header>';
        echo '<soap:Body>';
        echo '<cwmp:InformResponse>';
        echo '<MaxEnvelopes>1</MaxEnvelopes>';
        echo '</cwmp:InformResponse>';
        echo '</soap:Body>';
        echo '</soap:Envelope>';
    }
    
    private function handleGetParameterValuesResponse($response) {
        // Process response and mark task as completed
        if ($this->deviceId) {
            $stmt = $this->db->prepare("
                UPDATE tasks SET status = 'completed', completed_at = NOW(), result = ? 
                WHERE device_id = ? AND status = 'in_progress'
            ");
            $stmt->execute([$response->asXML(), $this->deviceId]);
        }
        
        $this->sendInformResponse();
    }
    
    private function handleSetParameterValuesResponse($response) {
        // Mark task as completed
        if ($this->deviceId) {
            $stmt = $this->db->prepare("
                UPDATE tasks SET status = 'completed', completed_at = NOW(), result = ? 
                WHERE device_id = ? AND status = 'in_progress'
            ");
            $stmt->execute([$response->asXML(), $this->deviceId]);
        }
        
        $this->sendInformResponse();
    }
    
    private function handleGetRPCMethodsResponse($response) {
        $this->sendInformResponse();
    }
    
    private function handleTransferCompleteResponse($response) {
        $this->sendInformResponse();
    }
    
    private function sendSOAPFault($faultCode, $faultString) {
        header('HTTP/1.1 500 Internal Server Error');
        header('Content-Type: text/xml; charset=utf-8');
        
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">';
        echo '<soap:Body>';
        echo '<soap:Fault>';
        echo '<faultcode>' . htmlspecialchars($faultCode) . '</faultcode>';
        echo '<faultstring>' . htmlspecialchars($faultString) . '</faultstring>';
        echo '</soap:Fault>';
        echo '</soap:Body>';
        echo '</soap:Envelope>';
    }
    
    private function sendError($code, $message) {
        http_response_code($code);
        echo $message;
    }
}
?>