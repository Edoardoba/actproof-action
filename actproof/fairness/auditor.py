"""
Fairness & Bias Auditor
Calcola metriche di disparità usando Fairlearn/AIF360 per sistemi ad alto rischio
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import numpy as np


class ProtectedAttribute(str, Enum):
    """Attributi protetti comuni"""
    GENDER = "gender"
    AGE = "age"
    ETHNICITY = "ethnicity"
    RACE = "race"
    DISABILITY = "disability"
    RELIGION = "religion"
    SEXUAL_ORIENTATION = "sexual_orientation"


class FairnessMetrics(BaseModel):
    """Metriche di fairness calcolate"""
    
    # Metriche di disparità
    demographic_parity_difference: float = Field(
        ...,
        description="Differenza di parità demografica (DPD)"
    )
    equalized_odds_difference: float = Field(
        ...,
        description="Differenza di equalized odds"
    )
    false_positive_rate_difference: float = Field(
        ...,
        description="Differenza False Positive Rate tra gruppi"
    )
    false_negative_rate_difference: float = Field(
        ...,
        description="Differenza False Negative Rate tra gruppi"
    )
    
    # Metriche per gruppo
    group_metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Metriche per ogni gruppo protetto"
    )
    
    # Thresholds di conformità EU AI Act
    compliant_dpd: bool = Field(
        ...,
        description="Conforme se DPD < 0.1 (10%)"
    )
    compliant_eod: bool = Field(
        ...,
        description="Conforme se EOD < 0.1 (10%)"
    )
    
    # Metadati
    protected_attribute: str = Field(..., description="Attributo protetto analizzato")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class BiasReport(BaseModel):
    """Report completo di bias e fairness"""
    
    system_id: str = Field(..., description="ID sistema analizzato")
    model_name: str = Field(..., description="Nome modello")
    
    # Metriche per ogni attributo protetto
    fairness_metrics: Dict[str, FairnessMetrics] = Field(
        default_factory=dict,
        description="Metriche per ogni attributo protetto"
    )
    
    # Risultato complessivo
    overall_compliant: bool = Field(..., description="Se il sistema è complessivamente conforme")
    critical_biases: List[str] = Field(
        default_factory=list,
        description="Bias critici identificati"
    )
    
    # Raccomandazioni
    recommendations: List[str] = Field(
        default_factory=list,
        description="Raccomandazioni per mitigare bias"
    )
    
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class FairnessAuditor:
    """
    Auditor per fairness e bias
    Supporta Fairlearn e AIF360
    """
    
    def __init__(self, use_fairlearn: bool = True, use_aif360: bool = False):
        """
        Inizializza auditor
        
        Args:
            use_fairlearn: Usa Fairlearn per calcoli
            use_aif360: Usa AIF360 per calcoli (alternativa)
        """
        self.use_fairlearn = use_fairlearn
        self.use_aif360 = use_aif360
        
        # Verifica dipendenze
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Verifica che le librerie necessarie siano installate"""
        if self.use_fairlearn:
            try:
                import fairlearn.metrics
                self.fairlearn_available = True
            except ImportError:
                self.fairlearn_available = False
                print("⚠️  Fairlearn non disponibile. Installa con: pip install fairlearn")
        
        if self.use_aif360:
            try:
                import aif360
                self.aif360_available = True
            except ImportError:
                self.aif360_available = False
                print("⚠️  AIF360 non disponibile. Installa con: pip install aif360")
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        protected_attributes: Dict[str, np.ndarray],
        threshold: float = 0.1,
    ) -> BiasReport:
        """
        Calcola metriche di fairness
        
        Args:
            y_true: Etichette vere (ground truth)
            y_pred: Predizioni del modello
            protected_attributes: Dict {attributo: array valori} per ogni attributo protetto
            threshold: Soglia per conformità (default 0.1 = 10%)
        
        Returns:
            BiasReport con tutte le metriche
        """
        fairness_metrics = {}
        
        for attr_name, attr_values in protected_attributes.items():
            metrics = self._calculate_attribute_metrics(
                y_true=y_true,
                y_pred=y_pred,
                protected_attribute=attr_values,
                attr_name=attr_name,
                threshold=threshold,
            )
            fairness_metrics[attr_name] = metrics
        
        # Determina conformità complessiva
        overall_compliant = all(
            m.compliant_dpd and m.compliant_eod
            for m in fairness_metrics.values()
        )
        
        # Identifica bias critici
        critical_biases = []
        for attr_name, metrics in fairness_metrics.items():
            if not metrics.compliant_dpd:
                critical_biases.append(
                    f"Parità demografica violata per {attr_name} (DPD={metrics.demographic_parity_difference:.3f})"
                )
            if not metrics.compliant_eod:
                critical_biases.append(
                    f"Equalized odds violato per {attr_name} (EOD={metrics.equalized_odds_difference:.3f})"
                )
        
        # Genera raccomandazioni
        recommendations = self._generate_recommendations(fairness_metrics, critical_biases)
        
        return BiasReport(
            system_id="unknown",
            model_name="unknown",
            fairness_metrics=fairness_metrics,
            overall_compliant=overall_compliant,
            critical_biases=critical_biases,
            recommendations=recommendations,
        )
    
    def _calculate_attribute_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        protected_attribute: np.ndarray,
        attr_name: str,
        threshold: float = 0.1,
    ) -> FairnessMetrics:
        """Calcola metriche per un singolo attributo protetto"""
        
        # Usa Fairlearn se disponibile
        if self.use_fairlearn and self.fairlearn_available:
            return self._calculate_with_fairlearn(
                y_true, y_pred, protected_attribute, attr_name, threshold
            )
        
        # Fallback: calcolo manuale
        return self._calculate_manual(
            y_true, y_pred, protected_attribute, attr_name, threshold
        )
    
    def _calculate_with_fairlearn(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        protected_attribute: np.ndarray,
        attr_name: str,
        threshold: float,
    ) -> FairnessMetrics:
        """Calcola metriche usando Fairlearn"""
        try:
            import fairlearn.metrics as fl_metrics
            
            # Calcola Demographic Parity Difference
            selection_rate_by_group = fl_metrics.selection_rate(
                y_true=y_pred,
                sensitive_features=protected_attribute,
            )
            dpd = max(selection_rate_by_group.values()) - min(selection_rate_by_group.values())
            
            # Calcola Equalized Odds Difference
            eod = fl_metrics.equalized_odds_difference(
                y_true=y_true,
                y_pred=y_pred,
                sensitive_features=protected_attribute,
            )
            
            # Calcola FPR e FNR per gruppo
            group_metrics = {}
            unique_groups = np.unique(protected_attribute)
            
            for group in unique_groups:
                group_mask = protected_attribute == group
                y_true_group = y_true[group_mask]
                y_pred_group = y_pred[group_mask]
                
                # Calcola FPR e FNR
                tn = np.sum((y_true_group == 0) & (y_pred_group == 0))
                fp = np.sum((y_true_group == 0) & (y_pred_group == 1))
                fn = np.sum((y_true_group == 1) & (y_pred_group == 0))
                tp = np.sum((y_true_group == 1) & (y_pred_group == 1))
                
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
                
                group_metrics[str(group)] = {
                    "fpr": float(fpr),
                    "fnr": float(fnr),
                    "selection_rate": float(np.mean(y_pred_group)),
                }
            
            # Calcola differenze FPR/FNR
            fpr_values = [m["fpr"] for m in group_metrics.values()]
            fnr_values = [m["fnr"] for m in group_metrics.values()]
            
            fpr_diff = max(fpr_values) - min(fpr_values) if fpr_values else 0.0
            fnr_diff = max(fnr_values) - min(fnr_values) if fnr_values else 0.0
            
            return FairnessMetrics(
                demographic_parity_difference=float(dpd),
                equalized_odds_difference=float(eod),
                false_positive_rate_difference=float(fpr_diff),
                false_negative_rate_difference=float(fnr_diff),
                group_metrics=group_metrics,
                compliant_dpd=abs(dpd) < threshold,
                compliant_eod=abs(eod) < threshold,
                protected_attribute=attr_name,
            )
        except Exception as e:
            print(f"Errore nel calcolo Fairlearn: {e}")
            return self._calculate_manual(y_true, y_pred, protected_attribute, attr_name, threshold)
    
    def _calculate_manual(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        protected_attribute: np.ndarray,
        attr_name: str,
        threshold: float,
    ) -> FairnessMetrics:
        """Calcolo manuale delle metriche (fallback)"""
        unique_groups = np.unique(protected_attribute)
        group_metrics = {}
        
        selection_rates = []
        fpr_values = []
        fnr_values = []
        
        for group in unique_groups:
            group_mask = protected_attribute == group
            y_true_group = y_true[group_mask]
            y_pred_group = y_pred[group_mask]
            
            # Selection rate (positive prediction rate)
            sr = np.mean(y_pred_group)
            selection_rates.append(sr)
            
            # Calcola FPR e FNR
            tn = np.sum((y_true_group == 0) & (y_pred_group == 0))
            fp = np.sum((y_true_group == 0) & (y_pred_group == 1))
            fn = np.sum((y_true_group == 1) & (y_pred_group == 0))
            tp = np.sum((y_true_group == 1) & (y_pred_group == 1))
            
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
            
            fpr_values.append(fpr)
            fnr_values.append(fnr)
            
            group_metrics[str(group)] = {
                "fpr": float(fpr),
                "fnr": float(fnr),
                "selection_rate": float(sr),
            }
        
        # Calcola differenze
        dpd = max(selection_rates) - min(selection_rates) if selection_rates else 0.0
        fpr_diff = max(fpr_values) - min(fpr_values) if fpr_values else 0.0
        fnr_diff = max(fnr_values) - min(fnr_values) if fnr_values else 0.0
        
        # EOD approssimato come max tra FPR diff e FNR diff
        eod = max(fpr_diff, fnr_diff)
        
        return FairnessMetrics(
            demographic_parity_difference=float(dpd),
            equalized_odds_difference=float(eod),
            false_positive_rate_difference=float(fpr_diff),
            false_negative_rate_difference=float(fnr_diff),
            group_metrics=group_metrics,
            compliant_dpd=abs(dpd) < threshold,
            compliant_eod=abs(eod) < threshold,
            protected_attribute=attr_name,
        )
    
    def _generate_recommendations(
        self,
        fairness_metrics: Dict[str, FairnessMetrics],
        critical_biases: List[str],
    ) -> List[str]:
        """Genera raccomandazioni per mitigare bias"""
        recommendations = []
        
        if not critical_biases:
            recommendations.append("✅ Nessun bias critico rilevato. Il sistema è conforme ai requisiti di fairness.")
            return recommendations
        
        recommendations.append(
            "⚠️  Bias critici rilevati. Azioni consigliate:"
        )
        
        # Raccomandazioni specifiche per tipo di bias
        for attr_name, metrics in fairness_metrics.items():
            if not metrics.compliant_dpd:
                recommendations.append(
                    f"  • Per {attr_name}: Implementare post-processing (es. threshold optimization) "
                    f"per ridurre DPD da {metrics.demographic_parity_difference:.3f} a < 0.1"
                )
            
            if not metrics.compliant_eod:
                recommendations.append(
                    f"  • Per {attr_name}: Rivedere il training data per bilanciare rappresentazione "
                    f"tra gruppi e ridurre EOD da {metrics.equalized_odds_difference:.3f} a < 0.1"
                )
        
        recommendations.append(
            "  • Considerare l'uso di tecniche di debiasing (pre-processing, in-processing, post-processing)"
        )
        recommendations.append(
            "  • Documentare le misure di mitigazione implementate nella documentazione tecnica"
        )
        
        return recommendations
