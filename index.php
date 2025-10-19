<?php
/**
 * TR-069 ACS Web Interface
 * Main dashboard for device management
 */

session_start();

// Check if installed
if (!file_exists('config/database.php')) {
    header('Location: install.php');
    exit;
}

require_once 'config/database.php';
require_once 'config/acs.php';
require_once 'classes/Database.php';

// Simple authentication
if (!isset($_SESSION['authenticated'])) {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        
        if ($username === ADMIN_USERNAME && password_verify($password, ADMIN_PASSWORD)) {
            $_SESSION['authenticated'] = true;
            $_SESSION['username'] = $username;
            header('Location: index.php');
            exit;
        } else {
            $login_error = "Credenciales incorrectas";
        }
    }
    
    // Show login form
    include 'templates/login.php';
    exit;
}

// Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: index.php');
    exit;
}

// Initialize database
$database = new Database();
$db = $database->getConnection();

// Get statistics
$stats = [];

// Total devices
$stmt = $db->query("SELECT COUNT(*) as count FROM devices");
$stats['total_devices'] = $stmt->fetch()['count'];

// Online devices (last inform within 5 minutes)
$stmt = $db->query("SELECT COUNT(*) as count FROM devices WHERE last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE)");
$stats['online_devices'] = $stmt->fetch()['count'];

// Pending tasks
$stmt = $db->query("SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'");
$stats['pending_tasks'] = $stmt->fetch()['count'];

// Recent events
$stmt = $db->query("SELECT COUNT(*) as count FROM events WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)");
$stats['recent_events'] = $stmt->fetch()['count'];

// Get recent devices
$stmt = $db->query("
    SELECT d.*, 
           CASE 
               WHEN d.last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
               WHEN d.last_inform > DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 'recent'
               ELSE 'offline'
           END as connection_status
    FROM devices d 
    ORDER BY d.last_inform DESC 
    LIMIT 10
");
$recent_devices = $stmt->fetchAll();

// Get recent events
$stmt = $db->query("
    SELECT e.*, d.serial_number, d.oui 
    FROM events e
    LEFT JOIN devices d ON e.device_id = d.id
    ORDER BY e.created_at DESC 
    LIMIT 20
");
$recent_events = $stmt->fetchAll();

$page_title = "Dashboard";
include 'templates/header.php';
?>

<div class="dashboard">
    <!-- Statistics Cards -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon">📱</div>
            <div class="stat-content">
                <h3><?= $stats['total_devices'] ?></h3>
                <p>Total Dispositivos</p>
            </div>
        </div>
        
        <div class="stat-card online">
            <div class="stat-icon">🟢</div>
            <div class="stat-content">
                <h3><?= $stats['online_devices'] ?></h3>
                <p>Dispositivos Online</p>
            </div>
        </div>
        
        <div class="stat-card pending">
            <div class="stat-icon">⏳</div>
            <div class="stat-content">
                <h3><?= $stats['pending_tasks'] ?></h3>
                <p>Tareas Pendientes</p>
            </div>
        </div>
        
        <div class="stat-card events">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
                <h3><?= $stats['recent_events'] ?></h3>
                <p>Eventos (1h)</p>
            </div>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <!-- Recent Devices -->
        <div class="dashboard-section">
            <div class="section-header">
                <h2>Dispositivos Recientes</h2>
                <a href="devices.php" class="btn btn-small">Ver Todos</a>
            </div>
            
            <div class="device-list">
                <?php if (empty($recent_devices)): ?>
                    <div class="empty-state">
                        <p>No hay dispositivos registrados aún.</p>
                        <p>Los dispositivos aparecerán aquí cuando se conecten al ACS.</p>
                    </div>
                <?php else: ?>
                    <?php foreach ($recent_devices as $device): ?>
                        <div class="device-item">
                            <div class="device-status <?= $device['connection_status'] ?>"></div>
                            <div class="device-info">
                                <strong><?= htmlspecialchars($device['oui'] . '-' . $device['serial_number']) ?></strong>
                                <div class="device-details">
                                    <?= htmlspecialchars($device['manufacturer'] ?? 'Unknown') ?> 
                                    <?= htmlspecialchars($device['model_name'] ?? '') ?>
                                </div>
                                <div class="device-meta">
                                    IP: <?= htmlspecialchars($device['ip_address'] ?? 'Unknown') ?> | 
                                    Última conexión: <?= $device['last_inform'] ? date('d/m/Y H:i', strtotime($device['last_inform'])) : 'Nunca' ?>
                                </div>
                            </div>
                            <div class="device-actions">
                                <a href="device.php?id=<?= $device['id'] ?>" class="btn btn-small">Ver</a>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
        
        <!-- Recent Events -->
        <div class="dashboard-section">
            <div class="section-header">
                <h2>Eventos Recientes</h2>
                <a href="events.php" class="btn btn-small">Ver Todos</a>
            </div>
            
            <div class="event-list">
                <?php if (empty($recent_events)): ?>
                    <div class="empty-state">
                        <p>No hay eventos recientes.</p>
                    </div>
                <?php else: ?>
                    <?php foreach ($recent_events as $event): ?>
                        <div class="event-item severity-<?= $event['severity'] ?>">
                            <div class="event-time">
                                <?= date('H:i', strtotime($event['created_at'])) ?>
                            </div>
                            <div class="event-content">
                                <div class="event-type"><?= htmlspecialchars($event['event_type']) ?></div>
                                <div class="event-device">
                                    <?= $event['serial_number'] ? htmlspecialchars($event['oui'] . '-' . $event['serial_number']) : 'Sistema' ?>
                                </div>
                                <?php if ($event['message']): ?>
                                    <div class="event-message"><?= htmlspecialchars($event['message']) ?></div>
                                <?php endif; ?>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<?php include 'templates/footer.php'; ?>