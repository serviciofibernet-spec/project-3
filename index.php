<?php
/**
 * Servidor TR-069 en PHP
 * Servidor SOAP para gestión remota de dispositivos CPE
 */

// Configuración de errores
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Incluir configuración
require_once 'config.php';
require_once 'includes/database.php';
require_once 'includes/tr069_server.php';

// Inicializar base de datos
$db = new Database();

// Crear servidor TR-069
$server = new TR069Server($db);

// Manejar solicitudes SOAP
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $server->handleRequest();
} else {
    // Mostrar información del servidor
    header('Content-Type: text/html; charset=utf-8');
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Servidor TR-069</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Servidor TR-069</h1>
            <div class="status">
                <h3>Estado del Servidor</h3>
                <p>✅ Servidor activo y funcionando</p>
                <p>📡 Endpoint SOAP: <?php echo $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']; ?></p>
                <p>🔧 Versión: 1.0.0</p>
            </div>
            <div class="info">
                <h3>Información del Servidor</h3>
                <p>Este servidor implementa el protocolo TR-069 para la gestión remota de dispositivos CPE.</p>
                <p><a href="admin.php">Panel de Administración</a></p>
                <p><a href="install.php">Configuración</a></p>
            </div>
        </div>
    </body>
    </html>
    <?php
}
?>