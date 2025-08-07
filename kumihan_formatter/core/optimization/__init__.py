"""
Phase B.1: 動的設定調整・最適化システム
=====================================

このモジュールは Issue #803 Phase B.1 の実装として、
Phase A基盤（58%削減）上に追加3-5%削減を実現する
高度最適化システムを提供します。

コンポーネント:
- AdaptiveSettingsManager: 動的設定調整
- ContextAwareOptimizer: コンテキスト認識最適化
- RealTimeConfigAdjuster: リアルタイム調整
- IntegratedSettingsOptimizer: 統合最適化システム

技術基盤:
- 既存EnhancedConfig拡張活用
- performance_metrics統合
- 学習型調整アルゴリズム
"""

# Phase B.3統合システムインポート
from .phase_b import (
    EffectMeasurementResult,
    EffectMeasurementSystem,
    OptimizationIntegrator,
    PhaseBIntegrationConfig,
    PhaseBReport,
    PhaseBReportGenerator,
    StabilityValidationResult,
    StabilityValidator,
)
from .settings import (
    ABTestConfig,
    ABTestResult,
    AdaptiveSettingsManager,
    ConfigAdjustment,
    ContextAwareOptimizer,
    IntegratedSettingsOptimizer,
    RealTimeConfigAdjuster,
    WorkContext,
)

__all__ = [
    "AdaptiveSettingsManager",
    "ContextAwareOptimizer",
    "RealTimeConfigAdjuster",
    "IntegratedSettingsOptimizer",
    "ConfigAdjustment",
    "WorkContext",
    "ABTestConfig",
    "ABTestResult",
    # Phase B.3統合検証・効果測定システム
    "OptimizationIntegrator",
    "EffectMeasurementSystem",
    "StabilityValidator",
    "PhaseBReportGenerator",
    "PhaseBIntegrationConfig",
    "EffectMeasurementResult",
    "StabilityValidationResult",
    "PhaseBReport",
]
