<?php
/**
 * TR-069 ACS - Device Management
 */

session_start();

if (!file_exists(__DIR__ . '/config.php')) {
    header('Location: install.php');
    exit;
}

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$config = require __DIR__ . '/config.php';
date_default_timezone_set($config['app']['timezone']);

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
    die('Database connection failed');
}

// Handle device actions
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    $device_id = (int)$_POST['device_id'];
    
    switch ($_POST['action']) {
        case 'reboot':
            $stmt = $pdo->prepare("INSERT INTO tasks (device_id, task_type, status) VALUES (?, 'Reboot', 'pending')");
            $stmt->execute([$device_id]);
            $message = "Tarea de reinicio programada";
            break;
            
        case 'get_params':
            $parameters = json_encode([
                'parameters' => [
                    'InternetGatewayDevice.DeviceInfo.',
                    'InternetGatewayDevice.ManagementServer.'
                ]
            ]);
            $stmt = $pdo->prepare("INSERT INTO tasks (device_id, task_type, parameters, status) VALUES (?, 'GetParameterValues', ?, 'pending')");
            $stmt->execute([$device_id, $parameters]);
            $message = "Tarea de obtención de parámetros programada";
            break;
    }
}

// Get all devices
$search = $_GET['search'] ?? '';
$status_filter = $_GET['status'] ?? '';

$sql = "SELECT * FROM devices WHERE 1=1";
$params = [];

if ($search) {
    $sql .= " AND (serial_number LIKE ? OR manufacturer LIKE ? OR model LIKE ?)";
    $params[] = "%$search%";
    $params[] = "%$search%";
    $params[] = "%$search%";
}

if ($status_filter) {
    $sql .= " AND status = ?";
    $params[] = $status_filter;
}

$sql .= " ORDER BY last_inform DESC";

$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$devices = $stmt->fetchAll();

