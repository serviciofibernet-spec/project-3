<?php
/**
 * Devices Management Page
 */

session_start();

// Check authentication
if (!isset($_SESSION['authenticated'])) {
    header('Location: index.php');
    exit;
}

require_once 'config/database.php';
require_once 'classes/Database.php';

$database = new Database();
$db = $database->getConnection();

// Handle device actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $device_id = $_POST['device_id'] ?? '';
    
    switch ($action) {
        case 'reboot':
            if ($device_id) {
                $stmt = $db->prepare("
                    INSERT INTO tasks (device_id, type, status, priority)
                    VALUES (?, 'Reboot', 'pending', 1)
                ");
                $stmt->execute([$device_id]);
                $success_message = "Tarea de reinicio programada";
            }
            break;
            
        case 'get_params':
            if ($device_id && isset($_POST['parameters'])) {
                $parameters = array_filter(explode("\n", $_POST['parameters']));
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
            if ($device_id && isset($_POST['param_values'])) {
                $param_lines = array_filter(explode("\n", $_POST['param_values']));
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
                    $success_message = "Tarea de configuración de parámetros programada";
                }
            }
            break;
    }
}

// Get devices with pagination
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$per_page = 20;
$offset = ($page - 1) * $per_page;

$search = $_GET['search'] ?? '';
$status_filter = $_GET['status'] ?? '';

$where_conditions = [];
$params = [];

if (!empty($search)) {
    $where_conditions[] = "(d.serial_number LIKE ? OR d.oui LIKE ? OR d.manufacturer LIKE ? OR d.model_name LIKE ?)";
    $search_param = "%$search%";
    $params = array_merge($params, [$search_param, $search_param, $search_param, $search_param]);
}

if (!empty($status_filter)) {
    if ($status_filter === 'online') {
        $where_conditions[] = "d.last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE)";
    } elseif ($status_filter === 'offline') {
        $where_conditions[] = "(d.last_inform IS NULL OR d.last_inform <= DATE_SUB(NOW(), INTERVAL 5 MINUTE))";
    }
}

$where_clause = !empty($where_conditions) ? 'WHERE ' . implode(' AND ', $where_conditions) : '';

// Get total count
$count_sql = "SELECT COUNT(*) as count FROM devices d $where_clause";
$stmt = $db->prepare($count_sql);
$stmt->execute($params);
$total_devices = $stmt->fetch()['count'];
$total_pages = ceil($total_devices / $per_page);

// Get devices
$sql = "
    SELECT d.*,
           CASE 
               WHEN d.last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
               ELSE 'offline'
           END as connection_status,
           (SELECT COUNT(*) FROM tasks t WHERE t.device_id = d.id AND t.status = 'pending') as pending_tasks
    FROM devices d 
    $where_clause
    ORDER BY d.last_inform DESC 
    LIMIT $per_page OFFSET $offset
";

$stmt = $db->prepare($sql);
$stmt->execute($params);
$devices = $stmt->fetchAll();

$page_title = "Dispositivos";
include 'templates/header.php';
?>

<div class="page-header">
    <h1 class="page-title">Dispositivos</h1>
    <p class="page-subtitle">Gestión y monitoreo de dispositivos CPE</p>
</div>

<?php if (isset($success_message)): ?>
    <div class="alert alert-success"><?= htmlspecialchars($success_message) ?></div>
<?php endif; ?>

<!-- Filters -->
<div class="filters" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <form method="GET" style="display: flex; gap: 15px; align-items: center;">
        <input type="text" name="search" placeholder="Buscar por serial, OUI, fabricante..." 
               value="<?= htmlspecialchars($search) ?>" 
               style="flex: 1; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 4px;">
        
        <select name="status" style="padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 4px;">
            <option value="">Todos los estados</option>
            <option value="online" <?= $status_filter === 'online' ? 'selected' : '' ?>>Online</option>
            <option value="offline" <?= $status_filter === 'offline' ? 'selected' : '' ?>>Offline</option>
        </select>
        
        <button type="submit" class="btn">Filtrar</button>
        <?php if (!empty($search) || !empty($status_filter)): ?>
            <a href="devices.php" class="btn btn-secondary">Limpiar</a>
        <?php endif; ?>
    </form>
</div>

<!-- Devices Table -->
<table class="table">
    <thead>
        <tr>
            <th>Estado</th>
            <th>Dispositivo</th>
            <th>Fabricante/Modelo</th>
            <th>IP Address</th>
            <th>Última Conexión</th>
            <th>Tareas</th>
            <th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        <?php if (empty($devices)): ?>
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                    No se encontraron dispositivos
                </td>
            </tr>
        <?php else: ?>
            <?php foreach ($devices as $device): ?>
                <tr>
                    <td>
                        <span class="badge badge-<?= $device['connection_status'] ?>">
                            <?= $device['connection_status'] === 'online' ? 'Online' : 'Offline' ?>
                        </span>
                    </td>
                    <td>
                        <strong><?= htmlspecialchars($device['oui'] . '-' . $device['serial_number']) ?></strong>
                        <?php if ($device['product_class']): ?>
                            <br><small style="color: #666;"><?= htmlspecialchars($device['product_class']) ?></small>
                        <?php endif; ?>
                    </td>
                    <td>
                        <?= htmlspecialchars($device['manufacturer'] ?? 'Unknown') ?>
                        <?php if ($device['model_name']): ?>
                            <br><small style="color: #666;"><?= htmlspecialchars($device['model_name']) ?></small>
                        <?php endif; ?>
                    </td>
                    <td><?= htmlspecialchars($device['ip_address'] ?? 'Unknown') ?></td>
                    <td>
                        <?php if ($device['last_inform']): ?>
                            <?= date('d/m/Y H:i', strtotime($device['last_inform'])) ?>
                        <?php else: ?>
                            <span style="color: #999;">Nunca</span>
                        <?php endif; ?>
                    </td>
                    <td>
                        <?php if ($device['pending_tasks'] > 0): ?>
                            <span class="badge badge-pending"><?= $device['pending_tasks'] ?> pendientes</span>
                        <?php else: ?>
                            <span style="color: #999;">Ninguna</span>
                        <?php endif; ?>
                    </td>
                    <td>
                        <a href="device.php?id=<?= $device['id'] ?>" class="btn btn-small">Ver</a>
                    </td>
                </tr>
            <?php endforeach; ?>
        <?php endif; ?>
    </tbody>
</table>

<!-- Pagination -->
<?php if ($total_pages > 1): ?>
    <div style="margin-top: 20px; text-align: center;">
        <?php for ($i = 1; $i <= $total_pages; $i++): ?>
            <?php if ($i === $page): ?>
                <span style="padding: 8px 12px; background: #667eea; color: white; border-radius: 4px; margin: 0 2px;"><?= $i ?></span>
            <?php else: ?>
                <a href="?page=<?= $i ?><?= !empty($search) ? '&search=' . urlencode($search) : '' ?><?= !empty($status_filter) ? '&status=' . urlencode($status_filter) : '' ?>" 
                   style="padding: 8px 12px; background: white; color: #667eea; border: 1px solid #667eea; border-radius: 4px; margin: 0 2px; text-decoration: none;"><?= $i ?></a>
            <?php endif; ?>
        <?php endfor; ?>
    </div>
<?php endif; ?>

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
</style>

<?php include 'templates/footer.php'; ?>