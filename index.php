<?php
/**
 * TR-069 ACS Dashboard
 * Admin panel for managing CPE devices
 */

session_start();

// Load configuration
if (!file_exists(__DIR__ . '/config.php')) {
    header('Location: install.php');
    exit;
}

$config = require __DIR__ . '/config.php';
date_default_timezone_set($config['app']['timezone']);

// Database connection
try {
    $dsn = sprintf(
        "mysql:host=%s;port=%d;dbname=%s;charset=%s",
        $config['db']['host'],
        $config['db']['port'],
        $config['db']['database'],
        $config['db']['charset']
    );
    $pdo = new PDO($dsn, $config['db']['username'], $config['db']['password']);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (PDOException $e) {
    die('Database connection failed: ' . $e->getMessage());
}

// Authentication check
if (!isset($_SESSION['user_id']) && $_SERVER['REQUEST_URI'] !== '/login.php') {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        
        $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch();
        
        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['username'] = $user['username'];
            $_SESSION['role'] = $user['role'];
            header('Location: index.php');
            exit;
        } else {
            $login_error = "Usuario o contraseña incorrectos";
        }
    }
    
    // Show login form
    ?>
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TR-069 ACS - Login</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .login-container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
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
            input[type="password"] {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            .btn {
                width: 100%;
                padding: 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #5568d3;
            }
            .error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>🔐 TR-069 ACS</h1>
            <?php if (isset($login_error)): ?>
                <div class="error"><?php echo htmlspecialchars($login_error); ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label>Usuario</label>
                    <input type="text" name="username" required autofocus>
                </div>
                <div class="form-group">
                    <label>Contraseña</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" name="login" class="btn">Iniciar Sesión</button>
            </form>
        </div>
    </body>
    </html>
    <?php
    exit;
}

// Logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: index.php');
    exit;
}

// Get statistics
$stmt = $pdo->query("SELECT COUNT(*) as total FROM devices");
$total_devices = $stmt->fetch()['total'];

$stmt = $pdo->query("SELECT COUNT(*) as online FROM devices WHERE status = 'online' AND last_inform > DATE_SUB(NOW(), INTERVAL 10 MINUTE)");
$online_devices = $stmt->fetch()['online'];

$stmt = $pdo->query("SELECT COUNT(*) as pending FROM tasks WHERE status = 'pending'");
$pending_tasks = $stmt->fetch()['pending'];

$stmt = $pdo->query("SELECT COUNT(*) as total FROM inform_log WHERE DATE(created_at) = CURDATE()");
$today_informs = $stmt->fetch()['total'];

