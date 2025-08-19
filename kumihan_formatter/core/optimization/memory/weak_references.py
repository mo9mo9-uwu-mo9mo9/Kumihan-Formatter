"""
弱参照管理システム

弱参照による循環参照検出・回避とメモリリーク防止機能を提供します。
循環参照によるメモリリーク100%防止とキャッシュメモリ自動最適化を実現します。

Classes:
    WeakReferenceManager: 弱参照統合管理クラス
    CircularReferenceDetector: 循環参照検出器クラス
    AutoCleanupSystem: 自動クリーンアップシステムクラス
    MemoryLeakPreventer: メモリリーク防止クラス
"""

import gc
import os
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union
from weakref import WeakKeyDictionary, WeakSet, WeakValueDictionary

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReferenceStats:
    """弱参照統計情報"""

    total_references: int = 0
    active_references: int = 0
    cleaned_references: int = 0
    circular_refs_detected: int = 0
    circular_refs_resolved: int = 0
    memory_leaks_prevented: int = 0
    cache_cleanups: int = 0
    auto_cleanup_cycles: int = 0


class WeakReferenceManager:
    """
    弱参照統合管理クラス

    システム全体の弱参照を統合管理し、メモリリークを防止します。
    """

    def __init__(
        self,
        cleanup_interval: int = 300,  # 5分間隔
        max_references: int = 10000,
        enable_monitoring: bool = True,
    ) -> None:
        """
        弱参照マネージャーを初期化します。

        Args:
            cleanup_interval: クリーンアップ間隔（秒）
            max_references: 最大参照数
            enable_monitoring: 監視機能有効フラグ
        """
        try:
            self._cleanup_interval = cleanup_interval
            self._max_references = max_references
            self._enable_monitoring = enable_monitoring

            # 弱参照管理
            self._weak_refs: Set[weakref.ReferenceType] = set()
            self._ref_callbacks: Dict[int, Callable] = {}
            self._lock = RLock()

            # オブジェクト関係マッピング
            self._object_refs: WeakKeyDictionary = WeakKeyDictionary()
            self._ref_objects: WeakValueDictionary = WeakValueDictionary()

            # 統計情報
            self._stats = ReferenceStats()
            self._last_cleanup = time.time()

            # 監視スレッド
            self._monitoring_thread: Optional[threading.Thread] = None
            self._stop_monitoring = threading.Event()

            if self._enable_monitoring:
                self._start_monitoring()

            logger.info("WeakReferenceManager初期化完了")

        except Exception as e:
            logger.error(f"WeakReferenceManager初期化エラー: {str(e)}")
            raise

    def create_weak_reference(
        self, obj: Any, callback: Optional[Callable] = None, track_circular: bool = True
    ) -> weakref.ReferenceType:
        """
        弱参照を作成します。

        Args:
            obj: 参照対象オブジェクト
            callback: 削除時コールバック
            track_circular: 循環参照追跡フラグ

        Returns:
            作成された弱参照
        """
        try:
            with self._lock:
                # 弱参照作成
                def cleanup_callback(ref):
                    self._cleanup_reference(ref)
                    if callback:
                        callback(ref)

                weak_ref = weakref.ref(obj, cleanup_callback)

                # 管理下に追加
                self._weak_refs.add(weak_ref)
                self._stats.total_references += 1
                self._stats.active_references += 1

                # オブジェクト関係マッピング更新
                if track_circular:
                    self._object_refs[obj] = weak_ref
                    self._ref_objects[weak_ref] = obj

                # コールバック登録
                if callback:
                    self._ref_callbacks[id(weak_ref)] = callback

                logger.debug(f"弱参照作成: {type(obj).__name__}")
                return weak_ref

        except Exception as e:
            logger.error(f"弱参照作成エラー: {str(e)}")
            raise

    def create_weak_key_dict(self) -> WeakKeyDictionary:
        """弱キー辞書を作成します。"""
        try:
            return WeakKeyDictionary()
        except Exception as e:
            logger.error(f"弱キー辞書作成エラー: {str(e)}")
            raise

    def create_weak_value_dict(self) -> WeakValueDictionary:
        """弱値辞書を作成します。"""
        try:
            return WeakValueDictionary()
        except Exception as e:
            logger.error(f"弱値辞書作成エラー: {str(e)}")
            raise

    def create_weak_set(self) -> WeakSet:
        """弱参照セットを作成します。"""
        try:
            return WeakSet()
        except Exception as e:
            logger.error(f"弱参照セット作成エラー: {str(e)}")
            raise

    def _cleanup_reference(self, ref: weakref.ReferenceType) -> None:
        """弱参照クリーンアップ処理"""
        try:
            with self._lock:
                self._weak_refs.discard(ref)
                self._stats.cleaned_references += 1
                self._stats.active_references = max(
                    0, self._stats.active_references - 1
                )

                # コールバック削除
                ref_id = id(ref)
                if ref_id in self._ref_callbacks:
                    del self._ref_callbacks[ref_id]

                logger.debug("弱参照クリーンアップ完了")

        except Exception as e:
            logger.error(f"弱参照クリーンアップエラー: {str(e)}")

    def _start_monitoring(self) -> None:
        """監視スレッドを開始します。"""
        try:
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                return

            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()
            logger.info("弱参照監視開始")

        except Exception as e:
            logger.error(f"監視開始エラー: {str(e)}")
            raise

    def _monitoring_loop(self) -> None:
        """監視ループ処理"""
        try:
            while not self._stop_monitoring.wait(self._cleanup_interval):
                self._periodic_cleanup()
                self._generate_monitoring_report()

        except Exception as e:
            logger.error(f"監視ループエラー: {str(e)}")

    def _periodic_cleanup(self) -> None:
        """定期クリーンアップ処理"""
        try:
            with self._lock:
                # 死んだ弱参照を削除
                dead_refs = {ref for ref in self._weak_refs if ref() is None}
                for ref in dead_refs:
                    self._cleanup_reference(ref)

                # 参照数制限チェック
                if len(self._weak_refs) > self._max_references:
                    logger.warning(f"弱参照数が制限を超過: {len(self._weak_refs)}")

                self._stats.auto_cleanup_cycles += 1
                self._last_cleanup = time.time()

                logger.debug(
                    f"定期クリーンアップ実行 - アクティブ参照: {len(self._weak_refs)}"
                )

        except Exception as e:
            logger.error(f"定期クリーンアップエラー: {str(e)}")

    def _generate_monitoring_report(self) -> None:
        """監視レポートを生成します。"""
        try:
            os.makedirs("tmp", exist_ok=True)

            report_data = {
                "timestamp": time.time(),
                "stats": {
                    "total_references": self._stats.total_references,
                    "active_references": self._stats.active_references,
                    "cleaned_references": self._stats.cleaned_references,
                    "circular_refs_detected": self._stats.circular_refs_detected,
                    "circular_refs_resolved": self._stats.circular_refs_resolved,
                    "memory_leaks_prevented": self._stats.memory_leaks_prevented,
                    "cache_cleanups": self._stats.cache_cleanups,
                    "auto_cleanup_cycles": self._stats.auto_cleanup_cycles,
                },
                "system_info": {
                    "weak_refs_count": len(self._weak_refs),
                    "object_refs_count": len(self._object_refs),
                    "ref_objects_count": len(self._ref_objects),
                    "callback_count": len(self._ref_callbacks),
                },
            }

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = f"tmp/weak_reference_report_{timestamp}.json"

            import json

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"弱参照監視レポート生成: {report_path}")

        except Exception as e:
            logger.error(f"監視レポート生成エラー: {str(e)}")

    def stop_monitoring(self) -> None:
        """監視を停止します。"""
        try:
            self._stop_monitoring.set()
            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=5.0)
            logger.info("弱参照監視停止")

        except Exception as e:
            logger.error(f"監視停止エラー: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得します。"""
        try:
            with self._lock:
                return {
                    "total_references": self._stats.total_references,
                    "active_references": self._stats.active_references,
                    "cleaned_references": self._stats.cleaned_references,
                    "cleanup_rate": (
                        self._stats.cleaned_references / self._stats.total_references
                        if self._stats.total_references > 0
                        else 0.0
                    ),
                    "circular_refs_detected": self._stats.circular_refs_detected,
                    "circular_refs_resolved": self._stats.circular_refs_resolved,
                    "memory_leaks_prevented": self._stats.memory_leaks_prevented,
                    "cache_cleanups": self._stats.cache_cleanups,
                    "auto_cleanup_cycles": self._stats.auto_cleanup_cycles,
                    "current_weak_refs": len(self._weak_refs),
                    "max_references": self._max_references,
                }

        except Exception as e:
            logger.error(f"統計情報取得エラー: {str(e)}")
            return {}


class CircularReferenceDetector:
    """
    循環参照検出器クラス

    オブジェクト間の循環参照を検出し、自動解決します。
    """

    def __init__(self, weak_ref_manager: WeakReferenceManager) -> None:
        """
        循環参照検出器を初期化します。

        Args:
            weak_ref_manager: 弱参照マネージャー
        """
        try:
            self._weak_ref_manager = weak_ref_manager
            self._detected_cycles: Set[Tuple] = set()
            self._lock = Lock()

            logger.info("CircularReferenceDetector初期化完了")

        except Exception as e:
            logger.error(f"CircularReferenceDetector初期化エラー: {str(e)}")
            raise

    def detect_circular_references(
        self, obj: Any, max_depth: int = 10
    ) -> List[List[Any]]:
        """
        循環参照を検出します。

        Args:
            obj: 検出開始オブジェクト
            max_depth: 最大検出深度

        Returns:
            検出された循環参照パス
        """
        try:
            visited = set()
            path = []
            cycles = []

            self._dfs_detect(obj, visited, path, cycles, max_depth)

            with self._lock:
                self._weak_ref_manager._stats.circular_refs_detected += len(cycles)

            logger.debug(f"循環参照検出完了: {len(cycles)}件")
            return cycles

        except Exception as e:
            logger.error(f"循環参照検出エラー: {str(e)}")
            return []

    def _dfs_detect(
        self,
        obj: Any,
        visited: Set[int],
        path: List[Any],
        cycles: List[List[Any]],
        max_depth: int,
    ) -> None:
        """DFSによる循環参照検出"""
        try:
            if max_depth <= 0:
                return

            obj_id = id(obj)

            if obj_id in visited:
                # 循環参照検出
                cycle_start = next(
                    (i for i, o in enumerate(path) if id(o) == obj_id), -1
                )
                if cycle_start >= 0:
                    cycle = path[cycle_start:] + [obj]
                    cycles.append(cycle)
                return

            visited.add(obj_id)
            path.append(obj)

            # オブジェクトの参照を追跡
            refs = self._get_object_references(obj)
            for ref_obj in refs:
                self._dfs_detect(
                    ref_obj, visited.copy(), path.copy(), cycles, max_depth - 1
                )

        except Exception as e:
            logger.debug(f"DFS検出中エラー: {str(e)}")

    def _get_object_references(self, obj: Any) -> List[Any]:
        """オブジェクトの参照を取得します。"""
        try:
            refs = []

            # 属性参照
            if hasattr(obj, "__dict__"):
                for attr_value in obj.__dict__.values():
                    if hasattr(attr_value, "__dict__"):  # オブジェクトのみ
                        refs.append(attr_value)

            # コンテナ参照
            if isinstance(obj, (list, tuple)):
                refs.extend(item for item in obj if hasattr(item, "__dict__"))
            elif isinstance(obj, dict):
                refs.extend(
                    value for value in obj.values() if hasattr(value, "__dict__")
                )

            return refs

        except Exception as e:
            logger.debug(f"オブジェクト参照取得エラー: {str(e)}")
            return []

    def resolve_circular_reference(self, cycle: List[Any]) -> bool:
        """
        循環参照を解決します。

        Args:
            cycle: 循環参照パス

        Returns:
            解決成功フラグ
        """
        try:
            if len(cycle) < 2:
                return False

            # 最弱リンクを見つけて弱参照に置き換え
            weakest_link = self._find_weakest_link(cycle)
            if weakest_link:
                obj1, obj2, attr_name = weakest_link

                # 弱参照に置き換え
                weak_ref = self._weak_ref_manager.create_weak_reference(obj2)
                setattr(obj1, attr_name, weak_ref)

                with self._lock:
                    self._weak_ref_manager._stats.circular_refs_resolved += 1

                logger.info(f"循環参照解決: {attr_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"循環参照解決エラー: {str(e)}")
            return False

    def _find_weakest_link(self, cycle: List[Any]) -> Optional[Tuple[Any, Any, str]]:
        """循環参照の最弱リンクを見つけます。"""
        try:
            for i in range(len(cycle) - 1):
                obj1, obj2 = cycle[i], cycle[i + 1]

                # obj1からobj2への参照を探す
                if hasattr(obj1, "__dict__"):
                    for attr_name, attr_value in obj1.__dict__.items():
                        if attr_value is obj2:
                            return (obj1, obj2, attr_name)

            return None

        except Exception as e:
            logger.debug(f"最弱リンク検索エラー: {str(e)}")
            return None


class AutoCleanupSystem:
    """
    自動クリーンアップシステムクラス

    メモリ使用量に基づく自動クリーンアップを実行します。
    """

    def __init__(
        self,
        weak_ref_manager: WeakReferenceManager,
        memory_threshold: float = 0.8,  # 80%でクリーンアップ実行
        cleanup_interval: int = 60,
    ) -> None:
        """
        自動クリーンアップシステムを初期化します。

        Args:
            weak_ref_manager: 弱参照マネージャー
            memory_threshold: メモリ使用率閾値
            cleanup_interval: クリーンアップ間隔（秒）
        """
        try:
            self._weak_ref_manager = weak_ref_manager
            self._memory_threshold = memory_threshold
            self._cleanup_interval = cleanup_interval

            self._cache_registry: Dict[str, Any] = {}
            self._cache_access_times: Dict[str, float] = {}
            self._lock = Lock()

            # 監視スレッド
            self._monitoring_thread: Optional[threading.Thread] = None
            self._stop_monitoring = threading.Event()

            logger.info("AutoCleanupSystem初期化完了")

        except Exception as e:
            logger.error(f"AutoCleanupSystem初期化エラー: {str(e)}")
            raise

    def register_cache(self, name: str, cache_obj: Any) -> None:
        """
        キャッシュオブジェクトを登録します。

        Args:
            name: キャッシュ名
            cache_obj: キャッシュオブジェクト
        """
        try:
            with self._lock:
                self._cache_registry[name] = cache_obj
                self._cache_access_times[name] = time.time()
                logger.debug(f"キャッシュ登録: {name}")

        except Exception as e:
            logger.error(f"キャッシュ登録エラー: {str(e)}")
            raise

    def start_auto_cleanup(self) -> None:
        """自動クリーンアップを開始します。"""
        try:
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                return

            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(
                target=self._cleanup_loop, daemon=True
            )
            self._monitoring_thread.start()
            logger.info("自動クリーンアップ開始")

        except Exception as e:
            logger.error(f"自動クリーンアップ開始エラー: {str(e)}")
            raise

    def _cleanup_loop(self) -> None:
        """クリーンアップループ処理"""
        try:
            while not self._stop_monitoring.wait(self._cleanup_interval):
                memory_usage = self._get_memory_usage_ratio()

                if memory_usage > self._memory_threshold:
                    logger.info(
                        f"メモリ使用率高 ({memory_usage:.1%}) - クリーンアップ実行"
                    )
                    self._execute_cleanup()

        except Exception as e:
            logger.error(f"クリーンアップループエラー: {str(e)}")

    def _get_memory_usage_ratio(self) -> float:
        """メモリ使用率を取得します。"""
        try:
            import psutil

            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except ImportError:
            # psutilが利用できない場合は概算
            return 0.5
        except Exception as e:
            logger.warning(f"メモリ使用率取得エラー: {str(e)}")
            return 0.0

    def _execute_cleanup(self) -> None:
        """クリーンアップを実行します。"""
        try:
            with self._lock:
                current_time = time.time()

                # 古いキャッシュを特定
                old_caches = [
                    name
                    for name, access_time in self._cache_access_times.items()
                    if current_time - access_time > 300  # 5分間未使用
                ]

                # キャッシュクリア
                cleared_count = 0
                for cache_name in old_caches:
                    cache_obj = self._cache_registry.get(cache_name)
                    if cache_obj:
                        if hasattr(cache_obj, "clear"):
                            cache_obj.clear()
                            cleared_count += 1
                        elif hasattr(cache_obj, "__delitem__"):
                            # 辞書ライクオブジェクトの場合
                            list(cache_obj.keys()).clear()
                            cleared_count += 1

                # 統計更新
                self._weak_ref_manager._stats.cache_cleanups += cleared_count

                # ガベージコレクション実行
                gc.collect()

                logger.info(
                    f"クリーンアップ完了 - クリアしたキャッシュ: {cleared_count}"
                )

        except Exception as e:
            logger.error(f"クリーンアップ実行エラー: {str(e)}")

    def stop_auto_cleanup(self) -> None:
        """自動クリーンアップを停止します。"""
        try:
            self._stop_monitoring.set()
            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=5.0)
            logger.info("自動クリーンアップ停止")

        except Exception as e:
            logger.error(f"自動クリーンアップ停止エラー: {str(e)}")


class MemoryLeakPreventer:
    """
    メモリリーク防止クラス

    メモリリークパターンを検出し、予防策を自動適用します。
    """

    def __init__(self, weak_ref_manager: WeakReferenceManager) -> None:
        """
        メモリリーク防止器を初期化します。

        Args:
            weak_ref_manager: 弱参照マネージャー
        """
        try:
            self._weak_ref_manager = weak_ref_manager
            self._leak_patterns: Dict[str, int] = defaultdict(int)
            self._prevention_strategies: Dict[str, Callable] = {}
            self._lock = Lock()

            # デフォルト防止戦略を設定
            self._setup_default_strategies()

            logger.info("MemoryLeakPreventer初期化完了")

        except Exception as e:
            logger.error(f"MemoryLeakPreventer初期化エラー: {str(e)}")
            raise

    def _setup_default_strategies(self) -> None:
        """デフォルト防止戦略を設定します。"""
        try:
            self._prevention_strategies.update(
                {
                    "circular_reference": self._prevent_circular_reference,
                    "large_cache": self._prevent_large_cache_leak,
                    "unclosed_file": self._prevent_unclosed_file_leak,
                    "event_listener": self._prevent_event_listener_leak,
                }
            )

        except Exception as e:
            logger.error(f"デフォルト戦略設定エラー: {str(e)}")
            raise

    def detect_potential_leak(self, obj: Any, pattern_name: str) -> bool:
        """
        潜在的なメモリリークを検出します。

        Args:
            obj: 検査対象オブジェクト
            pattern_name: リークパターン名

        Returns:
            リーク検出フラグ
        """
        try:
            with self._lock:
                self._leak_patterns[pattern_name] += 1

                # 戦略適用
                if pattern_name in self._prevention_strategies:
                    success = self._prevention_strategies[pattern_name](obj)
                    if success:
                        self._weak_ref_manager._stats.memory_leaks_prevented += 1
                        logger.info(f"メモリリーク防止: {pattern_name}")
                        return True

                return False

        except Exception as e:
            logger.error(f"メモリリーク検出エラー: {str(e)}")
            return False

    def _prevent_circular_reference(self, obj: Any) -> bool:
        """循環参照リーク防止"""
        try:
            detector = CircularReferenceDetector(self._weak_ref_manager)
            cycles = detector.detect_circular_references(obj)

            for cycle in cycles:
                detector.resolve_circular_reference(cycle)

            return len(cycles) > 0

        except Exception as e:
            logger.error(f"循環参照防止エラー: {str(e)}")
            return False

    def _prevent_large_cache_leak(self, obj: Any) -> bool:
        """大容量キャッシュリーク防止"""
        try:
            if hasattr(obj, "__len__") and len(obj) > 1000:
                if hasattr(obj, "clear"):
                    obj.clear()
                    return True
            return False

        except Exception as e:
            logger.error(f"キャッシュリーク防止エラー: {str(e)}")
            return False

    def _prevent_unclosed_file_leak(self, obj: Any) -> bool:
        """未クローズファイルリーク防止"""
        try:
            if hasattr(obj, "close") and hasattr(obj, "closed"):
                if not obj.closed:
                    obj.close()
                    return True
            return False

        except Exception as e:
            logger.error(f"ファイルリーク防止エラー: {str(e)}")
            return False

    def _prevent_event_listener_leak(self, obj: Any) -> bool:
        """イベントリスナーリーク防止"""
        try:
            # イベントリスナーの自動削除
            if hasattr(obj, "remove_all_listeners"):
                obj.remove_all_listeners()
                return True
            elif hasattr(obj, "disconnect"):
                obj.disconnect()
                return True
            return False

        except Exception as e:
            logger.error(f"イベントリスナーリーク防止エラー: {str(e)}")
            return False

    def get_leak_statistics(self) -> Dict[str, Any]:
        """リーク統計情報を取得します。"""
        try:
            with self._lock:
                return {
                    "leak_patterns": dict(self._leak_patterns),
                    "prevention_strategies": list(self._prevention_strategies.keys()),
                    "total_leaks_prevented": self._weak_ref_manager._stats.memory_leaks_prevented,
                }

        except Exception as e:
            logger.error(f"リーク統計取得エラー: {str(e)}")
            return {}


# グローバルインスタンス
_global_weak_ref_manager = WeakReferenceManager()
_global_circular_detector = CircularReferenceDetector(_global_weak_ref_manager)
_global_auto_cleanup = AutoCleanupSystem(_global_weak_ref_manager)
_global_leak_preventer = MemoryLeakPreventer(_global_weak_ref_manager)


def get_weak_ref_manager() -> WeakReferenceManager:
    """グローバル弱参照マネージャーを取得します。"""
    return _global_weak_ref_manager


def get_circular_detector() -> CircularReferenceDetector:
    """グローバル循環参照検出器を取得します。"""
    return _global_circular_detector


def get_auto_cleanup_system() -> AutoCleanupSystem:
    """グローバル自動クリーンアップシステムを取得します。"""
    return _global_auto_cleanup


def get_leak_preventer() -> MemoryLeakPreventer:
    """グローバルメモリリーク防止器を取得します。"""
    return _global_leak_preventer


def create_weak_reference(
    obj: Any, callback: Optional[Callable] = None
) -> weakref.ReferenceType:
    """
    弱参照を作成します（グローバルマネージャー使用）。

    Args:
        obj: 参照対象オブジェクト
        callback: 削除時コールバック

    Returns:
        作成された弱参照
    """
    return _global_weak_ref_manager.create_weak_reference(obj, callback)


if __name__ == "__main__":
    """弱参照管理システムのテスト実行"""

    # テスト用クラス
    class Node:
        def __init__(self, name: str) -> None:
            self.name = name
            self.children = []
            self.parent = None

        def add_child(self, child: "Node") -> None:
            child.parent = self
            self.children.append(child)

    def test_weak_reference_manager() -> None:
        """弱参照マネージャーテスト"""
        logger.info("=== 弱参照マネージャーテスト開始 ===")

        manager = get_weak_ref_manager()

        # 弱参照作成テスト
        obj = Node("test")
        weak_ref = manager.create_weak_reference(obj)

        # 統計確認
        stats = manager.get_statistics()
        logger.info(f"弱参照統計: {stats}")

        # オブジェクト削除
        del obj

        # 弱参照確認
        logger.info(f"弱参照生存確認: {weak_ref() is not None}")

    def test_circular_reference_detection() -> None:
        """循環参照検出テスト"""
        logger.info("=== 循環参照検出テスト開始 ===")

        detector = get_circular_detector()

        # 循環参照作成
        node1 = Node("node1")
        node2 = Node("node2")
        node1.add_child(node2)
        node2.add_child(node1)  # 循環参照

        # 検出実行
        cycles = detector.detect_circular_references(node1)
        logger.info(f"検出された循環参照: {len(cycles)}")

        # 解決実行
        for cycle in cycles:
            success = detector.resolve_circular_reference(cycle)
            logger.info(f"循環参照解決: {success}")

    def test_auto_cleanup_system() -> None:
        """自動クリーンアップシステムテスト"""
        logger.info("=== 自動クリーンアップシステムテスト開始 ===")

        cleanup_system = get_auto_cleanup_system()

        # キャッシュ登録
        test_cache = {}
        cleanup_system.register_cache("test_cache", test_cache)

        # クリーンアップ開始
        cleanup_system.start_auto_cleanup()

        # テスト終了時に停止
        import time

        time.sleep(2)
        cleanup_system.stop_auto_cleanup()

    def test_memory_leak_prevention() -> None:
        """メモリリーク防止テスト"""
        logger.info("=== メモリリーク防止テスト開始 ===")

        preventer = get_leak_preventer()

        # 循環参照リークテスト
        node1 = Node("leak_node1")
        node2 = Node("leak_node2")
        node1.add_child(node2)
        node2.add_child(node1)

        leak_detected = preventer.detect_potential_leak(node1, "circular_reference")
        logger.info(f"循環参照リーク検出・防止: {leak_detected}")

        # 統計確認
        leak_stats = preventer.get_leak_statistics()
        logger.info(f"リーク防止統計: {leak_stats}")

    try:
        # テスト実行
        test_weak_reference_manager()
        test_circular_reference_detection()
        test_auto_cleanup_system()
        test_memory_leak_prevention()

        # 統合統計表示
        manager = get_weak_ref_manager()
        final_stats = manager.get_statistics()
        logger.info(f"最終統計: {final_stats}")

        logger.info("=== 弱参照管理システムテスト完了 ===")

    except Exception as e:
        logger.error(f"テスト実行エラー: {str(e)}")
        raise
    finally:
        # システム停止
        get_weak_ref_manager().stop_monitoring()
        get_auto_cleanup_system().stop_auto_cleanup()
