"""
Schemi Pydantic per requisiti EU AI Act - Allegato IV
Traduzione dei requisiti legali in schemi di validazione
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Livelli di rischio AI Act"""
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    PROHIBITED = "prohibited"


class SystemType(str, Enum):
    """Tipi di sistema AI"""
    STANDALONE = "standalone"
    COMPONENT = "component"
    PRODUCT = "product"


class TechnicalDocumentation(BaseModel):
    """
    Documentazione Tecnica conforme all'Allegato IV dell'EU AI Act
    Articolo 11 - Requisiti per sistemi ad alto rischio
    """
    
    # Identificazione Sistema
    system_name: str = Field(..., description="Nome del sistema AI")
    system_version: Optional[str] = Field(None, description="Versione del sistema")
    system_type: SystemType = Field(..., description="Tipo di sistema")
    risk_level: RiskLevel = Field(..., description="Livello di rischio classificato")
    
    # Descrizione Generale (Articolo 11, punto a)
    general_description: str = Field(
        ...,
        description="Descrizione generale del sistema AI, incluso scopo e contesto d'uso"
    )
    intended_purpose: str = Field(
        ...,
        description="Scopo previsto del sistema AI e benefici attesi"
    )
    context_of_use: str = Field(
        ...,
        description="Contesto d'uso, inclusi utenti finali e condizioni operative"
    )
    
    # Descrizione Logica e Dati (Articolo 11, punto b)
    logic_description: str = Field(
        ...,
        description="Descrizione della logica del sistema AI e dei suoi algoritmi"
    )
    training_data_description: Optional[str] = Field(
        None,
        description="Descrizione dei dati di addestramento utilizzati"
    )
    data_preprocessing: Optional[str] = Field(
        None,
        description="Metodi di preprocessamento dei dati"
    )
    
    # Specifiche Tecniche (Articolo 11, punto c)
    technical_specifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Specifiche tecniche del sistema"
    )
    hardware_requirements: Optional[str] = Field(
        None,
        description="Requisiti hardware"
    )
    software_dependencies: List[str] = Field(
        default_factory=list,
        description="Dipendenze software"
    )
    
    # Metriche di Accuratezza (Articolo 11, punto d)
    accuracy_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Metriche di accuratezza, robustezza e cybersecurity"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metriche di performance"
    )
    
    # Gestione Rischi (Articolo 11, punto e)
    risk_management: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sistema di gestione dei rischi"
    )
    identified_risks: List[str] = Field(
        default_factory=list,
        description="Rischi identificati"
    )
    mitigation_measures: List[str] = Field(
        default_factory=list,
        description="Misure di mitigazione implementate"
    )
    
    # Human Oversight (Articolo 14)
    human_oversight: Optional[Dict[str, Any]] = Field(
        None,
        description="Piano di supervisione umana"
    )
    oversight_measures: List[str] = Field(
        default_factory=list,
        description="Misure di supervisione umana"
    )
    
    # Trasparenza e Informazione Utenti (Articolo 13)
    transparency_measures: List[str] = Field(
        default_factory=list,
        description="Misure di trasparenza implementate"
    )
    user_information: Optional[str] = Field(
        None,
        description="Informazioni fornite agli utenti"
    )
    
    # Conformità GDPR (se applicabile)
    gdpr_compliance: Optional[Dict[str, Any]] = Field(
        None,
        description="Informazioni sulla conformità GDPR"
    )
    data_protection_measures: List[str] = Field(
        default_factory=list,
        description="Misure di protezione dati"
    )
    
    # Metadati
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Creatore del documento")
    
    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: RiskLevel) -> RiskLevel:
        """Valida che sistemi ad alto rischio abbiano documentazione completa"""
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_name": "Sistema di Recruiting AI",
                "system_type": "standalone",
                "risk_level": "high",
                "general_description": "Sistema AI per screening CV",
                "intended_purpose": "Assistenza nella selezione candidati",
            }
        }


class AnnexIVRequirements(BaseModel):
    """
    Requisiti specifici dell'Allegato IV dell'EU AI Act
    Mappatura completa dei requisiti per documentazione tecnica
    """
    
    # Articolo 11 - Requisiti per sistemi ad alto rischio
    article_11_compliant: bool = Field(default=False, description="Conformità Articolo 11")
    article_11_missing_fields: List[str] = Field(
        default_factory=list,
        description="Campi mancanti per conformità Articolo 11"
    )
    
    # Articolo 13 - Trasparenza
    article_13_compliant: bool = Field(default=False, description="Conformità Articolo 13")
    
    # Articolo 14 - Human Oversight
    article_14_compliant: bool = Field(default=False, description="Conformità Articolo 14")
    human_oversight_required: bool = Field(default=True, description="Supervisione umana richiesta")
    
    # Articolo 15 - Accuratezza, Robustezza, Cybersecurity
    article_15_compliant: bool = Field(default=False, description="Conformità Articolo 15")
    accuracy_metrics_provided: bool = Field(default=False, description="Metriche accuratezza fornite")
    
    # ISO/IEC 42001 Requirements
    iso_42001_compliant: bool = Field(default=False, description="Conformità ISO/IEC 42001")
    management_system_established: bool = Field(
        default=False,
        description="Sistema di gestione AI stabilito"
    )
    
    # Dettagli conformità
    compliance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score di conformità (0-1)"
    )
    critical_gaps: List[str] = Field(
        default_factory=list,
        description="Lacune critiche da risolvere"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Raccomandazioni per migliorare conformità"
    )


# ============================================================================
# NEW: Article 10 - Data Governance
# ============================================================================

class DataQualityMetrics(BaseModel):
    """Metriche qualità dataset (Article 10)"""
    completeness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Completezza dati (0-1)")
    consistency: Optional[float] = Field(None, ge=0.0, le=1.0, description="Consistenza dati (0-1)")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuratezza dati (0-1)")
    timeliness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Attualità dati (0-1)")
    overall_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score complessivo qualità")


class BiasAssessment(BaseModel):
    """Valutazione bias nei dataset (Article 10)"""
    demographic_parity: Optional[float] = Field(None, description="Demographic parity score")
    equal_opportunity: Optional[float] = Field(None, description="Equal opportunity score")
    disparate_impact: Optional[float] = Field(None, description="Disparate impact ratio")
    bias_detected: bool = Field(False, description="Se è stato rilevato bias significativo")
    bias_categories: List[str] = Field(default_factory=list, description="Categorie di bias rilevate")
    mitigation_measures: List[str] = Field(default_factory=list, description="Misure mitigazione bias")


class DataLineage(BaseModel):
    """Tracciabilità origine dati (Article 10)"""
    source: Optional[str] = Field(None, description="Origine dati")
    collection_date: Optional[datetime] = Field(None, description="Data raccolta")
    collection_method: Optional[str] = Field(None, description="Metodo raccolta")
    processing_steps: List[str] = Field(default_factory=list, description="Steps di processing")
    transformations: List[str] = Field(default_factory=list, description="Trasformazioni applicate")
    data_owners: List[str] = Field(default_factory=list, description="Proprietari/custodi dati")


class DataGovernance(BaseModel):
    """Data Governance compliance (Article 10)"""
    datasets_documented: bool = Field(False, description="Tutti i dataset sono documentati")
    data_quality_metrics: Optional[DataQualityMetrics] = Field(None, description="Metriche qualità")
    bias_assessment: Optional[BiasAssessment] = Field(None, description="Valutazione bias")
    data_lineage: Optional[DataLineage] = Field(None, description="Tracciabilità dati")
    data_relevance_documented: bool = Field(False, description="Rilevanza dati per intended purpose documentata")
    representativeness_assessed: bool = Field(False, description="Rappresentatività dataset valutata")
    gdpr_compliance_verified: bool = Field(False, description="Conformità GDPR verificata")
    data_governance_policies: List[str] = Field(default_factory=list, description="Policy data governance")

    @property
    def compliant(self) -> bool:
        """Check se data governance è compliant"""
        return (
            self.datasets_documented and
            self.data_relevance_documented and
            self.representativeness_assessed and
            self.gdpr_compliance_verified
        )


# ============================================================================
# NEW: Article 9 - Risk Management System
# ============================================================================

class RiskCategory(str, Enum):
    """Categorie di rischio"""
    FUNDAMENTAL_RIGHTS = "fundamental_rights"
    HEALTH_SAFETY = "health_safety"
    BIAS_DISCRIMINATION = "bias_discrimination"
    CYBERSECURITY = "cybersecurity"
    DATA_PRIVACY = "data_privacy"
    TRANSPARENCY = "transparency"
    ENVIRONMENTAL = "environmental"
    OTHER = "other"


