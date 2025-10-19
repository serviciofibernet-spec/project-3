<?php
/**
 * Script de verificación de requisitos del sistema
 * Ejecutar desde la línea de comandos: php check_requirements.php
 * O desde el navegador antes de la instalación
 */

$requirements = [];
$errors = 0;
$warnings = 0;

// Función para mostrar resultados
function showResult($name, $status, $required = true, $message = '') {
    global $errors, $warnings;
    
    $icons = [
        'ok' => '✅',
        'error' => '❌',
        'warning' => '⚠️'
    ];
    
    if ($status === 'error' && $required) {
        $errors++;
    } elseif ($status === 'warning') {
        $warnings++;
    }
    
    $icon = $icons[$status] ?? '❓';
    
    if (PHP_SAPI === 'cli') {
        echo sprintf("%-40s %s %s\n", $name, $icon, $message);
    } else {
        return [
            'name' => $name,
            'status' => $status,
            'icon' => $icon,
            'message' => $message,
            'required' => $required
        ];
    }
}

// Verificar versión de PHP
$phpVersion = PHP_VERSION;
$phpOk = version_compare($phpVersion, '7.4.0', '>=');
$requirements[] = showResult(
    "PHP Version (actual: $phpVersion)",
    $phpOk ? 'ok' : 'error',
    true,
    $phpOk ? 'Compatible' : 'Requiere PHP 7.4 o superior'
);

// Verificar extensiones requeridas
$requiredExtensions = [
    'pdo' => 'PDO',
    'pdo_mysql' => 'PDO MySQL',
    'soap' => 'SOAP',
    'json' => 'JSON',
    'dom' => 'DOM',
    'simplexml' => 'SimpleXML',
    'mbstring' => 'Multibyte String'
];

foreach ($requiredExtensions as $ext => $name) {
    $loaded = extension_loaded($ext);
    $requirements[] = showResult(
        "Extensión $name",
        $loaded ? 'ok' : 'error',
        true,
        $loaded ? 'Instalada' : 'No instalada - Requerida'
    );
}

// Verificar extensiones opcionales
$optionalExtensions = [
    'openssl' => 'OpenSSL (para HTTPS)',
    'curl' => 'cURL (para connection requests)',
    'zip' => 'ZIP (para backups)',
    'gd' => 'GD (para gráficos)',
    'intl' => 'Intl (para internacionalización)'
];

foreach ($optionalExtensions as $ext => $name) {
    $loaded = extension_loaded($ext);
    $requirements[] = showResult(
        "Extensión $name",
        $loaded ? 'ok' : 'warning',
        false,
        $loaded ? 'Instalada' : 'No instalada - Opcional pero recomendada'
    );
}

// Verificar configuración de PHP
$configs = [
    'memory_limit' => [
        'value' => ini_get('memory_limit'),
        'required' => '128M',
        'check' => function($val) {
            $bytes = ini_parse_quantity($val);
            return $bytes >= 128 * 1024 * 1024;
        }
    ],
    'max_execution_time' => [
        'value' => ini_get('max_execution_time'),
        'required' => '300',
        'check' => function($val) {
            return $val == 0 || $val >= 300;
        }
    ],
    'post_max_size' => [
        'value' => ini_get('post_max_size'),
        'required' => '50M',
        'check' => function($val) {
            $bytes = ini_parse_quantity($val);
            return $bytes >= 50 * 1024 * 1024;
        }
    ],
    'upload_max_filesize' => [
        'value' => ini_get('upload_max_filesize'),
        'required' => '50M',
        'check' => function($val) {
            $bytes = ini_parse_quantity($val);
            return $bytes >= 50 * 1024 * 1024;
        }
    ]
];

foreach ($configs as $key => $config) {
    $ok = $config['check']($config['value']);
    $requirements[] = showResult(
        "$key (actual: {$config['value']})",
        $ok ? 'ok' : 'warning',
        false,
        $ok ? 'Adecuado' : "Recomendado: {$config['required']}"
    );
}

// Función helper para convertir ini values a bytes (para PHP < 8.2)
if (!function_exists('ini_parse_quantity')) {
    function ini_parse_quantity($val) {
        $val = trim($val);
        $last = strtolower($val[strlen($val)-1]);
        $val = (int)$val;
        switch($last) {
            case 'g':
                $val *= 1024;
            case 'm':
                $val *= 1024;
            case 'k':
                $val *= 1024;
        }
        return $val;
    }
}

// Verificar permisos de escritura
$writableDirs = [
    'config' => __DIR__ . '/config',
    'logs' => __DIR__ . '/logs'
];

foreach ($writableDirs as $name => $dir) {
    if (!file_exists($dir)) {
        @mkdir($dir, 0777, true);
    }
    $writable = is_writable($dir);
    $requirements[] = showResult(
        "Directorio $name escribible",
        $writable ? 'ok' : 'error',
        true,
        $writable ? 'Sí' : "No - Ejecute: chmod 777 $dir"
    );
}

// Verificar servidor web
$webServer = '';
if (isset($_SERVER['SERVER_SOFTWARE'])) {
    $webServer = $_SERVER['SERVER_SOFTWARE'];
    $isApache = stripos($webServer, 'apache') !== false;
    $isNginx = stripos($webServer, 'nginx') !== false;
    
    if ($isApache || $isNginx) {
        $requirements[] = showResult(
            "Servidor Web ($webServer)",
            'ok',
            true,
            'Compatible'
        );
    } else {
        $requirements[] = showResult(
            "Servidor Web ($webServer)",
            'warning',
            true,
            'No probado - Se recomienda Apache o Nginx'
        );
    }
}

