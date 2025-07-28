#!/usr/bin/env python3
"""
Performance Optimizer - Important Technical Debt Fix
パフォーマンス最適化システム

目的: スケーラビリティ改善とパフォーマンス最適化
- インテリジェントキャッシング
- 並列処理最適化
- I/O効率化
- メモリ使用量最適化
"""

import asyncio
import concurrent.futures
import functools
import hashlib
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import OrderedDict
import json
import pickle

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: Optional[int] = None

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    operation_name: str
    execution_time: float
    memory_usage: int
    cache_hit: bool
    timestamp: datetime

class LRUCache:
    """LRU（Least Recently Used）キャッシュ"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        with self._lock:
            if key not in self.cache:
                self._stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # TTLチェック
            if self._is_expired(entry):
                del self.cache[key]
                self._stats['misses'] += 1
                return None
            
            # LRUアップデート
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self.cache.move_to_end(key)
            
            self._stats['hits'] += 1
            return entry.value
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """キャッシュに値を設定"""
        with self._lock:
            size_bytes = self._calculate_size(value)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                size_bytes=size_bytes,
                ttl_seconds=ttl_seconds or self.ttl_seconds
            )
            
            # 既存エントリの更新
            if key in self.cache:
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                # 新規エントリの追加
                self.cache[key] = entry
                
                # サイズ制限チェック
                while len(self.cache) > self.max_size:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    self._stats['evictions'] += 1
            
            self._stats['size'] = len(self.cache)
    
    def clear(self):
        """キャッシュクリア"""
        with self._lock:
            self.cache.clear()
            self._stats['size'] = 0
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """TTL期限切れチェック"""
        if entry.ttl_seconds is None:
            return False
        
        elapsed = (datetime.now() - entry.created_at).total_seconds()
        return elapsed > entry.ttl_seconds
    
    def _calculate_size(self, value: Any) -> int:
        """値のサイズ計算"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value))
    
    def get_stats(self) -> Dict:
        """キャッシュ統計取得"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / max(total_requests, 1) * 100
            
            return {
                **self._stats,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

class PersistentCache:
    """永続化キャッシュ（SQLite使用）"""
    
    def __init__(self, db_path: Path, table_name: str = "cache"):
        self.db_path = db_path
        self.table_name = table_name
        self._lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at TIMESTAMP,
                    accessed_at TIMESTAMP,
                    access_count INTEGER,
                    ttl_seconds INTEGER
                )
            """)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_accessed 
                ON {self.table_name}(accessed_at)
            """)
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(f"""
                        SELECT value, created_at, ttl_seconds 
                        FROM {self.table_name} 
                        WHERE key = ?
                    """, (key,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    value_blob, created_at_str, ttl_seconds = row
                    created_at = datetime.fromisoformat(created_at_str)
                    
                    # TTLチェック
                    if ttl_seconds and (datetime.now() - created_at).total_seconds() > ttl_seconds:
                        self.delete(key)
                        return None
                    
                    # アクセス情報更新
                    conn.execute(f"""
                        UPDATE {self.table_name} 
                        SET accessed_at = ?, access_count = access_count + 1
                        WHERE key = ?
                    """, (datetime.now().isoformat(), key))
                    
                    return pickle.loads(value_blob)
                    
            except Exception as e:
                logger.error(f"永続キャッシュ取得エラー: {e}")
                return None
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """キャッシュに値を設定"""
        with self._lock:
            try:
                value_blob = pickle.dumps(value)
                now = datetime.now().isoformat()
                
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(f"""
                        INSERT OR REPLACE INTO {self.table_name}
                        (key, value, created_at, accessed_at, access_count, ttl_seconds)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (key, value_blob, now, now, ttl_seconds))
                    
            except Exception as e:
                logger.error(f"永続キャッシュ設定エラー: {e}")
    
    def delete(self, key: str):
        """キャッシュから削除"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute(f"DELETE FROM {self.table_name} WHERE key = ?", (key,))
            except Exception as e:
                logger.error(f"永続キャッシュ削除エラー: {e}")
    
    def cleanup_expired(self):
        """期限切れエントリの削除"""
        with self._lock:
            try:
                now = datetime.now()
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(f"""
                        SELECT key, created_at, ttl_seconds 
                        FROM {self.table_name} 
                        WHERE ttl_seconds IS NOT NULL
                    """)
                    
                    expired_keys = []
                    for key, created_at_str, ttl_seconds in cursor:
                        created_at = datetime.fromisoformat(created_at_str)
                        if (now - created_at).total_seconds() > ttl_seconds:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        conn.execute(f"DELETE FROM {self.table_name} WHERE key = ?", (key,))
                    
                    logger.info(f"期限切れキャッシュ削除: {len(expired_keys)}件")
                    
            except Exception as e:
                logger.error(f"期限切れキャッシュ削除エラー: {e}")

class ParallelExecutor:
    """並列実行最適化クラス"""
    
    def __init__(self, max_workers: Optional[int] = None):
        # CPU数の取得（macOS互換）
        try:
            cpu_count = len(os.sched_getaffinity(0))
        except (AttributeError, OSError):
            cpu_count = os.cpu_count() or 4
        
        self.max_workers = max_workers or min(32, cpu_count + 4)
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers)
    
    def execute_parallel(self, 
                        func: Callable, 
                        items: List[Any], 
                        use_processes: bool = False,
                        timeout: Optional[float] = None) -> List[Any]:
        """並列実行"""
        executor = self.process_pool if use_processes else self.thread_pool
        
        try:
            futures = [executor.submit(func, item) for item in items]
            results = []
            
            for future in concurrent.futures.as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"並列実行タスクエラー: {e}")
                    results.append(None)
            
            return results
            
        except concurrent.futures.TimeoutError:
            logger.error("並列実行タイムアウト")
            return []
    
    async def execute_async(self, 
                          func: Callable, 
                          items: List[Any]) -> List[Any]:
        """非同期並列実行"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_func(item):
            async with semaphore:
                return await asyncio.get_event_loop().run_in_executor(None, func, item)
        
        tasks = [bounded_func(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    def shutdown(self):
        """実行プール終了"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

class PerformanceOptimizer:
    """パフォーマンス最適化システム"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cache_dir = project_root / ".performance_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # キャッシングシステム
        self.memory_cache = LRUCache(max_size=2000, ttl_seconds=3600)  # 1時間TTL
        self.persistent_cache = PersistentCache(
            self.cache_dir / "performance_cache.db"
        )
        
        # 並列実行システム
        self.parallel_executor = ParallelExecutor()
        
        # パフォーマンス監視
        self.metrics_history = []
        self._lock = threading.RLock()
    
    def cached_function(self, 
                       ttl_seconds: Optional[int] = None,
                       use_persistent: bool = False,
                       cache_key_func: Optional[Callable] = None):
        """関数キャッシングデコレータ"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # キャッシュキー生成
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # キャッシュから取得試行
                cache = self.persistent_cache if use_persistent else self.memory_cache
                cached_value = cache.get(cache_key)
                
                start_time = time.time()
                
                if cached_value is not None:
                    # キャッシュヒット
                    execution_time = time.time() - start_time
                    self._record_metrics(func.__name__, execution_time, 0, True)
                    return cached_value
                
                # 関数実行
                import psutil
                process = psutil.Process()
                memory_before = process.memory_info().rss
                
                result = func(*args, **kwargs)
                
                memory_after = process.memory_info().rss
                execution_time = time.time() - start_time
                memory_usage = memory_after - memory_before
                
                # 結果をキャッシュに保存
                cache.put(cache_key, result, ttl_seconds)
                
                # メトリクス記録
                self._record_metrics(func.__name__, execution_time, memory_usage, False)
                
                return result
                
            return wrapper
        return decorator
    
    def batch_process(self, 
                     func: Callable, 
                     items: List[Any], 
                     batch_size: int = 100,
                     use_parallel: bool = True) -> List[Any]:
        """バッチ処理最適化"""
        if not items:
            return []
        
        results = []
        
        # バッチサイズに分割
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            if use_parallel and len(batch) > 1:
                # 並列実行
                batch_results = self.parallel_executor.execute_parallel(func, batch)
            else:
                # 逐次実行
                batch_results = [func(item) for item in batch]
            
            results.extend(batch_results)
        
        return results
    
    def optimize_file_operations(self, 
                                file_paths: List[Path], 
                                operation: Callable,
                                chunk_size: int = 8192) -> List[Any]:
        """ファイル操作最適化"""
        def optimized_operation(file_path: Path):
            try:
                # ファイルサイズチェック
                if not file_path.exists():
                    return None
                
                file_size = file_path.stat().st_size
                
                # 小さなファイルは通常処理
                if file_size < chunk_size:
                    return operation(file_path)
                
                # 大きなファイルはチャンク読み取り
                results = []
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        
                        chunk_result = operation(chunk)
                        if chunk_result:
                            results.append(chunk_result)
                
                return results
                
            except Exception as e:
                logger.error(f"ファイル操作最適化エラー {file_path}: {e}")
                return None
        
        return self.batch_process(optimized_operation, file_paths)
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """キャッシュキー生成"""
        key_data = {
            'function': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _record_metrics(self, operation_name: str, execution_time: float, 
                       memory_usage: int, cache_hit: bool):
        """パフォーマンスメトリクス記録"""
        with self._lock:
            metric = PerformanceMetrics(
                operation_name=operation_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cache_hit=cache_hit,
                timestamp=datetime.now()
            )
            
            self.metrics_history.append(metric)
            
            # 履歴サイズ制限
            if len(self.metrics_history) > 10000:
                self.metrics_history = self.metrics_history[-5000:]
    
    def get_performance_report(self) -> Dict:
        """パフォーマンスレポート生成"""
        with self._lock:
            if not self.metrics_history:
                return {"error": "メトリクス履歴がありません"}
            
            # 統計計算
            total_operations = len(self.metrics_history)
            cache_hits = sum(1 for m in self.metrics_history if m.cache_hit)
            cache_hit_rate = cache_hits / total_operations * 100
            
            execution_times = [m.execution_time for m in self.metrics_history]
            avg_execution_time = sum(execution_times) / len(execution_times)
            
            # 関数別統計
            function_stats = {}
            for metric in self.metrics_history:
                func_name = metric.operation_name
                if func_name not in function_stats:
                    function_stats[func_name] = {
                        'count': 0,
                        'total_time': 0,
                        'cache_hits': 0
                    }
                
                function_stats[func_name]['count'] += 1
                function_stats[func_name]['total_time'] += metric.execution_time
                if metric.cache_hit:
                    function_stats[func_name]['cache_hits'] += 1
            
            # レポート生成
            report = {
                "total_operations": total_operations,
                "cache_hit_rate": cache_hit_rate,
                "avg_execution_time": avg_execution_time,
                "memory_cache_stats": self.memory_cache.get_stats(),
                "function_statistics": {
                    func: {
                        **stats,
                        'avg_time': stats['total_time'] / stats['count'],
                        'cache_hit_rate': stats['cache_hits'] / stats['count'] * 100
                    } for func, stats in function_stats.items()
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return report
    
    def cleanup_caches(self):
        """キャッシュクリーンアップ"""
        logger.info("🧹 パフォーマンスキャッシュクリーンアップ開始...")
        
        # メモリキャッシュクリア
        self.memory_cache.clear()
        
        # 永続キャッシュの期限切れ削除
        self.persistent_cache.cleanup_expired()
        
        logger.info("✅ パフォーマンスキャッシュクリーンアップ完了")
    
    def shutdown(self):
        """最適化システム終了"""
        logger.info("⚡ パフォーマンス最適化システム終了中...")
        
        # 並列実行プール終了
        self.parallel_executor.shutdown()
        
        # キャッシュクリーンアップ
        self.cleanup_caches()
        
        logger.info("👋 パフォーマンス最適化システム終了完了")

# グローバルインスタンス
performance_optimizer = None

def init_performance_optimizer(project_root: Path):
    """パフォーマンス最適化システム初期化"""
    global performance_optimizer
    performance_optimizer = PerformanceOptimizer(project_root)
    return performance_optimizer

def get_performance_optimizer() -> Optional[PerformanceOptimizer]:
    """パフォーマンス最適化システム取得"""
    return performance_optimizer

# 便利デコレータ
def cached(ttl_seconds: Optional[int] = None, use_persistent: bool = False):
    """キャッシング便利デコレータ"""
    def decorator(func):
        if performance_optimizer:
            return performance_optimizer.cached_function(ttl_seconds, use_persistent)(func)
        return func
    return decorator

# テスト関数
def test_performance_optimizer():
    """パフォーマンス最適化システムテスト"""
    logger.info("🧪 パフォーマンス最適化システムテスト開始")
    
    project_root = Path(__file__).parent.parent
    optimizer = init_performance_optimizer(project_root)
    
    # キャッシュテスト
    @optimizer.cached_function(ttl_seconds=10)
    def expensive_operation(n: int) -> int:
        time.sleep(0.1)  # 重い処理をシミュレート
        return n * n
    
    # 初回実行（キャッシュミス）
    result1 = expensive_operation(10)
    assert result1 == 100
    
    # 2回目実行（キャッシュヒット）
    result2 = expensive_operation(10)
    assert result2 == 100
    
    # 並列処理テスト
    items = list(range(10))
    results = optimizer.batch_process(expensive_operation, items, use_parallel=True)
    assert len(results) == 10
    
    # レポート生成
    report = optimizer.get_performance_report()
    logger.info(f"パフォーマンスレポート: {report}")
    
    # クリーンアップ
    optimizer.shutdown()
    
    logger.info("🎯 パフォーマンス最適化システムテスト完了")

if __name__ == "__main__":
    test_performance_optimizer()