class RiskSeverity(str, Enum):
    """Severità rischio"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class RiskLikelihood(str, Enum):
    """Probabilità rischio"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class RiskStatus(str, Enum):
    """Stato rischio"""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    TRANSFERRED = "transferred"
    AVOIDED = "avoided"


class Risk(BaseModel):
    """Singolo rischio identificato (Article 9)"""
    risk_id: str = Field(..., description="ID univoco rischio")
    title: str = Field(..., description="Titolo rischio")
    description: str = Field(..., description="Descrizione dettagliata")
    category: RiskCategory = Field(..., description="Categoria rischio")
    severity: RiskSeverity = Field(..., description="Severità impatto")
    likelihood: RiskLikelihood = Field(..., description="Probabilità occorrenza")
    affected_stakeholders: List[str] = Field(default_factory=list, description="Stakeholder affetti")
    mitigation_measures: List[str] = Field(default_factory=list, description="Misure mitigazione")
    residual_severity: Optional[RiskSeverity] = Field(None, description="Severità residua post-mitigazione")
    residual_likelihood: Optional[RiskLikelihood] = Field(None, description="Probabilità residua")
    status: RiskStatus = Field(default=RiskStatus.IDENTIFIED, description="Stato corrente")
    owner: Optional[str] = Field(None, description="Responsabile gestione rischio")
    target_date: Optional[datetime] = Field(None, description="Data target risoluzione")
    identified_at: datetime = Field(default_factory=datetime.utcnow, description="Data identificazione")

    @property
    def risk_score(self) -> int:
        """Calcola risk score (1-25)"""
        severity_scores = {"critical": 5, "high": 4, "medium": 3, "low": 2, "negligible": 1}
        likelihood_scores = {"very_high": 5, "high": 4, "medium": 3, "low": 2, "very_low": 1}
        return severity_scores[self.severity.value] * likelihood_scores[self.likelihood.value]


class RiskManagementSystem(BaseModel):
    """Sistema gestione rischi (Article 9)"""
    continuous_process_established: bool = Field(False, description="Processo continuo stabilito")
    risk_register: List[Risk] = Field(default_factory=list, description="Registro rischi")
    risk_assessment_methodology: Optional[str] = Field(None, description="Metodologia valutazione rischi")
    residual_risks_acceptable: bool = Field(False, description="Rischi residui accettabili")
    periodic_review_frequency: Optional[str] = Field(None, description="Frequenza review periodica")
    last_review_date: Optional[datetime] = Field(None, description="Data ultima review")
    next_review_date: Optional[datetime] = Field(None, description="Data prossima review")

    @property
    def critical_risks_count(self) -> int:
        """Conta rischi critici"""
        return len([r for r in self.risk_register if r.severity == RiskSeverity.CRITICAL])

    @property
    def unmitigated_risks_count(self) -> int:
        """Conta rischi non mitigati"""
        return len([r for r in self.risk_register if r.status == RiskStatus.IDENTIFIED])

    @property
    def compliant(self) -> bool:
        """Check se risk management è compliant"""
        return (
            self.continuous_process_established and
            len(self.risk_register) > 0 and
            self.critical_risks_count == 0 and
            self.residual_risks_acceptable
        )


# ============================================================================
# NEW: Article 12 - Record-Keeping & Logging
# ============================================================================

class LoggingCapability(BaseModel):
    """Capacità di logging del sistema (Article 12)"""
    automatic_logging_enabled: bool = Field(False, description="Logging automatico abilitato")
    logging_library_detected: Optional[str] = Field(None, description="Libreria logging rilevata")
    retention_period_months: Optional[int] = Field(None, ge=6, description="Periodo retention (minimo 6 mesi)")
    audit_trail_immutable: bool = Field(False, description="Audit trail immutabile")
    events_logged: List[str] = Field(default_factory=list, description="Eventi loggati")
    log_storage_location: Optional[str] = Field(None, description="Location storage log")
    log_format: Optional[str] = Field(None, description="Formato log (JSON, structured, etc.)")
    access_control_implemented: bool = Field(False, description="Controllo accesso log implementato")

    @property
    def compliant(self) -> bool:
        """Check se logging è compliant"""
        required_events = ["input_data", "output_data", "decisions", "timestamp"]
        has_required_events = all(e in self.events_logged for e in required_events)
        return (
            self.automatic_logging_enabled and
            (self.retention_period_months or 0) >= 6 and
            self.audit_trail_immutable and
            has_required_events
        )


