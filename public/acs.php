<?php
declare(strict_types=1);

require dirname(__DIR__) . '/src/bootstrap.php';

use App\CWMP\Server;
use App\Logger;

try {
    (new Server())->handleHttp();
} catch (Throwable $e) {
    Logger::error('Fatal error in ACS', ['error' => $e->getMessage()]);
    header('HTTP/1.1 500 Internal Server Error');
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Internal server error';
}