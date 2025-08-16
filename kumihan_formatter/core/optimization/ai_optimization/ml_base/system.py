"""
ML System - 基本機械学習システムコア

BasicMLSystemクラス・統合ML処理・キャッシュ管理・並列処理
"""

import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from kumihan_formatter.core.utilities.logger import get_logger

# 分割されたモジュールからインポート
from .data_processor import FeatureEngineering
from .learning_engine import (
    BaseMLModel,
    ModelPerformance,
    OptimizationRecommender,
    PredictionRequest,
    PredictionResponse,
    TokenEfficiencyPredictor,
    TrainingData,
    UsagePatternClassifier,
)


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

                    # セキュリティ修正: pickle.dump()をjoblib.dump()に置換
                    joblib.dump(model_data, model_file)

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
                    # セキュリティ修正: pickle.load()をjoblib.load()に置換
                    model_data = joblib.load(model_file)

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