# ============================================================================
# NEW: Annex III - High-Risk AI System Classification
# ============================================================================

class AnnexIIICategory(str, Enum):
    """8 categorie sistemi alto rischio Annex III"""
    BIOMETRIC = "biometric_identification_categorization"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION = "education_vocational_training"
    EMPLOYMENT = "employment_workers_management"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION_ASYLUM = "migration_asylum_border"
    JUSTICE_DEMOCRACY = "justice_democratic_processes"
    NONE = "none"


class HighRiskClassification(BaseModel):
    """Classificazione high-risk secondo Annex III"""
    is_high_risk: bool = Field(False, description="Sistema è high-risk")
    annex_iii_categories: List[AnnexIIICategory] = Field(
        default_factory=list,
        description="Categorie Annex III applicabili"
    )
    classification_rationale: str = Field(
        default="",
        description="Spiegazione classificazione"
    )
    keywords_detected: List[str] = Field(
        default_factory=list,
        description="Keywords rilevate per classificazione"
    )
    additional_requirements: List[str] = Field(
        default_factory=list,
        description="Requisiti aggiuntivi per categoria"
    )
    notified_body_required: bool = Field(
        False,
        description="Richiesta valutazione notified body"
    )


# ============================================================================
# NEW: Annex X-XIII - GPAI (General Purpose AI) Requirements
# ============================================================================

class GPAIModelType(str, Enum):
    """Tipi di modelli GPAI"""
    LLM = "large_language_model"
    VISION = "vision_model"
    MULTIMODAL = "multimodal_model"
    EMBEDDING = "embedding_model"
    CODE_GENERATION = "code_generation"
    OTHER = "other"


class GPAIRole(str, Enum):
    """Ruolo nell'ecosistema GPAI"""
    PROVIDER = "provider"  # Chi sviluppa il modello GPAI
    DEPLOYER = "deployer"  # Chi usa il modello GPAI in un sistema
    BOTH = "both"


class GPAIModel(BaseModel):
    """Modello GPAI rilevato"""
    name: str = Field(..., description="Nome modello (es. gpt-4, claude-3)")
    provider: str = Field(..., description="Provider (OpenAI, Anthropic, etc.)")
    model_type: GPAIModelType = Field(..., description="Tipo modello GPAI")
    version: Optional[str] = Field(None, description="Versione modello")
    api_endpoint: Optional[str] = Field(None, description="Endpoint API")
    estimated_flops: Optional[float] = Field(None, description="FLOPs stimati (per systemic risk)")
    systemic_risk_threshold: bool = Field(False, description="Supera soglia rischio sistemico (10^25 FLOPS)")


class GPAICompliance(BaseModel):
    """Compliance GPAI secondo Annex X-XIII"""
    gpai_models_detected: List[GPAIModel] = Field(default_factory=list, description="Modelli GPAI rilevati")
    user_role: GPAIRole = Field(default=GPAIRole.DEPLOYER, description="Ruolo utente (provider/deployer)")

    # Annex XI - Technical Documentation (for providers)
    technical_doc_provided: bool = Field(False, description="Documentazione tecnica fornita (Art. 53)")

    # Annex XII - Transparency Obligations
    transparency_info_users: bool = Field(False, description="Utenti informati uso AI (Art. 52)")
    ai_generated_content_disclosed: bool = Field(False, description="Contenuto AI-generated dichiarato")

    # Annex XIII - Systemic Risk (for high-impact GPAI)
    systemic_risk_assessment_required: bool = Field(False, description="Valutazione rischio sistemico richiesta")
    systemic_risk_assessment_performed: bool = Field(False, description="Valutazione rischio sistemico eseguita")
    code_of_practice_compliant: bool = Field(False, description="Conforme Code of Practice GPAI")

    # Deployer-specific obligations
    upstream_provider_compliance_verified: bool = Field(
        False,
        description="Conformità provider upstream verificata"
    )
    intended_use_documented: bool = Field(False, description="Intended use case documentato")
    downstream_risk_assessment: bool = Field(False, description="Risk assessment downstream eseguito")

    @property
    def compliant_as_deployer(self) -> bool:
        """Check compliance come deployer GPAI"""
        return (
            self.transparency_info_users and
            self.ai_generated_content_disclosed and
            self.upstream_provider_compliance_verified and
            self.intended_use_documented and
            self.downstream_risk_assessment
        )


