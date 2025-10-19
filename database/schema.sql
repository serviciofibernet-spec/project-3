-- TR-069 ACS Database Schema

CREATE DATABASE IF NOT EXISTS tr069_acs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tr069_acs;

-- Tabla de usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role ENUM('admin', 'technician', 'client') DEFAULT 'client',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB;

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(255) NOT NULL,
    document VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

-- Tabla de dispositivos ONT
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    oui VARCHAR(10),
    product_class VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    hardware_version VARCHAR(50),
    software_version VARCHAR(50),
    client_id INT,
    connection_request_url VARCHAR(500),
    connection_request_username VARCHAR(100),
    connection_request_password VARCHAR(100),
    last_inform TIMESTAMP NULL,
    ip_address VARCHAR(50),
    mac_address VARCHAR(50),
    status ENUM('online', 'offline', 'pending', 'error') DEFAULT 'pending',
    provisioning_status ENUM('not_provisioned', 'provisioning', 'provisioned', 'failed') DEFAULT 'not_provisioned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    INDEX idx_serial_number (serial_number),
    INDEX idx_client_id (client_id),
    INDEX idx_status (status),
    INDEX idx_last_inform (last_inform)
) ENGINE=InnoDB;

-- Tabla de parámetros de dispositivos
CREATE TABLE IF NOT EXISTS device_parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    parameter_name VARCHAR(500) NOT NULL,
    parameter_value TEXT,
    parameter_type VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE KEY unique_device_param (device_id, parameter_name),
    INDEX idx_device_id (device_id),
    INDEX idx_parameter_name (parameter_name)
) ENGINE=InnoDB;

-- Tabla de perfiles de configuración
CREATE TABLE IF NOT EXISTS configuration_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_filter VARCHAR(255),
    configuration JSON NOT NULL,
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_model_filter (model_filter),
    INDEX idx_priority (priority)
) ENGINE=InnoDB;

-- Tabla de tareas de configuración
CREATE TABLE IF NOT EXISTS configuration_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    task_type ENUM('set_parameters', 'get_parameters', 'reboot', 'firmware_upgrade', 'factory_reset', 'add_object', 'delete_object') NOT NULL,
    parameters JSON,
    status ENUM('pending', 'in_progress', 'completed', 'failed', 'timeout') DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Tabla de historial de eventos
CREATE TABLE IF NOT EXISTS event_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    event_code VARCHAR(50),
    event_type VARCHAR(100),
    event_data JSON,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_event_code (event_code),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Tabla de diagnósticos
CREATE TABLE IF NOT EXISTS device_diagnostics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    optical_power_rx DECIMAL(10, 2),
    optical_power_tx DECIMAL(10, 2),
    temperature DECIMAL(10, 2),
    cpu_usage DECIMAL(5, 2),
    memory_usage DECIMAL(5, 2),
    uptime INT,
    wan_status VARCHAR(50),
    connected_devices_count INT DEFAULT 0,
    wifi_24ghz_status VARCHAR(50),
    wifi_5ghz_status VARCHAR(50),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB;

-- Tabla de dispositivos conectados al WiFi
CREATE TABLE IF NOT EXISTS connected_devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    mac_address VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    hostname VARCHAR(255),
    interface_type VARCHAR(50),
    connection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_mac_address (mac_address)
) ENGINE=InnoDB;

-- Tabla de sesiones CWMP
CREATE TABLE IF NOT EXISTS cwmp_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    status ENUM('active', 'completed', 'failed') DEFAULT 'active',
    inform_data JSON,
    INDEX idx_device_id (device_id),
    INDEX idx_session_id (session_id),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Tabla de firmware
CREATE TABLE IF NOT EXISTS firmware_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    version VARCHAR(50),
    file_url VARCHAR(500),
    file_size BIGINT,
    checksum VARCHAR(100),
    release_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model),
    INDEX idx_version (version)
) ENGINE=InnoDB;

-- Insertar usuario admin por defecto
INSERT INTO users (username, password_hash, email, role) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5W6S8F/qOpqKW', 'admin@tr069.local', 'admin')
ON DUPLICATE KEY UPDATE username=username;
