"""
Utilities per interagire con repository Git
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess


class GitUtils:
    """Utilities per operazioni Git"""

    @staticmethod
    def get_repository_info(repo_path: Path) -> dict:
        """
        Ottiene informazioni sul repository Git
        
        Args:
            repo_path: Percorso del repository
        
        Returns:
            Dizionario con informazioni repository
        """
        info = {
            "url": None,
            "commit_hash": None,
            "branch": None,
            "remote_url": None,
        }

        try:
            # Verifica se è un repository Git
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return info

            # Ottieni commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                info["commit_hash"] = result.stdout.strip()

            # Ottieni branch corrente
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()

            # Ottieni remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                info["remote_url"] = result.stdout.strip()
                info["url"] = info["remote_url"]

        except Exception as e:
            print(f"Errore nell'ottenere info Git: {e}")

        return info

    @staticmethod
    def is_git_repository(path: Path) -> bool:
        """Verifica se il percorso è un repository Git"""
        git_dir = path / ".git"
        return git_dir.exists() or git_dir.is_dir()

    @staticmethod
    def get_changed_files_between_commits(
        repo_path: Path,
        base_commit: str,
        head_commit: str
    ) -> List[Dict[str, Any]]:
        """
        Ottiene lista file cambiati tra due commit

        Args:
            repo_path: Percorso repository
            base_commit: Commit base
            head_commit: Commit head

        Returns:
            Lista file cambiati con metadata
        """
        changed_files = []

        try:
            # Esegui git diff per ottenere file cambiati
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{base_commit}...{head_commit}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return changed_files

            # Parse output
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue

                status_code, file_path = parts

                # Mappa status code
                status_map = {
                    "A": "added",
                    "M": "modified",
                    "D": "deleted",
                    "R": "renamed",
                    "C": "copied",
                }
                status = status_map.get(status_code[0], "modified")

                changed_files.append({
                    "path": file_path,
                    "status": status,
                    "status_code": status_code,
                })

        except Exception as e:
            print(f"Errore nell'ottenere file cambiati: {e}")

        return changed_files


def get_changed_files(
    repo_path: Path,
    base_commit: str,
    head_commit: str
) -> List[Dict[str, Any]]:
    """
    Helper function per ottenere file cambiati tra commit

    Args:
        repo_path: Percorso repository
        base_commit: Commit base
        head_commit: Commit head

    Returns:
        Lista file cambiati
    """
    return GitUtils.get_changed_files_between_commits(repo_path, base_commit, head_commit)
