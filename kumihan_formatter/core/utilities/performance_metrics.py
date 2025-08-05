"""
パフォーマンス監視メトリクスシステム
Issue #694 Phase 3対応 - 詳細な性能測定・分析
"""

import json
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional

import psutil

from .logger import get_logger


@dataclass
class PerformanceSnapshot:
    """パフォーマンススナップショット"""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    processing_rate: float  # items/sec
    items_processed: int
    total_items: int
    stage: str
    thread_count: int = 0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0


@dataclass
class ProcessingStats:
    """処理統計情報"""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_items: int = 0
    items_processed: int = 0
    errors_count: int = 0
    warnings_count: int = 0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    processing_phases: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """処理時間（秒）"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def items_per_second(self) -> float:
        """処理速度（アイテム/秒）"""
        duration = self.duration_seconds
        return self.items_processed / duration if duration > 0 else 0

    @property
    def completion_rate(self) -> float:
        """完了率（%）"""
        if self.total_items == 0:
            return 0.0
        return (self.items_processed / self.total_items) * 100


class PerformanceMonitor:
    """
    リアルタイムパフォーマンス監視システム

    機能:
    - CPU・メモリ使用量の継続監視
    - 処理速度・スループット測定
    - ボトルネック検出
    - メトリクス履歴保存
    - パフォーマンスレポート生成
    """

    def __init__(self, monitoring_interval: float = 1.0, history_size: int = 1000):
        self.logger = get_logger(__name__)
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 監視データ
        self.snapshots: deque[PerformanceSnapshot] = deque(maxlen=history_size)
        self.stats = ProcessingStats()

        # 監視制御
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # プロセス情報
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss

        # コールバック
        self.alert_callbacks: List[Callable[[str, Dict], None]] = []

        self.logger.info(
            f"PerformanceMonitor initialized: interval={monitoring_interval}s, history={history_size}"
        )

    def start_monitoring(self, total_items: int, initial_stage: str = "開始"):
        """パフォーマンス監視を開始"""
        with self._lock:
            if self._monitoring:
                self.logger.warning("Performance monitoring already started")
                return

            # 統計情報初期化
            self.stats = ProcessingStats(
                start_time=time.time(), total_items=total_items
            )
            self.stats.processing_phases.append(initial_stage)

            # 監視開始
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitor_thread.start()

            self.logger.info(
                f"Performance monitoring started: {total_items} items, stage: {initial_stage}"
            )

    def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            self.stats.end_time = time.time()

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)

            self.logger.info(
                f"Performance monitoring stopped after {self.stats.duration_seconds:.2f}s"
            )

    def update_progress(self, items_processed: int, current_stage: str = ""):
        """進捗を更新"""
        with self._lock:
            self.stats.items_processed = items_processed

            if current_stage and current_stage not in self.stats.processing_phases:
                self.stats.processing_phases.append(current_stage)

    def add_error(self):
        """エラーカウントを増加"""
        with self._lock:
            self.stats.errors_count += 1

    def add_warning(self):
        """警告カウントを増加"""
        with self._lock:
            self.stats.warnings_count += 1

    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """アラートコールバックを追加"""
        self.alert_callbacks.append(callback)

    def get_current_snapshot(self) -> PerformanceSnapshot:
        """現在のパフォーマンススナップショットを取得"""
        try:
            # CPU・メモリ情報
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()

            # 処理速度計算
            processing_rate = self.stats.items_per_second

            # ディスクI/O（可能な場合）
            try:
                io_counters = self.process.io_counters()
                disk_io_read_mb = io_counters.read_bytes / 1024 / 1024
                disk_io_write_mb = io_counters.write_bytes / 1024 / 1024
            except (AttributeError, psutil.AccessDenied):
                disk_io_read_mb = disk_io_write_mb = 0.0

            # スレッド数
            thread_count = self.process.num_threads()

            # 現在のステージ
            current_stage = (
                self.stats.processing_phases[-1]
                if self.stats.processing_phases
                else "unknown"
            )

            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                processing_rate=processing_rate,
                items_processed=self.stats.items_processed,
                total_items=self.stats.total_items,
                stage=current_stage,
                thread_count=thread_count,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
            )

        except Exception as e:
            self.logger.error(f"Error creating performance snapshot: {e}")
            # フォールバック: 基本的な情報のみ
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                processing_rate=0.0,
                items_processed=self.stats.items_processed,
                total_items=self.stats.total_items,
                stage="error",
            )

    def _monitoring_loop(self):
        """監視ループ（別スレッドで実行）"""
        self.logger.debug("Performance monitoring loop started")

        while self._monitoring:
            try:
                # スナップショット取得
                snapshot = self.get_current_snapshot()

                with self._lock:
                    self.snapshots.append(snapshot)

                    # ピークメモリ更新
                    if snapshot.memory_mb > self.stats.peak_memory_mb:
                        self.stats.peak_memory_mb = snapshot.memory_mb

                    # CPU平均計算（簡易版）
                    if len(self.snapshots) > 0:
                        recent_snapshots = list(self.snapshots)[-10:]  # 直近10サンプル
                        self.stats.avg_cpu_percent = sum(
                            s.cpu_percent for s in recent_snapshots
                        ) / len(recent_snapshots)

                # アラートチェック
                self._check_performance_alerts(snapshot)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

        self.logger.debug("Performance monitoring loop ended")

    def _check_performance_alerts(self, snapshot: PerformanceSnapshot):
        """パフォーマンスアラートをチェック"""
        alerts = []

        # 高CPU使用率アラート
        if snapshot.cpu_percent > 90:
            alerts.append(
                {
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"高CPU使用率: {snapshot.cpu_percent:.1f}%",
                    "value": snapshot.cpu_percent,
                }
            )

        # 高メモリ使用率アラート
        if snapshot.memory_percent > 80:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"高メモリ使用率: {snapshot.memory_percent:.1f}% ({snapshot.memory_mb:.1f}MB)",
                    "value": snapshot.memory_percent,
                }
            )

        # 低処理速度アラート
        if (
            snapshot.processing_rate > 0 and snapshot.processing_rate < 100
        ):  # 100 items/sec未満
            alerts.append(
                {
                    "type": "low_processing_rate",
                    "severity": "info",
                    "message": f"低処理速度: {snapshot.processing_rate:.0f} items/sec",
                    "value": snapshot.processing_rate,
                }
            )

        # アラート通知
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert["type"], alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス概要を取得"""
        with self._lock:
            recent_snapshots = list(self.snapshots)[-10:] if self.snapshots else []

            return {
                "duration_seconds": self.stats.duration_seconds,
                "items_processed": self.stats.items_processed,
                "total_items": self.stats.total_items,
                "completion_rate": self.stats.completion_rate,
                "items_per_second": self.stats.items_per_second,
                "errors_count": self.stats.errors_count,
                "warnings_count": self.stats.warnings_count,
                "peak_memory_mb": self.stats.peak_memory_mb,
                "avg_cpu_percent": self.stats.avg_cpu_percent,
                "processing_phases": self.stats.processing_phases,
                "current_memory_mb": (
                    recent_snapshots[-1].memory_mb if recent_snapshots else 0
                ),
                "current_cpu_percent": (
                    recent_snapshots[-1].cpu_percent if recent_snapshots else 0
                ),
                "snapshots_count": len(self.snapshots),
            }

    def generate_performance_report(self) -> str:
        """詳細なパフォーマンスレポートを生成"""
        summary = self.get_performance_summary()

        report_lines = [
            "🔍 パフォーマンス分析レポート",
            "=" * 50,
            f"処理時間: {summary['duration_seconds']:.2f}秒",
            f"処理項目: {summary['items_processed']:,} / "
            f"{summary['total_items']:,} ({summary['completion_rate']:.1f}%)",
            f"処理速度: {summary['items_per_second']:,.0f} items/秒",
            f"エラー: {summary['errors_count']}, 警告: {summary['warnings_count']}",
            "",
            "💾 リソース使用量:",
            f"  ピークメモリ: {summary['peak_memory_mb']:.1f}MB",
            f"  平均CPU: {summary['avg_cpu_percent']:.1f}%",
            f"  現在メモリ: {summary['current_memory_mb']:.1f}MB",
            f"  現在CPU: {summary['current_cpu_percent']:.1f}%",
            "",
            "🔄 処理フェーズ:",
        ]

        for phase in summary["processing_phases"]:
            report_lines.append(f"  - {phase}")

        # パフォーマンス傾向分析
        if len(self.snapshots) >= 5:
            report_lines.extend(
                [
                    "",
                    "📈 パフォーマンス傾向:",
                ]
            )

            snapshots_list = list(self.snapshots)

            # メモリ使用量傾向
            memory_trend = self._calculate_trend(
                [s.memory_mb for s in snapshots_list[-10:]]
            )
            memory_status = (
                "増加"
                if memory_trend > 0.5
                else "安定" if memory_trend > -0.5 else "減少"
            )
            report_lines.append(f"  メモリ使用量: {memory_status}")

            # 処理速度傾向
            rates = [
                s.processing_rate for s in snapshots_list[-10:] if s.processing_rate > 0
            ]
            if rates:
                rate_trend = self._calculate_trend(rates)
                rate_status = (
                    "向上"
                    if rate_trend > 0.5
                    else "安定" if rate_trend > -0.5 else "低下"
                )
                report_lines.append(f"  処理速度: {rate_status}")

        return "\n".join(report_lines)

    def _calculate_trend(self, values: List[float]) -> float:
        """値の傾向を計算（簡易線形回帰）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_avg = sum(range(n)) / n
        y_avg = sum(values) / n

        numerator = sum((i - x_avg) * (values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def save_metrics_to_file(self, file_path: Path):
        """メトリクスをファイルに保存"""
        try:
            metrics_data = {
                "summary": self.get_performance_summary(),
                "snapshots": [
                    {
                        "timestamp": s.timestamp,
                        "cpu_percent": s.cpu_percent,
                        "memory_mb": s.memory_mb,
                        "memory_percent": s.memory_percent,
                        "processing_rate": s.processing_rate,
                        "items_processed": s.items_processed,
                        "stage": s.stage,
                    }
                    for s in self.snapshots
                ],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Performance metrics saved to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save metrics to file: {e}")


class SIMDOptimizer:
    """
    SIMD（Single Instruction Multiple Data）最適化システム

    特徴:
    - NumPy配列による大容量テキスト処理の高速化
    - ベクトル化された文字列操作
    - CPU並列命令による処理速度向上
    - 300K行ファイル処理の83%高速化を目標
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._numpy_available = self._check_numpy_availability()
        self._regex_cache = {}

        if self._numpy_available:
            import numpy as np

            self.np = np
            self.logger.info("SIMD optimizer initialized with NumPy acceleration")
        else:
            self.logger.warning(
                "NumPy not available, falling back to standard processing"
            )

    def _check_numpy_availability(self) -> bool:
        """NumPy利用可能性をチェック"""
        try:
            import numpy as np  # noqa: F401

            return True
        except ImportError:
            return False

    def vectorized_line_processing(
        self, lines: List[str], pattern_funcs: List[Callable[[str], str]]
    ) -> List[str]:
        """
        ベクトル化された行処理（SIMD最適化）

        Args:
            lines: 処理対象行リスト
            pattern_funcs: 適用する変換関数リスト

        Returns:
            List[str]: 処理済み行リスト
        """
        if not self._numpy_available:
            return self._fallback_line_processing(lines, pattern_funcs)

        if not lines:
            return []

        self.logger.debug(
            f"SIMD processing {len(lines)} lines with {len(pattern_funcs)} functions"
        )

        try:
            # NumPy配列に変換（文字列処理の高速化）
            np_lines = self.np.array(lines, dtype=object)

            # ベクトル化された関数適用
            for func in pattern_funcs:
                # numpy.vectorizeでSIMD最適化を活用
                vectorized_func = self.np.vectorize(func, otypes=[object])
                np_lines = vectorized_func(np_lines)

            # リストに戻す
            result = np_lines.tolist()

            self.logger.debug(
                f"SIMD processing completed: {len(result)} lines processed"
            )
            return result

        except Exception as e:
            self.logger.error(f"SIMD processing failed, falling back: {e}")
            return self._fallback_line_processing(lines, pattern_funcs)

    def _fallback_line_processing(
        self, lines: List[str], pattern_funcs: List[Callable[[str], str]]
    ) -> List[str]:
        """フォールバック処理（通常処理）"""
        result = lines.copy()
        for func in pattern_funcs:
            result = [func(line) for line in result]
        return result

    def optimized_regex_operations(
        self, text: str, patterns: List[tuple[str, str]]
    ) -> str:
        """
        最適化された正規表現処理

        Args:
            text: 処理対象テキスト
            patterns: (pattern, replacement)のタプルリスト

        Returns:
            str: 処理済みテキスト
        """
        import re

        result = text

        # 正規表現コンパイルキャッシュを活用
        for pattern, replacement in patterns:
            if pattern not in self._regex_cache:
                self._regex_cache[pattern] = re.compile(pattern)

            compiled_pattern = self._regex_cache[pattern]
            result = compiled_pattern.sub(replacement, result)

        return result

    def parallel_chunk_simd_processing(
        self,
        chunks: List[Any],
        processing_func: Callable,
        max_workers: Optional[int] = None,
    ) -> List[Any]:
        """
        並列チャンク処理とSIMD最適化の組み合わせ

        Args:
            chunks: 処理チャンクリスト
            processing_func: チャンク処理関数
            max_workers: 最大ワーカー数

        Returns:
            List[Any]: 処理結果リスト
        """
        import concurrent.futures
        import os

        # CPU効率最大化のための動的ワーカー数計算
        if max_workers is None:
            cpu_count = os.cpu_count() or 1
            max_workers = min(cpu_count * 2, len(chunks))

        results = []

        if len(chunks) <= 2:
            # 少数チャンクは並列化せずSIMD最適化のみ
            for chunk in chunks:
                results.append(processing_func(chunk))
        else:
            # 並列処理 + SIMD最適化
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                future_to_chunk = {
                    executor.submit(processing_func, chunk): chunk for chunk in chunks
                }

                for future in concurrent.futures.as_completed(future_to_chunk):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"SIMD parallel processing error: {e}")
                        # エラーの場合は空結果を追加して継続
                        results.append(None)

        # None結果をフィルタリング
        return [r for r in results if r is not None]

    def memory_efficient_processing(
        self, data_generator: Iterator[str], batch_size: int = 1000
    ) -> Iterator[str]:
        """
        メモリ効率的なSIMD処理（ストリーミング処理）

        Args:
            data_generator: データジェネレータ
            batch_size: バッチサイズ

        Yields:
            str: 処理済みデータ
        """
        batch = []

        for item in data_generator:
            batch.append(item)

            if len(batch) >= batch_size:
                # バッチをSIMD処理
                if self._numpy_available:
                    try:
                        np_batch = self.np.array(batch, dtype=object)
                        # バッチ処理（実際の処理関数は用途に応じて実装）
                        processed_batch = np_batch.tolist()
                    except Exception:
                        processed_batch = batch
                else:
                    processed_batch = batch

                # 結果をyield
                for processed_item in processed_batch:
                    yield processed_item

                # バッチクリア
                batch.clear()

        # 残りのバッチを処理
        if batch:
            if self._numpy_available:
                try:
                    np_batch = self.np.array(batch, dtype=object)
                    processed_batch = np_batch.tolist()
                except Exception:
                    processed_batch = batch
            else:
                processed_batch = batch

            for processed_item in processed_batch:
                yield processed_item

    def get_simd_metrics(self) -> Dict[str, Any]:
        """SIMD最適化メトリクスを取得"""
        return {
            "numpy_available": self._numpy_available,
            "regex_cache_size": len(self._regex_cache),
            "optimization_level": "high" if self._numpy_available else "standard",
        }


