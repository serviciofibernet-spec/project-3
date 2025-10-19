<?php
/**
 * TR-069 ACS Configuration File
 * Rename this file to config.php and update with your settings
 */

return [
    // Database Configuration
    'db' => [
        'host' => 'localhost',
        'port' => 3306,
        'database' => 'tr069_acs',
        'username' => 'root',
        'password' => '',
        'charset' => 'utf8mb4'
    ],
    
    // ACS Server Configuration
    'acs' => [
        'url' => 'http://localhost/acs.php',
        'username' => 'acs_user',
        'password' => 'acs_pass',
        'inform_interval' => 300, // seconds
        'session_timeout' => 300
    ],
    
    // Security
    'security' => [
        'session_secret' => 'change_this_to_random_string',
        'enable_https' => false,
        'require_device_auth' => true
    ],
    
    // Logging
    'logging' => [
        'enabled' => true,
        'log_path' => __DIR__ . '/logs',
        'log_level' => 'info', // debug, info, warning, error
        'log_requests' => true
    ],
    
    // Application
    'app' => [
        'timezone' => 'UTC',
        'debug' => false
    ]
];
