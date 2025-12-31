"""
Modelli per metadati repository e file
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Metadati di un singolo file"""
    path: str = Field(..., description="Percorso relativo del file")
    language: Optional[str] = Field(None, description="Linguaggio di programmazione")
    size: int = Field(..., description="Dimensione in bytes")
    lines_of_code: Optional[int] = Field(None, description="Numero di righe di codice")
    last_modified: Optional[datetime] = Field(None, description="Ultima modifica")
    sha256: Optional[str] = Field(None, description="Hash SHA256 del file")


class RepositoryMetadata(BaseModel):
    """Metadati del repository"""
    url: Optional[str] = Field(None, description="URL del repository")
    path: str = Field(..., description="Percorso locale del repository")
    commit_hash: Optional[str] = Field(None, description="Hash del commit corrente")
    branch: Optional[str] = Field(None, description="Branch corrente")
    remote_url: Optional[str] = Field(None, description="URL del remote")
    total_files: int = Field(default=0, description="Numero totale di file")
    total_size: int = Field(default=0, description="Dimensione totale in bytes")
    languages: List[str] = Field(default_factory=list, description="Linguaggi rilevati")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp della scansione")
