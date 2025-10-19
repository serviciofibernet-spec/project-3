<?php
/**
 * Clase para manejo de base de datos SQLite
 */

class Database {
    private $pdo;
    
    public function __construct() {
        $this->connect();
    }
    
    private function connect() {
        try {
            $this->pdo = new PDO('sqlite:' . DB_PATH);
            $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            logMessage('ERROR', 'Error de conexión a la base de datos: ' . $e->getMessage());
            throw new Exception('Error de conexión a la base de datos');
        }
    }
    
    public function initialize() {
        try {
            // Crear tabla de dispositivos
            $this->pdo->exec("
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    manufacturer TEXT,
                    model TEXT,
                    serial_number TEXT,
                    hardware_version TEXT,
                    software_version TEXT,
                    connection_request_url TEXT,
                    last_inform_time DATETIME,
                    last_inform_data TEXT,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
            
            // Crear tabla de sesiones
            $this->pdo->exec("
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            ");
            
            // Crear tabla de parámetros
            $this->pdo->exec("
                CREATE TABLE IF NOT EXISTS parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    parameter_value TEXT,
                    parameter_type TEXT DEFAULT 'string',
                    writable BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id),
                    UNIQUE(device_id, parameter_name)
                )
            ");
            
            // Crear tabla de logs
            $this->pdo->exec("
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            ");
            
            // Marcar como inicializada
            file_put_contents(DB_INITIALIZED, date('Y-m-d H:i:s'));
            
            logMessage('INFO', 'Base de datos inicializada correctamente');
            
        } catch (PDOException $e) {
            logMessage('ERROR', 'Error al inicializar la base de datos: ' . $e->getMessage());
            throw new Exception('Error al inicializar la base de datos');
        }
    }
    
    public function getDevice($deviceId) {
        $stmt = $this->pdo->prepare("SELECT * FROM devices WHERE device_id = ?");
        $stmt->execute([$deviceId]);
        return $stmt->fetch();
    }
    
    public function createDevice($deviceData) {
        $stmt = $this->pdo->prepare("
            INSERT INTO devices (device_id, manufacturer, model, serial_number, hardware_version, software_version, connection_request_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ");
        
        return $stmt->execute([
            $deviceData['device_id'],
            $deviceData['manufacturer'] ?? '',
            $deviceData['model'] ?? '',
            $deviceData['serial_number'] ?? '',
            $deviceData['hardware_version'] ?? '',
            $deviceData['software_version'] ?? '',
            $deviceData['connection_request_url'] ?? ''
        ]);
    }
    
    public function updateDevice($deviceId, $deviceData) {
        $fields = [];
        $values = [];
        
        foreach ($deviceData as $key => $value) {
            if ($key !== 'device_id') {
                $fields[] = "$key = ?";
                $values[] = $value;
            }
        }
        
        $values[] = $deviceId;
        
        $stmt = $this->pdo->prepare("
            UPDATE devices SET " . implode(', ', $fields) . ", updated_at = CURRENT_TIMESTAMP 
            WHERE device_id = ?
        ");
        
        return $stmt->execute($values);
    }
    
    public function getAllDevices() {
        $stmt = $this->pdo->prepare("SELECT * FROM devices ORDER BY created_at DESC");
        $stmt->execute();
        return $stmt->fetchAll();
    }
    
    public function createSession($deviceId, $sessionId, $expiresAt) {
        $stmt = $this->pdo->prepare("
            INSERT INTO sessions (device_id, session_id, expires_at)
            VALUES (?, ?, ?)
        ");
        
        return $stmt->execute([$deviceId, $sessionId, $expiresAt]);
    }
    
    public function getSession($sessionId) {
        $stmt = $this->pdo->prepare("
            SELECT s.*, d.* FROM sessions s 
            JOIN devices d ON s.device_id = d.device_id 
            WHERE s.session_id = ? AND s.expires_at > datetime('now')
        ");
        $stmt->execute([$sessionId]);
        return $stmt->fetch();
    }
    
    public function deleteSession($sessionId) {
        $stmt = $this->pdo->prepare("DELETE FROM sessions WHERE session_id = ?");
        return $stmt->execute([$sessionId]);
    }
    
    public function setParameter($deviceId, $parameterName, $parameterValue, $parameterType = 'string', $writable = false) {
        $stmt = $this->pdo->prepare("
            INSERT OR REPLACE INTO parameters (device_id, parameter_name, parameter_value, parameter_type, writable, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ");
        
        return $stmt->execute([$deviceId, $parameterName, $parameterValue, $parameterType, $writable ? 1 : 0]);
    }
    
    public function getParameter($deviceId, $parameterName) {
        $stmt = $this->pdo->prepare("
            SELECT * FROM parameters 
            WHERE device_id = ? AND parameter_name = ?
        ");
        $stmt->execute([$deviceId, $parameterName]);
        return $stmt->fetch();
    }
    
    public function getParameters($deviceId) {
        $stmt = $this->pdo->prepare("
            SELECT * FROM parameters 
            WHERE device_id = ? 
            ORDER BY parameter_name
        ");
        $stmt->execute([$deviceId]);
        return $stmt->fetchAll();
    }
    
    public function logAction($deviceId, $action, $details = '') {
        $stmt = $this->pdo->prepare("
            INSERT INTO logs (device_id, action, details)
            VALUES (?, ?, ?)
        ");
        
        return $stmt->execute([$deviceId, $action, $details]);
    }
    
    public function getLogs($deviceId = null, $limit = 100) {
        if ($deviceId) {
            $stmt = $this->pdo->prepare("
                SELECT * FROM logs 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ");
            $stmt->execute([$deviceId, $limit]);
        } else {
            $stmt = $this->pdo->prepare("
                SELECT * FROM logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ");
            $stmt->execute([$limit]);
        }
        
        return $stmt->fetchAll();
    }
    
    public function isInitialized() {
        return file_exists(DB_INITIALIZED);
    }
}
?>