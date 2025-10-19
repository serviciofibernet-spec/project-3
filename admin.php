<?php
/**
 * Panel de Administración del Servidor TR-069
 */

require_once 'config.php';
require_once 'includes/database.php';

// Verificar si está instalado
if (!getConfig('installed')) {
    header('Location: install.php');
    exit;
}

// Verificar autenticación
session_start();
if (!isset($_SESSION['admin_logged_in'])) {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['username']) && isset($_POST['password'])) {
        $username = $_POST['username'];
        $password = $_POST['password'];
        
        if ($username === getConfig('admin_username') && password_verify($password, getConfig('admin_password'))) {
            $_SESSION['admin_logged_in'] = true;
            $_SESSION['admin_username'] = $username;
        } else {
            $error = 'Credenciales incorrectas';
        }
    }
    
    if (!isset($_SESSION['admin_logged_in'])) {
        showLoginForm($error ?? '');
        exit;
    }
}

// Inicializar base de datos
$db = new Database();

// Procesar acciones
$action = $_GET['action'] ?? 'dashboard';
$message = '';
$error = '';

switch ($action) {
    case 'logout':
        session_destroy();
        header('Location: admin.php');
        exit;
        
    case 'delete_device':
        $deviceId = $_GET['device_id'] ?? '';
        if ($deviceId) {
            // Implementar eliminación de dispositivo
            $message = "Dispositivo $deviceId eliminado";
        }
        break;
        
    case 'clear_logs':
        // Implementar limpieza de logs
        $message = 'Logs eliminados';
        break;
}

// Obtener datos para el dashboard
$devices = $db->getAllDevices();
$logs = $db->getLogs(null, 50);
$totalDevices = count($devices);
$activeDevices = count(array_filter($devices, function($d) { return $d['status'] === 'active'; }));

