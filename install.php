<?php
declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '1');

$configTemplatePath = __DIR__ . '/config/config.php.template';
$configPath = __DIR__ . '/config/config.php';
$schemaPath = __DIR__ . '/schema.sql';

function h(?string $s): string { return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }

$errors = [];
$success = false;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    $dbHost = trim($_POST['db_host'] ?? 'localhost');
    $dbPort = (int)($_POST['db_port'] ?? 3306);
    $dbName = trim($_POST['db_name'] ?? 'tr069');
    $dbUser = trim($_POST['db_user'] ?? 'root');
    $dbPass = (string)($_POST['db_pass'] ?? '');
    $timezone = trim($_POST['timezone'] ?? 'UTC');
    $acsUser = trim($_POST['acs_user'] ?? '');
    $acsPass = (string)($_POST['acs_pass'] ?? '');

    if ($dbHost === '' || $dbName === '' || $dbUser === '') {
        $errors[] = 'DB host, name and user are required.';
    }

    if (!$errors) {
        try {
            // Connect without DB to create it if missing
            $dsnNoDb = sprintf('mysql:host=%s;port=%d;charset=utf8mb4', $dbHost, $dbPort);
            $pdo = new PDO($dsnNoDb, $dbUser, $dbPass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
            $pdo->exec('CREATE DATABASE IF NOT EXISTS `'.str_replace('`','``',$dbName).'` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
            $pdo = null;

            // Connect to the chosen DB
            $dsn = sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4', $dbHost, $dbPort, $dbName);
            $pdo = new PDO($dsn, $dbUser, $dbPass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);

            // Run schema
            if (!is_file($schemaPath)) {
                throw new RuntimeException('Schema file not found: ' . $schemaPath);
            }
            $sql = file_get_contents($schemaPath);
            if ($sql === false) {
                throw new RuntimeException('Failed to read schema file.');
            }
            // Execute multiple statements safely
            foreach (array_filter(array_map('trim', explode(';', $sql))) as $statement) {
                if ($statement !== '') {
                    $pdo->exec($statement);
                }
            }

            // Write config file
            $config = [
                'db' => [
                    'host' => $dbHost,
                    'port' => $dbPort,
                    'name' => $dbName,
                    'user' => $dbUser,
                    'pass' => $dbPass,
                    'charset' => 'utf8mb4',
                ],
                'acs' => [
                    'username' => $acsUser !== '' ? $acsUser : null,
                    'password' => $acsUser !== '' ? $acsPass : null,
                    'timezone' => $timezone !== '' ? $timezone : 'UTC',
                ],
            ];

            $configPhp = "<?php\nreturn " . var_export($config, true) . ";\n";
            if (@file_put_contents($configPath, $configPhp) === false) {
                throw new RuntimeException('Failed to write config file to ' . $configPath . '. Check permissions.');
            }

            $success = true;
        } catch (Throwable $t) {
            $errors[] = $t->getMessage();
        }
    }
}

$installed = is_file($configPath);
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Instalador TR-069 ACS (PHP)</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; margin: 2rem; }
    .container { max-width: 820px; margin: 0 auto; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1.25rem; }
    .row { display: grid; grid-template-columns: 1fr 2fr; gap: 0.75rem 1rem; align-items: center; }
    label { font-weight: 600; }
    input[type=text], input[type=number], input[type=password] { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 6px; }
    .actions { margin-top: 1rem; }
    button { background: #2b62ff; color: white; border: 0; border-radius: 6px; padding: 0.6rem 1rem; cursor: pointer; }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert.error { background: #ffecec; color: #b30000; border: 1px solid #ffb3b3; }
    .alert.ok { background: #ecfff1; color: #0a7a2f; border: 1px solid #a2f0c4; }
    small { color: #666; }
  </style>
</head>
<body>
<div class="container">
  <h1>Instalar servidor TR-069 (ACS)</h1>

  <?php if ($success): ?>
    <div class="alert ok">Instalación completada. Archivo de configuración creado. <a href="index.php">Ir al inicio</a></div>
  <?php endif; ?>

  <?php if ($errors): ?>
    <div class="alert error">
      <strong>Errores:</strong>
      <ul>
        <?php foreach ($errors as $e): ?>
          <li><?= h($e) ?></li>
        <?php endforeach; ?>
      </ul>
    </div>
  <?php endif; ?>

  <div class="card">
    <form method="post">
      <div class="row">
        <label for="db_host">DB Host</label>
        <input id="db_host" name="db_host" type="text" value="<?= h($_POST['db_host'] ?? 'localhost') ?>" required />

        <label for="db_port">DB Puerto</label>
        <input id="db_port" name="db_port" type="number" value="<?= h($_POST['db_port'] ?? '3306') ?>" required />

        <label for="db_name">DB Nombre</label>
        <input id="db_name" name="db_name" type="text" value="<?= h($_POST['db_name'] ?? 'tr069') ?>" required />

        <label for="db_user">DB Usuario</label>
        <input id="db_user" name="db_user" type="text" value="<?= h($_POST['db_user'] ?? 'root') ?>" required />

        <label for="db_pass">DB Password</label>
        <input id="db_pass" name="db_pass" type="password" value="<?= h($_POST['db_pass'] ?? '') ?>" />

        <label for="timezone">Zona horaria</label>
        <input id="timezone" name="timezone" type="text" value="<?= h($_POST['timezone'] ?? 'UTC') ?>" />
        <small>Ejemplo: Europe/Madrid, America/Mexico_City</small>

        <label for="acs_user">ACS Usuario (opcional)</label>
        <input id="acs_user" name="acs_user" type="text" value="<?= h($_POST['acs_user'] ?? '') ?>" />

        <label for="acs_pass">ACS Password (opcional)</label>
        <input id="acs_pass" name="acs_pass" type="password" value="<?= h($_POST['acs_pass'] ?? '') ?>" />
      </div>

      <div class="actions">
        <button type="submit">Instalar</button>
        <?php if ($installed): ?>
          <small style="margin-left: 0.5rem;">Ya existe configuración en <code>config/config.php</code>. Al instalar se sobrescribirá.</small>
        <?php endif; ?>
      </div>
    </form>
  </div>

  <p style="margin-top: 1rem; color:#555;">Tras instalar, envía <strong>POST</strong> SOAP de tu CPE a <code>acs.php</code>.</p>
</div>
</body>
</html>
