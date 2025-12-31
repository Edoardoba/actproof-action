"""
Extension methods for PolicyEngine - Comprehensive Recommendations Generator
This file contains helper methods for the extended PolicyEngine
"""

from typing import List
from actproof.compliance.requirements import (
    AnnexIVRequirements,
    RiskManagementSystem,
    DataGovernance,
    LoggingCapability,
    HighRiskClassification,
    GPAICompliance,
    RiskLevel,
    AnnexIIICategory,
)


def generate_comprehensive_recommendations(
    requirements_check: AnnexIVRequirements,
    article_9: RiskManagementSystem,
    article_10: DataGovernance,
    article_12: LoggingCapability,
    annex_iii: HighRiskClassification,
    gpai: GPAICompliance,
    risk_level: RiskLevel,
) -> List[str]:
    """
    Generate comprehensive recommendations covering ALL articles and annexes

    Args:
        requirements_check: AnnexIVRequirements with all validations
        article_9: Risk Management System validation
        article_10: Data Governance validation
        article_12: Logging capability validation
        annex_iii: High-Risk classification
        gpai: GPAI compliance validation
        risk_level: System risk level

    Returns:
        List of prioritized recommendations
    """
    recommendations = []

    # PRIORITY 1: CRITICAL GAPS (Must-Fix)
    if not article_10.compliant:
        recommendations.append(
            "🔴 CRITICAL: Implement Data Governance framework (Article 10) - "
            "Document dataset quality, assess bias, establish data lineage"
        )

    if not article_9.compliant:
        recommendations.append(
            "🔴 CRITICAL: Establish Risk Management System (Article 9) - "
            f"Create risk register (currently {len(article_9.risk_register)} risks identified), "
            "implement mitigation measures, perform periodic reviews"
        )

    if not article_12.compliant:
        recommendations.append(
            "🔴 CRITICAL: Implement automatic logging system (Article 12) - "
            f"{'Install logging library, ' if not article_12.automatic_logging_enabled else ''}"
            f"{'Set retention period (minimum 6 months), ' if not article_12.retention_period_months else ''}"
            "ensure immutable audit trail, log input/output/decisions/timestamp"
        )

    if not requirements_check.article_11_compliant:
        missing = ", ".join(requirements_check.article_11_missing_fields[:3])
        recommendations.append(
            f"🔴 CRITICAL: Complete Technical Documentation (Article 11) - "
            f"Missing fields: {missing}..."
        )

    if risk_level == RiskLevel.HIGH and not requirements_check.article_14_compliant:
        recommendations.append(
            "🔴 CRITICAL: Implement Human Oversight measures (Article 14) - "
            "Define oversight procedures, assign oversight roles, "
            "implement intervention mechanisms for HIGH-RISK system"
        )

    # PRIORITY 2: HIGH-RISK SPECIFIC REQUIREMENTS
    if risk_level == RiskLevel.HIGH:
        if requirements_check.article_61 and not requirements_check.article_61.registration_completed:
            recommendations.append(
                "🟠 HIGH PRIORITY: Register system in EU Database (Article 61) - "
                "Required for all HIGH-RISK AI systems before market placement"
            )

        if requirements_check.article_72_73 and not requirements_check.article_72_73.monitoring_plan_established:
            recommendations.append(
                "🟠 HIGH PRIORITY: Establish Post-Market Monitoring plan (Article 72) - "
                "Define monitoring procedures, set review frequency, establish feedback mechanisms"
            )

        if requirements_check.article_16_17 and not requirements_check.article_17_compliant:
            recommendations.append(
                "🟠 HIGH PRIORITY: Establish Quality Management System (Article 17) - "
                "Implement QMS according to Annex VI requirements: compliance strategy, "
                "design controls, testing procedures, change management"
            )

    # PRIORITY 3: ANNEX III CLASSIFICATION
    if annex_iii.is_high_risk and annex_iii.annex_iii_categories:
        category_name = annex_iii.annex_iii_categories[0].value.replace("_", " ").title()
        recommendations.append(
            f"🟠 HIGH-RISK CLASSIFICATION: System classified as '{category_name}' (Annex III) - "
            f"{annex_iii.classification_rationale[:100]}... "
            "Ensure compliance with category-specific requirements"
        )

        # Add category-specific recommendations
        if annex_iii.additional_requirements:
            for req in annex_iii.additional_requirements[:2]:
                recommendations.append(f"   └─ {req}")

    # PRIORITY 4: GPAI REQUIREMENTS
    if len(gpai.gpai_models_detected) > 0:
        gpai_names = ", ".join([m.name for m in gpai.gpai_models_detected[:3]])

        if not gpai.transparency_info_users:
            recommendations.append(
                f"🟡 GPAI: Inform users about AI usage (Article 52 / Annex XII) - "
                f"Detected GPAI models: {gpai_names}. Users must be informed they're interacting with AI"
            )

        if not gpai.ai_generated_content_disclosed:
            recommendations.append(
                "🟡 GPAI: Disclose AI-generated content (Article 52) - "
                "Mark all AI-generated text, images, audio, video as AI-generated"
            )

        if not gpai.intended_use_documented:
            recommendations.append(
                "🟡 GPAI: Document intended use case (Deployer obligation) - "
                "Clearly document how GPAI models are used in your specific context"
            )

        if not gpai.downstream_risk_assessment:
            recommendations.append(
                "🟡 GPAI: Perform downstream risk assessment (Deployer obligation) - "
                "Assess risks specific to your use case of GPAI models"
            )

        # Systemic risk warning
        if any(m.systemic_risk_threshold for m in gpai.gpai_models_detected):
            recommendations.append(
                "⚠️  GPAI SYSTEMIC RISK: One or more GPAI models may exceed 10^25 FLOPs threshold - "
                "Additional Annex XIII requirements may apply. Verify with provider"
            )

    # PRIORITY 5: DATA GOVERNANCE SPECIFICS
    if article_10.data_quality_metrics and article_10.data_quality_metrics.overall_score < 0.7:
        recommendations.append(
            f"🟡 DATA QUALITY: Improve dataset documentation (Article 10) - "
            f"Current quality score: {article_10.data_quality_metrics.overall_score:.1%}. "
            "Document dataset source, size, license, metadata"
        )

    if article_10.bias_assessment and article_10.bias_assessment.bias_detected:
        categories = ", ".join(article_10.bias_assessment.bias_categories)
        recommendations.append(
            f"🟡 BIAS DETECTED: Implement bias mitigation (Article 10) - "
            f"Bias categories detected: {categories}. "
            "Perform fairness audit, implement mitigation measures"
        )

    if not article_10.representativeness_assessed:
        recommendations.append(
            "🟡 DATA REPRESENTATIVENESS: Assess dataset representativeness (Article 10) - "
            "Verify datasets are representative of target population"
        )

    # PRIORITY 6: RISK MANAGEMENT SPECIFICS
    if article_9.critical_risks_count > 0:
        recommendations.append(
            f"🟡 CRITICAL RISKS: Mitigate {article_9.critical_risks_count} critical risk(s) (Article 9) - "
            "Address all CRITICAL severity risks before deployment"
        )

    if article_9.unmitigated_risks_count > 0:
        recommendations.append(
            f"🟡 RISK MITIGATION: Address {article_9.unmitigated_risks_count} unmitigated risk(s) (Article 9) - "
            "Implement mitigation measures for all identified risks"
        )

    # PRIORITY 7: ACCURACY & ROBUSTNESS
    if not requirements_check.article_15_compliant:
        recommendations.append(
            "🟡 METRICS: Provide quantitative accuracy metrics (Article 15) - "
            "Document accuracy, robustness, and cybersecurity metrics. "
            "Include: precision, recall, F1-score, adversarial robustness, security assessments"
        )

    # PRIORITY 8: TRANSPARENCY
    if not requirements_check.article_13_compliant:
        recommendations.append(
            "🟡 TRANSPARENCY: Implement transparency measures (Article 13) - "
            "Provide clear instructions for use, document limitations, "
            "inform users about AI system capabilities"
        )

    # PRIORITY 9: PROVIDER OBLIGATIONS
    if requirements_check.article_16_17:
        compliance_pct = requirements_check.article_16_17.compliance_percentage * 100
        if compliance_pct < 80:
            recommendations.append(
                f"🟡 PROVIDER OBLIGATIONS: Complete provider obligations (Article 16) - "
                f"Current: {compliance_pct:.0f}% compliant. "
                "Review Article 16 checklist and complete missing obligations"
            )

    # PRIORITY 10: INCIDENT REPORTING
    if requirements_check.article_72_73:
        if not requirements_check.article_72_73.incident_reporting_procedure:
            recommendations.append(
                "🟢 INCIDENT MANAGEMENT: Define incident reporting procedure (Article 73) - "
                "Establish process for identifying, reporting, and managing incidents"
            )

        if not requirements_check.article_72_73.incident_contact_designated:
            recommendations.append(
                "🟢 INCIDENT CONTACT: Designate incident reporting contact (Article 73) - "
                "Assign responsible person/team for handling serious incidents"
            )

    # PRIORITY 11: GENERAL IMPROVEMENTS
    if len(recommendations) < 3:  # System is relatively compliant
        recommendations.append(
            "✅ GOOD PROGRESS: System shows strong compliance foundation. "
            "Focus on documentation completeness and continuous monitoring"
        )

    # Limit to top 15 recommendations to avoid overwhelming users
    return recommendations[:15]
