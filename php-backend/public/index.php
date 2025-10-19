<?php
declare(strict_types=1);

use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use Slim\Factory\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

$app = AppFactory::create();
$app->addBodyParsingMiddleware();

// Bootstrap DB schema on startup (idempotent)
require_once __DIR__ . '/../src/Config.php';
require_once __DIR__ . '/../src/Db.php';
require_once __DIR__ . '/../scripts/bootstrap.php';

$app->get('/health', function(Request $req, Response $res) {
    $res->getBody()->write(json_encode(['ok' => true]));
    return $res->withHeader('Content-Type', 'application/json');
});

// Include routes
(require __DIR__ . '/../src/routes.php')($app);

$app->run();
