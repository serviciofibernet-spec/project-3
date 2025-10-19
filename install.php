<?php
/**
 * TR-069 Server Installation Script
 * This script will configure your TR-069 ACS (Auto Configuration Server)
 */

session_start();

// Check if already installed
if (file_exists('config/database.php') && !isset($_GET['reinstall'])) {
    header('Location: index.php');
    exit;
}

$step = isset($_GET['step']) ? (int)$_GET['step'] : 1;
$error = '';
$success = '';

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    switch ($step) {
        case 1:
            // Database configuration
            $db_host = $_POST['db_host'] ?? '';
            $db_name = $_POST['db_name'] ?? '';
            $db_user = $_POST['db_user'] ?? '';
            $db_pass = $_POST['db_pass'] ?? '';
            $db_port = $_POST['db_port'] ?? '3306';
            
            // Test database connection
            try {
                $pdo = new PDO("mysql:host=$db_host;port=$db_port", $db_user, $db_pass);
                $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                
                // Create database if it doesn't exist
                $pdo->exec("CREATE DATABASE IF NOT EXISTS `$db_name` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
                $pdo->exec("USE `$db_name`");
                
                // Store in session for next step
                $_SESSION['db_config'] = [
                    'host' => $db_host,
                    'name' => $db_name,
                    'user' => $db_user,
                    'pass' => $db_pass,
                    'port' => $db_port
                ];
                
                $step = 2;
            } catch (Exception $e) {
                $error = "Error de conexión a la base de datos: " . $e->getMessage();
            }
            break;
            
        case 2:
            // ACS configuration
            $acs_url = $_POST['acs_url'] ?? '';
            $acs_username = $_POST['acs_username'] ?? '';
            $acs_password = $_POST['acs_password'] ?? '';
            $admin_username = $_POST['admin_username'] ?? '';
            $admin_password = $_POST['admin_password'] ?? '';
            
            if (empty($acs_url) || empty($admin_username) || empty($admin_password)) {
                $error = "Todos los campos son obligatorios";
            } else {
                $_SESSION['acs_config'] = [
                    'url' => $acs_url,
                    'username' => $acs_username,
                    'password' => $acs_password,
                    'admin_username' => $admin_username,
                    'admin_password' => password_hash($admin_password, PASSWORD_DEFAULT)
                ];
                $step = 3;
            }
            break;
            
        case 3:
            // Final installation
            if (isset($_SESSION['db_config']) && isset($_SESSION['acs_config'])) {
                try {
                    // Create config directory
                    if (!is_dir('config')) {
                        mkdir('config', 0755, true);
                    }
                    
                    // Create database config file
                    $db_config = $_SESSION['db_config'];
                    $db_config_content = "<?php\n";
                    $db_config_content .= "// Database configuration\n";
                    $db_config_content .= "define('DB_HOST', '{$db_config['host']}');\n";
                    $db_config_content .= "define('DB_NAME', '{$db_config['name']}');\n";
                    $db_config_content .= "define('DB_USER', '{$db_config['user']}');\n";
                    $db_config_content .= "define('DB_PASS', '{$db_config['pass']}');\n";
                    $db_config_content .= "define('DB_PORT', '{$db_config['port']}');\n";
                    
                    file_put_contents('config/database.php', $db_config_content);
                    
                    // Create ACS config file
                    $acs_config = $_SESSION['acs_config'];
                    $acs_config_content = "<?php\n";
                    $acs_config_content .= "// ACS configuration\n";
                    $acs_config_content .= "define('ACS_URL', '{$acs_config['url']}');\n";
                    $acs_config_content .= "define('ACS_USERNAME', '{$acs_config['username']}');\n";
                    $acs_config_content .= "define('ACS_PASSWORD', '{$acs_config['password']}');\n";
                    $acs_config_content .= "define('ADMIN_USERNAME', '{$acs_config['admin_username']}');\n";
                    $acs_config_content .= "define('ADMIN_PASSWORD', '{$acs_config['admin_password']}');\n";
                    
                    file_put_contents('config/acs.php', $acs_config_content);
                    
                    // Create database tables
                    $pdo = new PDO(
                        "mysql:host={$db_config['host']};dbname={$db_config['name']};port={$db_config['port']}", 
                        $db_config['user'], 
                        $db_config['pass']
                    );
                    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                    
                    // Read and execute SQL schema
                    $sql = file_get_contents('sql/schema.sql');
                    $pdo->exec($sql);
                    
                    // Clear session
                    unset($_SESSION['db_config']);
                    unset($_SESSION['acs_config']);
                    
                    $success = "¡Instalación completada exitosamente!";
                    $step = 4;
                } catch (Exception $e) {
                    $error = "Error durante la instalación: " . $e->getMessage();
                }
            }
            break;
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instalación TR-069 Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            padding: 40px;
            width: 100%;
            max-width: 500px;
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo h1 {
            color: #333;
            font-size: 28px;
            font-weight: 300;
        }
        
        .logo p {
            color: #666;
            margin-top: 5px;
        }
        
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        .step {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 10px;
            font-weight: bold;
            color: #999;
        }
        
        .step.active {
            background: #667eea;
            color: white;
        }
        
        .step.completed {
            background: #4caf50;
            color: white;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #333;
        }
        
        input[type="text"],
        input[type="password"],
        input[type="url"],
        input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5a67d8;
        }
        
        .error {
            background: #fee;
            color: #c53030;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #c53030;
        }
        
        .success {
            background: #f0fff4;
            color: #38a169;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #38a169;
        }
        
        .help-text {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>TR-069 Server</h1>
            <p>Configuración e Instalación</p>
        </div>
        
        <div class="step-indicator">
            <div class="step <?= $step >= 1 ? ($step > 1 ? 'completed' : 'active') : '' ?>">1</div>
            <div class="step <?= $step >= 2 ? ($step > 2 ? 'completed' : 'active') : '' ?>">2</div>
            <div class="step <?= $step >= 3 ? ($step > 3 ? 'completed' : 'active') : '' ?>">3</div>
            <div class="step <?= $step >= 4 ? 'active' : '' ?>">4</div>
        </div>
        
        <?php if ($error): ?>
            <div class="error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        
        <?php if ($success): ?>
            <div class="success"><?= htmlspecialchars($success) ?></div>
        <?php endif; ?>
        
        <?php if ($step === 1): ?>
            <h2>Paso 1: Configuración de Base de Datos</h2>
            <form method="POST">
                <div class="form-group">
                    <label for="db_host">Servidor de Base de Datos:</label>
                    <input type="text" id="db_host" name="db_host" value="localhost" required>
                    <div class="help-text">Dirección del servidor MySQL</div>
                </div>
                
                <div class="form-group">
                    <label for="db_port">Puerto:</label>
                    <input type="number" id="db_port" name="db_port" value="3306" required>
                </div>
                
                <div class="form-group">
                    <label for="db_name">Nombre de la Base de Datos:</label>
                    <input type="text" id="db_name" name="db_name" value="tr069_acs" required>
                    <div class="help-text">Se creará automáticamente si no existe</div>
                </div>
                
                <div class="form-group">
                    <label for="db_user">Usuario:</label>
                    <input type="text" id="db_user" name="db_user" required>
                </div>
                
                <div class="form-group">
                    <label for="db_pass">Contraseña:</label>
                    <input type="password" id="db_pass" name="db_pass">
                </div>
                
                <button type="submit" class="btn">Continuar</button>
            </form>
        <?php elseif ($step === 2): ?>
            <h2>Paso 2: Configuración del ACS</h2>
            <form method="POST">
                <div class="form-group">
                    <label for="acs_url">URL del ACS:</label>
                    <input type="url" id="acs_url" name="acs_url" value="http://<?= $_SERVER['HTTP_HOST'] ?>/acs.php" required>
                    <div class="help-text">URL donde los dispositivos se conectarán</div>
                </div>
                
                <div class="form-group">
                    <label for="acs_username">Usuario ACS (opcional):</label>
                    <input type="text" id="acs_username" name="acs_username">
                    <div class="help-text">Autenticación HTTP para dispositivos</div>
                </div>
                
                <div class="form-group">
                    <label for="acs_password">Contraseña ACS (opcional):</label>
                    <input type="password" id="acs_password" name="acs_password">
                </div>
                
                <div class="form-group">
                    <label for="admin_username">Usuario Administrador:</label>
                    <input type="text" id="admin_username" name="admin_username" value="admin" required>
                    <div class="help-text">Para acceder a la interfaz web</div>
                </div>
                
                <div class="form-group">
                    <label for="admin_password">Contraseña Administrador:</label>
                    <input type="password" id="admin_password" name="admin_password" required>
                </div>
                
                <button type="submit" class="btn">Continuar</button>
            </form>
        <?php elseif ($step === 3): ?>
            <h2>Paso 3: Finalizar Instalación</h2>
            <p>Se crearán los archivos de configuración y las tablas de la base de datos.</p>
            <form method="POST">
                <button type="submit" class="btn">Instalar</button>
            </form>
        <?php elseif ($step === 4): ?>
            <h2>¡Instalación Completada!</h2>
            <p>Tu servidor TR-069 ha sido configurado exitosamente.</p>
            <div style="margin: 20px 0;">
                <strong>Próximos pasos:</strong>
                <ul style="margin: 10px 0 0 20px;">
                    <li>Accede a la <a href="index.php">interfaz de administración</a></li>
                    <li>Configura tus dispositivos para conectarse a: <code><?= htmlspecialchars($_SESSION['acs_config']['url'] ?? 'URL_ACS') ?></code></li>
                    <li>Revisa los logs en el directorio <code>logs/</code></li>
                </ul>
            </div>
            <a href="index.php" class="btn" style="text-decoration: none; display: inline-block; text-align: center;">Ir al Panel de Control</a>
        <?php endif; ?>
    </div>
</body>
</html>