"""
ActProof.ai - API Authentication Middleware
Handles API token authentication for GitHub Actions and API clients
"""

import os
import jwt
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends, Request
from actproof.config import get_settings

logger = logging.getLogger(__name__)


class StaticTokenAuth:
    """Static token authentication for early users and GitHub Actions"""
    
    # Default static token for GitHub Marketplace (public token for easy onboarding)
    DEFAULT_STATIC_TOKEN = "bab9ba47fd28e4abb985acbd2b23a6c64d0c3640621d85715af54ce67ed306c3"
    
    def __init__(self):
        self.settings = get_settings()
        # Static token from environment, or use default for marketplace
        self.static_token = os.getenv("ACTPROOF_STATIC_API_TOKEN", self.DEFAULT_STATIC_TOKEN)
        # JWT secret key for generating/verifying tokens
        self.jwt_secret = self.settings.secret_key
        self.jwt_algorithm = self.settings.jwt_algorithm
        
    def verify_token(self, token: str) -> Dict[str, str]:
        """
        Verify API token (supports both static token and JWT)
        
        Args:
            token: API token string
            
        Returns:
            Dict with user information (user_id, email, tier)
            
        Raises:
            HTTPException: If token is invalid
        """
        # Check static token first (for early users)
        if self.static_token and token == self.static_token:
            logger.info("✅ Static token authentication successful")
            return {
                "user_id": "github-actions-user",
                "email": "github-actions@actproof.ai",
                "tier": "free",
                "source": "static_token"
            }
        
        # Try JWT token verification
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            logger.info(f"✅ JWT token authentication successful for user {payload.get('user_id')}")
            return {
                "user_id": payload.get("user_id", "unknown"),
                "email": payload.get("email", "unknown@actproof.ai"),
                "tier": payload.get("tier", "free"),
                "source": "jwt"
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            # If static token not set, provide helpful error
            if not self.static_token:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token. Please contact support to get an API token."
                )
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )
    
    def generate_api_token(
        self, 
        user_id: str, 
        email: str, 
        tier: str = "free",
        expires_days: int = 365
    ) -> str:
        """
        Generate a JWT API token for a user
        
        Args:
            user_id: User identifier
            email: User email
            tier: User tier (free, pro, enterprise)
            expires_days: Token expiration in days (default 1 year)
            
        Returns:
            JWT token string
        """
        expiration = datetime.utcnow() + timedelta(days=expires_days)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "tier": tier,
            "purpose": "api_token",
            "iat": datetime.utcnow(),
            "exp": expiration
        }
        
        token = jwt.encode(
            payload, 
            self.jwt_secret, 
            algorithm=self.jwt_algorithm
        )
        
        logger.info(f"Generated API token for user {user_id} (tier: {tier})")
        return token


# Global auth instance
_auth: Optional[StaticTokenAuth] = None


def get_auth() -> StaticTokenAuth:
    """Get global authentication instance"""
    global _auth
    if _auth is None:
        _auth = StaticTokenAuth()
    return _auth


async def verify_api_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Dict[str, str]:
    """
    FastAPI dependency to verify API token from Authorization header
    
    Usage:
        @router.post("/api/scan")
        async def scan_endpoint(user: dict = Depends(verify_api_token)):
            user_id = user["user_id"]
            ...
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide: Authorization: Bearer <token>"
        )
    
    try:
        # Extract Bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header format. Use: Bearer <token>"
            )
        
        token = parts[1]
        auth = get_auth()
        user_info = auth.verify_token(token)
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )

