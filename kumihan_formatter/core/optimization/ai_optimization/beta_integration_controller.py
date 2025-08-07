"""
Phase B.4-Beta統合最適化システム（後方互換性レイヤー）

Alpha基盤+Beta拡張統合・相乗効果最大化
- Phase B.4-Alpha基盤（68.8%削減）完全活用
- Beta高度MLシステム統合・協調動作
- 統合相乗効果最大化・効果増幅
- 72-73%削減目標達成・システム安定性維持

NOTE: Issue #813対応 - 1511行ファイルを2ファイルに分割
      integration/配下に分割実装・後方互換性100%維持
"""

# 統合システム完全インポート（後方互換性確保）
from .integration import (
    AlphaBetaCoordinator,
    IntegrationMetrics,
    IntegrationMode,
    PerformanceMonitor,
    PhaseB4BetaIntegrator,
    SynergyEffect,
    SynergyType,
)

# 後方互換性完全確保エクスポート
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
