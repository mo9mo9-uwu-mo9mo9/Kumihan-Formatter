"""
Phase B.4-Beta継続学習システム実装 - コア機能

データ品質管理・ハイパーパラメータ自動最適化
- データ品質監視・異常検出・バイアス分析
- ハイパーパラメータ自動最適化・履歴管理
"""

import time
import warnings
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, List, cast

import numpy as np

if TYPE_CHECKING:
    import scipy.stats as stats

    # Removed unused ML imports: sklearn, lightgbm, xgboost

from kumihan_formatter.core.utilities.logger import get_logger

from ..basic_ml_system import TrainingData

warnings.filterwarnings("ignore")

OPTUNA_AVAILABLE = True
try:
    from optuna import Trial, create_study
except ImportError:
    OPTUNA_AVAILABLE = False
    # Fallback for type hints when optuna is not available
    Trial = None
    create_study = None


class DataQualityManager:
    """データ品質管理システム"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config

        # 品質履歴
        self.quality_history: deque[Dict[str, Any]] = deque(maxlen=1000)

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
                            if float(abs(label_skewness)) > 1.0
                            else "medium" if float(abs(label_skewness)) > 0.5 else "low"
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
            return {"bias_score": 0.0, "error": str(e)}

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

            return cast(float, min(1.0, score))
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
                                "normality_score": (1.0 if shapiro_p > 0.05 else 0.0),
                            }
                        )
                    except Exception:
                        distribution_analysis["normality"] = "unknown"  # type: ignore[assignment]

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
        data_stats: Dict[str, Any],
        outlier_detection: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        distribution_analysis: Dict[str, Any],
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

            return cast(float, max(0.0, min(1.0, score)))
        except Exception as e:
            self.logger.error(f"Quality score calculation failed: {e}")
            return 0.0

    def _generate_quality_recommendations(
        self,
        quality_score: float,
        outlier_detection: Dict[str, Any],
        bias_analysis: Dict[str, Any],
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
