"""ストリーミングパーサのパフォーマンス最適化機能"""

import statistics
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .interfaces import StreamingParserConfig


@dataclass
class PerformanceMetrics:
    """パフォーマンス測定結果"""

    total_time: float = 0.0
    chunk_processing_times: List[float] = field(default_factory=list)
    memory_usage_samples: List[int] = field(default_factory=list)
    throughput_mbps: float = 0.0
    chunks_per_second: float = 0.0
    average_chunk_time: float = 0.0
    median_chunk_time: float = 0.0
    max_chunk_time: float = 0.0
    min_chunk_time: float = 0.0
    memory_peak_mb: float = 0.0
    memory_average_mb: float = 0.0
    gc_count: int = 0
    gc_time: float = 0.0

    def calculate_statistics(self) -> None:
        """統計値を計算"""
        if self.chunk_processing_times:
            self.average_chunk_time = statistics.mean(self.chunk_processing_times)
            self.median_chunk_time = statistics.median(self.chunk_processing_times)
            self.max_chunk_time = max(self.chunk_processing_times)
            self.min_chunk_time = min(self.chunk_processing_times)
            self.chunks_per_second = len(self.chunk_processing_times) / self.total_time if self.total_time > 0 else 0

        if self.memory_usage_samples:
            self.memory_peak_mb = max(self.memory_usage_samples) / 1024 / 1024
            self.memory_average_mb = statistics.mean(self.memory_usage_samples) / 1024 / 1024


class PerformanceProfiler:
    """パフォーマンスプロファイラー"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._start_time: Optional[float] = None
        self._chunk_start_time: Optional[float] = None
        self._total_bytes_processed = 0
        self._memory_monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start_profiling(self) -> None:
        """プロファイリング開始"""
        self._start_time = time.time()
        self._monitoring = True
        self._stop_event.clear()

        # メモリ監視スレッドを開始
        self._memory_monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self._memory_monitor_thread.start()

    def stop_profiling(self) -> PerformanceMetrics:
        """プロファイリング終了"""
        if self._start_time:
            self.metrics.total_time = time.time() - self._start_time

        # メモリ監視を停止
        self._monitoring = False
        self._stop_event.set()
        if self._memory_monitor_thread:
            self._memory_monitor_thread.join(timeout=1.0)

        # 統計値を計算
        self.metrics.calculate_statistics()

        # スループットを計算
        if self.metrics.total_time > 0:
            self.metrics.throughput_mbps = self._total_bytes_processed / 1024 / 1024 / self.metrics.total_time

        return self.metrics

    @contextmanager
    def measure_chunk_processing(self, chunk_size: int):
        """チャンク処理時間を測定"""
        start_time = time.time()
        try:
            yield
        finally:
            processing_time = time.time() - start_time
            with self._lock:
                self.metrics.chunk_processing_times.append(processing_time)
                self._total_bytes_processed += chunk_size

    def _monitor_memory(self) -> None:
        """メモリ使用量を監視"""
        import psutil

        process = psutil.Process()

        while not self._stop_event.is_set():
            try:
                memory_info = process.memory_info()
                with self._lock:
                    self.metrics.memory_usage_samples.append(memory_info.rss)
            except Exception:
                pass

            time.sleep(0.1)  # 100ms間隔でサンプリング

    def add_gc_event(self, gc_time: float) -> None:
        """ガベージコレクションイベントを記録"""
        with self._lock:
            self.metrics.gc_count += 1
            self.metrics.gc_time += gc_time


class AdaptiveChunkSizer:
    """適応的チャンクサイズ調整器"""

    def __init__(self, config: StreamingParserConfig):
        self.config = config
        self._performance_history: deque = deque(maxlen=10)
        self._current_chunk_size = config.default_chunk_size
        self._adjustment_factor = 1.0

    def get_optimal_chunk_size(
        self, file_size: int, available_memory: int, recent_performance: Optional[PerformanceMetrics] = None
    ) -> int:
        """最適なチャンクサイズを取得"""

        # ベースサイズを計算
        base_size = self.config.adjust_chunk_size(file_size)

        # メモリ制約を考慮
        memory_limited_size = min(base_size, available_memory // 4)  # 利用可能メモリの1/4を上限

        # パフォーマンス履歴を考慮
        if recent_performance and self._should_adjust_size(recent_performance):
            adjusted_size = self._adjust_based_on_performance(memory_limited_size, recent_performance)
        else:
            adjusted_size = memory_limited_size

        # 範囲内に制限
        final_size = max(self.config.min_chunk_size, min(adjusted_size, self.config.max_chunk_size))

        self._current_chunk_size = final_size
        return final_size

    def _should_adjust_size(self, performance: PerformanceMetrics) -> bool:
        """サイズ調整が必要かを判定"""

        # メモリ使用量が高すぎる場合
        if performance.memory_peak_mb > (self.config.max_memory_usage / 1024 / 1024 * 0.8):
            return True

        # 処理時間のばらつきが大きい場合
        if performance.chunk_processing_times and len(performance.chunk_processing_times) > 3:
            std_dev = statistics.stdev(performance.chunk_processing_times)
            mean_time = statistics.mean(performance.chunk_processing_times)
            if std_dev > mean_time * 0.5:  # 標準偏差が平均の50%以上
                return True

        return False

    def _adjust_based_on_performance(self, current_size: int, performance: PerformanceMetrics) -> int:
        """パフォーマンスに基づいてサイズを調整"""

        # メモリ使用量によるペナルティ
        memory_ratio = performance.memory_peak_mb / (self.config.max_memory_usage / 1024 / 1024)
        if memory_ratio > 0.8:
            # メモリ使用量が多い場合はサイズを減らす
            memory_factor = 0.7
        elif memory_ratio < 0.5:
            # メモリ使用量が少ない場合はサイズを増やす
            memory_factor = 1.2
        else:
            memory_factor = 1.0

        # 処理時間によるボーナス
        if performance.average_chunk_time > 0:
            target_time = 1.0  # 目標：1秒/チャンク
            time_factor = target_time / performance.average_chunk_time
            time_factor = max(0.5, min(2.0, time_factor))  # 0.5-2.0の範囲に制限
        else:
            time_factor = 1.0

        # 調整係数を計算
        adjustment = memory_factor * time_factor
        adjusted_size = int(current_size * adjustment)

        return adjusted_size


class CacheOptimizer:
    """キャッシュ最適化器"""

    def __init__(self):
        self._cache_hit_rates: Dict[str, float] = {}
        self._cache_usage_patterns: Dict[str, List[float]] = {}

    def analyze_cache_patterns(self, cache_stats: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュパターンを分析"""

        recommendations = {
            "cache_size_adjustments": {},
            "ttl_adjustments": {},
            "eviction_policy_suggestions": {},
            "overall_efficiency": 0.0,
        }

        total_hits = 0
        total_requests = 0

        for cache_name, stats in cache_stats.items():
            hits = stats.get("hits", 0)
            misses = stats.get("misses", 0)
            total_requests_cache = hits + misses

            if total_requests_cache > 0:
                hit_rate = hits / total_requests_cache
                self._cache_hit_rates[cache_name] = hit_rate

                total_hits += hits
                total_requests += total_requests_cache

                # キャッシュサイズの推奨
                if hit_rate < 0.7:  # 70%未満の場合
                    recommendations["cache_size_adjustments"][cache_name] = "increase"
                elif hit_rate > 0.95:  # 95%以上の場合
                    recommendations["cache_size_adjustments"][cache_name] = "decrease"

                # TTLの推奨
                avg_access_time = stats.get("avg_access_time", 0)
                if avg_access_time > 300:  # 5分以上古い
                    recommendations["ttl_adjustments"][cache_name] = "decrease"
                elif avg_access_time < 30:  # 30秒未満
                    recommendations["ttl_adjustments"][cache_name] = "increase"

        # 全体効率
        if total_requests > 0:
            recommendations["overall_efficiency"] = total_hits / total_requests

        return recommendations

    def optimize_memory_layout(self, chunk_access_patterns: List[Tuple[int, float]]) -> Dict[str, Any]:
        """メモリレイアウトを最適化"""

        # アクセスパターンの分析
        access_times = [time for _, time in chunk_access_patterns]
        chunk_indices = [idx for idx, _ in chunk_access_patterns]

        # 局所性の分析
        locality_score = self._calculate_locality(chunk_indices)

        # 推奨事項
        recommendations = {
            "prefetch_distance": 2 if locality_score > 0.8 else 1,
            "cache_line_size": 64 * 1024 if locality_score > 0.6 else 32 * 1024,
            "memory_pooling": locality_score > 0.7,
            "async_loading": len(chunk_access_patterns) > 10,
        }

        return recommendations

    def _calculate_locality(self, indices: List[int]) -> float:
        """空間局所性を計算"""
        if len(indices) < 2:
            return 0.0

        sequential_accesses = 0
        total_transitions = len(indices) - 1

        for i in range(total_transitions):
            if abs(indices[i + 1] - indices[i]) <= 2:  # 2チャンク以内
                sequential_accesses += 1

        return sequential_accesses / total_transitions


