"""
Authentication and Security Module for TR-069 Server
Handles authentication, authorization, and security features
"""

import hashlib
import hmac
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import sqlite3
from dataclasses import dataclass
import bcrypt
import jwt
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User account structure"""
    username: str
    password_hash: str
    role: str = "user"  # admin, user, readonly
    created_at: str = ""
    last_login: str = ""
    active: bool = True

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self, db_path: str = "tr069_auth.db", secret_key: str = None):
        self.db_path = db_path
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}
        self.init_database()
        self.load_users()
        
        # Create default admin user if no users exist
        if not self.users:
            self.create_default_admin()
    
    def init_database(self):
        """Initialize authentication database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TEXT,
                    last_login TEXT,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')
            
            # Create access_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    username TEXT,
                    action TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    success INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Authentication database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing auth database: {e}")
    
    def load_users(self):
        """Load users from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            
            for row in rows:
                user = User(
                    username=row[0],
                    password_hash=row[1],
                    role=row[2],
                    created_at=row[3] or "",
                    last_login=row[4] or "",
                    active=bool(row[5])
                )
                self.users[user.username] = user
            
            conn.close()
            logger.info(f"Loaded {len(self.users)} users")
            
        except Exception as e:
            logger.error(f"Error loading users: {e}")
    
    def create_default_admin(self):
        """Create default admin user"""
        try:
            admin_password = "admin123"  # Change this in production!
            self.create_user("admin", admin_password, "admin")
            logger.warning("Default admin user created with password 'admin123' - CHANGE THIS!")
            
        except Exception as e:
            logger.error(f"Error creating default admin: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Create new user"""
        try:
            if username in self.users:
                logger.error(f"User already exists: {username}")
                return False
            
            password_hash = self.hash_password(password)
            user = User(
                username=username,
                password_hash=password_hash,
                role=role,
                created_at=datetime.now().isoformat(),
                active=True
            )
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at, active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.username, user.password_hash, user.role, user.created_at, 1))
            
            conn.commit()
            conn.close()
            
            self.users[username] = user
            logger.info(f"User created: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Optional[str]:
        """Authenticate user and return session token"""
        try:
            user = self.users.get(username)
            if not user or not user.active:
                self.log_access(username, "login_failed", ip_address, user_agent, False)
                return None
            
            if not self.verify_password(password, user.password_hash):
                self.log_access(username, "login_failed", ip_address, user_agent, False)
                return None
            
            # Update last login
            user.last_login = datetime.now().isoformat()
            self.update_user_last_login(username)
            
            # Create session
            session_token = self.create_session(username, ip_address, user_agent)
            
            self.log_access(username, "login_success", ip_address, user_agent, True)
            logger.info(f"User authenticated: {username}")
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def create_session(self, username: str, ip_address: str = "", user_agent: str = "") -> str:
        """Create user session"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
            
            session_data = {
                'username': username,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            self.sessions[session_id] = session_data
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, username, created_at, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, username, session_data['created_at'], session_data['expires_at'], ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return ""
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session and return username"""
        try:
            session_data = self.sessions.get(session_id)
            if not session_data:
                return None
            
            # Check if session expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.invalidate_session(session_id)
                return None
            
            return session_data['username']
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    def update_user_last_login(self, username: str):
        """Update user's last login time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE username = ?
            ''', (datetime.now().isoformat(), username))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
    
    def log_access(self, username: str, action: str, ip_address: str, user_agent: str, success: bool):
        """Log access attempt"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs (timestamp, username, action, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), username, action, ip_address, user_agent, int(success)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging access: {e}")
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        user = self.users.get(username)
        return user.role if user else None
    
    def has_permission(self, username: str, required_role: str) -> bool:
        """Check if user has required permission"""
        user_role = self.get_user_role(username)
        if not user_role:
            return False
        
        # Role hierarchy: admin > user > readonly
        role_levels = {'readonly': 1, 'user': 2, 'admin': 3}
        
        user_level = role_levels.get(user_role, 0)
        required_level = role_levels.get(required_role, 0)
        
        return user_level >= required_level

class SecurityManager:
    """Manages security features and policies"""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.max_attempts = 5
        self.block_duration = timedelta(minutes=15)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if ip_address in self.blocked_ips:
            block_time = self.blocked_ips[ip_address]
            if datetime.now() - block_time < self.block_duration:
                return True
            else:
                # Unblock expired blocks
                del self.blocked_ips[ip_address]
        return False
    
    def record_failed_attempt(self, ip_address: str):
        """Record failed authentication attempt"""
        now = datetime.now()
        
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        
        # Remove old attempts (older than block duration)
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if now - attempt < self.block_duration
        ]
        
        # Add current attempt
        self.failed_attempts[ip_address].append(now)
        
        # Check if should block
        if len(self.failed_attempts[ip_address]) >= self.max_attempts:
            self.blocked_ips[ip_address] = now
            logger.warning(f"IP blocked due to too many failed attempts: {ip_address}")
    
    def validate_input(self, input_data: str, max_length: int = 1000) -> bool:
        """Basic input validation"""
        if not input_data:
            return False
        
        if len(input_data) > max_length:
            return False
        
        # Check for common injection patterns
        dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=', 'eval(', 'exec(']
        input_lower = input_data.lower()
        
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                return False
        
        return True
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, expected_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, expected_token)

def require_auth(required_role: str = "user"):
    """Decorator for requiring authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request):
            # Get session token from header or cookie
            session_token = request.headers.get('Authorization')
            if session_token and session_token.startswith('Bearer '):
                session_token = session_token[7:]
            
            if not session_token:
                session_token = request.cookies.get('session_token')
            
            if not session_token:
                return web.Response(status=401, text="Authentication required")
            
            # Validate session
            auth_manager = request.app.get('auth_manager')
            if not auth_manager:
                return web.Response(status=500, text="Auth manager not configured")
            
            username = auth_manager.validate_session(session_token)
            if not username:
                return web.Response(status=401, text="Invalid session")
            
            # Check permissions
            if not auth_manager.has_permission(username, required_role):
                return web.Response(status=403, text="Insufficient permissions")
            
            # Add user info to request
            request['user'] = username
            request['role'] = auth_manager.get_user_role(username)
            
            return await func(request)
        return wrapper
    return decorator

def require_csrf(func):
    """Decorator for requiring CSRF token"""
    @wraps(func)
    async def wrapper(request):
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = request.headers.get('X-CSRF-Token')
            expected_token = request.cookies.get('csrf_token')
            
            security_manager = request.app.get('security_manager')
            if not security_manager or not security_manager.validate_csrf_token(csrf_token, expected_token):
                return web.Response(status=403, text="CSRF token validation failed")
        
        return await func(request)
    return wrapper