<?php
declare(strict_types=1);

$root = dirname(__DIR__);
require $root . '/src/bootstrap.php';

use App\Logger;

$errors = [];
$success = false;

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    $dbHost = trim($_POST['db_host'] ?? '127.0.0.1');
    $dbPort = (int) ($_POST['db_port'] ?? 3306);
    $dbName = trim($_POST['db_name'] ?? 'acs');
    $dbUser = trim($_POST['db_user'] ?? 'root');
    $dbPass = (string) ($_POST['db_pass'] ?? '');

    $authEnabled = isset($_POST['auth_enabled']) ? true : false;
    $authUser = trim($_POST['auth_user'] ?? '');
    $authPass = (string) ($_POST['auth_pass'] ?? '');

    if ($authEnabled && ($authUser === '' || $authPass === '')) {
        $errors[] = 'Si activa autenticación, usuario y contraseña son obligatorios.';
    }

    // Try DB connection
    try {
        $dsnNoDb = sprintf('mysql:host=%s;port=%d;charset=utf8mb4', $dbHost, $dbPort);
        $pdo = new PDO($dsnNoDb, $dbUser, $dbPass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        // Create database if not exists
        $pdo->exec('CREATE DATABASE IF NOT EXISTS `'.$dbName.'` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci');
        $pdo = null;

        // Connect to DB and run schema
        $dsn = sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4', $dbHost, $dbPort, $dbName);
        $pdo2 = new PDO($dsn, $dbUser, $dbPass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $schema = file_get_contents($root . '/config/schema.sql') ?: '';
        if ($schema === '') {
            throw new RuntimeException('No se pudo leer schema.sql');
        }
        $pdo2->exec($schema);

        // Write config.php
        $configText = "<?php\nreturn [\n    'db' => [\n        'host' => '" . addslashes($dbHost) . "',\n        'port' => " . (int) $dbPort . ",\n        'name' => '" . addslashes($dbName) . "',\n        'user' => '" . addslashes($dbUser) . "',\n        'pass' => '" . addslashes($dbPass) . "',\n        'charset' => 'utf8mb4',\n    ],\n    'auth' => [\n        'enabled' => " . ($authEnabled ? 'true' : 'false') . ",\n        'user' => '" . addslashes($authUser) . "',\n        'pass' => '" . addslashes($authPass) . "',\n    ],\n];\n";
        if (!is_dir($root . '/config')) {
            @mkdir($root . '/config', 0775, true);
        }
        if (file_put_contents($root . '/config/config.php', $configText) === false) {
            throw new RuntimeException('No se pudo escribir config/config.php');
        }

        $success = true;
    } catch (Throwable $e) {
        $errors[] = $e->getMessage();
        Logger::error('Install error', ['error' => $e->getMessage()]);
    }
}

?><!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Instalación ACS TR-069</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;margin:2rem;}
.container{max-width:720px;margin:0 auto}
.card{border:1px solid #ddd;border-radius:8px;padding:1rem 1.25rem}
label{display:block;margin:.5rem 0 .25rem}
input[type=text],input[type=number],input[type=password]{width:100%;padding:.5rem;border:1px solid #ccc;border-radius:6px}
button{background:#2563eb;color:white;border:none;border-radius:6px;padding:.6rem 1rem;margin-top:1rem;cursor:pointer}
.alert{padding:.75rem 1rem;border-radius:6px;margin-bottom:1rem}
.alert.error{background:#fee2e2;color:#991b1b;border:1px solid #fecaca}
.alert.success{background:#dcfce7;color:#166534;border:1px solid #bbf7d0}
fieldset{border:1px solid #e5e7eb;border-radius:8px;margin-top:1rem}
legend{padding:0 .5rem;color:#374151}
.small{color:#6b7280;font-size:.9rem}
</style>
</head>
<body>
<div class="container">
  <h1>Instalación ACS TR-069</h1>
  <p class="small">Este instalador creará la base de datos y guardará la configuración en <code>config/config.php</code>.</p>

  <?php if ($success): ?>
    <div class="alert success">Instalación completada. Por favor, borre <code>public/install.php</code> por seguridad.</div>
    <div class="card">
      <p>Endpoint ACS listo:</p>
      <ul>
        <li>URL ACS: <code><?php echo htmlspecialchars((($_SERVER['HTTPS'] ?? 'off') === 'on' ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? 'localhost') . dirname($_SERVER['REQUEST_URI']) . '/acs.php', ENT_QUOTES); ?></code></li>
      </ul>
    </div>
  <?php endif; ?>

  <?php if (!empty($errors)): ?>
    <div class="alert error">
      <?php foreach ($errors as $err): ?>
        <div>• <?php echo htmlspecialchars($err, ENT_QUOTES); ?></div>
      <?php endforeach; ?>
    </div>
  <?php endif; ?>

  <form method="post" class="card">
    <h2>Base de datos MySQL</h2>
    <label>Host</label>
    <input type="text" name="db_host" value="<?php echo htmlspecialchars($_POST['db_host'] ?? '127.0.0.1', ENT_QUOTES); ?>" required />
    <label>Puerto</label>
    <input type="number" name="db_port" value="<?php echo htmlspecialchars($_POST['db_port'] ?? '3306', ENT_QUOTES); ?>" required />
    <label>Nombre BD</label>
    <input type="text" name="db_name" value="<?php echo htmlspecialchars($_POST['db_name'] ?? 'acs', ENT_QUOTES); ?>" required />
    <label>Usuario</label>
    <input type="text" name="db_user" value="<?php echo htmlspecialchars($_POST['db_user'] ?? 'root', ENT_QUOTES); ?>" required />
    <label>Contraseña</label>
    <input type="password" name="db_pass" value="<?php echo htmlspecialchars($_POST['db_pass'] ?? '', ENT_QUOTES); ?>" />

    <fieldset>
      <legend>Autenticación HTTP básica (opcional)</legend>
      <label><input type="checkbox" name="auth_enabled" <?php echo isset($_POST['auth_enabled']) ? 'checked' : ''; ?> /> Activar</label>
      <label>Usuario</label>
      <input type="text" name="auth_user" value="<?php echo htmlspecialchars($_POST['auth_user'] ?? '', ENT_QUOTES); ?>" />
      <label>Contraseña</label>
      <input type="password" name="auth_pass" value="<?php echo htmlspecialchars($_POST['auth_pass'] ?? '', ENT_QUOTES); ?>" />
    </fieldset>

    <button type="submit">Instalar</button>
  </form>
</div>
</body>
</html>
