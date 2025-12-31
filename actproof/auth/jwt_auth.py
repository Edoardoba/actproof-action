"""
JWT-based authentication provider
Simple implementation using SQLite for development
"""

import jwt
import bcrypt
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
from .base import AuthProvider, User, AuthToken


class JWTAuth(AuthProvider):
    """JWT authentication implementation with SQLite backend"""

    def __init__(
        self,
        secret_key: str,
        database_path: str = "./actproof_users.db",
        algorithm: str = "HS256",
        token_expiration_minutes: int = 1440,  # 24 hours
    ):
        """
        Initialize JWT authentication

        Args:
            secret_key: Secret key for JWT signing
            database_path: Path to SQLite database
            algorithm: JWT algorithm
            token_expiration_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiration = token_expiration_minutes
        self.db_path = database_path

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def _create_token(self, user_id: str, email: str) -> AuthToken:
        """Create JWT token for user"""
        expiration = datetime.utcnow() + timedelta(minutes=self.token_expiration)

        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expiration,
            "iat": datetime.utcnow()
        }

        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return AuthToken(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.token_expiration * 60
        )

    def register(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        """Register new user"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        password_hash = self._hash_password(password)

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                (email, password_hash, full_name)
            )
            conn.commit()
            user_id = cursor.lastrowid

            return User(
                id=str(user_id),
                email=email,
                full_name=full_name,
                created_at=datetime.utcnow()
            )
        except sqlite3.IntegrityError:
            raise ValueError("Email already registered")
        finally:
            conn.close()

    def login(self, email: str, password: str) -> AuthToken:
        """Authenticate user and return token"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise ValueError("Invalid email or password")

        if not self._verify_password(password, user['password_hash']):
            raise ValueError("Invalid email or password")

        return self._create_token(str(user['id']), user['email'])

    def verify_token(self, token: str) -> User:
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload['user_id']
            return self.get_user(user_id)
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh access token (simplified - reuses verify_token)"""
        user = self.verify_token(refresh_token)
        return self._create_token(user.id, user.email)

    def logout(self, token: str) -> bool:
        """Logout user (with JWT, just client-side deletion)"""
        # In a production system, you'd maintain a blacklist of tokens
        return True

    def get_user(self, user_id: str) -> User:
        """Get user by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise ValueError("User not found")

        return User(
            id=str(user['id']),
            email=user['email'],
            full_name=user['full_name'],
            created_at=datetime.fromisoformat(user['created_at'])
        )

    def update_user(self, user_id: str, **kwargs) -> User:
        """Update user information"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        allowed_fields = ['full_name', 'email']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_user(user_id)

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]

        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()

        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> bool:
        """Delete user account"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def reset_password_request(self, email: str) -> bool:
        """Request password reset (simplified - returns reset token)"""
        # In production, send email with reset link
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return False

        # In production, create and store reset token with expiration
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        # In production, verify reset token first
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # This is simplified - in production, decode token to get user_id
        return True
