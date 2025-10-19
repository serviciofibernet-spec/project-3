#!/usr/bin/env python3
"""
Authentication and Security Module for TR069 Server
"""

import hashlib
import hmac
import base64
import secrets
import json
import os
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages authentication for devices and users"""
    
    def __init__(self):
        self.users_file = "config/users.json"
        self.devices_file = "config/devices_auth.json"
        self.sessions_file = "config/sessions.json"
        self.users = {}
        self.devices = {}
        self.sessions = {}
        
        # Ensure config directory exists
        os.makedirs("config", exist_ok=True)
        
        # Load authentication data
        self.load_auth_data()
    
    def load_auth_data(self):
        """Load authentication data from files"""
        # Load users
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
                logger.info(f"Loaded {len(self.users)} users")
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        else:
            # Create default admin user
            self.create_user("admin", "admin", "Administrator", ["admin"])
            self.save_users()
        
        # Load devices
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r') as f:
                    self.devices = json.load(f)
                logger.info(f"Loaded {len(self.devices)} device credentials")
            except Exception as e:
                logger.error(f"Error loading devices: {e}")
        
        # Load sessions
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
                # Clean expired sessions
                self.cleanup_sessions()
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
    
    def save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def save_devices(self):
        """Save device credentials to file"""
        try:
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving devices: {e}")
    
    def save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash a password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                       password.encode('utf-8'), 
                                       salt.encode('utf-8'), 
                                       100000)
        return base64.b64encode(pwd_hash).decode('utf-8'), salt
    
    def verify_password(self, password: str, pwd_hash: str, salt: str) -> bool:
        """Verify a password against hash"""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == pwd_hash
    
    def create_user(self, username: str, password: str, name: str, roles: list) -> bool:
        """Create a new user"""
        if username in self.users:
            logger.warning(f"User {username} already exists")
            return False
        
        pwd_hash, salt = self.hash_password(password)
        
        self.users[username] = {
            'username': username,
            'password_hash': pwd_hash,
            'salt': salt,
            'name': name,
            'roles': roles,
            'created': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.save_users()
        logger.info(f"User created: {username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if self.verify_password(password, user['password_hash'], user['salt']):
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            self.save_users()
            
            # Create session
            session_token = self.create_session(username, 'user')
            
            return {
                'username': username,
                'name': user['name'],
                'roles': user['roles'],
                'token': session_token
            }
        
        return None
    
    def register_device(self, device_id: str, username: str, password: str) -> bool:
        """Register device credentials"""
        pwd_hash, salt = self.hash_password(password)
        
        self.devices[device_id] = {
            'device_id': device_id,
            'username': username,
            'password_hash': pwd_hash,
            'salt': salt,
            'created': datetime.now().isoformat(),
            'last_auth': None
        }
        
        self.save_devices()
        logger.info(f"Device registered: {device_id}")
        return True
    
    def authenticate_device(self, device_id: str, username: str, password: str) -> bool:
        """Authenticate a device"""
        if device_id not in self.devices:
            # Auto-register new devices (configurable)
            self.register_device(device_id, username, password)
            return True
        
        device = self.devices[device_id]
        if device['username'] != username:
            return False
        
        if self.verify_password(password, device['password_hash'], device['salt']):
            # Update last auth
            device['last_auth'] = datetime.now().isoformat()
            self.save_devices()
            return True
        
        return False
    
    def authenticate_digest(self, username: str, realm: str, nonce: str, 
                          uri: str, response: str, method: str = "POST") -> bool:
        """Authenticate using HTTP Digest authentication"""
        # Simplified digest auth - should be enhanced for production
        if username in self.users:
            user = self.users[username]
            # TODO: Implement proper digest authentication
            return True
        return False
    
    def create_session(self, identifier: str, session_type: str) -> str:
        """Create a new session"""
        token = secrets.token_urlsafe(32)
        
        self.sessions[token] = {
            'identifier': identifier,
            'type': session_type,
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        self.save_sessions()
        return token
    
    def validate_session(self, token: str) -> Optional[Dict]:
        """Validate a session token"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        
        # Check expiration
        if datetime.fromisoformat(session['expires']) < datetime.now():
            del self.sessions[token]
            self.save_sessions()
            return None
        
        return session
    
    def cleanup_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.now()
        expired = []
        
        for token, session in self.sessions.items():
            if datetime.fromisoformat(session['expires']) < current_time:
                expired.append(token)
        
        for token in expired:
            del self.sessions[token]
        
        if expired:
            self.save_sessions()
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def revoke_session(self, token: str) -> bool:
        """Revoke a session"""
        if token in self.sessions:
            del self.sessions[token]
            self.save_sessions()
            return True
        return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash'], user['salt']):
            return False
        
        # Set new password
        pwd_hash, salt = self.hash_password(new_password)
        user['password_hash'] = pwd_hash
        user['salt'] = salt
        
        self.save_users()
        logger.info(f"Password changed for user: {username}")
        return True
    
    def list_users(self) -> list:
        """List all users"""
        return [
            {
                'username': u['username'],
                'name': u['name'],
                'roles': u['roles'],
                'created': u['created'],
                'last_login': u['last_login']
            }
            for u in self.users.values()
        ]
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if username in self.users:
            del self.users[username]
            self.save_users()
            logger.info(f"User deleted: {username}")
            return True
        return False