"""
Base authentication provider interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User data model"""
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


@dataclass
class AuthToken:
    """Authentication token data"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class AuthProvider(ABC):
    """Abstract base class for authentication providers"""

    @abstractmethod
    def register(self, email: str, password: str, full_name: Optional[str] = None) -> User:
        """
        Register a new user

        Args:
            email: User email
            password: User password
            full_name: User's full name (optional)

        Returns:
            User object

        Raises:
            ValueError: If registration fails
        """
        pass

    @abstractmethod
    def login(self, email: str, password: str) -> AuthToken:
        """
        Authenticate user and return token

        Args:
            email: User email
            password: User password

        Returns:
            AuthToken with access token

        Raises:
            ValueError: If authentication fails
        """
        pass

    @abstractmethod
    def verify_token(self, token: str) -> User:
        """
        Verify authentication token and return user

        Args:
            token: JWT or access token

        Returns:
            User object

        Raises:
            ValueError: If token is invalid
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> AuthToken:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            New AuthToken

        Raises:
            ValueError: If refresh fails
        """
        pass

    @abstractmethod
    def logout(self, token: str) -> bool:
        """
        Logout user (invalidate token)

        Args:
            token: Access token to invalidate

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> User:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        pass

    @abstractmethod
    def update_user(self, user_id: str, **kwargs) -> User:
        """
        Update user information

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated User object
        """
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user account

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def reset_password_request(self, email: str) -> bool:
        """
        Request password reset

        Args:
            email: User email

        Returns:
            True if email sent
        """
        pass

    @abstractmethod
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            True if successful
        """
        pass
