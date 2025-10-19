<?php
declare(strict_types=1);

namespace App;

final class Logger
{
    public static function log(string $level, string $message, array $context = []): void
    {
        $level = strtolower($level);
        $ts = (new \DateTimeImmutable('now'))
            ->setTimezone(new \DateTimeZone('UTC'))
            ->format('Y-m-d H:i:s');
        $line = sprintf('[%s] %s: %s %s', $ts, strtoupper($level), $message, $context ? json_encode($context, JSON_UNESCAPED_SLASHES) : '');

        $file = Config::rootPath('storage/logs/acs.log');
        @file_put_contents($file, $line . PHP_EOL, FILE_APPEND);
        // Also to PHP error log for convenience
        error_log($line);
    }

    public static function info(string $message, array $context = []): void
    {
        self::log('info', $message, $context);
    }

    public static function error(string $message, array $context = []): void
    {
        self::log('error', $message, $context);
    }

    public static function debug(string $message, array $context = []): void
    {
        self::log('debug', $message, $context);
    }
}
