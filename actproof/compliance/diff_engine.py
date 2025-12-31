"""
Compliance Diff Engine
Confronta risultati compliance tra due revisioni (base/head)
Per supportare CI/CD e review process
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from pathlib import Path
import hashlib
import json

from actproof.compliance.requirements import ComplianceResult, RiskLevel


class ArticleDelta(BaseModel):
    """Delta per un singolo articolo"""
    article: str = Field(..., description="Nome articolo (es: 'Article 11')")
    base_compliant: bool = Field(..., description="Compliance nella revisione base")
    head_compliant: bool = Field(..., description="Compliance nella revisione head")
    changed: bool = Field(..., description="Se lo stato è cambiato")
    direction: str = Field(..., description="'improved', 'degraded', or 'unchanged'")
    details: Dict[str, Any] = Field(default_factory=dict, description="Dettagli aggiuntivi")


class ComplianceGapDelta(BaseModel):
    """Delta per gap critici"""
    gap: str = Field(..., description="Descrizione gap")
    status: str = Field(..., description="'new', 'resolved', or 'existing'")


class FileDelta(BaseModel):
    """Delta per file cambiati"""
    file_path: str = Field(..., description="Percorso file")
    change_type: str = Field(..., description="'added', 'modified', 'deleted'")
    affected_articles: List[str] = Field(default_factory=list, description="Articoli potenzialmente impattati")


class ComplianceDiffResult(BaseModel):
    """Risultato del confronto compliance tra base e head"""

    # Versione schema
    schema_version: str = Field(default="1.0.0", description="Versione schema diff")

    # Metadata
    repo_id: str = Field(..., description="ID repository")
    base_commit: str = Field(..., description="Commit SHA base")
    head_commit: str = Field(..., description="Commit SHA head")
    diff_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp diff")

    # Score delta
    base_score: float = Field(..., description="Score compliance base (0-1)")
    head_score: float = Field(..., description="Score compliance head (0-1)")
    score_delta: float = Field(..., description="Delta score (head - base)")
    score_direction: str = Field(..., description="'improved', 'degraded', or 'unchanged'")

    # Risk level
    base_risk_level: RiskLevel = Field(..., description="Risk level base")
    head_risk_level: RiskLevel = Field(..., description="Risk level head")
    risk_level_changed: bool = Field(..., description="Se risk level è cambiato")

    # Article-level delta
    article_deltas: List[ArticleDelta] = Field(default_factory=list, description="Delta per articolo")
    improved_articles: List[str] = Field(default_factory=list, description="Articoli migliorati")
    degraded_articles: List[str] = Field(default_factory=list, description="Articoli peggiorati")

    # Gap delta
    gap_deltas: List[ComplianceGapDelta] = Field(default_factory=list, description="Delta gap critici")
    new_critical_gaps: List[str] = Field(default_factory=list, description="Nuovi gap critici")
    resolved_gaps: List[str] = Field(default_factory=list, description="Gap risolti")

    # File changes (se disponibili)
    changed_files: List[FileDelta] = Field(default_factory=list, description="File cambiati")

    # Summary
    summary: str = Field(..., description="Summary testuale del diff")

    # Hash risultati per audit trail
    base_result_hash: str = Field(..., description="Hash risultato base")
    head_result_hash: str = Field(..., description="Hash risultato head")
    diff_hash: str = Field(default="", description="Hash di questo diff")

    def compute_diff_hash(self) -> str:
        """Calcola hash deterministico del diff"""
        data = {
            "schema_version": self.schema_version,
            "repo_id": self.repo_id,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "base_score": self.base_score,
            "head_score": self.head_score,
            "score_delta": self.score_delta,
            "base_result_hash": self.base_result_hash,
            "head_result_hash": self.head_result_hash,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def model_post_init(self, __context):
        """Calcola hash dopo inizializzazione"""
        if not self.diff_hash:
            self.diff_hash = self.compute_diff_hash()


class ComplianceDiffEngine:
    """
    Engine per calcolare diff compliance tra revisioni
    Supporta CI/CD gates e review process
    """

    def __init__(self):
        """Inizializza diff engine"""
        pass

    def compute_diff(
        self,
        base_result: ComplianceResult,
        head_result: ComplianceResult,
        repo_id: str,
        base_commit: str,
        head_commit: str,
        changed_files: Optional[List[Dict[str, Any]]] = None,
    ) -> ComplianceDiffResult:
        """
        Calcola diff deterministico tra due compliance results

        Args:
            base_result: Risultato compliance base
            head_result: Risultato compliance head
            repo_id: ID repository
            base_commit: Commit SHA base
            head_commit: Commit SHA head
            changed_files: Lista file cambiati (opzionale)

        Returns:
            Diff result completo
        """
        # Calcola delta score
        base_score = base_result.requirements_check.compliance_score
        head_score = head_result.requirements_check.compliance_score
        score_delta = head_score - base_score

        # Determina direzione
        if abs(score_delta) < 0.01:  # Threshold per "unchanged"
            score_direction = "unchanged"
        elif score_delta > 0:
            score_direction = "improved"
        else:
            score_direction = "degraded"

        # Analizza delta articoli
        article_deltas = self._compute_article_deltas(
            base_result.requirements_check,
            head_result.requirements_check
        )

        improved_articles = [
            a.article for a in article_deltas if a.direction == "improved"
        ]
        degraded_articles = [
            a.article for a in article_deltas if a.direction == "degraded"
        ]

        # Analizza gap delta
        gap_deltas = self._compute_gap_deltas(
            base_result.requirements_check.critical_gaps,
            head_result.requirements_check.critical_gaps
        )

        new_gaps = [g.gap for g in gap_deltas if g.status == "new"]
        resolved_gaps = [g.gap for g in gap_deltas if g.status == "resolved"]

        # Analizza file changes (se forniti)
        file_deltas = self._analyze_file_changes(changed_files, degraded_articles)

        # Genera summary
        summary = self._generate_summary(
            score_direction, score_delta, improved_articles, degraded_articles,
            new_gaps, resolved_gaps
        )

        # Hash risultati
        base_hash = self._hash_compliance_result(base_result)
        head_hash = self._hash_compliance_result(head_result)

        # Costruisci diff result
        diff_result = ComplianceDiffResult(
            repo_id=repo_id,
            base_commit=base_commit,
            head_commit=head_commit,
            base_score=base_score,
            head_score=head_score,
            score_delta=score_delta,
            score_direction=score_direction,
            base_risk_level=base_result.risk_level,
            head_risk_level=head_result.risk_level,
            risk_level_changed=base_result.risk_level != head_result.risk_level,
            article_deltas=article_deltas,
            improved_articles=improved_articles,
            degraded_articles=degraded_articles,
            gap_deltas=gap_deltas,
            new_critical_gaps=new_gaps,
            resolved_gaps=resolved_gaps,
            changed_files=file_deltas,
            summary=summary,
            base_result_hash=base_hash,
            head_result_hash=head_hash,
        )

        # Calcola hash diff
        diff_result.diff_hash = diff_result.compute_diff_hash()

        return diff_result

    def _compute_article_deltas(self, base_req, head_req) -> List[ArticleDelta]:
        """Calcola delta per ogni articolo"""
        deltas = []

        # Articoli da verificare
        articles = [
            ("Article 11 (Technical Documentation)", "article_11_compliant"),
            ("Article 13 (Transparency)", "article_13_compliant"),
            ("Article 14 (Human Oversight)", "article_14_compliant"),
            ("Article 15 (Accuracy & Robustness)", "article_15_compliant"),
        ]

        for article_name, field_name in articles:
            base_val = getattr(base_req, field_name, False)
            head_val = getattr(head_req, field_name, False)
            changed = base_val != head_val

            if changed:
                direction = "improved" if head_val and not base_val else "degraded"
            else:
                direction = "unchanged"

            details = {}
            # Aggiungi dettagli specifici per Article 11
            if field_name == "article_11_compliant":
                details["base_missing_fields"] = base_req.article_11_missing_fields
                details["head_missing_fields"] = head_req.article_11_missing_fields
                if base_req.article_11_missing_fields != head_req.article_11_missing_fields:
                    details["fields_added"] = [
                        f for f in base_req.article_11_missing_fields
                        if f not in head_req.article_11_missing_fields
                    ]
                    details["fields_still_missing"] = head_req.article_11_missing_fields

            deltas.append(ArticleDelta(
                article=article_name,
                base_compliant=base_val,
                head_compliant=head_val,
                changed=changed,
                direction=direction,
                details=details
            ))

        return deltas

    def _compute_gap_deltas(
        self, base_gaps: List[str], head_gaps: List[str]
    ) -> List[ComplianceGapDelta]:
        """Calcola delta per gap critici"""
        deltas = []

        base_set = set(base_gaps)
        head_set = set(head_gaps)

        # Nuovi gap
        for gap in head_set - base_set:
            deltas.append(ComplianceGapDelta(gap=gap, status="new"))

        # Gap risolti
        for gap in base_set - head_set:
            deltas.append(ComplianceGapDelta(gap=gap, status="resolved"))

        # Gap esistenti
        for gap in base_set & head_set:
            deltas.append(ComplianceGapDelta(gap=gap, status="existing"))

        return deltas

    def _analyze_file_changes(
        self, changed_files: Optional[List[Dict[str, Any]]],
        degraded_articles: List[str]
    ) -> List[FileDelta]:
        """Analizza file cambiati e correlazione con articoli"""
        if not changed_files:
            return []

        file_deltas = []
        for file_info in changed_files:
            file_path = file_info.get("path", "")
            change_type = file_info.get("status", "modified")

            # Correlazione euristica file -> articoli
            affected = []
            # Se ci sono articoli degradati, considera tutti i file cambiati come potenziali cause
            if degraded_articles and any(ext in file_path for ext in [".py", ".js", ".ts", ".java"]):
                affected = degraded_articles[:2]  # Limita a primi 2 per brevità

            file_deltas.append(FileDelta(
                file_path=file_path,
                change_type=change_type,
                affected_articles=affected
            ))

        return file_deltas[:10]  # Limita a 10 file per performance

    def _generate_summary(
        self,
        direction: str,
        delta: float,
        improved: List[str],
        degraded: List[str],
        new_gaps: List[str],
        resolved_gaps: List[str],
    ) -> str:
        """Genera summary testuale del diff"""
        lines = []

        # Score summary
        if direction == "improved":
            lines.append(f"✅ Compliance score improved by {delta:+.1%}")
        elif direction == "degraded":
            lines.append(f"⚠️  Compliance score degraded by {delta:.1%}")
        else:
            lines.append(f"➖ Compliance score unchanged ({delta:+.1%})")

        # Articoli
        if improved:
            lines.append(f"\nImproved articles ({len(improved)}): {', '.join(improved)}")
        if degraded:
            lines.append(f"\n⚠️  Degraded articles ({len(degraded)}): {', '.join(degraded)}")

        # Gap
        if new_gaps:
            lines.append(f"\n⚠️  New critical gaps ({len(new_gaps)})")
        if resolved_gaps:
            lines.append(f"\n✅ Resolved gaps ({len(resolved_gaps)})")

        return "\n".join(lines)

    def _hash_compliance_result(self, result: ComplianceResult) -> str:
        """Calcola hash deterministico di un compliance result"""
        data = {
            "system_id": result.system_id,
            "compliant": result.compliant,
            "compliance_score": result.requirements_check.compliance_score,
            "risk_level": result.risk_level.value,
            "critical_gaps": sorted(result.requirements_check.critical_gaps),
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def format_github_comment(self, diff_result: ComplianceDiffResult) -> str:
        """
        Formatta diff result come GitHub PR comment

        Args:
            diff_result: Risultato diff

        Returns:
            Markdown comment per GitHub PR
        """
        lines = []

        lines.append("## 🤖 ActProof.ai Compliance Diff")
        lines.append("")
        lines.append(f"**Base:** `{diff_result.base_commit[:8]}`  ")
        lines.append(f"**Head:** `{diff_result.head_commit[:8]}`")
        lines.append("")

        # Score delta
        if diff_result.score_direction == "improved":
            icon = "✅"
        elif diff_result.score_direction == "degraded":
            icon = "⚠️"
        else:
            icon = "➖"

        lines.append(f"### {icon} Compliance Score")
        lines.append("")
        lines.append(f"- **Base:** {diff_result.base_score:.1%}")
        lines.append(f"- **Head:** {diff_result.head_score:.1%}")
        lines.append(f"- **Delta:** {diff_result.score_delta:+.1%}")
        lines.append("")

        # Top 5 article deltas (changed only)
        changed_articles = [a for a in diff_result.article_deltas if a.changed]
        if changed_articles:
            lines.append("### 📊 Article Changes")
            lines.append("")
            for article in changed_articles[:5]:
                status = "✅" if article.direction == "improved" else "⚠️"
                lines.append(f"- {status} **{article.article}**: {article.direction}")
            lines.append("")

        # New critical gaps
        if diff_result.new_critical_gaps:
            lines.append("### ⚠️  New Critical Gaps")
            lines.append("")
            for gap in diff_result.new_critical_gaps[:5]:
                lines.append(f"- {gap}")
            lines.append("")

        # Resolved gaps
        if diff_result.resolved_gaps:
            lines.append("### ✅ Resolved Gaps")
            lines.append("")
            for gap in diff_result.resolved_gaps[:5]:
                lines.append(f"- ~~{gap}~~")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated by ActProof.ai at {diff_result.diff_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        return "\n".join(lines)
