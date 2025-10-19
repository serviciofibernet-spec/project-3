<?php
/**
 * Individual Device Management Page
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

$device_id = $_GET['id'] ?? '';

if (empty($device_id)) {
    header('Location: devices.php');
    exit;
}

// Get device information
$stmt = $db->prepare("
    SELECT d.*,
           CASE 
               WHEN d.last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
               ELSE 'offline'
           END as connection_status
    FROM devices d 
    WHERE d.id = ?
");
$stmt->execute([$device_id]);
$device = $stmt->fetch();

if (!$device) {
    header('Location: devices.php');
    exit;
}

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    switch ($action) {
        case 'reboot':
            $stmt = $db->prepare("
                INSERT INTO tasks (device_id, type, status, priority)
                VALUES (?, 'Reboot', 'pending', 1)
            ");
            $stmt->execute([$device_id]);
            $success_message = "Tarea de reinicio programada";
            break;
            
        case 'get_params':
            $parameters = array_filter(explode("\n", $_POST['parameters'] ?? ''));
            if (!empty($parameters)) {
                $task_params = json_encode(['names' => $parameters]);
                
                $stmt = $db->prepare("
                    INSERT INTO tasks (device_id, type, parameters, status, priority)
                    VALUES (?, 'GetParameterValues', ?, 'pending', 3)
                ");
                $stmt->execute([$device_id, $task_params]);
                $success_message = "Tarea de obtención de parámetros programada";
            }
            break;
            
        case 'set_params':
            $param_lines = array_filter(explode("\n", $_POST['param_values'] ?? ''));
            $param_values = [];
            
            foreach ($param_lines as $line) {
                $parts = explode('=', $line, 2);
                if (count($parts) === 2) {
                    $param_values[trim($parts[0])] = trim($parts[1]);
                }
            }
            
            if (!empty($param_values)) {
                $task_params = json_encode(['values' => $param_values]);
                
                $stmt = $db->prepare("
                    INSERT INTO tasks (device_id, type, parameters, status, priority)
                    VALUES (?, 'SetParameterValues', ?, 'pending', 2)
                ");
                $stmt->execute([$device_id, $task_params]);
                $success_message = "Tarea de configuración programada";
            }
            break;
    }
}

// Get device parameters
$stmt = $db->prepare("
    SELECT * FROM parameters 
    WHERE device_id = ? 
    ORDER BY name ASC
");
$stmt->execute([$device_id]);
$parameters = $stmt->fetchAll();

// Get recent tasks
$stmt = $db->prepare("
    SELECT * FROM tasks 
    WHERE device_id = ? 
    ORDER BY created_at DESC 
    LIMIT 10
");
$stmt->execute([$device_id]);
$recent_tasks = $stmt->fetchAll();

// Get recent events
$stmt = $db->prepare("
    SELECT * FROM events 
    WHERE device_id = ? 
    ORDER BY created_at DESC 
    LIMIT 20
");
$stmt->execute([$device_id]);
$recent_events = $stmt->fetchAll();

$page_title = "Dispositivo " . $device['oui'] . '-' . $device['serial_number'];
include 'templates/header.php';
?>

<div class="page-header">
    <h1 class="page-title"><?= htmlspecialchars($device['oui'] . '-' . $device['serial_number']) ?></h1>
    <p class="page-subtitle">
        <?= htmlspecialchars($device['manufacturer'] ?? 'Unknown') ?> 
        <?= htmlspecialchars($device['model_name'] ?? '') ?>
        - Estado: 
        <span class="badge badge-<?= $device['connection_status'] ?>">
            <?= $device['connection_status'] === 'online' ? 'Online' : 'Offline' ?>
        </span>
    </p>
</div>

<?php if (isset($success_message)): ?>
    <div class="alert alert-success"><?= htmlspecialchars($success_message) ?></div>
<?php endif; ?>

<div class="device-tabs">
    <div class="tab-buttons">
        <button class="tab-button active" onclick="showTab('info')">Información</button>
        <button class="tab-button" onclick="showTab('parameters')">Parámetros</button>
        <button class="tab-button" onclick="showTab('tasks')">Tareas</button>
        <button class="tab-button" onclick="showTab('events')">Eventos</button>
        <button class="tab-button" onclick="showTab('actions')">Acciones</button>
    </div>
    
    <!-- Device Info Tab -->
    <div id="info-tab" class="tab-content active">
        <div class="info-grid">
            <div class="info-card">
                <h3>Información del Dispositivo</h3>
                <table class="info-table">
                    <tr><td><strong>Serial Number:</strong></td><td><?= htmlspecialchars($device['serial_number']) ?></td></tr>
                    <tr><td><strong>OUI:</strong></td><td><?= htmlspecialchars($device['oui']) ?></td></tr>
                    <tr><td><strong>Product Class:</strong></td><td><?= htmlspecialchars($device['product_class'] ?? 'N/A') ?></td></tr>
                    <tr><td><strong>Manufacturer:</strong></td><td><?= htmlspecialchars($device['manufacturer'] ?? 'N/A') ?></td></tr>
                    <tr><td><strong>Model:</strong></td><td><?= htmlspecialchars($device['model_name'] ?? 'N/A') ?></td></tr>
                    <tr><td><strong>Software Version:</strong></td><td><?= htmlspecialchars($device['software_version'] ?? 'N/A') ?></td></tr>
                    <tr><td><strong>Hardware Version:</strong></td><td><?= htmlspecialchars($device['hardware_version'] ?? 'N/A') ?></td></tr>
                </table>
            </div>
            
            <div class="info-card">
                <h3>Estado de Conexión</h3>
                <table class="info-table">
                    <tr><td><strong>IP Address:</strong></td><td><?= htmlspecialchars($device['ip_address'] ?? 'Unknown') ?></td></tr>
                    <tr><td><strong>MAC Address:</strong></td><td><?= htmlspecialchars($device['mac_address'] ?? 'N/A') ?></td></tr>
                    <tr><td><strong>Última Conexión:</strong></td><td>
                        <?php if ($device['last_inform']): ?>
                            <?= date('d/m/Y H:i:s', strtotime($device['last_inform'])) ?>
                        <?php else: ?>
                            Nunca
                        <?php endif; ?>
                    </td></tr>
                    <tr><td><strong>Último Boot:</strong></td><td>
                        <?php if ($device['last_boot']): ?>
                            <?= date('d/m/Y H:i:s', strtotime($device['last_boot'])) ?>
                        <?php else: ?>
                            N/A
                        <?php endif; ?>
                    </td></tr>
                    <tr><td><strong>Connection Request URL:</strong></td><td><?= htmlspecialchars($device['connection_request_url'] ?? 'N/A') ?></td></tr>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Parameters Tab -->
    <div id="parameters-tab" class="tab-content">
        <div class="parameters-section">
            <h3>Parámetros del Dispositivo</h3>
            <?php if (empty($parameters)): ?>
                <p>No hay parámetros disponibles para este dispositivo.</p>
            <?php else: ?>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Valor</th>
                            <th>Tipo</th>
                            <th>Última Actualización</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($parameters as $param): ?>
                            <tr>
                                <td style="font-family: monospace; font-size: 12px;"><?= htmlspecialchars($param['name']) ?></td>
                                <td><?= htmlspecialchars($param['value']) ?></td>
                                <td><?= htmlspecialchars($param['type']) ?></td>
                                <td><?= date('d/m/Y H:i', strtotime($param['last_updated'])) ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
    
    <!-- Tasks Tab -->
    <div id="tasks-tab" class="tab-content">
        <div class="tasks-section">
            <h3>Tareas Recientes</h3>
            <?php if (empty($recent_tasks)): ?>
                <p>No hay tareas para este dispositivo.</p>
            <?php else: ?>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Tipo</th>
                            <th>Estado</th>
                            <th>Creada</th>
                            <th>Completada</th>
                            <th>Resultado</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($recent_tasks as $task): ?>
                            <tr>
                                <td><?= htmlspecialchars($task['type']) ?></td>
                                <td><span class="badge badge-<?= $task['status'] ?>"><?= htmlspecialchars($task['status']) ?></span></td>
                                <td><?= date('d/m/Y H:i', strtotime($task['created_at'])) ?></td>
                                <td>
                                    <?php if ($task['completed_at']): ?>
                                        <?= date('d/m/Y H:i', strtotime($task['completed_at'])) ?>
                                    <?php else: ?>
                                        -
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <?php if ($task['error_message']): ?>
                                        <span style="color: #e53e3e;"><?= htmlspecialchars($task['error_message']) ?></span>
                                    <?php elseif ($task['result']): ?>
                                        <span style="color: #38a169;">Completada</span>
                                    <?php else: ?>
                                        -
                                    <?php endif; ?>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
    
    <!-- Events Tab -->
    <div id="events-tab" class="tab-content">
        <div class="events-section">
            <h3>Eventos Recientes</h3>
            <?php if (empty($recent_events)): ?>
                <p>No hay eventos para este dispositivo.</p>
            <?php else: ?>
                <div class="event-list">
                    <?php foreach ($recent_events as $event): ?>
                        <div class="event-item severity-<?= $event['severity'] ?>">
                            <div class="event-time">
                                <?= date('d/m H:i', strtotime($event['created_at'])) ?>
                            </div>
                            <div class="event-content">
                                <div class="event-type"><?= htmlspecialchars($event['event_type']) ?></div>
                                <?php if ($event['event_code']): ?>
                                    <div class="event-device">Código: <?= htmlspecialchars($event['event_code']) ?></div>
                                <?php endif; ?>
                                <?php if ($event['message']): ?>
                                    <div class="event-message"><?= htmlspecialchars($event['message']) ?></div>
                                <?php endif; ?>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
    
    <!-- Actions Tab -->
    <div id="actions-tab" class="tab-content">
        <div class="actions-grid">
            <!-- Reboot Device -->
            <div class="action-card">
                <h3>Reiniciar Dispositivo</h3>
                <p>Envía un comando de reinicio al dispositivo.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="reboot">
                    <button type="submit" class="btn confirm-action">Reiniciar Dispositivo</button>
                </form>
            </div>
            
            <!-- Get Parameters -->
            <div class="action-card">
                <h3>Obtener Parámetros</h3>
                <p>Solicita valores de parámetros específicos del dispositivo.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="get_params">
                    <textarea name="parameters" placeholder="Device.WiFi.SSID.1.SSID&#10;Device.WiFi.Radio.1.Enable&#10;Device.DeviceInfo.SoftwareVersion" 
                              style="width: 100%; height: 100px; margin: 10px 0; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;"></textarea>
                    <button type="submit" class="btn">Obtener Parámetros</button>
                </form>
            </div>
            
            <!-- Set Parameters -->
            <div class="action-card">
                <h3>Configurar Parámetros</h3>
                <p>Establece valores de parámetros en el dispositivo.</p>
                <form method="POST">
                    <input type="hidden" name="action" value="set_params">
                    <textarea name="param_values" placeholder="Device.WiFi.SSID.1.SSID=MyNetwork&#10;Device.WiFi.Radio.1.Enable=true" 
                              style="width: 100%; height: 100px; margin: 10px 0; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;"></textarea>
                    <button type="submit" class="btn confirm-action">Configurar Parámetros</button>
                </form>
            </div>
        </div>
    </div>
</div>

<style>
.alert {
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 20px;
}

.alert-success {
    background: #f0fff4;
    color: #38a169;
    border-left: 4px solid #38a169;
}

.device-tabs {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow: hidden;
}

.tab-buttons {
    display: flex;
    border-bottom: 1px solid #e2e8f0;
}

.tab-button {
    padding: 15px 20px;
    border: none;
    background: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: #666;
    border-bottom: 2px solid transparent;
    transition: all 0.3s;
}

.tab-button:hover {
    background: #f7fafc;
}

.tab-button.active {
    color: #667eea;
    border-bottom-color: #667eea;
    background: #f7fafc;
}

.tab-content {
    display: none;
    padding: 20px;
}

.tab-content.active {
    display: block;
}

.info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.info-card {
    background: #f7fafc;
    padding: 20px;
    border-radius: 8px;
}

.info-card h3 {
    margin-bottom: 15px;
    font-size: 16px;
    font-weight: 600;
}

.info-table {
    width: 100%;
}

.info-table td {
    padding: 8px 0;
    border-bottom: 1px solid #e2e8f0;
}

.info-table td:first-child {
    width: 40%;
    color: #666;
}

.actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.action-card {
    background: #f7fafc;
    padding: 20px;
    border-radius: 8px;
}

.action-card h3 {
    margin-bottom: 10px;
    font-size: 16px;
    font-weight: 600;
}

.action-card p {
    color: #666;
    margin-bottom: 15px;
    font-size: 14px;
}

@media (max-width: 768px) {
    .info-grid {
        grid-template-columns: 1fr;
    }
    
    .tab-buttons {
        flex-wrap: wrap;
    }
    
    .tab-button {
        flex: 1;
        min-width: 120px;
    }
}
</style>

<script>
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
}
</script>

<?php include 'templates/footer.php'; ?>