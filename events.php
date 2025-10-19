<?php
/**
 * Events Log Page
 */

session_start();

if (!isset($_SESSION['authenticated'])) {
    header('Location: index.php');
    exit;
}

require_once 'config/database.php';
require_once 'classes/Database.php';

$database = new Database();
$db = $database->getConnection();

// Get events with device information
$stmt = $db->query("
    SELECT e.*, d.serial_number, d.oui, d.manufacturer
    FROM events e
    LEFT JOIN devices d ON e.device_id = d.id
    ORDER BY e.created_at DESC
    LIMIT 200
");
$events = $stmt->fetchAll();

$page_title = "Eventos";
include 'templates/header.php';
?>

<div class="page-header">
    <h1 class="page-title">Eventos</h1>
    <p class="page-subtitle">Registro de eventos del sistema y dispositivos</p>
</div>

<div class="event-list" style="background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <?php if (empty($events)): ?>
        <div class="empty-state">
            <p>No hay eventos registrados</p>
        </div>
    <?php else: ?>
        <?php foreach ($events as $event): ?>
            <div class="event-item severity-<?= $event['severity'] ?>">
                <div class="event-time">
                    <?= date('d/m/Y H:i:s', strtotime($event['created_at'])) ?>
                </div>
                <div class="event-content">
                    <div class="event-type">
                        <?= htmlspecialchars($event['event_type']) ?>
                        <?php if ($event['event_code']): ?>
                            (<?= htmlspecialchars($event['event_code']) ?>)
                        <?php endif; ?>
                    </div>
                    <div class="event-device">
                        <?php if ($event['serial_number']): ?>
                            <a href="device.php?id=<?= $event['device_id'] ?>">
                                <?= htmlspecialchars($event['oui'] . '-' . $event['serial_number']) ?>
                            </a>
                        <?php else: ?>
                            Sistema
                        <?php endif; ?>
                    </div>
                    <?php if ($event['message']): ?>
                        <div class="event-message"><?= htmlspecialchars($event['message']) ?></div>
                    <?php endif; ?>
                    <?php if ($event['command_key']): ?>
                        <div class="event-message">Command Key: <?= htmlspecialchars($event['command_key']) ?></div>
                    <?php endif; ?>
                </div>
                <div class="event-severity">
                    <span class="badge badge-<?= $event['severity'] ?>"><?= htmlspecialchars($event['severity']) ?></span>
                </div>
            </div>
        <?php endforeach; ?>
    <?php endif; ?>
</div>

<style>
.event-item {
    display: flex;
    gap: 15px;
    padding: 15px 20px;
    border-bottom: 1px solid #f7fafc;
    align-items: flex-start;
}

.event-item:last-child {
    border-bottom: none;
}

.event-time {
    color: #666;
    font-size: 12px;
    min-width: 120px;
    font-family: monospace;
}

.event-content {
    flex: 1;
}

.event-type {
    font-weight: 500;
    font-size: 14px;
    margin-bottom: 2px;
}

.event-device {
    font-size: 12px;
    color: #666;
    margin-bottom: 2px;
}

.event-device a {
    color: #667eea;
    text-decoration: none;
}

.event-device a:hover {
    text-decoration: underline;
}

.event-message {
    color: #999;
    font-size: 12px;
}

.event-severity {
    min-width: 80px;
}

.badge-info {
    background: #e6f3ff;
    color: #0066cc;
}

.badge-warning {
    background: #fff3cd;
    color: #856404;
}

.badge-error {
    background: #f8d7da;
    color: #721c24;
}

.badge-critical {
    background: #721c24;
    color: white;
}
</style>

<?php include 'templates/footer.php'; ?>