-- TR-069 ACS Database Schema
-- Created for TR-069 Auto Configuration Server

-- Devices table - stores information about CPE devices
CREATE TABLE IF NOT EXISTS `devices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `serial_number` varchar(64) NOT NULL,
  `oui` varchar(6) NOT NULL,
  `product_class` varchar(64) DEFAULT NULL,
  `manufacturer` varchar(64) DEFAULT NULL,
  `model_name` varchar(64) DEFAULT NULL,
  `software_version` varchar(64) DEFAULT NULL,
  `hardware_version` varchar(64) DEFAULT NULL,
  `connection_request_url` varchar(255) DEFAULT NULL,
  `connection_request_username` varchar(64) DEFAULT NULL,
  `connection_request_password` varchar(64) DEFAULT NULL,
  `last_inform` timestamp NULL DEFAULT NULL,
  `last_boot` timestamp NULL DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `mac_address` varchar(17) DEFAULT NULL,
  `status` enum('online','offline','error') DEFAULT 'offline',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_device` (`serial_number`, `oui`),
  KEY `idx_last_inform` (`last_inform`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sessions table - stores TR-069 session information
CREATE TABLE IF NOT EXISTS `sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `session_id` varchar(128) NOT NULL,
  `state` enum('active','completed','error','timeout') DEFAULT 'active',
  `started_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `completed_at` timestamp NULL DEFAULT NULL,
  `last_activity` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `inform_data` text,
  `error_message` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_id` (`session_id`),
  KEY `device_id` (`device_id`),
  KEY `idx_state` (`state`),
  KEY `idx_started_at` (`started_at`),
  CONSTRAINT `fk_sessions_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Parameters table - stores device parameters
CREATE TABLE IF NOT EXISTS `parameters` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` text,
  `type` varchar(32) DEFAULT 'string',
  `writable` tinyint(1) DEFAULT 1,
  `last_updated` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_param` (`device_id`, `name`),
  KEY `device_id` (`device_id`),
  KEY `idx_name` (`name`),
  CONSTRAINT `fk_parameters_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tasks table - stores pending tasks for devices
CREATE TABLE IF NOT EXISTS `tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `type` enum('GetParameterValues','SetParameterValues','AddObject','DeleteObject','Download','Upload','Reboot','FactoryReset') NOT NULL,
  `parameters` text,
  `status` enum('pending','in_progress','completed','failed') DEFAULT 'pending',
  `priority` int(11) DEFAULT 5,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `started_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `result` text,
  `error_message` text,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `idx_status` (`status`),
  KEY `idx_priority` (`priority`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_tasks_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Events table - stores device events and logs
CREATE TABLE IF NOT EXISTS `events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) DEFAULT NULL,
  `session_id` int(11) DEFAULT NULL,
  `event_type` varchar(64) NOT NULL,
  `event_code` varchar(64) DEFAULT NULL,
  `command_key` varchar(32) DEFAULT NULL,
  `message` text,
  `severity` enum('info','warning','error','critical') DEFAULT 'info',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `session_id` (`session_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_severity` (`severity`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_events_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_events_session` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Presets table - stores parameter presets for device configuration
CREATE TABLE IF NOT EXISTS `presets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `description` text,
  `parameters` text NOT NULL,
  `device_filter` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Firmware table - stores firmware information for downloads
CREATE TABLE IF NOT EXISTS `firmware` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `version` varchar(64) NOT NULL,
  `manufacturer` varchar(64) DEFAULT NULL,
  `model` varchar(64) DEFAULT NULL,
  `file_path` varchar(255) NOT NULL,
  `file_size` bigint(20) DEFAULT NULL,
  `checksum` varchar(64) DEFAULT NULL,
  `description` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_firmware` (`name`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default preset for basic configuration
INSERT INTO `presets` (`name`, `description`, `parameters`) VALUES 
('Basic WiFi Setup', 'Configuración básica de WiFi', 
 '{"Device.WiFi.Radio.1.Enable":"true","Device.WiFi.SSID.1.Enable":"true","Device.WiFi.SSID.1.SSID":"MyNetwork","Device.WiFi.AccessPoint.1.Security.ModeEnabled":"WPA2-PSK"}');

-- Create indexes for better performance
CREATE INDEX idx_devices_last_inform ON devices(last_inform DESC);
CREATE INDEX idx_sessions_device_state ON sessions(device_id, state);
CREATE INDEX idx_parameters_device_name ON parameters(device_id, name);
CREATE INDEX idx_tasks_device_status ON tasks(device_id, status, priority);
CREATE INDEX idx_events_device_created ON events(device_id, created_at DESC);