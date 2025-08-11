"""
Phase B統合システム - 統合APIパッケージ
Issue #803 Phase B.3実装 - 分割されたモジュールの統合インターフェース

分割後の各モジュールからの統一インポートAPI:
- config: 設定・データクラス定義
- measurement: 効果測定システム
- validation: 安定性検証・レポート機能
- integrator: メイン統合制御システム

使用例:
    from kumihan_formatter.core.optimization.phase_b import (
        OptimizationIntegrator,
        PhaseBIntegrationConfig,
    )

    config = PhaseBIntegrationConfig(target_reduction_rate=66.8)
    integrator = OptimizationIntegrator(config)
"""

# 設定・データクラス
from .config import (
    EffectMeasurementResult,
    PhaseBIntegrationConfig,
    PhaseBReport,
    StabilityValidationResult,
)

# メイン統合システム
from .integrator import OptimizationIntegrator, create_phase_b_integrator

# 効果測定システム
from .measurement import EffectMeasurementSystem

# 安定性検証・レポート
from .validation import PhaseBReportGenerator, StabilityValidator

# 後方互換性のためのエイリアス
OptimizationIntegratorSystem = OptimizationIntegrator
PhaseBEffectMeasurement = EffectMeasurementSystem

__all__ = [
    # 設定・データクラス
    "PhaseBIntegrationConfig",
    "EffectMeasurementResult",
    "StabilityValidationResult",
    "PhaseBReport",
    # システムコンポーネント
    "EffectMeasurementSystem",
    "StabilityValidator",
    "PhaseBReportGenerator",
    # メインシステム
    "OptimizationIntegrator",
    "create_phase_b_integrator",
    # 後方互換エイリアス
    "OptimizationIntegratorSystem",
    "PhaseBEffectMeasurement",
]

# バージョン情報
__version__ = "1.0.0"
__author__ = "Phase B.3 Integration System"
__description__ = "Phase B統合システム - 効果測定・安定性検証・レポート生成"

# パッケージメタデータ
__package_info__ = {
    "name": "phase_b",
    "version": __version__,
    "description": __description__,
    "modules": ["config", "measurement", "validation", "integrator"],
    "split_from": "phase_b_integrator.py",
    "total_lines_split": 1108,
    "target_max_lines_per_file": 400,
}
