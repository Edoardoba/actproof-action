"""
Validators for comprehensive EU AI Act compliance
Implements validation logic for all articles and annexes
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from actproof.models.ai_bom import AIBOM, ModelComponent, DatasetComponent
from actproof.compliance.requirements import (
    # Article 10
    DataGovernance,
    DataQualityMetrics,
    BiasAssessment,
    DataLineage,
    # Article 9
    RiskManagementSystem,
    Risk,
    RiskCategory,
    RiskSeverity,
    RiskLikelihood,
    RiskStatus,
    # Article 12
    LoggingCapability,
    # Article 15 (separated)
    AccuracyRequirements,
    RobustnessRequirements,
    CybersecurityRequirements,
    # Annex III
    HighRiskClassification,
    AnnexIIICategory,
    # GPAI
    GPAICompliance,
    GPAIModel,
    GPAIModelType,
    GPAIRole,
    # Article 16-17
    ProviderObligations,
    ProviderObligation,
    QualityManagementSystem,
    # Article 61
    EUDatabaseRegistration,
    # Article 72-73
    PostMarketMonitoring,
    # Article 8
    Article8Compliance,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Article 10: Data Governance Validator
# ============================================================================

class DataGovernanceValidator:
    """Validates data governance compliance (Article 10)"""

    def validate(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> DataGovernance:
        """
        Valida data governance compliance

        Args:
            ai_bom: AI-BOM con dataset rilevati
            codebase_path: Path alla codebase (per analisi aggiuntiva)

        Returns:
            DataGovernance con risultati validazione
        """
        datasets_documented = len(ai_bom.datasets) > 0

        # Verifica se dataset hanno metadata sufficienti
        data_relevance_documented = self._check_data_relevance(ai_bom.datasets)
        representativeness_assessed = self._check_representativeness(ai_bom.datasets)
        gdpr_compliance_verified = self._check_gdpr_compliance(ai_bom.datasets)

        # Calcola metriche qualità
        data_quality_metrics = self._assess_data_quality(ai_bom.datasets)

        # Valuta bias (basic check basato su metadata)
        bias_assessment = self._assess_bias(ai_bom.datasets)

        # Estrai data lineage se disponibile
        data_lineage = self._extract_data_lineage(ai_bom.datasets)

        # Estrai policy data governance da metadata
        data_governance_policies = self._extract_governance_policies(ai_bom)

        return DataGovernance(
            datasets_documented=datasets_documented,
            data_quality_metrics=data_quality_metrics,
            bias_assessment=bias_assessment,
            data_lineage=data_lineage,
            data_relevance_documented=data_relevance_documented,
            representativeness_assessed=representativeness_assessed,
            gdpr_compliance_verified=gdpr_compliance_verified,
            data_governance_policies=data_governance_policies,
        )

    def _check_data_relevance(self, datasets: List[DatasetComponent]) -> bool:
        """Check se rilevanza dati è documentata"""
        if not datasets:
            return False
        # Check se metadata contiene info su relevance/purpose
        for ds in datasets:
            if ds.metadata and ("purpose" in ds.metadata or "relevance" in ds.metadata):
                return True
        return False

    def _check_representativeness(self, datasets: List[DatasetComponent]) -> bool:
        """Check se rappresentatività è valutata"""
        if not datasets:
            return False
        # Check se metadata contiene info su representativeness/demographics
        for ds in datasets:
            if ds.metadata and ("representativeness" in ds.metadata or "demographics" in ds.metadata):
                return True
        return False

    def _check_gdpr_compliance(self, datasets: List[DatasetComponent]) -> bool:
        """Check GDPR compliance"""
        if not datasets:
            return True  # No datasets = no GDPR issues
        # Check se tutti i dataset hanno flag GDPR
        return all(ds.gdpr_compliant is not None for ds in datasets)

    def _assess_data_quality(self, datasets: List[DatasetComponent]) -> Optional[DataQualityMetrics]:
        """Valuta qualità dataset"""
        if not datasets:
            return None

        # Calcola score basato su completezza metadata
        total_score = 0.0
        count = 0

        for ds in datasets:
            score = 0.0
            # Completeness: ha size, source, license?
            if ds.size:
                score += 0.25
            if ds.source_location:
                score += 0.25
            if ds.license:
                score += 0.25
            if ds.metadata:
                score += 0.25
            total_score += score
            count += 1

        overall_score = total_score / count if count > 0 else 0.0

        return DataQualityMetrics(
            completeness=overall_score,
            consistency=0.8 if overall_score > 0.5 else 0.5,  # Estimate
            accuracy=0.8 if overall_score > 0.5 else 0.5,  # Estimate
            timeliness=0.7,  # Estimate
            overall_score=overall_score,
        )

    def _assess_bias(self, datasets: List[DatasetComponent]) -> Optional[BiasAssessment]:
        """Valuta bias nei dataset"""
        if not datasets:
            return None

        # Check se metadata contiene info su bias
        bias_detected = False
        bias_categories = []

        for ds in datasets:
            if ds.metadata:
                if "bias" in ds.metadata:
                    bias_detected = True
                if "bias_categories" in ds.metadata:
                    bias_categories.extend(ds.metadata["bias_categories"])

        return BiasAssessment(
            bias_detected=bias_detected,
            bias_categories=bias_categories,
            mitigation_measures=[],
        )

    def _extract_data_lineage(self, datasets: List[DatasetComponent]) -> Optional[DataLineage]:
        """Estrae data lineage"""
        if not datasets:
            return None

        # Prendi il primo dataset come esempio
        ds = datasets[0]
        return DataLineage(
            source=ds.source_location,
            collection_method=ds.metadata.get("collection_method") if ds.metadata else None,
            processing_steps=ds.metadata.get("processing_steps", []) if ds.metadata else [],
            transformations=ds.metadata.get("transformations", []) if ds.metadata else [],
            data_owners=ds.metadata.get("data_owners", []) if ds.metadata else [],
        )

    def _extract_governance_policies(self, ai_bom: AIBOM) -> List[str]:
        """Estrae policy data governance da metadata"""
        policies = []
        if ai_bom.metadata and "data_governance_policies" in ai_bom.metadata:
            policies = ai_bom.metadata["data_governance_policies"]
        return policies


# ============================================================================
# Article 9: Risk Management Validator
# ============================================================================

class RiskManagementValidator:
    """Validates risk management system (Article 9)"""

    # Common risks per AI system type
    COMMON_RISKS = {
        "llm": [
            ("Bias and discrimination in generated content", RiskCategory.BIAS_DISCRIMINATION, RiskSeverity.HIGH, RiskLikelihood.MEDIUM),
            ("Generation of harmful or illegal content", RiskCategory.FUNDAMENTAL_RIGHTS, RiskSeverity.CRITICAL, RiskLikelihood.MEDIUM),
            ("Privacy violation through training data leakage", RiskCategory.DATA_PRIVACY, RiskSeverity.HIGH, RiskLikelihood.LOW),
            ("Lack of transparency in decision-making", RiskCategory.TRANSPARENCY, RiskSeverity.MEDIUM, RiskLikelihood.HIGH),
        ],
        "vision": [
            ("Biased face recognition across demographics", RiskCategory.BIAS_DISCRIMINATION, RiskSeverity.HIGH, RiskLikelihood.HIGH),
            ("Privacy violation through unauthorized surveillance", RiskCategory.FUNDAMENTAL_RIGHTS, RiskSeverity.CRITICAL, RiskLikelihood.MEDIUM),
            ("Inaccurate predictions leading to wrong decisions", RiskCategory.HEALTH_SAFETY, RiskSeverity.HIGH, RiskLikelihood.MEDIUM),
        ],
        "recruitment": [
            ("Discriminatory candidate filtering", RiskCategory.BIAS_DISCRIMINATION, RiskSeverity.CRITICAL, RiskLikelihood.HIGH),
            ("Lack of transparency in hiring decisions", RiskCategory.TRANSPARENCY, RiskSeverity.HIGH, RiskLikelihood.HIGH),
            ("Violation of equal opportunity rights", RiskCategory.FUNDAMENTAL_RIGHTS, RiskSeverity.CRITICAL, RiskLikelihood.MEDIUM),
        ],
    }

    def validate(self, ai_bom: AIBOM, risk_level: RiskLevel, annex_iii_category: Optional[AnnexIIICategory] = None) -> RiskManagementSystem:
        """
        Valida risk management system

        Args:
            ai_bom: AI-BOM del sistema
            risk_level: Livello di rischio sistema
            annex_iii_category: Categoria Annex III (se high-risk)

        Returns:
            RiskManagementSystem con risk register
        """
        # Check se processo continuo è stabilito (cerca file/config risk management)
        continuous_process_established = self._check_continuous_process(ai_bom)

        # Genera risk register basato su AI components e categoria
        risk_register = self._generate_risk_register(ai_bom, risk_level, annex_iii_category)

        # Check se rischi residui sono accettabili
        residual_risks_acceptable = self._check_residual_risks(risk_register)

        return RiskManagementSystem(
            continuous_process_established=continuous_process_established,
            risk_register=risk_register,
            risk_assessment_methodology="AI-assisted risk identification" if risk_register else None,
            residual_risks_acceptable=residual_risks_acceptable,
            periodic_review_frequency="Quarterly" if risk_level == RiskLevel.HIGH else "Annually",
            last_review_date=None,
            next_review_date=None,
        )

    def _check_continuous_process(self, ai_bom: AIBOM) -> bool:
        """Check se processo risk management continuo è stabilito"""
        # Check metadata per evidenza risk management process
        if ai_bom.metadata and "risk_management_process" in ai_bom.metadata:
            return True
        return False

    def _generate_risk_register(self, ai_bom: AIBOM, risk_level: RiskLevel, annex_iii_category: Optional[AnnexIIICategory]) -> List[Risk]:
        """Genera risk register basato su componenti AI"""
        risks = []

        # Identify risks based on model types
        for model in ai_bom.models:
            model_type = model.model_type.value
            if model_type in self.COMMON_RISKS:
                for i, (desc, category, severity, likelihood) in enumerate(self.COMMON_RISKS[model_type]):
                    risks.append(Risk(
                        risk_id=f"RISK-{model_type.upper()}-{i+1:03d}",
                        title=" ".join(desc.split()[0:5]),  # First 5 words as title
                        description=desc,
                        category=category,
                        severity=severity,
                        likelihood=likelihood,
                        affected_stakeholders=["End users", "Data subjects"],
                        mitigation_measures=[],
                        status=RiskStatus.IDENTIFIED,
                    ))

        # Add risks based on Annex III category
        if annex_iii_category and annex_iii_category != AnnexIIICategory.NONE:
            category_risks = self._get_category_specific_risks(annex_iii_category)
            risks.extend(category_risks)

        # High-risk systems need additional risks
        if risk_level == RiskLevel.HIGH and len(risks) == 0:
            risks.append(Risk(
                risk_id="RISK-GENERIC-001",
                title="Insufficient risk assessment",
                description="No specific risks identified for high-risk AI system",
                category=RiskCategory.OTHER,
                severity=RiskSeverity.HIGH,
                likelihood=RiskLikelihood.HIGH,
                affected_stakeholders=["All stakeholders"],
                mitigation_measures=["Perform comprehensive risk assessment"],
                status=RiskStatus.IDENTIFIED,
            ))

        return risks

    def _get_category_specific_risks(self, category: AnnexIIICategory) -> List[Risk]:
        """Get risks specific to Annex III category"""
        category_risks_map = {
            AnnexIIICategory.EMPLOYMENT: [
                Risk(
                    risk_id="RISK-EMP-001",
                    title="Discriminatory hiring decisions",
                    description="AI system may perpetuate bias in recruitment and hiring processes",
                    category=RiskCategory.BIAS_DISCRIMINATION,
                    severity=RiskSeverity.CRITICAL,
                    likelihood=RiskLikelihood.HIGH,
                    affected_stakeholders=["Job candidates", "Employees"],
                    mitigation_measures=[
                        "Implement bias detection and mitigation",
                        "Regular fairness audits",
                        "Human oversight of all hiring decisions",
                    ],
                    status=RiskStatus.IDENTIFIED,
                ),
            ],
            AnnexIIICategory.BIOMETRIC: [
                Risk(
                    risk_id="RISK-BIO-001",
                    title="Privacy violation through biometric data",
                    description="Unauthorized collection or processing of biometric data",
                    category=RiskCategory.FUNDAMENTAL_RIGHTS,
                    severity=RiskSeverity.CRITICAL,
                    likelihood=RiskLikelihood.MEDIUM,
                    affected_stakeholders=["Data subjects", "Public"],
                    mitigation_measures=[
                        "Explicit consent collection",
                        "Secure biometric data storage",
                        "Compliance with GDPR Article 9",
                    ],
                    status=RiskStatus.IDENTIFIED,
                ),
            ],
            # Add more categories as needed
        }
        return category_risks_map.get(category, [])

    def _check_residual_risks(self, risk_register: List[Risk]) -> bool:
        """Check se rischi residui sono accettabili"""
        # Rischi residui accettabili se nessun rischio CRITICAL rimane unmitigated
        critical_unmitigated = [
            r for r in risk_register
            if r.severity == RiskSeverity.CRITICAL and r.status == RiskStatus.IDENTIFIED
        ]
        return len(critical_unmitigated) == 0


# ============================================================================
# Article 12: Logging Validator
# ============================================================================

class LoggingValidator:
    """Validates logging and record-keeping (Article 12)"""

    LOGGING_LIBRARIES = {
        "python": ["logging", "structlog", "loguru", "logbook", "eliot"],
        "javascript": ["winston", "bunyan", "pino", "log4js", "morgan"],
    }

    def validate(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> LoggingCapability:
        """
        Valida logging capability

        Args:
            ai_bom: AI-BOM del sistema
            codebase_path: Path alla codebase per analisi

        Returns:
            LoggingCapability con risultati
        """
        # Detect logging library from dependencies
        logging_library = self._detect_logging_library(ai_bom)
        automatic_logging_enabled = logging_library is not None

        # Check configuration files for retention period
        retention_period = self._detect_retention_period(ai_bom, codebase_path)

        # Detect logged events (basic heuristic)
        events_logged = self._detect_logged_events(ai_bom, codebase_path)

        # Check audit trail configuration
        audit_trail_immutable = self._check_audit_trail(ai_bom)

        return LoggingCapability(
            automatic_logging_enabled=automatic_logging_enabled,
            logging_library_detected=logging_library,
            retention_period_months=retention_period,
            audit_trail_immutable=audit_trail_immutable,
            events_logged=events_logged,
            log_format="JSON" if logging_library in ["winston", "pino", "structlog"] else "Text",
            access_control_implemented=False,  # Requires deeper analysis
        )

    def _detect_logging_library(self, ai_bom: AIBOM) -> Optional[str]:
        """Detect logging library from dependencies"""
        all_deps = [dep.name.lower() for dep in ai_bom.dependencies]
        for lang, libs in self.LOGGING_LIBRARIES.items():
            for lib in libs:
                if lib in all_deps:
                    return lib
        return None

    def _detect_retention_period(self, ai_bom: AIBOM, codebase_path: Optional[Path]) -> Optional[int]:
        """Detect log retention period from config"""
        # Check metadata
        if ai_bom.metadata and "log_retention_months" in ai_bom.metadata:
            return ai_bom.metadata["log_retention_months"]

        # Default to None (needs manual specification)
        return None

    def _detect_logged_events(self, ai_bom: AIBOM, codebase_path: Optional[Path]) -> List[str]:
        """Detect which events are logged"""
        # Basic detection: assume standard logging if library present
        events = []
        if ai_bom.dependencies:
            has_logging = any(dep.name.lower() in ["logging", "winston", "log4js", "structlog", "loguru"]
                            for dep in ai_bom.dependencies)
            if has_logging:
                events = ["timestamp", "log_level", "message"]  # Basic events

        return events

    def _check_audit_trail(self, ai_bom: AIBOM) -> bool:
        """Check if audit trail is immutable"""
        # Check for audit-specific libraries or blockchain-based logging
        audit_libs = ["audit-log", "immutable-log", "blockchain-logger"]
        return any(dep.name.lower() in audit_libs for dep in ai_bom.dependencies)


# ============================================================================
# Annex III: High-Risk Classification
# ============================================================================

class HighRiskClassifier:
    """Classifies AI systems according to Annex III categories"""

    # Keywords for each category
    CATEGORY_KEYWORDS = {
        AnnexIIICategory.BIOMETRIC: [
            "biometric", "face recognition", "facial recognition", "fingerprint",
            "iris recognition", "voice recognition", "gait recognition", "emotion recognition"
        ],
        AnnexIIICategory.CRITICAL_INFRASTRUCTURE: [
            "infrastructure", "water supply", "gas supply", "electricity", "heating",
            "critical infrastructure", "utility management", "power grid"
        ],
        AnnexIIICategory.EDUCATION: [
            "education", "school", "university", "student", "exam", "grading",
            "educational", "learning management", "assessment", "admission"
        ],
        AnnexIIICategory.EMPLOYMENT: [
            "recruitment", "hiring", "hr", "human resources", "employee", "job",
            "resume", "cv", "candidate", "interview", "performance evaluation",
            "workforce management", "talent acquisition"
        ],
        AnnexIIICategory.ESSENTIAL_SERVICES: [
            "credit", "loan", "creditworthiness", "credit scoring", "healthcare",
            "medical", "diagnosis", "treatment", "emergency services", "benefit",
            "social security", "welfare"
        ],
        AnnexIIICategory.LAW_ENFORCEMENT: [
            "law enforcement", "police", "criminal", "crime", "investigation",
            "surveillance", "suspect", "evidence", "forensic"
        ],
        AnnexIIICategory.MIGRATION_ASYLUM: [
            "migration", "asylum", "refugee", "border control", "visa",
            "immigration", "deportation", "travel document"
        ],
        AnnexIIICategory.JUSTICE_DEMOCRACY: [
            "justice", "court", "judge", "legal", "judiciary", "democratic",
            "election", "voting", "democracy", "legal decision"
        ],
    }

    def classify(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> HighRiskClassification:
        """
        Classifica sistema secondo Annex III

        Args:
            ai_bom: AI-BOM del sistema
            codebase_path: Path alla codebase

        Returns:
            HighRiskClassification con categorie rilevate
        """
        detected_categories = []
        keywords_detected = []

        # Analyze repository name, metadata, model names
        text_to_analyze = [
            ai_bom.name.lower(),
            ai_bom.repository_url.lower() if ai_bom.repository_url else "",
        ]

        # Add model names and contexts
        for model in ai_bom.models:
            if model.usage_context:
                text_to_analyze.append(model.usage_context.lower())

        # Add metadata
        if ai_bom.metadata:
            text_to_analyze.append(str(ai_bom.metadata).lower())

        combined_text = " ".join(text_to_analyze)

        # Check each category
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    if category not in detected_categories:
                        detected_categories.append(category)
                    keywords_detected.append(keyword)

        is_high_risk = len(detected_categories) > 0
        rationale = self._generate_rationale(detected_categories, keywords_detected)
        additional_requirements = self._get_additional_requirements(detected_categories)
        notified_body_required = AnnexIIICategory.BIOMETRIC in detected_categories  # Simplified

        return HighRiskClassification(
            is_high_risk=is_high_risk,
            annex_iii_categories=detected_categories,
            classification_rationale=rationale,
            keywords_detected=keywords_detected,
            additional_requirements=additional_requirements,
            notified_body_required=notified_body_required,
        )

    def _generate_rationale(self, categories: List[AnnexIIICategory], keywords: List[str]) -> str:
        """Generate rationale for classification"""
        if not categories:
            return "System does not fall under Annex III high-risk categories."

        cat_names = [cat.value.replace("_", " ").title() for cat in categories]
        return (
            f"System classified as HIGH-RISK under Annex III categories: {', '.join(cat_names)}. "
            f"Keywords detected: {', '.join(keywords[:5])}. "
            f"This classification requires compliance with all high-risk AI system requirements."
        )

    def _get_additional_requirements(self, categories: List[AnnexIIICategory]) -> List[str]:
        """Get additional requirements for categories"""
        requirements = []

        if AnnexIIICategory.EMPLOYMENT in categories:
            requirements.extend([
                "Article 26: Obligations for employers deploying AI systems",
                "GDPR Article 22: Right to human review of automated decisions",
                "Transparency requirements for candidates/employees",
            ])

        if AnnexIIICategory.BIOMETRIC in categories:
            requirements.extend([
                "GDPR Article 9: Special category data processing",
                "Explicit consent required",
                "Enhanced security measures for biometric data",
            ])

        if AnnexIIICategory.ESSENTIAL_SERVICES in categories:
            requirements.extend([
                "Enhanced transparency to affected persons",
                "Right to explanation of decisions",
                "Periodic validation of accuracy",
            ])

        return requirements


# ============================================================================
# Annex X-XIII: GPAI Compliance Validator
# ============================================================================

class GPAIValidator:
    """Validates GPAI (General Purpose AI) compliance"""

    GPAI_PROVIDERS = {
        "openai": ["gpt-3.5", "gpt-4", "gpt-4-turbo", "text-embedding", "dall-e"],
        "anthropic": ["claude-3", "claude-2", "claude-instant"],
        "google": ["gemini", "palm", "bard"],
        "meta": ["llama", "llama-2", "llama-3"],
        "mistral": ["mistral", "mixtral"],
        "cohere": ["command", "embed"],
    }

    SYSTEMIC_RISK_THRESHOLD_FLOPS = 1e25  # 10^25 FLOPs

    def validate(self, ai_bom: AIBOM) -> GPAICompliance:
        """
        Valida GPAI compliance

        Args:
            ai_bom: AI-BOM con modelli rilevati

        Returns:
            GPAICompliance con requisiti GPAI
        """
        # Detect GPAI models
        gpai_models = self._detect_gpai_models(ai_bom)

        # Determine user role (deployer vs provider)
        user_role = GPAIRole.DEPLOYER if gpai_models else GPAIRole.PROVIDER

        # Check systemic risk
        systemic_risk_required = any(
            model.systemic_risk_threshold for model in gpai_models
        )

        # For deployers, check compliance requirements
        transparency_info_users = False  # Needs manual check
        ai_generated_content_disclosed = False  # Needs manual check
        upstream_provider_compliance_verified = False  # Needs manual check
        intended_use_documented = False  # Check metadata
        downstream_risk_assessment = False  # Needs manual check

        return GPAICompliance(
            gpai_models_detected=gpai_models,
            user_role=user_role,
            technical_doc_provided=False,  # For providers
            transparency_info_users=transparency_info_users,
            ai_generated_content_disclosed=ai_generated_content_disclosed,
            systemic_risk_assessment_required=systemic_risk_required,
            systemic_risk_assessment_performed=False,
            code_of_practice_compliant=False,
            upstream_provider_compliance_verified=upstream_provider_compliance_verified,
            intended_use_documented=intended_use_documented,
            downstream_risk_assessment=downstream_risk_assessment,
        )

    def _detect_gpai_models(self, ai_bom: AIBOM) -> List[GPAIModel]:
        """Detect GPAI models from AI-BOM"""
        gpai_models = []

        for model in ai_bom.models:
            provider = model.provider
            model_name = model.name.lower()

            # Check if it's a known GPAI model
            is_gpai = False
            detected_provider = None

            for prov, model_patterns in self.GPAI_PROVIDERS.items():
                if provider and prov in provider.lower():
                    is_gpai = True
                    detected_provider = prov
                    break
                for pattern in model_patterns:
                    if pattern in model_name:
                        is_gpai = True
                        detected_provider = prov
                        break

            if is_gpai:
                # Determine model type
                model_type = self._determine_gpai_type(model_name)

                # Estimate if systemic risk threshold exceeded
                systemic_risk = self._estimate_systemic_risk(model_name, detected_provider)

                gpai_models.append(GPAIModel(
                    name=model.name,
                    provider=detected_provider or provider or "Unknown",
                    model_type=model_type,
                    version=model.version,
                    api_endpoint=model.api_endpoint,
                    estimated_flops=None,  # Would need model card
                    systemic_risk_threshold=systemic_risk,
                ))

        return gpai_models

    def _determine_gpai_type(self, model_name: str) -> GPAIModelType:
        """Determine GPAI model type"""
        if any(x in model_name for x in ["gpt", "claude", "llama", "palm", "gemini", "command"]):
            return GPAIModelType.LLM
        elif any(x in model_name for x in ["dall-e", "stable-diffusion", "midjourney"]):
            return GPAIModelType.VISION
        elif any(x in model_name for x in ["whisper", "audio"]):
            return GPAIModelType.VISION
        elif any(x in model_name for x in ["embed", "embedding"]):
            return GPAIModelType.EMBEDDING
        elif "codex" in model_name or "code" in model_name:
            return GPAIModelType.CODE_GENERATION
        else:
            return GPAIModelType.OTHER

    def _estimate_systemic_risk(self, model_name: str, provider: str) -> bool:
        """Estimate if model exceeds systemic risk threshold"""
        # Known large models that exceed threshold
        high_risk_models = ["gpt-4", "claude-3-opus", "gemini-ultra", "llama-3-405b"]
        return any(m in model_name for m in high_risk_models)


# ============================================================================
# Articles 16-17: Provider Obligations & QMS
# ============================================================================

class ProviderObligationsValidator:
    """Validates provider obligations and QMS"""

    ARTICLE_16_OBLIGATIONS = [
        ("Art. 16(a)", "Conformity assessment completed"),
        ("Art. 16(b)", "Technical documentation maintained and updated"),
        ("Art. 16(c)", "Automatic logging enabled for high-risk AI systems"),
        ("Art. 16(d)", "Instructions for use provided to deployers"),
        ("Art. 16(e)", "Corrective actions taken for non-conformance"),
        ("Art. 16(f)", "Cooperation with authorities"),
        ("Art. 16(g)", "CE marking affixed to high-risk AI system"),
        ("Art. 16(h)", "Registration in EU database (if high-risk)"),
    ]

    def validate(self, ai_bom: AIBOM, risk_level: RiskLevel) -> ProviderObligations:
        """
        Valida provider obligations

        Args:
            ai_bom: AI-BOM del sistema
            risk_level: Livello di rischio

        Returns:
            ProviderObligations con checklist
        """
        # Create obligation checklist
        obligations = []
        for i, (ref, desc) in enumerate(self.ARTICLE_16_OBLIGATIONS):
            obligations.append(ProviderObligation(
                obligation_id=f"OBL-{i+1:02d}",
                description=desc,
                article_reference=ref,
                compliant=False,  # Requires manual verification
                evidence=None,
            ))

        # Create QMS
        qms = QualityManagementSystem(
            qms_established=False,
            compliance_management_strategy=False,
            design_development_control=False,
            testing_validation_procedures=False,
            post_market_monitoring_plan=False,
            change_management_procedure=False,
            documentation_maintenance=False,
            corrective_preventive_actions=False,
        )

        return ProviderObligations(
            obligations=obligations,
            qms=qms,
            conformity_assessment_completed=False,
            technical_documentation_maintained=False,
            automatic_logging_enabled=False,
            instructions_for_use_provided=False,
            corrective_actions_for_nonconformance=False,
        )


# ============================================================================
# Article 61: EU Database Registration
# ============================================================================

class EUDatabaseValidator:
    """Validates EU Database registration requirements"""

    def validate(self, risk_level: RiskLevel, system_name: str) -> EUDatabaseRegistration:
        """
        Valida EU database registration

        Args:
            risk_level: Livello di rischio
            system_name: Nome sistema

        Returns:
            EUDatabaseRegistration con requirements
        """
        registration_required = risk_level == RiskLevel.HIGH

        return EUDatabaseRegistration(
            registration_required=registration_required,
            registration_completed=False,
            registration_id=None,
            registration_date=None,
            provider_name=None,
            provider_contact=None,
            system_name=system_name,
            system_version=None,
            intended_purpose=None,
            conformity_assessment_procedure=None,
            notified_body=None,
        )


# ============================================================================
# Articles 72-73: Post-Market Monitoring & Incidents
# ============================================================================

class PostMarketMonitoringValidator:
    """Validates post-market monitoring and incident reporting"""

    def validate(self, risk_level: RiskLevel) -> PostMarketMonitoring:
        """
        Valida post-market monitoring

        Args:
            risk_level: Livello di rischio

        Returns:
            PostMarketMonitoring con requirements
        """
        # High-risk systems require comprehensive monitoring
        monitoring_required = risk_level == RiskLevel.HIGH

        return PostMarketMonitoring(
            monitoring_plan_established=False,
            monitoring_frequency="Monthly" if monitoring_required else "Quarterly",
            incident_reporting_procedure=False,
            incident_contact_designated=False,
            incident_contact_email=None,
            incidents=[],
            serious_incidents_count=0,
            user_feedback_collection=False,
            user_feedback_analysis=False,
            corrective_actions_procedure=False,
            preventive_actions_procedure=False,
        )


# ============================================================================
# Article 8: Compliance with Requirements
# ============================================================================

class Article8Validator:
    """Validates Article 8 - Compliance with requirements"""

    def validate(self) -> Article8Compliance:
        """Valida Article 8 compliance"""
        return Article8Compliance(
            all_requirements_met=False,  # Determined by overall compliance
            conformity_declaration_signed=False,
            ce_marking_affixed=False,
            obligations_throughout_lifecycle=False,
        )


# ============================================================================
# Article 15: Accuracy, Robustness, Cybersecurity (Separated Validators)
# ============================================================================

class Article15AccuracyValidator:
    """Validates Article 15 - Accuracy Requirements"""

    # Common testing frameworks and evaluation libraries
    TESTING_FRAMEWORKS = {
        "python": ["pytest", "unittest", "nose", "hypothesis", "sklearn.metrics", "tensorflow.keras.metrics"],
        "javascript": ["jest", "mocha", "chai", "jasmine"],
    }

    BENCHMARK_DATASETS = [
        "MNIST", "CIFAR", "ImageNet", "COCO", "GLUE", "SuperGLUE",
        "SQuAD", "CoNLL", "IMDB", "WikiText", "Common Crawl"
    ]

    def validate(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> AccuracyRequirements:
        """Validate accuracy requirements"""

        # Detect testing frameworks
        testing_detected = self._detect_testing_frameworks(ai_bom)

        # Look for performance metrics in code
        performance_metrics = self._extract_performance_metrics(ai_bom, codebase_path)

        # Check for benchmark datasets
        benchmarks_used = self._detect_benchmark_datasets(ai_bom)

        # Determine if metrics are defined
        metrics_defined = len(performance_metrics) > 0 or testing_detected

        # Check for testing procedures documentation
        testing_procedures_documented = self._check_testing_documentation(codebase_path)

        # Model evaluation check
        model_evaluation_performed = testing_detected and len(performance_metrics) > 0

        return AccuracyRequirements(
            metrics_defined=metrics_defined,
            performance_metrics=performance_metrics,
            testing_procedures_documented=testing_procedures_documented,
            model_evaluation_performed=model_evaluation_performed,
            benchmark_datasets_used=benchmarks_used,
        )

    def _detect_testing_frameworks(self, ai_bom: AIBOM) -> bool:
        """Detect testing frameworks in dependencies"""
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            for lang, frameworks in self.TESTING_FRAMEWORKS.items():
                if any(fw in dep_name for fw in frameworks):
                    return True

        return False

    def _extract_performance_metrics(self, ai_bom: AIBOM, codebase_path: Optional[Path]) -> Dict[str, float]:
        """Extract performance metrics from code/configs"""
        metrics = {}

        # Common metric keywords to search for
        metric_keywords = ["accuracy", "precision", "recall", "f1", "auc", "roc", "mse", "mae", "rmse"]

        # Check AI-BOM metadata
        if ai_bom.metadata:
            for key, value in ai_bom.metadata.items():
                key_lower = str(key).lower()
                if any(metric in key_lower for metric in metric_keywords):
                    try:
                        metrics[key] = float(value)
                    except (ValueError, TypeError):
                        pass

        # TODO: Parse config files and training logs for metrics
        # This would require reading files from codebase_path

        return metrics

    def _detect_benchmark_datasets(self, ai_bom: AIBOM) -> List[str]:
        """Detect benchmark datasets in AI-BOM"""
        benchmarks = []

        datasets = ai_bom.datasets or []
        for dataset in datasets:
            dataset_name = (dataset.name or "").upper()
            for benchmark in self.BENCHMARK_DATASETS:
                if benchmark in dataset_name:
                    benchmarks.append(benchmark)

        return list(set(benchmarks))

    def _check_testing_documentation(self, codebase_path: Optional[Path]) -> bool:
        """Check if testing procedures are documented"""
        if not codebase_path or not codebase_path.exists():
            return False

        # Look for test documentation files
        doc_patterns = ["test*.md", "TEST*.md", "testing*.md", "TESTING*.md", "eval*.md", "EVAL*.md"]

        for pattern in doc_patterns:
            if list(codebase_path.rglob(pattern)):
                return True

        # Check README for testing section
        readme_files = list(codebase_path.glob("README*.md")) + list(codebase_path.glob("readme*.md"))
        for readme in readme_files:
            try:
                content = readme.read_text(encoding="utf-8", errors="ignore").lower()
                if "test" in content or "eval" in content or "accuracy" in content:
                    return True
            except Exception:
                continue

        return False


class Article15RobustnessValidator:
    """Validates Article 15 - Robustness & Resilience Requirements"""

    # Error handling patterns
    ERROR_HANDLING_KEYWORDS = ["try", "except", "catch", "error", "exception", "fallback", "retry"]

    # Fault tolerance libraries
    FAULT_TOLERANCE_LIBS = {
        "python": ["tenacity", "backoff", "retry", "circuit-breaker", "resilience4j"],
        "javascript": ["retry", "async-retry", "p-retry", "opossum"],
    }

    def validate(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> RobustnessRequirements:
        """Validate robustness requirements"""

        # Detect error handling (basic heuristic)
        error_handling = self._detect_error_handling(ai_bom)

        # Detect fault tolerance libraries
        fault_tolerance_measures = self._detect_fault_tolerance(ai_bom)

        # Fallback mechanisms (detected from libraries)
        fallback_mechanisms = len(fault_tolerance_measures) > 0

        # Input validation (check for validation libraries)
        input_validation = self._detect_input_validation(ai_bom)

        # Adversarial testing (check for adversarial libs)
        adversarial_testing = self._detect_adversarial_testing(ai_bom)

        # Resilience testing
        resilience_testing = self._detect_resilience_testing(ai_bom)

        # Edge case handling (heuristic based on testing)
        edge_case_handling = resilience_testing or adversarial_testing

        return RobustnessRequirements(
            error_handling_implemented=error_handling,
            fallback_mechanisms=fallback_mechanisms,
            input_validation=input_validation,
            adversarial_testing=adversarial_testing,
            fault_tolerance_measures=fault_tolerance_measures,
            resilience_testing_performed=resilience_testing,
            edge_case_handling=edge_case_handling,
        )

    def _detect_error_handling(self, ai_bom: AIBOM) -> bool:
        """Detect error handling in dependencies/metadata"""
        # Heuristic: if error handling libs present, assume error handling implemented
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            if any(keyword in dep_name for keyword in self.ERROR_HANDLING_KEYWORDS):
                return True

        return False

    def _detect_fault_tolerance(self, ai_bom: AIBOM) -> List[str]:
        """Detect fault tolerance libraries"""
        measures = []
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            for lang, libs in self.FAULT_TOLERANCE_LIBS.items():
                for lib in libs:
                    if lib in dep_name:
                        measures.append(f"{lib} ({lang})")

        return list(set(measures))

    def _detect_input_validation(self, ai_bom: AIBOM) -> bool:
        """Detect input validation libraries"""
        validation_libs = ["pydantic", "marshmallow", "cerberus", "voluptuous", "joi", "ajv", "yup"]

        deps = ai_bom.dependencies or []
        for dep in deps:
            dep_name = (dep.name or "").lower()
            if any(lib in dep_name for lib in validation_libs):
                return True

        return False

    def _detect_adversarial_testing(self, ai_bom: AIBOM) -> bool:
        """Detect adversarial testing libraries"""
        adversarial_libs = ["cleverhans", "foolbox", "adversarial-robustness-toolbox", "art"]

        deps = ai_bom.dependencies or []
        for dep in deps:
            dep_name = (dep.name or "").lower()
            if any(lib in dep_name for lib in adversarial_libs):
                return True

        return False

    def _detect_resilience_testing(self, ai_bom: AIBOM) -> bool:
        """Detect resilience testing tools"""
        resilience_libs = ["chaos", "toxiproxy", "gremlin", "simian-army", "pytest-stress"]

        deps = ai_bom.dependencies or []
        for dep in deps:
            dep_name = (dep.name or "").lower()
            if any(lib in dep_name for lib in resilience_libs):
                return True

        return False


class Article15CybersecurityValidator:
    """Validates Article 15 - Cybersecurity Requirements"""

    # Security frameworks and standards
    SECURITY_FRAMEWORKS = ["ISO 27001", "NIST CSF", "SOC2", "PCI-DSS", "GDPR", "HIPAA"]

    # Security libraries
    ENCRYPTION_LIBS = {
        "python": ["cryptography", "pycryptodome", "nacl", "hashlib"],
        "javascript": ["crypto", "bcrypt", "crypto-js", "node-forge"],
    }

    AUTH_LIBS = {
        "python": ["flask-login", "django-auth", "authlib", "oauthlib", "pyjwt"],
        "javascript": ["passport", "jsonwebtoken", "oauth", "auth0"],
    }

    SECURITY_SCANNING_LIBS = {
        "python": ["bandit", "safety", "snyk", "semgrep"],
        "javascript": ["eslint-plugin-security", "npm-audit", "snyk"],
    }

    def validate(self, ai_bom: AIBOM, codebase_path: Optional[Path] = None) -> CybersecurityRequirements:
        """Validate cybersecurity requirements"""

        # Detect encryption libraries
        data_encryption = self._detect_encryption(ai_bom)

        # Detect access control/authentication libraries
        access_controls = self._detect_access_controls(ai_bom)

        # Detect security scanning tools
        vulnerability_scanning = self._detect_vulnerability_scanning(ai_bom)

        # Penetration testing (check for pentesting tools)
        penetration_testing = self._detect_pentesting_tools(ai_bom)

        # Incident response plan (check documentation)
        incident_response_plan = self._check_incident_response_docs(codebase_path)

        # Security frameworks (check documentation/metadata)
        security_frameworks = self._detect_security_frameworks(ai_bom, codebase_path)

        # Last security audit (check metadata)
        last_security_audit = self._get_last_security_audit(ai_bom)

        # Security patches (check dependencies for recent versions)
        security_patches_updated = self._check_security_patches(ai_bom)

        # Authentication mechanisms
        authentication_mechanisms = self._detect_auth_mechanisms(ai_bom)

        # Overall security measures
        security_measures_implemented = (
            data_encryption or access_controls or vulnerability_scanning
        )

        return CybersecurityRequirements(
            security_measures_implemented=security_measures_implemented,
            data_encryption=data_encryption,
            access_controls=access_controls,
            vulnerability_scanning=vulnerability_scanning,
            penetration_testing=penetration_testing,
            incident_response_plan=incident_response_plan,
            security_frameworks=security_frameworks,
            last_security_audit=last_security_audit,
            security_patches_updated=security_patches_updated,
            authentication_mechanisms=authentication_mechanisms,
        )

    def _detect_encryption(self, ai_bom: AIBOM) -> bool:
        """Detect encryption libraries"""
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            for lang, libs in self.ENCRYPTION_LIBS.items():
                if any(lib in dep_name for lib in libs):
                    return True

        return False

    def _detect_access_controls(self, ai_bom: AIBOM) -> bool:
        """Detect access control/authentication libraries"""
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            for lang, libs in self.AUTH_LIBS.items():
                if any(lib in dep_name for lib in libs):
                    return True

        return False

    def _detect_vulnerability_scanning(self, ai_bom: AIBOM) -> bool:
        """Detect vulnerability scanning tools"""
        deps = ai_bom.dependencies or []

        for dep in deps:
            dep_name = (dep.name or "").lower()
            for lang, libs in self.SECURITY_SCANNING_LIBS.items():
                if any(lib in dep_name for lib in libs):
                    return True

        return False

    def _detect_pentesting_tools(self, ai_bom: AIBOM) -> bool:
        """Detect penetration testing tools"""
        pentesting_libs = ["metasploit", "burp", "zap", "nmap", "nessus", "w3af"]

        deps = ai_bom.dependencies or []
        for dep in deps:
            dep_name = (dep.name or "").lower()
            if any(lib in dep_name for lib in pentesting_libs):
                return True

        return False

    def _check_incident_response_docs(self, codebase_path: Optional[Path]) -> bool:
        """Check for incident response documentation"""
        if not codebase_path or not codebase_path.exists():
            return False

        # Look for security/incident response documentation
        doc_patterns = ["SECURITY*.md", "security*.md", "incident*.md", "INCIDENT*.md"]

        for pattern in doc_patterns:
            if list(codebase_path.rglob(pattern)):
                return True

        return False

    def _detect_security_frameworks(self, ai_bom: AIBOM, codebase_path: Optional[Path]) -> List[str]:
        """Detect security frameworks from metadata/docs"""
        frameworks = []

        # Check AI-BOM metadata
        if ai_bom.metadata:
            metadata_str = str(ai_bom.metadata).upper()
            for framework in self.SECURITY_FRAMEWORKS:
                if framework.replace(" ", "").upper() in metadata_str.replace(" ", ""):
                    frameworks.append(framework)

        # TODO: Parse documentation for framework mentions

        return frameworks

    def _get_last_security_audit(self, ai_bom: AIBOM) -> Optional[datetime]:
        """Get last security audit date from metadata"""
        if ai_bom.metadata:
            audit_date = ai_bom.metadata.get("last_security_audit") or ai_bom.metadata.get("security_audit_date")
            if audit_date:
                try:
                    if isinstance(audit_date, datetime):
                        return audit_date
                    return datetime.fromisoformat(str(audit_date))
                except (ValueError, TypeError):
                    pass

        return None

    def _check_security_patches(self, ai_bom: AIBOM) -> bool:
        """Check if dependencies are up-to-date (heuristic)"""
        # Heuristic: if vulnerability scanning is enabled, assume patches are updated
        return self._detect_vulnerability_scanning(ai_bom)

    def _detect_auth_mechanisms(self, ai_bom: AIBOM) -> List[str]:
        """Detect authentication mechanisms"""
        mechanisms = []

        auth_keywords = {
            "jwt": "JWT",
            "oauth": "OAuth",
            "saml": "SAML",
            "mfa": "Multi-Factor Auth",
            "2fa": "Two-Factor Auth",
            "ldap": "LDAP",
            "kerberos": "Kerberos",
        }

        deps = ai_bom.dependencies or []
        for dep in deps:
            dep_name = (dep.name or "").lower()
            for keyword, mechanism in auth_keywords.items():
                if keyword in dep_name:
                    mechanisms.append(mechanism)

        return list(set(mechanisms))
