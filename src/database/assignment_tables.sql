-- Additional tables for auto-assignment functionality

-- Assignment rules table
CREATE TABLE IF NOT EXISTS assignment_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rule_type ENUM('serial_pattern', 'mac_pattern', 'location_based', 'service_area') NOT NULL,
    rule_config JSON NOT NULL,
    priority INT DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Assignment notifications for unassigned devices
CREATE TABLE IF NOT EXISTS assignment_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    serial_number VARCHAR(50) NOT NULL,
    model VARCHAR(50),
    ip_address VARCHAR(45),
    status ENUM('pending', 'resolved', 'ignored') DEFAULT 'pending',
    resolved_by INT,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Pre-registered devices table
CREATE TABLE IF NOT EXISTS pre_registered_devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    client_id INT NOT NULL,
    registered_by INT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (registered_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Client profiles association table
CREATE TABLE IF NOT EXISTS client_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    profile_id INT NOT NULL,
    priority INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES configuration_profiles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_client_profile (client_id, profile_id)
);

-- Insert some example assignment rules
INSERT IGNORE INTO assignment_rules (name, description, rule_type, rule_config, priority) VALUES 
('Huawei HG8245H Serial Pattern', 'Assign devices with specific serial pattern to designated client', 'serial_pattern', 
'{"pattern": "^HG8245H.*", "client_id": 1}', 8),

('MAC Address OUI Pattern', 'Assign devices based on MAC address OUI', 'mac_pattern', 
'{"pattern": "^00:25:9E.*", "client_id": 1}', 7),

('Default Huawei Assignment', 'Default assignment for Huawei devices', 'serial_pattern', 
'{"pattern": "^HG.*", "client_id": null}', 1);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assignment_notifications_status ON assignment_notifications(status);
CREATE INDEX IF NOT EXISTS idx_assignment_notifications_created ON assignment_notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_pre_registered_serial ON pre_registered_devices(serial_number);
CREATE INDEX IF NOT EXISTS idx_client_profiles_client ON client_profiles(client_id);
CREATE INDEX IF NOT EXISTS idx_assignment_rules_priority ON assignment_rules(priority, is_active);