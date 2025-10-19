<?php
/**
 * Endpoint principal del servidor ACS TR-069
 * Este archivo recibe todas las comunicaciones de los dispositivos CPE
 */

// Configurar manejo de errores
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

// Incluir autoloader si existe
if (file_exists(__DIR__ . '/../vendor/autoload.php')) {
    require_once __DIR__ . '/../vendor/autoload.php';
}

// Incluir la clase del servidor
require_once __DIR__ . '/../src/TR069Server.php';

use TR069\TR069Server;

try {
    // Crear instancia del servidor
    $server = new TR069Server();
    
    // Procesar la solicitud
    $server->handleRequest();
    
} catch (Exception $e) {
    // Log del error
    error_log("Error en ACS: " . $e->getMessage());
    
    // Enviar respuesta de error SOAP
    header('Content-Type: text/xml; charset=utf-8');
    header('HTTP/1.1 500 Internal Server Error');
    
    $fault = '<?xml version="1.0" encoding="UTF-8"?>';
    $fault .= '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">';
    $fault .= '<soap:Body>';
    $fault .= '<soap:Fault>';
    $fault .= '<faultcode>Server</faultcode>';
    $fault .= '<faultstring>' . htmlspecialchars($e->getMessage()) . '</faultstring>';
    $fault .= '</soap:Fault>';
    $fault .= '</soap:Body>';
    $fault .= '</soap:Envelope>';
    
    echo $fault;
}