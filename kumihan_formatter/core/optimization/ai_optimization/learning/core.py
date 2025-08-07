"""
Phase B.4-Beta継続学習システム実装 - コア機能

データ品質管理・ハイパーパラメータ自動最適化
- データ品質監視・異常検出・バイアス分析
- ハイパーパラメータ自動最適化・履歴管理
"""

import time
import warnings
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

import numpy as np
import scipy.stats as stats
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score

from kumihan_formatter.core.utilities.logger import get_logger

from ..basic_ml_system import TrainingData

warnings.filterwarnings("ignore")

# ハイパーパラメータ最適化
try:
    from optuna import Trial, create_study

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False


class DataQualityManager:
    """データ品質管理システム"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config

        # 品質履歴
        self.quality_history: deque = deque(maxlen=1000)

        # 異常検出閾値
        self.outlier_threshold = config.get("outlier_threshold", 3.0)
        self.bias_threshold = config.get("bias_threshold", 0.1)

    def validate_training_data(self, training_data: TrainingData) -> Dict[str, Any]:
        """学習データ品質検証"""
        try:
            validation_start = time.time()

            # 基本統計
            data_stats = self._calculate_data_statistics(training_data)

            # 異常値検出
            outlier_detection = self._detect_outliers(training_data)

            # バイアス検出
            bias_analysis = self._analyze_bias(training_data)

            # データ分布分析
            distribution_analysis = self._analyze_distribution(training_data)

            # 総合品質スコア
            quality_score = self._calculate_quality_score(
                data_stats, outlier_detection, bias_analysis, distribution_analysis
            )

            validation_result = {
                "quality_score": quality_score,
                "data_statistics": data_stats,
                "outlier_detection": outlier_detection,
                "bias_analysis": bias_analysis,
                "distribution_analysis": distribution_analysis,
                "validation_time": time.time() - validation_start,
                "recommendations": self._generate_quality_recommendations(
                    quality_score, outlier_detection, bias_analysis
                ),
            }

            # 履歴保存
            self.quality_history.append(
                {
                    "timestamp": time.time(),
                    "quality_score": quality_score,
                    "data_size": len(training_data.features),
                }
            )

            self.logger.debug(
                f"Data quality validation completed: score={quality_score:.3f}"
            )
            return validation_result

        except Exception as e:
            self.logger.error(f"Data quality validation failed: {e}")
            return {"quality_score": 0.0, "error": str(e)}

    def _calculate_data_statistics(self, training_data: TrainingData) -> Dict[str, Any]:
        """データ統計計算"""
        try:
            features = training_data.features
            labels = training_data.labels

            return {
                "sample_count": len(features),
                "feature_count": features.shape[1] if len(features.shape) > 1 else 1,
                "feature_means": (
                    np.mean(features, axis=0).tolist() if len(features) > 0 else []
                ),
                "feature_stds": (
                    np.std(features, axis=0).tolist() if len(features) > 0 else []
                ),
                "label_mean": float(np.mean(labels)) if len(labels) > 0 else 0.0,
                "label_std": float(np.std(labels)) if len(labels) > 0 else 0.0,
                "missing_values": int(np.sum(np.isnan(features)))
                + int(np.sum(np.isnan(labels))),
            }

        except Exception as e:
            self.logger.error(f"Data statistics calculation failed: {e}")
            return {"sample_count": 0, "error": str(e)}

    def _detect_outliers(self, training_data: TrainingData) -> Dict[str, Any]:
        """異常値検出"""
        try:
            features = training_data.features
            labels = training_data.labels

            # Z-score異常値検出
            if len(features) > 0:
                z_scores = np.abs(stats.zscore(features, axis=0, nan_policy="omit"))
                feature_outliers = np.sum(z_scores > self.outlier_threshold, axis=1)
            else:
                feature_outliers = np.array([])

            # ラベル異常値検出
            if len(labels) > 0:
                label_z_scores = np.abs(stats.zscore(labels, nan_policy="omit"))
                label_outliers = label_z_scores > self.outlier_threshold
            else:
                label_outliers = np.array([])

            # 総合異常値
            total_outliers = len(feature_outliers) + int(np.sum(label_outliers))
            outlier_ratio = (
                total_outliers / max(1, len(features)) if len(features) > 0 else 0.0
            )

            return {
                "feature_outlier_count": (
                    int(np.sum(feature_outliers > 0))
                    if len(feature_outliers) > 0
                    else 0
                ),
                "label_outlier_count": (
                    int(np.sum(label_outliers)) if len(label_outliers) > 0 else 0
                ),
                "total_outlier_count": total_outliers,
                "outlier_ratio": outlier_ratio,
                "outlier_threshold": self.outlier_threshold,
                "quality_impact": (
                    "high"
                    if outlier_ratio > 0.1
                    else "medium" if outlier_ratio > 0.05 else "low"
                ),
            }

        except Exception as e:
            self.logger.error(f"Outlier detection failed: {e}")
            return {"total_outlier_count": 0, "outlier_ratio": 0.0, "error": str(e)}

    def _analyze_bias(self, training_data: TrainingData) -> Dict[str, Any]:
        """バイアス分析"""
        try:
            features = training_data.features
            labels = training_data.labels

            bias_metrics = {}

            if len(features) > 10:  # 最小サンプルサイズ
                # 特徴量バイアス検出
                feature_correlations = []
                for i in range(features.shape[1]):
                    if np.var(features[:, i]) > 0:
                        correlation = np.corrcoef(features[:, i], labels)[0, 1]
                        if not np.isnan(correlation):
                            feature_correlations.append(abs(correlation))

                if feature_correlations:
                    max_correlation = max(feature_correlations)
                    bias_metrics["max_feature_correlation"] = max_correlation
                    bias_metrics["high_correlation_features"] = sum(
                        1 for corr in feature_correlations if corr > 0.8
                    )

                # ラベル分布バイアス
                label_skewness = stats.skew(labels)
                label_kurtosis = stats.kurtosis(labels)

                bias_metrics.update(
                    {
                        "label_skewness": float(label_skewness),
                        "label_kurtosis": float(label_kurtosis),
                        "distribution_bias": (
                            "high"
                            if abs(label_skewness) > 1.0
                            else "medium" if abs(label_skewness) > 0.5 else "low"
                        ),
                    }
                )

            # 総合バイアススコア
            bias_score = self._calculate_bias_score(bias_metrics)
            bias_metrics["bias_score"] = bias_score
            bias_metrics["bias_level"] = (
                "high" if bias_score > 0.7 else "medium" if bias_score > 0.4 else "low"
            )

            return bias_metrics

        except Exception as e:
            self.logger.error(f"Bias analysis failed: {e}")
            return {"bias_score": 0.0, "bias_level": "unknown", "error": str(e)}

    def _calculate_bias_score(self, bias_metrics: Dict[str, Any]) -> float:
        """バイアススコア計算"""
        try:
            score = 0.0

            # 相関バイアス
            max_correlation = bias_metrics.get("max_feature_correlation", 0.0)
            score += min(1.0, max_correlation) * 0.4

            # 分布バイアス
            skewness = abs(bias_metrics.get("label_skewness", 0.0))
            score += min(1.0, skewness / 2.0) * 0.3

            kurtosis = abs(bias_metrics.get("label_kurtosis", 0.0))
            score += min(1.0, kurtosis / 10.0) * 0.3

            return min(1.0, score)

        except Exception:
            return 0.0

    def _analyze_distribution(self, training_data: TrainingData) -> Dict[str, Any]:
        """データ分布分析"""
        try:
            features = training_data.features
            labels = training_data.labels

            distribution_analysis = {}

            if len(labels) > 10:
                # ラベル分布分析
                distribution_analysis.update(
                    {
                        "label_min": float(np.min(labels)),
                        "label_max": float(np.max(labels)),
                        "label_range": float(np.max(labels) - np.min(labels)),
                        "label_iqr": float(
                            np.percentile(labels, 75) - np.percentile(labels, 25)
                        ),
                        "label_median": float(np.median(labels)),
                    }
                )

                # 正規性検定
                if len(labels) >= 8:  # shapiro-wilk最小サンプル
                    try:
                        shapiro_stat, shapiro_p = stats.shapiro(
                            labels[:5000]
                        )  # サンプル制限
                        distribution_analysis.update(
                            {
                                "shapiro_statistic": float(shapiro_stat),
                                "shapiro_p_value": float(shapiro_p),
                                "normality": (
                                    "normal" if shapiro_p > 0.05 else "non_normal"
                                ),
                            }
                        )
                    except Exception:
                        distribution_analysis["normality"] = "unknown"

            # 特徴量分布サマリー
            if len(features) > 0:
                feature_ranges = np.max(features, axis=0) - np.min(features, axis=0)
                distribution_analysis.update(
                    {
                        "feature_range_mean": float(np.mean(feature_ranges)),
                        "feature_range_std": float(np.std(feature_ranges)),
                        "zero_variance_features": int(
                            np.sum(np.var(features, axis=0) == 0)
                        ),
                    }
                )

            return distribution_analysis

        except Exception as e:
            self.logger.error(f"Distribution analysis failed: {e}")
            return {"error": str(e)}

    def _calculate_quality_score(
        self,
        data_stats: Dict,
        outlier_detection: Dict,
        bias_analysis: Dict,
        distribution_analysis: Dict,
    ) -> float:
        """総合品質スコア計算"""
        try:
            score = 1.0

            # サンプルサイズペナルティ
            sample_count = data_stats.get("sample_count", 0)
            if sample_count < 50:
                score *= 0.7
            elif sample_count < 100:
                score *= 0.85

            # 異常値ペナルティ
            outlier_ratio = outlier_detection.get("outlier_ratio", 0.0)
            score *= 1.0 - min(0.5, outlier_ratio * 2)

            # バイアスペナルティ
            bias_score = bias_analysis.get("bias_score", 0.0)
            score *= 1.0 - bias_score * 0.3

            # 欠損値ペナルティ
            missing_values = data_stats.get("missing_values", 0)
            if missing_values > 0:
                score *= 0.9

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    def _generate_quality_recommendations(
        self, quality_score: float, outlier_detection: Dict, bias_analysis: Dict
    ) -> List[str]:
        """品質改善推奨事項生成"""
        recommendations = []

        try:
            # 品質スコアベース推奨
            if quality_score < 0.6:
                recommendations.append(
                    "データ品質が低いため、データクリーニングを実施してください"
                )

            # 異常値対処
            outlier_ratio = outlier_detection.get("outlier_ratio", 0.0)
            if outlier_ratio > 0.1:
                recommendations.append(
                    "異常値が多く検出されました。外れ値除去を検討してください"
                )

            # バイアス対処
            bias_level = bias_analysis.get("bias_level", "low")
            if bias_level == "high":
                recommendations.append(
                    "データにバイアスが検出されました。データ収集戦略の見直しを推奨します"
                )

            # 分布対処
            distribution_bias = bias_analysis.get("distribution_bias", "low")
            if distribution_bias == "high":
                recommendations.append(
                    "ラベル分布に偏りがあります。データバランシングを検討してください"
                )

            if not recommendations:
                recommendations.append("データ品質は良好です")

        except Exception:
            recommendations.append("品質分析でエラーが発生しました")

        return recommendations


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

            # 最適化問題定義
            def objective(trial: Trial) -> float:
                return self._objective_function(
                    trial, model_type, training_data, validation_data
                )

            # 最適化実行
            study = create_study(direction="minimize")
            study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)

            # 最適パラメータ取得
            best_params = study.best_params
            best_value = study.best_value

            # 結果構築
            optimization_result = {
                "model_name": model_name,
                "model_type": model_type,
                "best_parameters": best_params,
                "best_score": best_value,
                "n_trials": len(study.trials),
                "optimization_time": time.time() - optimization_start,
                "improvement_over_default": self._calculate_improvement(
                    model_type, best_value
                ),
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

            return score

        except Exception as e:
            self.logger.warning(f"Objective function evaluation failed: {e}")
            return float("inf")

    def _create_model_with_trial_params(self, trial: Trial, model_type: str):
        """試行パラメータでモデル作成"""
        try:
            if model_type == "lightgbm":
                try:
                    import lightgbm as lgb

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
                    import xgboost as xgb

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
                    return (baseline_score - best_score) / baseline_score

            return 0.0

        except Exception:
            return 0.0
