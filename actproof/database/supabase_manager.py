"""
Supabase Database Manager for ActProof.ai

This module provides a high-level interface for database operations using Supabase client.
It handles:
- User management
- Scan CRUD operations
- Notifications
- Real-time updates
- Analytics and statistics
"""

import os
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import uuid

from supabase import create_client, Client
from postgrest.exceptions import APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseManager:
    """
    Manager class for Supabase database operations.

    Example:
        ```python
        db = SupabaseManager()

        # Create user
        user = db.create_user(email="user@example.com", full_name="John Doe")

        # Create scan
        scan = db.create_scan(
            user_id=user['id'],
            repo_url="https://github.com/user/repo",
            is_public=False
        )

        # Update scan status
        db.update_scan_status(scan['id'], 'completed', ai_bom={...})
        ```
    """

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None, service_role_key: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase anon key (defaults to SUPABASE_KEY env var)
            service_role_key: Supabase service role key (defaults to SUPABASE_SERVICE_KEY env var)
                             This bypasses RLS and should be used for admin operations
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        self.service_role_key = service_role_key or os.getenv('SUPABASE_SERVICE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Create service role client if available (bypasses RLS)
        if self.service_role_key:
            self.service_client: Optional[Client] = create_client(self.supabase_url, self.service_role_key)
            logger.info("✅ Supabase client initialized with service role key (RLS bypass enabled)")
        else:
            self.service_client = None
            logger.info("✅ Supabase client initialized (using anon key)")

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def _get_user_client(self, access_token: str) -> Client:
        """
        Create a Supabase client with user's access token for RLS policies.
        
        Args:
            access_token: User's JWT access token from Supabase Auth
            
        Returns:
            Supabase client authenticated with user token
        """
        # Create a new client with the user's token
        # The anon key is still needed for the client initialization
        user_client = create_client(self.supabase_url, self.supabase_key)
        # Set the access token in the headers for RLS
        # This ensures auth.uid() works correctly in RLS policies
        user_client.auth.set_session(access_token=access_token, refresh_token="")
        return user_client

    def create_user(
        self,
        user_id: str,
        email: str,
        full_name: Optional[str] = None,
        company_name: Optional[str] = None,
        subscription_plan: str = "free",
        preferences: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user in the database with all required fields.

        Args:
            user_id: UUID from Supabase Auth (must match auth.users.id)
            email: User email (must be unique)
            full_name: User's full name
            company_name: Company name
            subscription_plan: 'free', 'pro', or 'enterprise'
            preferences: User preferences as dict (defaults to empty dict)
            access_token: User's access token for RLS (required for RLS policies)

        Returns:
            Created user record

        Raises:
            APIError: If email already exists or validation fails
        """
        try:
            # Check if user already exists
            existing_user = self.get_user(user_id)
            if existing_user:
                logger.info(f"User {email} (ID: {user_id}) already exists in database")
                return existing_user
            
            # Set default limits based on subscription plan
            plan_limits = {
                'free': {
                    'scans_limit': 10,
                    'storage_limit_gb': 5.0
                },
                'pro': {
                    'scans_limit': 100,
                    'storage_limit_gb': 50.0
                },
                'enterprise': {
                    'scans_limit': 1000,
                    'storage_limit_gb': 500.0
                }
            }
            
            limits = plan_limits.get(subscription_plan, plan_limits['free'])
            
            user_data = {
                'id': user_id,  # Use the UUID from Supabase Auth
                'email': email.lower(),
                'full_name': full_name,
                'company_name': company_name,
                'subscription_plan': subscription_plan,
                'scans_limit': int(limits['scans_limit']),  # Ensure integer
                'scans_used': 0,  # Explicitly set to 0
                'storage_limit_gb': float(limits['storage_limit_gb']),  # Ensure float
                'storage_used_gb': 0.0,  # Explicitly set to 0.0
                'is_active': True,
                'preferences': preferences or {}
            }
            
            logger.debug(f"Creating user with data: {user_data}")
            
            # Use service role client if available (bypasses RLS), otherwise try user token
            client_to_use = self.client
            if self.service_client:
                # Service role key bypasses RLS - use it for admin operations
                client_to_use = self.service_client
                logger.debug(f"Using service role key to create user {user_id} (RLS bypassed)")
            elif access_token:
                try:
                    # Create a client with user's token for RLS
                    client_to_use = self._get_user_client(access_token)
                    logger.debug(f"Using user token for RLS when creating user {user_id}")
                except Exception as token_error:
                    logger.warning(f"Failed to create user client with token, using default: {token_error}")
                    # Fall back to default client (might fail if RLS is strict)
            
            # Note: created_at and updated_at are set automatically by database defaults
            result = client_to_use.table('users').insert(user_data).execute()

            logger.info(f"✅ User created in database: {email} (ID: {user_id})")
            return result.data[0]

        except APIError as e:
            logger.error(f"❌ Failed to create user {email}: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Uses service role client if available to bypass RLS.
        """
        try:
            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            client_type = "service_role" if self.service_client else "anon"
            
            logger.debug(f"Getting user {user_id} using {client_type} client")
            result = client_to_use.table('users').select('*').eq('id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.debug(f"✅ User {user_id} found in database")
                return result.data[0]
            else:
                logger.warning(f"⚠️ User {user_id} not found in database (empty result from {client_type} client)")
                # If using anon client and got empty result, might be RLS issue
                if not self.service_client:
                    logger.warning(f"⚠️ Consider using SUPABASE_SERVICE_KEY to bypass RLS for admin operations")
                return None
        except APIError as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            # Log more details about the error
            if hasattr(e, 'code'):
                logger.error(f"   Error code: {e.code}")
            if hasattr(e, 'message'):
                logger.error(f"   Error message: {e.message}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error getting user {user_id}: {e}", exc_info=True)
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Uses service role client if available to bypass RLS.
        """
        try:
            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            
            result = client_to_use.table('users').select('*').eq('email', email.lower()).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.debug(f"User with email {email} not found in database (empty result)")
                return None
        except APIError as e:
            logger.error(f"❌ Failed to get user by email {email}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error getting user by email {email}: {e}")
            return None

    def update_user(self, user_id: str, updates: Dict[str, Any], access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Update user fields
        
        Args:
            user_id: User ID to update
            updates: Dictionary of fields to update
            access_token: Optional user token for RLS (uses service role if available)
        
        Returns:
            Updated user record
        """
        try:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Use service role client if available (bypasses RLS), otherwise try user token
            client_to_use = self.client
            if self.service_client:
                # Service role key bypasses RLS - use it for admin operations
                client_to_use = self.service_client
                logger.debug(f"Using service role key to update user {user_id} (RLS bypassed)")
            elif access_token:
                try:
                    # Create a client with user's token for RLS
                    client_to_use = self._get_user_client(access_token)
                    logger.debug(f"Using user token for RLS when updating user {user_id}")
                except Exception as token_error:
                    logger.warning(f"Failed to create user client with token, using default: {token_error}")
                    # Fall back to default client (might fail if RLS is strict)
            
            result = client_to_use.table('users').update(updates).eq('id', user_id).execute()
            logger.info(f"✅ User updated: {user_id}")
            return result.data[0]
        except APIError as e:
            logger.error(f"❌ Failed to update user {user_id}: {e}")
            raise

    def increment_scans_used(self, user_id: str) -> None:
        """Increment user's scans_used counter"""
        try:
            # Use RPC function for atomic increment
            self.client.rpc('increment_user_scans', {'p_user_id': user_id}).execute()
            logger.info(f"✅ Incremented scans_used for user {user_id}")
        except APIError as e:
            logger.error(f"❌ Failed to increment scans_used: {e}")

    def check_scan_limit(self, user_id: str) -> bool:
        """
        Check if user can create new scan.
        
        If user doesn't exist in database, tries to create a default record.
        This can happen if registration in Auth succeeded but database insert failed.

        Returns:
            True if user has remaining scans, False otherwise
        """
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"⚠️ User {user_id} not found in database. Attempting to create default record...")
            # Try to get user info from Auth to create database record
            try:
                # Get user email from auth (we need to query auth.users or use a different method)
                # For now, create a minimal user record with default values
                # This is a fallback - ideally the user should be created during registration
                default_user_data = {
                    'id': user_id,
                    'email': f'user_{user_id[:8]}@unknown.local',  # Placeholder email
                    'subscription_plan': 'free',
                    'scans_limit': 10,
                    'scans_used': 0,
                    'storage_limit_gb': 5.0,
                    'storage_used_gb': 0.0,
                    'is_active': True,
                    'preferences': {}
                }
                
                # Use service client if available, otherwise try with anon key
                client_to_use = self.service_client if self.service_client else self.client
                result = client_to_use.table('users').insert(default_user_data).execute()
                user = result.data[0] if result.data else None
                logger.info(f"✅ Created fallback user record for {user_id}")
            except APIError as create_error:
                error_code = create_error.code if hasattr(create_error, 'code') else None
                error_message = str(create_error)
                
                # Check if user already exists (duplicate key error)
                if error_code == '23505' or 'duplicate key' in error_message.lower() or 'already exists' in error_message.lower():
                    logger.info(f"ℹ️ User {user_id} already exists in database (duplicate key). Fetching existing record...")
                    # User exists, try to fetch it again
                    user = self.get_user(user_id)
                    if user:
                        logger.info(f"✅ Retrieved existing user record for {user_id}")
                    else:
                        logger.warning(f"⚠️ User {user_id} exists but could not be retrieved")
                        return False
                else:
                    logger.error(f"❌ Failed to create fallback user record: {create_error}")
                    return False
            except Exception as create_error:
                logger.error(f"❌ Failed to create fallback user record: {create_error}")
                return False
        
        if not user:
            return False

        # Check if scans_used is None or not set (shouldn't happen, but safety check)
        scans_used = user.get('scans_used', 0) or 0
        scans_limit = user.get('scans_limit', 10) or 10
        
        logger.debug(f"User {user_id}: scans_used={scans_used}, scans_limit={scans_limit}")
        return scans_used < scans_limit

    # ========================================================================
    # SCAN OPERATIONS
    # ========================================================================

    def create_scan(
        self,
        repo_url: str,
        user_id: Optional[str] = None,
        is_public: bool = False,
        branch: str = "main",
        metadata: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new scan.

        Args:
            repo_url: GitHub/GitLab repository URL
            user_id: User ID (None for public scans)
            is_public: Whether scan is public (accessible to all)
            branch: Git branch to scan
            metadata: Additional metadata (tags, notes, etc.)
            access_token: User's access token for RLS (optional, uses service role if available)

        Returns:
            Created scan record
        """
        try:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            repo_owner = repo_url.rstrip('/').split('/')[-2] if '/' in repo_url else None

            # Generate a new UUID for the scan
            # The database will use this as the primary key
            new_scan_id = str(uuid.uuid4())

            scan_data = {
                'id': new_scan_id,
                'user_id': user_id,
                'repo_url': repo_url,
                'repo_name': repo_name,
                'repo_owner': repo_owner,
                'branch': branch,
                'status': 'pending',
                'is_public': is_public,
                'metadata': metadata or {},
                'started_at': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            logger.debug(f"Creating scan with ID: {new_scan_id}, is_public: {is_public}, user_id: {user_id}")

            # Use service role client if available (bypasses RLS), otherwise try user token
            client_to_use = self.client
            if self.service_client:
                # Service role key bypasses RLS - use it for admin operations
                client_to_use = self.service_client
                logger.debug(f"Using service role key to create scan (RLS bypassed)")
            elif access_token:
                try:
                    # Create a client with user's token for RLS
                    client_to_use = self._get_user_client(access_token)
                    logger.debug(f"Using user token for RLS when creating scan")
                except Exception as token_error:
                    logger.warning(f"Failed to create user client with token, using default: {token_error}")
                    # Fall back to default client (might fail if RLS is strict)

            result = client_to_use.table('scans').insert(scan_data).execute()
            logger.info(f"✅ Scan created: {scan_data['id']} for {repo_url}")
            return result.data[0]

        except APIError as e:
            logger.error(f"❌ Failed to create scan: {e}")
            raise

    def get_scan(self, scan_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get scan by ID
        
        Uses service role client if available to bypass RLS.
        """
        try:
            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            if access_token and not self.service_client:
                try:
                    client_to_use = self._get_user_client(access_token)
                except Exception as token_error:
                    logger.debug(f"Could not create user client for get_scan: {token_error}")
            
            result = client_to_use.table('scans').select('*').eq('id', scan_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.debug(f"✅ Scan {scan_id} found in database")
                return result.data[0]
            else:
                logger.debug(f"⚠️ Scan {scan_id} not found in database (empty result)")
                return None
        except APIError as e:
            logger.error(f"❌ Failed to get scan {scan_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error getting scan {scan_id}: {e}", exc_info=True)
            return None

    def get_user_scans(
        self,
        user_id: str,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all scans for a user.

        Args:
            user_id: User ID
            limit: Maximum number of scans to return
            status: Filter by status (optional)

        Returns:
            List of scan records
        """
        try:
            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            client_type = "service_role (RLS bypassed)" if self.service_client else "anon (RLS active)"
            logger.debug(f"Getting scans for user {user_id} using {client_type} client")

            query = client_to_use.table('scans').select('*').eq('user_id', user_id)

            if status:
                query = query.eq('status', status)

            result = query.order('created_at', desc=True).limit(limit).execute()

            # Clean and validate the data
            scans = result.data or []
            logger.info(f"✅ Retrieved {len(scans)} scans from database for user {user_id} using {client_type}")

            # Parse JSON fields if they are strings
            for scan in scans:
                # Parse JSON string fields
                for field in ['ai_bom', 'compliance_result', 'scan_summary', 'stats', 'metadata']:
                    if field in scan and isinstance(scan[field], str):
                        try:
                            scan[field] = json.loads(scan[field])
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Failed to parse {field} for scan {scan.get('id')}: {e}")
                            scan[field] = {}

            return scans

        except APIError as e:
            logger.error(f"❌ Failed to get user scans: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error getting user scans: {e}", exc_info=True)
            return []

    def get_recent_scans(self, limit: int = 20, include_public: bool = True) -> List[Dict[str, Any]]:
        """Get recent scans (optionally include public scans)"""
        try:
            query = self.client.table('scans').select('*')

            if include_public:
                query = query.eq('is_public', True)

            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data

        except APIError as e:
            logger.error(f"❌ Failed to get recent scans: {e}")
            return []

    def update_scan_status(
        self,
        scan_id: str,
        status: str,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update scan status.

        Args:
            scan_id: Scan ID
            status: New status ('pending', 'cloning', 'scanning', 'analyzing', 'completed', 'failed')
            error_message: Error message if status is 'failed'
            completed_at: Completion timestamp (auto-set if status is 'completed' or 'failed')
            access_token: Optional user access token for RLS

        Returns:
            Updated scan record, or None if update succeeded but record couldn't be retrieved
        """
        try:
            updates = {
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            if status in ['completed', 'failed'] and not completed_at:
                updates['completed_at'] = datetime.now(timezone.utc).isoformat()
            elif completed_at:
                updates['completed_at'] = completed_at.isoformat()

            if error_message:
                updates['error_message'] = error_message

            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            if access_token and not self.service_client:
                try:
                    client_to_use = self._get_user_client(access_token)
                except Exception as token_error:
                    logger.debug(f"Could not create user client for scan update: {token_error}")

            result = client_to_use.table('scans').update(updates).eq('id', scan_id).execute()
            logger.info(f"✅ Scan status updated: {scan_id} → {status}")
            
            # Check if result contains data
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                # Update succeeded but we can't retrieve the record (likely RLS issue)
                # This is OK - the update was successful
                logger.debug(f"Scan {scan_id} updated successfully but record not returned (RLS may be blocking read)")
                return None

        except APIError as e:
            logger.error(f"❌ Failed to update scan status: {e}")
            raise

    def _make_json_serializable(self, obj: Any) -> Any:
        """
        Recursively convert objects to JSON-serializable format.
        Handles datetime, date, UUID, and other non-serializable types.
        """
        from datetime import date
        import uuid as uuid_module
        
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, uuid_module.UUID):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'model_dump'):
            # Pydantic models
            try:
                return self._make_json_serializable(obj.model_dump(mode='json'))
            except (TypeError, AttributeError):
                try:
                    return self._make_json_serializable(obj.model_dump())
                except (TypeError, AttributeError):
                    return str(obj)
        elif hasattr(obj, 'dict'):
            # Pydantic v1 models
            return self._make_json_serializable(obj.dict())
        elif hasattr(obj, '__dict__'):
            # Generic objects with __dict__
            return self._make_json_serializable(obj.__dict__)
        else:
            # Try to return as-is if it's a basic type
            try:
                import json
                json.dumps(obj)  # Test if serializable
                return obj
            except (TypeError, ValueError):
                # Fallback to string representation
                return str(obj)

    def update_scan_results(
        self,
        scan_id: str,
        ai_bom: Optional[Dict[str, Any]] = None,
        compliance_result: Optional[Dict[str, Any]] = None,
        scan_summary: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update scan results.

        Args:
            scan_id: Scan ID
            ai_bom: AI Bill of Materials (JSONB)
            compliance_result: Compliance check results (JSONB)
            scan_summary: Summary statistics (JSONB)
            stats: Scan statistics (JSONB)
            access_token: Optional user access token for RLS

        Returns:
            Updated scan record, or None if update succeeded but record couldn't be retrieved
        """
        try:
            updates = {'updated_at': datetime.now(timezone.utc).isoformat()}

            if ai_bom is not None:
                updates['ai_bom'] = self._make_json_serializable(ai_bom)
            if compliance_result is not None:
                updates['compliance_result'] = self._make_json_serializable(compliance_result)
            if scan_summary is not None:
                updates['scan_summary'] = self._make_json_serializable(scan_summary)
            if stats is not None:
                updates['stats'] = self._make_json_serializable(stats)

            # Use service client if available (bypasses RLS)
            client_to_use = self.service_client if self.service_client else self.client
            if access_token and not self.service_client:
                try:
                    client_to_use = self._get_user_client(access_token)
                except Exception as token_error:
                    logger.debug(f"Could not create user client for scan results update: {token_error}")

            result = client_to_use.table('scans').update(updates).eq('id', scan_id).execute()
            logger.info(f"✅ Scan results updated: {scan_id}")
            
            # Check if result contains data
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.debug(f"Scan {scan_id} results updated successfully but record not returned (RLS may be blocking read)")
                return None

        except APIError as e:
            logger.error(f"❌ Failed to update scan results: {e}")
            raise
        except TypeError as e:
            logger.error(f"❌ JSON serialization error in update_scan_results: {e}", exc_info=True)
            raise

    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan"""
        try:
            self.client.table('scans').delete().eq('id', scan_id).execute()
            logger.info(f"✅ Scan deleted: {scan_id}")
            return True
        except APIError as e:
            logger.error(f"❌ Failed to delete scan {scan_id}: {e}")
            return False

    # ========================================================================
    # NOTIFICATION OPERATIONS
    # ========================================================================

    def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a notification.

        Args:
            user_id: User ID
            notification_type: Type ('scan_completed', 'scan_failed', etc.)
            title: Notification title
            message: Notification message
            data: Additional data (scan_id, repo_url, etc.)
            priority: Priority level ('low', 'normal', 'high', 'urgent')
            access_token: Optional user access token for RLS (uses service role if available)

        Returns:
            Created notification record
        """
        try:
            notification_data = {
                'user_id': user_id,
                'type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'priority': priority,
                'is_read': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            # Use service role client if available (bypasses RLS), otherwise try user token
            client_to_use = self.client
            if self.service_client:
                # Service role key bypasses RLS - use it for admin operations
                client_to_use = self.service_client
                logger.debug(f"Using service role key to create notification for user {user_id} (RLS bypassed)")
            elif access_token:
                try:
                    # Create a client with user's token for RLS
                    client_to_use = self._get_user_client(access_token)
                    logger.debug(f"Using user token for RLS when creating notification for user {user_id}")
                except Exception as token_error:
                    logger.warning(f"Failed to create user client with token, using default: {token_error}")
                    # Fall back to default client (might fail if RLS is strict)

            result = client_to_use.table('notifications').insert(notification_data).execute()
            logger.info(f"✅ Notification created for user {user_id}: {title}")
            return result.data[0]

        except APIError as e:
            logger.error(f"❌ Failed to create notification: {e}")
            raise

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user notifications"""
        try:
            query = self.client.table('notifications').select('*').eq('user_id', user_id)

            if unread_only:
                query = query.eq('is_read', False)

            result = query.order('created_at', desc=True).limit(limit).execute()
            return result.data

        except APIError as e:
            logger.error(f"❌ Failed to get notifications: {e}")
            return []

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            self.client.table('notifications').update({
                'is_read': True,
                'read_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', notification_id).execute()
            return True
        except APIError as e:
            logger.error(f"❌ Failed to mark notification as read: {e}")
            return False

    def mark_all_notifications_read(self, user_id: str) -> bool:
        """Mark all user notifications as read"""
        try:
            self.client.table('notifications').update({
                'is_read': True,
                'read_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).eq('is_read', False).execute()
            return True
        except APIError as e:
            logger.error(f"❌ Failed to mark all notifications as read: {e}")
            return False

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        try:
            result = self.client.table('notifications').select('id', count='exact').eq(
                'user_id', user_id
            ).eq('is_read', False).execute()
            return result.count or 0
        except APIError as e:
            logger.error(f"❌ Failed to get unread count: {e}")
            return 0

    # ========================================================================
    # ANALYTICS AND STATISTICS
    # ========================================================================

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics.

        Returns:
            Dictionary with:
            - total_scans
            - completed_scans
            - failed_scans
            - pending_scans
            - avg_duration_seconds
            - total_models_found
            - total_datasets_found
            - avg_compliance_score
        """
        try:
            # Use database function
            result = self.client.rpc('get_user_statistics', {'p_user_id': user_id}).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            # Fallback to manual calculation
            scans = self.get_user_scans(user_id, limit=1000)

            total_scans = len(scans)
            completed_scans = len([s for s in scans if s['status'] == 'completed'])
            failed_scans = len([s for s in scans if s['status'] == 'failed'])
            pending_scans = len([s for s in scans if s['status'] in ['pending', 'cloning', 'scanning', 'analyzing']])

            durations = [s['duration_seconds'] for s in scans if s.get('duration_seconds')]
            avg_duration = sum(durations) / len(durations) if durations else 0

            total_models = sum([
                s.get('scan_summary', {}).get('models_found', 0)
                for s in scans if s.get('scan_summary')
            ])

            total_datasets = sum([
                s.get('scan_summary', {}).get('datasets_found', 0)
                for s in scans if s.get('scan_summary')
            ])

            compliance_scores = [
                float(s.get('compliance_result', {}).get('compliance_score', 0))
                for s in scans if s.get('compliance_result')
            ]
            avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0

            return {
                'total_scans': total_scans,
                'completed_scans': completed_scans,
                'failed_scans': failed_scans,
                'pending_scans': pending_scans,
                'avg_duration_seconds': avg_duration,
                'total_models_found': total_models,
                'total_datasets_found': total_datasets,
                'avg_compliance_score': avg_compliance
            }

        except APIError as e:
            logger.error(f"❌ Failed to get user statistics: {e}")
            return {}

    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete dashboard data for a user.

        Returns:
            Dictionary with user info, statistics, recent scans, and notifications
        """
        user = self.get_user(user_id)
        stats = self.get_user_statistics(user_id)
        recent_scans = self.get_user_scans(user_id, limit=10)
        notifications = self.get_user_notifications(user_id, unread_only=True, limit=5)
        unread_count = self.get_unread_count(user_id)

        return {
            'user': user,
            'statistics': stats,
            'recent_scans': recent_scans,
            'notifications': notifications,
            'unread_notifications_count': unread_count
        }

    # ========================================================================
    # REALTIME SUBSCRIPTIONS
    # ========================================================================

    def subscribe_to_scans(self, user_id: str, callback):
        """
        Subscribe to real-time scan updates for a user.

        Args:
            user_id: User ID
            callback: Function to call on update

        Example:
            ```python
            def on_scan_update(payload):
                print(f"Scan updated: {payload['new']}")

            db.subscribe_to_scans(user_id, on_scan_update)
            ```
        """
        channel = self.client.channel(f'scans:{user_id}')
        channel.on(
            'postgres_changes',
            callback=callback,
            event='*',
            schema='public',
            table='scans',
            filter=f'user_id=eq.{user_id}'
        )
        channel.subscribe()
        return channel

    def subscribe_to_notifications(self, user_id: str, callback):
        """Subscribe to real-time notification updates"""
        channel = self.client.channel(f'notifications:{user_id}')
        channel.on(
            'postgres_changes',
            callback=callback,
            event='INSERT',
            schema='public',
            table='notifications',
            filter=f'user_id=eq.{user_id}'
        )
        channel.subscribe()
        return channel

    # ========================================================================
    # AUDIT LOG
    # ========================================================================

    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log an action to audit trail"""
        try:
            self.client.table('audit_logs').insert({
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details or {},
                'ip_address': ip_address,
                'user_agent': user_agent,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
        except APIError as e:
            logger.error(f"❌ Failed to log action: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db_manager(supabase_url: Optional[str] = None, supabase_key: Optional[str] = None, service_role_key: Optional[str] = None) -> SupabaseManager:
    """
    Get a database manager instance (singleton pattern).
    
    Args:
        supabase_url: Optional Supabase URL (defaults to SUPABASE_URL env var or settings)
        supabase_key: Optional Supabase key (defaults to SUPABASE_KEY env var or settings)
        service_role_key: Optional Supabase service role key (defaults to SUPABASE_SERVICE_KEY env var or settings)
    
    Returns:
        SupabaseManager instance
    """
    if not hasattr(get_db_manager, '_instance'):
        # If not provided, try to get from settings
        if not supabase_url or not supabase_key:
            try:
                from actproof.config import get_settings
                settings = get_settings()
                supabase_url = supabase_url or settings.supabase_url
                supabase_key = supabase_key or settings.supabase_key
                # Try to get service role key from settings if available
                if not service_role_key:
                    service_role_key = getattr(settings, 'supabase_service_key', None) or os.getenv('SUPABASE_SERVICE_KEY')
            except Exception as e:
                logger.debug(f"Could not load settings: {e}")
        
        get_db_manager._instance = SupabaseManager(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            service_role_key=service_role_key
        )
    return get_db_manager._instance