# ============================================================================
# NEW: Article 16-17 - Provider Obligations & QMS
# ============================================================================

class ProviderObligation(BaseModel):
    """Singolo obbligo provider (Article 16)"""
    obligation_id: str = Field(..., description="ID obbligo")
    description: str = Field(..., description="Descrizione obbligo")
    article_reference: str = Field(..., description="Riferimento articolo")
    compliant: bool = Field(False, description="Obbligo soddisfatto")
    evidence: Optional[str] = Field(None, description="Evidenza conformità")


class QualityManagementSystem(BaseModel):
    """Quality Management System secondo Annex VI (Article 17)"""
    qms_established: bool = Field(False, description="QMS stabilito")

    # Annex VI requirements
    compliance_management_strategy: bool = Field(False, description="Strategia compliance management")
    design_development_control: bool = Field(False, description="Controllo design & development")
    testing_validation_procedures: bool = Field(False, description="Procedure testing & validation")
    post_market_monitoring_plan: bool = Field(False, description="Piano post-market monitoring")
    change_management_procedure: bool = Field(False, description="Procedura change management")
    documentation_maintenance: bool = Field(False, description="Mantenimento documentazione")
    corrective_preventive_actions: bool = Field(False, description="Azioni correttive/preventive")

    iso_42001_compliant: bool = Field(False, description="Conforme ISO/IEC 42001")
    last_audit_date: Optional[datetime] = Field(None, description="Data ultimo audit")
    next_audit_date: Optional[datetime] = Field(None, description="Data prossimo audit")

    @property
    def compliant(self) -> bool:
        """Check se QMS è compliant"""
        return (
            self.qms_established and
            self.compliance_management_strategy and
            self.design_development_control and
            self.testing_validation_procedures and
            self.post_market_monitoring_plan and
            self.change_management_procedure
        )


class ProviderObligations(BaseModel):
    """Obblighi provider (Article 16-17)"""
    obligations: List[ProviderObligation] = Field(default_factory=list, description="Lista obblighi")
    qms: Optional[QualityManagementSystem] = Field(None, description="Quality Management System")
    conformity_assessment_completed: bool = Field(False, description="Conformity assessment completata")
    technical_documentation_maintained: bool = Field(False, description="Documentazione tecnica mantenuta")
    automatic_logging_enabled: bool = Field(False, description="Logging automatico abilitato")
    instructions_for_use_provided: bool = Field(False, description="Istruzioni d'uso fornite")
    corrective_actions_for_nonconformance: bool = Field(
        False,
        description="Azioni correttive per non-conformità"
    )

    @property
    def compliance_percentage(self) -> float:
        """Percentuale obblighi soddisfatti"""
        if not self.obligations:
            return 0.0
        compliant_count = len([o for o in self.obligations if o.compliant])
        return compliant_count / len(self.obligations)


# ============================================================================
# NEW: Article 61 - EU Database Registration
# ============================================================================

class EUDatabaseRegistration(BaseModel):
    """Registrazione database EU (Article 61)"""
    registration_required: bool = Field(False, description="Registrazione richiesta")
    registration_completed: bool = Field(False, description="Registrazione completata")
    registration_id: Optional[str] = Field(None, description="ID registrazione EU database")
    registration_date: Optional[datetime] = Field(None, description="Data registrazione")

    # Informazioni richieste per registrazione
    provider_name: Optional[str] = Field(None, description="Nome provider")
    provider_contact: Optional[str] = Field(None, description="Contatto provider")
    system_name: Optional[str] = Field(None, description="Nome sistema")
    system_version: Optional[str] = Field(None, description="Versione sistema")
    intended_purpose: Optional[str] = Field(None, description="Intended purpose")
    conformity_assessment_procedure: Optional[str] = Field(None, description="Procedura conformity assessment")
    notified_body: Optional[str] = Field(None, description="Notified body (se applicabile)")

    @property
    def compliant(self) -> bool:
        """Check se registrazione è compliant"""
        if not self.registration_required:
            return True
        return self.registration_completed and self.registration_id is not None


