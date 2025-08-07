"""
Phase B.4-Beta統合システム初期化

統合インポート管理・後方互換性確保
- Alpha基盤+Beta拡張統合コアシステム
- Phase統合管理・性能監視システム
- 循環インポート回避・完全互換性維持
"""

# Beta統合コアシステム
from .beta_core import (
    AlphaBetaCoordinator,
    IntegrationMetrics,
    IntegrationMode,
    SynergyEffect,
    SynergyType,
)

# Phase統合管理システム
from .integration_manager import PerformanceMonitor, PhaseB4BetaIntegrator

# 後方互換性エクスポート
__all__ = [
    # 統合システム
    "PhaseB4BetaIntegrator",
    "AlphaBetaCoordinator",
    "PerformanceMonitor",
    # 統合モード・メトリクス
    "IntegrationMode",
    "IntegrationMetrics",
    "SynergyType",
    "SynergyEffect",
]
