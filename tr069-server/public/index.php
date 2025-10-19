<?php
/**
 * Panel de Administración del Servidor TR-069
 */
session_start();

// Verificar si está instalado
if (!file_exists(__DIR__ . '/../config/config.php')) {
    header('Location: ../install.php');
    exit;
}

require_once __DIR__ . '/../config/config.php';

// Verificar autenticación
if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

// Conectar a la base de datos
try {
    $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
    $db = new PDO($dsn, DB_USER, DB_PASS);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Error de conexión: " . $e->getMessage());
}

// Obtener estadísticas
$stats = [];

// Total de dispositivos
$stmt = $db->query("SELECT COUNT(*) as total FROM devices");
$stats['total_devices'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Dispositivos online
$stmt = $db->query("SELECT COUNT(*) as total FROM devices WHERE status = 'online'");
$stats['online_devices'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Sesiones activas
$stmt = $db->query("SELECT COUNT(*) as total FROM cwmp_sessions WHERE status = 'active'");
$stats['active_sessions'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Tareas pendientes
$stmt = $db->query("SELECT COUNT(*) as total FROM tasks WHERE status IN ('pending', 'queued')");
$stats['pending_tasks'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];

// Obtener dispositivos recientes
$stmt = $db->query("
    SELECT * FROM devices 
    ORDER BY last_inform DESC 
    LIMIT 10
");
$recent_devices = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Obtener logs recientes
$stmt = $db->query("
    SELECT * FROM logs 
    WHERE log_level IN ('WARNING', 'ERROR', 'CRITICAL')
    ORDER BY created_at DESC 
    LIMIT 10
");
$recent_logs = $stmt->fetchAll(PDO::FETCH_ASSOC);

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Control - TR-069 Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            display: flex;
            align-items: center;
        }
        
        .logo svg {
            width: 32px;
            height: 32px;
            margin-right: 10px;
        }
        
        .user-menu {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .user-avatar {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #667eea;
            font-weight: bold;
        }
        
        .btn-logout {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            transition: all 0.3s;
        }
        
        .btn-logout:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .nav {
            background: white;
            border-bottom: 1px solid #e0e0e0;
            padding: 0 2rem;
        }
        
        .nav-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 30px;
        }
        
        .nav-item {
            padding: 1rem 0;
            color: #666;
            text-decoration: none;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .nav-item:hover {
            color: #667eea;
        }
        
        .nav-item.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            font-size: 24px;
        }
        
        .stat-icon.blue {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .stat-icon.green {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        
        .stat-icon.orange {
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            color: white;
        }
        
        .stat-icon.red {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #999;
            font-size: 0.9rem;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        .panel-header {
            background: #f8f9fa;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .panel-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
        }
        
        .panel-body {
            padding: 1.5rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            color: #666;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            padding: 0.75rem;
            border-bottom: 2px solid #e0e0e0;
        }
        
        td {
            padding: 0.75rem;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-badge.online {
            background: #d4f4dd;
            color: #22863a;
        }
        
        .status-badge.offline {
            background: #ffeaa7;
            color: #d68910;
        }
        
        .status-badge.error {
            background: #ffe5e5;
            color: #d73a49;
        }
        
        .log-item {
            padding: 0.75rem;
            border-left: 3px solid;
            margin-bottom: 0.5rem;
            background: #f8f9fa;
            border-radius: 0 6px 6px 0;
        }
        
        .log-item.warning {
            border-left-color: #f59e0b;
        }
        
        .log-item.error {
            border-left-color: #ef4444;
        }
        
        .log-item.critical {
            border-left-color: #dc2626;
            background: #fee;
        }
        
        .log-time {
            color: #999;
            font-size: 0.8rem;
        }
        
        .log-message {
            color: #333;
            margin-top: 0.25rem;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 1rem;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            text-align: center;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: #999;
        }
        
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                TR-069 Server
            </div>
            <div class="user-menu">
                <div class="user-info">
                    <div class="user-avatar">
                        <?= strtoupper(substr($_SESSION['username'] ?? 'A', 0, 1)) ?>
                    </div>
                    <span><?= htmlspecialchars($_SESSION['username'] ?? 'Admin') ?></span>
                </div>
                <a href="logout.php" class="btn-logout">Cerrar Sesión</a>
            </div>
        </div>
    </header>
    
    <nav class="nav">
        <div class="nav-content">
            <a href="index.php" class="nav-item active">Dashboard</a>
            <a href="devices.php" class="nav-item">Dispositivos</a>
            <a href="tasks.php" class="nav-item">Tareas</a>
            <a href="firmware.php" class="nav-item">Firmware</a>
            <a href="configurations.php" class="nav-item">Configuraciones</a>
            <a href="logs.php" class="nav-item">Logs</a>
            <a href="settings.php" class="nav-item">Ajustes</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon blue">📡</div>
                <div class="stat-value"><?= $stats['total_devices'] ?></div>
                <div class="stat-label">Total Dispositivos</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">✅</div>
                <div class="stat-value"><?= $stats['online_devices'] ?></div>
                <div class="stat-label">Dispositivos Online</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon orange">🔄</div>
                <div class="stat-value"><?= $stats['active_sessions'] ?></div>
                <div class="stat-label">Sesiones Activas</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon red">📋</div>
                <div class="stat-value"><?= $stats['pending_tasks'] ?></div>
                <div class="stat-label">Tareas Pendientes</div>
            </div>
        </div>
        
        <div class="content-grid">
            <div class="panel">
                <div class="panel-header">
                    <h2 class="panel-title">Dispositivos Recientes</h2>
                    <a href="devices.php" style="color: #667eea; text-decoration: none; font-size: 0.9rem;">Ver todos →</a>
                </div>
                <div class="panel-body" style="padding: 0;">
                    <?php if (empty($recent_devices)): ?>
                        <div class="empty-state">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <p>No hay dispositivos registrados</p>
                        </div>
                    <?php else: ?>
                        <table>
                            <thead>
                                <tr>
                                    <th>Dispositivo</th>
                                    <th>Modelo</th>
                                    <th>IP</th>
                                    <th>Estado</th>
                                    <th>Última Conexión</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($recent_devices as $device): ?>
                                    <tr>
                                        <td><?= htmlspecialchars($device['device_id']) ?></td>
                                        <td><?= htmlspecialchars($device['model_name'] ?? 'N/A') ?></td>
                                        <td><?= htmlspecialchars($device['ip_address'] ?? 'N/A') ?></td>
                                        <td>
                                            <span class="status-badge <?= $device['status'] ?>">
                                                <?= $device['status'] ?>
                                            </span>
                                        </td>
                                        <td><?= $device['last_inform'] ? date('d/m/Y H:i', strtotime($device['last_inform'])) : 'Nunca' ?></td>
                                    </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php endif; ?>
                </div>
            </div>
            
            <div>
                <div class="panel" style="margin-bottom: 20px;">
                    <div class="panel-header">
                        <h2 class="panel-title">Acciones Rápidas</h2>
                    </div>
                    <div class="panel-body">
                        <div class="quick-actions">
                            <a href="devices.php?action=add" class="btn">➕ Agregar Dispositivo</a>
                            <a href="tasks.php?action=new" class="btn btn-secondary">📝 Nueva Tarea</a>
                            <a href="firmware.php?action=upload" class="btn btn-secondary">⬆️ Subir Firmware</a>
                            <a href="devices.php?action=scan" class="btn">🔍 Escanear Red</a>
                        </div>
                    </div>
                </div>
                
                <div class="panel">
                    <div class="panel-header">
                        <h2 class="panel-title">Logs Recientes</h2>
                        <a href="logs.php" style="color: #667eea; text-decoration: none; font-size: 0.9rem;">Ver todos →</a>
                    </div>
                    <div class="panel-body">
                        <?php if (empty($recent_logs)): ?>
                            <div class="empty-state">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <p>No hay logs de advertencia o error</p>
                            </div>
                        <?php else: ?>
                            <?php foreach ($recent_logs as $log): ?>
                                <div class="log-item <?= strtolower($log['log_level']) ?>">
                                    <div class="log-time">
                                        <?= date('d/m/Y H:i:s', strtotime($log['created_at'])) ?>
                                    </div>
                                    <div class="log-message">
                                        <?= htmlspecialchars($log['message']) ?>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>