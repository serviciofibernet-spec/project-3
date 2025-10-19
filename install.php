<?php
/**
 * Instalador del Servidor TR-069
 * Configuración inicial del servidor
 */

require_once 'config.php';

$step = isset($_GET['step']) ? (int)$_GET['step'] : 1;
$error = '';
$success = '';

// Procesar formularios
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    switch ($step) {
        case 1:
            // Configuración básica
            $server_name = $_POST['server_name'] ?? '';
            $server_url = $_POST['server_url'] ?? '';
            $admin_username = $_POST['admin_username'] ?? '';
            $admin_password = $_POST['admin_password'] ?? '';
            
            if (empty($server_name) || empty($server_url) || empty($admin_username) || empty($admin_password)) {
                $error = 'Todos los campos son obligatorios';
            } else {
                setConfig('server_name', $server_name);
                setConfig('server_url', $server_url);
                setConfig('admin_username', $admin_username);
                setConfig('admin_password', password_hash($admin_password, PASSWORD_DEFAULT));
                $success = 'Configuración básica guardada';
                $step = 2;
            }
            break;
            
        case 2:
            // Configuración de base de datos
            $db_type = $_POST['db_type'] ?? 'sqlite';
            
            if ($db_type === 'sqlite') {
                setConfig('db_type', 'sqlite');
                setConfig('db_path', DB_PATH);
                $success = 'Configuración de base de datos guardada';
                $step = 3;
            } else {
                $error = 'Solo SQLite está soportado actualmente';
            }
            break;
            
        case 3:
            // Configuración de autenticación
            $auth_enabled = isset($_POST['auth_enabled']);
            $session_timeout = (int)($_POST['session_timeout'] ?? 3600);
            
            setConfig('auth_enabled', $auth_enabled);
            setConfig('session_timeout', $session_timeout);
            
            // Inicializar base de datos
            require_once 'includes/database.php';
            $db = new Database();
            $db->initialize();
            
            // Marcar como instalado
            setConfig('installed', true);
            setConfig('install_date', date('Y-m-d H:i:s'));
            
            $success = 'Instalación completada exitosamente';
            $step = 4;
            break;
    }
}

?>
<!DOCTYPE html>
<html>
<head>
    <title>Instalador - Servidor TR-069</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 600px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        .step { 
            margin-bottom: 30px; 
        }
        .step-number { 
            background: #007cba; 
            color: white; 
            width: 30px; 
            height: 30px; 
            border-radius: 50%; 
            display: inline-flex; 
            align-items: center; 
            justify-content: center; 
            margin-right: 10px; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
        }
        input[type="text"], input[type="password"], input[type="number"], input[type="url"] { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            box-sizing: border-box; 
        }
        input[type="checkbox"] { 
            margin-right: 10px; 
        }
        .btn { 
            background: #007cba; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
        }
        .btn:hover { 
            background: #005a87; 
        }
        .error { 
            background: #ffebee; 
            color: #c62828; 
            padding: 10px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .success { 
            background: #e8f5e8; 
            color: #2e7d32; 
            padding: 10px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }
        .progress { 
            background: #e0e0e0; 
            height: 4px; 
            border-radius: 2px; 
            margin-bottom: 30px; 
        }
        .progress-bar { 
            background: #007cba; 
            height: 100%; 
            border-radius: 2px; 
            transition: width 0.3s; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Instalador del Servidor TR-069</h1>
        
        <div class="progress">
            <div class="progress-bar" style="width: <?php echo ($step / 4) * 100; ?>%"></div>
        </div>
        
        <?php if ($error): ?>
            <div class="error">❌ <?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        
        <?php if ($success): ?>
            <div class="success">✅ <?php echo htmlspecialchars($success); ?></div>
        <?php endif; ?>
        
        <?php if ($step === 1): ?>
            <div class="step">
                <h2><span class="step-number">1</span>Configuración Básica</h2>
                <form method="POST">
                    <div class="form-group">
                        <label for="server_name">Nombre del Servidor:</label>
                        <input type="text" id="server_name" name="server_name" 
                               value="<?php echo htmlspecialchars(getConfig('server_name', 'TR069-PHP-Server')); ?>" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="server_url">URL del Servidor:</label>
                        <input type="url" id="server_url" name="server_url" 
                               value="<?php echo htmlspecialchars(getConfig('server_url', 'http://' . $_SERVER['HTTP_HOST'] . dirname($_SERVER['REQUEST_URI']))); ?>" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="admin_username">Usuario Administrador:</label>
                        <input type="text" id="admin_username" name="admin_username" 
                               value="<?php echo htmlspecialchars(getConfig('admin_username', 'admin')); ?>" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="admin_password">Contraseña Administrador:</label>
                        <input type="password" id="admin_password" name="admin_password" required>
                    </div>
                    
                    <button type="submit" class="btn">Siguiente</button>
                </form>
            </div>
            
        <?php elseif ($step === 2): ?>
            <div class="step">
                <h2><span class="step-number">2</span>Configuración de Base de Datos</h2>
                <form method="POST">
                    <div class="form-group">
                        <label>
                            <input type="radio" name="db_type" value="sqlite" checked>
                            SQLite (Recomendado)
                        </label>
                        <p>Base de datos ligera que no requiere configuración adicional.</p>
                    </div>
                    
                    <button type="submit" class="btn">Siguiente</button>
                </form>
            </div>
            
        <?php elseif ($step === 3): ?>
            <div class="step">
                <h2><span class="step-number">3</span>Configuración de Autenticación</h2>
                <form method="POST">
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="auth_enabled" checked>
                            Habilitar autenticación
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label for="session_timeout">Timeout de Sesión (segundos):</label>
                        <input type="number" id="session_timeout" name="session_timeout" 
                               value="<?php echo getConfig('session_timeout', 3600); ?>" min="300" max="86400">
                    </div>
                    
                    <button type="submit" class="btn">Instalar</button>
                </form>
            </div>
            
        <?php elseif ($step === 4): ?>
            <div class="step">
                <h2><span class="step-number">4</span>Instalación Completada</h2>
                <div class="success">
                    <h3>🎉 ¡Instalación exitosa!</h3>
                    <p>El servidor TR-069 ha sido configurado correctamente.</p>
                </div>
                
                <h3>Próximos pasos:</h3>
                <ul>
                    <li><a href="index.php">Ir al servidor principal</a></li>
                    <li><a href="admin.php">Acceder al panel de administración</a></li>
                    <li>Configurar dispositivos CPE para conectarse a este servidor</li>
                </ul>
                
                <h3>Información del servidor:</h3>
                <ul>
                    <li><strong>Endpoint SOAP:</strong> <?php echo getConfig('server_url'); ?></li>
                    <li><strong>Usuario admin:</strong> <?php echo getConfig('admin_username'); ?></li>
                    <li><strong>Fecha de instalación:</strong> <?php echo getConfig('install_date'); ?></li>
                </ul>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>