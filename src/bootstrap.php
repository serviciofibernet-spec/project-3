<?php
declare(strict_types=1);

// Bootstrap for ACS

// Set strict error reporting during development; you can lower this in production
error_reporting(E_ALL & ~E_NOTICE);
ini_set('display_errors', '0');
ini_set('log_errors', '1');

// Ensure multibyte-safe defaults
if (function_exists('mb_internal_encoding')) {
    mb_internal_encoding('UTF-8');
}

// Project root
$__ACS_ROOT = dirname(__DIR__);

// Autoloader for App\\ namespace
spl_autoload_register(function (string $class): void {
    $prefix = 'App\\';
    $baseDir = __DIR__ . DIRECTORY_SEPARATOR;

    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }

    $relativeClass = substr($class, $len);
    $file = $baseDir . str_replace('\\', DIRECTORY_SEPARATOR, $relativeClass) . '.php';

    if (is_file($file)) {
        require $file;
    }
});

// Load config
$configPath = $__ACS_ROOT . '/config/config.php';
if (is_file($configPath)) {
    /** @psalm-suppress UnresolvableInclude */
    $config = require $configPath;
    if (is_array($config)) {
        App\Config::init($config, $__ACS_ROOT);
    }
}

// Ensure log dir exists
$logDir = $__ACS_ROOT . '/storage/logs';
if (!is_dir($logDir)) {
    @mkdir($logDir, 0775, true);
}
