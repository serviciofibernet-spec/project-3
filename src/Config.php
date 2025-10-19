<?php
declare(strict_types=1);

namespace App;

final class Config
{
    /** @var array<string, mixed> */
    private static array $config = [];

    private static string $projectRoot = '';

    /**
     * @param array<string, mixed> $config
     */
    public static function init(array $config, string $projectRoot): void
    {
        self::$config = $config;
        self::$projectRoot = rtrim($projectRoot, '/');
    }

    /**
     * @return mixed|null
     */
    public static function get(string $key, $default = null)
    {
        $segments = explode('.', $key);
        $value = self::$config;
        foreach ($segments as $segment) {
            if (!is_array($value) || !array_key_exists($segment, $value)) {
                return $default;
            }
            $value = $value[$segment];
        }
        return $value;
    }

    public static function rootPath(string $path = ''): string
    {
        if ($path === '') {
            return self::$projectRoot;
        }
        return self::$projectRoot . '/' . ltrim($path, '/');
    }
}
