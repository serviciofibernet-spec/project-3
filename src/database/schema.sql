-- TR069 Huawei ONT Management Database Schema

-- Users table for admin and client access
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'client', 'technician') DEFAULT 'client',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Clients table for customer information
CREATE TABLE IF NOT EXISTS clients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    client_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    service_plan VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Configuration profiles for automatic setup
CREATE TABLE IF NOT EXISTS configuration_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    ont_model VARCHAR(50),
    default_config JSON NOT NULL,
    wifi_config JSON,
    network_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ONT devices table
CREATE TABLE IF NOT EXISTS devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    mac_address VARCHAR(17) UNIQUE,
    client_id INT,
    profile_id INT,
    model VARCHAR(50),
    firmware_version VARCHAR(50),
    hardware_version VARCHAR(50),
    connection_request_url VARCHAR(255),
    connection_request_username VARCHAR(50),
    connection_request_password VARCHAR(100),
    last_inform TIMESTAMP,
    ip_address VARCHAR(45),
    status ENUM('online', 'offline', 'error', 'configuring') DEFAULT 'offline',
    optical_power DECIMAL(5,2),
    signal_level DECIMAL(5,2),
    uptime BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (profile_id) REFERENCES configuration_profiles(id) ON DELETE SET NULL
);

-- Device configurations table
CREATE TABLE IF NOT EXISTS device_configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    parameter_name VARCHAR(255) NOT NULL,
    parameter_value TEXT,
    parameter_type ENUM('string', 'int', 'boolean', 'datetime') DEFAULT 'string',
    is_writable BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE KEY unique_device_parameter (device_id, parameter_name)
);

-- WiFi configurations
CREATE TABLE IF NOT EXISTS wifi_configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    ssid_2_4ghz VARCHAR(32),
    password_2_4ghz VARCHAR(64),
    channel_2_4ghz INT DEFAULT 6,
    enabled_2_4ghz BOOLEAN DEFAULT TRUE,
    ssid_5ghz VARCHAR(32),
    password_5ghz VARCHAR(64),
    channel_5ghz INT DEFAULT 36,
    enabled_5ghz BOOLEAN DEFAULT TRUE,
    security_mode ENUM('WPA2-PSK', 'WPA3-PSK', 'WPA2/WPA3-PSK') DEFAULT 'WPA2-PSK',
    max_clients INT DEFAULT 32,
    guest_network_enabled BOOLEAN DEFAULT FALSE,
    guest_ssid VARCHAR(32),
    guest_password VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- Network configurations
CREATE TABLE IF NOT EXISTS network_configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    wan_type ENUM('DHCP', 'PPPoE', 'Static') DEFAULT 'PPPoE',
    pppoe_username VARCHAR(100),
    pppoe_password VARCHAR(100),
    static_ip VARCHAR(45),
    static_netmask VARCHAR(45),
    static_gateway VARCHAR(45),
    primary_dns VARCHAR(45) DEFAULT '8.8.8.8',
    secondary_dns VARCHAR(45) DEFAULT '8.8.4.4',
    vlan_id INT,
    vlan_priority INT DEFAULT 0,
    mtu INT DEFAULT 1500,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- Port configurations
CREATE TABLE IF NOT EXISTS port_configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    port_number INT NOT NULL,
    port_type ENUM('ethernet', 'usb', 'phone') DEFAULT 'ethernet',
    enabled BOOLEAN DEFAULT TRUE,
    speed ENUM('auto', '10', '100', '1000') DEFAULT 'auto',
    duplex ENUM('auto', 'half', 'full') DEFAULT 'auto',
    vlan_id INT,
    description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE KEY unique_device_port (device_id, port_number)
);