class ParallelProcessingOptimizer:
    """並列処理最適化器"""

    def __init__(self, config: StreamingParserConfig):
        self.config = config
        self._cpu_count = self._get_cpu_count()

    def get_optimal_worker_count(
        self, chunk_count: int, avg_chunk_processing_time: float, memory_per_chunk: int
    ) -> int:
        """最適なワーカー数を計算"""

        # CPUバウンドかI/Oバウンドかを判定
        is_cpu_bound = avg_chunk_processing_time > 0.1  # 100ms以上はCPUバウンド

        if is_cpu_bound:
            # CPUバウンドの場合はCPU数まで
            max_workers = self._cpu_count
        else:
            # I/Oバウンドの場合はより多くのワーカーを許可
            max_workers = self._cpu_count * 2

        # メモリ制約を考慮
        available_memory = self.config.max_memory_usage
        memory_limited_workers = available_memory // memory_per_chunk

        # 実際のワーカー数を決定
        optimal_workers = min(
            max_workers, memory_limited_workers, chunk_count, self.config.worker_threads  # チャンク数以上は不要
        )

        return max(1, optimal_workers)  # 最低1ワーカー

    def _get_cpu_count(self) -> int:
        """CPU数を取得"""
        import os

        return os.cpu_count() or 1


@contextmanager
def performance_profiling():
    """パフォーマンスプロファイリングのコンテキストマネージャー"""
    profiler = PerformanceProfiler()
    profiler.start_profiling()
    try:
        yield profiler
    finally:
        metrics = profiler.stop_profiling()
        print(f"\\n=== パフォーマンス結果 ===")
        print(f"総処理時間: {metrics.total_time:.2f}秒")
        print(f"スループット: {metrics.throughput_mbps:.2f} MB/s")
        print(f"チャンク/秒: {metrics.chunks_per_second:.2f}")
        print(f"平均チャンク処理時間: {metrics.average_chunk_time:.3f}秒")
        print(f"メモリピーク: {metrics.memory_peak_mb:.1f} MB")
        print(f"GC回数: {metrics.gc_count}")
        print("========================")