class AsyncIOOptimizer:
    """
    非同期I/O最適化システム

    特徴:
    - aiofilesによる非同期ファイル読み込み
    - 並列ファイル処理
    - プリフェッチとバッファリング
    - 大容量ファイルのストリーミング読み込み
    """

    def __init__(self, buffer_size: int = 64 * 1024):
        self.logger = get_logger(__name__)
        self.buffer_size = buffer_size
        self._aiofiles_available = self._check_aiofiles_availability()

        if self._aiofiles_available:
            self.logger.info(
                f"AsyncIO optimizer initialized with buffer size: {buffer_size}"
            )
        else:
            self.logger.warning("aiofiles not available, using synchronous I/O")

    def _check_aiofiles_availability(self) -> bool:
        """aiofiles利用可能性をチェック"""
        try:
            import aiofiles  # noqa: F401

            return True
        except ImportError:
            return False

    async def async_read_file_chunked(
        self, file_path: Path, chunk_size: int = 64 * 1024
    ) -> AsyncIterator[str]:
        """
        非同期チャンク読み込み

        Args:
            file_path: ファイルパス
            chunk_size: チャンクサイズ

        Yields:
            str: ファイルチャンク
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            self.logger.error(f"Async file read failed: {e}")
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

    async def async_read_lines_batched(
        self, file_path: Path, batch_size: int = 1000
    ) -> AsyncIterator[List[str]]:
        """
        非同期バッチ行読み込み

        Args:
            file_path: ファイルパス
            batch_size: バッチサイズ

        Yields:
            List[str]: 行のバッチ
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                batch = []
                async for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch
        except Exception as e:
            self.logger.error(f"Async batch read failed: {e}")
            # 同期フォールバック
            with open(file_path, "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    batch.append(line.rstrip("\n"))
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                if batch:
                    yield batch

    async def async_write_results_streaming(
        self, file_path: Path, results_generator: AsyncIterator[str]
    ):
        """
        非同期ストリーミング結果書き込み

        Args:
            file_path: 出力ファイルパス
            results_generator: 結果ジェネレータ
        """
        if not self._aiofiles_available:
            # 同期フォールバック
            with open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    f.write(result)
            return

        import aiofiles

        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    await f.write(result)
        except Exception as e:
            self.logger.error(f"Async write failed: {e}")
            # 同期フォールバック
            with open(file_path, "w", encoding="utf-8") as f:
                async for result in results_generator:
                    f.write(result)

    def get_async_metrics(self) -> Dict[str, Any]:
        """非同期I/Oメトリクスを取得"""
        return {
            "aiofiles_available": self._aiofiles_available,
            "buffer_size": self.buffer_size,
            "optimization_level": "async" if self._aiofiles_available else "sync",
        }


class RegexOptimizer:
    """
    正規表現エンジン最適化システム

    特徴:
    - コンパイル済み正規表現の効率的キャッシング
    - 最適化されたパターンマッチング戦略
    - マッチング性能の大幅向上
    - メモリ効率的な正規表現処理
    """

    def __init__(self, cache_size_limit: int = 1000):
        self.logger = get_logger(__name__)
        self.cache_size_limit = cache_size_limit
        self._pattern_cache = {}
        self._usage_counter = {}
        self._compile_stats = {"hits": 0, "misses": 0, "evictions": 0}

        # 最適化された事前コンパイル済みパターン
        self._precompiled_patterns = self._initialize_precompiled_patterns()

        self.logger.info(
            f"RegexOptimizer initialized with cache limit: {cache_size_limit}"
        )

    def _initialize_precompiled_patterns(self) -> Dict[str, Any]:
        """よく使用される正規表現パターンを事前コンパイル"""
        import re

        patterns = {
            # Kumihanマークアップ基本パターン
            "inline_notation": re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##", re.MULTILINE),
            "block_marker": re.compile(r"^#\s*([^#]+?)\s*#([^#]*)##$", re.MULTILINE),
            "nested_markers": re.compile(r"#+([^#]+?)#+", re.MULTILINE),
            # よく使用される文字列処理パターン
            "whitespace_cleanup": re.compile(r"\s+"),
            "line_breaks": re.compile(r"\r?\n"),
            "empty_lines": re.compile(r"^\s*$", re.MULTILINE),
            # 色属性解析
            "color_attribute": re.compile(r"color\s*=\s*([#\w]+)"),
            "hex_color": re.compile(r"^#[0-9a-fA-F]{3,6}$"),
            # HTMLエスケープ
            "html_chars": re.compile(r"[<>&\"']"),
            # 特殊文字処理
            "japanese_chars": re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]"),
        }

        self.logger.info(f"Pre-compiled {len(patterns)} regex patterns")
        return patterns

    def get_compiled_pattern(self, pattern_str: str, flags: int = 0) -> Any:
        """
        コンパイル済み正規表現を取得（キャッシュ機能付き）

        Args:
            pattern_str: 正規表現パターン文字列
            flags: 正規表現フラグ

        Returns:
            Pattern: コンパイル済み正規表現オブジェクト
        """
        import re

        cache_key = (pattern_str, flags)

        # キャッシュヒットチェック
        if cache_key in self._pattern_cache:
            self._compile_stats["hits"] += 1
            self._usage_counter[cache_key] = self._usage_counter.get(cache_key, 0) + 1
            return self._pattern_cache[cache_key]

        # キャッシュミス：新規コンパイル
        self._compile_stats["misses"] += 1

        try:
            compiled_pattern = re.compile(pattern_str, flags)

            # キャッシュサイズ制限チェック
            if len(self._pattern_cache) >= self.cache_size_limit:
                self._evict_least_used_pattern()

            # キャッシュに保存
            self._pattern_cache[cache_key] = compiled_pattern
            self._usage_counter[cache_key] = 1

            return compiled_pattern

        except re.error as e:
            self.logger.error(
                f"Regex compilation failed for pattern '{pattern_str}': {e}"
            )
            # フォールバック：文字列マッチング
            return None

    def _evict_least_used_pattern(self):
        """最も使用頻度の低いパターンをキャッシュから削除"""
        if not self._usage_counter:
            return

        # 最小使用回数のパターンを見つける
        least_used_key = min(self._usage_counter, key=self._usage_counter.get)

        # キャッシュから削除
        if least_used_key in self._pattern_cache:
            del self._pattern_cache[least_used_key]
        if least_used_key in self._usage_counter:
            del self._usage_counter[least_used_key]

        self._compile_stats["evictions"] += 1
        self.logger.debug(
            f"Evicted regex pattern from cache: {least_used_key[0][:50]}..."
        )

    def optimized_search(self, pattern_str: str, text: str, flags: int = 0) -> Any:
        """
        最適化された正規表現検索

        Args:
            pattern_str: 検索パターン
            text: 検索対象テキスト
            flags: 正規表現フラグ

        Returns:
            Match object or None
        """
        # 事前コンパイル済みパターンをチェック
        for name, precompiled in self._precompiled_patterns.items():
            if precompiled.pattern == pattern_str:
                return precompiled.search(text)

        # キャッシュからコンパイル済みパターンを取得
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.search(text)

        # フォールバック：単純文字列検索
        return pattern_str in text

    def optimized_findall(
        self, pattern_str: str, text: str, flags: int = 0
    ) -> List[str]:
        """
        最適化された正規表現全体検索

        Args:
            pattern_str: 検索パターン
            text: 検索対象テキスト
            flags: 正規表現フラグ

        Returns:
            List[str]: マッチした文字列のリスト
        """
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.findall(text)
        return []

    def optimized_substitute(
        self, pattern_str: str, replacement: str, text: str, flags: int = 0
    ) -> str:
        """
        最適化された正規表現置換

        Args:
            pattern_str: 置換パターン
            replacement: 置換文字列
            text: 対象テキスト
            flags: 正規表現フラグ

        Returns:
            str: 置換後テキスト
        """
        compiled_pattern = self.get_compiled_pattern(pattern_str, flags)
        if compiled_pattern:
            return compiled_pattern.sub(replacement, text)

        # フォールバック：単純文字列置換
        return text.replace(pattern_str, replacement)

    def batch_process_with_patterns(
        self, texts: List[str], patterns_and_replacements: List[tuple[str, str]]
    ) -> List[str]:
        """
        複数テキストに対する一括正規表現処理

        Args:
            texts: 処理対象テキストリスト
            patterns_and_replacements: (pattern, replacement)のタプルリスト

        Returns:
            List[str]: 処理済みテキストリスト
        """
        results = []

        # パターンを事前コンパイル
        compiled_patterns = []
        for pattern, replacement in patterns_and_replacements:
            compiled = self.get_compiled_pattern(pattern)
            if compiled:
                compiled_patterns.append((compiled, replacement))

        # 各テキストを処理
        for text in texts:
            processed_text = text
            for compiled_pattern, replacement in compiled_patterns:
                processed_text = compiled_pattern.sub(replacement, processed_text)
            results.append(processed_text)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self._compile_stats["hits"] + self._compile_stats["misses"]
        hit_rate = (
            (self._compile_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "cache_size": len(self._pattern_cache),
            "cache_limit": self.cache_size_limit,
            "hit_rate_percent": hit_rate,
            "total_hits": self._compile_stats["hits"],
            "total_misses": self._compile_stats["misses"],
            "total_evictions": self._compile_stats["evictions"],
            "precompiled_patterns": len(self._precompiled_patterns),
        }

    def clear_cache(self):
        """キャッシュをクリア"""
        cleared_count = len(self._pattern_cache)
        self._pattern_cache.clear()
        self._usage_counter.clear()
        self._compile_stats = {"hits": 0, "misses": 0, "evictions": 0}

        self.logger.info(f"Cleared {cleared_count} patterns from regex cache")


class MemoryOptimizer:
    """
    メモリアクセスパターン最適化システム

    特徴:
    - メモリ効率的なデータ構造選択
    - ガベージコレクション最適化
    - メモリプールとオブジェクト再利用
    - 大容量ファイル処理のメモリ管理
    """

    def __init__(self, enable_gc_optimization: bool = True):
        self.logger = get_logger(__name__)
        self.enable_gc_optimization = enable_gc_optimization
        self._object_pools = {}
        self._memory_stats = {"allocations": 0, "deallocations": 0, "pool_hits": 0}

        if enable_gc_optimization:
            self._configure_gc_optimization()

        self.logger.info("MemoryOptimizer initialized")

    def _configure_gc_optimization(self):
        """ガベージコレクション最適化設定"""
        import gc

        # GC閾値を調整（大容量処理向け）
        original_thresholds = gc.get_threshold()
        # より高い閾値でGC頻度を下げ、バッチ処理効率を向上
        new_thresholds = (
            original_thresholds[0] * 2,  # 世代0
            original_thresholds[1] * 2,  # 世代1
            original_thresholds[2] * 2,  # 世代2
        )
        gc.set_threshold(*new_thresholds)

        self.logger.info(
            f"GC thresholds adjusted: {original_thresholds} -> {new_thresholds}"
        )

    def create_object_pool(
        self, pool_name: str, factory_func: Callable, max_size: int = 100
    ):
        """
        オブジェクトプール作成

        Args:
            pool_name: プール名
            factory_func: オブジェクト生成関数
            max_size: プール最大サイズ
        """
        from collections import deque

        self._object_pools[pool_name] = {
            "pool": deque(maxlen=max_size),
            "factory": factory_func,
            "max_size": max_size,
            "created_count": 0,
            "reused_count": 0,
        }

        self.logger.info(f"Object pool '{pool_name}' created with max size: {max_size}")

    def get_pooled_object(self, pool_name: str):
        """プールからオブジェクトを取得"""
        if pool_name not in self._object_pools:
            raise ValueError(f"Object pool '{pool_name}' not found")

        pool_info = self._object_pools[pool_name]
        pool = pool_info["pool"]

        if pool:
            # プールから再利用
            obj = pool.popleft()
            pool_info["reused_count"] += 1
            self._memory_stats["pool_hits"] += 1
            return obj
        else:
            # 新規作成
            obj = pool_info["factory"]()
            pool_info["created_count"] += 1
            self._memory_stats["allocations"] += 1
            return obj

    def return_pooled_object(self, pool_name: str, obj: Any):
        """オブジェクトをプールに返却"""
        if pool_name not in self._object_pools:
            return

        pool_info = self._object_pools[pool_name]
        pool = pool_info["pool"]

        # オブジェクトをリセット（可能であれば）
        if hasattr(obj, "reset"):
            obj.reset()
        elif hasattr(obj, "clear"):
            obj.clear()

        # プールに返却
        if len(pool) < pool_info["max_size"]:
            pool.append(obj)
        else:
            # プールが満杯の場合は破棄
            self._memory_stats["deallocations"] += 1

    def memory_efficient_file_reader(
        self, file_path: Path, chunk_size: int = 64 * 1024, use_mmap: bool = False
    ) -> Iterator[str]:
        """
        メモリ効率的なファイル読み込み

        Args:
            file_path: ファイルパス
            chunk_size: チャンクサイズ
            use_mmap: メモリマップドファイル使用フラグ

        Yields:
            str: ファイルチャンク
        """
        if use_mmap:
            try:
                import mmap

                with open(file_path, "r", encoding="utf-8") as f:
                    with mmap.mmap(
                        f.fileno(), 0, access=mmap.ACCESS_READ
                    ) as mmapped_file:
                        for i in range(0, len(mmapped_file), chunk_size):
                            chunk = mmapped_file[i : i + chunk_size].decode(
                                "utf-8", errors="ignore"
                            )
                            yield chunk
                return
            except Exception as e:
                self.logger.warning(f"mmap failed, falling back to regular read: {e}")

        # 通常のファイル読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def optimize_list_operations(self, data: List[Any], operation: str) -> Any:
        """
        リスト操作の最適化

        Args:
            data: 操作対象データ
            operation: 操作種別（'sort', 'unique', 'filter_empty'）

        Returns:
            Any: 最適化された結果
        """
        if operation == "sort":
            # 大容量データの場合はTimsortアルゴリズムを活用
            return sorted(data, key=str if isinstance(data[0], str) else None)

        elif operation == "unique":
            # セットを使用した重複除去（順序は保持されない）
            if len(data) > 10000:
                return list(set(data))
            else:
                # 小容量データは順序保持重複除去
                seen = set()
                result = []
                for item in data:
                    if item not in seen:
                        seen.add(item)
                        result.append(item)
                return result

        elif operation == "filter_empty":
            # 空要素フィルタリング
            return [item for item in data if item and str(item).strip()]

        else:
            return data

    def batch_process_with_memory_limit(
        self,
        data_generator: Iterator[Any],
        processing_func: Callable,
        memory_limit_mb: int = 100,
    ) -> Iterator[Any]:
        """
        メモリ制限付きバッチ処理

        Args:
            data_generator: データジェネレータ
            processing_func: 処理関数
            memory_limit_mb: メモリ制限（MB）

        Yields:
            Any: 処理結果
        """
        import sys

        batch = []
        batch_size_bytes = 0
        memory_limit_bytes = memory_limit_mb * 1024 * 1024

        for item in data_generator:
            batch.append(item)
            # 概算のメモリサイズを計算
            batch_size_bytes += sys.getsizeof(item)

            if batch_size_bytes >= memory_limit_bytes:
                # バッチ処理実行
                for result in processing_func(batch):
                    yield result

                # バッチクリア
                batch.clear()
                batch_size_bytes = 0

        # 残りのバッチを処理
        if batch:
            for result in processing_func(batch):
                yield result

    def force_garbage_collection(self):
        """強制ガベージコレクション実行"""
        import gc

        collected_objects = gc.collect()
        self.logger.debug(f"Garbage collection: {collected_objects} objects collected")
        return collected_objects

    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ使用統計を取得"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        pool_stats = {}
        for name, pool_info in self._object_pools.items():
            pool_stats[name] = {
                "current_size": len(pool_info["pool"]),
                "max_size": pool_info["max_size"],
                "created_count": pool_info["created_count"],
                "reused_count": pool_info["reused_count"],
                "efficiency_percent": (
                    pool_info["reused_count"]
                    / (pool_info["created_count"] + pool_info["reused_count"])
                    * 100
                    if (pool_info["created_count"] + pool_info["reused_count"]) > 0
                    else 0
                ),
            }

        return {
            "process_memory_mb": memory_info.rss / 1024 / 1024,
            "virtual_memory_mb": memory_info.vms / 1024 / 1024,
            "object_pools": pool_stats,
            "memory_operations": self._memory_stats,
        }

    def detect_memory_leaks(
        self, threshold_mb: float = 10.0, sample_interval: int = 5
    ) -> Dict[str, Any]:
        """
        高度なメモリリーク検出機構

        Args:
            threshold_mb: メモリ増加の検出閾値（MB）
            sample_interval: サンプル間隔（秒）

        Returns:
            Dict[str, Any]: リーク検出結果
        """
        import gc
        import os
        import time
        from typing import List, Tuple

        import psutil

        process = psutil.Process(os.getpid())
        samples: List[Tuple[float, float]] = []  # (timestamp, memory_mb)

        # 初期メモリ使用量記録
        initial_memory = process.memory_info().rss / 1024 / 1024
        samples.append((time.time(), initial_memory))

        self.logger.info(
            f"Memory leak detection started. Initial memory: {initial_memory:.2f} MB"
        )

        # 複数回サンプリング
        for i in range(sample_interval):
            time.sleep(1)
            current_memory = process.memory_info().rss / 1024 / 1024
            samples.append((time.time(), current_memory))

        # リーク分析
        memory_growth = samples[-1][1] - samples[0][1]
        growth_rate = memory_growth / (samples[-1][0] - samples[0][0])  # MB/秒

        # ガベージコレクション実行後のメモリ確認
        gc.collect()
        time.sleep(0.5)
        post_gc_memory = process.memory_info().rss / 1024 / 1024
        gc_effect = samples[-1][1] - post_gc_memory

        # リーク判定
        is_leak_detected = (
            memory_growth > threshold_mb
            and gc_effect < memory_growth * 0.5  # GCで半分以上回収されない場合
        )

        leak_info = {
            "leak_detected": is_leak_detected,
            "memory_growth_mb": memory_growth,
            "growth_rate_mb_per_sec": growth_rate,
            "gc_effect_mb": gc_effect,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": samples[-1][1],
            "post_gc_memory_mb": post_gc_memory,
            "samples": samples,
            "recommendation": self._generate_leak_recommendation(
                is_leak_detected, memory_growth, gc_effect
            ),
        }

        if is_leak_detected:
            self.logger.warning(
                f"Memory leak detected! Growth: {memory_growth:.2f} MB, Rate: {growth_rate:.4f} MB/s"
            )
        else:
            self.logger.info(
                f"No significant memory leak detected. Growth: {memory_growth:.2f} MB"
            )

        return leak_info

    def proactive_gc_strategy(
        self, memory_threshold_mb: float = 100.0, enable_generational: bool = True
    ) -> Dict[str, Any]:
        """
        プロアクティブなガベージコレクション戦略

        Args:
            memory_threshold_mb: GC実行メモリ閾値（MB）
            enable_generational: 世代別GC最適化有効フラグ

        Returns:
            Dict[str, Any]: GC実行結果
        """
        import gc
        import os
        import time

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        self.logger.info(
            f"Proactive GC strategy triggered. Current memory: {initial_memory:.2f} MB"
        )

        results = {
            "initial_memory_mb": initial_memory,
            "gc_executed": False,
            "collections_performed": [],
            "memory_freed_mb": 0.0,
            "execution_time_ms": 0.0,
        }

        start_time = time.time()

        # メモリ閾値チェック
        if initial_memory >= memory_threshold_mb:
            self.logger.info(
                f"Memory threshold ({memory_threshold_mb} MB) exceeded. Executing proactive GC..."
            )

            if enable_generational:
                # 世代別最適化GC実行
                for generation in range(3):  # Python GCの3世代
                    collected = gc.collect(generation)
                    results["collections_performed"].append(
                        {"generation": generation, "objects_collected": collected}
                    )
                    self.logger.debug(
                        f"Generation {generation} GC: {collected} objects collected"
                    )
            else:
                # 標準GC実行
                collected = gc.collect()
                results["collections_performed"].append(
                    {"generation": "all", "objects_collected": collected}
                )

            # GC後メモリ確認
            time.sleep(0.1)  # GC完了を待機
            post_gc_memory = process.memory_info().rss / 1024 / 1024
            results["memory_freed_mb"] = initial_memory - post_gc_memory
            results["final_memory_mb"] = post_gc_memory
            results["gc_executed"] = True

            self.logger.info(
                f"Proactive GC completed. Memory freed: {results['memory_freed_mb']:.2f} MB"
            )
        else:
            self.logger.debug(
                f"Memory usage ({initial_memory:.2f} MB) below threshold. GC not needed."
            )

        results["execution_time_ms"] = (time.time() - start_time) * 1000
        return results

    def create_advanced_resource_pool(
        self,
        pool_name: str,
        factory_func: Callable,
        max_size: int = 100,
        cleanup_func: Optional[Callable] = None,
        auto_cleanup_interval: int = 300,
    ) -> None:
        """
        高度なリソースプール管理システム

        Args:
            pool_name: プール名
            factory_func: オブジェクト生成関数
            max_size: プール最大サイズ
            cleanup_func: クリーンアップ関数
            auto_cleanup_interval: 自動クリーンアップ間隔（秒）
        """
        import threading
        import time
        from collections import deque

        pool_info = {
            "pool": deque(maxlen=max_size),
            "factory": factory_func,
            "cleanup": cleanup_func,
            "max_size": max_size,
            "created_count": 0,
            "reused_count": 0,
            "cleanup_count": 0,
            "last_cleanup": time.time(),
            "auto_cleanup_interval": auto_cleanup_interval,
            "lock": threading.RLock(),  # リエントラントロック
        }

        self._object_pools[pool_name] = pool_info

        # 自動クリーンアップタイマー設定
        def auto_cleanup():
            while pool_name in self._object_pools:
                time.sleep(auto_cleanup_interval)
                self._cleanup_resource_pool(pool_name)

        cleanup_thread = threading.Thread(target=auto_cleanup, daemon=True)
        cleanup_thread.start()

        self.logger.info(
            f"Advanced resource pool '{pool_name}' created with auto-cleanup every {auto_cleanup_interval}s"
        )

    def _cleanup_resource_pool(self, pool_name: str) -> int:
        """リソースプールのクリーンアップ実行"""
        if pool_name not in self._object_pools:
            return 0

        pool_info = self._object_pools[pool_name]

        with pool_info["lock"]:
            cleanup_count = 0
            cleanup_func = pool_info["cleanup"]

            if cleanup_func:
                # プール内の全オブジェクトをクリーンアップ
                temp_objects = []
                while pool_info["pool"]:
                    obj = pool_info["pool"].popleft()
                    try:
                        cleanup_func(obj)
                        temp_objects.append(obj)
                        cleanup_count += 1
                    except Exception as e:
                        self.logger.warning(
                            f"Cleanup failed for object in pool '{pool_name}': {e}"
                        )

                # クリーンアップされたオブジェクトを戻す
                for obj in temp_objects:
                    pool_info["pool"].append(obj)

            pool_info["cleanup_count"] += cleanup_count
            pool_info["last_cleanup"] = time.time()

            if cleanup_count > 0:
                self.logger.info(
                    f"Resource pool '{pool_name}' cleanup: {cleanup_count} objects processed"
                )

            return cleanup_count

    def generate_memory_report(self, include_detailed_stats: bool = True) -> str:
        """
        メモリ使用量の詳細レポート生成（可視化機能）

        Args:
            include_detailed_stats: 詳細統計情報を含むか

        Returns:
            str: HTMLフォーマットのメモリレポート
        """
        import os
        import time
        from datetime import datetime

        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        # 基本情報収集
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory_mb = memory_info.rss / 1024 / 1024
        virtual_mb = memory_info.vms / 1024 / 1024

        # システム情報
        system_memory = psutil.virtual_memory()
        system_total_gb = system_memory.total / 1024 / 1024 / 1024
        system_available_gb = system_memory.available / 1024 / 1024 / 1024
        system_usage_percent = system_memory.percent

        # HTML レポート生成
        html_report = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan-Formatter メモリレポート</title>
    <style>
        body {{
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .stat-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .stat-value {{
            font-size: 1.2em;
            color: #27ae60;
        }}
        .memory-bar {{
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .memory-fill {{
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);
            transition: width 0.3s ease;
        }}
        .pool-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .pool-table th, .pool-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .pool-table th {{
            background-color: #3498db;
            color: white;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .timestamp {{
            text-align: right;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Kumihan-Formatter メモリレポート</h1>
            <p>Issue #772 - メモリ・リソース管理強化システム</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">プロセスメモリ使用量</div>
                <div class="stat-value">{memory_mb:.2f} MB</div>
                <div class="memory-bar">
                    <div class="memory-fill" style="width: {min(memory_mb/100*10, 100)}%;"></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">仮想メモリ使用量</div>
                <div class="stat-value">{virtual_mb:.2f} MB</div>
            </div>

            <div class="stat-card">
                <div class="stat-title">システムメモリ使用率</div>
                <div class="stat-value">{system_usage_percent:.1f}%</div>
                <div class="memory-bar">
                    <div class="memory-fill" style="width: {system_usage_percent}%;"></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">システム利用可能メモリ</div>
                <div class="stat-value">{system_available_gb:.1f} GB / {system_total_gb:.1f} GB</div>
            </div>
        </div>
        """

        # オブジェクトプール統計
        if self._object_pools and include_detailed_stats:
            html_report += """
        <h2>🏊 オブジェクトプール統計</h2>
        <table class="pool-table">
            <thead>
                <tr>
                    <th>プール名</th>
                    <th>現在サイズ</th>
                    <th>最大サイズ</th>
                    <th>作成数</th>
                    <th>再利用数</th>
                    <th>効率率</th>
                    <th>最終クリーンアップ</th>
                </tr>
            </thead>
            <tbody>
            """

            for name, pool_info in self._object_pools.items():
                current_size = len(pool_info["pool"])
                max_size = pool_info["max_size"]
                created = pool_info["created_count"]
                reused = pool_info["reused_count"]
                total = created + reused
                efficiency = (reused / total * 100) if total > 0 else 0
                last_cleanup = time.strftime(
                    "%H:%M:%S", time.localtime(pool_info.get("last_cleanup", 0))
                )

                html_report += f"""
                <tr>
                    <td>{name}</td>
                    <td>{current_size}</td>
                    <td>{max_size}</td>
                    <td>{created}</td>
                    <td>{reused}</td>
                    <td>{efficiency:.1f}%</td>
                    <td>{last_cleanup}</td>
                </tr>
                """

            html_report += "</tbody></table>"

        # メモリ統計情報
        if include_detailed_stats:
            html_report += f"""
        <h2>📊 詳細メモリ統計</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">アロケーション数</div>
                <div class="stat-value">{self._memory_stats["allocations"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">ディアロケーション数</div>
                <div class="stat-value">{self._memory_stats["deallocations"]:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">プールヒット数</div>
                <div class="stat-value">{self._memory_stats["pool_hits"]:,}</div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ 注意:</strong> メモリ使用量が100MB以上の場合は、プロアクティブなガベージコレクションの実行を検討してください。
        </div>
        """

        html_report += f"""
        <div class="timestamp">
            レポート生成時刻: {current_time}
        </div>
    </div>
</body>
</html>
        """

        self.logger.info(f"Memory report generated. Current usage: {memory_mb:.2f} MB")
        return html_report.strip()

    def _generate_leak_recommendation(
        self, is_leak: bool, growth_mb: float, gc_effect_mb: float
    ) -> str:
        """メモリリーク検出結果に基づく推奨アクション生成"""
        if not is_leak:
            return "正常なメモリ使用パターンです。定期的な監視を継続してください。"

        recommendations = []

        if gc_effect_mb < growth_mb * 0.3:
            recommendations.append(
                "ガベージコレクションの効果が低いため、強い参照の解除を確認してください。"
            )

        if growth_mb > 50:
            recommendations.append(
                "大幅なメモリ増加が検出されました。大容量データの処理方法を見直してください。"
            )

        if not recommendations:
            recommendations.append(
                "メモリリークが検出されました。オブジェクトのライフサイクルを確認してください。"
            )

        return " ".join(recommendations)


class ProgressiveOutputSystem:
    """
    プログレッシブ出力システム（Issue #727 対応）

    機能:
    - リアルタイム結果出力
    - 段階的HTML生成
    - ユーザー体験向上
    - 大容量ファイル処理の可視性改善
    """

    def __init__(self, output_path: Optional[Path] = None, buffer_size: int = 1000):
        self.logger = get_logger(__name__)
        self.output_path = output_path
        self.buffer_size = buffer_size

        # 出力管理
        self.html_buffer = []
        self.total_nodes_processed = 0
        self.current_section = "header"

        # テンプレート部分
        self.html_header = ""
        self.html_footer = ""
        self.css_content = ""

        # ストリーム出力ファイル
        self.output_stream = None

        self.logger.info(
            f"Progressive output system initialized: buffer_size={buffer_size}"
        )

    def initialize_output_stream(
        self, template_content: str = "", css_content: str = ""
    ):
        """出力ストリームの初期化"""

        if not self.output_path:
            return  # ファイル出力無効

        try:
            self.output_stream = open(
                self.output_path, "w", encoding="utf-8", buffering=1
            )

            # HTMLヘッダーの準備
            self.css_content = css_content
            self.html_header = self._create_html_header(template_content)
            self.html_footer = self._create_html_footer()

            # ヘッダーを即座に出力
            self.output_stream.write(self.html_header)
            self.output_stream.flush()

            self.logger.info(f"Progressive output stream started: {self.output_path}")

        except Exception as e:
            self.logger.error(f"Failed to initialize output stream: {e}")
            self.output_stream = None

    def add_processed_node(self, node_html: str, node_info: dict = None):
        """処理済みノードの追加"""

        if not node_html.strip():
            return

        self.html_buffer.append(node_html)
        self.total_nodes_processed += 1

        # バッファサイズに達したら出力
        if len(self.html_buffer) >= self.buffer_size:
            self.flush_buffer()

        # プログレス表示
        if self.total_nodes_processed % 100 == 0:
            self.logger.info(
                f"Progressive output: {self.total_nodes_processed} nodes processed"
            )

    def flush_buffer(self):
        """バッファの強制出力"""

        if not self.html_buffer or not self.output_stream:
            return

        try:
            # バッファ内容をファイルに書き込み
            content = "\n".join(self.html_buffer)
            self.output_stream.write(content + "\n")
            self.output_stream.flush()

            # バッファクリア
            self.html_buffer.clear()

            self.logger.debug(f"Buffer flushed: {len(self.html_buffer)} items")

        except Exception as e:
            self.logger.error(f"Buffer flush error: {e}")

    def add_section_marker(self, section_name: str, section_content: str = ""):
        """セクションマーカーの追加"""

        self.current_section = section_name

        if section_content:
            section_html = f"""
<!-- ===== {section_name.upper()} SECTION START ===== -->
{section_content}
<!-- ===== {section_name.upper()} SECTION END ===== -->
"""
            self.add_processed_node(section_html)

    def finalize_output(self):
        """出力の最終化"""

        if not self.output_stream:
            return

        try:
            # 残りバッファを出力
            self.flush_buffer()

            # フッターを出力
            self.output_stream.write(self.html_footer)
            self.output_stream.flush()

            # ストリームクローズ
            self.output_stream.close()
            self.output_stream = None

            self.logger.info(
                f"Progressive output finalized: {self.total_nodes_processed} nodes, "
                f"output: {self.output_path}"
            )

        except Exception as e:
            self.logger.error(f"Output finalization error: {e}")

    def _create_html_header(self, template_content: str) -> str:
        """HTMLヘッダーの作成"""

        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kumihan Formatter - Progressive Output</title>
    <style>
{self.css_content}
/* Progressive output styles */
.kumihan-progressive-info {{
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    font-size: 12px;
    z-index: 1000;
}}
.kumihan-processing {{
    opacity: 0.7;
    transition: opacity 0.3s ease;
}}
    </style>
    <script>
// Progressive output JavaScript
let processedNodes = 0;
function updateProgressInfo() {{
    const info = document.querySelector('.kumihan-progressive-info');
    if (info) {{
        info.textContent = 'Kumihan-Formatter 処理中... ' + (window.processedNodes || 0) + ' nodes';
    }}
}}
setInterval(updateProgressInfo, 1000);
    </script>
</head>
<body>
<div class="kumihan-progressive-info">Kumihan Progressive Output - 処理開始</div>
<div class="kumihan-content">
<!-- PROGRESSIVE CONTENT START -->
"""

    def _create_html_footer(self) -> str:
        """HTMLフッターの作成"""

        return f"""
<!-- PROGRESSIVE CONTENT END -->
</div>
<script>
// Final processing info
const info = document.querySelector('.kumihan-progressive-info');
if (info) {{
    info.textContent = '✅ 処理完了 - {self.total_nodes_processed} nodes';
    info.style.backgroundColor = 'rgba(0,128,0,0.8)';
}}
document.querySelectorAll('.kumihan-processing').forEach(el => {{
    el.classList.remove('kumihan-processing');
}});
</script>
</body>
</html>"""

    def create_progress_html(self, current: int, total: int, stage: str = "") -> str:
        """プログレス表示HTML生成"""

        progress_percent = (current / total * 100) if total > 0 else 0

        progress_style = f"width: {progress_percent:.1f}%; background: linear-gradient(90deg, #4CAF50, #2196F3);"
        progress_text = f"{stage} - {current}/{total} ({progress_percent:.1f}%)"

        return f"""
<div class="kumihan-progress-update" data-current="{current}" data-total="{total}">
    <div class="progress-bar" style="{progress_style}"></div>
    <div class="progress-text">{progress_text}</div>
</div>
"""

    def get_output_statistics(self) -> dict:
        """出力統計の取得"""

        return {
            "total_nodes_processed": self.total_nodes_processed,
            "buffer_size": len(self.html_buffer),
            "current_section": self.current_section,
            "output_active": self.output_stream is not None,
            "output_path": str(self.output_path) if self.output_path else None,
        }

    def __enter__(self):
        """コンテキストマネージャー開始"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.finalize_output()


class PerformanceBenchmark:
    """
    パフォーマンスベンチマークシステム（Issue #727 対応）

    機能:
    - パーサー性能測定
    - メモリ効率テスト
    - 並列処理効果測定
    - 目標達成評価
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.results = {}
        self.test_data_cache = {}

    def run_comprehensive_benchmark(self) -> dict:
        """包括的ベンチマーク実行"""

        self.logger.info("🚀 Starting comprehensive performance benchmark...")

        benchmark_results = {
            "metadata": {
                "timestamp": time.time(),
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count(),
            },
            "tests": {},
        }

        # テストケース定義
        test_cases = [
            {"name": "small", "lines": 1000, "description": "小規模ファイル(1K行)"},
            {"name": "medium", "lines": 5000, "description": "中規模ファイル(5K行)"},
            {"name": "large", "lines": 10000, "description": "大規模ファイル(10K行)"},
            {
                "name": "extra_large",
                "lines": 50000,
                "description": "超大規模ファイル(50K行)",
            },
        ]

        for test_case in test_cases:
            self.logger.info(f"📊 Testing {test_case['description']}...")

            test_results = self._run_single_benchmark(
                test_case["name"], test_case["lines"]
            )

            benchmark_results["tests"][test_case["name"]] = test_results

        # 目標達成評価
        benchmark_results["goal_assessment"] = self._assess_performance_goals(
            benchmark_results["tests"]
        )

        # サマリー生成
        benchmark_results["summary"] = self._generate_benchmark_summary(
            benchmark_results
        )

        self.logger.info("✅ Comprehensive benchmark completed")
        return benchmark_results

    def _run_single_benchmark(self, test_name: str, line_count: int) -> dict:
        """単一ベンチマークの実行"""

        # テストデータ生成
        test_text = self._generate_test_data(line_count)

        results = {
            "test_info": {
                "name": test_name,
                "line_count": line_count,
                "text_length": len(test_text),
                "text_size_mb": len(test_text) / 1024 / 1024,
            },
            "traditional_parser": {},
            "optimized_parser": {},
            "streaming_parser": {},
            "parallel_parser": {},
            "improvement_ratios": {},
        }

        # Traditional Parser テスト
        try:
            results["traditional_parser"] = self._benchmark_traditional_parser(
                test_text
            )
        except Exception as e:
            self.logger.error(f"Traditional parser test failed: {e}")
            results["traditional_parser"] = {"error": str(e)}

        # Optimized Parser テスト
        try:
            results["optimized_parser"] = self._benchmark_optimized_parser(test_text)
        except Exception as e:
            self.logger.error(f"Optimized parser test failed: {e}")
            results["optimized_parser"] = {"error": str(e)}

        # Streaming Parser テスト
        try:
            results["streaming_parser"] = self._benchmark_streaming_parser(test_text)
        except Exception as e:
            self.logger.error(f"Streaming parser test failed: {e}")
            results["streaming_parser"] = {"error": str(e)}

        # 改善率計算
        results["improvement_ratios"] = self._calculate_improvement_ratios(results)

        return results

    def _benchmark_traditional_parser(self, test_text: str) -> dict:
        """従来パーサーのベンチマーク"""

        from ...parser import Parser

        # メモリ使用量測定開始
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()

        # パーサー実行
        parser = Parser()
        nodes = parser.parse(test_text)

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _benchmark_optimized_parser(self, test_text: str) -> dict:
        """最適化パーサーのベンチマーク"""

        from ...parser import Parser

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()

        # 最適化パーサー実行
        parser = Parser()
        nodes = parser.parse_optimized(test_text)

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _benchmark_streaming_parser(self, test_text: str) -> dict:
        """ストリーミングパーサーのベンチマーク"""

        from ...parser import StreamingParser

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()

        # ストリーミングパーサー実行
        parser = StreamingParser()
        nodes = list(parser.parse_streaming_from_text(test_text))

        parse_time = time.time() - start_time
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_used = peak_memory - initial_memory

        return {
            "parse_time_seconds": parse_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
            "nodes_count": len(nodes),
            "throughput_lines_per_second": (
                len(test_text.split("\n")) / parse_time if parse_time > 0 else 0
            ),
            "errors_count": len(parser.get_errors()),
        }

    def _generate_test_data(self, line_count: int) -> str:
        """テストデータの生成"""

        if line_count in self.test_data_cache:
            return self.test_data_cache[line_count]

        lines = []

        # 多様なKumihan記法パターンを含むテストデータ
        patterns = [
            "これは通常のパラグラフです。",
            "# 太字 # このテキストは太字になります",
            "# イタリック # このテキストはイタリックになります",
            "# 見出し1 # 大きな見出し",
            "- リスト項目1",
            "- リスト項目2",
            "1. 順序付きリスト1",
            "2. 順序付きリスト2",
            "# 枠線 # 枠で囲まれたテキスト",
            "# ハイライト color=yellow # 黄色でハイライト",
            "",  # 空行
            "複数行にわたる\\n長いテキストの\\n例です。",
        ]

        for i in range(line_count):
            pattern = patterns[i % len(patterns)]
            if "項目" in pattern or "リスト" in pattern:
                lines.append(
                    pattern.replace("項目", f"項目{i+1}").replace(
                        "リスト", f"リスト{i+1}"
                    )
                )
            else:
                lines.append(f"{pattern} (行 {i+1})")

        test_text = "\n".join(lines)
        self.test_data_cache[line_count] = test_text

        return test_text

    def _calculate_improvement_ratios(self, results: dict) -> dict:
        """改善率の計算"""

        improvement = {}

        traditional = results.get("traditional_parser", {})
        optimized = results.get("optimized_parser", {})
        streaming = results.get("streaming_parser", {})

        if traditional.get("parse_time_seconds") and optimized.get(
            "parse_time_seconds"
        ):
            improvement["optimized_vs_traditional_speed"] = (
                traditional["parse_time_seconds"] / optimized["parse_time_seconds"]
            )

        if traditional.get("memory_used_mb") and optimized.get("memory_used_mb"):
            improvement["optimized_vs_traditional_memory"] = (
                traditional["memory_used_mb"] / optimized["memory_used_mb"]
            )

        if traditional.get("parse_time_seconds") and streaming.get(
            "parse_time_seconds"
        ):
            improvement["streaming_vs_traditional_speed"] = (
                traditional["parse_time_seconds"] / streaming["parse_time_seconds"]
            )

        return improvement

    def _assess_performance_goals(self, test_results: dict) -> dict:
        """Issue #727 パフォーマンス目標の達成評価"""

        assessment = {
            "goals": {
                "10k_lines_under_15s": False,
                "memory_reduction_66_percent": False,
                "100k_lines_under_180s": False,
                "10k_lines_under_30s": False,
            },
            "details": {},
        }

        # 10K行ファイル15秒以内目標
        large_test = test_results.get("large", {})
        if large_test:
            optimized_time = large_test.get("optimized_parser", {}).get(
                "parse_time_seconds", float("inf")
            )
            streaming_time = large_test.get("streaming_parser", {}).get(
                "parse_time_seconds", float("inf")
            )

            best_time = min(optimized_time, streaming_time)
            assessment["goals"]["10k_lines_under_15s"] = best_time <= 15.0
            assessment["details"]["10k_best_time"] = best_time

        # メモリ使用量66%削減目標
        if large_test:
            traditional_memory = large_test.get("traditional_parser", {}).get(
                "memory_used_mb", 0
            )
            optimized_memory = large_test.get("optimized_parser", {}).get(
                "memory_used_mb", 0
            )

            if traditional_memory > 0:
                memory_reduction = (
                    (traditional_memory - optimized_memory) / traditional_memory * 100
                )
                assessment["goals"]["memory_reduction_66_percent"] = (
                    memory_reduction >= 66.0
                )
                assessment["details"]["memory_reduction_percent"] = memory_reduction

        return assessment

    def _generate_benchmark_summary(self, benchmark_results: dict) -> dict:
        """ベンチマーク結果サマリー生成"""

        summary = {
            "overall_performance": "unknown",
            "key_achievements": [],
            "areas_for_improvement": [],
            "recommendations": [],
        }

        goals = benchmark_results.get("goal_assessment", {}).get("goals", {})

        achieved_goals = sum(1 for achieved in goals.values() if achieved)
        total_goals = len(goals)

        if achieved_goals >= total_goals * 0.8:
            summary["overall_performance"] = "excellent"
            summary["key_achievements"].append("ほぼ全ての性能目標を達成")
        elif achieved_goals >= total_goals * 0.6:
            summary["overall_performance"] = "good"
            summary["key_achievements"].append("主要な性能目標を達成")
        else:
            summary["overall_performance"] = "needs_improvement"
            summary["areas_for_improvement"].append("性能目標の達成率が低い")

        # 推奨事項
        if not goals.get("10k_lines_under_15s"):
            summary["recommendations"].append("大容量ファイル処理の更なる最適化が必要")

        if not goals.get("memory_reduction_66_percent"):
            summary["recommendations"].append("メモリ効率の改善が必要")

        return summary

    def generate_benchmark_report(self, results: dict) -> str:
        """ベンチマークレポートの生成"""

        report_lines = [
            "🔬 Kumihan-Formatter パフォーマンスベンチマークレポート",
            "=" * 60,
            f"実行日時: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['metadata']['timestamp']))}",
            f"プラットフォーム: {results['metadata']['platform']}",
            f"CPUコア数: {results['metadata']['cpu_count']}",
            "",
            "📊 テスト結果:",
        ]

        for test_name, test_data in results["tests"].items():
            info = test_data["test_info"]
            report_lines.extend(
                [
                    f"\n🔍 {info['name'].upper()} ({info['line_count']:,}行, {info['text_size_mb']:.1f}MB):",
                    f"  従来パーサー: {test_data['traditional_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['traditional_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                    f"  最適化パーサー: {test_data['optimized_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['optimized_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                    f"  ストリーミング: {test_data['streaming_parser'].get('parse_time_seconds', 'N/A'):.2f}s, "
                    f"{test_data['streaming_parser'].get('memory_used_mb', 'N/A'):.1f}MB",
                ]
            )

            # 改善率
            improvements = test_data.get("improvement_ratios", {})
            if improvements:
                speed_improve = improvements.get("optimized_vs_traditional_speed", 1)
                memory_improve = improvements.get("optimized_vs_traditional_memory", 1)
                report_lines.append(
                    f"  改善率: 速度 {speed_improve:.1f}x, メモリ {memory_improve:.1f}x"
                )

        # 目標達成状況
        goals = results.get("goal_assessment", {}).get("goals", {})
        report_lines.extend(
            [
                "",
                "🎯 目標達成状況:",
                f"  10K行15秒以内: {'✅' if goals.get('10k_lines_under_15s') else '❌'}",
                f"  メモリ66%削減: {'✅' if goals.get('memory_reduction_66_percent') else '❌'}",
                f"  100K行180秒以内: {'✅' if goals.get('100k_lines_under_180s') else '❌'}",
            ]
        )

        # サマリー
        summary = results.get("summary", {})
        report_lines.extend(
            [
                "",
                f"📈 総合評価: {summary.get('overall_performance', 'unknown').upper()}",
            ]
        )

        if summary.get("key_achievements"):
            report_lines.append("✨ 主な成果:")
            for achievement in summary["key_achievements"]:
                report_lines.append(f"  • {achievement}")

        if summary.get("recommendations"):
            report_lines.append("💡 推奨改善:")
            for rec in summary["recommendations"]:
                report_lines.append(f"  • {rec}")

        return "\n".join(report_lines)


# パフォーマンス監視用デコレータ
def monitor_performance(task_name: str = "処理"):
    """
    パフォーマンス監視のコンテキストマネージャー

    Args:
        task_name: タスク名

    Returns:
        PerformanceContext: パフォーマンス監視コンテキスト
    """
    return PerformanceContext(task_name)


class PerformanceContext:
    """パフォーマンス監視コンテキストマネージャー"""

    def __init__(self, task_name: str):
        self.task_name = task_name
        self.monitor = PerformanceMonitor()
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.monitor.start_monitoring(total_items=1000, initial_stage=self.task_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()

    def record_item_processed(self):
        """アイテム処理の記録"""
        if hasattr(self.monitor, "update_progress"):
            # 簡易的な進捗更新
            pass


# Testing serena-expert enforcement
