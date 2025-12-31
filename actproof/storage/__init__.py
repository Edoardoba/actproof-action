"""
Cloud storage abstraction layer for ActProof.ai
Supports multiple backends: S3, Azure Blob, GCS, local filesystem
"""

from .base import StorageBackend
from .local_storage import LocalStorage
from .s3_storage import S3Storage

__all__ = ["StorageBackend", "LocalStorage", "S3Storage", "get_storage_backend"]


def get_storage_backend(backend_type: str = "local", **kwargs) -> StorageBackend:
    """
    Factory function to get storage backend instance

    Args:
        backend_type: Type of storage backend ("local", "s3", "azure", "gcs")
        **kwargs: Backend-specific configuration

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If backend_type is not supported
    """
    backends = {
        "local": LocalStorage,
        "s3": S3Storage,
    }

    backend_class = backends.get(backend_type.lower())
    if backend_class is None:
        raise ValueError(
            f"Unsupported storage backend: {backend_type}. "
            f"Supported backends: {list(backends.keys())}"
        )

    return backend_class(**kwargs)
