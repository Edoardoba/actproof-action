"""
Generatore AI-BOM conforme a SPDX 3.0
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from actproof.models.ai_bom import (
    AIBOM,
    ModelComponent,
    DatasetComponent,
    DependencyComponent,
    DetectionLocation,
    ModelType,
    DatasetType,
    LicenseType,
)
from actproof.models.metadata import RepositoryMetadata
from actproof.parser.detector import AIDetector
from actproof.utils.config_extractor import ConfigExtractor
from actproof.utils.git_utils import GitUtils


class AIBOMGenerator:
    """Generatore di AI-BOM in formato SPDX 3.0"""

    def __init__(self, repository_path: Path):
        self.repository_path = Path(repository_path)
        self.detector = AIDetector(repository_root=self.repository_path)
        self.config_extractor = ConfigExtractor()
        self.git_utils = GitUtils()

    def generate(self, creator: str = "ActProof.ai Scanner") -> AIBOM:
        """
        Genera un AI-BOM completo dal repository
        
        Args:
            creator: Nome del creatore del documento
        
        Returns:
            Oggetto AIBOM validato
        """
        # Ottieni metadati repository
        repo_info = self.git_utils.get_repository_info(self.repository_path)
        
        # Scansiona codice per componenti AI
        scan_results = self.detector.scan_directory(self.repository_path)
        
        # Estrai dipendenze da file di configurazione
        dependencies_config = self.config_extractor.extract_from_directory(self.repository_path)
        
        # Costruisci componenti modello
        models = self._extract_models(scan_results)
        
        # Costruisci componenti dataset
        datasets = self._extract_datasets(scan_results)
        
        # Costruisci componenti dipendenza
        dependencies = self._extract_dependencies(scan_results, dependencies_config)
        
        # Genera ID univoci
        spdx_id = f"SPDXRef-DOCUMENT-{uuid.uuid4().hex[:8]}"
        namespace = f"https://actproof.ai/spdx/{uuid.uuid4()}"
        
        # Crea AI-BOM
        ai_bom = AIBOM(
            spdx_id=spdx_id,
            name=f"AI-BOM for {self.repository_path.name}",
            document_namespace=namespace,
            creator=creator,
            repository_url=repo_info.get("url"),
            repository_commit=repo_info.get("commit_hash"),
            models=models,
            datasets=datasets,
            dependencies=dependencies,
            metadata={
                "scan_results": {
                    "files_scanned": scan_results["files_scanned"],
                    "total_detections": len(scan_results["detections"]),
                },
                "repository_branch": repo_info.get("branch"),
            },
        )
        
        return ai_bom

    def _create_detection_location(self, detection: Dict[str, Any], detection_type: str) -> Optional[DetectionLocation]:
        """
        Create a DetectionLocation from a detection dict.

        Args:
            detection: Detection dictionary from the detector
            detection_type: Type of detection for display

        Returns:
            DetectionLocation object or None if location info missing
        """
        location = detection.get("location", {})
        if not location:
            # Fallback for legacy detections without location info
            return None

        try:
            return DetectionLocation(
                file_path=location.get("file_path", detection.get("relative_path", detection.get("file", "unknown"))),
                line_number=location.get("line_number", 1),
                column=location.get("column"),
                end_line=location.get("end_line"),
                end_column=location.get("end_column"),
                code_snippet=location.get("code_snippet"),
                detection_type=detection_type,
                confidence=1.0,
            )
        except Exception:
            return None

    def _extract_models(self, scan_results: Dict[str, Any]) -> List[ModelComponent]:
        """
        Estrae componenti modello dalle scansioni.

        Handles:
        - AI API clients (OpenAI, Anthropic, LangChain)
        - HuggingFace models (from_pretrained with strings or variables)
        - Sklearn models
        - Custom models
        """
        import re
        models = []
        seen_models = set()
        # Store detection locations for each model key
        model_locations: Dict[str, List[DetectionLocation]] = {}

        # Track files with from_pretrained calls to search for model names
        files_with_pretrained = set()

        # Da rilevamenti di client AI
        for detection in scan_results.get("ai_clients", []):
            match = detection.get("match", {})
            file_path = detection.get("file", "")
            query_type = detection.get("query_type", "")

            # Determina provider dal tipo di query
            provider = None
            model_type = ModelType.LLM

            if "openai" in query_type.lower():
                provider = "OpenAI"
            elif "anthropic" in query_type.lower():
                provider = "Anthropic"
            elif "langchain" in query_type.lower():
                provider = "LangChain"
                # Extract class name for more specific identification
                class_name = match.get("text", "")
                if "Chat" in class_name:
                    provider = f"LangChain ({class_name})"

            if provider:
                model_key = f"{provider}:{file_path}"
                # Create detection location
                location = self._create_detection_location(detection, f"{provider.lower()}_client")
                locations = [location] if location else []

                if model_key not in seen_models:
                    models.append(ModelComponent(
                        name=f"{provider} API Client",
                        model_type=model_type,
                        provider=provider.split(" (")[0],  # Remove class name for provider field
                        detected_in=[file_path],
                        detection_locations=locations,
                        usage_context="api_call",
                    ))
                    seen_models.add(model_key)

        # Da rilevamenti di chiamate modello
        for detection in scan_results.get("models", []):
            match = detection.get("match", {})
            file_path = detection.get("file", "")
            match_text = match.get("text", "")
            query_type = detection.get("query_type", "")

            # Create detection location for this detection
            det_location = self._create_detection_location(detection, query_type)
            locations = [det_location] if det_location else []

            # Handle HuggingFace model with direct string
            if query_type == "huggingface_model":
                if match.get("type") == "model_name":
                    model_name = match.get("text", "").strip('"\'')
                    if model_name:
                        model_key = f"hf:{model_name}:{file_path}"
                        if model_key not in seen_models:
                            models.append(ModelComponent(
                                name=model_name,
                                model_type=self._infer_model_type(model_name),
                                provider="HuggingFace",
                                source_location=f"https://huggingface.co/{model_name}",
                                detected_in=[file_path],
                                detection_locations=locations,
                                usage_context="inference",
                            ))
                            seen_models.add(model_key)
                        continue

            # Handle from_pretrained with any argument (including variables)
            if query_type in ["from_pretrained_any", "huggingface_auto_classes"]:
                files_with_pretrained.add(file_path)
                # Try to extract class name
                class_name = match.get("text", "")
                obj_name = None
                if "AutoModel" in class_name or "AutoTokenizer" in class_name:
                    # Extract the Auto class name
                    auto_match = re.search(r'(Auto\w+)', class_name)
                    if auto_match:
                        obj_name = auto_match.group(1)

                # Try to find model name in the file
                model_name = self._find_model_name_in_file(file_path)
                if model_name:
                    model_key = f"hf:{model_name}:{file_path}"
                    if model_key not in seen_models:
                        models.append(ModelComponent(
                            name=model_name,
                            model_type=self._infer_model_type(model_name),
                            provider="HuggingFace",
                            source_location=f"https://huggingface.co/{model_name}",
                            detected_in=[file_path],
                            detection_locations=locations,
                            usage_context="inference",
                        ))
                        seen_models.add(model_key)
                else:
                    # Could not find model name, but we know HF is used
                    model_key = f"hf_unknown:{file_path}"
                    if model_key not in seen_models:
                        models.append(ModelComponent(
                            name=f"HuggingFace Model ({obj_name or 'from_pretrained'})",
                            model_type=ModelType.CUSTOM,
                            provider="HuggingFace",
                            detected_in=[file_path],
                            detection_locations=locations,
                            usage_context="inference",
                        ))
                        seen_models.add(model_key)
                continue

            # Handle sklearn models
            if query_type == "sklearn_model":
                class_name = match.get("text", "Unknown")
                # Clean up the class name
                sklearn_match = re.search(r'(\w+(?:Classifier|Regressor|Clustering|Forest|Boost|SVC?|SVR?|KMeans|PCA|Scaler))', class_name)
                if sklearn_match:
                    class_name = sklearn_match.group(1)

                model_key = f"sklearn:{class_name}:{file_path}"
                if model_key not in seen_models:
                    models.append(ModelComponent(
                        name=f"sklearn.{class_name}",
                        model_type=ModelType.CUSTOM,
                        provider="scikit-learn",
                        detected_in=[file_path],
                        detection_locations=locations,
                        usage_context="training" if "fit" in match_text.lower() else "inference",
                    ))
                    seen_models.add(model_key)
                continue

            # Handle training calls
            if query_type == "training":
                model_key = f"training:{file_path}"
                if model_key not in seen_models:
                    models.append(ModelComponent(
                        name="Custom Training Model",
                        model_type=ModelType.CUSTOM,
                        detected_in=[file_path],
                        detection_locations=locations,
                        usage_context="training",
                    ))
                    seen_models.add(model_key)
                continue

            # Fallback: search for model patterns in match text
            match_text_lower = match_text.lower()
            hf_match = re.search(r'from_pretrained\s*\(["\']([^"\']+)["\']', match_text_lower)
            if hf_match:
                model_name = hf_match.group(1)
                model_key = f"hf:{model_name}:{file_path}"
                if model_key not in seen_models:
                    models.append(ModelComponent(
                        name=model_name,
                        model_type=self._infer_model_type(model_name),
                        provider="HuggingFace",
                        source_location=f"https://huggingface.co/{model_name}",
                        detected_in=[file_path],
                        detection_locations=locations,
                        usage_context="inference",
                    ))
                    seen_models.add(model_key)
            elif "model" in match_text_lower or "predict" in match_text_lower:
                model_key = f"model:{file_path}"
                if model_key not in seen_models:
                    models.append(ModelComponent(
                        name="Custom Model",
                        model_type=ModelType.CUSTOM,
                        detected_in=[file_path],
                        detection_locations=locations,
                        usage_context="inference",
                    ))
                    seen_models.add(model_key)

        return models

    def _infer_model_type(self, model_name: str) -> ModelType:
        """Infer model type from model name"""
        model_name_lower = model_name.lower()

        # LLM models
        if any(x in model_name_lower for x in ["bert", "gpt", "llama", "mistral", "falcon", "gemma", "phi", "qwen", "t5", "bart", "roberta"]):
            return ModelType.LLM

        # Vision models
        if any(x in model_name_lower for x in ["vit", "resnet", "clip", "dino", "sam", "yolo", "detr"]):
            return ModelType.VISION

        # Embedding models
        if any(x in model_name_lower for x in ["embed", "sentence-transformer", "all-minilm", "bge", "e5"]):
            return ModelType.EMBEDDING

        return ModelType.CUSTOM

    def _find_model_name_in_file(self, file_path: str) -> Optional[str]:
        """
        Search file for model name string that might be used with from_pretrained.
        Looks for patterns like:
        - MODEL_NAME = "bert-base-uncased"
        - model_id = 'facebook/bart-large'
        """
        import re

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Common patterns for model name variables
            patterns = [
                # Variable assignment with model name
                r'(?:MODEL_NAME|model_name|model_id|MODEL_ID|model|checkpoint|CHECKPOINT)\s*=\s*["\']([^"\']+/[^"\']+)["\']',
                r'(?:MODEL_NAME|model_name|model_id|MODEL_ID|model|checkpoint|CHECKPOINT)\s*=\s*["\']([a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+)["\']',
                # HuggingFace style model names (org/model or model-name)
                r'from_pretrained\s*\(\s*["\']([^"\']+)["\']',
                # Pipeline with model
                r'pipeline\s*\([^,]+,\s*model\s*=\s*["\']([^"\']+)["\']',
                r'pipeline\s*\([^,]+,\s*["\']([^"\']+/[^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Return the first valid model name
                    for match in matches:
                        # Filter out common non-model strings
                        if not any(x in match.lower() for x in ["http://", "https://", ".csv", ".json", ".txt", "path", "file"]):
                            return match

            return None
        except Exception:
            return None

    def _extract_datasets(self, scan_results: Dict[str, Any]) -> List[DatasetComponent]:
        """Estrae componenti dataset dalle scansioni"""
        datasets = []
        seen_datasets = set()

        # Raggruppa detections per file per trovare dataset_name associato a load_dataset
        datasets_by_file = {}
        for detection in scan_results.get("datasets", []):
            file_path = detection.get("file", "")
            if file_path not in datasets_by_file:
                datasets_by_file[file_path] = []
            datasets_by_file[file_path].append(detection)

        for file_path, detections in datasets_by_file.items():
            dataset_name = None
            primary_detection = None

            # Cerca capture "dataset_name" nei match
            for detection in detections:
                match = detection.get("match", {})
                match_type = match.get("type", "")

                if match_type == "dataset_name":
                    dataset_name = match.get("text", "").strip('"\'')
                    primary_detection = detection
                    break

            # Fallback: regex sul file se non trovato
            if not dataset_name:
                import re
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = re.findall(r'load_dataset\s*\(["\']([^"\']+)["\']', content)
                    if matches:
                        dataset_name = matches[0]
                except:
                    pass

            if dataset_name:
                dataset_key = f"dataset:{dataset_name}:{file_path}"
                if dataset_key not in seen_datasets:
                    # Create detection location from the first detection in this file
                    location = None
                    if primary_detection:
                        location = self._create_detection_location(primary_detection, "dataset_load")
                    elif detections:
                        location = self._create_detection_location(detections[0], "dataset_load")
                    locations = [location] if location else []

                    datasets.append(DatasetComponent(
                        name=dataset_name,
                        dataset_type=DatasetType.TRAINING,
                        detected_in=[file_path],
                        detection_locations=locations,
                    ))
                    seen_datasets.add(dataset_key)

        return datasets

    def _extract_dependencies(
        self, scan_results: Dict[str, Any], config_dependencies: List[Dict[str, Any]]
    ) -> List[DependencyComponent]:
        """Estrae componenti dipendenza"""
        dependencies = []
        seen_deps = set()
        
        # Da file di configurazione
        for dep in config_dependencies:
            name = dep.get("name", "")
            if name and name not in seen_deps:
                is_ai_related = self.config_extractor.is_ai_related(name)
                
                dependencies.append(DependencyComponent(
                    name=name,
                    version=dep.get("version"),
                    package_manager=dep.get("package_manager"),
                    is_ai_related=is_ai_related,
                    detected_in=[dep.get("source_file", "")],
                ))
                seen_deps.add(name)
        
        # Da import nel codice
        for detection in scan_results.get("ml_libraries", []):
            match = detection.get("match", {})
            file_path = detection.get("file", "")
            
            # Estrai nome libreria dal match
            match_text = match.get("text", "")
            # Pattern semplice per estrarre nome libreria
            import re
            lib_match = re.search(r"import\s+([a-zA-Z0-9_]+)", match_text)
            if lib_match:
                lib_name = lib_match.group(1).lower()
                if lib_name not in seen_deps:
                    dependencies.append(DependencyComponent(
                        name=lib_name,
                        is_ai_related=True,
                        detected_in=[file_path],
                    ))
                    seen_deps.add(lib_name)
        
        return dependencies

    def save(self, ai_bom: AIBOM, output_path: Path, format: str = "json") -> None:
        """
        Salva l'AI-BOM su file
        
        Args:
            ai_bom: Oggetto AIBOM
            output_path: Percorso di output
            format: Formato ("json" o "yaml")
        """
        output_path = Path(output_path)
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(ai_bom.model_dump(mode="json", exclude_none=True), f, indent=2, default=str)
        elif format == "yaml":
            import yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(ai_bom.model_dump(mode="json", exclude_none=True), f, default_flow_style=False, default=str)
        else:
            raise ValueError(f"Formato non supportato: {format}")
