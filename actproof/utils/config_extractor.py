"""
Estrattore metadati da file di configurazione
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml
import toml


class ConfigExtractor:
    """Estrae metadati da file di configurazione comuni"""

    def __init__(self):
        self.dependencies: List[Dict[str, Any]] = []

    def extract_from_requirements_txt(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Estrae dipendenze da requirements.txt
        
        Returns:
            Lista di dipendenze con nome e versione
        """
        dependencies = []
        
        if not file_path.exists():
            return dependencies

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Pattern: package==version, package>=version, package~=version
                    match = re.match(r"^([a-zA-Z0-9_-]+[a-zA-Z0-9._-]*)([=~<>!]+)(.+)$", line)
                    if match:
                        name = match.group(1).lower()
                        version = match.group(3).split(";")[0].strip()  # Rimuove markers
                        
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "package_manager": "pip",
                            "source_file": str(file_path),
                        })
                    else:
                        # Solo nome senza versione
                        name = line.split(";")[0].split("#")[0].strip()
                        if name:
                            dependencies.append({
                                "name": name.lower(),
                                "version": None,
                                "package_manager": "pip",
                                "source_file": str(file_path),
                            })
        except Exception as e:
            print(f"Errore nell'estrazione da {file_path}: {e}")

        return dependencies

    def extract_from_package_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Estrae dipendenze da package.json
        
        Returns:
            Lista di dipendenze
        """
        dependencies = []
        
        if not file_path.exists():
            return dependencies

        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Estrai dependencies e devDependencies
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        dependencies.append({
                            "name": name.lower(),
                            "version": version if isinstance(version, str) else None,
                            "package_manager": "npm",
                            "source_file": str(file_path),
                        })
        except Exception as e:
            print(f"Errore nell'estrazione da {file_path}: {e}")

        return dependencies

    def extract_from_pyproject_toml(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Estrae dipendenze da pyproject.toml
        
        Returns:
            Lista di dipendenze
        """
        dependencies = []
        
        if not file_path.exists():
            return dependencies

        try:
            data = toml.load(file_path)
            
            # Estrai da [project.dependencies]
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    match = re.match(r"^([a-zA-Z0-9_-]+[a-zA-Z0-9._-]*)([=~<>!]+)?(.+)?$", dep)
                    if match:
                        name = match.group(1).lower()
                        version = match.group(3) if match.group(3) else None
                        
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "package_manager": "pip",
                            "source_file": str(file_path),
                        })

            # Estrai da [tool.poetry.dependencies]
            if "tool" in data and "poetry" in data["tool"]:
                if "dependencies" in data["tool"]["poetry"]:
                    for name, version in data["tool"]["poetry"]["dependencies"].items():
                        if name != "python":
                            dependencies.append({
                                "name": name.lower(),
                                "version": str(version) if version != "*" else None,
                                "package_manager": "poetry",
                                "source_file": str(file_path),
                            })
        except Exception as e:
            print(f"Errore nell'estrazione da {file_path}: {e}")

        return dependencies

    def extract_from_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Estrae dipendenze da tutti i file di configurazione nella directory
        
        Returns:
            Lista completa di dipendenze
        """
        all_dependencies = []
        
        # Cerca file di configurazione
        config_files = {
            "requirements.txt": self.extract_from_requirements_txt,
            "requirements-dev.txt": self.extract_from_requirements_txt,
            "package.json": self.extract_from_package_json,
            "pyproject.toml": self.extract_from_pyproject_toml,
        }

        for filename, extractor_func in config_files.items():
            file_path = directory / filename
            if file_path.exists():
                deps = extractor_func(file_path)
                all_dependencies.extend(deps)

        return all_dependencies

    def is_ai_related(self, package_name: str) -> bool:
        """
        Determina se un package è relativo ad AI/ML

        Args:
            package_name: Nome del package

        Returns:
            True se è AI/ML related
        """
        ai_keywords = [
            # Major AI/LLM providers
            "openai", "anthropic", "cohere", "replicate", "together",
            "groq", "fireworks", "mistralai", "google-generativeai",
            "vertexai", "bedrock", "ollama",

            # ML frameworks
            "torch", "tensorflow", "keras", "sklearn", "scikit-learn",
            "pytorch", "jax", "flax", "onnx", "xgboost", "lightgbm",
            "catboost", "prophet", "statsmodels",

            # HuggingFace ecosystem
            "transformers", "huggingface", "huggingface-hub", "datasets",
            "tokenizers", "accelerate", "peft", "trl", "evaluate",
            "sentence-transformers", "sentence_transformers",

            # LLM frameworks
            "langchain", "llama-index", "llama_index", "llamaindex",
            "haystack", "guidance", "semantic-kernel", "autogen",
            "crewai", "dspy", "instructor", "outlines", "vllm",

            # Vector databases (used with AI)
            "chromadb", "pinecone", "weaviate", "qdrant", "milvus",
            "faiss", "pgvector", "lancedb",

            # ML utilities
            "mlflow", "wandb", "neptune", "clearml", "optuna",
            "ray", "dask", "polars",

            # Data science
            "pandas", "numpy", "scipy", "matplotlib", "seaborn",
            "plotly", "bokeh", "altair",

            # Computer vision
            "opencv", "cv2", "pillow", "torchvision", "detectron2",
            "ultralytics", "yolo",

            # Audio/Speech
            "whisper", "speechrecognition", "torchaudio", "librosa",

            # NLP
            "spacy", "nltk", "gensim", "flair", "stanza",

            # Fairness/explainability
            "fairlearn", "aif360", "shap", "lime", "alibi",
            "interpret", "eli5",
        ]

        package_lower = package_name.lower().replace("-", "_").replace(".", "_")
        return any(keyword.replace("-", "_") in package_lower for keyword in ai_keywords)
