#!/usr/bin/env python3
"""
Resource Manager - Critical Memory Leak Fix
リソース管理システム

目的: 長時間実行時のメモリリーク防止
- メモリ使用量監視
- 自動リソース解放
- 循環参照解消
- ガベージコレクション最適化
"""

import gc
import psutil
import threading
import time
import weakref
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from contextlib import contextmanager
import logging

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class MemorySnapshot:
    """メモリスナップショット"""
    timestamp: datetime
    process_memory: float  # MB
    python_objects: int
    gc_collections: Dict[int, int]
    active_threads: int
    open_files: int

@dataclass
class ResourceLeak:
    """リソースリーク情報"""
    resource_type: str
    leak_count: int
    leak_rate: float  # per minute
    first_detected: datetime
    severity: str  # "low", "medium", "high", "critical"

class CircularReferenceTracker:
    """循環参照追跡クラス"""
    
    def __init__(self):
        self._tracked_objects = weakref.WeakSet()
        self._reference_graph = {}
        self._lock = threading.RLock()
    
    def track_object(self, obj: Any, name: str = None):
        """オブジェクト追跡開始"""
        with self._lock:
            self._tracked_objects.add(obj)
            if name:
                self._reference_graph[id(obj)] = {
                    'name': name,
                    'type': type(obj).__name__,
                    'created': datetime.now(),
                    'refs': []
                }
    
    def find_circular_references(self) -> List[Dict]:
        """循環参照検出"""
        with self._lock:
            circular_refs = []
            
            # GCによる循環参照検出
            gc.collect()  # 強制ガベージコレクション
            
            for generation in range(3):
                objects = gc.get_objects(generation)
                for obj in objects:
                    if gc.is_tracked(obj):
                        refs = gc.get_referents(obj)
                        for ref in refs:
                            if ref is obj:  # 自己参照
                                circular_refs.append({
                                    'type': 'self_reference',
                                    'object_type': type(obj).__name__,
                                    'object_id': id(obj),
                                    'generation': generation
                                })
            
            return circular_refs

