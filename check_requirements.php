<?php
/**
 * TR-069 ACS System Requirements Checker
 * Run this script to verify your system meets all requirements
 */

header('Content-Type: text/html; charset=utf-8');

function checkRequirement($name, $status, $message = '') {
    $icon = $status ? '✅' : '❌';
    $class = $status ? 'success' : 'error';
    echo "<div class='requirement $class'>";
    echo "<span class='icon'>$icon</span>";
    echo "<div class='info'>";
    echo "<strong>$name</strong>";
    if ($message) echo "<br><small>$message</small>";
    echo "</div>";
    echo "</div>";
    return $status;
}

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TR-069 ACS - Verificación de Requisitos</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        .requirement {
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .requirement.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .requirement.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .requirement .icon {
            font-size: 24px;
            margin-right: 15px;
        }
        .requirement .info {
            flex: 1;
        }
        .requirement strong {
            color: #333;
        }
        .requirement small {
            color: #666;
            font-size: 12px;
        }
        .summary {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 5px;
            padding: 20px;
            margin-top: 30px;
            text-align: center;
        }
        .summary.error {
            background: #f8d7da;
            border: 1px solid #dc3545;
        }
        .summary h2 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        .summary.error h2 {
            color: #dc3545;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 15px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #5568d3;
        }
        .info-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Verificación de Requisitos</h1>
        <p class="subtitle">TR-069 ACS Server</p>
        
        <?php
        $allOk = true;
        
        // PHP Version
        echo '<div class="section">';
        echo '<div class="section-title">🐘 PHP</div>';
        
        $phpVersion = PHP_VERSION;
        $phpOk = version_compare($phpVersion, '7.4.0', '>=');
        $allOk &= checkRequirement(
            'Versión de PHP',
            $phpOk,
            "Versión actual: $phpVersion " . ($phpOk ? '(OK)' : '(Se requiere 7.4 o superior)')
        );
        
        // Required Extensions
        echo '<div class="section-title" style="margin-top: 20px;">🧩 Extensiones PHP Requeridas</div>';
        
        $extensions = [
            'pdo' => 'PDO (PHP Data Objects)',
            'pdo_mysql' => 'PDO MySQL Driver',
            'soap' => 'SOAP (para protocolo TR-069)',
            'simplexml' => 'SimpleXML (para parsear SOAP)',
            'json' => 'JSON',
            'mbstring' => 'Multibyte String',
        ];
        
        foreach ($extensions as $ext => $name) {
            $loaded = extension_loaded($ext);
            $allOk &= checkRequirement($name, $loaded);
        }
        
        // Recommended Extensions
        echo '<div class="section-title" style="margin-top: 20px;">💡 Extensiones Recomendadas</div>';
        
        $recommended = [
            'curl' => 'cURL (para connection requests)',
            'openssl' => 'OpenSSL (para HTTPS)',
            'zip' => 'ZIP (para backups)'
        ];
        
        foreach ($recommended as $ext => $name) {
            $loaded = extension_loaded($ext);
            checkRequirement($name, $loaded, $loaded ? '' : 'Opcional pero recomendado');
        }
        
        // File Permissions
        echo '<div class="section-title" style="margin-top: 20px;">📁 Permisos de Archivos</div>';
        
        $writable = is_writable(__DIR__);
        $allOk &= checkRequirement(
            'Directorio de instalación',
            $writable,
            $writable ? 'Tiene permisos de escritura' : 'No tiene permisos de escritura'
        );
        
        $logsDir = __DIR__ . '/logs';
        if (is_dir($logsDir)) {
            $logsWritable = is_writable($logsDir);
            checkRequirement(
                'Directorio de logs',
                $logsWritable,
                $logsWritable ? 'Tiene permisos de escritura' : 'No tiene permisos de escritura'
            );
        } else {
            checkRequirement(
                'Directorio de logs',
                false,
                'No existe (se creará automáticamente)'
            );
        }
        
        // Database Connection Test (if config exists)
        if (file_exists(__DIR__ . '/config.php')) {
            echo '<div class="section-title" style="margin-top: 20px;">🗄️ Base de Datos</div>';
            
            try {
                $config = require __DIR__ . '/config.php';
                $dsn = sprintf(
                    "mysql:host=%s;port=%d;dbname=%s;charset=%s",
                    $config['db']['host'],
                    $config['db']['port'],
                    $config['db']['database'],
                    $config['db']['charset']
                );
                $pdo = new PDO($dsn, $config['db']['username'], $config['db']['password']);
                $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                
                checkRequirement(
                    'Conexión a la base de datos',
                    true,
                    'Conectado a ' . $config['db']['database']
                );
                
                // Check tables
                $stmt = $pdo->query("SHOW TABLES");
                $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
                $requiredTables = ['devices', 'parameters', 'tasks', 'inform_log', 'users', 'config'];
                $tablesOk = count(array_intersect($tables, $requiredTables)) === count($requiredTables);
                
                checkRequirement(
                    'Tablas de la base de datos',
                    $tablesOk,
                    $tablesOk ? 'Todas las tablas presentes' : 'Faltan tablas (ejecutar install.php)'
                );
                
            } catch (PDOException $e) {
                checkRequirement(
                    'Conexión a la base de datos',
                    false,
                    'Error: ' . $e->getMessage()
                );
            }
        }
        
        // Server Information
        echo '<div class="section-title" style="margin-top: 20px;">ℹ️ Información del Servidor</div>';
        echo '<div class="info-box">';
        echo '<strong>Sistema Operativo:</strong> ' . PHP_OS . '<br>';
        echo '<strong>Servidor Web:</strong> ' . ($_SERVER['SERVER_SOFTWARE'] ?? 'Desconocido') . '<br>';
        echo '<strong>PHP SAPI:</strong> ' . php_sapi_name() . '<br>';
        echo '<strong>Memoria Límite:</strong> ' . ini_get('memory_limit') . '<br>';
        echo '<strong>Max Execution Time:</strong> ' . ini_get('max_execution_time') . 's<br>';
        echo '<strong>Post Max Size:</strong> ' . ini_get('post_max_size') . '<br>';
        echo '<strong>Upload Max Filesize:</strong> ' . ini_get('upload_max_filesize');
        echo '</div>';
        
        echo '</div>'; // Close section
        
        // Summary
        if ($allOk) {
            echo '<div class="summary">';
            echo '<h2>✅ ¡Sistema Listo!</h2>';
            echo '<p>Tu sistema cumple con todos los requisitos para ejecutar TR-069 ACS.</p>';
            if (!file_exists(__DIR__ . '/config.php')) {
                echo '<a href="install.php" class="btn">Proceder a la Instalación →</a>';
            } else {
                echo '<a href="index.php" class="btn">Ir al Dashboard →</a>';
            }
            echo '</div>';
        } else {
            echo '<div class="summary error">';
            echo '<h2>❌ Requisitos No Cumplidos</h2>';
            echo '<p>Por favor, instala las extensiones faltantes y verifica los permisos antes de continuar.</p>';
            echo '<a href="#" onclick="location.reload()" class="btn">Verificar Nuevamente</a>';
            echo '</div>';
        }
        ?>
    </div>
</body>
</html>
