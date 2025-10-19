<?php
/**
 * TR-069 ACS Installation Script
 * This script will guide you through the installation process
 */

session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Check if already installed
if (file_exists('config.php') && !isset($_GET['reinstall'])) {
    if (!isset($_POST['confirm_reinstall'])) {
        ?>
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TR-069 ACS - Ya Instalado</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }
                .container {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    max-width: 600px;
                    width: 100%;
                    padding: 40px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }
                .btn {
                    display: inline-block;
                    padding: 12px 30px;
                    margin: 10px 5px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    text-decoration: none;
                    transition: all 0.3s;
                }
                .btn-primary {
                    background: #667eea;
                    color: white;
                }
                .btn-danger {
                    background: #dc3545;
                    color: white;
                }
                .btn:hover {
                    opacity: 0.9;
                    transform: translateY(-2px);
                }
                .text-center {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 TR-069 ACS Ya Está Instalado</h1>
                <div class="warning">
                    <strong>⚠️ Advertencia:</strong> La aplicación ya está instalada. Si continúas, se sobrescribirá la configuración actual y se perderán todos los datos.
                </div>
                <div class="text-center">
                    <a href="index.php" class="btn btn-primary">Ir al Panel de Control</a>
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="confirm_reinstall" value="1">
                        <button type="submit" class="btn btn-danger" onclick="return confirm('¿Estás seguro? Se perderán todos los datos.');">Reinstalar</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        <?php
        exit;
    }
}

