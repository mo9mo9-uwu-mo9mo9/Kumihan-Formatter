"""
ML Models Base - 機械学習モデル基底クラスとデータ構造

BaseMLModel、TrainingData、ModelPerformance、予測関連クラス
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np

from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


@dataclass
class TrainingData:
    """学習データ構造"""

    features: np.ndarray
    targets: np.ndarray
    labels: np.ndarray
    feature_names: List[str]
    target_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModelPerformance:
    """モデル性能情報"""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time: float
    prediction_time: float
    model_size: int
    cross_val_score: float


@dataclass
class PredictionRequest:
    """予測リクエスト"""

    features: Union[np.ndarray, Dict[str, Any]]
    model_name: str
    confidence_threshold: float = 0.5
    return_probabilities: bool = False


@dataclass
class PredictionResponse:
    """予測レスポンス"""

    prediction: Union[float, int, str]
    confidence: float
    probabilities: Optional[np.ndarray] = None
    feature_importance: Optional[Dict[str, float]] = None
    processing_time: float = 0.0


class BaseMLModel(ABC):
    """機械学習モデル基底クラス"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.model: Any = None
        self.scaler: Any = None
        self.is_trained = False
        self.feature_names: list[str] = []
        self.performance_metrics: dict[str, float] = {}
        self.label_encoder: Any = None  # For classification models
        self.logger = get_logger(f"{__name__}.{name}")

    @abstractmethod
    def create_model(self) -> Any:
        """モデル作成（継承先で実装）"""
        raise NotImplementedError("create_model must be implemented by subclass")

    @abstractmethod
    def train(self, data: TrainingData) -> bool:
        """モデル訓練（継承先で実装）"""
        raise NotImplementedError("train must be implemented by subclass")

    @abstractmethod
    def predict(self, features: np.ndarray) -> PredictionResponse:
        """予測実行（継承先で実装）"""
        raise NotImplementedError("predict must be implemented by subclass")
