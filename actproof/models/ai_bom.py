"""
Modelli Pydantic V2 per AI-BOM conforme a SPDX 3.0
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ComponentType(str, Enum):
    """Tipi di componenti AI"""
    MODEL = "model"
    DATASET = "dataset"
    LIBRARY = "library"
    API_CLIENT = "api_client"
    INFRASTRUCTURE = "infrastructure"


class ModelType(str, Enum):
    """Tipi di modelli AI"""
    LLM = "llm"
    VISION = "vision"
    AUDIO = "audio"
    EMBEDDING = "embedding"
    FINE_TUNED = "fine_tuned"
    CUSTOM = "custom"


class DatasetType(str, Enum):
    """Tipi di dataset"""
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"
    PRODUCTION = "production"


class LicenseType(str, Enum):
    """Tipi di licenze"""
    APACHE_2_0 = "Apache-2.0"
    MIT = "MIT"
    GPL_3_0 = "GPL-3.0"
    PROPRIETARY = "Proprietary"
    UNKNOWN = "Unknown"


class DetectionLocation(BaseModel):
    """
    Location where an AI component was detected in the codebase.

    This model stores precise location information for display in the dashboard,
    allowing users to navigate directly to the source of a detection.
    """
    file_path: str = Field(..., description="Path to the file relative to repository root")
    line_number: int = Field(..., ge=1, description="Line number where detection starts (1-indexed)")
    column: Optional[int] = Field(None, ge=0, description="Column position (0-indexed)")
    end_line: Optional[int] = Field(None, ge=1, description="End line for multi-line detections")
    end_column: Optional[int] = Field(None, ge=0, description="End column position")
    code_snippet: Optional[str] = Field(None, description="Code snippet around the detection")
    detection_type: str = Field(..., description="Type of detection (e.g., 'from_pretrained', 'openai_client')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence score")

    def to_display_string(self) -> str:
        """Format for display: file.py:42"""
        return f"{self.file_path}:{self.line_number}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code_snippet": self.code_snippet,
            "detection_type": self.detection_type,
            "confidence": self.confidence,
            "display": self.to_display_string(),
        }


class ModelComponent(BaseModel):
    """Componente modello AI"""
    name: str = Field(..., description="Nome del modello")
    version: Optional[str] = Field(None, description="Versione del modello")
    model_type: ModelType = Field(..., description="Tipo di modello")
    provider: Optional[str] = Field(None, description="Provider (OpenAI, Anthropic, etc.)")
    api_endpoint: Optional[str] = Field(None, description="Endpoint API se disponibile")
    license: Optional[LicenseType] = Field(None, description="Licenza del modello")
    source_location: Optional[str] = Field(None, description="URL o percorso sorgente")
    parameters: Optional[int] = Field(None, description="Numero di parametri")
    detected_in: List[str] = Field(default_factory=list, description="File dove è stato rilevato (legacy)")
    detection_locations: List[DetectionLocation] = Field(default_factory=list, description="Precise locations with line numbers")
    usage_context: Optional[str] = Field(None, description="Contesto d'uso (inference, training, etc.)")

    def get_primary_location(self) -> Optional[str]:
        """Get the primary detection location for display"""
        if self.detection_locations:
            return self.detection_locations[0].to_display_string()
        elif self.detected_in:
            return self.detected_in[0]
        return None


class DatasetComponent(BaseModel):
    """Componente dataset"""
    name: str = Field(..., description="Nome del dataset")
    dataset_type: DatasetType = Field(..., description="Tipo di dataset")
    source_location: Optional[str] = Field(None, description="URL o percorso sorgente")
    size: Optional[int] = Field(None, description="Dimensione in record o file")
    license: Optional[LicenseType] = Field(None, description="Licenza del dataset")
    gdpr_compliant: Optional[bool] = Field(None, description="Conformità GDPR")
    detected_in: List[str] = Field(default_factory=list, description="File dove è stato rilevato (legacy)")
    detection_locations: List[DetectionLocation] = Field(default_factory=list, description="Precise locations with line numbers")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadati aggiuntivi")

    def get_primary_location(self) -> Optional[str]:
        """Get the primary detection location for display"""
        if self.detection_locations:
            return self.detection_locations[0].to_display_string()
        elif self.detected_in:
            return self.detected_in[0]
        return None


class DependencyComponent(BaseModel):
    """Componente dipendenza (libreria)"""
    name: str = Field(..., description="Nome della libreria")
    version: Optional[str] = Field(None, description="Versione")
    package_manager: Optional[str] = Field(None, description="Package manager (pip, npm, etc.)")
    license: Optional[LicenseType] = Field(None, description="Licenza")
    is_ai_related: bool = Field(False, description="Se è una libreria AI/ML")
    vulnerability_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS score se disponibile")
    detected_in: List[str] = Field(default_factory=list, description="File di configurazione dove è stato rilevato (legacy)")
    detection_locations: List[DetectionLocation] = Field(default_factory=list, description="Precise locations with line numbers")


class AIBOM(BaseModel):
    """
    AI Bill of Materials conforme a SPDX 3.0
    """
    spdx_version: str = Field(default="SPDX-3.0", description="Versione SPDX")
    data_license: str = Field(default="CC0-1.0", description="Licenza dei metadati")
    spdx_id: str = Field(..., description="ID univoco SPDX")
    name: str = Field(..., description="Nome del documento AI-BOM")
    document_namespace: str = Field(..., description="Namespace univoco del documento")
    created: datetime = Field(default_factory=datetime.utcnow, description="Data di creazione")
    creator: str = Field(..., description="Creatore del documento")
    
    # Componenti AI
    models: List[ModelComponent] = Field(default_factory=list, description="Modelli AI rilevati")
    datasets: List[DatasetComponent] = Field(default_factory=list, description="Dataset rilevati")
    dependencies: List[DependencyComponent] = Field(default_factory=list, description="Dipendenze rilevate")
    
    # Metadati repository
    repository_url: Optional[str] = Field(None, description="URL del repository")
    repository_commit: Optional[str] = Field(None, description="Commit hash")
    scan_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp della scansione")
    
    # Metadati aggiuntivi
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati aggiuntivi")

    @field_validator("spdx_id")
    @classmethod
    def validate_spdx_id(cls, v: str) -> str:
        """Valida formato SPDX ID"""
        if not v.startswith("SPDXRef-"):
            raise ValueError("SPDX ID deve iniziare con 'SPDXRef-'")
        return v

    @field_validator("document_namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Valida formato namespace"""
        if not v.startswith("https://"):
            raise ValueError("Namespace deve essere un URL HTTPS valido")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "spdx_version": "SPDX-3.0",
                "spdx_id": "SPDXRef-DOCUMENT",
                "name": "AI-BOM Example",
                "document_namespace": "https://actproof.ai/spdx/example",
                "creator": "ActProof.ai Scanner",
                "models": [],
                "datasets": [],
                "dependencies": []
            }
        }
