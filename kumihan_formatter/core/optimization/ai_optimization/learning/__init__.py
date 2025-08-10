"""
学習システム統合API

Phase B.4-Beta継続学習システム・統合インターフェース
- データ品質管理・適応的最適化
- パターン認識・ハイパーパラメータ最適化
- メイン学習システム・継続学習統合

使用例:
    from .learning import LearningSystem, DataQualityManager

    # メインシステム
    learning_system = LearningSystem(config)
    result = learning_system.train_models_incrementally(models, training_data)

    # 個別コンポーネント
    quality_manager = DataQualityManager(config)
    quality_result = quality_manager.validate_training_data(training_data)
"""

from .core import DataQualityManager
from .pattern_engine import (
    OPTUNA_AVAILABLE,
    HyperparameterOptimizer,
    OnlineLearningEngine,
)
from .system import LearningSystem

# 公開API
__all__ = [
    # メインシステム
    "LearningSystem",
    # データ品質管理
    "DataQualityManager",
    # パターン認識・最適化
    "HyperparameterOptimizer",
    "OnlineLearningEngine",
    "OPTUNA_AVAILABLE",
]

# バージョン情報
__version__ = "1.0.0"
__author__ = "Kumihan-Formatter AI Learning System"
__description__ = "Phase B.4-Beta継続学習システム - 統合学習・品質管理・最適化"
