"""
メモリ監視データ管理機能 - オブジェクト追跡とデータ管理
メモリ監視のデータ管理とカスタムオブジェクト追跡
Issue #402対応 - パフォーマンス最適化
"""

import threading
import time
import weakref
from collections import defaultdict
from typing import Any, Union

from ..utilities.logger import get_logger


class MemoryDataManager:
    """メモリ監視システムのデータ管理機能
    基本機能:
    - カスタムオブジェクト追跡
    - weak referenceのクリーンアップ
    - データのクリア処理
    """

    def __init__(self, enable_object_tracking: bool = True):
        """データ管理機能を初期化

        Args:
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        self.logger = get_logger(__name__)
        self.enable_object_tracking = enable_object_tracking

        # データストレージ
        self.custom_objects: dict[str, set[weakref.ReferenceType[Any]]] = defaultdict(
            set
        )
        self._lock = threading.RLock()

        # 統計
        self.stats: dict[str, Union[int, float, None]] = {
            "total_snapshots": 0,
            "monitoring_start_time": None,
            "total_monitoring_time": 0.0,
        }

    def register_object(self, obj: Any, obj_type: str) -> None:
        """カスタムオブジェクトを追跡に登録

        Args:
            obj: 追跡するオブジェクト
            obj_type: オブジェクトのタイプ名
        """
        if not self.enable_object_tracking:
            return

        try:
            weak_ref = weakref.ref(obj)
            with self._lock:
                self.custom_objects[obj_type].add(weak_ref)

            self.logger.debug(f"オブジェクト追跡に登録: {obj_type}")

        except TypeError:
            # weak reference を作成できないオブジェクト
            self.logger.debug(f"weak reference 作成不可のオブジェクト: {obj_type}")

    def cleanup_weak_refs(self) -> None:
        """死んでいるweak referenceをクリーンアップ"""
        if not self.enable_object_tracking:
            return

        cleaned_count = 0
        with self._lock:
            for obj_type in list(self.custom_objects.keys()):
                alive_refs = set()
                for weak_ref in self.custom_objects[obj_type]:
                    if weak_ref() is not None:
                        alive_refs.add(weak_ref)
                    else:
                        cleaned_count += 1

                if alive_refs:
                    self.custom_objects[obj_type] = alive_refs
                else:
                    del self.custom_objects[obj_type]

        if cleaned_count > 0:
            self.logger.debug(f"weak reference クリーンアップ: {cleaned_count}個")

    def clear_data(self) -> None:
        """蓄積されたデータをクリア"""
        with self._lock:
            object_types = len(self.custom_objects)
            self.custom_objects.clear()

            # 統計をリセット（一部は保持）
            current_monitoring_time = self.stats.get("total_monitoring_time", 0.0)
            if (
                isinstance(current_monitoring_time, (int, float))
                and self.stats["monitoring_start_time"] is not None
            ):
                current_monitoring_time += (
                    time.time() - self.stats["monitoring_start_time"]
                )

            self.stats = {
                "total_snapshots": 0,
                "monitoring_start_time": None,
                "total_monitoring_time": current_monitoring_time,
            }

        self.logger.info(
            f"メモリ監視データをクリア cleared_object_types={object_types}"
        )

    def get_custom_objects_count(self) -> dict[str, int]:
        """カスタムオブジェクトの数を取得

        Returns:
            dict[str, int]: オブジェクトタイプ別の数
        """
        if not self.enable_object_tracking:
            return {}

        result = {}
        with self._lock:
            for obj_type, weak_refs in self.custom_objects.items():
                # 生きているオブジェクトのみカウント
                alive_count = sum(1 for ref in weak_refs if ref() is not None)
                result[obj_type] = alive_count

        return result

    def update_stats(self, key: str, value: Union[int, float, None]) -> None:
        """統計を更新

        Args:
            key: 統計のキー
            value: 値
        """
        with self._lock:
            self.stats[key] = value

    def get_stats(self) -> dict[str, Union[int, float, None]]:
        """統計を取得

        Returns:
            dict: 統計情報
        """
        with self._lock:
            return self.stats.copy()
