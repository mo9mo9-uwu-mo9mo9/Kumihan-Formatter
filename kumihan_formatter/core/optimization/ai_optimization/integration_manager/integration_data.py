"""
統合管理データ構造

AI Integration Manager用のデータクラス定義
"""

from dataclasses import dataclass


@dataclass
class IntegrationStatus:
    """統合状態情報"""

    phase_b_operational: bool
    ai_systems_ready: bool
    integration_health: float
    last_sync_time: float
    error_count: int
    recovery_mode: bool


@dataclass
class CoordinatedResult:
    """協調最適化結果"""

    phase_b_contribution: float
    ai_contribution: float
    synergy_effect: float
    total_improvement: float
    integration_success: bool
    execution_time: float
    coordination_quality: float


@dataclass
class SystemHealth:
    """システム健全性情報"""

    phase_b_health: float
    ai_health: float
    integration_health: float
    performance_score: float
    stability_score: float
    recommendation: str