# ============================================================================
# NEW: Article 72-73 - Post-Market Monitoring & Incident Reporting
# ============================================================================

class IncidentSeverity(str, Enum):
    """Severità incident"""
    SERIOUS = "serious"  # Richiede reporting autorità
    MODERATE = "moderate"
    MINOR = "minor"


class Incident(BaseModel):
    """Incident rilevato (Article 73)"""
    incident_id: str = Field(..., description="ID incident")
    title: str = Field(..., description="Titolo incident")
    description: str = Field(..., description="Descrizione dettagliata")
    severity: IncidentSeverity = Field(..., description="Severità")
    occurred_at: datetime = Field(..., description="Data/ora occorrenza")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Data/ora rilevamento")
    reported_to_authorities: bool = Field(False, description="Reportato ad autorità")
    root_cause: Optional[str] = Field(None, description="Root cause")
    corrective_actions: List[str] = Field(default_factory=list, description="Azioni correttive")
    preventive_actions: List[str] = Field(default_factory=list, description="Azioni preventive")
    resolved: bool = Field(False, description="Risolto")
    resolved_at: Optional[datetime] = Field(None, description="Data risoluzione")


class PostMarketMonitoring(BaseModel):
    """Post-market monitoring (Article 72)"""
    monitoring_plan_established: bool = Field(False, description="Piano monitoring stabilito")
    monitoring_frequency: Optional[str] = Field(None, description="Frequenza monitoring")

    # Incident reporting (Article 73)
    incident_reporting_procedure: bool = Field(False, description="Procedura reporting incident definita")
    incident_contact_designated: bool = Field(False, description="Contatto incident designato")
    incident_contact_email: Optional[str] = Field(None, description="Email contatto incident")
    incidents: List[Incident] = Field(default_factory=list, description="Incidents rilevati")
    serious_incidents_count: int = Field(0, description="Numero serious incidents")

    # User feedback
    user_feedback_collection: bool = Field(False, description="Raccolta feedback utenti")
    user_feedback_analysis: bool = Field(False, description="Analisi feedback utenti")

    # Corrective/Preventive Actions (Article 20-21)
    corrective_actions_procedure: bool = Field(False, description="Procedura azioni correttive")
    preventive_actions_procedure: bool = Field(False, description="Procedura azioni preventive")

    @property
    def compliant(self) -> bool:
        """Check se post-market monitoring è compliant"""
        return (
            self.monitoring_plan_established and
            self.incident_reporting_procedure and
            self.incident_contact_designated and
            self.corrective_actions_procedure
        )


# ============================================================================
# NEW: Article 8 - Compliance with Requirements
# ============================================================================

class Article8Compliance(BaseModel):
    """Compliance with requirements (Article 8)"""
    all_requirements_met: bool = Field(False, description="Tutti i requisiti soddisfatti")
    conformity_declaration_signed: bool = Field(False, description="Dichiarazione conformità firmata")
    ce_marking_affixed: bool = Field(False, description="Marcatura CE apposta")
    obligations_throughout_lifecycle: bool = Field(
        False,
        description="Obblighi durante tutto il lifecycle"
    )

    @property
    def compliant(self) -> bool:
        """Check Article 8 compliance"""
        return self.all_requirements_met and self.conformity_declaration_signed


# ============================================================================
# Article 15: Accuracy, Robustness, Cybersecurity (Separate Models)
# ============================================================================

class AccuracyRequirements(BaseModel):
    """
    Article 15 - Accuracy Requirements
    Separated from Article15 for better granularity
    """
    metrics_defined: bool = Field(default=False, description="Accuracy metrics defined")
    performance_metrics: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Performance metrics (precision, recall, F1, etc.)"
    )
    testing_procedures_documented: bool = Field(
        default=False,
        description="Testing procedures documented"
    )
    model_evaluation_performed: bool = Field(
        default=False,
        description="Model evaluation performed"
    )
    benchmark_datasets_used: List[str] = Field(
        default_factory=list,
        description="Benchmark datasets used for evaluation"
    )

    @property
    def compliant(self) -> bool:
        """Check if accuracy requirements are met"""
        return (
            self.metrics_defined and
            self.testing_procedures_documented and
            self.model_evaluation_performed
        )


