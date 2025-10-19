<?php
/**
 * Tasks Management Page
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

// Get tasks with device information
$stmt = $db->query("
    SELECT t.*, d.serial_number, d.oui, d.manufacturer, d.model_name
    FROM tasks t
    LEFT JOIN devices d ON t.device_id = d.id
    ORDER BY t.created_at DESC
    LIMIT 100
");
$tasks = $stmt->fetchAll();

$page_title = "Tareas";
include 'templates/header.php';
?>

<div class="page-header">
    <h1 class="page-title">Tareas</h1>
    <p class="page-subtitle">Historial y estado de tareas enviadas a dispositivos</p>
</div>

<table class="table">
    <thead>
        <tr>
            <th>Dispositivo</th>
            <th>Tipo</th>
            <th>Estado</th>
            <th>Prioridad</th>
            <th>Creada</th>
            <th>Iniciada</th>
            <th>Completada</th>
            <th>Resultado</th>
        </tr>
    </thead>
    <tbody>
        <?php if (empty($tasks)): ?>
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #666;">
                    No hay tareas registradas
                </td>
            </tr>
        <?php else: ?>
            <?php foreach ($tasks as $task): ?>
                <tr>
                    <td>
                        <?php if ($task['serial_number']): ?>
                            <a href="device.php?id=<?= $task['device_id'] ?>">
                                <?= htmlspecialchars($task['oui'] . '-' . $task['serial_number']) ?>
                            </a>
                            <?php if ($task['manufacturer']): ?>
                                <br><small style="color: #666;"><?= htmlspecialchars($task['manufacturer']) ?></small>
                            <?php endif; ?>
                        <?php else: ?>
                            <span style="color: #999;">Dispositivo eliminado</span>
                        <?php endif; ?>
                    </td>
                    <td><?= htmlspecialchars($task['type']) ?></td>
                    <td>
                        <span class="badge badge-<?= $task['status'] ?>">
                            <?= htmlspecialchars($task['status']) ?>
                        </span>
                    </td>
                    <td><?= $task['priority'] ?></td>
                    <td><?= date('d/m/Y H:i', strtotime($task['created_at'])) ?></td>
                    <td>
                        <?php if ($task['started_at']): ?>
                            <?= date('d/m/Y H:i', strtotime($task['started_at'])) ?>
                        <?php else: ?>
                            -
                        <?php endif; ?>
                    </td>
                    <td>
                        <?php if ($task['completed_at']): ?>
                            <?= date('d/m/Y H:i', strtotime($task['completed_at'])) ?>
                        <?php else: ?>
                            -
                        <?php endif; ?>
                    </td>
                    <td>
                        <?php if ($task['error_message']): ?>
                            <span style="color: #e53e3e;" title="<?= htmlspecialchars($task['error_message']) ?>">Error</span>
                        <?php elseif ($task['result']): ?>
                            <span style="color: #38a169;">Éxito</span>
                        <?php else: ?>
                            -
                        <?php endif; ?>
                    </td>
                </tr>
            <?php endforeach; ?>
        <?php endif; ?>
    </tbody>
</table>

<?php include 'templates/footer.php'; ?>