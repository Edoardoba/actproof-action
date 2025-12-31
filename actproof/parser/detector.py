"""
Detector per identificare componenti AI nel codice
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from actproof.parser.code_parser import CodeParser
from actproof.queries.python_queries import PYTHON_QUERIES
from actproof.queries.javascript_queries import JAVASCRIPT_QUERIES
from actproof.config import get_settings

logger = logging.getLogger(__name__)


class AIDetector:
    """Detector per componenti AI, ML e dataset"""

    def __init__(self, repository_root: Optional[Path] = None):
        self.parser = CodeParser()
        self.detections: List[Dict[str, Any]] = []
        self.settings = get_settings()
        self.skipped_files = []
        self.repository_root = repository_root
        self._file_cache: Dict[str, List[str]] = {}

    def _get_file_lines(self, file_path: Path) -> List[str]:
        """Cache and return file lines for snippet extraction"""
        file_key = str(file_path)
        if file_key not in self._file_cache:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    self._file_cache[file_key] = f.readlines()
            except Exception:
                self._file_cache[file_key] = []
        return self._file_cache[file_key]

    def _get_code_snippet(self, file_path: Path, start_line: int, end_line: int, context: int = 1) -> str:
        """
        Extract code snippet around the detection.

        Args:
            file_path: Path to the file
            start_line: Starting line number (0-indexed)
            end_line: Ending line number (0-indexed)
            context: Number of context lines before/after

        Returns:
            Code snippet as string
        """
        lines = self._get_file_lines(file_path)
        if not lines:
            return ""

        # Calculate range with context
        snippet_start = max(0, start_line - context)
        snippet_end = min(len(lines), end_line + context + 1)

        snippet_lines = lines[snippet_start:snippet_end]
        return "".join(snippet_lines).strip()

    def _get_relative_path(self, file_path: Path) -> str:
        """Get path relative to repository root"""
        if self.repository_root:
            try:
                return str(file_path.relative_to(self.repository_root))
            except ValueError:
                pass
        return str(file_path)

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Scansiona un file per componenti AI

        Args:
            file_path: Percorso del file

        Returns:
            Lista di rilevamenti with location information
        """
        detections = []
        language = self.parser._detect_language(file_path)

        if language == "python":
            queries = PYTHON_QUERIES
        elif language in ["javascript", "typescript"]:
            queries = JAVASCRIPT_QUERIES
        else:
            return detections

        relative_path = self._get_relative_path(file_path)

        for query_name, query_string in queries.items():
            matches = self.parser.query_file(file_path, query_string, language)
            for match in matches:
                # Extract location info from tree-sitter match
                start_point = match.get("start_point", (0, 0))
                end_point = match.get("end_point", (0, 0))

                # tree-sitter uses 0-indexed lines, convert to 1-indexed
                line_number = start_point[0] + 1 if isinstance(start_point, tuple) else 1
                column = start_point[1] if isinstance(start_point, tuple) else 0
                end_line = end_point[0] + 1 if isinstance(end_point, tuple) else line_number
                end_column = end_point[1] if isinstance(end_point, tuple) else 0

                # Get code snippet
                code_snippet = self._get_code_snippet(
                    file_path,
                    start_point[0] if isinstance(start_point, tuple) else 0,
                    end_point[0] if isinstance(end_point, tuple) else 0
                )

                detection = {
                    "file": str(file_path),
                    "relative_path": relative_path,
                    "query_type": query_name,
                    "language": language,
                    "match": match,
                    # Location information
                    "location": {
                        "file_path": relative_path,
                        "line_number": line_number,
                        "column": column,
                        "end_line": end_line,
                        "end_column": end_column,
                        "code_snippet": code_snippet[:500] if code_snippet else None,  # Limit snippet size
                    }
                }
                detections.append(detection)
                self.detections.append(detection)

        return detections

    def scan_directory(self, directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scansiona una directory ricorsivamente

        Args:
            directory: Directory da scansionare
            extensions: Estensioni file da includere (None = tutte supportate)

        Returns:
            Dizionario con risultati della scansione
        """
        if extensions is None:
            extensions = [".py", ".js", ".jsx", ".ts", ".tsx"]

        # Set repository root for relative path calculation
        if self.repository_root is None:
            self.repository_root = directory

        results = {
            "models": [],
            "datasets": [],
            "ai_clients": [],
            "ml_libraries": [],
            "files_scanned": 0,
            "detections": [],
        }

        max_file_size_bytes = self.settings.max_file_size_mb * 1024 * 1024

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    file_size = file_path.stat().st_size
                    
                    # Skip file troppo grandi
                    if file_size > max_file_size_bytes:
                        self.skipped_files.append({
                            "path": str(file_path.relative_to(directory)),
                            "size_mb": file_size / (1024 * 1024)
                        })
                        logger.debug(
                            f"Skipping large file: {file_path.relative_to(directory)} "
                            f"({file_size / (1024*1024):.2f} MB > {self.settings.max_file_size_mb} MB)"
                        )
                        continue
                    
                    detections = self.scan_file(file_path)
                    results["files_scanned"] += 1
                    results["detections"].extend(detections)
                except (OSError, PermissionError) as e:
                    # Skip files that can't be accessed
                    logger.debug(f"Could not scan file {file_path}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error scanning file {file_path}: {e}")
                    continue
        
        # Add skipped files info to results
        if self.skipped_files:
            results["skipped_files"] = self.skipped_files
            results["skipped_files_count"] = len(self.skipped_files)
            logger.info(f"Skipped {len(self.skipped_files)} large file(s) during scanning")

        # Categorizza i rilevamenti
        for detection in results["detections"]:
            query_type = detection["query_type"]

            # AI API Clients
            if query_type in ["openai_client", "anthropic_client", "ai_api_call", "langchain"]:
                results["ai_clients"].append(detection)
            # ML/AI Library Imports
            elif query_type in ["ml_library_import", "ai_library_import", "ai_library_require", "ai_from_import"]:
                results["ml_libraries"].append(detection)
            # Model Detection (expanded to catch more patterns)
            elif query_type in [
                "model_call",
                "huggingface_model",
                "from_pretrained_any",
                "huggingface_auto_classes",
                "huggingface_pipeline",
                "sklearn_model",
                "training"
            ]:
                results["models"].append(detection)
            # Dataset Detection
            elif query_type in ["dataset_load", "pandas_data", "torch_dataloader"]:
                results["datasets"].append(detection)

        return results
