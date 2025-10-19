<?php
/**
 * TR-069 ACS (Auto Configuration Server) Implementation
 * This is the main endpoint that CPE devices will connect to
 */

error_reporting(E_ALL);
ini_set('display_errors', 0); // Don't display errors to CPE devices

// Include configuration
require_once 'config/database.php';
require_once 'config/acs.php';
require_once 'classes/Database.php';
require_once 'classes/TR069Server.php';
require_once 'classes/Logger.php';

// Start output buffering to capture any unwanted output
ob_start();

try {
    // Initialize logger
    $logger = new Logger('logs/acs.log');
    
    // Log incoming request
    $logger->info("ACS Request from " . $_SERVER['REMOTE_ADDR'] . " - " . $_SERVER['REQUEST_METHOD']);
    
    // Initialize database
    $database = new Database();
    $db = $database->getConnection();
    
    // Initialize TR-069 server
    $tr069 = new TR069Server($db, $logger);
    
    // Handle HTTP authentication if configured
    if (defined('ACS_USERNAME') && !empty(ACS_USERNAME)) {
        if (!isset($_SERVER['PHP_AUTH_USER']) || 
            $_SERVER['PHP_AUTH_USER'] !== ACS_USERNAME || 
            $_SERVER['PHP_AUTH_PW'] !== ACS_PASSWORD) {
            
            header('WWW-Authenticate: Basic realm="TR-069 ACS"');
            header('HTTP/1.0 401 Unauthorized');
            $logger->warning("Authentication failed for " . $_SERVER['REMOTE_ADDR']);
            exit;
        }
    }
    
    // Process the TR-069 request
    $tr069->handleRequest();
    
} catch (Exception $e) {
    // Log error
    if (isset($logger)) {
        $logger->error("ACS Error: " . $e->getMessage());
    }
    
    // Send error response to CPE
    header('HTTP/1.1 500 Internal Server Error');
    header('Content-Type: text/xml; charset=utf-8');
    
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    echo '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">';
    echo '<soap:Body>';
    echo '<soap:Fault>';
    echo '<faultcode>Server</faultcode>';
    echo '<faultstring>Internal Server Error</faultstring>';
    echo '</soap:Fault>';
    echo '</soap:Body>';
    echo '</soap:Envelope>';
}

// Clean up output buffer
ob_end_clean();
?>