class RobustnessRequirements(BaseModel):
    """
    Article 15 - Robustness & Resilience Requirements
    Separated from Article15 for better granularity
    """
    error_handling_implemented: bool = Field(
        default=False,
        description="Error handling implemented"
    )
    fallback_mechanisms: bool = Field(
        default=False,
        description="Fallback mechanisms available"
    )
    input_validation: bool = Field(
        default=False,
        description="Input validation implemented"
    )
    adversarial_testing: bool = Field(
        default=False,
        description="Adversarial testing conducted"
    )
    fault_tolerance_measures: List[str] = Field(
        default_factory=list,
        description="Fault tolerance measures implemented"
    )
    resilience_testing_performed: bool = Field(
        default=False,
        description="Resilience testing performed"
    )
    edge_case_handling: bool = Field(
        default=False,
        description="Edge case handling implemented"
    )

    @property
    def compliant(self) -> bool:
        """Check if robustness requirements are met"""
        return (
            self.error_handling_implemented and
            self.fallback_mechanisms and
            self.input_validation and
            len(self.fault_tolerance_measures) > 0
        )


class CybersecurityRequirements(BaseModel):
    """
    Article 15 - Cybersecurity Requirements
    Separated from Article15 for better granularity
    """
    security_measures_implemented: bool = Field(
        default=False,
        description="Security measures implemented"
    )
    data_encryption: bool = Field(
        default=False,
        description="Data encryption in transit and at rest"
    )
    access_controls: bool = Field(
        default=False,
        description="Access controls implemented"
    )
    vulnerability_scanning: bool = Field(
        default=False,
        description="Vulnerability scanning performed"
    )
    penetration_testing: bool = Field(
        default=False,
        description="Penetration testing conducted"
    )
    incident_response_plan: bool = Field(
        default=False,
        description="Incident response plan documented"
    )
    security_frameworks: List[str] = Field(
        default_factory=list,
        description="Security frameworks used (ISO 27001, NIST, SOC2, etc.)"
    )
    last_security_audit: Optional[datetime] = Field(
        None,
        description="Last security audit date"
    )
    security_patches_updated: bool = Field(
        default=False,
        description="Security patches regularly updated"
    )
    authentication_mechanisms: List[str] = Field(
        default_factory=list,
        description="Authentication mechanisms (MFA, OAuth, etc.)"
    )

    @property
    def compliant(self) -> bool:
        """Check if cybersecurity requirements are met"""
        return (
            self.security_measures_implemented and
            self.data_encryption and
            self.access_controls and
            self.incident_response_plan and
            len(self.security_frameworks) > 0
        )


# ============================================================================
# EXTENDED: AnnexIVRequirements - Now includes ALL articles
# ============================================================================

