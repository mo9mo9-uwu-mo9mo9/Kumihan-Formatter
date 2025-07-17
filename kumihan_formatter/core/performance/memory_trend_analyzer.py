"""メモリトレンド分析機能。

メモリ使用量のトレンド分析とパターン検出を行う専用モジュール。
"""

import time
from typing import Any

from .memory_types import MemorySnapshot


class MemoryTrendAnalyzer:
    """メモリ使用量のトレンド分析機能"""

    def get_memory_trend(
        self, snapshots: list[MemorySnapshot], window_minutes: int = 30
    ) -> dict[str, Any]:
        """メモリ使用量のトレンドを分析

        Args:
            snapshots: 分析対象のスナップショットリスト
            window_minutes: 分析ウィンドウ（分）

        Returns:
            dict: トレンド分析結果
        """
        if not snapshots:
            return {"error": "No snapshots available"}

        current_time = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = current_time - window_seconds

        # ウィンドウ内のスナップショットを抽出
        window_snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]

        if len(window_snapshots) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # トレンド計算
        memory_values = [s.memory_mb for s in window_snapshots]
        gc_object_values = [s.gc_objects for s in window_snapshots]

        start_memory = memory_values[0]
        end_memory = memory_values[-1]
        memory_change = end_memory - start_memory
        memory_change_percent = (
            (memory_change / start_memory * 100) if start_memory > 0 else 0
        )

        start_gc = gc_object_values[0]
        end_gc = gc_object_values[-1]
        gc_change = end_gc - start_gc

        # 統計計算
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        min_memory = min(memory_values)
        memory_volatility = (
            (max_memory - min_memory) / avg_memory * 100 if avg_memory > 0 else 0
        )

        # 傾きを計算してトレンドを判定
        memory_slope = self._calculate_slope(
            [s.timestamp for s in window_snapshots], [float(v) for v in memory_values]
        )
        gc_slope = self._calculate_slope(
            [s.timestamp for s in window_snapshots],
            [float(v) for v in gc_object_values],
        )

        # トレンド判定
        trend = "stable"
        if abs(memory_change_percent) > 10:
            trend = "increasing" if memory_change > 0 else "decreasing"
        elif memory_volatility > 20:
            trend = "volatile"

        result = {
            "analysis_window_minutes": window_minutes,
            "data_points": len(window_snapshots),
            "memory_trend": {
                "start_mb": start_memory,
                "end_mb": end_memory,
                "change_mb": memory_change,
                "change_percent": memory_change_percent,
                "average_mb": avg_memory,
                "max_mb": max_memory,
                "min_mb": min_memory,
                "volatility_percent": memory_volatility,
                "slope": memory_slope,
                "trend": trend,
            },
            "gc_objects_trend": {
                "start_count": start_gc,
                "end_count": end_gc,
                "change_count": gc_change,
                "slope": gc_slope,
            },
        }

        # 分析結果に基づく推奨事項
        recommendations = []
        if trend == "increasing" and memory_change_percent > 20:
            recommendations.append("メモリリークの可能性があります。詳細調査を推奨")
        elif memory_volatility > 30:
            recommendations.append(
                "メモリ使用量が不安定です。ガベージコレクション設定の見直しを推奨"
            )
        elif gc_change > 1000:
            recommendations.append(
                "オブジェクト数が急増しています。メモリ効率的なコードの見直しを推奨"
            )

        if recommendations:
            result["recommendations"] = recommendations

        return result

    def _calculate_slope(self, x_values: list[float], y_values: list[float]) -> float:
        """最小二乗法で傾きを計算

        Args:
            x_values: X軸の値（時間）
            y_values: Y軸の値（メモリ使用量など）

        Returns:
            float: 傾き
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)

        denominator = n * sum_x_squared - sum_x * sum_x
        if abs(denominator) < 1e-10:  # ゼロ除算回避
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def detect_memory_patterns(self, snapshots: list[MemorySnapshot]) -> dict[str, Any]:
        """メモリ使用パターンを検出

        Args:
            snapshots: 分析対象のスナップショットリスト

        Returns:
            dict: パターン検出結果
        """
        if len(snapshots) < 10:
            return {"error": "Insufficient data for pattern detection"}

        memory_values = [s.memory_mb for s in snapshots]
        timestamps = [s.timestamp for s in snapshots]

        # 周期性の検出（簡易版）
        patterns: dict[str, Any] = {
            "periodic": False,
            "trend": "stable",
            "anomalies": [],
        }

        # 異常値検出
        avg_memory = sum(memory_values) / len(memory_values)
        std_dev = (
            sum((x - avg_memory) ** 2 for x in memory_values) / len(memory_values)
        ) ** 0.5

        threshold = 2 * std_dev
        for i, (timestamp, memory) in enumerate(zip(timestamps, memory_values)):
            if abs(memory - avg_memory) > threshold:
                patterns["anomalies"].append(
                    {
                        "index": i,
                        "timestamp": timestamp,
                        "memory_mb": memory,
                        "deviation": abs(memory - avg_memory),
                    }
                )

        # 全体的なトレンド
        overall_slope = self._calculate_slope(timestamps, memory_values)
        if abs(overall_slope) > 0.1:  # 閾値は調整可能
            patterns["trend"] = "increasing" if overall_slope > 0 else "decreasing"

        return patterns
