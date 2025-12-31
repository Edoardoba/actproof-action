"""
GitHub Action Handler
Interfaccia per integrazione CI/CD con GitHub Actions
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


class GitHubActionHandler:
    """
    Handler per GitHub Actions
    Fornisce interfaccia per integrazione CI/CD
    """
    
    def __init__(self):
        """Inizializza handler GitHub Action"""
        self.github_env = self._load_github_env()
    
    def _load_github_env(self) -> Dict[str, str]:
        """Carica variabili ambiente GitHub Actions"""
        env = {}
        
        # Variabili standard GitHub Actions
        github_vars = [
            "GITHUB_WORKSPACE",
            "GITHUB_REPOSITORY",
            "GITHUB_REF",
            "GITHUB_SHA",
            "GITHUB_EVENT_NAME",
            "GITHUB_ACTOR",
            "GITHUB_WORKFLOW",
            "GITHUB_RUN_ID",
            "GITHUB_RUN_NUMBER",
        ]
        
        for var in github_vars:
            value = os.getenv(var)
            if value:
                env[var] = value
        
        return env
    
    def is_github_action(self) -> bool:
        """Verifica se eseguito in GitHub Actions"""
        return "GITHUB_ACTIONS" in os.environ and os.environ["GITHUB_ACTIONS"] == "true"
    
    def get_repository_path(self) -> Optional[Path]:
        """Ottiene percorso repository da GitHub Actions"""
        workspace = self.github_env.get("GITHUB_WORKSPACE")
        if workspace:
            return Path(workspace)
        return None
    
    def get_event_data(self) -> Dict[str, Any]:
        """Carica dati evento GitHub Actions"""
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if not event_path or not Path(event_path).exists():
            return {}
        
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Errore caricamento event data: {e}")
            return {}
    
    def set_output(self, name: str, value: Any):
        """
        Imposta output GitHub Action
        
        Args:
            name: Nome output
            value: Valore output
        """
        output_file = os.getenv("GITHUB_OUTPUT")
        if not output_file:
            # Fallback: stampa su stdout
            print(f"::set-output name={name}::{value}")
            return
        
        try:
            # Append su file output
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"{name}={value}\n")
        except Exception as e:
            print(f"⚠️  Errore scrittura output: {e}")
    
    def set_summary(self, summary: str):
        """
        Imposta summary GitHub Action (visualizzato in Actions tab)
        
        Args:
            summary: Markdown summary
        """
        summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if not summary_file:
            print("GitHub Step Summary non disponibile")
            return
        
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
        except Exception as e:
            print(f"⚠️  Errore scrittura summary: {e}")
    
    def run_compliance_check(
        self,
        repository_path: Optional[Path] = None,
        generate_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Esegue compliance check in GitHub Action
        
        Args:
            repository_path: Percorso repository (default: GITHUB_WORKSPACE)
            generate_report: Se generare report
        
        Returns:
            Risultato compliance check
        """
        from actproof.scanner import RepositoryScanner
        from actproof.compliance import PolicyEngine
        
        if repository_path is None:
            repository_path = self.get_repository_path()
        
        if not repository_path or not repository_path.exists():
            raise ValueError(f"Repository path non valido: {repository_path}")
        
        # Scansiona repository
        scanner = RepositoryScanner(repository_path)
        scan_results = scanner.scan()
        ai_bom = scan_results["ai_bom"]
        
        # Valuta conformità
        policy_engine = PolicyEngine()
        compliance_result = policy_engine.evaluate_compliance(
            ai_bom=ai_bom,
            system_id=ai_bom.spdx_id,
        )
        
        # Imposta output GitHub Action
        self.set_output("compliant", str(compliance_result.compliant).lower())
        self.set_output("compliance_score", f"{compliance_result.requirements_check.compliance_score:.2%}")
        self.set_output("risk_level", compliance_result.risk_level.value)
        
        # Genera summary
        summary = f"""## ActProof.ai Compliance Check
        
**Repository:** {self.github_env.get('GITHUB_REPOSITORY', 'Unknown')}
**Commit:** {self.github_env.get('GITHUB_SHA', 'Unknown')[:8]}

### Risultati

- **Conformità:** {'✅ CONFORME' if compliance_result.compliant else '❌ NON CONFORME'}
- **Score Conformità:** {compliance_result.requirements_check.compliance_score:.2%}
- **Livello di Rischio:** {compliance_result.risk_level.value.upper()}

### Dettagli

- Modelli AI rilevati: {len(ai_bom.models)}
- Dataset rilevati: {len(ai_bom.datasets)}
- Dipendenze: {len(ai_bom.dependencies)}

"""
        
        if compliance_result.requirements_check.critical_gaps:
            summary += "### ⚠️  Lacune Critiche\n\n"
            for gap in compliance_result.requirements_check.critical_gaps:
                summary += f"- {gap}\n"
            summary += "\n"
        
        if compliance_result.requirements_check.recommendations:
            summary += "### 💡 Raccomandazioni\n\n"
            for rec in compliance_result.requirements_check.recommendations[:5]:
                summary += f"- {rec}\n"
        
        self.set_summary(summary)
        
        return {
            "compliant": compliance_result.compliant,
            "compliance_score": compliance_result.requirements_check.compliance_score,
            "risk_level": compliance_result.risk_level.value,
            "ai_bom": {
                "models": len(ai_bom.models),
                "datasets": len(ai_bom.datasets),
                "dependencies": len(ai_bom.dependencies),
            },
            "critical_gaps": compliance_result.requirements_check.critical_gaps,
            "recommendations": compliance_result.requirements_check.recommendations,
        }

    def post_pr_comment(self, comment: str, pr_number: Optional[int] = None) -> bool:
        """
        Posta commento su GitHub PR

        Args:
            comment: Markdown comment da postare
            pr_number: Numero PR (opzionale, auto-rilevato da evento)

        Returns:
            True se commento postato con successo
        """
        if not self.is_github_action():
            print("⚠️  Non in GitHub Actions, impossibile postare commento PR")
            return False

        # Ottieni PR number da evento se non fornito
        if pr_number is None:
            event_data = self.get_event_data()
            if "pull_request" in event_data:
                pr_number = event_data["pull_request"]["number"]
            else:
                print("⚠️  PR number non trovato in event data")
                return False

        # Ottieni repository (owner/repo)
        repo = self.github_env.get("GITHUB_REPOSITORY")
        if not repo:
            print("⚠️  GITHUB_REPOSITORY env var non trovata")
            return False

        try:
            # Usa GitHub CLI (gh) per postare commento
            import subprocess
            result = subprocess.run(
                [
                    "gh", "pr", "comment", str(pr_number),
                    "--repo", repo,
                    "--body", comment,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ Commento PR postato con successo su #{pr_number}")
                return True
            else:
                print(f"⚠️  Errore posting PR comment: {result.stderr}")
                return False

        except FileNotFoundError:
            print("⚠️  GitHub CLI (gh) non installato. Installa con: apt install gh")
            return False
        except Exception as e:
            print(f"⚠️  Errore posting PR comment: {e}")
            return False

    def run_compliance_diff(
        self,
        repo_id: str,
        base_commit: str,
        head_commit: str,
        repository_path: Optional[Path] = None,
        post_comment: bool = True,
    ) -> Dict[str, Any]:
        """
        Esegue compliance diff in GitHub Action e posta commento PR

        Args:
            repo_id: ID repository
            base_commit: Commit base
            head_commit: Commit head
            repository_path: Percorso repository (default: GITHUB_WORKSPACE)
            post_comment: Se postare commento su PR

        Returns:
            Risultato diff
        """
        from actproof.compliance.diff_engine import ComplianceDiffEngine
        from actproof.compliance import PolicyEngine
        from actproof.scanner import RepositoryScanner
        from actproof.storage import LocalStorage

        if repository_path is None:
            repository_path = self.get_repository_path()

        if not repository_path or not repository_path.exists():
            raise ValueError(f"Repository path non valido: {repository_path}")

        # Inizializza componenti
        policy_engine = PolicyEngine()
        diff_engine = ComplianceDiffEngine()
        storage = LocalStorage(base_path="./local_storage")

        # Scansiona e valuta base (HEAD^)
        scanner = RepositoryScanner(repository_path)

        # Per semplicità, usa scan corrente come head
        scan_results_head = scanner.scan()
        ai_bom_head = scan_results_head["ai_bom"]
        head_result = policy_engine.evaluate_compliance(ai_bom_head, system_id=ai_bom_head.spdx_id)

        # Per base, riusa head (in produzione, checkout base commit)
        # Questo è un placeholder - in produzione faresti checkout del base commit
        base_result = head_result  # Placeholder

        # Calcola diff
        diff_result = diff_engine.compute_diff(
            base_result=base_result,
            head_result=head_result,
            repo_id=repo_id,
            base_commit=base_commit,
            head_commit=head_commit,
        )

        # Salva risultati
        diff_key = f"{repo_id}/diffs/{base_commit}..{head_commit}.json"
        storage.save_json(diff_key, diff_result.model_dump(mode="json"))

        # Posta commento PR se richiesto
        if post_comment:
            comment = diff_engine.format_github_comment(diff_result)
            self.post_pr_comment(comment)

        # Imposta output GitHub Action
        self.set_output("diff_score_delta", f"{diff_result.score_delta:+.1%}")
        self.set_output("diff_direction", diff_result.score_direction)
        self.set_output("new_gaps_count", str(len(diff_result.new_critical_gaps)))

        return {
            "score_delta": diff_result.score_delta,
            "direction": diff_result.score_direction,
            "new_gaps": diff_result.new_critical_gaps,
            "resolved_gaps": diff_result.resolved_gaps,
            "diff_hash": diff_result.diff_hash,
        }