// Verificar mod_rewrite para Apache
if (PHP_SAPI !== 'cli' && function_exists('apache_get_modules')) {
    $modules = apache_get_modules();
    $hasModRewrite = in_array('mod_rewrite', $modules);
    $requirements[] = showResult(
        "Apache mod_rewrite",
        $hasModRewrite ? 'ok' : 'error',
        true,
        $hasModRewrite ? 'Habilitado' : 'No habilitado - Requerido para URLs limpias'
    );
}

// Si se ejecuta desde CLI
if (PHP_SAPI === 'cli') {
    echo "\n" . str_repeat('=', 60) . "\n";
    echo "VERIFICACIÓN DE REQUISITOS DEL SISTEMA TR-069 SERVER\n";
    echo str_repeat('=', 60) . "\n\n";
    
    echo "PHP y Extensiones:\n";
    echo str_repeat('-', 60) . "\n";
    
    // Los resultados ya se mostraron arriba
    
    echo "\n" . str_repeat('=', 60) . "\n";
    echo "RESUMEN:\n";
    echo str_repeat('-', 60) . "\n";
    
    if ($errors > 0) {
        echo "❌ Se encontraron $errors errores críticos\n";
        echo "   El sistema no puede instalarse hasta resolver estos problemas.\n";
    } else {
        echo "✅ Todos los requisitos críticos están cumplidos\n";
    }
    
    if ($warnings > 0) {
        echo "⚠️  Se encontraron $warnings advertencias\n";
        echo "   El sistema funcionará pero con limitaciones.\n";
    }
    
    echo "\n";
    exit($errors > 0 ? 1 : 0);
}

// Si se ejecuta desde el navegador
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación de Requisitos - TR-069 Server</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 40px;
        }
        .requirement {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 10px;
            transition: all 0.3s;
        }
        .requirement:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .requirement.error {
            background: #fee;
            border-left: 4px solid #dc3545;
        }
        .requirement.warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        .requirement.ok {
            background: #d4edda;
            border-left: 4px solid #28a745;
        }
        .icon {
            font-size: 24px;
            margin-right: 10px;
        }
        .name {
            flex: 1;
            font-weight: 500;
        }
        .status {
            color: #666;
            font-size: 14px;
        }
        .summary {
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            margin: 10px;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .btn.disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin: 30px 0 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .info-box h3 {
            margin: 0 0 10px;
            color: #1976d2;
        }
        .info-box p {
            margin: 5px 0;
            color: #555;
        }
        .info-box code {
            background: #fff;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Verificación de Requisitos del Sistema</h1>
        
        <div class="section-title">Versión de PHP y Extensiones Requeridas</div>
        <?php 
        $criticalReqs = array_filter($requirements, function($r) {
            return $r !== null && isset($r['required']) && $r['required'];
        });
        
        foreach ($criticalReqs as $req): 
            if ($req === null) continue;
        ?>
            <div class="requirement <?= $req['status'] ?>">
                <div>
                    <span class="icon"><?= $req['icon'] ?></span>
                    <span class="name"><?= htmlspecialchars($req['name']) ?></span>
                </div>
                <div class="status"><?= htmlspecialchars($req['message']) ?></div>
            </div>
        <?php endforeach; ?>
        
        <div class="section-title">Extensiones Opcionales y Configuración</div>
        <?php 
        $optionalReqs = array_filter($requirements, function($r) {
            return $r !== null && isset($r['required']) && !$r['required'];
        });
        
        foreach ($optionalReqs as $req): 
            if ($req === null) continue;
        ?>
            <div class="requirement <?= $req['status'] ?>">
                <div>
                    <span class="icon"><?= $req['icon'] ?></span>
                    <span class="name"><?= htmlspecialchars($req['name']) ?></span>
                </div>
                <div class="status"><?= htmlspecialchars($req['message']) ?></div>
            </div>
        <?php endforeach; ?>
        
        <div class="summary">
            <?php if ($errors > 0): ?>
                <h2 style="color: #dc3545;">❌ Se encontraron <?= $errors ?> errores críticos</h2>
                <p>El sistema no puede instalarse hasta resolver estos problemas.</p>
                
                <div class="info-box" style="margin-top: 20px; text-align: left;">
                    <h3>Cómo resolver los errores:</h3>
                    <p><strong>Para extensiones faltantes en Ubuntu/Debian:</strong></p>
                    <p><code>sudo apt-get install php7.4-pdo php7.4-mysql php7.4-soap php7.4-xml php7.4-mbstring</code></p>
                    
                    <p><strong>Para extensiones faltantes en CentOS/RHEL:</strong></p>
                    <p><code>sudo yum install php-pdo php-mysql php-soap php-xml php-mbstring</code></p>
                    
                    <p><strong>Para permisos de directorios:</strong></p>
                    <p><code>chmod -R 777 config/ logs/</code></p>
                </div>
                
                <a href="#" class="btn disabled" onclick="alert('Resuelva los errores antes de continuar'); return false;">No se puede instalar</a>
            <?php else: ?>
                <h2 style="color: #28a745;">✅ Todos los requisitos críticos están cumplidos</h2>
                <?php if ($warnings > 0): ?>
                    <p style="color: #ffc107;">⚠️ Hay <?= $warnings ?> advertencias que podrían limitar algunas funciones.</p>
                <?php else: ?>
                    <p>El sistema está listo para ser instalado.</p>
                <?php endif; ?>
                <a href="install.php" class="btn">Continuar con la Instalación →</a>
            <?php endif; ?>
            
            <a href="check_requirements.php" class="btn" style="background: #6c757d;">🔄 Verificar Nuevamente</a>
        </div>
    </div>
</body>
</html>