"""
Scanner principale per analisi repository Git
"""

from pathlib import Path
from typing import Optional
from actproof.bom.generator import AIBOMGenerator
from actproof.models.ai_bom import AIBOM
from actproof.models.metadata import RepositoryMetadata
from actproof.utils.git_utils import GitUtils


class RepositoryScanner:
    """Scanner principale per repository"""

    def __init__(self, repository_path: Path):
        self.repository_path = Path(repository_path)
        self.git_utils = GitUtils()

    def scan(self) -> dict:
        """
        Esegue una scansione completa del repository
        
        Returns:
            Dizionario con risultati della scansione
        """
        if not self.repository_path.exists():
            raise ValueError(f"Repository non trovato: {self.repository_path}")

        # Verifica se è un repository Git
        is_git = self.git_utils.is_git_repository(self.repository_path)
        repo_info = self.git_utils.get_repository_info(self.repository_path) if is_git else {}

        # Genera AI-BOM
        generator = AIBOMGenerator(self.repository_path)
        ai_bom = generator.generate()

        return {
            "repository_path": str(self.repository_path),
            "is_git_repository": is_git,
            "repository_info": repo_info,
            "ai_bom": ai_bom,
            "summary": {
                "models_found": len(ai_bom.models),
                "datasets_found": len(ai_bom.datasets),
                "dependencies_found": len(ai_bom.dependencies),
            },
        }

    def generate_bom(
        self, output_path: Optional[Path] = None, format: str = "json", creator: str = "ActProof.ai Scanner"
    ) -> Path:
        """
        Genera e salva l'AI-BOM
        
        Args:
            output_path: Percorso di output (None = auto-generato)
            format: Formato ("json" o "yaml")
            creator: Nome del creatore
        
        Returns:
            Percorso del file generato
        """
        generator = AIBOMGenerator(self.repository_path)
        ai_bom = generator.generate(creator=creator)

        if output_path is None:
            repo_name = self.repository_path.name or "repository"
            timestamp = ai_bom.scan_timestamp.strftime("%Y%m%d_%H%M%S")
            output_path = self.repository_path.parent / f"{repo_name}_ai-bom_{timestamp}.spdx.{format}"

        generator.save(ai_bom, output_path, format=format)
        return Path(output_path)