// Handle installation
$step = isset($_POST['step']) ? (int)$_POST['step'] : 1;
$errors = [];
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $step === 2) {
    // Validate input
    $db_host = trim($_POST['db_host'] ?? '');
    $db_port = trim($_POST['db_port'] ?? '3306');
    $db_name = trim($_POST['db_name'] ?? '');
    $db_user = trim($_POST['db_user'] ?? '');
    $db_pass = $_POST['db_pass'] ?? '';
    $acs_url = trim($_POST['acs_url'] ?? '');
    $acs_user = trim($_POST['acs_user'] ?? '');
    $acs_pass = $_POST['acs_pass'] ?? '';
    $admin_user = trim($_POST['admin_user'] ?? 'admin');
    $admin_pass = $_POST['admin_pass'] ?? '';
    $admin_email = trim($_POST['admin_email'] ?? '');
    
    // Validation
    if (empty($db_host)) $errors[] = "El host de la base de datos es requerido";
    if (empty($db_name)) $errors[] = "El nombre de la base de datos es requerido";
    if (empty($db_user)) $errors[] = "El usuario de la base de datos es requerido";
    if (empty($acs_url)) $errors[] = "La URL del ACS es requerida";
    if (empty($acs_user)) $errors[] = "El usuario del ACS es requerido";
    if (empty($acs_pass)) $errors[] = "La contraseña del ACS es requerida";
    if (empty($admin_pass)) $errors[] = "La contraseña del administrador es requerida";
    
    if (empty($errors)) {
        // Test database connection
        try {
            $dsn = "mysql:host={$db_host};port={$db_port};charset=utf8mb4";
            $pdo = new PDO($dsn, $db_user, $db_pass);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            
            // Create database if not exists
            $pdo->exec("CREATE DATABASE IF NOT EXISTS `{$db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            $pdo->exec("USE `{$db_name}`");
            
            // Import schema
            $schema = file_get_contents(__DIR__ . '/schema.sql');
            $statements = array_filter(array_map('trim', explode(';', $schema)));
            
            foreach ($statements as $statement) {
                if (!empty($statement) && !preg_match('/^--/', $statement)) {
                    $pdo->exec($statement);
                }
            }
            
            // Update admin user
            $hashed_password = password_hash($admin_pass, PASSWORD_BCRYPT);
            $stmt = $pdo->prepare("UPDATE users SET username = ?, password = ?, email = ? WHERE role = 'admin' LIMIT 1");
            $stmt->execute([$admin_user, $hashed_password, $admin_email]);
            
            // Create config.php
            $config = [
                'db' => [
                    'host' => $db_host,
                    'port' => (int)$db_port,
                    'database' => $db_name,
                    'username' => $db_user,
                    'password' => $db_pass,
                    'charset' => 'utf8mb4'
                ],
                'acs' => [
                    'url' => $acs_url,
                    'username' => $acs_user,
                    'password' => $acs_pass,
                    'inform_interval' => 300,
                    'session_timeout' => 300
                ],
                'security' => [
                    'session_secret' => bin2hex(random_bytes(32)),
                    'enable_https' => false,
                    'require_device_auth' => true
                ],
                'logging' => [
                    'enabled' => true,
                    'log_path' => __DIR__ . '/logs',
                    'log_level' => 'info',
                    'log_requests' => true
                ],
                'app' => [
                    'timezone' => 'UTC',
                    'debug' => false
                ]
            ];
            
            $config_content = "<?php\n/**\n * TR-069 ACS Configuration File\n * Generated by installer on " . date('Y-m-d H:i:s') . "\n */\n\nreturn " . var_export($config, true) . ";\n";
            
            if (file_put_contents(__DIR__ . '/config.php', $config_content)) {
                // Create logs directory
                if (!is_dir(__DIR__ . '/logs')) {
                    mkdir(__DIR__ . '/logs', 0755, true);
                }
                
                // Create .htaccess for logs
                file_put_contents(__DIR__ . '/logs/.htaccess', "Deny from all");
                
                $success = true;
            } else {
                $errors[] = "No se pudo crear el archivo config.php. Verifica los permisos.";
            }
            
        } catch (PDOException $e) {
            $errors[] = "Error de base de datos: " . $e->getMessage();
        } catch (Exception $e) {
            $errors[] = "Error: " . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TR-069 ACS - Instalación</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
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
        input[type="url"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .section-title {
            color: #667eea;
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
            width: 100%;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .alert-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .success-icon {
            text-align: center;
            font-size: 64px;
            margin: 20px 0;
        }
        
        .success-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .success-actions a {
            text-decoration: none;
        }
        
        .requirements {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .requirements ul {
            margin-left: 20px;
            margin-top: 10px;
        }
        
        .requirements li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <?php if ($success): ?>
            <div class="success-icon">✅</div>
            <h1>¡Instalación Completada!</h1>
            <p class="subtitle">TR-069 ACS ha sido instalado correctamente</p>
            
            <div class="alert alert-success">
                <strong>✓ Base de datos configurada</strong><br>
                <strong>✓ Archivos de configuración creados</strong><br>
                <strong>✓ Usuario administrador configurado</strong>
            </div>
            
            <div class="section">
                <div class="section-title">📋 Información de Acceso</div>
                <p><strong>Usuario:</strong> <?php echo htmlspecialchars($admin_user); ?></p>
                <p><strong>URL ACS:</strong> <?php echo htmlspecialchars($acs_url); ?></p>
                <p><strong>Usuario ACS:</strong> <?php echo htmlspecialchars($acs_user); ?></p>
            </div>
            
            <div class="requirements">
                <strong>⚠️ Importante:</strong>
                <ul>
                    <li>Por seguridad, considera eliminar o proteger el archivo install.php</li>
                    <li>Configura tus dispositivos CPE con la URL del ACS y las credenciales</li>
                    <li>Asegúrate de que el directorio /logs tenga permisos de escritura</li>
                </ul>
            </div>
            
            <div class="success-actions">
                <a href="index.php" class="btn btn-primary">Ir al Panel de Control</a>
            </div>
            
        <?php else: ?>
            <h1>🚀 Instalación de TR-069 ACS</h1>
            <p class="subtitle">Servidor de Auto-Configuración TR-069</p>
            
            <?php if ($step === 1): ?>
                <div class="requirements">
                    <strong>📋 Requisitos del Sistema:</strong>
                    <ul>
                        <li>PHP 7.4 o superior (con extensiones: pdo, pdo_mysql, soap, simplexml)</li>
                        <li>MySQL 5.7 o superior / MariaDB 10.2 o superior</li>
                        <li>Servidor web (Apache/Nginx) con mod_rewrite habilitado</li>
                        <li>Permisos de escritura en el directorio de instalación</li>
                    </ul>
                </div>
                
                <form method="POST">
                    <input type="hidden" name="step" value="2">
                    <button type="submit" class="btn btn-primary">Comenzar Instalación →</button>
                </form>
            <?php else: ?>
                <?php if (!empty($errors)): ?>
                    <div class="alert alert-danger">
                        <strong>❌ Errores encontrados:</strong>
                        <ul>
                            <?php foreach ($errors as $error): ?>
                                <li><?php echo htmlspecialchars($error); ?></li>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                <?php endif; ?>
                
                <form method="POST">
                    <input type="hidden" name="step" value="2">
                    
                    <div class="section">
                        <div class="section-title">🗄️ Configuración de Base de Datos</div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="db_host">Host *</label>
                                <input type="text" id="db_host" name="db_host" value="<?php echo htmlspecialchars($_POST['db_host'] ?? 'localhost'); ?>" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="db_port">Puerto</label>
                                <input type="number" id="db_port" name="db_port" value="<?php echo htmlspecialchars($_POST['db_port'] ?? '3306'); ?>">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="db_name">Nombre de la Base de Datos *</label>
                            <input type="text" id="db_name" name="db_name" value="<?php echo htmlspecialchars($_POST['db_name'] ?? 'tr069_acs'); ?>" required>
                            <div class="help-text">Se creará automáticamente si no existe</div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="db_user">Usuario *</label>
                                <input type="text" id="db_user" name="db_user" value="<?php echo htmlspecialchars($_POST['db_user'] ?? 'root'); ?>" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="db_pass">Contraseña</label>
                                <input type="password" id="db_pass" name="db_pass" value="<?php echo htmlspecialchars($_POST['db_pass'] ?? ''); ?>">
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">🌐 Configuración del ACS</div>
                        
                        <div class="form-group">
                            <label for="acs_url">URL del ACS *</label>
                            <input type="url" id="acs_url" name="acs_url" value="<?php echo htmlspecialchars($_POST['acs_url'] ?? 'http://' . $_SERVER['HTTP_HOST'] . dirname($_SERVER['PHP_SELF']) . '/acs.php'); ?>" required>
                            <div class="help-text">URL completa donde los dispositivos CPE se conectarán</div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="acs_user">Usuario del ACS *</label>
                                <input type="text" id="acs_user" name="acs_user" value="<?php echo htmlspecialchars($_POST['acs_user'] ?? 'acs_user'); ?>" required>
                                <div class="help-text">Usuario para autenticación de dispositivos</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="acs_pass">Contraseña del ACS *</label>
                                <input type="password" id="acs_pass" name="acs_pass" required>
                                <div class="help-text">Contraseña para autenticación de dispositivos</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">👤 Usuario Administrador</div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="admin_user">Usuario *</label>
                                <input type="text" id="admin_user" name="admin_user" value="<?php echo htmlspecialchars($_POST['admin_user'] ?? 'admin'); ?>" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="admin_email">Email</label>
                                <input type="email" id="admin_email" name="admin_email" value="<?php echo htmlspecialchars($_POST['admin_email'] ?? ''); ?>">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="admin_pass">Contraseña *</label>
                            <input type="password" id="admin_pass" name="admin_pass" required>
                            <div class="help-text">Mínimo 6 caracteres recomendados</div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">🚀 Instalar TR-069 ACS</button>
                </form>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</body>
</html>
