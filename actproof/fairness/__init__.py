"""
Modulo Fairness & Bias Auditing
Fase 3: Automazione test di non-discriminazione per sistemi ad alto rischio
"""

from actproof.fairness.auditor import FairnessAuditor, FairnessMetrics, BiasReport
from actproof.fairness.report_generator import LegalReportGenerator

__all__ = [
    "FairnessAuditor",
    "FairnessMetrics",
    "BiasReport",
    "LegalReportGenerator",
]
