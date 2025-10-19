<?php
declare(strict_types=1);

require __DIR__ . '/src/Config.php';
require __DIR__ . '/src/Database.php';

use TR069\Config;
use TR069\Database;

if (!Config::isInstalled()) {
    header('Location: install.php');
    exit;
}

$config = Config::load();
$deviceCount = null;
try {
    $pdo = Database::getConnection();
    $stmt = $pdo->query('SELECT COUNT(*) AS c FROM devices');
    $row = $stmt->fetch();
    $deviceCount = (int)($row['c'] ?? 0);
} catch (Throwable $t) {
    $deviceCount = null;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TR-069 ACS</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; margin: 2rem; }
    .container { max-width: 820px; margin: 0 auto; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1.25rem; }
    a.button { display: inline-block; background: #2b62ff; color: white; padding: 0.5rem 0.8rem; border-radius: 6px; text-decoration: none; }
    code { background: #f6f6f6; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
<div class="container">
  <h1>Servidor TR-069 (ACS)</h1>
  <div class="card">
    <p>El endpoint del ACS está en <code>acs.php</code>.</p>
    <?php if ($deviceCount !== null): ?>
      <p>Dispositivos registrados: <strong><?= $deviceCount ?></strong></p>
    <?php else: ?>
      <p>No se pudo conectar a la base de datos.</p>
    <?php endif; ?>
    <p><a class="button" href="install.php">Reconfigurar</a></p>
  </div>
</div>
</body>
</html>
