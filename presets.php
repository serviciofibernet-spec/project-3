<?php
/**
 * Configuration Presets Management Page
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

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'create_preset') {
        $name = $_POST['name'] ?? '';
        $description = $_POST['description'] ?? '';
        $param_lines = array_filter(explode("\n", $_POST['parameters'] ?? ''));
        
        $param_values = [];
        foreach ($param_lines as $line) {
            $parts = explode('=', $line, 2);
            if (count($parts) === 2) {
                $param_values[trim($parts[0])] = trim($parts[1]);
            }
        }
        
        if (!empty($name) && !empty($param_values)) {
            try {
                $stmt = $db->prepare("
                    INSERT INTO presets (name, description, parameters)
                    VALUES (?, ?, ?)
                ");
                $stmt->execute([$name, $description, json_encode($param_values)]);
                $success_message = "Preset creado exitosamente";
            } catch (Exception $e) {
                $error_message = "Error al crear preset: " . $e->getMessage();
            }
        } else {
            $error_message = "Nombre y parámetros son obligatorios";
        }
    }
    
    if ($action === 'apply_preset') {
        $preset_id = $_POST['preset_id'] ?? '';
        $device_ids = $_POST['device_ids'] ?? [];
        
        if (!empty($preset_id) && !empty($device_ids)) {
            // Get preset
            $stmt = $db->prepare("SELECT * FROM presets WHERE id = ?");
            $stmt->execute([$preset_id]);
            $preset = $stmt->fetch();
            
            if ($preset) {
                $task_params = json_encode(['values' => json_decode($preset['parameters'], true)]);
                
                foreach ($device_ids as $device_id) {
                    $stmt = $db->prepare("
                        INSERT INTO tasks (device_id, type, parameters, status, priority)
                        VALUES (?, 'SetParameterValues', ?, 'pending', 2)
                    ");
                    $stmt->execute([$device_id, $task_params]);
                }
                
                $success_message = "Preset aplicado a " . count($device_ids) . " dispositivo(s)";
            }
        }
    }
}

// Get presets
$stmt = $db->query("SELECT * FROM presets ORDER BY created_at DESC");
$presets = $stmt->fetchAll();

// Get devices for preset application
$stmt = $db->query("
    SELECT id, serial_number, oui, manufacturer, model_name,
           CASE 
               WHEN last_inform > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
               ELSE 'offline'
           END as connection_status
    FROM devices 
    ORDER BY last_inform DESC
");
$devices = $stmt->fetchAll();

$page_title = "Presets de Configuración";
include 'templates/header.php';
?>

<div class="page-header">
    <h1 class="page-title">Presets de Configuración</h1>
    <p class="page-subtitle">Plantillas de configuración reutilizables para dispositivos</p>
</div>

<?php if (isset($success_message)): ?>
    <div class="alert alert-success"><?= htmlspecialchars($success_message) ?></div>
<?php endif; ?>

<?php if (isset($error_message)): ?>
    <div class="alert alert-error"><?= htmlspecialchars($error_message) ?></div>
<?php endif; ?>

<div class="presets-grid">
    <!-- Create New Preset -->
    <div class="preset-card create-card">
        <h3>Crear Nuevo Preset</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_preset">
            
            <div class="form-group">
                <label for="name">Nombre del Preset:</label>
                <input type="text" id="name" name="name" required 
                       style="width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;">
            </div>
            
            <div class="form-group">
                <label for="description">Descripción:</label>
                <textarea id="description" name="description" 
                          style="width: 100%; height: 60px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;"></textarea>
            </div>
            
            <div class="form-group">
                <label for="parameters">Parámetros (uno por línea, formato: nombre=valor):</label>
                <textarea id="parameters" name="parameters" required
                          placeholder="Device.WiFi.SSID.1.SSID=MyNetwork&#10;Device.WiFi.Radio.1.Enable=true&#10;Device.WiFi.AccessPoint.1.Security.ModeEnabled=WPA2-PSK"
                          style="width: 100%; height: 120px; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-family: monospace; font-size: 12px;"></textarea>
            </div>
            
            <button type="submit" class="btn">Crear Preset</button>
        </form>
    </div>
    
    <!-- Existing Presets -->
    <?php foreach ($presets as $preset): ?>
        <div class="preset-card">
            <div class="preset-header">
                <h3><?= htmlspecialchars($preset['name']) ?></h3>
                <small style="color: #666;">Creado: <?= date('d/m/Y', strtotime($preset['created_at'])) ?></small>
            </div>
            
            <?php if ($preset['description']): ?>
                <p class="preset-description"><?= htmlspecialchars($preset['description']) ?></p>
            <?php endif; ?>
            
            <div class="preset-parameters">
                <strong>Parámetros:</strong>
                <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px; font-family: monospace;">
                    <?php 
                    $params = json_decode($preset['parameters'], true);
                    foreach ($params as $name => $value): 
                    ?>
                        <li><?= htmlspecialchars($name) ?> = <?= htmlspecialchars($value) ?></li>
                    <?php endforeach; ?>
                </ul>
            </div>
            
            <!-- Apply Preset Form -->
            <form method="POST" style="margin-top: 15px;">
                <input type="hidden" name="action" value="apply_preset">
                <input type="hidden" name="preset_id" value="<?= $preset['id'] ?>">
                
                <label style="font-size: 12px; font-weight: 500;">Aplicar a dispositivos:</label>
                <div style="max-height: 150px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 4px; padding: 5px; margin: 5px 0;">
                    <?php foreach ($devices as $device): ?>
                        <label style="display: block; padding: 2px 5px; font-size: 11px; font-weight: normal;">
                            <input type="checkbox" name="device_ids[]" value="<?= $device['id'] ?>" 
                                   <?= $device['connection_status'] === 'offline' ? 'disabled title="Dispositivo offline"' : '' ?>>
                            <?= htmlspecialchars($device['oui'] . '-' . $device['serial_number']) ?>
                            <span class="badge badge-<?= $device['connection_status'] ?>" style="margin-left: 5px; font-size: 10px;">
                                <?= $device['connection_status'] ?>
                            </span>
                        </label>
                    <?php endforeach; ?>
                </div>
                
                <button type="submit" class="btn btn-small confirm-action">Aplicar Preset</button>
            </form>
        </div>
    <?php endforeach; ?>
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

.alert-error {
    background: #fed7d7;
    color: #e53e3e;
    border-left: 4px solid #e53e3e;
}

.presets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}

.preset-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 20px;
}

.create-card {
    background: #f7fafc;
    border: 2px dashed #cbd5e0;
}

.preset-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.preset-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}

.preset-description {
    color: #666;
    font-size: 14px;
    margin-bottom: 15px;
}

.preset-parameters {
    background: #f7fafc;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 15px;
    font-size: 12px;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    font-size: 12px;
}

@media (max-width: 768px) {
    .presets-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<?php include 'templates/footer.php'; ?>