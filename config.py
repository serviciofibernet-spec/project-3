"""
Configuration Management for TR-069 Server
Handles loading and validation of server configuration
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Server configuration structure"""
    host: str = "0.0.0.0"
    port: int = 7547
    ssl_enabled: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    debug: bool = False

@dataclass
class DatabaseConfig:
    """Database configuration structure"""
    devices_db: str = "data/tr069_devices.db"
    auth_db: str = "data/tr069_auth.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24

@dataclass
class LoggingConfig:
    """Logging configuration structure"""
    level: str = "INFO"
    file: str = "logs/tr069_server.log"
    max_size: str = "10MB"
    backup_count: int = 5
    console_output: bool = True

@dataclass
class SecurityConfig:
    """Security configuration structure"""
    max_failed_attempts: int = 5
    block_duration_minutes: int = 15
    session_timeout_hours: int = 24
    csrf_protection: bool = True
    rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 15

@dataclass
class TR069Config:
    """Main TR-069 server configuration"""
    server: ServerConfig
    database: DatabaseConfig
    logging: LoggingConfig
    security: SecurityConfig
    
    def __post_init__(self):
        # Ensure data and logs directories exist
        Path(os.path.dirname(self.database.devices_db)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(self.database.auth_db)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(self.logging.file)).mkdir(parents=True, exist_ok=True)

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_file: str = "config/server_config.json"):
        self.config_file = config_file
        self.config: Optional[TR069Config] = None
    
    def load_config(self) -> TR069Config:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                logger.info(f"Loading configuration from {self.config_file}")
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Parse configuration sections
                server_config = ServerConfig(**config_data.get('server', {}))
                database_config = DatabaseConfig(**config_data.get('database', {}))
                logging_config = LoggingConfig(**config_data.get('logging', {}))
                security_config = SecurityConfig(**config_data.get('security', {}))
                
                self.config = TR069Config(
                    server=server_config,
                    database=database_config,
                    logging=logging_config,
                    security=security_config
                )
                
                logger.info("Configuration loaded successfully")
            else:
                logger.warning(f"Configuration file not found: {self.config_file}")
                logger.info("Creating default configuration")
                self.config = self.create_default_config()
                self.save_config()
            
            # Validate configuration
            self.validate_config()
            
            return self.config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            self.config = self.create_default_config()
            return self.config
    
    def create_default_config(self) -> TR069Config:
        """Create default configuration"""
        return TR069Config(
            server=ServerConfig(),
            database=DatabaseConfig(),
            logging=LoggingConfig(),
            security=SecurityConfig()
        )
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            if not self.config:
                logger.error("No configuration to save")
                return
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_dict = {
                'server': asdict(self.config.server),
                'database': asdict(self.config.database),
                'logging': asdict(self.config.logging),
                'security': asdict(self.config.security)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def validate_config(self):
        """Validate configuration values"""
        if not self.config:
            raise ValueError("No configuration loaded")
        
        # Validate server configuration
        if not (1 <= self.config.server.port <= 65535):
            raise ValueError(f"Invalid port number: {self.config.server.port}")
        
        if self.config.server.ssl_enabled:
            if not self.config.server.ssl_cert_path or not os.path.exists(self.config.server.ssl_cert_path):
                raise ValueError("SSL certificate file not found")
            if not self.config.server.ssl_key_path or not os.path.exists(self.config.server.ssl_key_path):
                raise ValueError("SSL key file not found")
        
        # Validate logging configuration
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.config.logging.level}")
        
        # Validate security configuration
        if self.config.security.max_failed_attempts < 1:
            raise ValueError("max_failed_attempts must be at least 1")
        
        if self.config.security.block_duration_minutes < 1:
            raise ValueError("block_duration_minutes must be at least 1")
        
        if self.config.security.session_timeout_hours < 1:
            raise ValueError("session_timeout_hours must be at least 1")
        
        logger.info("Configuration validation passed")
    
    def get_config(self) -> Optional[TR069Config]:
        """Get current configuration"""
        return self.config
    
    def update_config(self, section: str, updates: Dict[str, Any]) -> bool:
        """Update configuration section"""
        try:
            if not self.config:
                logger.error("No configuration loaded")
                return False
            
            if section == 'server':
                for key, value in updates.items():
                    if hasattr(self.config.server, key):
                        setattr(self.config.server, key, value)
            elif section == 'database':
                for key, value in updates.items():
                    if hasattr(self.config.database, key):
                        setattr(self.config.database, key, value)
            elif section == 'logging':
                for key, value in updates.items():
                    if hasattr(self.config.logging, key):
                        setattr(self.config.logging, key, value)
            elif section == 'security':
                for key, value in updates.items():
                    if hasattr(self.config.security, key):
                        setattr(self.config.security, key, value)
            else:
                logger.error(f"Unknown configuration section: {section}")
                return False
            
            # Validate updated configuration
            self.validate_config()
            
            # Save updated configuration
            self.save_config()
            
            logger.info(f"Configuration section '{section}' updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

def setup_logging(logging_config: LoggingConfig):
    """Setup logging based on configuration"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(logging_config.file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Set up file handler with rotation
        from logging.handlers import RotatingFileHandler
        
        # Parse max_size (e.g., "10MB" -> 10*1024*1024)
        max_size = logging_config.max_size.upper()
        if max_size.endswith('MB'):
            max_bytes = int(max_size[:-2]) * 1024 * 1024
        elif max_size.endswith('KB'):
            max_bytes = int(max_size[:-2]) * 1024
        else:
            max_bytes = int(max_size)
        
        file_handler = RotatingFileHandler(
            logging_config.file,
            maxBytes=max_bytes,
            backupCount=logging_config.backup_count
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, logging_config.level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        if logging_config.console_output:
            root_logger.addHandler(console_handler)
        
        logger.info("Logging configured successfully")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=getattr(logging, logging_config.level, logging.INFO),
            format=log_format
        )