"""
AI Optimization Module - Phase B.4 AI駆動型最適化システム

Phase B.4-Alpha実装: AIコアエンジン基本実装・2.0%削減達成
Phase B基盤（66.8%削減）+ AI追加効果（2.0%）= 総合68.8%削減実現

Components:
- AIOptimizerCore: メインAI最適化エンジン
- AIIntegrationManager: Phase B統合管理システム
- BasicMLSystem: 基本機械学習システム
- AIEffectMeasurement: AI効果測定・検証システム
"""

from .ai_optimizer_core import (
    AIOptimizerCore,
    OptimizationContext,
    OptimizationResult,
    PredictionResult,
)
from .integration_manager import (
    AIIntegrationManager,
    CoordinatedResult,
    IntegrationStatus,
    SystemHealth,
)
from .measurement import (
    AIEffectMeasurement,
    EffectReport,
    MeasurementResult,
    QualityMetrics,
    StabilityAssessment,
)
from .ml import (
    BasicMLSystem,
    FeatureEngineering,
    ModelPerformance,
    PredictionRequest,
    PredictionResponse,
    TrainingData,
)

__all__ = [
    # Core AI Engine
    "AIOptimizerCore",
    "OptimizationContext",
    "PredictionResult",
    "OptimizationResult",
    # Integration Management
    "AIIntegrationManager",
    "IntegrationStatus",
    "CoordinatedResult",
    "SystemHealth",
    # Machine Learning System
    "BasicMLSystem",
    "TrainingData",
    "ModelPerformance",
    "PredictionRequest",
    "PredictionResponse",
    "FeatureEngineering",
    # Effect Measurement
    "AIEffectMeasurement",
    "MeasurementResult",
    "EffectReport",
    "QualityMetrics",
    "StabilityAssessment",
]

# Module version
__version__ = "1.0.0-alpha"

# Phase B.4 configuration
PHASE_B4_CONFIG = {
    "target_ai_contribution": 2.0,  # 2.0% AI追加削減目標
    "phase_b_baseline": 66.8,  # Phase B基盤削減効果
    "total_efficiency_target": 68.8,  # 総合削減目標
    "stability_threshold": 98.0,  # 安定性目標
    "response_time_target": 200,  # 応答時間目標（ms）
    "prediction_accuracy_target": 85,  # 予測精度目標（%）
}
