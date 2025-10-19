<?php
declare(strict_types=1);

namespace TR069;

final class Config
{
    private static ?array $cached = null;

    public static function isInstalled(): bool
    {
        return is_file(__DIR__ . '/../config/config.php');
    }

    public static function load(): array
    {
        if (self::$cached !== null) {
            return self::$cached;
        }
        $configPath = __DIR__ . '/../config/config.php';
        if (is_file($configPath)) {
            $config = require $configPath;
        } else {
            $config = require __DIR__ . '/../config/config.php.template';
        }
        if (!is_array($config)) {
            $config = [];
        }
        self::$cached = $config;
        if (!empty($config['acs']['timezone'])) {
            date_default_timezone_set((string)$config['acs']['timezone']);
        } else {
            date_default_timezone_set('UTC');
        }
        return self::$cached;
    }
}
