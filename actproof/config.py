"""
Configuration management for ActProof.ai
Handles environment variables and settings validation
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Literal, Union
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "ActProof.ai"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # API Keys
    openai_api_key: Optional[str] = None

    # Storage Backend
    storage_backend: Literal["local", "s3", "azure", "gcs"] = "local"

    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "eu-central-1"
    s3_bucket_name: str = "actproof-scan-results"
    s3_endpoint_url: Optional[str] = None  # For S3-compatible services (R2, MinIO)

    # Azure Blob Storage
    azure_storage_account: Optional[str] = None
    azure_storage_key: Optional[str] = None
    azure_container_name: str = "actproof-scans"

    # Google Cloud Storage
    gcs_bucket_name: str = "actproof-scan-results"
    gcs_credentials_path: Optional[Path] = None

    # Database
    database_url: str = "sqlite:///./actproof.db"  # Default to SQLite for development

    # Supabase (Auth + DB + Storage)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_key: Optional[str] = None  # Service role key (bypasses RLS, for admin operations)
    supabase_jwt_secret: Optional[str] = None

    # Vector Store
    vector_store_backend: Literal["chroma", "pinecone", "weaviate", "qdrant"] = "chroma"

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "eu-west1-gcp"
    pinecone_index_name: str = "actproof-knowledge-base"

    # Weaviate
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None

    # Qdrant
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    # Security
    secret_key: str = "change-this-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours
    
    # API Authentication
    static_api_token: Optional[str] = None  # Static token for early users (set via ACTPROOF_STATIC_API_TOKEN env var)

    # CORS
    cors_origins: Union[str, list[str]] = "http://localhost:5000,http://localhost:3000"
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        """Parse CORS origins from string (comma-separated) or list"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v if isinstance(v, list) else []

    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Concurrent Scans Limiting
    max_concurrent_scans: int = 3  # Maximum number of simultaneous scans

    # File Upload
    max_upload_size_mb: int = 100
    allowed_extensions: Union[str, set[str]] = ".py,.js,.ts,.java,.go,.rs"
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v: Union[str, set[str]]) -> set[str]:
        """Parse allowed extensions from string (comma-separated) or set"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return {ext.strip() for ext in v.split(',') if ext.strip()}
        return v if isinstance(v, set) else set()
    
    # File Scanning Limits
    max_file_size_mb: int = 10  # Maximum file size to scan (in MB)
    max_repo_size_gb: float = 5.0  # Maximum repository size to clone (in GB)
    skip_large_files: bool = True  # Skip large files during scanning

    # Temporary Storage
    temp_repos_dir: Path = Path("./temp_repos")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