// Get recent devices
$stmt = $pdo->query("
    SELECT * FROM devices 
    ORDER BY last_inform DESC 
    LIMIT 10
");
$recent_devices = $stmt->fetchAll();

// Get recent informs
$stmt = $pdo->query("
    SELECT il.*, d.serial_number, d.manufacturer, d.model 
    FROM inform_log il
    LEFT JOIN devices d ON il.device_id = d.id
    ORDER BY il.created_at DESC 
    LIMIT 20
");
$recent_informs = $stmt->fetchAll();

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TR-069 ACS - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f6fa;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .navbar h1 {
            font-size: 24px;
        }
        
        .navbar .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .navbar a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        
        .navbar a:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .stat-icon {
            font-size: 48px;
            width: 70px;
            height: 70px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }
        
        .stat-icon.blue { background: #e3f2fd; }
        .stat-icon.green { background: #e8f5e9; }
        .stat-icon.orange { background: #fff3e0; }
        .stat-icon.purple { background: #f3e5f5; }
        
        .stat-info h3 {
            color: #666;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 5px;
        }
        
        .stat-info .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        table thead {
            background: #f8f9fa;
        }
        
        table th {
            text-align: left;
            padding: 12px;
            font-weight: 600;
            color: #666;
            font-size: 14px;
        }
        
        table td {
            padding: 12px;
            border-top: 1px solid #eee;
            color: #333;
            font-size: 14px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-online {
            background: #d4edda;
            color: #155724;
        }
        
        .status-offline {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-pending {
            background: #fff3cd;
            color: #856404;
        }
        
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
            border: none;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
        }
        
        .btn-small {
            padding: 4px 12px;
            font-size: 12px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 10px;
        }
        
        .config-info {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .config-info strong {
            color: #1976d2;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s;
        }
        
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: 600;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>🚀 TR-069 ACS Dashboard</h1>
        <div class="user-info">
            <span>👤 <?php echo htmlspecialchars($_SESSION['username']); ?></span>
            <a href="?logout">Cerrar Sesión</a>
        </div>
    </div>
    
    <div class="container">
        <!-- Statistics -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-icon blue">📱</div>
                <div class="stat-info">
                    <h3>Dispositivos Totales</h3>
                    <div class="value"><?php echo $total_devices; ?></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">✅</div>
                <div class="stat-info">
                    <h3>Dispositivos Online</h3>
                    <div class="value"><?php echo $online_devices; ?></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon orange">⏳</div>
                <div class="stat-info">
                    <h3>Tareas Pendientes</h3>
                    <div class="value"><?php echo $pending_tasks; ?></div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">📊</div>
                <div class="stat-info">
                    <h3>Informs Hoy</h3>
                    <div class="value"><?php echo $today_informs; ?></div>
                </div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="section">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('devices')">Dispositivos</div>
                <div class="tab" onclick="switchTab('informs')">Historial de Informs</div>
                <div class="tab" onclick="switchTab('config')">Configuración</div>
            </div>
            
            <!-- Devices Tab -->
            <div id="devices" class="tab-content active">
                <div class="section-title">
                    <span>📱 Dispositivos Recientes</span>
                    <a href="devices.php" class="btn btn-primary btn-small">Ver Todos</a>
                </div>
                
                <?php if (empty($recent_devices)): ?>
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <p>No hay dispositivos registrados aún</p>
                        <p style="margin-top: 10px; font-size: 14px;">Los dispositivos aparecerán aquí cuando envíen su primer Inform</p>
                    </div>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Serial Number</th>
                                <th>Fabricante</th>
                                <th>Modelo</th>
                                <th>Versión SW</th>
                                <th>IP</th>
                                <th>Último Inform</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($recent_devices as $device): ?>
                                <tr>
                                    <td><strong><?php echo htmlspecialchars($device['serial_number']); ?></strong></td>
                                    <td><?php echo htmlspecialchars($device['manufacturer']); ?></td>
                                    <td><?php echo htmlspecialchars($device['model']); ?></td>
                                    <td><?php echo htmlspecialchars($device['software_version']); ?></td>
                                    <td><?php echo htmlspecialchars($device['ip_address']); ?></td>
                                    <td><?php echo $device['last_inform'] ? date('Y-m-d H:i:s', strtotime($device['last_inform'])) : '-'; ?></td>
                                    <td>
                                        <span class="status-badge status-<?php echo $device['status']; ?>">
                                            <?php echo ucfirst($device['status']); ?>
                                        </span>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
            
            <!-- Informs Tab -->
            <div id="informs" class="tab-content">
                <div class="section-title">
                    <span>📊 Historial de Informs</span>
                </div>
                
                <?php if (empty($recent_informs)): ?>
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <p>No hay informs registrados aún</p>
                    </div>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha/Hora</th>
                                <th>Serial Number</th>
                                <th>Fabricante</th>
                                <th>Modelo</th>
                                <th>Evento</th>
                                <th>IP</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($recent_informs as $inform): ?>
                                <tr>
                                    <td><?php echo date('Y-m-d H:i:s', strtotime($inform['created_at'])); ?></td>
                                    <td><strong><?php echo htmlspecialchars($inform['serial_number']); ?></strong></td>
                                    <td><?php echo htmlspecialchars($inform['manufacturer'] ?? '-'); ?></td>
                                    <td><?php echo htmlspecialchars($inform['model'] ?? '-'); ?></td>
                                    <td><?php echo htmlspecialchars($inform['event_code']); ?></td>
                                    <td><?php echo htmlspecialchars($inform['ip_address']); ?></td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
            
            <!-- Config Tab -->
            <div id="config" class="tab-content">
                <div class="section-title">
                    <span>⚙️ Configuración del Servidor</span>
                </div>
                
                <div class="config-info">
                    <p><strong>URL del ACS:</strong> <?php echo htmlspecialchars($config['acs']['url']); ?></p>
                    <p style="margin-top: 10px;"><strong>Usuario ACS:</strong> <?php echo htmlspecialchars($config['acs']['username']); ?></p>
                    <p style="margin-top: 10px;"><strong>Intervalo de Inform:</strong> <?php echo $config['acs']['inform_interval']; ?> segundos</p>
                    <p style="margin-top: 10px;"><strong>Base de Datos:</strong> <?php echo htmlspecialchars($config['db']['database']); ?>@<?php echo htmlspecialchars($config['db']['host']); ?></p>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                    <p><strong>📝 Configuración para dispositivos CPE:</strong></p>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li>ACS URL: <code><?php echo htmlspecialchars($config['acs']['url']); ?></code></li>
                        <li>ACS Username: <code><?php echo htmlspecialchars($config['acs']['username']); ?></code></li>
                        <li>ACS Password: <code>***</code> (configurado en install.php)</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Auto refresh every 30 seconds
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
