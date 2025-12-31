"""
Local filesystem storage backend
For development and testing purposes
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from .base import StorageBackend


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class LocalStorage(StorageBackend):
    """Local filesystem storage implementation"""

    def __init__(self, base_path: str = "./local_storage"):
        """
        Initialize local storage

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Convert storage key to file path"""
        # Remove leading slashes and ensure key is within base_path
        clean_key = key.lstrip("/")
        file_path = self.base_path / clean_key

        # Ensure the path is within base_path (prevent directory traversal)
        try:
            file_path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Invalid key: {key}")

        return file_path

    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Save file to local filesystem"""
        file_path = self._get_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(data)
        return str(file_path)

    def save_json(self, key: str, data: dict) -> str:
        """Save JSON data to local filesystem"""
        json_data = json.dumps(data, indent=2, cls=DateTimeEncoder).encode("utf-8")
        return self.save_file(key, json_data, content_type="application/json")

    def get_file(self, key: str) -> bytes:
        """Retrieve file from local filesystem"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        return file_path.read_bytes()

    def get_json(self, key: str) -> dict:
        """Retrieve JSON data from local filesystem"""
        data = self.get_file(key)
        return json.loads(data.decode("utf-8"))

    def delete_file(self, key: str) -> bool:
        """Delete file from local filesystem"""
        file_path = self._get_file_path(key)

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def file_exists(self, key: str) -> bool:
        """Check if file exists"""
        file_path = self._get_file_path(key)
        return file_path.exists()

    def get_download_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate download URL (for local storage, just return file path)
        In a real web app, this would be a route to serve the file
        """
        return f"/api/storage/download/{key}"

    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix"""
        prefix_path = self._get_file_path(prefix) if prefix else self.base_path

        if not prefix_path.exists():
            return []

        if prefix_path.is_file():
            return [str(prefix_path.relative_to(self.base_path))]

        files = []
        for file_path in prefix_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                files.append(str(relative_path))

        return sorted(files)