class AnnexIVRequirements(BaseModel):
    """
    Requisiti specifici dell'Allegato IV dell'EU AI Act
    EXTENDED: Ora include TUTTI gli articoli rilevanti
    """

    # EXISTING: Articoli base (11, 13, 14, 15)
    article_11_compliant: bool = Field(default=False, description="Conformità Articolo 11")
    article_11_missing_fields: List[str] = Field(
        default_factory=list,
        description="Campi mancanti per conformità Articolo 11"
    )
    article_13_compliant: bool = Field(default=False, description="Conformità Articolo 13")
    article_14_compliant: bool = Field(default=False, description="Conformità Articolo 14")
    human_oversight_required: bool = Field(default=True, description="Supervisione umana richiesta")
    article_15_compliant: bool = Field(default=False, description="Conformità Articolo 15")
    accuracy_metrics_provided: bool = Field(default=False, description="Metriche accuratezza fornite")

    # NEW: Article 8
    article_8: Optional[Article8Compliance] = Field(None, description="Conformità Articolo 8")

    # NEW: Article 9 - Risk Management
    article_9: Optional[RiskManagementSystem] = Field(None, description="Sistema gestione rischi (Art. 9)")
    article_9_compliant: bool = Field(default=False, description="Conformità Articolo 9")

    # NEW: Article 10 - Data Governance
    article_10: Optional[DataGovernance] = Field(None, description="Data Governance (Art. 10)")
    article_10_compliant: bool = Field(default=False, description="Conformità Articolo 10")

    # NEW: Article 12 - Logging
    article_12: Optional[LoggingCapability] = Field(None, description="Logging & Record-keeping (Art. 12)")
    article_12_compliant: bool = Field(default=False, description="Conformità Articolo 12")

    # NEW: Article 15 - Separated into 3 components
    article_15_accuracy: Optional[AccuracyRequirements] = Field(None, description="Accuracy (Art. 15)")
    article_15_robustness: Optional[RobustnessRequirements] = Field(None, description="Robustness (Art. 15)")
    article_15_cybersecurity: Optional[CybersecurityRequirements] = Field(None, description="Cybersecurity (Art. 15)")

    # NEW: Article 16-17 - Provider Obligations & QMS
    article_16_17: Optional[ProviderObligations] = Field(None, description="Obblighi Provider & QMS (Art. 16-17)")
    article_16_compliant: bool = Field(default=False, description="Conformità Articolo 16")
    article_17_compliant: bool = Field(default=False, description="Conformità Articolo 17")

    # NEW: Annex III - High-Risk Classification
    annex_iii: Optional[HighRiskClassification] = Field(None, description="Classificazione High-Risk (Annex III)")

    # NEW: Annex X-XIII - GPAI
    gpai: Optional[GPAICompliance] = Field(None, description="GPAI Compliance (Annex X-XIII)")
    gpai_compliant: bool = Field(default=False, description="Conformità GPAI")

    # NEW: Article 61 - EU Database
    article_61: Optional[EUDatabaseRegistration] = Field(None, description="Registrazione EU Database (Art. 61)")
    article_61_compliant: bool = Field(default=False, description="Conformità Articolo 61")

    # NEW: Article 72-73 - Post-Market Monitoring
    article_72_73: Optional[PostMarketMonitoring] = Field(None, description="Post-Market Monitoring (Art. 72-73)")
    article_72_compliant: bool = Field(default=False, description="Conformità Articolo 72")
    article_73_compliant: bool = Field(default=False, description="Conformità Articolo 73")

    # EXISTING: ISO/IEC 42001
    iso_42001_compliant: bool = Field(default=False, description="Conformità ISO/IEC 42001")
    management_system_established: bool = Field(
        default=False,
        description="Sistema di gestione AI stabilito"
    )

    # EXISTING: Overall compliance
    compliance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score di conformità (0-1)"
    )
    critical_gaps: List[str] = Field(
        default_factory=list,
        description="Lacune critiche da risolvere"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Raccomandazioni per migliorare conformità"
    )

    @property
    def total_articles_checked(self) -> int:
        """Numero totale articoli verificati"""
        return 13  # Articles: 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 61, 72, 73

    @property
    def articles_compliant_count(self) -> int:
        """Numero articoli conformi"""
        return sum([
            self.article_8.compliant if self.article_8 else False,
            self.article_9_compliant,
            self.article_10_compliant,
            self.article_11_compliant,
            self.article_12_compliant,
            self.article_13_compliant,
            self.article_14_compliant,
            self.article_15_compliant,
            self.article_16_compliant,
            self.article_17_compliant,
            self.article_61_compliant,
            self.article_72_compliant,
            self.article_73_compliant,
        ])


# ============================================================================
# EXTENDED: ComplianceResult
# ============================================================================

class ComplianceResult(BaseModel):
    """Risultato della valutazione di conformità"""

    system_id: str = Field(..., description="ID del sistema valutato")
    compliant: bool = Field(..., description="Se il sistema è conforme")
    risk_level: RiskLevel = Field(..., description="Livello di rischio")

    technical_documentation: Optional[TechnicalDocumentation] = Field(
        None,
        description="Documentazione tecnica generata"
    )
    requirements_check: AnnexIVRequirements = Field(
        ...,
        description="Verifica requisiti Allegato IV"
    )

    # Dettagli valutazione
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_by: Optional[str] = Field(None, description="Valutatore")

    # Riferimenti AI-BOM
    ai_bom_id: Optional[str] = Field(None, description="ID AI-BOM associato")

    # Report compliance
    compliance_report: Dict[str, Any] = Field(
        default_factory=dict,
        description="Report dettagliato conformità"
    )