class MemoryManager:
    """メモリ管理クラス"""
    
    def __init__(self, max_memory_mb: int = 512, check_interval: int = 30):
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self.process = psutil.Process()
        
        # メモリ履歴（最大1000件）
        self.memory_history = deque(maxlen=1000)
        
        # リソース追跡
        self.tracked_resources = {}
        self.resource_callbacks = {}
        
        # 循環参照追跡
        self.circular_tracker = CircularReferenceTracker()
        
        # 監視状態
        self.monitoring = False
        self.monitor_thread = None
        self._lock = threading.RLock()
        
        # アラート設定
        self.memory_thresholds = {
            'warning': max_memory_mb * 0.7,
            'critical': max_memory_mb * 0.9
        }
        
        # ガベージコレクション設定最適化
        self._optimize_gc_settings()
    
    def start_monitoring(self):
        """メモリ監視開始"""
        if self.monitoring:
            return
            
        logger.info("🔍 メモリ監視を開始...")
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """メモリ監視停止"""
        logger.info("🛑 メモリ監視を停止...")
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """メモリ監視ループ"""
        while self.monitoring:
            try:
                snapshot = self._create_memory_snapshot()
                self.memory_history.append(snapshot)
                
                # メモリ使用量チェック
                self._check_memory_usage(snapshot)
                
                # リソースリーク検出
                leaks = self._detect_resource_leaks()
                if leaks:
                    self._handle_resource_leaks(leaks)
                
                # 循環参照検出
                circular_refs = self.circular_tracker.find_circular_references()
                if circular_refs:
                    logger.warning(f"循環参照検出: {len(circular_refs)}件")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"メモリ監視エラー: {e}")
                time.sleep(self.check_interval)
    
    def _create_memory_snapshot(self) -> MemorySnapshot:
        """メモリスナップショット作成"""
        try:
            memory_info = self.process.memory_info()
            process_memory = memory_info.rss / 1024 / 1024  # MB
            
            # Pythonオブジェクト数
            python_objects = len(gc.get_objects())
            
            # GC統計
            gc_stats = {}
            for i in range(3):
                gc_stats[i] = gc.get_count()[i]
            
            # スレッド数
            active_threads = threading.active_count()
            
            # オープンファイル数
            try:
                open_files = len(self.process.open_files())
            except (psutil.AccessDenied, AttributeError):
                open_files = 0
            
            return MemorySnapshot(
                timestamp=datetime.now(),
                process_memory=process_memory,
                python_objects=python_objects,
                gc_collections=gc_stats,
                active_threads=active_threads,
                open_files=open_files
            )
            
        except Exception as e:
            logger.error(f"メモリスナップショット作成失敗: {e}")
            return MemorySnapshot(
                timestamp=datetime.now(),
                process_memory=0,
                python_objects=0,
                gc_collections={},
                active_threads=0,
                open_files=0
            )
    
    def _check_memory_usage(self, snapshot: MemorySnapshot):
        """メモリ使用量チェック"""
        memory_mb = snapshot.process_memory
        
        if memory_mb >= self.memory_thresholds['critical']:
            logger.critical(f"🚨 メモリ使用量が危険レベル: {memory_mb:.1f}MB")
            self._emergency_memory_cleanup()
            
        elif memory_mb >= self.memory_thresholds['warning']:
            logger.warning(f"⚠️ メモリ使用量が警告レベル: {memory_mb:.1f}MB")
            self._preventive_memory_cleanup()
        
        # メモリ使用量のトレンド監視
        if len(self.memory_history) >= 10:
            recent_snapshots = list(self.memory_history)[-10:]
            memory_trend = self._calculate_memory_trend(recent_snapshots)
            
            if memory_trend > 2.0:  # 2MB/分以上の増加
                logger.warning(f"メモリリーク疑い: 増加率 {memory_trend:.2f}MB/分")
    
    def _calculate_memory_trend(self, snapshots: List[MemorySnapshot]) -> float:
        """メモリ使用量トレンド計算"""
        if len(snapshots) < 2:
            return 0.0
        
        time_diff = (snapshots[-1].timestamp - snapshots[0].timestamp).total_seconds() / 60  # 分
        memory_diff = snapshots[-1].process_memory - snapshots[0].process_memory
        
        return memory_diff / max(time_diff, 1)
    
    def _detect_resource_leaks(self) -> List[ResourceLeak]:
        """リソースリーク検出"""
        leaks = []
        
        if len(self.memory_history) < 5:
            return leaks
        
        recent_snapshots = list(self.memory_history)[-5:]
        
        # Pythonオブジェクト数の増加チェック
        object_counts = [s.python_objects for s in recent_snapshots]
        if len(set(object_counts)) > 1:  # 変化がある場合
            object_increase = object_counts[-1] - object_counts[0]
            if object_increase > 1000:  # 1000オブジェクト以上増加
                time_diff = (recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp).total_seconds() / 60
                leak_rate = object_increase / max(time_diff, 1)
                
                severity = "critical" if leak_rate > 100 else "high" if leak_rate > 50 else "medium"
                
                leaks.append(ResourceLeak(
                    resource_type="python_objects",
                    leak_count=object_increase,
                    leak_rate=leak_rate,
                    first_detected=recent_snapshots[0].timestamp,
                    severity=severity
                ))
        
        # スレッド数の増加チェック
        thread_counts = [s.active_threads for s in recent_snapshots]
        thread_increase = thread_counts[-1] - thread_counts[0]
        if thread_increase > 5:  # 5スレッド以上増加
            leaks.append(ResourceLeak(
                resource_type="threads",
                leak_count=thread_increase,
                leak_rate=thread_increase,
                first_detected=recent_snapshots[0].timestamp,
                severity="high"
            ))
        
        return leaks
    
    def _handle_resource_leaks(self, leaks: List[ResourceLeak]):
        """リソースリーク対応"""
        for leak in leaks:
            logger.error(f"リソースリーク検出: {leak.resource_type} (+{leak.leak_count}, {leak.leak_rate:.1f}/min)")
            
            if leak.severity in ['critical', 'high']:
                if leak.resource_type == "python_objects":
                    self._aggressive_memory_cleanup()
                elif leak.resource_type == "threads":
                    self._cleanup_dead_threads()
    
    def _emergency_memory_cleanup(self):
        """緊急メモリクリーンアップ"""
        logger.warning("🚨 緊急メモリクリーンアップ実行...")
        
        # 強制ガベージコレクション
        collected = gc.collect()
        logger.info(f"ガベージコレクション: {collected}オブジェクトを回収")
        
        # 登録されたクリーンアップコールバック実行
        for resource_type, callback in self.resource_callbacks.items():
            try:
                callback()
                logger.info(f"{resource_type} クリーンアップ完了")
            except Exception as e:
                logger.error(f"{resource_type} クリーンアップ失敗: {e}")
        
        # メモリマップファイルの解放
        self._release_memory_maps()
    
    def _preventive_memory_cleanup(self):
        """予防的メモリクリーンアップ"""
        logger.info("🧹 予防的メモリクリーンアップ実行...")
        
        # 軽量なガベージコレクション
        gc.collect(1)  # 世代1まで
        
        # 古いメモリ履歴削除
        if len(self.memory_history) > 500:
            # 古い半分を削除
            for _ in range(len(self.memory_history) // 2):
                self.memory_history.popleft()
    
    def _aggressive_memory_cleanup(self):
        """積極的メモリクリーンアップ"""
        logger.warning("💣 積極的メモリクリーンアップ実行...")
        
        # 全世代のガベージコレクション
        for generation in range(3):
            collected = gc.collect(generation)
            logger.debug(f"世代{generation} GC: {collected}オブジェクト回収")
        
        # 弱参照クリーンアップ
        weakref_count = len(list(weakref.getweakrefs(self)))
        logger.debug(f"弱参照数: {weakref_count}")
    
    def _cleanup_dead_threads(self):
        """デッドスレッドクリーンアップ"""
        logger.info("🧵 デッドスレッドクリーンアップ実行...")
        
        active_threads = threading.enumerate()
        dead_threads = [t for t in active_threads if not t.is_alive()]
        
        for thread in dead_threads:
            try:
                thread.join(timeout=1)
                logger.debug(f"デッドスレッド回収: {thread.name}")
            except:
                pass
    
    def _release_memory_maps(self):
        """メモリマップファイル解放"""
        try:
            # プロセスのメモリマップ情報取得・解放
            memory_maps = self.process.memory_maps()
            logger.debug(f"メモリマップ数: {len(memory_maps)}")
        except (psutil.AccessDenied, AttributeError):
            pass
    
    def _optimize_gc_settings(self):
        """ガベージコレクション設定最適化"""
        # GC閾値をメモリ効率重視に調整
        gc.set_threshold(700, 10, 10)  # デフォルト: (700, 10, 10)
        
        # デバッグフラグを無効化（本番環境）
        gc.set_debug(0)
        
        logger.debug("ガベージコレクション設定を最適化しました")
    
    def register_cleanup_callback(self, resource_type: str, callback: Callable):
        """クリーンアップコールバック登録"""
        self.resource_callbacks[resource_type] = callback
        logger.debug(f"クリーンアップコールバック登録: {resource_type}")
    
    def track_resource(self, resource_id: str, resource: Any):
        """リソース追跡"""
        with self._lock:
            self.tracked_resources[resource_id] = {
                'resource': weakref.ref(resource),
                'created': datetime.now(),
                'type': type(resource).__name__
            }
            
            # 循環参照追跡にも登録
            self.circular_tracker.track_object(resource, resource_id)
    
    def release_resource(self, resource_id: str):
        """リソース解放"""
        with self._lock:
            if resource_id in self.tracked_resources:
                del self.tracked_resources[resource_id]
                logger.debug(f"リソース解放: {resource_id}")
    
    @contextmanager
    def memory_limit_context(self, limit_mb: Optional[int] = None):
        """メモリ制限コンテキスト"""
        original_limit = self.max_memory_mb
        if limit_mb:
            self.max_memory_mb = limit_mb
            
        try:
            yield
        finally:
            self.max_memory_mb = original_limit
    
    def get_memory_report(self) -> Dict:
        """メモリレポート生成"""
        if not self.memory_history:
            return {"error": "メモリ履歴がありません"}
        
        current = self.memory_history[-1]
        
        # 統計計算
        memory_values = [s.process_memory for s in self.memory_history]
        
        report = {
            "current_memory_mb": current.process_memory,
            "max_memory_mb": max(memory_values),
            "min_memory_mb": min(memory_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "python_objects": current.python_objects,
            "active_threads": current.active_threads,
            "open_files": current.open_files,
            "gc_collections": current.gc_collections,
            "memory_trend": self._calculate_memory_trend(list(self.memory_history)[-10:]) if len(self.memory_history) >= 10 else 0,
            "tracked_resources": len(self.tracked_resources),
            "monitoring_duration": len(self.memory_history) * self.check_interval,
            "timestamp": current.timestamp.isoformat()
        }
        
        return report

# グローバルインスタンス
memory_manager = MemoryManager()

# 便利関数
def start_memory_monitoring():
    """メモリ監視開始"""
    memory_manager.start_monitoring()

def stop_memory_monitoring():
    """メモリ監視停止"""
    memory_manager.stop_monitoring()

def emergency_cleanup():
    """緊急クリーンアップ"""
    memory_manager._emergency_memory_cleanup()

def get_memory_status() -> Dict:
    """メモリ状況取得"""
    return memory_manager.get_memory_report()

@contextmanager
def memory_tracking(resource_id: str, resource: Any):
    """リソース追跡コンテキスト"""
    memory_manager.track_resource(resource_id, resource)
    try:
        yield resource
    finally:
        memory_manager.release_resource(resource_id)

# テスト関数
def test_memory_manager():
    """メモリマネージャーテスト"""
    logger.info("🧪 メモリマネージャーテスト開始")
    
    # 監視開始
    start_memory_monitoring()
    
    # メモリ使用テスト
    test_data = []
    for i in range(10):
        # 意図的にメモリを使用
        data = list(range(10000))
        test_data.append(data)
        time.sleep(1)
    
    # レポート生成
    report = get_memory_status()
    logger.info(f"メモリレポート: {report}")
    
    # クリーンアップテスト
    emergency_cleanup()
    
    # 監視停止
    stop_memory_monitoring()
    
    logger.info("🎯 メモリマネージャーテスト完了")

if __name__ == "__main__":
    test_memory_manager()