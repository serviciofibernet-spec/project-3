<?php
/**
 * Configuración del Servidor TR-069
 */

// Configuración de la base de datos
define('DB_PATH', __DIR__ . '/data/tr069.db');
define('DB_INITIALIZED', __DIR__ . '/data/.db_initialized');

// Configuración del servidor
define('SERVER_NAME', 'TR069-PHP-Server');
define('SERVER_VERSION', '1.0.0');
define('LOG_LEVEL', 'INFO');

// Configuración de autenticación
define('AUTH_ENABLED', true);
define('DEFAULT_USERNAME', 'admin');
define('DEFAULT_PASSWORD', 'admin123');

// Configuración de sesiones
define('SESSION_TIMEOUT', 3600); // 1 hora

// Configuración de logging
define('LOG_FILE', __DIR__ . '/logs/tr069.log');

// Crear directorios necesarios
$directories = [
    dirname(DB_PATH),
    dirname(LOG_FILE)
];

foreach ($directories as $dir) {
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
}

// Función para logging
function logMessage($level, $message) {
    $timestamp = date('Y-m-d H:i:s');
    $logEntry = "[$timestamp] [$level] $message" . PHP_EOL;
    file_put_contents(LOG_FILE, $logEntry, FILE_APPEND | LOCK_EX);
}

// Función para obtener configuración
function getConfig($key, $default = null) {
    static $config = null;
    
    if ($config === null) {
        $configFile = __DIR__ . '/data/config.json';
        if (file_exists($configFile)) {
            $config = json_decode(file_get_contents($configFile), true) ?: [];
        } else {
            $config = [];
        }
    }
    
    return isset($config[$key]) ? $config[$key] : $default;
}

// Función para guardar configuración
function setConfig($key, $value) {
    $configFile = __DIR__ . '/data/config.json';
    $config = [];
    
    if (file_exists($configFile)) {
        $config = json_decode(file_get_contents($configFile), true) ?: [];
    }
    
    $config[$key] = $value;
    
    if (!is_dir(dirname($configFile))) {
        mkdir(dirname($configFile), 0755, true);
    }
    
    file_put_contents($configFile, json_encode($config, JSON_PRETTY_PRINT));
}
?>