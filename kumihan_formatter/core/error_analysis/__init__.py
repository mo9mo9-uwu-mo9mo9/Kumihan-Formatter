"""
Error analysis and correction suggestion system
Issue #700対応
"""

from .correction_engine import CorrectionEngine, CorrectionRule
from .statistics_generator import ErrorStatistics, StatisticsGenerator

__all__ = [
    "CorrectionEngine",
    "CorrectionRule",
    "StatisticsGenerator",
    "ErrorStatistics",
]
