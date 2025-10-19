<?php
namespace App;

class Config {
    public static function env(string $key, ?string $default = null): string {
        $val = getenv($key);
        return $val === false ? ($default ?? '') : $val;
    }

    public static function db(): array {
        return [
            'host' => self::env('MYSQL_HOST', 'localhost'),
            'port' => (int) self::env('MYSQL_PORT', '3306'),
            'user' => self::env('MYSQL_USER', 'root'),
            'pass' => self::env('MYSQL_PASSWORD', ''),
            'db'   => self::env('MYSQL_DB', 'acs'),
        ];
    }

    public static function genieAcsNbi(): string {
        return self::env('GENIEACS_NBI_URL', 'http://localhost:7557');
    }
}
