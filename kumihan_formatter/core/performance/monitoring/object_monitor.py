"""オブジェクトモニタリングシステム - カスタムオブジェクト追跡

Single Responsibility Principle適用: オブジェクト追跡の責任分離
Issue #476 Phase4対応 - memory.py分割による技術的負債削減
"""

import weakref
from collections import defaultdict
from typing import Any, Dict, List, Set

from ...utilities.logger import get_logger


class ObjectMonitor:
    """カスタムオブジェクト追跡システム

    責任:
    - オブジェクトのライフサイクル追跡
    - オブジェクト種別の統計管理
    - 弱参照による安全な追跡
    """

    def __init__(self, enable_tracking: bool = True):
        """オブジェクトモニターを初期化

        Args:
            enable_tracking: オブジェクト追跡を有効にするか
        """
        self.enable_tracking = enable_tracking
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.tracked_objects: Set[weakref.ref] = set()  # type: ignore
        self.logger = get_logger(__name__)

    def track_object(self, obj: Any, object_type: str) -> None:
        """オブジェクトを追跡対象に追加

        Args:
            obj: 追跡するオブジェクト
            object_type: オブジェクトの種類
        """
        if not self.enable_tracking:
            return

        def cleanup_callback(ref: weakref.ref) -> None:  # type: ignore
            """オブジェクトがガベージコレクションされた際のクリーンアップ"""
            self.tracked_objects.discard(ref)
            if self.object_counts[object_type] > 0:
                self.object_counts[object_type] -= 1

        try:
            ref = weakref.ref(obj, cleanup_callback)
            self.tracked_objects.add(ref)
            self.object_counts[object_type] += 1
        except TypeError:
            # 弱参照をサポートしないオブジェクトの場合
            self.logger.debug(f"Cannot create weak reference for {object_type}")
            self.object_counts[object_type] += 1

    def get_object_counts(self) -> Dict[str, int]:
        """現在のオブジェクト数を取得

        Returns:
            オブジェクト種別ごとの数
        """
        if not self.enable_tracking:
            return {}
        return dict(self.object_counts)

    def get_total_tracked_objects(self) -> int:
        """追跡中のオブジェクト総数を取得

        Returns:
            追跡中のオブジェクト総数
        """
        return sum(self.object_counts.values())

    def get_tracking_statistics(self) -> Dict[str, Any]:
        """追跡統計を取得

        Returns:
            追跡統計情報
        """
        if not self.enable_tracking:
            return {"enabled": False}

        object_counts = self.get_object_counts()
        return {
            "enabled": True,
            "total_objects": sum(object_counts.values()),
            "object_types": len(object_counts),
            "counts_by_type": object_counts,
            "weak_references": len(self.tracked_objects),
        }

    def cleanup_dead_references(self) -> int:
        """無効な弱参照をクリーンアップ

        Returns:
            削除された参照の数
        """
        if not self.enable_tracking:
            return 0

        dead_refs = []
        for ref in self.tracked_objects:
            if ref() is None:  # オブジェクトが削除済み
                dead_refs.append(ref)

        for ref in dead_refs:
            self.tracked_objects.discard(ref)

        return len(dead_refs)

    def generate_recommendations(self) -> List[str]:
        """オブジェクト追跡ベースの改善提案を生成

        Returns:
            改善提案のリスト
        """
        recommendations: list[str] = []

        if not self.enable_tracking:
            return recommendations

        object_counts = self.get_object_counts()
        if not object_counts:
            return recommendations

        max_objects = max(object_counts.values())
        if max_objects > 10000:
            recommendations.append(
                "Large number of tracked objects. Consider object pooling or caching strategies."
            )

        # 特定のオブジェクトタイプが多い場合の提案
        for obj_type, count in object_counts.items():
            if count > 5000:
                recommendations.append(
                    f"High count of {obj_type} objects ({count}). "
                    f"Consider reviewing {obj_type} lifecycle management."
                )

        return recommendations

    def clear_tracking(self) -> None:
        """すべての追跡情報をクリア"""
        self.object_counts.clear()
        self.tracked_objects.clear()

    def disable_tracking(self) -> None:
        """オブジェクト追跡を無効化"""
        self.enable_tracking = False
        self.clear_tracking()

    def enable_tracking_mode(self) -> None:
        """オブジェクト追跡を有効化"""
        self.enable_tracking = True

    def is_tracking_enabled(self) -> bool:
        """オブジェクト追跡が有効かどうかを確認

        Returns:
            追跡が有効な場合True
        """
        return self.enable_tracking
