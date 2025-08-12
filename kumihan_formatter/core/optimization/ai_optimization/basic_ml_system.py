"""
Basic ML System - 基本機械学習システム（Phase B.4-Alpha）

軽量・高速ML処理システム - scikit-learn基盤・Phase B運用データ活用
予測システム基盤・学習データ管理・特徴量エンジニアリング・モデル訓練推論
"""

import pickle
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Kumihan-Formatter基盤
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
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_names: list[str] = []
        self.performance_metrics: dict[str, float] = {}
        self.label_encoder = None  # For classification models
        self.logger = get_logger(f"{__name__}.{name}")

    @abstractmethod
    def create_model(self) -> Any:
        """モデル作成（継承先で実装）"""
        pass

    @abstractmethod
    def train(self, data: TrainingData) -> bool:
        """モデル訓練（継承先で実装）"""
        pass

    @abstractmethod
    def predict(self, features: np.ndarray) -> PredictionResponse:
        """予測実行（継承先で実装）"""
        pass


class TokenEfficiencyPredictor(BaseMLModel):
    """Token効率性予測モデル"""

    def create_model(self) -> "RandomForestRegressor":
        """RandomForest回帰モデル作成"""
        from sklearn.ensemble import RandomForestRegressor

        return RandomForestRegressor(
            n_estimators=self.config.get("n_estimators", 50),
            max_depth=self.config.get("max_depth", 10),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """Token効率性予測モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import StandardScaler

            training_start = time.time()

            # モデル・スケーラー初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()

            # Type assertion for mypy
            assert self.model is not None, "Model creation failed"

            # 特徴量正規化
            X_scaled = self.scaler.fit_transform(data.features)

            # 学習実行
            self.model.fit(X_scaled, data.targets)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, data.targets, cv=5, scoring="r2"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "r2_score": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Token efficiency predictor trained: "
                f"R²={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Token efficiency training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """Token効率性予測"""
        if not self.is_trained:
            return PredictionResponse(
                prediction=0.0, confidence=0.0, processing_time=0.0
            )
        if self.model is None:
            raise RuntimeError("Model not trained properly")
        if self.scaler is None:
            raise RuntimeError("Scaler not initialized properly")

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction = self.model.predict(features_scaled)[0]

            # 信頼度計算
            if hasattr(self.model, "estimators_"):
                # Random Forestの場合、各木の予測分散から信頼度計算
                tree_predictions = [
                    tree.predict(features_scaled)[0] for tree in self.model.estimators_
                ]
                confidence = 1.0 - (
                    np.std(tree_predictions) / max(np.mean(tree_predictions), 0.1)
                )
                confidence = max(0.0, min(1.0, confidence))
            else:
                confidence = 0.8  # デフォルト信頼度

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=float(prediction),
                confidence=confidence,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Token efficiency prediction failed: {e}")
            return PredictionResponse(
                prediction=0.0, confidence=0.0, processing_time=0.0
            )


class UsagePatternClassifier(BaseMLModel):
    """使用パターン分類モデル"""

    def create_model(self) -> "RandomForestClassifier":
        """RandomForest分類モデル作成"""
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=self.config.get("n_estimators", 30),
            max_depth=self.config.get("max_depth", 8),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """使用パターン分類モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import LabelEncoder, StandardScaler

            training_start = time.time()

            # モデル・スケーラー・エンコーダー初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()

            # Type assertion for mypy
            assert self.model is not None, "Model creation failed"

            self.label_encoder = LabelEncoder()

            # 特徴量正規化
            X_scaled = self.scaler.fit_transform(data.features)

            # ラベルエンコーディング
            y_encoded = self.label_encoder.fit_transform(data.targets)

            # 学習実行
            self.model.fit(X_scaled, y_encoded)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, y_encoded, cv=5, scoring="accuracy"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "accuracy": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
                "class_count": len(self.label_encoder.classes_),
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Usage pattern classifier trained: "
                f"Accuracy={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Usage pattern training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """使用パターン分類予測"""
        if not self.is_trained:
            return PredictionResponse(
                prediction="unknown", confidence=0.0, processing_time=0.0
            )
        if self.model is None:
            raise RuntimeError("Model not trained properly")
        if self.scaler is None:
            raise RuntimeError("Scaler not initialized properly")
        assert self.label_encoder is not None, "Label encoder not initialized properly"

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction_encoded = self.model.predict(features_scaled)[0]
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]

            # 予測確率・信頼度
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                probabilities=probabilities,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Usage pattern prediction failed: {e}")
            return PredictionResponse(
                prediction="unknown", confidence=0.0, processing_time=0.0
            )


class OptimizationRecommender(BaseMLModel):
    """最適化推奨システム"""

    def create_model(self) -> "RandomForestClassifier":
        """最適化推奨分類モデル作成"""
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=self.config.get("n_estimators", 40),
            max_depth=self.config.get("max_depth", 12),
            random_state=42,
            n_jobs=-1,
        )

    def train(self, data: TrainingData) -> bool:
        """最適化推奨モデル訓練"""
        try:
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import LabelEncoder, StandardScaler

            training_start = time.time()

            # モデル・前処理器初期化
            self.model = self.create_model()
            self.scaler = StandardScaler()

            # Type assertion for mypy
            assert self.model is not None, "Model creation failed"

            self.label_encoder = LabelEncoder()

            # データ前処理
            X_scaled = self.scaler.fit_transform(data.features)
            y_encoded = self.label_encoder.fit_transform(data.targets)

            # 学習実行
            self.model.fit(X_scaled, y_encoded)

            # 性能評価
            cv_scores = cross_val_score(
                self.model, X_scaled, y_encoded, cv=5, scoring="accuracy"
            )

            # 性能記録
            training_time = time.time() - training_start
            self.performance_metrics = {
                "accuracy": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "training_time": training_time,
                "feature_count": data.features.shape[1],
                "sample_count": data.features.shape[0],
                "optimization_types": len(self.label_encoder.classes_),
            }

            self.feature_names = data.feature_names
            self.is_trained = True

            self.logger.info(
                f"Optimization recommender trained: "
                f"Accuracy={cv_scores.mean():.3f}±{cv_scores.std():.3f}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Optimization recommender training failed: {e}")
            return False

    def predict(self, features: np.ndarray) -> PredictionResponse:
        """最適化推奨予測"""
        if not self.is_trained:
            return PredictionResponse(
                prediction="basic_optimization", confidence=0.0, processing_time=0.0
            )

        if self.model is None:
            raise RuntimeError("Model not trained properly")
        if self.scaler is None:
            raise RuntimeError("Scaler not initialized properly")
        assert self.label_encoder is not None, "Label encoder not initialized properly"

        try:
            prediction_start = time.time()

            # 特徴量正規化
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            # 予測実行
            prediction_encoded = self.model.predict(features_scaled)[0]
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]

            # 予測確率・信頼度
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))

            # 特徴量重要度
            feature_importance = None
            if hasattr(self.model, "feature_importances_") and self.feature_names:
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )

            processing_time = time.time() - prediction_start

            return PredictionResponse(
                prediction=prediction,
                confidence=confidence,
                probabilities=probabilities,
                feature_importance=feature_importance,
                processing_time=processing_time,
            )

        except Exception as e:
            self.logger.error(f"Optimization recommendation failed: {e}")
            return PredictionResponse(
                prediction="basic_optimization", confidence=0.0, processing_time=0.0
            )


class FeatureEngineering:
    """特徴量エンジニアリング"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.feature_extractors = {
            "basic": self._extract_basic_features,
            "statistical": self._extract_statistical_features,
            "temporal": self._extract_temporal_features,
            "contextual": self._extract_contextual_features,
        }

    def extract_features(
        self,
        optimization_data: Dict[str, Any],
        feature_types: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """Phase B運用データ特徴量抽出"""
        if feature_types is None:
            feature_types = ["basic", "statistical"]

        try:
            all_features = []
            all_feature_names = []

            for feature_type in feature_types:
                if feature_type in self.feature_extractors:
                    features, feature_names = self.feature_extractors[feature_type](
                        optimization_data
                    )
                    all_features.extend(features)
                    all_feature_names.extend(
                        [f"{feature_type}_{name}" for name in feature_names]
                    )

            feature_array = np.array(all_features).reshape(1, -1)

            self.logger.debug(
                f"Extracted {len(all_features)} features from Phase B data"
            )
            return feature_array, all_feature_names

        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return np.array([]).reshape(1, -1), []

    def _extract_basic_features(
        self, data: Dict[str, Any]
    ) -> Tuple[List[float], List[str]]:
        """基本特徴量抽出"""
        features = []
        feature_names = []

        # 操作特徴量
        operation_type = data.get("operation_type", "unknown")
        features.append(float(hash(operation_type) % 1000))
        feature_names.append("operation_type_hash")

        # コンテンツサイズ
        content_size = data.get("content_size", 0)
        features.append(float(content_size))
        feature_names.append("content_size")

        # 複雑度スコア
        complexity_score = data.get("complexity_score", 0.0)
        features.append(float(complexity_score))
        feature_names.append("complexity_score")

        # Phase B効率性
        optimization_efficiency = data.get("optimization_efficiency", 66.8)
        features.append(float(optimization_efficiency))
        feature_names.append("optimization_efficiency")

        # 設定数
        settings_count = len(data.get("current_settings", {}))
        features.append(float(settings_count))
        feature_names.append("settings_count")

        return features, feature_names

    def _extract_statistical_features(
        self, data: Dict[str, Any]
    ) -> Tuple[List[float], List[str]]:
        """統計特徴量抽出"""
        features = []
        feature_names = []

        # 履歴統計
        recent_operations = data.get("recent_operations", [])
        if recent_operations:
            # 操作頻度
            features.append(float(len(recent_operations)))
            feature_names.append("operation_frequency")

            # 操作多様性
            unique_operations = len(set(recent_operations))
            diversity = (
                unique_operations / len(recent_operations) if recent_operations else 0
            )
            features.append(diversity)
            feature_names.append("operation_diversity")

            # 操作パターン一貫性
            if len(recent_operations) > 1:
                pattern_consistency = len(set(recent_operations[-3:])) / min(
                    3, len(recent_operations)
                )
                features.append(pattern_consistency)
                feature_names.append("pattern_consistency")
            else:
                features.append(1.0)
                feature_names.append("pattern_consistency")
        else:
            features.extend([0.0, 0.0, 0.0])
            feature_names.extend(
                ["operation_frequency", "operation_diversity", "pattern_consistency"]
            )

        # 効率性統計
        efficiency_history = data.get("efficiency_history", [])
        if efficiency_history:
            features.append(np.mean(efficiency_history))
            feature_names.append("efficiency_mean")

            features.append(np.std(efficiency_history))
            feature_names.append("efficiency_std")

            # トレンド計算
            if len(efficiency_history) > 1:
                trend = efficiency_history[-1] - efficiency_history[0]
                features.append(trend)
                feature_names.append("efficiency_trend")
            else:
                features.append(0.0)
                feature_names.append("efficiency_trend")
        else:
            features.extend([0.0, 0.0, 0.0])
            feature_names.extend(
                ["efficiency_mean", "efficiency_std", "efficiency_trend"]
            )

        return features, feature_names

    def _extract_temporal_features(
        self, data: Dict[str, Any]
    ) -> Tuple[List[float], List[str]]:
        """時系列特徴量抽出"""
        features = []
        feature_names = []

        # 時間ベース特徴量
        current_time = time.time()

        # 最終操作からの経過時間
        last_operation_time = data.get("last_operation_time", current_time)
        time_since_last = current_time - last_operation_time
        features.append(min(3600.0, time_since_last))  # 最大1時間でクリップ
        feature_names.append("time_since_last_operation")

        # 操作間隔統計
        operation_intervals = data.get("operation_intervals", [])
        if operation_intervals:
            features.append(np.mean(operation_intervals))
            feature_names.append("avg_operation_interval")

            features.append(np.std(operation_intervals))
            feature_names.append("operation_interval_std")
        else:
            features.extend([0.0, 0.0])
            feature_names.extend(["avg_operation_interval", "operation_interval_std"])

        # 時間帯特徴量
        hour_of_day = time.localtime(current_time).tm_hour
        features.append(float(hour_of_day))
        feature_names.append("hour_of_day")

        return features, feature_names

    def _extract_contextual_features(
        self, data: Dict[str, Any]
    ) -> Tuple[List[float], List[str]]:
        """コンテキスト特徴量抽出"""
        features = []
        feature_names = []

        # システム状態特徴量
        system_load = data.get("system_load", 0.5)
        features.append(float(system_load))
        feature_names.append("system_load")

        # メモリ使用率
        memory_usage = data.get("memory_usage", 0.5)
        features.append(float(memory_usage))
        feature_names.append("memory_usage")

        # 並行処理数
        concurrent_operations = data.get("concurrent_operations", 1)
        features.append(float(concurrent_operations))
        feature_names.append("concurrent_operations")

        # ユーザー行動パターン
        user_activity_level = data.get("user_activity_level", "normal")
        activity_mapping = {"low": 0.0, "normal": 1.0, "high": 2.0}
        features.append(activity_mapping.get(user_activity_level, 1.0))
        feature_names.append("user_activity_level")

        return features, feature_names


class BasicMLSystem:
    """基本機械学習システム（Phase B.4-Alpha）

    軽量・高速ML処理システム - Phase B運用データ活用・85%以上精度目標
    予測システム基盤・学習データ管理・特徴量エンジニアリング・モデル訓練推論
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """MLシステム初期化"""
        from collections import OrderedDict

        self.logger = get_logger(__name__)
        self.config = config or {}

        # MLモデル群
        self.models: Dict[str, BaseMLModel] = {}

        # 特徴量エンジニアリング
        self.feature_extractor = FeatureEngineering()

        # 【メモリリーク対策】学習データ管理
        self.training_data_store: Dict[str, List[TrainingData]] = {}
        self._training_data_max_size = self.config.get("training_data_max_size", 50)

        # MLパイプライン
        self.ml_pipeline: Optional[Dict[str, Any]] = None

        # 【メモリリーク対策】性能追跡
        self.performance_history: Dict[str, List[ModelPerformance]] = {}
        self._performance_history_max_size = self.config.get(
            "performance_history_max_size", 100
        )

        # 【メモリリーク対策】予測キャッシュ（LRU実装）
        self.prediction_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.cache_max_size = self.config.get("cache_max_size", 500)

        # 初期化処理
        self._initialize_ml_system()

        self.logger.info("BasicMLSystem initialized successfully")

    def _initialize_ml_system(self) -> None:
        """MLシステム初期化"""
        try:
            # MLモデル初期化
            self._initialize_models()

            # MLパイプライン構築
            self._create_ml_pipeline()

            # 学習データストア初期化
            self._initialize_data_store()

            self.logger.info("ML system components initialized successfully")

        except Exception as e:
            self.logger.error(f"ML system initialization failed: {e}")
            raise

    def _initialize_models(self) -> None:
        """MLモデル群初期化"""
        try:
            # Token効率性予測モデル
            self.models["efficiency_predictor"] = TokenEfficiencyPredictor(
                "efficiency_predictor", self.config.get("efficiency_predictor", {})
            )

            # 使用パターン分類モデル
            self.models["pattern_classifier"] = UsagePatternClassifier(
                "pattern_classifier", self.config.get("pattern_classifier", {})
            )

            # 最適化推奨モデル
            self.models["optimization_recommender"] = OptimizationRecommender(
                "optimization_recommender",
                self.config.get("optimization_recommender", {}),
            )

            self.logger.info(f"Initialized {len(self.models)} ML models")

        except Exception as e:
            self.logger.error(f"ML models initialization failed: {e}")
            raise

    def _create_ml_pipeline(self) -> None:
        """MLパイプライン構築"""
        try:
            # 基本処理パイプライン
            self.ml_pipeline = {
                "data_preprocessing": self._preprocess_data,
                "feature_extraction": self.feature_extractor.extract_features,
                "model_prediction": self._execute_model_prediction,
                "result_postprocessing": self._postprocess_results,
            }

            self.logger.info("ML pipeline created successfully")

        except Exception as e:
            self.logger.error(f"ML pipeline creation failed: {e}")
            raise

    def _initialize_data_store(self) -> None:
        """学習データストア初期化"""
        try:
            # モデル別データストア初期化
            for model_name in self.models.keys():
                self.training_data_store[model_name] = []
                self.performance_history[model_name] = []

            self.logger.info("Training data store initialized")

        except Exception as e:
            self.logger.error(f"Data store initialization failed: {e}")
            raise

    def extract_features(
        self, optimization_data: Dict[str, Any]
    ) -> Tuple[np.ndarray, List[str]]:
        """Phase B運用データ特徴量抽出"""
        try:
            # Phase B運用統計データ活用・AI学習用特徴量生成
            features, feature_names = self.feature_extractor.extract_features(
                optimization_data, feature_types=["basic", "statistical", "temporal"]
            )

            self.logger.debug(
                f"Extracted {len(feature_names)} features for ML processing"
            )
            return features, feature_names

        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            # 空の特徴量を返す（フォールバック）
            return np.array([]), []

    def train_basic_models(
        self, training_data: Dict[str, TrainingData]
    ) -> Dict[str, bool]:
        """基本予測モデル訓練（85%以上精度目標）"""
        training_results = {}

        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 並列モデル訓練
                training_futures = {}

                for model_name, data in training_data.items():
                    if model_name in self.models:
                        future = executor.submit(
                            self._train_single_model, model_name, data
                        )
                        training_futures[model_name] = future

                # 訓練結果取得
                for model_name, future in training_futures.items():
                    try:
                        training_results[model_name] = future.result(
                            timeout=60.0
                        )  # 60秒タイムアウト
                    except Exception as e:
                        self.logger.error(f"Model {model_name} training failed: {e}")
                        training_results[model_name] = False

            # 成功率計算
            success_count = sum(1 for success in training_results.values() if success)
            total_models = len(training_results)
            success_rate = success_count / total_models if total_models > 0 else 0.0

            self.logger.info(
                f"Model training completed: {success_count}/{total_models} models "
                f"successful ({success_rate*100:.1f}%)"
            )
            return training_results

        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return {}

    def _train_single_model(self, model_name: str, data: TrainingData) -> bool:
        """【メモリリーク対策・例外処理強化】単一モデル訓練"""
        try:

            if model_name not in self.models:
                self.logger.error(f"Unknown model: {model_name}")
                return False

            model = self.models[model_name]

            # モデル訓練実行
            training_success = model.train(data)

            if training_success:
                # 学習データストアに追加（メモリリーク対策）
                self.training_data_store[model_name].append(data)

                # ストアサイズ制限
                if (
                    len(self.training_data_store[model_name])
                    > self._training_data_max_size
                ):
                    keep_size = self._training_data_max_size // 2
                    self.training_data_store[model_name] = self.training_data_store[
                        model_name
                    ][-keep_size:]
                    self.logger.debug(
                        f"Training data for {model_name} trimmed to {keep_size} records"
                    )

                self.logger.info(f"Model {model_name} training successful")
                return True
            else:
                self.logger.warning(f"Model {model_name} training failed")
                return False

        except Exception as e:
            self.logger.error(f"Training failed for model {model_name}: {e}")
            return False

    def predict_optimization_opportunities(
        self, context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化機会AI予測（リアルタイム予測・Phase B設定協調調整・2.0%削減効果実現）"""
        try:
            prediction_start = time.time()

            # キャッシュ確認
            cache_key = self._generate_prediction_cache_key(context_data)
            if cache_key in self.prediction_cache:
                cached_result = self.prediction_cache[cache_key]
                self.logger.debug(f"Using cached prediction: {cache_key}")
                return self._format_optimization_prediction(
                    cached_result, from_cache=True
                )

            # 特徴量抽出
            features, feature_names = self.extract_features(context_data)
            if features.size == 0:
                self.logger.warning(
                    "Feature extraction failed, using fallback prediction"
                )
                return {
                    "optimization_opportunities": ["basic_optimization"],
                    "predictions": {},
                    "integrated_confidence": 0.0,
                    "expected_improvement": 0.0,
                    "processing_time": time.time() - prediction_start,
                    "model_contributions": {},
                }

            # 並列予測実行
            predictions = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                prediction_futures = {}

                for model_name, model in self.models.items():
                    if model.is_trained:
                        future = executor.submit(model.predict, features)
                        prediction_futures[model_name] = future

                # 予測結果取得
                for model_name, future in prediction_futures.items():
                    try:
                        predictions[model_name] = future.result(
                            timeout=2.0
                        )  # 2秒タイムアウト
                    except Exception as e:
                        self.logger.warning(f"Prediction failed for {model_name}: {e}")
                        predictions[model_name] = PredictionResponse(
                            prediction=0.0, confidence=0.0, processing_time=0.0
                        )

            # 統合予測結果生成
            integrated_result = self._integrate_predictions(predictions, context_data)

            # 最適化機会特定
            optimization_opportunities = self._identify_optimization_opportunities(
                integrated_result, context_data
            )

            # 結果構築
            final_result = {
                "optimization_opportunities": optimization_opportunities,
                "predictions": {
                    name: pred.__dict__ for name, pred in predictions.items()
                },
                "integrated_confidence": integrated_result.get("confidence", 0.0),
                "expected_improvement": integrated_result.get("improvement", 0.0),
                "processing_time": time.time() - prediction_start,
                "model_contributions": integrated_result.get("model_contributions", {}),
            }

            # キャッシュ保存
            self._update_prediction_cache(cache_key, final_result)

            self.logger.info(
                f"Optimization opportunities predicted in {final_result['processing_time']:.3f}s"
            )
            return final_result

        except Exception as e:
            self.logger.error(f"Prediction optimization failed: {e}")
            return {
                "optimization_opportunities": ["basic_optimization"],
                "predictions": {},
                "integrated_confidence": 0.0,
                "expected_improvement": 0.0,
                "processing_time": 0.0,
                "model_contributions": {},
                "error": str(e),
            }

    def _integrate_predictions(
        self, predictions: Dict[str, PredictionResponse], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """予測結果統合"""
        try:
            # 効率性予測統合
            efficiency_pred = predictions.get("efficiency_predictor")
            predicted_efficiency = (
                efficiency_pred.prediction if efficiency_pred else 0.0
            )
            efficiency_confidence = (
                efficiency_pred.confidence if efficiency_pred else 0.0
            )

            # パターン分析統合
            pattern_pred = predictions.get("pattern_classifier")
            usage_pattern = pattern_pred.prediction if pattern_pred else "unknown"
            pattern_confidence = pattern_pred.confidence if pattern_pred else 0.0

            # 最適化推奨統合
            optimization_pred = predictions.get("optimization_recommender")
            recommended_optimization = (
                optimization_pred.prediction if optimization_pred else "basic"
            )
            optimization_confidence = (
                optimization_pred.confidence if optimization_pred else 0.0
            )

            # 統合信頼度計算
            confidences = [
                efficiency_confidence,
                pattern_confidence,
                optimization_confidence,
            ]
            integrated_confidence = (
                np.mean([c for c in confidences if c > 0.0])
                if any(c > 0.0 for c in confidences)
                else 0.0
            )

            # 期待改善効果計算
            base_improvement = max(
                0.0, predicted_efficiency - context.get("current_efficiency", 66.8)
            )
            confidence_adjustment = integrated_confidence * 0.5  # 信頼度による調整
            expected_improvement = min(
                2.0, base_improvement + confidence_adjustment
            )  # 最大2.0%

            return {
                "predicted_efficiency": predicted_efficiency,
                "usage_pattern": usage_pattern,
                "recommended_optimization": recommended_optimization,
                "confidence": integrated_confidence,
                "improvement": expected_improvement,
                "model_contributions": {
                    "efficiency_predictor": efficiency_confidence,
                    "pattern_classifier": pattern_confidence,
                    "optimization_recommender": optimization_confidence,
                },
            }

        except Exception as e:
            self.logger.error(f"Prediction integration failed: {e}")
            return {
                "predicted_efficiency": 0.0,
                "usage_pattern": "unknown",
                "recommended_optimization": "basic",
                "confidence": 0.0,
                "improvement": 0.0,
                "model_contributions": {},
            }

    def _identify_optimization_opportunities(
        self, integrated_result: Dict[str, Any], context: Dict[str, Any]
    ) -> List[str]:
        """最適化機会特定"""
        opportunities = []

        try:
            # 効率性ベース機会特定
            predicted_efficiency = integrated_result.get("predicted_efficiency", 0.0)
            current_efficiency = context.get("current_efficiency", 66.8)

            if predicted_efficiency > current_efficiency + 1.0:
                opportunities.append("high_efficiency_optimization")

            # 使用パターンベース機会特定
            usage_pattern = integrated_result.get("usage_pattern", "unknown")
            if usage_pattern == "repetitive":
                opportunities.append("pattern_based_optimization")
            elif usage_pattern == "complex":
                opportunities.append("complexity_reduction")
            elif usage_pattern == "large_content":
                opportunities.append("content_size_optimization")

            # 推奨最適化ベース機会特定
            recommended_optimization = integrated_result.get(
                "recommended_optimization", "basic"
            )
            if recommended_optimization != "basic":
                opportunities.append(f"{recommended_optimization}_optimization")

            # コンテキストベース機会特定
            content_size = context.get("content_size", 0)
            if content_size > 5000:
                opportunities.append("large_content_handling")

            complexity_score = context.get("complexity_score", 0.0)
            if complexity_score > 0.7:
                opportunities.append("complexity_optimization")

            # デフォルト機会
            if not opportunities:
                opportunities.append("basic_optimization")

            # 重複除去・優先度順
            unique_opportunities = list(
                dict.fromkeys(opportunities)
            )  # 順序保持重複除去

            return unique_opportunities[:5]  # 最大5つの機会

        except Exception as e:
            self.logger.error(f"Optimization opportunity identification failed: {e}")
            return ["basic_optimization"]

    def _generate_prediction_cache_key(self, context_data: Dict[str, Any]) -> str:
        """予測キャッシュキー生成"""
        try:
            key_components = [
                str(context_data.get("operation_type", "default")),
                str(context_data.get("content_size", 0) // 100),  # 100単位でグループ化
                str(round(context_data.get("complexity_score", 0.0), 1)),
                str(len(context_data.get("recent_operations", []))),
            ]
            return "_".join(key_components)

        except Exception as e:
            self.logger.warning(f"Cache key generation failed: {e}")
            return "default_cache_key"

    def _update_prediction_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """【メモリリーク対策】LRU予測キャッシュ更新"""
        try:
            # 【LRUキャッシュ】サイズ制限
            if len(self.prediction_cache) >= self.cache_max_size:
                # 最も古いエントリを削除（FIFO + LRU）
                oldest_key = next(iter(self.prediction_cache))
                del self.prediction_cache[oldest_key]
                self.logger.debug(f"Cache evicted oldest entry: {oldest_key}")

            # 簡易化された結果をキャッシュ
            cached_result = {
                "optimization_opportunities": result.get(
                    "optimization_opportunities", []
                ),
                "expected_improvement": result.get("expected_improvement", 0.0),
                "integrated_confidence": result.get("integrated_confidence", 0.0),
                "cached_at": time.time(),
            }

            self.prediction_cache[cache_key] = cached_result

            self.logger.debug(
                f"Cache updated: {len(self.prediction_cache)}/{self.cache_max_size} entries"
            )

        except Exception as e:
            self.logger.warning(f"Cache update failed: {e}")

    def _format_optimization_prediction(
        self, cached_result: Dict[str, Any], from_cache: bool = False
    ) -> Dict[str, Any]:
        """最適化予測結果フォーマット"""
        return {
            "optimization_opportunities": cached_result.get(
                "optimization_opportunities", []
            ),
            "expected_improvement": cached_result.get("expected_improvement", 0.0),
            "integrated_confidence": cached_result.get("integrated_confidence", 0.0),
            "processing_time": 0.001 if from_cache else 0.0,  # キャッシュは高速
            "from_cache": from_cache,
            "cached_at": cached_result.get("cached_at", 0.0),
        }

    def _preprocess_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """データ前処理"""
        try:
            # データ正規化・異常値処理
            processed_data = raw_data.copy()

            # 数値データ正規化
            if "content_size" in processed_data:
                processed_data["content_size"] = max(0, processed_data["content_size"])

            if "complexity_score" in processed_data:
                processed_data["complexity_score"] = max(
                    0.0, min(1.0, processed_data.get("complexity_score", 0.0))
                )

            return processed_data

        except Exception as e:
            self.logger.error(f"Data preprocessing failed: {e}")
            return raw_data.copy()  # フォールバック: 元データ返却

    def _execute_model_prediction(
        self, model_name: str, features: np.ndarray
    ) -> PredictionResponse:
        """モデル予測実行"""
        try:
            if model_name not in self.models:
                return PredictionResponse(prediction=0.0, confidence=0.0)

            model = self.models[model_name]
            if not model.is_trained:
                return PredictionResponse(prediction=0.0, confidence=0.0)

            # モデル予測実行
            return model.predict(features)

        except Exception as e:
            self.logger.error(f"Model prediction failed for {model_name}: {e}")
            return PredictionResponse(
                prediction=0.0, confidence=0.0, processing_time=0.0
            )

    def _postprocess_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """結果後処理"""
        try:
            # 結果正規化・品質チェック
            processed_results = results.copy()

            # 改善効果上限チェック
            if "expected_improvement" in processed_results:
                processed_results["expected_improvement"] = min(
                    2.0, max(0.0, processed_results["expected_improvement"])
                )

            # 信頼度正規化
            if "integrated_confidence" in processed_results:
                processed_results["integrated_confidence"] = min(
                    1.0, max(0.0, processed_results["integrated_confidence"])
                )

            return processed_results

        except Exception as e:
            self.logger.error(f"Result postprocessing failed: {e}")
            return results.copy()  # フォールバック: 元結果返却

    def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """モデル性能取得"""
        try:
            if model_name:
                if model_name in self.models:
                    model = self.models[model_name]
                    return {
                        "model_name": model_name,
                        "is_trained": model.is_trained,
                        "performance_metrics": model.performance_metrics,
                        "feature_count": len(model.feature_names),
                    }
                else:
                    return {"error": f"Model {model_name} not found"}

            # Get all model performances
            all_performance = {}
            for name, model in self.models.items():
                all_performance[name] = {
                    "model_name": name,
                    "is_trained": model.is_trained,
                    "performance_metrics": model.performance_metrics,
                    "feature_count": len(model.feature_names),
                }
            return all_performance

        except Exception as e:
            self.logger.error(f"Model performance retrieval failed: {e}")
            return {"error": str(e)}

    def save_models(self, model_path: Path) -> bool:
        """モデル保存"""
        try:
            model_path.mkdir(parents=True, exist_ok=True)

            saved_count = 0
            for model_name, model in self.models.items():
                if model.is_trained:
                    model_file = model_path / f"{model_name}.pkl"

                    # モデル保存データ構築
                    model_data = {
                        "model": model.model,
                        "scaler": model.scaler,
                        "feature_names": model.feature_names,
                        "performance_metrics": model.performance_metrics,
                        "config": model.config,
                    }

                    # ラベルエンコーダー保存（分類モデル用）
                    if hasattr(model, "label_encoder"):
                        model_data["label_encoder"] = model.label_encoder

                    with open(model_file, "wb") as f:
                        pickle.dump(model_data, f)

                    saved_count += 1

            self.logger.info(f"Saved {saved_count} trained models to {model_path}")
            return saved_count > 0
        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")
            return False  # フォールバック: 保存失敗

    def load_models(self, model_path: Path) -> bool:
        """モデル読込"""
        try:
            loaded_count = 0

            for model_name in self.models.keys():
                model_file = model_path / f"{model_name}.pkl"

                if model_file.exists():
                    with open(model_file, "rb") as f:
                        model_data = pickle.load(f)

                    # モデル復元
                    model = self.models[model_name]
                    model.model = model_data["model"]
                    model.scaler = model_data["scaler"]
                    model.feature_names = model_data["feature_names"]
                    model.performance_metrics = model_data["performance_metrics"]
                    model.is_trained = True

                    # ラベルエンコーダー復元（分類モデル用）
                    if "label_encoder" in model_data and hasattr(
                        model, "label_encoder"
                    ):
                        model.label_encoder = model_data["label_encoder"]

                    loaded_count += 1

            self.logger.info(f"Loaded {loaded_count} models from {model_path}")
            return loaded_count > 0
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            return False  # フォールバック: 読み込み失敗

    def reset_cache(self) -> None:
        """キャッシュリセット"""
        self.prediction_cache.clear()
        self.logger.info("Prediction cache cleared")

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        try:
            trained_models = sum(
                1 for model in self.models.values() if model.is_trained
            )
            total_models = len(self.models)

            return {
                "models": {
                    "total": total_models,
                    "trained": trained_models,
                    "training_rate": (
                        trained_models / total_models if total_models > 0 else 0.0
                    ),
                },
                "cache": {
                    "size": len(self.prediction_cache),
                    "max_size": self.cache_max_size,
                    "utilization": len(self.prediction_cache) / self.cache_max_size,
                },
                "data_store": {
                    "total_datasets": sum(
                        len(datasets) for datasets in self.training_data_store.values()
                    ),
                    "models_with_data": sum(
                        1 for datasets in self.training_data_store.values() if datasets
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"System status retrieval failed: {e}")
            return {"error": str(e)}
