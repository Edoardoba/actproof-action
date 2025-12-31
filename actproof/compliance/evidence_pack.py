"""
Evidence Pack Generator
Genera ZIP scaricabile con tutti gli artefatti per audit compliance
"""

import json
import hashlib
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from actproof.compliance.requirements import ComplianceResult
from actproof.models.ai_bom import AIBOM
from actproof.storage.base import StorageBackend


class EvidenceManifest(BaseModel):
    """Manifest per Evidence Pack (obbligatorio, versionato)"""

    # Schema version
    schema_version: str = Field(default="1.0.0", description="Versione schema manifest")

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp generazione")
    repo_id: str = Field(..., description="ID repository")
    commit: Optional[str] = Field(None, description="Commit SHA")
    scan_run_id: Optional[str] = Field(None, description="ID scan run")

    # Contenuto pack
    files: List[Dict[str, str]] = Field(default_factory=list, description="Lista file nel pack con hash")

    # Integrità
    root_hash: str = Field(default="", description="Hash radice del pack")
    audit_trail_ref: Optional[str] = Field(None, description="Riferimento audit trail")

    def compute_root_hash(self) -> str:
        """Calcola hash radice basato sui file inclusi"""
        if not self.files:
            return ""

        # Concatena hash di tutti i file ordinati
        file_hashes = sorted([f["hash"] for f in self.files])
        combined = "".join(file_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()

    def model_post_init(self, __context):
        """Calcola root hash dopo inizializzazione"""
        if not self.root_hash and self.files:
            self.root_hash = self.compute_root_hash()


class EvidencePackGenerator:
    """
    Generator per Evidence Pack
    Crea ZIP con tutti gli artefatti necessari per audit
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """
        Inizializza generator

        Args:
            storage: Storage backend per salvare pack (opzionale)
        """
        self.storage = storage

    def generate_pack(
        self,
        repo_id: str,
        ai_bom: Optional[AIBOM] = None,
        compliance_result: Optional[ComplianceResult] = None,
        scan_run_id: Optional[str] = None,
        commit: Optional[str] = None,
        rag_queries: Optional[List[Dict[str, Any]]] = None,
        fairness_results: Optional[Dict[str, Any]] = None,
        include_reports: bool = True,
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Genera Evidence Pack completo

        Args:
            repo_id: ID repository
            ai_bom: AI-BOM
            compliance_result: Risultato compliance
            scan_run_id: ID scan run
            commit: Commit SHA
            rag_queries: Query RAG eseguite
            fairness_results: Risultati fairness audit
            include_reports: Include report PDF/DOCX
            output_path: Percorso output ZIP (opzionale)

        Returns:
            Dict con informazioni sul pack generato
        """
        # Crea directory temporanea
        temp_dir = Path(tempfile.mkdtemp(prefix="evidence_pack_"))

        try:
            # Prepara contenuto pack
            pack_files = []

            # 1. README.txt
            readme_content = self._generate_readme(repo_id, commit, scan_run_id)
            readme_path = temp_dir / "README.txt"
            readme_path.write_text(readme_content)
            pack_files.append({
                "filename": "README.txt",
                "path": "README.txt",
                "hash": self._hash_file(readme_path),
            })

            # 2. AI-BOM (SPDX JSON)
            if ai_bom:
                bom_content = json.dumps(ai_bom.model_dump(mode="json"), indent=2)
                bom_path = temp_dir / "ai-bom" / "spdx.json"
                bom_path.parent.mkdir(parents=True, exist_ok=True)
                bom_path.write_text(bom_content)
                pack_files.append({
                    "filename": "ai-bom/spdx.json",
                    "path": "ai-bom/spdx.json",
                    "hash": self._hash_file(bom_path),
                })

            # 3. Policy Results
            if compliance_result:
                policy_content = json.dumps(compliance_result.model_dump(mode="json"), indent=2)
                policy_path = temp_dir / "policy" / "policy_results.json"
                policy_path.parent.mkdir(parents=True, exist_ok=True)
                policy_path.write_text(policy_content)
                pack_files.append({
                    "filename": "policy/policy_results.json",
                    "path": "policy/policy_results.json",
                    "hash": self._hash_file(policy_path),
                })

                # Gaps separati
                gaps_data = {
                    "critical_gaps": compliance_result.requirements_check.critical_gaps,
                    "recommendations": compliance_result.requirements_check.recommendations,
                    "compliance_score": compliance_result.requirements_check.compliance_score,
                }
                gaps_content = json.dumps(gaps_data, indent=2)
                gaps_path = temp_dir / "policy" / "gaps.json"
                gaps_path.write_text(gaps_content)
                pack_files.append({
                    "filename": "policy/gaps.json",
                    "path": "policy/gaps.json",
                    "hash": self._hash_file(gaps_path),
                })

            # 4. Evidence Index
            evidence_index = self._generate_evidence_index(ai_bom, compliance_result, commit)
            evidence_path = temp_dir / "evidence" / "evidence_index.json"
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence_index, indent=2))
            pack_files.append({
                "filename": "evidence/evidence_index.json",
                "path": "evidence/evidence_index.json",
                "hash": self._hash_file(evidence_path),
            })

            # 5. RAG Queries
            if rag_queries:
                rag_content = json.dumps(rag_queries, indent=2)
                rag_path = temp_dir / "rag" / "rag_queries.json"
                rag_path.parent.mkdir(parents=True, exist_ok=True)
                rag_path.write_text(rag_content)
                pack_files.append({
                    "filename": "rag/rag_queries.json",
                    "path": "rag/rag_queries.json",
                    "hash": self._hash_file(rag_path),
                })

            # 6. Fairness Results
            if fairness_results:
                fairness_content = json.dumps(fairness_results, indent=2)
                fairness_path = temp_dir / "fairness" / "fairness_results.json"
                fairness_path.parent.mkdir(parents=True, exist_ok=True)
                fairness_path.write_text(fairness_content)
                pack_files.append({
                    "filename": "fairness/fairness_results.json",
                    "path": "fairness/fairness_results.json",
                    "hash": self._hash_file(fairness_path),
                })

            # 7. Manifest
            manifest = EvidenceManifest(
                repo_id=repo_id,
                commit=commit,
                scan_run_id=scan_run_id,
                files=pack_files,
            )
            manifest.root_hash = manifest.compute_root_hash()

            manifest_content = json.dumps(manifest.model_dump(mode="json"), indent=2)
            manifest_path = temp_dir / "manifest.json"
            manifest_path.write_text(manifest_content)

            # Crea ZIP
            if output_path is None:
                output_path = Path(tempfile.gettempdir()) / f"evidence_pack_{repo_id}_{commit or scan_run_id}.zip"

            self._create_zip(temp_dir, output_path)

            # Salva in storage se disponibile
            storage_key = None
            download_url = None
            if self.storage:
                storage_key = f"{repo_id}/evidence-packs/{commit or scan_run_id}.zip"
                with open(output_path, "rb") as f:
                    zip_data = f.read()
                self.storage.save_file(storage_key, zip_data, content_type="application/zip")

                # Salva anche manifest separatamente
                manifest_key = f"{repo_id}/evidence-packs/{commit or scan_run_id}_manifest.json"
                self.storage.save_json(manifest_key, manifest.model_dump(mode="json"))

                download_url = self.storage.get_download_url(storage_key)

            return {
                "pack_id": f"{repo_id}_{commit or scan_run_id}",
                "output_path": str(output_path),
                "storage_key": storage_key,
                "download_url": download_url,
                "manifest": manifest.model_dump(mode="json"),
                "file_count": len(pack_files) + 1,  # +1 for manifest
                "root_hash": manifest.root_hash,
            }

        finally:
            # Cleanup temp directory
            # In produzione, potresti voler mantenere per debug
            pass

    def _generate_readme(self, repo_id: str, commit: Optional[str], scan_run_id: Optional[str]) -> str:
        """Genera README.txt per il pack"""
        return f"""ActProof.ai Evidence Pack
============================

Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Repository ID: {repo_id}
Commit: {commit or 'N/A'}
Scan Run ID: {scan_run_id or 'N/A'}

CONTENTS
--------
This Evidence Pack contains all artifacts necessary for EU AI Act compliance audit:

1. /manifest.json              - Pack manifest with file inventory and integrity hashes
2. /README.txt                 - This file
3. /ai-bom/spdx.json          - AI Bill of Materials (SPDX 3.0 format)
4. /policy/policy_results.json - Compliance evaluation results
5. /policy/gaps.json          - Critical gaps and recommendations
6. /evidence/evidence_index.json - Evidence index with file references
7. /rag/rag_queries.json      - RAG queries executed (if applicable)
8. /fairness/fairness_results.json - Fairness audit results (if applicable)
9. /reports/                  - Generated reports (PDF/DOCX, if requested)

INTEGRITY VERIFICATION
-----------------------
1. Verify manifest.json root_hash matches combined hash of all files
2. Each file entry in manifest includes SHA-256 hash
3. To verify a file: sha256sum <filename> and compare with manifest

INTERPRETING RESULTS
--------------------
- compliance_score: 0.0 to 1.0 (1.0 = fully compliant)
- risk_level: minimal, limited, high, or prohibited
- critical_gaps: Issues that MUST be resolved for compliance
- recommendations: Suggested improvements

For questions or support, contact: support@actproof.ai
"""

    def _generate_evidence_index(
        self,
        ai_bom: Optional[AIBOM],
        compliance_result: Optional[ComplianceResult],
        commit: Optional[str]
    ) -> Dict[str, Any]:
        """Genera evidence index con riferimenti a regole/articoli"""
        index = {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "commit": commit,
            "files": [],
            "compliance_mappings": [],
        }

        # File evidences
        if ai_bom:
            for model in ai_bom.models:
                index["files"].append({
                    "type": "model",
                    "name": model.name,
                    "provider": model.provider,
                    "version": model.version,
                    "hash": None,  # In produzione, calcola hash del modello
                })

            for dataset in ai_bom.datasets:
                index["files"].append({
                    "type": "dataset",
                    "name": dataset.name,
                    "hash": None,
                })

        # Compliance mappings
        if compliance_result:
            req = compliance_result.requirements_check

            articles = [
                ("Article 11", "article_11_compliant"),
                ("Article 13", "article_13_compliant"),
                ("Article 14", "article_14_compliant"),
                ("Article 15", "article_15_compliant"),
            ]

            for article_name, field_name in articles:
                compliant = getattr(req, field_name, False)
                index["compliance_mappings"].append({
                    "article": article_name,
                    "compliant": compliant,
                    "evidence_files": ["ai-bom/spdx.json", "policy/policy_results.json"],
                })

        return index

    def _hash_file(self, file_path: Path) -> str:
        """Calcola SHA-256 hash di un file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _create_zip(self, source_dir: Path, output_path: Path):
        """Crea ZIP da directory"""
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

    def verify_pack_integrity(self, pack_path: Path) -> Dict[str, Any]:
        """
        Verifica integrità di un Evidence Pack

        Args:
            pack_path: Percorso al file ZIP

        Returns:
            Dict con risultati verifica
        """
        with zipfile.ZipFile(pack_path, "r") as zipf:
            # Leggi manifest
            manifest_data = json.loads(zipf.read("manifest.json"))
            manifest = EvidenceManifest(**manifest_data)

            # Verifica hash di ogni file
            mismatches = []
            for file_info in manifest.files:
                file_content = zipf.read(file_info["filename"])
                computed_hash = hashlib.sha256(file_content).hexdigest()

                if computed_hash != file_info["hash"]:
                    mismatches.append({
                        "filename": file_info["filename"],
                        "expected_hash": file_info["hash"],
                        "computed_hash": computed_hash,
                    })

            # Verifica root hash
            file_hashes = sorted([f["hash"] for f in manifest.files])
            combined = "".join(file_hashes)
            computed_root_hash = hashlib.sha256(combined.encode()).hexdigest()

            root_hash_valid = computed_root_hash == manifest.root_hash

            return {
                "valid": len(mismatches) == 0 and root_hash_valid,
                "file_count": len(manifest.files),
                "mismatches": mismatches,
                "root_hash_valid": root_hash_valid,
                "expected_root_hash": manifest.root_hash,
                "computed_root_hash": computed_root_hash,
            }
