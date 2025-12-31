"""
Authentication module for ActProof.ai
Supports multiple auth providers: Supabase, Auth0, custom JWT
"""

from .base import AuthProvider
from .jwt_auth import JWTAuth
from .supabase_auth import SupabaseAuth

__all__ = ["AuthProvider", "JWTAuth", "SupabaseAuth", "get_auth_provider"]


def get_auth_provider(provider_type: str = "jwt", **kwargs) -> AuthProvider:
    """
    Factory function to get authentication provider

    Args:
        provider_type: Type of auth provider ("jwt", "supabase", "auth0")
        **kwargs: Provider-specific configuration

    Returns:
        AuthProvider instance
    """
    providers = {
        "jwt": JWTAuth,
        "supabase": SupabaseAuth,
    }

    provider_class = providers.get(provider_type.lower())
    if provider_class is None:
        raise ValueError(
            f"Unsupported auth provider: {provider_type}. "
            f"Supported providers: {list(providers.keys())}"
        )

    return provider_class(**kwargs)