function showLoginForm($error = '') {
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Administración TR-069</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
            .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            .btn { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
            .error { background: #ffebee; color: #c62828; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>🔐 Iniciar Sesión</h2>
            <?php if ($error): ?>
                <div class="error">❌ <?php echo htmlspecialchars($error); ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label for="username">Usuario:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Contraseña:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn">Iniciar Sesión</button>
            </form>
        </div>
    </body>
    </html>
    <?php
}

?>
<!DOCTYPE html>
<html>
<head>
    <title>Administración - Servidor TR-069</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
        .header { background: #007cba; color: white; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .nav { background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .nav a { margin-right: 20px; text-decoration: none; color: #007cba; font-weight: bold; }
        .nav a:hover { text-decoration: underline; }
        .card { background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #007cba; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; font-weight: bold; }
        .status-active { color: #28a745; font-weight: bold; }
        .status-inactive { color: #dc3545; font-weight: bold; }
        .btn { background: #007cba; color: white; padding: 8px 16px; border: none; border-radius: 3px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #005a87; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .message { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .log-entry { font-family: monospace; font-size: 0.9em; margin-bottom: 5px; padding: 5px; background: #f8f9fa; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🛠️ Panel de Administración TR-069</h1>
            <p>Gestión de dispositivos y monitoreo del servidor</p>
        </div>
    </div>
    
    <div class="container">
        <div class="nav">
            <a href="?action=dashboard">📊 Dashboard</a>
            <a href="?action=devices">📱 Dispositivos</a>
            <a href="?action=logs">📋 Logs</a>
            <a href="?action=settings">⚙️ Configuración</a>
            <a href="?action=logout" style="float: right;">🚪 Cerrar Sesión</a>
        </div>
        
        <?php if ($message): ?>
            <div class="message">✅ <?php echo htmlspecialchars($message); ?></div>
        <?php endif; ?>
        
        <?php if ($error): ?>
            <div class="error">❌ <?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        
        <?php if ($action === 'dashboard'): ?>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number"><?php echo $totalDevices; ?></div>
                    <div>Total Dispositivos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number"><?php echo $activeDevices; ?></div>
                    <div>Dispositivos Activos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number"><?php echo count($logs); ?></div>
                    <div>Eventos Recientes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number"><?php echo getConfig('server_name', 'TR069-Server'); ?></div>
                    <div>Servidor</div>
                </div>
            </div>
            
            <div class="card">
                <h3>📱 Dispositivos Recientes</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Fabricante</th>
                            <th>Modelo</th>
                            <th>Estado</th>
                            <th>Última Conexión</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach (array_slice($devices, 0, 10) as $device): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($device['device_id']); ?></td>
                                <td><?php echo htmlspecialchars($device['manufacturer']); ?></td>
                                <td><?php echo htmlspecialchars($device['model']); ?></td>
                                <td><span class="status-<?php echo $device['status']; ?>"><?php echo ucfirst($device['status']); ?></span></td>
                                <td><?php echo $device['last_inform_time'] ? date('Y-m-d H:i:s', strtotime($device['last_inform_time'])) : 'Nunca'; ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            
            <div class="card">
                <h3>📋 Actividad Reciente</h3>
                <?php foreach (array_slice($logs, 0, 20) as $log): ?>
                    <div class="log-entry">
                        <strong><?php echo date('Y-m-d H:i:s', strtotime($log['timestamp'])); ?></strong>
                        [<?php echo htmlspecialchars($log['device_id'] ?: 'Sistema'); ?>]
                        <?php echo htmlspecialchars($log['action']); ?>
                        <?php if ($log['details']): ?>
                            - <?php echo htmlspecialchars($log['details']); ?>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
            
        <?php elseif ($action === 'devices'): ?>
            <div class="card">
                <h3>📱 Gestión de Dispositivos</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Fabricante</th>
                            <th>Modelo</th>
                            <th>Número de Serie</th>
                            <th>Versión HW</th>
                            <th>Versión SW</th>
                            <th>Estado</th>
                            <th>Última Conexión</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($devices as $device): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($device['device_id']); ?></td>
                                <td><?php echo htmlspecialchars($device['manufacturer']); ?></td>
                                <td><?php echo htmlspecialchars($device['model']); ?></td>
                                <td><?php echo htmlspecialchars($device['serial_number']); ?></td>
                                <td><?php echo htmlspecialchars($device['hardware_version']); ?></td>
                                <td><?php echo htmlspecialchars($device['software_version']); ?></td>
                                <td><span class="status-<?php echo $device['status']; ?>"><?php echo ucfirst($device['status']); ?></span></td>
                                <td><?php echo $device['last_inform_time'] ? date('Y-m-d H:i:s', strtotime($device['last_inform_time'])) : 'Nunca'; ?></td>
                                <td>
                                    <a href="?action=device_details&device_id=<?php echo urlencode($device['device_id']); ?>" class="btn">Ver</a>
                                    <a href="?action=delete_device&device_id=<?php echo urlencode($device['device_id']); ?>" class="btn btn-danger" onclick="return confirm('¿Eliminar dispositivo?')">Eliminar</a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            
        <?php elseif ($action === 'device_details'): ?>
            <?php
            $deviceId = $_GET['device_id'] ?? '';
            $device = $db->getDevice($deviceId);
            if (!$device) {
                echo '<div class="error">Dispositivo no encontrado</div>';
            } else {
                $deviceLogs = $db->getLogs($deviceId, 50);
                $parameters = $db->getParameters($deviceId);
            ?>
            <div class="card">
                <h3>📱 Detalles del Dispositivo: <?php echo htmlspecialchars($device['device_id']); ?></h3>
                
                <h4>Información General</h4>
                <table class="table">
                    <tr><td><strong>ID del Dispositivo:</strong></td><td><?php echo htmlspecialchars($device['device_id']); ?></td></tr>
                    <tr><td><strong>Fabricante:</strong></td><td><?php echo htmlspecialchars($device['manufacturer']); ?></td></tr>
                    <tr><td><strong>Modelo:</strong></td><td><?php echo htmlspecialchars($device['model']); ?></td></tr>
                    <tr><td><strong>Número de Serie:</strong></td><td><?php echo htmlspecialchars($device['serial_number']); ?></td></tr>
                    <tr><td><strong>Versión Hardware:</strong></td><td><?php echo htmlspecialchars($device['hardware_version']); ?></td></tr>
                    <tr><td><strong>Versión Software:</strong></td><td><?php echo htmlspecialchars($device['software_version']); ?></td></tr>
                    <tr><td><strong>Estado:</strong></td><td><span class="status-<?php echo $device['status']; ?>"><?php echo ucfirst($device['status']); ?></span></td></tr>
                    <tr><td><strong>Última Conexión:</strong></td><td><?php echo $device['last_inform_time'] ? date('Y-m-d H:i:s', strtotime($device['last_inform_time'])) : 'Nunca'; ?></td></tr>
                    <tr><td><strong>Registrado:</strong></td><td><?php echo date('Y-m-d H:i:s', strtotime($device['created_at'])); ?></td></tr>
                </table>
                
                <h4>Parámetros del Dispositivo</h4>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Valor</th>
                            <th>Tipo</th>
                            <th>Escribible</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($parameters as $param): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($param['parameter_name']); ?></td>
                                <td><?php echo htmlspecialchars($param['parameter_value']); ?></td>
                                <td><?php echo htmlspecialchars($param['parameter_type']); ?></td>
                                <td><?php echo $param['writable'] ? 'Sí' : 'No'; ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
                
                <h4>Historial de Actividad</h4>
                <?php foreach ($deviceLogs as $log): ?>
                    <div class="log-entry">
                        <strong><?php echo date('Y-m-d H:i:s', strtotime($log['timestamp'])); ?></strong>
                        <?php echo htmlspecialchars($log['action']); ?>
                        <?php if ($log['details']): ?>
                            - <?php echo htmlspecialchars($log['details']); ?>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
            <?php } ?>
            
        <?php elseif ($action === 'logs'): ?>
            <div class="card">
                <h3>📋 Logs del Sistema</h3>
                <p><a href="?action=clear_logs" class="btn btn-danger" onclick="return confirm('¿Eliminar todos los logs?')">Limpiar Logs</a></p>
                <?php foreach ($logs as $log): ?>
                    <div class="log-entry">
                        <strong><?php echo date('Y-m-d H:i:s', strtotime($log['timestamp'])); ?></strong>
                        [<?php echo htmlspecialchars($log['device_id'] ?: 'Sistema'); ?>]
                        <?php echo htmlspecialchars($log['action']); ?>
                        <?php if ($log['details']): ?>
                            - <?php echo htmlspecialchars($log['details']); ?>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
            
        <?php elseif ($action === 'settings'): ?>
            <div class="card">
                <h3>⚙️ Configuración del Servidor</h3>
                <table class="table">
                    <tr><td><strong>Nombre del Servidor:</strong></td><td><?php echo htmlspecialchars(getConfig('server_name', 'TR069-Server')); ?></td></tr>
                    <tr><td><strong>URL del Servidor:</strong></td><td><?php echo htmlspecialchars(getConfig('server_url', 'http://localhost')); ?></td></tr>
                    <tr><td><strong>Usuario Administrador:</strong></td><td><?php echo htmlspecialchars(getConfig('admin_username', 'admin')); ?></td></tr>
                    <tr><td><strong>Autenticación Habilitada:</strong></td><td><?php echo getConfig('auth_enabled', true) ? 'Sí' : 'No'; ?></td></tr>
                    <tr><td><strong>Timeout de Sesión:</strong></td><td><?php echo getConfig('session_timeout', 3600); ?> segundos</td></tr>
                    <tr><td><strong>Fecha de Instalación:</strong></td><td><?php echo getConfig('install_date', 'No disponible'); ?></td></tr>
                </table>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>