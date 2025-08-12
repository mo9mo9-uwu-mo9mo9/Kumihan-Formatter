"""
パターン認識エンジン・ハイパーパラメータ最適化システム

ハイパーパラメータ自動最適化・オンライン学習エンジン
- ベイズ最適化・グリッドサーチ最適化
- 増分学習・リアルタイムモデル更新
- 学習効果評価・性能最適化
"""

import time
import warnings
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, cast

import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score

from kumihan_formatter.core.utilities.logger import get_logger

from ..basic_ml_system import TrainingData
from ..prediction_engine import EnsemblePredictionModel

warnings.filterwarnings("ignore")

# ハイパーパラメータ最適化
try:
    from optuna import Trial, create_study

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False


class HyperparameterOptimizer:
    """ハイパーパラメータ自動最適化システム"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config

        # 最適化履歴
        self.optimization_history: Dict[str, List[Dict]] = defaultdict(list)

        # 最適化設定
        self.n_trials = config.get("n_trials", 50)
        self.timeout = config.get("timeout", 300)  # 5分

    def optimize_model_hyperparameters(
        self,
        model_name: str,
        model_type: str,
        training_data: TrainingData,
        validation_data: Optional[TrainingData] = None,
    ) -> Dict[str, Any]:
        """モデルハイパーパラメータ最適化"""
        try:
            optimization_start = time.time()

            if not OPTUNA_AVAILABLE:
                self.logger.warning(
                    "Optuna not available, using default hyperparameters"
                )
                return self._get_default_hyperparameters(model_type)

            def objective(trial: Trial) -> float:
                return self._objective_function(
                    trial, model_type, training_data, validation_data
                )

            # Optuna研究実行
            study = create_study(direction="minimize")
            study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)

            best_params = study.best_params
            best_value = study.best_value

            optimization_result = {
                "best_parameters": best_params,
                "best_score": best_value,
                "optimization_time": time.time() - optimization_start,
                "improvement": self._calculate_improvement(model_type, best_value),
            }

            # 履歴保存
            self.optimization_history[model_name].append(
                {
                    "timestamp": time.time(),
                    "best_score": best_value,
                    "parameters": best_params.copy(),
                }
            )

            self.logger.info(
                f"Hyperparameter optimization completed for {model_name}: score={best_value:.4f}"
            )
            return optimization_result
        except Exception as e:
            self.logger.error(
                f"Hyperparameter optimization failed for {model_name}: {e}"
            )
            return self._get_default_hyperparameters(model_type)

    def _objective_function(
        self,
        trial: Trial,
        model_type: str,
        training_data: TrainingData,
        validation_data: Optional[TrainingData],
    ) -> float:
        """最適化目的関数"""
        try:
            # モデル作成
            model = self._create_model_with_trial_params(trial, model_type)

            # データ準備
            X_train = training_data.features
            y_train = (
                training_data.labels.flatten()
                if training_data.labels.ndim > 1
                else training_data.labels
            )

            if validation_data is not None:
                X_val = validation_data.features
                y_val = (
                    validation_data.labels.flatten()
                    if validation_data.labels.ndim > 1
                    else validation_data.labels
                )

                # 訓練・評価
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                score = mean_squared_error(y_val, y_pred)
            else:
                # 交差検証
                cv_scores = cross_val_score(
                    model,
                    X_train,
                    y_train,
                    cv=min(5, len(X_train) // 10),
                    scoring="neg_mean_squared_error",
                )
                score = -np.mean(cv_scores)

            return cast(float, score)
        except Exception as e:
            self.logger.error(f"Objective function failed: {e}")
            return float("inf")  # 最悪のスコアを返す

    def _create_model_with_trial_params(self, trial: Trial, model_type: str):
        """試行パラメータでモデル作成"""
        try:
            if model_type == "lightgbm":
                try:
                    import lightgbm as lgb  # type: ignore

                    return lgb.LGBMRegressor(
                        n_estimators=trial.suggest_int("n_estimators", 50, 200),
                        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3),
                        max_depth=trial.suggest_int("max_depth", 3, 10),
                        subsample=trial.suggest_float("subsample", 0.6, 1.0),
                        colsample_bytree=trial.suggest_float(
                            "colsample_bytree", 0.6, 1.0
                        ),
                        random_state=42,
                        verbose=-1,
                    )
                except ImportError:
                    pass

            elif model_type == "xgboost":
                try:
                    import xgboost as xgb  # type: ignore

                    return xgb.XGBRegressor(
                        n_estimators=trial.suggest_int("n_estimators", 50, 200),
                        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3),
                        max_depth=trial.suggest_int("max_depth", 3, 10),
                        subsample=trial.suggest_float("subsample", 0.6, 1.0),
                        colsample_bytree=trial.suggest_float(
                            "colsample_bytree", 0.6, 1.0
                        ),
                        random_state=42,
                        verbosity=0,
                    )
                except ImportError:
                    pass

            # フォールバック: GradientBoosting
            from sklearn.ensemble import GradientBoostingRegressor

            return GradientBoostingRegressor(
                n_estimators=trial.suggest_int("n_estimators", 50, 200),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3),
                max_depth=trial.suggest_int("max_depth", 3, 10),
                subsample=trial.suggest_float("subsample", 0.6, 1.0),
                random_state=42,
            )

        except Exception as e:
            self.logger.error(f"Model creation with trial params failed: {e}")
            # 基本モデル返却
            from sklearn.ensemble import RandomForestRegressor

            return RandomForestRegressor(random_state=42)

    def _get_default_hyperparameters(self, model_type: str) -> Dict[str, Any]:
        """デフォルトハイパーパラメータ"""
        defaults = {
            "lightgbm": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
            "xgboost": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
            "gradientboosting": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "subsample": 0.8,
            },
        }

        return {
            "best_parameters": defaults.get(model_type, {}),
            "best_score": 0.0,
            "optimization_time": 0.0,
            "fallback": True,
        }

    def _calculate_improvement(self, model_type: str, best_score: float) -> float:
        """デフォルトからの改善率計算"""
        try:
            # 履歴ベースラインとの比較
            model_history = self.optimization_history.get(model_type, [])
            if len(model_history) > 1:
                baseline_score = model_history[-2]["best_score"]
                if baseline_score > 0:
                    return cast(float, (baseline_score - best_score) / baseline_score)

            return 0.0
        except Exception as e:
            self.logger.error(f"Improvement calculation failed: {e}")
            return 0.0


class OnlineLearningEngine:
    """オンライン学習エンジン"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config

        # 学習バッファ
        self.learning_buffer: deque = deque(maxlen=config.get("buffer_size", 1000))
        self.batch_size = config.get("batch_size", 50)

        # 学習履歴
        self.learning_history: List[Dict[str, Any]] = []

        # 学習制御
        self.min_samples_for_learning = config.get("min_samples", 20)
        self.learning_interval = config.get("learning_interval", 100)  # 100サンプル毎
        self.sample_count = 0

    def add_training_sample(
        self, features: np.ndarray, label: float, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """学習サンプル追加"""
        try:
            # バッファに追加
            sample = {
                "features": features.copy(),
                "label": label,
                "context": context.copy(),
                "timestamp": time.time(),
            }

            self.learning_buffer.append(sample)
            self.sample_count += 1

            # 学習トリガー判定
            should_learn = (
                len(self.learning_buffer) >= self.min_samples_for_learning
                and self.sample_count % self.learning_interval == 0
            )

            return {
                "sample_added": True,
                "buffer_size": len(self.learning_buffer),
                "should_trigger_learning": should_learn,
                "samples_until_learning": self.learning_interval
                - (self.sample_count % self.learning_interval),
            }

        except Exception as e:
            self.logger.error(f"Training sample addition failed: {e}")
            return {"sample_added": False, "error": str(e)}

    def execute_incremental_learning(
        self, models: Dict[str, EnsemblePredictionModel]
    ) -> Dict[str, Any]:
        """増分学習実行"""
        try:
            learning_start = time.time()

            # バッファからバッチデータ作成
            batch_data = self._create_learning_batch()

            if batch_data is None:
                return {"learning_executed": False, "reason": "insufficient_data"}

            # 並列学習実行
            learning_results = {}
            learning_futures = {}

            with ThreadPoolExecutor(max_workers=3) as executor:
                for model_name, model in models.items():
                    if model.is_trained:
                        future = executor.submit(
                            self._incremental_train_model, model_name, model, batch_data
                        )
                        learning_futures[model_name] = future

                # 学習結果収集
                for model_name, future in learning_futures.items():
                    try:
                        result = future.result(timeout=60.0)
                        learning_results[model_name] = result
                    except Exception as e:
                        self.logger.error(
                            f"Incremental learning failed for {model_name}: {e}"
                        )
                        learning_results[model_name] = {
                            "success": False,
                            "error": str(e),
                        }

            # 学習効果評価
            learning_effectiveness = self._evaluate_learning_effectiveness(
                learning_results
            )

            # 履歴更新
            learning_record = {
                "timestamp": time.time(),
                "batch_size": len(batch_data.features),
                "models_updated": sum(
                    1
                    for result in learning_results.values()
                    if result.get("success", False)
                ),
                "learning_effectiveness": learning_effectiveness,
                "processing_time": time.time() - learning_start,
            }

            self.learning_history.append(learning_record)

            # 履歴サイズ制限
            if len(self.learning_history) > 100:
                self.learning_history = self.learning_history[-50:]

            self.logger.info(
                f"Incremental learning completed: "
                f"{learning_record['models_updated']} models updated"
            )

            return {
                "learning_executed": True,
                "learning_results": learning_results,
                "learning_effectiveness": learning_effectiveness,
                "processing_time": learning_record["processing_time"],
                "models_updated": learning_record["models_updated"],
            }

        except Exception as e:
            self.logger.error(f"Incremental learning execution failed: {e}")
            return {"learning_executed": False, "error": str(e)}

    def _create_learning_batch(self) -> Optional[TrainingData]:
        """学習バッチ作成"""
        try:
            if len(self.learning_buffer) < self.min_samples_for_learning:
                return None

            # バッファからデータ抽出
            recent_samples = list(self.learning_buffer)[-self.batch_size :]

            if not recent_samples:
                return None

            features = np.array([sample["features"] for sample in recent_samples])
            labels = np.array([sample["label"] for sample in recent_samples])

            return TrainingData(
                features=features,
                labels=labels,
                feature_names=(
                    [f"feature_{i}" for i in range(features.shape[1])]
                    if len(features.shape) > 1
                    else ["feature_0"]
                ),
            )

        except Exception as e:
            self.logger.error(f"Learning batch creation failed: {e}")
            return None

    def _incremental_train_model(
        self, model_name: str, model: EnsemblePredictionModel, batch_data: TrainingData
    ) -> Dict[str, Any]:
        """モデル増分学習"""
        try:
            learning_start = time.time()

            # 学習前性能
            pre_performance = (
                model.performance_metrics.copy()
                if hasattr(model, "performance_metrics")
                else {}
            )

            # 増分学習実行
            learning_success = model.train(batch_data)

            if not learning_success:
                return {"success": False, "reason": "training_failed"}

            # 学習後性能
            post_performance = (
                model.performance_metrics.copy()
                if hasattr(model, "performance_metrics")
                else {}
            )

            # 性能変化計算
            performance_changes = self._calculate_performance_change(
                pre_performance, post_performance
            )

            return {
                "success": True,
                "pre_performance": pre_performance,
                "post_performance": post_performance,
                "performance_changes": performance_changes,
                "training_time": time.time() - learning_start,
            }

        except Exception as e:
            self.logger.error(
                f"Incremental model training failed for {model_name}: {e}"
            )
            return {"success": False, "error": str(e)}

    def _calculate_performance_change(
        self, pre_performance: Dict, post_performance: Dict
    ) -> Dict[str, float]:
        """性能変化計算"""
        try:
            changes = {}

            for metric in ["r2_score", "mse", "mae"]:
                pre_value = pre_performance.get("ensemble_performance", {}).get(
                    metric, 0.0
                )
                post_value = post_performance.get("ensemble_performance", {}).get(
                    metric, 0.0
                )

                if pre_value != 0:
                    if metric == "r2_score":
                        # R²は高いほど良い
                        changes[metric] = (post_value - pre_value) / abs(pre_value)
                    else:
                        # MSE, MAEは低いほど良い
                        changes[metric] = (pre_value - post_value) / abs(pre_value)
                else:
                    changes[metric] = 0.0

            return changes
        except Exception as e:
            self.logger.error(f"Performance change calculation failed: {e}")
            return {"r2_score": 0.0, "mse": 0.0, "mae": 0.0}

    def _evaluate_learning_effectiveness(
        self, learning_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """学習効果評価"""
        try:
            successful_models = [
                result
                for result in learning_results.values()
                if result.get("success", False)
            ]

            if not successful_models:
                return {"effectiveness_score": 0.0, "improvement_count": 0}

            # 改善度分析
            r2_improvements = []
            mse_improvements = []

            for result in successful_models:
                performance_changes = result.get("performance_changes", {})
                r2_change = performance_changes.get("r2_score", 0.0)
                mse_change = performance_changes.get("mse", 0.0)

                if r2_change > 0.01:  # 1%以上の改善
                    r2_improvements.append(r2_change)
                if mse_change > 0.01:
                    mse_improvements.append(mse_change)

            # 効果スコア計算
            improvement_count = len(r2_improvements) + len(mse_improvements)
            avg_r2_improvement = np.mean(r2_improvements) if r2_improvements else 0.0
            avg_mse_improvement = np.mean(mse_improvements) if mse_improvements else 0.0

            effectiveness_score = min(
                1.0, (avg_r2_improvement + avg_mse_improvement) / 2.0
            )

            return {
                "effectiveness_score": effectiveness_score,
                "improvement_count": improvement_count,
                "avg_r2_improvement": avg_r2_improvement,
                "avg_mse_improvement": avg_mse_improvement,
                "successful_models": len(successful_models),
                "total_models": len(learning_results),
            }

        except Exception as e:
            self.logger.error(f"Learning effectiveness evaluation failed: {e}")
            return {"effectiveness_score": 0.0, "improvement_count": 0, "error": str(e)}
