<?php
/**
 * Instalador del Servidor TR-069
 * Este script configura la base de datos y los parámetros iniciales del servidor
 */

session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

$step = isset($_GET['step']) ? (int)$_GET['step'] : 1;
$message = '';
$error = '';

// Procesar formulario de configuración
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($step === 1) {
        // Validar conexión a base de datos
        $db_host = $_POST['db_host'];
        $db_port = $_POST['db_port'];
        $db_name = $_POST['db_name'];
        $db_user = $_POST['db_user'];
        $db_pass = $_POST['db_pass'];
        
        try {
            $dsn = "mysql:host=$db_host;port=$db_port;charset=utf8mb4";
            $pdo = new PDO($dsn, $db_user, $db_pass);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            
            // Crear base de datos si no existe
            $pdo->exec("CREATE DATABASE IF NOT EXISTS `$db_name` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            $pdo->exec("USE `$db_name`");
            
            // Guardar configuración en sesión
            $_SESSION['db_config'] = [
                'host' => $db_host,
                'port' => $db_port,
                'name' => $db_name,
                'user' => $db_user,
                'pass' => $db_pass
            ];
            
            header('Location: install.php?step=2');
            exit;
        } catch (PDOException $e) {
            $error = "Error de conexión: " . $e->getMessage();
        }
    } elseif ($step === 2) {
        // Configuración del servidor TR-069
        $_SESSION['server_config'] = [
            'server_url' => $_POST['server_url'],
            'server_port' => $_POST['server_port'],
            'acs_path' => $_POST['acs_path'],
            'auth_enabled' => isset($_POST['auth_enabled']),
            'auth_user' => $_POST['auth_user'],
            'auth_pass' => $_POST['auth_pass'],
            'session_timeout' => $_POST['session_timeout'],
            'log_level' => $_POST['log_level']
        ];
        
        header('Location: install.php?step=3');
        exit;
    } elseif ($step === 3) {
        // Configuración del administrador
        $_SESSION['admin_config'] = [
            'admin_user' => $_POST['admin_user'],
            'admin_pass' => password_hash($_POST['admin_pass'], PASSWORD_DEFAULT),
            'admin_email' => $_POST['admin_email'],
            'timezone' => $_POST['timezone']
        ];
        
        header('Location: install.php?step=4');
        exit;
    } elseif ($step === 4) {
        // Instalación final
        try {
            // Conectar a la base de datos
            $db = $_SESSION['db_config'];
            $dsn = "mysql:host={$db['host']};port={$db['port']};dbname={$db['name']};charset=utf8mb4";
            $pdo = new PDO($dsn, $db['user'], $db['pass']);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            
            // Crear tablas
            $sql = file_get_contents(__DIR__ . '/database/schema.sql');
            $pdo->exec($sql);
            
            // Insertar configuración inicial
            $stmt = $pdo->prepare("INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)");
            foreach ($_SESSION['server_config'] as $key => $value) {
                $stmt->execute([$key, $value]);
            }
            
            // Crear usuario administrador
            $admin = $_SESSION['admin_config'];
            $stmt = $pdo->prepare("INSERT INTO users (username, password, email, role, created_at) VALUES (?, ?, ?, 'admin', NOW())");
            $stmt->execute([$admin['admin_user'], $admin['admin_pass'], $admin['admin_email']]);
            
            // Generar archivo de configuración
            $config_content = "<?php\n\n";
            $config_content .= "// Configuración de Base de Datos\n";
            $config_content .= "define('DB_HOST', '{$db['host']}');\n";
            $config_content .= "define('DB_PORT', '{$db['port']}');\n";
            $config_content .= "define('DB_NAME', '{$db['name']}');\n";
            $config_content .= "define('DB_USER', '{$db['user']}');\n";
            $config_content .= "define('DB_PASS', '{$db['pass']}');\n\n";
            
            $config_content .= "// Configuración del Servidor TR-069\n";
            foreach ($_SESSION['server_config'] as $key => $value) {
                $key_upper = strtoupper($key);
                if (is_bool($value)) {
                    $value = $value ? 'true' : 'false';
                } else {
                    $value = "'$value'";
                }
                $config_content .= "define('$key_upper', $value);\n";
            }
            
            $config_content .= "\n// Configuración General\n";
            $config_content .= "define('TIMEZONE', '{$admin['timezone']}');\n";
            $config_content .= "define('LOG_PATH', __DIR__ . '/../logs/');\n";
            $config_content .= "define('UPLOAD_PATH', __DIR__ . '/../uploads/');\n";
            
            file_put_contents(__DIR__ . '/config/config.php', $config_content);
            
            // Limpiar sesión
            session_destroy();
            
            $message = "Instalación completada exitosamente!";
            $step = 5;
        } catch (Exception $e) {
            $error = "Error durante la instalación: " . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instalación - Servidor TR-069</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .progress {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }
        
        .progress::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e0e0e0;
            z-index: 0;
        }
        
        .progress-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 1;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .step-circle.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .step-circle.completed {
            background: #4caf50;
            color: white;
        }
        
        .step-label {
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        input[type="text"],
        input[type="password"],
        input[type="email"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
        }
        
        input[type="checkbox"] {
            margin-right: 10px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
            margin-right: 10px;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-error {
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
        }
        
        .alert-success {
            background: #efe;
            border: 1px solid #cfc;
            color: #3c3;
        }
        
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        
        .info-box h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .info-box p {
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .button-group {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Instalación del Servidor TR-069</h1>
        <p class="subtitle">Configure su servidor CWMP en unos simples pasos</p>
        
        <div class="progress">
            <div class="progress-step">
                <div class="step-circle <?= $step >= 1 ? ($step > 1 ? 'completed' : 'active') : '' ?>">1</div>
                <span class="step-label">Base de Datos</span>
            </div>
            <div class="progress-step">
                <div class="step-circle <?= $step >= 2 ? ($step > 2 ? 'completed' : 'active') : '' ?>">2</div>
                <span class="step-label">Servidor</span>
            </div>
            <div class="progress-step">
                <div class="step-circle <?= $step >= 3 ? ($step > 3 ? 'completed' : 'active') : '' ?>">3</div>
                <span class="step-label">Administrador</span>
            </div>
            <div class="progress-step">
                <div class="step-circle <?= $step >= 4 ? ($step > 4 ? 'completed' : 'active') : '' ?>">4</div>
                <span class="step-label">Finalizar</span>
            </div>
        </div>
        
        <?php if ($error): ?>
            <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        
        <?php if ($message): ?>
            <div class="alert alert-success"><?= htmlspecialchars($message) ?></div>
        <?php endif; ?>
        
        <?php if ($step === 1): ?>
            <form method="POST">
                <div class="info-box">
                    <h3>📊 Configuración de Base de Datos</h3>
                    <p>Configure la conexión a MySQL/MariaDB. La base de datos será creada automáticamente si no existe.</p>
                </div>
                
                <div class="form-group">
                    <label for="db_host">Host de Base de Datos:</label>
                    <input type="text" id="db_host" name="db_host" value="localhost" required>
                </div>
                
                <div class="form-group">
                    <label for="db_port">Puerto:</label>
                    <input type="number" id="db_port" name="db_port" value="3306" required>
                </div>
                
                <div class="form-group">
                    <label for="db_name">Nombre de Base de Datos:</label>
                    <input type="text" id="db_name" name="db_name" value="tr069_server" required>
                </div>
                
                <div class="form-group">
                    <label for="db_user">Usuario:</label>
                    <input type="text" id="db_user" name="db_user" required>
                </div>
                
                <div class="form-group">
                    <label for="db_pass">Contraseña:</label>
                    <input type="password" id="db_pass" name="db_pass">
                </div>
                
                <button type="submit" class="btn">Siguiente →</button>
            </form>
            
        <?php elseif ($step === 2): ?>
            <form method="POST">
                <div class="info-box">
                    <h3>⚙️ Configuración del Servidor TR-069</h3>
                    <p>Configure los parámetros del servidor ACS (Auto Configuration Server) para la comunicación con los dispositivos CPE.</p>
                </div>
                
                <div class="form-group">
                    <label for="server_url">URL del Servidor (sin http://):</label>
                    <input type="text" id="server_url" name="server_url" value="<?= $_SERVER['HTTP_HOST'] ?? 'localhost' ?>" required>
                </div>
                
                <div class="form-group">
                    <label for="server_port">Puerto del Servidor:</label>
                    <input type="number" id="server_port" name="server_port" value="8080" required>
                </div>
                
                <div class="form-group">
                    <label for="acs_path">Ruta ACS (path):</label>
                    <input type="text" id="acs_path" name="acs_path" value="/acs" required>
                </div>
                
                <div class="form-group">
                    <div class="checkbox-group">
                        <input type="checkbox" id="auth_enabled" name="auth_enabled" checked>
                        <label for="auth_enabled">Habilitar autenticación HTTP</label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="auth_user">Usuario de Autenticación HTTP:</label>
                    <input type="text" id="auth_user" name="auth_user" value="acs">
                </div>
                
                <div class="form-group">
                    <label for="auth_pass">Contraseña de Autenticación HTTP:</label>
                    <input type="password" id="auth_pass" name="auth_pass" value="acs123">
                </div>
                
                <div class="form-group">
                    <label for="session_timeout">Timeout de Sesión (segundos):</label>
                    <input type="number" id="session_timeout" name="session_timeout" value="300" required>
                </div>
                
                <div class="form-group">
                    <label for="log_level">Nivel de Log:</label>
                    <select id="log_level" name="log_level">
                        <option value="ERROR">ERROR - Solo errores</option>
                        <option value="WARNING">WARNING - Advertencias y errores</option>
                        <option value="INFO" selected>INFO - Información general</option>
                        <option value="DEBUG">DEBUG - Información detallada</option>
                    </select>
                </div>
                
                <div class="button-group">
                    <a href="install.php?step=1" class="btn btn-secondary">← Anterior</a>
                    <button type="submit" class="btn">Siguiente →</button>
                </div>
            </form>
            
        <?php elseif ($step === 3): ?>
            <form method="POST">
                <div class="info-box">
                    <h3>👤 Cuenta de Administrador</h3>
                    <p>Configure la cuenta de administrador para acceder al panel de control del servidor TR-069.</p>
                </div>
                
                <div class="form-group">
                    <label for="admin_user">Nombre de Usuario:</label>
                    <input type="text" id="admin_user" name="admin_user" value="admin" required>
                </div>
                
                <div class="form-group">
                    <label for="admin_pass">Contraseña:</label>
                    <input type="password" id="admin_pass" name="admin_pass" required minlength="6">
                </div>
                
                <div class="form-group">
                    <label for="admin_email">Email:</label>
                    <input type="email" id="admin_email" name="admin_email" required>
                </div>
                
                <div class="form-group">
                    <label for="timezone">Zona Horaria:</label>
                    <select id="timezone" name="timezone">
                        <option value="America/New_York">America/New_York</option>
                        <option value="America/Chicago">America/Chicago</option>
                        <option value="America/Los_Angeles">America/Los_Angeles</option>
                        <option value="America/Mexico_City" selected>America/Mexico_City</option>
                        <option value="America/Argentina/Buenos_Aires">America/Argentina/Buenos_Aires</option>
                        <option value="America/Sao_Paulo">America/Sao_Paulo</option>
                        <option value="Europe/London">Europe/London</option>
                        <option value="Europe/Madrid">Europe/Madrid</option>
                        <option value="Europe/Paris">Europe/Paris</option>
                        <option value="Asia/Tokyo">Asia/Tokyo</option>
                        <option value="Asia/Shanghai">Asia/Shanghai</option>
                    </select>
                </div>
                
                <div class="button-group">
                    <a href="install.php?step=2" class="btn btn-secondary">← Anterior</a>
                    <button type="submit" class="btn">Siguiente →</button>
                </div>
            </form>
            
        <?php elseif ($step === 4): ?>
            <form method="POST">
                <div class="info-box">
                    <h3>🎯 Finalizar Instalación</h3>
                    <p>Revise la configuración y haga clic en "Instalar" para completar la instalación.</p>
                </div>
                
                <h3>Resumen de Configuración:</h3>
                <ul style="color: #666; line-height: 1.8; margin: 20px 0;">
                    <li>✅ Base de datos configurada</li>
                    <li>✅ Servidor TR-069 configurado</li>
                    <li>✅ Cuenta de administrador creada</li>
                </ul>
                
                <p style="color: #666; margin: 20px 0;">
                    Al hacer clic en "Instalar", se crearán las tablas de base de datos y se generará el archivo de configuración.
                </p>
                
                <div class="button-group">
                    <a href="install.php?step=3" class="btn btn-secondary">← Anterior</a>
                    <button type="submit" class="btn">🚀 Instalar</button>
                </div>
            </form>
            
        <?php elseif ($step === 5): ?>
            <div style="text-align: center;">
                <div style="font-size: 72px; margin-bottom: 20px;">✅</div>
                <h2 style="color: #4caf50; margin-bottom: 20px;">¡Instalación Completada!</h2>
                
                <div class="info-box" style="text-align: left;">
                    <h3>Próximos Pasos:</h3>
                    <ol style="color: #666; line-height: 1.8; margin-left: 20px;">
                        <li>Elimine el archivo <code>install.php</code> por seguridad</li>
                        <li>Acceda al panel de administración en <a href="/admin">./admin</a></li>
                        <li>Configure sus dispositivos CPE con la URL del ACS</li>
                        <li>Revise los logs en la carpeta <code>./logs</code></li>
                    </ol>
                </div>
                
                <div style="margin-top: 30px;">
                    <a href="public/index.php" class="btn">Ir al Panel de Administración →</a>
                </div>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>