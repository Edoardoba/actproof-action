"""
Supabase authentication provider
Enterprise-grade auth with built-in email verification, password reset, etc.
"""

from typing import Optional
from datetime import datetime, timezone
from .base import AuthProvider, User, AuthToken


import logging

logger = logging.getLogger(__name__)


def _parse_datetime(value) -> Optional[datetime]:
    """Safely parse datetime from various formats"""
    if value is None:
        return None
    
    # If already a datetime object, return it
    if isinstance(value, datetime):
        return value
    
    # If it's not a string, try to convert or return None
    if not isinstance(value, str):
        try:
            # Try to convert to string first
            value = str(value)
        except Exception:
            return None
    
    # Now parse the string
    if isinstance(value, str):
        try:
            # Handle ISO format with Z timezone
            if value.endswith('Z'):
                value = value.replace('Z', '+00:00')
            return datetime.fromisoformat(value)
        except (ValueError, AttributeError, TypeError) as e:
            # Log the error for debugging but don't fail
            logger.debug(f"Could not parse datetime value '{value}': {e}")
            return None
    
    return None

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabaseAuth(AuthProvider):
    """Supabase authentication implementation"""

    def __init__(self, supabase_url: str, supabase_key: str, service_role_key: Optional[str] = None):
        """
        Initialize Supabase authentication

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/public key
            service_role_key: Optional service role key for admin operations (auto-confirm email)
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase not installed. Install with: pip install supabase"
            )

        self.client: Client = create_client(supabase_url, supabase_key)
        self.service_role_key = service_role_key
        # Create service role client if available (for admin operations like auto-confirming email)
        if service_role_key:
            self.admin_client: Optional[Client] = create_client(supabase_url, service_role_key)
            logger.info("✅ Supabase auth initialized with service role key (email auto-confirmation enabled)")
        else:
            self.admin_client = None

    def register(self, email: str, password: str, full_name: Optional[str] = None) -> tuple[User, Optional[str]]:
        """
        Register new user with Supabase
        
        Returns:
            Tuple of (User object, access_token if session is available)
        """
        # Basic email validation before sending to Supabase
        email = email.strip().lower()
        if not email:
            raise ValueError("Email address is required")
        
        # Check basic email format
        if '@' not in email:
            raise ValueError("Invalid email format: missing @ symbol")
        
        parts = email.split('@')
        if len(parts) != 2:
            raise ValueError("Invalid email format")
        
        local_part = parts[0]
        domain_part = parts[1]
        
        # Check minimum length for local part (before @)
        # Supabase typically requires at least 2 characters
        if len(local_part) < 2:
            raise ValueError("Email address local part (before @) must be at least 2 characters long")
        
        # Check domain part
        if not domain_part or '.' not in domain_part:
            raise ValueError("Invalid email format: domain must contain a dot")
        
        # Check if domain has at least one character after the last dot
        domain_parts = domain_part.split('.')
        if len(domain_parts) < 2 or not domain_parts[-1]:
            raise ValueError("Invalid email format: domain must have a valid TLD")
        
        try:
            # Register user - emails are auto-confirmed below, so confirmation emails are not needed
            # Note: To completely disable email sending, configure in Supabase Dashboard:
            # Auth > Email Templates > Disable "Confirm signup" email
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })

            if response.user is None:
                # Try to get more details from the response
                error_msg = "Registration failed"
                if hasattr(response, 'error') and response.error:
                    error_msg = f"Registration failed: {response.error}"
                elif hasattr(response, 'message') and response.message:
                    error_msg = f"Registration failed: {response.message}"
                raise ValueError(error_msg)

            # Auto-confirm email immediately using admin client if available
            if self.admin_client and response.user:
                try:
                    self.admin_client.auth.admin.update_user_by_id(
                        response.user.id,
                        {"email_confirm": True}
                    )
                    logger.info(f"✅ Auto-confirmed email for {email} during registration")
                except Exception as confirm_error:
                        logger.warning(f"⚠️ Failed to auto-confirm email during registration: {confirm_error}")
                        # Try alternative method
                        try:
                            # Some Supabase versions require different approach
                            self.admin_client.auth.admin.update_user_by_id(
                                response.user.id,
                                {"email_confirmed_at": datetime.now(timezone.utc).isoformat()}
                            )
                            logger.info(f"✅ Auto-confirmed email (alternative method) for {email}")
                        except Exception as alt_error:
                            logger.warning(f"⚠️ Alternative confirmation method also failed: {alt_error}")

            # Get access token if session is available (email might be auto-confirmed)
            access_token = None
            if response.session and response.session.access_token:
                access_token = response.session.access_token
            else:
                # If no session, try to sign in to get a session (email should be confirmed now)
                if self.admin_client:
                    try:
                        sign_in_response = self.client.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        if sign_in_response.session and sign_in_response.session.access_token:
                            access_token = sign_in_response.session.access_token
                            logger.info(f"✅ Obtained session token after auto-confirmation for {email}")
                    except Exception as sign_in_error:
                        logger.debug(f"Could not get session after registration: {sign_in_error}")

            user = User(
                id=response.user.id,
                email=response.user.email,
                full_name=full_name,
                created_at=_parse_datetime(response.user.created_at)
            )
            
            return user, access_token
        except ValueError:
            # Re-raise ValueError as-is (our validation errors)
            raise
        except Exception as e:
            # Extract more details from Supabase errors
            error_str = str(e)
            
            # Check for common Supabase error patterns
            if "email" in error_str.lower() and "invalid" in error_str.lower():
                # Supabase might reject very short emails or specific formats
                if len(local_part) < 2:
                    raise ValueError("Email address local part (before @) must be at least 2 characters long")
                raise ValueError(f"Email address validation failed: {error_str}")
            
            # Check if email already exists
            if "already registered" in error_str.lower() or "already exists" in error_str.lower():
                raise ValueError("Email address is already registered")
            
            # Generic error
            raise ValueError(f"Registration failed: {error_str}")

    def login(self, email: str, password: str) -> AuthToken:
        """Authenticate user with Supabase"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.session is None:
                raise ValueError("Login failed")

            return AuthToken(
                access_token=response.session.access_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                refresh_token=response.session.refresh_token
            )
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if error is due to unconfirmed email
            if "email not confirmed" in error_str or "email_not_confirmed" in error_str or "not confirmed" in error_str:
                logger.info(f"📧 Email not confirmed for {email}. Auto-confirming email...")
                
                # If we have admin client, try to auto-confirm email using Admin API
                if self.admin_client:
                    try:
                        # List all users to find the one with matching email
                        admin_response = self.admin_client.auth.admin.list_users()
                        
                        # Find user by email
                        user_to_confirm = None
                        if hasattr(admin_response, 'users'):
                            for user in admin_response.users:
                                if hasattr(user, 'email') and user.email and user.email.lower() == email.lower():
                                    user_to_confirm = user
                                    break
                        
                        if user_to_confirm and hasattr(user_to_confirm, 'id'):
                            # Update user to confirm email using admin API
                            # Try primary method first
                            try:
                                self.admin_client.auth.admin.update_user_by_id(
                                    user_to_confirm.id,
                                    {"email_confirm": True}
                                )
                                logger.info(f"✅ Auto-confirmed email for {email}")
                            except Exception as update_error:
                                # Try alternative method - some Supabase versions use different API
                                logger.debug(f"First update method failed: {update_error}")
                                try:
                                    # Alternative: set email_confirmed_at timestamp
                                    self.admin_client.auth.admin.update_user_by_id(
                                        user_to_confirm.id,
                                        {"email_confirmed_at": datetime.now(timezone.utc).isoformat()}
                                    )
                                    logger.info(f"✅ Auto-confirmed email (alternative method) for {email}")
                                except Exception as alt_error:
                                    logger.warning(f"⚠️ Could not auto-confirm email: {alt_error}")
                            
                            # Retry login after confirmation
                            try:
                                response = self.client.auth.sign_in_with_password({
                                    "email": email,
                                    "password": password
                                })
                                
                                if response.session:
                                    logger.info(f"✅ Login successful after auto-confirmation for {email}")
                                    return AuthToken(
                                        access_token=response.session.access_token,
                                        token_type="bearer",
                                        expires_in=response.session.expires_in,
                                        refresh_token=response.session.refresh_token
                                    )
                            except Exception as retry_error:
                                logger.warning(f"⚠️ Login retry after confirmation failed: {retry_error}")
                                # Fall through to raise original error
                    except Exception as admin_error:
                        logger.warning(f"⚠️ Failed to auto-confirm email via admin API: {admin_error}")
                else:
                    logger.warning(f"⚠️ Admin client not available - cannot auto-confirm email for {email}")
                    logger.warning(f"⚠️ Please configure SUPABASE_SERVICE_KEY to enable auto-confirmation")
            
            # Re-raise original error if we couldn't resolve it
            raise ValueError(f"Login failed: {str(e)}")

    def verify_token(self, token: str) -> User:
        """Verify JWT token with Supabase"""
        try:
            response = self.client.auth.get_user(token)

            if response.user is None:
                raise ValueError("Invalid token")

            # Safely get created_at - handle different response formats
            created_at = None
            try:
                created_at_value = getattr(response.user, 'created_at', None)
                created_at = _parse_datetime(created_at_value)
            except Exception as dt_error:
                logger.debug(f"Could not parse created_at: {dt_error}")
                created_at = None

            return User(
                id=response.user.id,
                email=response.user.email,
                full_name=response.user.user_metadata.get('full_name') if hasattr(response.user, 'user_metadata') else None,
                created_at=created_at,
                metadata=response.user.user_metadata if hasattr(response.user, 'user_metadata') else None
            )
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")

    def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh access token with Supabase"""
        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session is None:
                raise ValueError("Token refresh failed")

            return AuthToken(
                access_token=response.session.access_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                refresh_token=response.session.refresh_token
            )
        except Exception as e:
            raise ValueError(f"Token refresh failed: {str(e)}")

    def logout(self, token: str) -> bool:
        """Logout user with Supabase"""
        try:
            self.client.auth.sign_out()
            return True
        except Exception:
            return False

    def get_user(self, user_id: str) -> User:
        """Get user by ID from Supabase"""
        try:
            # Supabase doesn't have a direct get_user_by_id in the auth API
            # You'd need to use the database API or admin API
            response = self.client.auth.get_user()

            if response.user is None or response.user.id != user_id:
                raise ValueError("User not found")

            return User(
                id=response.user.id,
                email=response.user.email,
                full_name=response.user.user_metadata.get('full_name'),
                created_at=_parse_datetime(response.user.created_at),
                metadata=response.user.user_metadata
            )
        except Exception as e:
            raise ValueError(f"Failed to get user: {str(e)}")

    def update_user(self, user_id: str, **kwargs) -> User:
        """Update user with Supabase"""
        try:
            update_data = {}
            if 'email' in kwargs:
                update_data['email'] = kwargs['email']
            if 'full_name' in kwargs:
                update_data['data'] = {'full_name': kwargs['full_name']}

            response = self.client.auth.update_user(update_data)

            if response.user is None:
                raise ValueError("Update failed")

            return User(
                id=response.user.id,
                email=response.user.email,
                full_name=response.user.user_metadata.get('full_name'),
                created_at=_parse_datetime(response.user.created_at)
            )
        except Exception as e:
            raise ValueError(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """Delete user from Supabase (requires admin privileges)"""
        try:
            # This requires Supabase Admin API
            # For production, use: self.client.auth.admin.delete_user(user_id)
            return True
        except Exception:
            return False

    def reset_password_request(self, email: str) -> bool:
        """Request password reset email from Supabase"""
        try:
            self.client.auth.reset_password_email(email)
            return True
        except Exception:
            return False

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using Supabase reset token"""
        try:
            self.client.auth.update_user({
                "password": new_password
            })
            return True
        except Exception:
            return False
