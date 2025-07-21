"""メモリリーク検出システム - リーク検出とアラート

Single Responsibility Principle適用: リーク検出の責任分離
Issue #476 Phase4対応 - memory.py分割による技術的負債削減
"""

from collections import defaultdict
from typing import Any, Dict, List

from ...utilities.logger import get_logger
from ..core.metrics import MemoryLeak, MemorySnapshot


class LeakDetector:
    """メモリリーク検出システム

    責任:
    - メモリリークの検出
    - リーク重要度の判定
    - アラート管理
    """

    def __init__(
        self,
        leak_detection_threshold: int = 10,
        memory_alert_threshold: float = 0.8,
        leak_alert_threshold: int = 5,
    ):
        """リーク検出器を初期化

        Args:
            leak_detection_threshold: リーク検出の閾値
            memory_alert_threshold: メモリ使用量アラート閾値（80%）
            leak_alert_threshold: リークアラート閾値（5個）
        """
        self.leak_detection_threshold = leak_detection_threshold
        self.memory_alert_threshold = memory_alert_threshold
        self.leak_alert_threshold = leak_alert_threshold

        self.detected_leaks: List[MemoryLeak] = []
        self.logger = get_logger(__name__)

    def detect_leaks(
        self, current_snapshot: MemorySnapshot, previous_snapshot: MemorySnapshot
    ) -> List[MemoryLeak]:
        """メモリリークを検出

        Args:
            current_snapshot: 現在のスナップショット
            previous_snapshot: 前回のスナップショット

        Returns:
            検出されたリークのリスト
        """
        new_leaks = []

        # プロセスメモリの増加をチェック
        memory_increase = (
            current_snapshot.process_memory - previous_snapshot.process_memory
        )
        if memory_increase > self.leak_detection_threshold * 1024 * 1024:  # MB単位
            leak = MemoryLeak(
                object_type="process_memory",
                count_increase=1,
                size_estimate=memory_increase,
                first_detected=current_snapshot.timestamp,
                last_detected=current_snapshot.timestamp,
                severity=self._determine_leak_severity(memory_increase),
            )
            new_leaks.append(leak)
            self.detected_leaks.append(leak)

        # カスタムオブジェクトの増加をチェック
        for obj_type, current_count in current_snapshot.custom_objects.items():
            previous_count = previous_snapshot.custom_objects.get(obj_type, 0)
            count_increase = current_count - previous_count

            if count_increase > self.leak_detection_threshold:
                leak = MemoryLeak(
                    object_type=obj_type,
                    count_increase=count_increase,
                    size_estimate=count_increase * 1024,  # 推定サイズ
                    first_detected=current_snapshot.timestamp,
                    last_detected=current_snapshot.timestamp,
                    severity=self._determine_leak_severity(count_increase * 1024),
                )
                new_leaks.append(leak)
                self.detected_leaks.append(leak)

        return new_leaks

    def _determine_leak_severity(self, size_bytes: int) -> str:
        """リークの重要度を判定

        Args:
            size_bytes: リークサイズ（バイト）

        Returns:
            重要度レベル
        """
        size_mb = size_bytes / 1024 / 1024
        if size_mb >= 100:
            return "critical"
        elif size_mb >= 50:
            return "high"
        elif size_mb >= 10:
            return "medium"
        else:
            return "low"

    def check_alerts(self, latest_snapshot: MemorySnapshot) -> List[str]:
        """アラートをチェック

        Args:
            latest_snapshot: 最新のスナップショット

        Returns:
            発生したアラートメッセージのリスト
        """
        alerts = []

        # メモリ使用量アラート
        try:
            import psutil  # noqa: F401

            memory_usage_ratio = (
                latest_snapshot.total_memory - latest_snapshot.available_memory
            ) / latest_snapshot.total_memory
            if memory_usage_ratio > self.memory_alert_threshold:
                alert_msg = (
                    f"High memory usage detected: {memory_usage_ratio:.1%} "
                    f"(threshold: {self.memory_alert_threshold:.1%})"
                )
                alerts.append(alert_msg)
                self.logger.warning(alert_msg)
        except ImportError:
            pass  # psutil不可時はスキップ

        # リークアラート
        recent_leaks = [
            leak
            for leak in self.detected_leaks
            if leak.severity in ["high", "critical"]
        ]
        if len(recent_leaks) >= self.leak_alert_threshold:
            alert_msg = f"Multiple memory leaks detected: {len(recent_leaks)} leaks"
            alerts.append(alert_msg)
            self.logger.warning(alert_msg)

        return alerts

    def get_leak_summary(self) -> Dict[str, Any]:
        """リーク検出のサマリーを取得

        Returns:
            リークサマリー
        """
        if not self.detected_leaks:
            return {"total_leaks": 0, "severity_breakdown": {}}

        severity_breakdown: Dict[str, int] = defaultdict(int)
        for leak in self.detected_leaks:
            severity_breakdown[leak.severity] += 1

        return {
            "total_leaks": len(self.detected_leaks),
            "severity_breakdown": dict(severity_breakdown),
            "latest_leak_time": max(leak.last_detected for leak in self.detected_leaks),
        }

    def get_detailed_leaks(self) -> List[Dict[str, Any]]:
        """詳細なリーク情報を取得

        Returns:
            詳細リーク情報のリスト
        """
        return [
            {
                "object_type": leak.object_type,
                "count_increase": leak.count_increase,
                "size_estimate_mb": leak.size_estimate / 1024 / 1024,
                "age_seconds": leak.age_seconds,
                "estimated_leak_rate": leak.estimated_leak_rate,
                "severity": leak.severity,
            }
            for leak in self.detected_leaks
        ]

    def generate_recommendations(self) -> List[str]:
        """リークベースの改善提案を生成

        Returns:
            改善提案のリスト
        """
        recommendations = []

        if self.detected_leaks:
            high_severity_leaks = [
                leak
                for leak in self.detected_leaks
                if leak.severity in ["high", "critical"]
            ]
            if high_severity_leaks:
                recommendations.append(
                    "Critical memory leaks detected. Consider reviewing object lifecycle management."
                )

            # オブジェクトタイプ別の分析
            object_types = set(leak.object_type for leak in self.detected_leaks)
            if len(object_types) > 3:
                recommendations.append(
                    "Multiple object types showing memory leaks. Consider comprehensive memory audit."
                )

        return recommendations

    def clear_leaks(self) -> None:
        """検出されたリークをクリア"""
        self.detected_leaks.clear()

    def get_leak_count(self) -> int:
        """検出されたリーク数を取得

        Returns:
            リーク数
        """
        return len(self.detected_leaks)
