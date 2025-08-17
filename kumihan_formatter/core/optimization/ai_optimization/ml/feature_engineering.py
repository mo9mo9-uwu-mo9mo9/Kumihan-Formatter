"""特徴量エンジニアリング処理"""

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kumihan_formatter.core.utilities.logger import get_logger


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
