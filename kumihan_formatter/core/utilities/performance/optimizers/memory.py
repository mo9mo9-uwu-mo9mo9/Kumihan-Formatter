"""
メモリ最適化システム
Issue #813対応 - performance_metrics.py分割版（メモリ最適化）

特徴:
- 動的メモリ使用量監視・制御
- ガベージコレクション最適化
- メモリプール管理
- 大容量データの効率的処理
"""

import gc
import weakref
from collections import deque
from typing import Any, Dict, Iterator, List, Optional, Union

import psutil

from ...logger import get_logger


class MemoryOptimizer:
    """
    メモリ最適化システム

    特徴:
    - 動的メモリ使用量監視・制御
    - ガベージコレクション最適化
    - メモリプール管理
    - 大容量データの効率的処理
    """

    def __init__(
        self, memory_limit_mb: Optional[int] = None, gc_threshold: float = 0.8
    ):
        self.logger = get_logger(__name__)
        self.process = psutil.Process()

        # メモリ制限設定（デフォルト：利用可能メモリの80%）
        if memory_limit_mb is None:
            available_memory = psutil.virtual_memory().available / 1024 / 1024
            self.memory_limit_mb = available_memory * 0.8
        else:
            self.memory_limit_mb = memory_limit_mb

        self.gc_threshold = gc_threshold

        # メモリ監視
        self._memory_history = deque(maxlen=100)
        self._object_refs = weakref.WeakSet()

        # ガベージコレクション統計
        self._gc_stats = {"forced_collections": 0, "objects_collected": 0}

        # メモリプール（文字列キャッシュ用）
        self._string_cache = {}
        self._string_cache_limit = 10000

        self.logger.info(
            f"MemoryOptimizer initialized: limit={self.memory_limit_mb:.1f}MB, "
            f"gc_threshold={gc_threshold}"
        )

    def get_current_memory_usage(self) -> Dict[str, float]:
        """現在のメモリ使用量を取得"""
        try:
            memory_info = self.process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": self.process.memory_percent(),
                "available_system_mb": psutil.virtual_memory().available / 1024 / 1024,
            }
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0, "available_system_mb": 0}

    def check_memory_pressure(self) -> bool:
        """メモリ圧迫状態をチェック"""
        current_usage = self.get_current_memory_usage()
        current_mb = current_usage["rss_mb"]

        # 履歴に追加
        self._memory_history.append(current_mb)

        # メモリ制限チェック
        is_over_limit = current_mb > self.memory_limit_mb * self.gc_threshold

        if is_over_limit:
            self.logger.warning(
                f"Memory pressure detected: {current_mb:.1f}MB "
                f"(limit: {self.memory_limit_mb:.1f}MB)"
            )

        return is_over_limit

    def force_garbage_collection(self) -> int:
        """強制ガベージコレクション実行"""
        before_count = len(gc.get_objects())

        # 全世代のガベージコレクション実行
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)

        after_count = len(gc.get_objects())
        objects_freed = before_count - after_count

        self._gc_stats["forced_collections"] += 1
        self._gc_stats["objects_collected"] += objects_freed

        self.logger.info(
            f"Forced GC: {objects_freed} objects freed, "
            f"{collected} collections performed"
        )

        return objects_freed

    def optimize_memory_if_needed(self) -> bool:
        """必要に応じてメモリ最適化を実行"""
        if self.check_memory_pressure():
            # 文字列キャッシュクリア
            self.clear_string_cache()

            # 強制ガベージコレクション
            freed_objects = self.force_garbage_collection()

            # 再度メモリチェック
            new_usage = self.get_current_memory_usage()

            self.logger.info(
                f"Memory optimization completed: "
                f"freed {freed_objects} objects, "
                f"current usage: {new_usage['rss_mb']:.1f}MB"
            )

            return True

        return False

    def memory_efficient_string_processing(self, text: str) -> str:
        """メモリ効率的な文字列処理"""
        # 文字列キャッシュをチェック
        text_hash = hash(text)
        if text_hash in self._string_cache:
            return self._string_cache[text_hash]

        # 処理実行（実際の処理は用途に応じて実装）
        processed_text = text.strip()

        # キャッシュサイズ制限チェック
        if len(self._string_cache) < self._string_cache_limit:
            self._string_cache[text_hash] = processed_text

        return processed_text

    def clear_string_cache(self) -> int:
        """文字列キャッシュをクリア"""
        cleared_count = len(self._string_cache)
        self._string_cache.clear()

        self.logger.debug(f"Cleared {cleared_count} cached strings")
        return cleared_count

    def memory_safe_iterator(
        self, data: Union[List, Iterator], chunk_size: int = 1000
    ) -> Iterator:
        """メモリ安全なイテレータ（チャンク処理）"""
        if isinstance(data, list):
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                yield chunk

                # チャンク処理後にメモリ最適化
                if i % (chunk_size * 10) == 0:  # 10チャンクごと
                    self.optimize_memory_if_needed()
        else:
            chunk = []
            for item in data:
                chunk.append(item)
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
                    self.optimize_memory_if_needed()

            if chunk:
                yield chunk

    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ統計情報を取得"""
        current_usage = self.get_current_memory_usage()

        # メモリ履歴から傾向を分析
        if len(self._memory_history) >= 2:
            memory_trend = self._memory_history[-1] - self._memory_history[-2]
        else:
            memory_trend = 0

        return {
            "current_usage_mb": current_usage["rss_mb"],
            "memory_limit_mb": self.memory_limit_mb,
            "usage_percent": (current_usage["rss_mb"] / self.memory_limit_mb * 100),
            "memory_trend_mb": memory_trend,
            "gc_stats": self._gc_stats.copy(),
            "string_cache_size": len(self._string_cache),
            "tracked_objects": len(self._object_refs),
            "gc_enabled": gc.isenabled(),
            "gc_thresholds": gc.get_threshold(),
        }

    def register_object_for_tracking(self, obj: Any):
        """オブジェクトを追跡対象に登録"""
        self._object_refs.add(obj)

    def cleanup_resources(self):
        """リソースクリーンアップ"""
        self.clear_string_cache()
        self._object_refs.clear()
        self._memory_history.clear()
        self.force_garbage_collection()

        self.logger.info("Memory optimizer resources cleaned up")
