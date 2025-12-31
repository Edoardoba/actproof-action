"""
Parser Tree-sitter per analisi statica del codice
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from actproof.config import get_settings

logger = logging.getLogger(__name__)


class CodeParser:
    """Parser per analisi codice con Tree-sitter"""

    def __init__(self):
        self.parsers: Dict[str, Parser] = {}
        self._init_parsers()

    def _init_parsers(self):
        """Inizializza i parser per i linguaggi supportati"""
        self.languages = {}
        
        # Python
        try:
            python_language = Language(tspython.language())
            # Prova con costruttore che accetta language
            python_parser = Parser(python_language)
            self.parsers["python"] = python_parser
            self.languages["python"] = python_language
        except (TypeError, AttributeError) as e:
            # Fallback: prova a impostare language come attributo
            try:
                python_language = Language(tspython.language())
                python_parser = Parser()
                python_parser.language = python_language
                self.parsers["python"] = python_parser
                self.languages["python"] = python_language
            except Exception as e2:
                print(f"Warning: Impossibile inizializzare parser Python: {e2}")
                # Continua senza parser Python

        # JavaScript/TypeScript
        try:
            js_language = Language(tsjavascript.language())
            js_parser = Parser(js_language)
            self.parsers["javascript"] = js_parser
            self.parsers["typescript"] = js_parser  # Usa lo stesso parser
            self.languages["javascript"] = js_language
            self.languages["typescript"] = js_language
        except (TypeError, AttributeError) as e:
            # Fallback: prova a impostare language come attributo
            try:
                js_language = Language(tsjavascript.language())
                js_parser = Parser()
                js_parser.language = js_language
                self.parsers["javascript"] = js_parser
                self.parsers["typescript"] = js_parser
                self.languages["javascript"] = js_language
                self.languages["typescript"] = js_language
            except Exception as e2:
                print(f"Warning: Impossibile inizializzare parser JavaScript: {e2}")
                # Continua senza parser JavaScript

    def parse_file(self, file_path: Path, language: Optional[str] = None) -> Optional[Any]:
        """
        Parse un file e restituisce l'AST
        
        Args:
            file_path: Percorso del file
            language: Linguaggio (auto-detect se None)
        
        Returns:
            AST tree o None se parsing fallisce
        """
        if not file_path.exists():
            return None

        # Auto-detect language se non specificato
        if language is None:
            language = self._detect_language(file_path)
            if language is None:
                return None

        if language not in self.parsers:
            return None

        try:
            # Safety check: verify file size before reading
            settings = get_settings()
            max_file_size_bytes = settings.max_file_size_mb * 1024 * 1024
            
            try:
                file_size = file_path.stat().st_size
                if file_size > max_file_size_bytes:
                    logger.warning(
                        f"File too large to parse: {file_path} "
                        f"({file_size / (1024*1024):.2f} MB > {settings.max_file_size_mb} MB)"
                    )
                    return None
            except (OSError, PermissionError):
                # If we can't check size, try to read anyway but be cautious
                pass
            
            with open(file_path, "rb") as f:
                source_code = f.read()
            
            # Additional safety check after reading
            if len(source_code) > max_file_size_bytes:
                logger.warning(
                    f"File content too large after reading: {file_path} "
                    f"({len(source_code) / (1024*1024):.2f} MB)"
                )
                return None
            
            parser = self.parsers[language]
            tree = parser.parse(source_code)
            return tree
        except MemoryError as e:
            logger.error(f"Out of memory while parsing {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Errore nel parsing di {file_path}: {e}")
            return None

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Rileva il linguaggio dal nome del file"""
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        return language_map.get(ext)

    def query_file(
        self, file_path: Path, query_string: str, language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Esegue una query Tree-sitter su un file
        
        Args:
            file_path: Percorso del file
            query_string: Query Tree-sitter (S-expression)
            language: Linguaggio (auto-detect se None)
        
        Returns:
            Lista di match della query
        """
        tree = self.parse_file(file_path, language)
        if tree is None:
            return []

        if language is None:
            language = self._detect_language(file_path)
            if language is None:
                return []

        if language not in self.parsers:
            return []

        try:
            from tree_sitter import Query, QueryCursor

            parser = self.parsers[language]
            language_obj = self.languages.get(language)
            if language_obj is None:
                return []
            
            # Crea query
            query = Query(language_obj, query_string)
            
            # Usa QueryCursor per eseguire la query
            cursor = QueryCursor(query)
            
            # Esegui query sul root node
            matches = cursor.matches(tree.root_node)

            results = []
            # matches restituisce una lista di tuple (pattern_index, captures_dict)
            for match in matches:
                pattern_index, captures_dict = match
                # captures_dict è un dizionario {capture_name: [nodes]}
                for capture_name, nodes in captures_dict.items():
                    for node in nodes:
                        results.append({
                            "type": capture_name,
                            "text": node.text.decode("utf-8") if hasattr(node.text, "decode") else str(node.text),
                            "start_point": node.start_point,
                            "end_point": node.end_point,
                            "file": str(file_path),
                        })

            return results
        except Exception as e:
            print(f"Errore nella query su {file_path}: {e}")
            return []
