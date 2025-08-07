"""
Phase B統合システム設定・データクラス定義
Issue #803 Phase B.3実装 - 設定・データモデル分離

Phase B統合システム用の設定クラスと結果データクラス:
- PhaseBIntegrationConfig: システム設定
- EffectMeasurementResult: 効果測定結果
- StabilityValidationResult: 安定性検証結果
- PhaseBReport: 総合レポートデータ
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class PhaseBIntegrationConfig:
    """Phase B統合システム設定"""

    measurement_interval: float = 30.0  # 測定間隔（秒）
    stability_check_interval: float = 60.0  # 安定性チェック間隔
    report_generation_interval: float = 300.0  # レポート生成間隔
    min_measurement_samples: int = 10  # 最小測定サンプル数
    target_reduction_rate: float = 66.8  # 目標削減率（%）
    phase_a_baseline: float = 58.0  # Phase A基盤削減率
    phase_b1_target: float = 3.8  # Phase B.1目標削減率
    phase_b2_target: float = 5.0  # Phase B.2目標削減率
    stability_threshold: float = 0.95  # 安定性閾値
    performance_threshold: float = 1.05  # パフォーマンス閾値


@dataclass
class EffectMeasurementResult:
    """効果測定結果"""

    timestamp: datetime
    phase_a_rate: float  # Phase A削減率
    phase_b1_rate: float  # Phase B.1削減率
    phase_b2_rate: float  # Phase B.2削減率
    total_rate: float  # 総合削減率
    target_achievement: bool  # 目標達成フラグ
    measurement_confidence: float  # 測定信頼度
    baseline_tokens: int  # ベースライントークン数
    optimized_tokens: int  # 最適化後トークン数
    samples_count: int  # サンプル数


@dataclass
class StabilityValidationResult:
    """安定性検証結果"""

    timestamp: datetime
    system_stability: float  # システム安定性スコア
    performance_impact: float  # パフォーマンス影響
    error_rate: float  # エラー発生率
    memory_usage: float  # メモリ使用量
    processing_speed: float  # 処理速度
    integration_health: Dict[str, float]  # 統合ヘルス状況
    validation_passed: bool  # 検証合格フラグ


@dataclass
class PhaseBReport:
    """Phase B総合レポート"""

    generation_time: datetime
    phase_b_summary: Dict[str, Any]  # Phase B実装サマリー
    effect_measurement: EffectMeasurementResult  # 効果測定結果
    stability_validation: StabilityValidationResult  # 安定性検証
    goal_achievement: Dict[str, Any]  # 目標達成状況
    recommendations: List[str]  # 改善提言
    phase_b4_roadmap: Dict[str, Any]  # Phase B.4以降への道筋