// Get device details if requested
$device_details = null;
$device_parameters = [];
if (isset($_GET['id'])) {
    $device_id = (int)$_GET['id'];
    $stmt = $pdo->prepare("SELECT * FROM devices WHERE id = ?");
    $stmt->execute([$device_id]);
    $device_details = $stmt->fetch();
    
    if ($device_details) {
        $stmt = $pdo->prepare("SELECT * FROM parameters WHERE device_id = ? ORDER BY parameter_name");
        $stmt->execute([$device_id]);
        $device_parameters = $stmt->fetchAll();
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TR-069 ACS - Dispositivos</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
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
        }
        .navbar h1 { font-size: 24px; }
        .navbar a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .navbar a:hover { background: rgba(255,255,255,0.2); }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
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
        }
        .filters {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filters input,
        .filters select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .filters input { flex: 1; min-width: 250px; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table thead { background: #f8f9fa; }
        table th {
            text-align: left;
            padding: 12px;
            font-weight: 600;
            color: #666;
        }
        table td {
            padding: 12px;
            border-top: 1px solid #eee;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-online { background: #d4edda; color: #155724; }
        .status-offline { background: #f8d7da; color: #721c24; }
        .status-pending { background: #fff3cd; color: #856404; }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content {
            background: white;
            border-radius: 10px;
            padding: 30px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            width: 90%;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .close { cursor: pointer; font-size: 24px; }
        .param-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .param-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .param-item:hover { background: #f8f9fa; }
        .param-name {
            font-weight: 600;
            color: #333;
            font-size: 13px;
        }
        .param-value {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
            word-break: break-all;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>📱 Gestión de Dispositivos</h1>
        <a href="index.php">← Volver al Dashboard</a>
    </div>
    
    <div class="container">
        <?php if (isset($message)): ?>
            <div class="alert alert-success"><?php echo htmlspecialchars($message); ?></div>
        <?php endif; ?>
        
        <div class="section">
            <div class="section-title">🔍 Filtros de Búsqueda</div>
            
            <form method="GET" class="filters">
                <input type="text" name="search" placeholder="Buscar por serial, fabricante o modelo..." value="<?php echo htmlspecialchars($search); ?>">
                <select name="status">
                    <option value="">Todos los estados</option>
                    <option value="online" <?php echo $status_filter === 'online' ? 'selected' : ''; ?>>Online</option>
                    <option value="offline" <?php echo $status_filter === 'offline' ? 'selected' : ''; ?>>Offline</option>
                    <option value="pending" <?php echo $status_filter === 'pending' ? 'selected' : ''; ?>>Pending</option>
                </select>
                <button type="submit" class="btn btn-primary">Buscar</button>
            </form>
        </div>
        
        <div class="section">
            <div class="section-title">📋 Lista de Dispositivos (<?php echo count($devices); ?>)</div>
            
            <?php if (empty($devices)): ?>
                <p style="text-align: center; color: #999; padding: 40px;">No se encontraron dispositivos</p>
            <?php else: ?>
                <table>
                    <thead>
                        <tr>
                            <th>Serial Number / OUI</th>
                            <th>Fabricante</th>
                            <th>Modelo</th>
                            <th>Versión SW</th>
                            <th>IP</th>
                            <th>Último Inform</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($devices as $device): ?>
                            <tr>
                                <td>
                                    <strong><?php echo htmlspecialchars($device['serial_number']); ?></strong><br>
                                    <small style="color: #999;">OUI: <?php echo htmlspecialchars($device['oui']); ?></small>
                                </td>
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
                                <td>
                                    <a href="?id=<?php echo $device['id']; ?>" class="btn btn-primary btn-small">Ver Detalles</a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
    
    <!-- Device Details Modal -->
    <?php if ($device_details): ?>
        <div class="modal active" id="deviceModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>📱 Detalles del Dispositivo</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div>
                        <strong>Serial Number:</strong><br>
                        <?php echo htmlspecialchars($device_details['serial_number']); ?>
                    </div>
                    <div>
                        <strong>OUI:</strong><br>
                        <?php echo htmlspecialchars($device_details['oui']); ?>
                    </div>
                    <div>
                        <strong>Fabricante:</strong><br>
                        <?php echo htmlspecialchars($device_details['manufacturer']); ?>
                    </div>
                    <div>
                        <strong>Modelo:</strong><br>
                        <?php echo htmlspecialchars($device_details['model']); ?>
                    </div>
                    <div>
                        <strong>Versión HW:</strong><br>
                        <?php echo htmlspecialchars($device_details['hardware_version']); ?>
                    </div>
                    <div>
                        <strong>Versión SW:</strong><br>
                        <?php echo htmlspecialchars($device_details['software_version']); ?>
                    </div>
                    <div>
                        <strong>IP Address:</strong><br>
                        <?php echo htmlspecialchars($device_details['ip_address']); ?>
                    </div>
                    <div>
                        <strong>Estado:</strong><br>
                        <span class="status-badge status-<?php echo $device_details['status']; ?>">
                            <?php echo ucfirst($device_details['status']); ?>
                        </span>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="device_id" value="<?php echo $device_details['id']; ?>">
                        <input type="hidden" name="action" value="reboot">
                        <button type="submit" class="btn btn-danger btn-small" onclick="return confirm('¿Reiniciar dispositivo?')">
                            🔄 Reiniciar
                        </button>
                    </form>
                    <form method="POST" style="display: inline;">
                        <input type="hidden" name="device_id" value="<?php echo $device_details['id']; ?>">
                        <input type="hidden" name="action" value="get_params">
                        <button type="submit" class="btn btn-success btn-small">
                            📥 Obtener Parámetros
                        </button>
                    </form>
                </div>
                
                <h3 style="margin-bottom: 15px;">Parámetros (<?php echo count($device_parameters); ?>)</h3>
                <div class="param-list">
                    <?php if (empty($device_parameters)): ?>
                        <p style="text-align: center; color: #999; padding: 20px;">
                            No hay parámetros disponibles. Espera al próximo Inform o solicita parámetros.
                        </p>
                    <?php else: ?>
                        <?php foreach ($device_parameters as $param): ?>
                            <div class="param-item">
                                <div class="param-name"><?php echo htmlspecialchars($param['parameter_name']); ?></div>
                                <div class="param-value"><?php echo htmlspecialchars($param['parameter_value']); ?></div>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
            </div>
        </div>
        
        <script>
            function closeModal() {
                window.location.href = 'devices.php';
            }
        </script>
    <?php endif; ?>
</body>
</html>
