"""
Base storage backend interface
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path
import json


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Save file to storage

        Args:
            key: Storage key/path
            data: File data as bytes
            content_type: MIME type of the file

        Returns:
            URL or path to the saved file
        """
        pass

    @abstractmethod
    def save_json(self, key: str, data: dict) -> str:
        """
        Save JSON data to storage

        Args:
            key: Storage key/path
            data: Dictionary to save as JSON

        Returns:
            URL or path to the saved file
        """
        pass

    @abstractmethod
    def get_file(self, key: str) -> bytes:
        """
        Retrieve file from storage

        Args:
            key: Storage key/path

        Returns:
            File data as bytes
        """
        pass

    @abstractmethod
    def get_json(self, key: str) -> dict:
        """
        Retrieve JSON data from storage

        Args:
            key: Storage key/path

        Returns:
            Parsed JSON as dictionary
        """
        pass

    @abstractmethod
    def delete_file(self, key: str) -> bool:
        """
        Delete file from storage

        Args:
            key: Storage key/path

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in storage

        Args:
            key: Storage key/path

        Returns:
            True if file exists
        """
        pass

    @abstractmethod
    def get_download_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate a download URL for a file

        Args:
            key: Storage key/path
            expiration: URL expiration time in seconds

        Returns:
            Download URL
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files with given prefix

        Args:
            prefix: Key prefix to filter by

        Returns:
            List of file keys
        """
        pass
