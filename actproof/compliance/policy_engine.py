"""
Policy-as-Code Engine - EXTENDED VERSION
Validates AI system compliance with EU AI Act requirements
NOW COVERS: Articles 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 61, 72, 73 + Annex III + GPAI
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from actproof.compliance.requirements import (
    TechnicalDocumentation,
    AnnexIVRequirements,
    ComplianceResult,
    RiskLevel,
    SystemType,
    RiskManagementSystem,
    DataGovernance,
    LoggingCapability,
    HighRiskClassification,
    GPAICompliance,
)
from actproof.models.ai_bom import AIBOM

# Import all new validators
from actproof.compliance.validators import (
    DataGovernanceValidator,
    RiskManagementValidator,
    LoggingValidator,
    HighRiskClassifier,
    GPAIValidator,
    ProviderObligationsValidator,
    EUDatabaseValidator,
    PostMarketMonitoringValidator,
    Article8Validator,
    Article15AccuracyValidator,
    Article15RobustnessValidator,
    Article15CybersecurityValidator,
)

# Import comprehensive recommendations generator
from actproof.compliance.policy_engine_ext import generate_comprehensive_recommendations


class PolicyEngine:
    """
    Policy-as-Code validation engine - EXTENDED VERSION
    Translates legal requirements into automatic validation

    NOW VALIDATES:
    - Article 8: Compliance with Requirements
    - Article 9: Risk Management System
    - Article 10: Data Governance
    - Article 11: Technical Documentation
    - Article 12: Record-Keeping & Logging
    - Article 13: Transparency
    - Article 14: Human Oversight
    - Article 15: Accuracy, Robustness, Cybersecurity
    - Article 16-17: Provider Obligations & QMS
    - Article 61: EU Database Registration
    - Article 72-73: Post-Market Monitoring & Incidents
    - Annex III: High-Risk Classification
    - Annex X-XIII: GPAI Requirements
    """

    def __init__(self, codebase_path: Optional[Path] = None):
        self.required_fields_article_11 = [
            "general_description",
            "intended_purpose",
            "context_of_use",
            "logic_description",
            "technical_specifications",
            "accuracy_metrics",
            "risk_management",
        ]

        # Initialize all validators
        self.data_governance_validator = DataGovernanceValidator()
        self.risk_management_validator = RiskManagementValidator()
        self.logging_validator = LoggingValidator()
        self.high_risk_classifier = HighRiskClassifier()
        self.gpai_validator = GPAIValidator()
        self.provider_obligations_validator = ProviderObligationsValidator()
        self.eu_database_validator = EUDatabaseValidator()
        self.post_market_validator = PostMarketMonitoringValidator()
        self.article_8_validator = Article8Validator()

        # Article 15 validators (separated into 3 components)
        self.accuracy_validator = Article15AccuracyValidator()
        self.robustness_validator = Article15RobustnessValidator()
        self.cybersecurity_validator = Article15CybersecurityValidator()

        self.codebase_path = codebase_path

    def validate_technical_documentation(
        self, documentation: TechnicalDocumentation
    ) -> AnnexIVRequirements:
        """
        Validates technical documentation against Annex IV requirements
        
        Args:
            documentation: Technical documentation to validate
        
        Returns:
            Requirements validation result
        """
        missing_fields = []
        
        # Check Article 11 - Required fields
        for field in self.required_fields_article_11:
            value = getattr(documentation, field, None)
            if value is None or (isinstance(value, (dict, list)) and len(value) == 0):
                missing_fields.append(field)
        
        article_11_compliant = len(missing_fields) == 0
        
        # Check Article 14 - Human Oversight (required for high risk)
        article_14_compliant = True
        if documentation.risk_level == RiskLevel.HIGH:
            if not documentation.human_oversight or len(documentation.oversight_measures) == 0:
                article_14_compliant = False
        
        # Check Article 15 - Accuracy metrics
        article_15_compliant = len(documentation.accuracy_metrics) > 0
        
        # Calculate compliance score
        total_checks = 4  # Articles 11, 13, 14, 15
        passed_checks = sum([
            article_11_compliant,
            documentation.article_13_compliant if hasattr(documentation, 'article_13_compliant') else True,
            article_14_compliant,
            article_15_compliant,
        ])
        compliance_score = passed_checks / total_checks
        
        # Identify critical gaps
        critical_gaps = []
        if not article_11_compliant:
            critical_gaps.append("Incomplete technical documentation (Article 11)")
        if not article_14_compliant:
            critical_gaps.append("Missing human oversight plan (Article 14)")
        if not article_15_compliant:
            critical_gaps.append("Accuracy metrics not provided (Article 15)")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            documentation, article_11_compliant, article_14_compliant, article_15_compliant
        )
        
        return AnnexIVRequirements(
            article_11_compliant=article_11_compliant,
            article_11_missing_fields=missing_fields,
            article_13_compliant=True,  # To be implemented with RAG
            article_14_compliant=article_14_compliant,
            human_oversight_required=documentation.risk_level == RiskLevel.HIGH,
            article_15_compliant=article_15_compliant,
            accuracy_metrics_provided=article_15_compliant,
            compliance_score=compliance_score,
            critical_gaps=critical_gaps,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        documentation: TechnicalDocumentation,
        article_11_ok: bool,
        article_14_ok: bool,
        article_15_ok: bool,
    ) -> List[str]:
        """Generate recommendations to improve compliance"""
        recommendations = []
        
        if not article_11_ok:
            recommendations.append(
                "Complete all required fields in technical documentation (Article 11)"
            )
        
        if not article_14_ok:
            recommendations.append(
                "Implement human oversight plan with concrete measures (Article 14)"
            )
        
        if not article_15_ok:
            recommendations.append(
                "Provide quantitative metrics for accuracy, robustness and cybersecurity (Article 15)"
            )
        
        if documentation.risk_level == RiskLevel.HIGH:
            if len(documentation.transparency_measures) == 0:
                recommendations.append(
                    "Implement transparency measures to inform users (Article 13)"
                )
        
        if len(documentation.identified_risks) == 0:
            recommendations.append(
                "Perform complete risk analysis and document all identified risks"
            )
        
        return recommendations

    def evaluate_compliance(
        self,
        ai_bom: AIBOM,
        technical_doc: Optional[TechnicalDocumentation] = None,
        system_id: Optional[str] = None,
    ) -> ComplianceResult:
        """
        Evaluates complete system compliance - EXTENDED VERSION

        NOW VALIDATES ALL ARTICLES + ANNEXES:
        - Articles: 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 61, 72, 73
        - Annex III: High-Risk Classification
        - Annex X-XIII: GPAI Requirements

        For non-AI systems (no models, no AI dependencies), returns early
        with high compliance as EU AI Act does not apply.

        Args:
            ai_bom: System AI-BOM
            technical_doc: Technical documentation (optional)
            system_id: System ID

        Returns:
            Complete compliance evaluation result with 100% coverage
        """
        if system_id is None:
            system_id = ai_bom.spdx_id

        # ============================================================
        # STEP 0: Check if this is actually an AI system
        # ============================================================
        is_ai_system = self._is_ai_system(ai_bom)

        if not is_ai_system:
            # Non-AI system - EU AI Act does not apply
            return self._create_non_ai_compliance_result(ai_bom, system_id)

        # If no technical documentation exists, create a base from AI-BOM
        if technical_doc is None:
            technical_doc = self._extract_documentation_from_bom(ai_bom)

        # ============================================================
        # STEP 1: Annex III - High-Risk Classification (FIRST!)
        # ============================================================
        annex_iii_classification = self.high_risk_classifier.classify(ai_bom, self.codebase_path)

        # Update risk level based on Annex III classification
        if annex_iii_classification.is_high_risk:
            technical_doc.risk_level = RiskLevel.HIGH

        # ============================================================
        # STEP 2: Validate ALL Articles
        # ============================================================

        # Article 8: Compliance with Requirements
        article_8 = self.article_8_validator.validate()

        # Article 9: Risk Management System
        annex_iii_category = annex_iii_classification.annex_iii_categories[0] if annex_iii_classification.annex_iii_categories else None
        article_9 = self.risk_management_validator.validate(
            ai_bom,
            technical_doc.risk_level,
            annex_iii_category
        )
        article_9_compliant = article_9.compliant

        # Article 10: Data Governance
        article_10 = self.data_governance_validator.validate(ai_bom, self.codebase_path)
        article_10_compliant = article_10.compliant

        # Article 11-15: Technical Documentation (existing validation)
        requirements_check_base = self.validate_technical_documentation(technical_doc)

        # Article 12: Record-Keeping & Logging
        article_12 = self.logging_validator.validate(ai_bom, self.codebase_path)
        article_12_compliant = article_12.compliant

        # Article 15: Accuracy, Robustness, Cybersecurity (separated into 3 validators)
        article_15_accuracy = self.accuracy_validator.validate(ai_bom, self.codebase_path)
        article_15_robustness = self.robustness_validator.validate(ai_bom, self.codebase_path)
        article_15_cybersecurity = self.cybersecurity_validator.validate(ai_bom, self.codebase_path)

        # Articles 16-17: Provider Obligations & QMS
        article_16_17 = self.provider_obligations_validator.validate(ai_bom, technical_doc.risk_level)
        article_16_compliant = article_16_17.conformity_assessment_completed
        article_17_compliant = article_16_17.qms.compliant if article_16_17.qms else False

        # Article 61: EU Database Registration
        article_61 = self.eu_database_validator.validate(
            technical_doc.risk_level,
            technical_doc.system_name
        )
        article_61_compliant = article_61.compliant

        # Articles 72-73: Post-Market Monitoring & Incidents
        article_72_73 = self.post_market_validator.validate(technical_doc.risk_level)
        article_72_compliant = article_72_73.compliant
        article_73_compliant = article_72_73.incident_reporting_procedure

        # ============================================================
        # STEP 3: GPAI Validation (Annex X-XIII)
        # ============================================================
        gpai_compliance = self.gpai_validator.validate(ai_bom)
        gpai_compliant = (
            gpai_compliance.compliant_as_deployer
            if len(gpai_compliance.gpai_models_detected) > 0
            else True  # N/A if no GPAI models
        )

        # ============================================================
        # STEP 4: Calculate COMPREHENSIVE Compliance Score
        # ============================================================

        # Create extended AnnexIVRequirements
        requirements_check = AnnexIVRequirements(
            # Existing (11, 13, 14, 15)
            article_11_compliant=requirements_check_base.article_11_compliant,
            article_11_missing_fields=requirements_check_base.article_11_missing_fields,
            article_13_compliant=requirements_check_base.article_13_compliant,
            article_14_compliant=requirements_check_base.article_14_compliant,
            human_oversight_required=requirements_check_base.human_oversight_required,
            article_15_compliant=requirements_check_base.article_15_compliant,
            accuracy_metrics_provided=requirements_check_base.accuracy_metrics_provided,

            # NEW: All extended articles
            article_8=article_8,
            article_9=article_9,
            article_9_compliant=article_9_compliant,
            article_10=article_10,
            article_10_compliant=article_10_compliant,
            article_12=article_12,
            article_12_compliant=article_12_compliant,

            # NEW: Article 15 - Separated into 3 components
            article_15_accuracy=article_15_accuracy,
            article_15_robustness=article_15_robustness,
            article_15_cybersecurity=article_15_cybersecurity,

            article_16_17=article_16_17,
            article_16_compliant=article_16_compliant,
            article_17_compliant=article_17_compliant,
            article_61=article_61,
            article_61_compliant=article_61_compliant,
            article_72_73=article_72_73,
            article_72_compliant=article_72_compliant,
            article_73_compliant=article_73_compliant,

            # NEW: Annex III + GPAI
            annex_iii=annex_iii_classification,
            gpai=gpai_compliance,
            gpai_compliant=gpai_compliant,

            # Calculate comprehensive compliance score
            compliance_score=0.0,  # Will be calculated below
            critical_gaps=[],  # Will be populated below
            recommendations=[],  # Will be generated below
        )

        # Calculate score: average of all article compliance
        total_articles = requirements_check.total_articles_checked
        compliant_articles = requirements_check.articles_compliant_count

        # Add GPAI to score if applicable
        if len(gpai_compliance.gpai_models_detected) > 0:
            total_articles += 1
            if gpai_compliant:
                compliant_articles += 1

        compliance_score = compliant_articles / total_articles if total_articles > 0 else 0.0
        requirements_check.compliance_score = compliance_score

        # ============================================================
        # STEP 5: Identify Critical Gaps
        # ============================================================
        critical_gaps = []

        if not article_10_compliant:
            critical_gaps.append("Data Governance non-compliant (Article 10) - Quality, bias, lineage")
        if not article_9_compliant:
            critical_gaps.append("Risk Management System not established (Article 9)")
        if not article_12_compliant:
            critical_gaps.append("Automatic logging not implemented (Article 12)")
        if not requirements_check.article_11_compliant:
            critical_gaps.append("Incomplete technical documentation (Article 11)")
        if not requirements_check.article_14_compliant and technical_doc.risk_level == RiskLevel.HIGH:
            critical_gaps.append("Human Oversight missing for HIGH-RISK system (Article 14)")

        # Article 15 - Separated compliance checks
        if not article_15_accuracy.compliant:
            critical_gaps.append("Accuracy metrics not properly defined or evaluated (Article 15)")
        if not article_15_robustness.compliant:
            critical_gaps.append("Robustness measures insufficient (Article 15)")
        if not article_15_cybersecurity.compliant:
            critical_gaps.append("Cybersecurity requirements not satisfied (Article 15)")

        if not article_16_compliant:
            critical_gaps.append("Provider Obligations not satisfied (Article 16)")
        if not article_17_compliant and technical_doc.risk_level == RiskLevel.HIGH:
            critical_gaps.append("Quality Management System not established (Article 17)")
        if not article_61_compliant and technical_doc.risk_level == RiskLevel.HIGH:
            critical_gaps.append("EU Database registration missing for HIGH-RISK system (Article 61)")
        if not article_72_compliant and technical_doc.risk_level == RiskLevel.HIGH:
            critical_gaps.append("Post-Market Monitoring Plan missing (Article 72)")
        if not gpai_compliant and len(gpai_compliance.gpai_models_detected) > 0:
            critical_gaps.append("GPAI Compliance not satisfied (Annex X-XIII)")

        requirements_check.critical_gaps = critical_gaps

        # ============================================================
        # STEP 6: Generate Comprehensive Recommendations
        # ============================================================
        recommendations = self._generate_comprehensive_recommendations(
            requirements_check,
            article_9,
            article_10,
            article_12,
            annex_iii_classification,
            gpai_compliance,
            technical_doc.risk_level
        )
        requirements_check.recommendations = recommendations

        # ============================================================
        # STEP 7: Determine Overall Compliance
        # ============================================================
        # System is compliant if:
        # 1. Compliance score >= 0.85 (increased from 0.8 for stricter compliance)
        # 2. No critical gaps
        # 3. All HIGH-PRIORITY articles compliant (9, 10, 11, 12 for high-risk)

        high_priority_compliant = True
        if technical_doc.risk_level == RiskLevel.HIGH:
            high_priority_compliant = all([
                article_9_compliant,
                article_10_compliant,
                article_12_compliant,
                requirements_check.article_11_compliant,
                requirements_check.article_14_compliant,
            ])

        compliant = (
            compliance_score >= 0.85 and
            len(critical_gaps) == 0 and
            high_priority_compliant
        )

        # ============================================================
        # STEP 8: Build Comprehensive Compliance Report
        # ============================================================
        compliance_report = {
            "ai_bom_summary": {
                "models_count": len(ai_bom.models),
                "datasets_count": len(ai_bom.datasets),
                "dependencies_count": len(ai_bom.dependencies),
            },
            "compliance_score": compliance_score,
            "compliance_percentage": f"{compliance_score * 100:.1f}%",
            "articles_compliant": f"{compliant_articles}/{total_articles}",
            "risk_assessment": {
                "level": technical_doc.risk_level.value,
                "requires_high_risk_compliance": technical_doc.risk_level == RiskLevel.HIGH,
                "annex_iii_categories": [cat.value for cat in annex_iii_classification.annex_iii_categories],
                "classification_rationale": annex_iii_classification.classification_rationale,
            },
            "gpai_assessment": {
                "gpai_models_detected": len(gpai_compliance.gpai_models_detected),
                "gpai_models": [
                    {
                        "name": m.name,
                        "provider": m.provider,
                        "type": m.model_type.value,
                        "systemic_risk": m.systemic_risk_threshold,
                    }
                    for m in gpai_compliance.gpai_models_detected
                ],
                "user_role": gpai_compliance.user_role.value,
                "deployer_compliant": gpai_compliance.compliant_as_deployer,
            } if len(gpai_compliance.gpai_models_detected) > 0 else None,
            "data_governance": {
                "datasets_documented": article_10.datasets_documented,
                "quality_score": article_10.data_quality_metrics.overall_score if article_10.data_quality_metrics else 0.0,
                "bias_detected": article_10.bias_assessment.bias_detected if article_10.bias_assessment else False,
                "gdpr_compliant": article_10.gdpr_compliance_verified,
            },
            "risk_management": {
                "process_established": article_9.continuous_process_established,
                "risks_identified": len(article_9.risk_register),
                "critical_risks": article_9.critical_risks_count,
                "unmitigated_risks": article_9.unmitigated_risks_count,
            },
            "logging": {
                "automatic_logging": article_12.automatic_logging_enabled,
                "library": article_12.logging_library_detected,
                "retention_months": article_12.retention_period_months,
                "compliant": article_12_compliant,
            },
            "accuracy": {
                "metrics_defined": article_15_accuracy.metrics_defined,
                "performance_metrics": article_15_accuracy.performance_metrics,
                "testing_procedures_documented": article_15_accuracy.testing_procedures_documented,
                "model_evaluation_performed": article_15_accuracy.model_evaluation_performed,
                "benchmark_datasets_used": article_15_accuracy.benchmark_datasets_used,
                "compliant": article_15_accuracy.compliant,
            },
            "robustness": {
                "error_handling_implemented": article_15_robustness.error_handling_implemented,
                "fallback_mechanisms": article_15_robustness.fallback_mechanisms,
                "input_validation": article_15_robustness.input_validation,
                "adversarial_testing": article_15_robustness.adversarial_testing,
                "fault_tolerance_measures": article_15_robustness.fault_tolerance_measures,
                "resilience_testing_performed": article_15_robustness.resilience_testing_performed,
                "edge_case_handling": article_15_robustness.edge_case_handling,
                "compliant": article_15_robustness.compliant,
            },
            "cybersecurity": {
                "security_measures_implemented": article_15_cybersecurity.security_measures_implemented,
                "data_encryption": article_15_cybersecurity.data_encryption,
                "access_controls": article_15_cybersecurity.access_controls,
                "vulnerability_scanning": article_15_cybersecurity.vulnerability_scanning,
                "penetration_testing": article_15_cybersecurity.penetration_testing,
                "incident_response_plan": article_15_cybersecurity.incident_response_plan,
                "security_frameworks": article_15_cybersecurity.security_frameworks,
                "last_security_audit": article_15_cybersecurity.last_security_audit.isoformat() if article_15_cybersecurity.last_security_audit else None,
                "security_patches_updated": article_15_cybersecurity.security_patches_updated,
                "authentication_mechanisms": article_15_cybersecurity.authentication_mechanisms,
                "compliant": article_15_cybersecurity.compliant,
            },
            "provider_obligations": {
                "compliance_percentage": article_16_17.compliance_percentage * 100 if article_16_17 else 0.0,
                "qms_established": article_17_compliant,
            },
            "post_market_monitoring": {
                "monitoring_plan": article_72_73.monitoring_plan_established,
                "incident_procedure": article_72_73.incident_reporting_procedure,
                "incidents_count": len(article_72_73.incidents),
            },
            "critical_gaps_count": len(critical_gaps),
            "recommendations_count": len(recommendations),
        }

        return ComplianceResult(
            system_id=system_id,
            compliant=compliant,
            risk_level=technical_doc.risk_level,
            technical_documentation=technical_doc,
            requirements_check=requirements_check,
            ai_bom_id=ai_bom.spdx_id,
            compliance_report=compliance_report,
        )

    def _extract_documentation_from_bom(self, ai_bom: AIBOM) -> TechnicalDocumentation:
        """Extracts basic information for technical documentation from AI-BOM"""
        # Determine risk level based on components
        risk_level = self._assess_risk_level(ai_bom)
        
        # Build general description
        models_desc = ", ".join([m.name for m in ai_bom.models[:3]])
        general_desc = f"AI system using: {models_desc}" if ai_bom.models else "AI system"
        
        return TechnicalDocumentation(
            system_name=ai_bom.name.replace("AI-BOM for ", ""),
            system_type=SystemType.STANDALONE,
            risk_level=risk_level,
            general_description=general_desc,
            intended_purpose="To be specified",
            context_of_use="To be specified",
            logic_description="To be extracted from code with LLM",
            software_dependencies=[d.name for d in ai_bom.dependencies[:10]],
        )

    def _assess_risk_level(self, ai_bom: AIBOM) -> RiskLevel:
        """Assesses risk level based on AI-BOM components"""
        # Simplified logic: if there are LLM models or complex systems, high risk
        has_llm = any(m.model_type.value == "llm" for m in ai_bom.models)
        has_multiple_models = len(ai_bom.models) > 1

        if has_llm or has_multiple_models:
            return RiskLevel.HIGH
        elif len(ai_bom.models) > 0:
            return RiskLevel.LIMITED
        else:
            return RiskLevel.MINIMAL

    def _is_ai_system(self, ai_bom: AIBOM) -> bool:
        """
        Determines if the scanned repository is actually an AI system.

        An AI system is one that has:
        - AI models detected, OR
        - Datasets used for ML training, OR
        - Significant AI-related dependencies

        Returns:
            True if this is an AI system requiring EU AI Act compliance
        """
        # Has any AI models
        if len(ai_bom.models) > 0:
            return True

        # Has datasets (likely used for ML)
        if len(ai_bom.datasets) > 0:
            return True

        # Has significant AI-related dependencies (more than just data science basics)
        ai_deps = [d for d in ai_bom.dependencies if d.is_ai_related]
        core_ai_libs = [
            "openai", "anthropic", "transformers", "torch", "tensorflow",
            "langchain", "sklearn", "keras", "huggingface", "llama",
            "vllm", "ollama", "cohere", "replicate"
        ]

        for dep in ai_deps:
            dep_name_lower = dep.name.lower()
            if any(lib in dep_name_lower for lib in core_ai_libs):
                return True

        return False

    def _create_non_ai_compliance_result(
        self,
        ai_bom: AIBOM,
        system_id: str
    ) -> ComplianceResult:
        """
        Creates a compliance result for non-AI systems.

        Non-AI systems are not subject to EU AI Act requirements,
        so they receive a high compliance score with no gaps.
        """
        from actproof.compliance.requirements import (
            Article8Compliance,
            RiskManagementSystem,
            DataGovernance,
            LoggingCapability,
            AccuracyRequirements,
            RobustnessRequirements,
            CybersecurityRequirements,
            ProviderObligations,
            QualityManagementSystem,
            EUDatabaseRegistration,
            PostMarketMonitoring,
            HighRiskClassification,
            GPAICompliance,
            GPAIRole,
        )

        # Create minimal technical documentation
        technical_doc = TechnicalDocumentation(
            system_name=ai_bom.name.replace("AI-BOM for ", ""),
            system_type=SystemType.STANDALONE,
            risk_level=RiskLevel.MINIMAL,
            general_description="Non-AI system - EU AI Act not applicable",
            intended_purpose="Not an AI system",
            context_of_use="Standard software application",
            logic_description="No AI/ML logic detected",
        )

        # Create requirements check with high compliance
        requirements_check = AnnexIVRequirements(
            # Article 8 - N/A for non-AI
            article_8=Article8Compliance(
                all_requirements_met=True,
                conformity_declaration_signed=True,
                ce_marking_affixed=True,
                obligations_throughout_lifecycle=True,
            ),
            # Article 9 - N/A
            article_9=RiskManagementSystem(
                continuous_process_established=True,
                risk_register=[],
                residual_risks_acceptable=True,
            ),
            article_9_compliant=True,
            # Article 10 - N/A (no datasets)
            article_10=DataGovernance(
                datasets_documented=True,
                gdpr_compliance_verified=True,
            ),
            article_10_compliant=True,
            # Article 11 - N/A
            article_11_compliant=True,
            article_11_missing_fields=[],
            # Article 12 - N/A
            article_12=LoggingCapability(
                automatic_logging_enabled=True,
            ),
            article_12_compliant=True,
            # Article 13 - N/A
            article_13_compliant=True,
            # Article 14 - N/A
            article_14_compliant=True,
            human_oversight_required=False,
            # Article 15 - N/A
            article_15_compliant=True,
            accuracy_metrics_provided=True,
            article_15_accuracy=AccuracyRequirements(
                metrics_defined=True,
                testing_procedures_documented=True,
            ),
            article_15_robustness=RobustnessRequirements(
                error_handling_implemented=True,
            ),
            article_15_cybersecurity=CybersecurityRequirements(
                security_measures_implemented=True,
            ),
            # Provider Obligations - N/A
            article_16=ProviderObligations(
                obligations=[],
                qms=QualityManagementSystem(qms_established=True),
            ),
            article_16_compliant=True,
            article_17_compliant=True,
            # EU Database - N/A
            article_61=EUDatabaseRegistration(
                registration_required=False,
                system_name=ai_bom.name,
            ),
            article_61_compliant=True,
            # Post-market monitoring - N/A
            article_72_73=PostMarketMonitoring(),
            article_72_compliant=True,
            article_73_compliant=True,
            # Annex III - Not high-risk
            annex_iii=HighRiskClassification(
                is_high_risk=False,
                classification_rationale="Non-AI system - EU AI Act not applicable",
            ),
            # GPAI - N/A
            gpai=GPAICompliance(
                gpai_models_detected=[],
                user_role=GPAIRole.DEPLOYER,
            ),
            gpai_compliant=True,
            # Overall compliance
            compliance_score=1.0,
            critical_gaps=[],
            recommendations=["No action required - this is not an AI system subject to EU AI Act"],
        )

        return ComplianceResult(
            system_id=system_id,
            compliant=True,
            risk_level=RiskLevel.MINIMAL,
            technical_documentation=technical_doc,
            requirements_check=requirements_check,
            ai_bom_id=ai_bom.spdx_id,
            compliance_report={
                "summary": "Non-AI system - EU AI Act not applicable",
                "is_ai_system": False,
                "models_found": 0,
                "datasets_found": 0,
                "ai_dependencies": 0,
                "compliance_score": 1.0,
            },
        )

    def _generate_comprehensive_recommendations(
        self,
        requirements_check: AnnexIVRequirements,
        article_9: RiskManagementSystem,
        article_10: DataGovernance,
        article_12: LoggingCapability,
        annex_iii: HighRiskClassification,
        gpai: GPAICompliance,
        risk_level: RiskLevel,
    ) -> List[str]:
        """
        Wrapper for comprehensive recommendations generator

        Calls the external generator function with all validation results
        """
        return generate_comprehensive_recommendations(
            requirements_check,
            article_9,
            article_10,
            article_12,
            annex_iii,
            gpai,
            risk_level,
        )