-- Monitoring data
CREATE TABLE IF NOT EXISTS monitoring_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    optical_power DECIMAL(5,2),
    optical_rx_power DECIMAL(5,2),
    optical_tx_power DECIMAL(5,2),
    temperature DECIMAL(5,2),
    voltage DECIMAL(5,2),
    current_ma DECIMAL(8,2),
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    uptime BIGINT,
    wifi_clients_2_4ghz INT DEFAULT 0,
    wifi_clients_5ghz INT DEFAULT 0,
    total_wifi_clients INT DEFAULT 0,
    wan_status ENUM('connected', 'disconnected', 'connecting') DEFAULT 'disconnected',
    lan_status ENUM('up', 'down') DEFAULT 'down',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_recorded (device_id, recorded_at)
);

-- Connected devices (WiFi clients)
CREATE TABLE IF NOT EXISTS connected_devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ont_device_id INT NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    ip_address VARCHAR(45),
    hostname VARCHAR(100),
    connection_type ENUM('wifi_2_4ghz', 'wifi_5ghz', 'ethernet') NOT NULL,
    signal_strength INT,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data_usage_mb BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (ont_device_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE KEY unique_ont_mac (ont_device_id, mac_address)
);

-- Task queue for TR069 operations
CREATE TABLE IF NOT EXISTS task_queue (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    task_type ENUM('reboot', 'firmware_upgrade', 'config_change', 'factory_reset', 'get_parameters', 'set_parameters') NOT NULL,
    parameters JSON,
    status ENUM('pending', 'in_progress', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    priority INT DEFAULT 5,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    created_by INT,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_status_priority (status, priority),
    INDEX idx_device_status (device_id, status)
);

-- Firmware versions
CREATE TABLE IF NOT EXISTS firmware_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ont_model VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64),
    release_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_model_version (ont_model, version)
);

-- System logs
CREATE TABLE IF NOT EXISTS system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    level ENUM('error', 'warn', 'info', 'debug') DEFAULT 'info',
    message TEXT NOT NULL,
    device_id INT,
    user_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    additional_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_level_created (level, created_at),
    INDEX idx_device_created (device_id, created_at)
);

-- Configuration change history
CREATE TABLE IF NOT EXISTS configuration_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    parameter_name VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INT,
    change_reason VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_device_changed (device_id, changed_at)
);

-- Insert default admin user
INSERT IGNORE INTO users (username, email, password_hash, role) VALUES 
('admin', 'admin@tr069server.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.QBm', 'admin');

-- Insert default configuration profiles
INSERT IGNORE INTO configuration_profiles (name, description, ont_model, default_config, wifi_config, network_config) VALUES 
('Huawei HG8245H Default', 'Default configuration for Huawei HG8245H', 'HG8245H', 
'{"management": {"web_port": 80, "ssh_enabled": false, "telnet_enabled": false}}',
'{"ssid_2_4ghz": "HUAWEI-{SERIAL_LAST_4}", "password_2_4ghz": "huawei{SERIAL_LAST_6}", "channel_2_4ghz": 6, "ssid_5ghz": "HUAWEI-5G-{SERIAL_LAST_4}", "password_5ghz": "huawei{SERIAL_LAST_6}", "channel_5ghz": 36}',
'{"wan_type": "PPPoE", "primary_dns": "8.8.8.8", "secondary_dns": "8.8.4.4", "mtu": 1500}'),

('Huawei HG8245Q2 Default', 'Default configuration for Huawei HG8245Q2', 'HG8245Q2',
'{"management": {"web_port": 80, "ssh_enabled": false, "telnet_enabled": false}}',
'{"ssid_2_4ghz": "HUAWEI-{SERIAL_LAST_4}", "password_2_4ghz": "huawei{SERIAL_LAST_6}", "channel_2_4ghz": 6, "ssid_5ghz": "HUAWEI-5G-{SERIAL_LAST_4}", "password_5ghz": "huawei{SERIAL_LAST_6}", "channel_5ghz": 36}',
'{"wan_type": "PPPoE", "primary_dns": "8.8.8.8", "secondary_dns": "8.8.4.4", "mtu": 1500}');