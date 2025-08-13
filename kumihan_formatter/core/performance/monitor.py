"""
パフォーマンス監視システム
Issue #813対応 - performance_metrics.pyから分離
"""

import json
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from ..utilities.logger import get_logger


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
        return (self.items_processed / self.total_items) * 100.0


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
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        self.logger.info(
            f"PerformanceMonitor initialized: interval={monitoring_interval}s, "
            f"history={history_size}"
        )

    def start_monitoring(self, total_items: int, initial_stage: str = "開始") -> None:
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
                f"Performance monitoring started: {total_items} items, "
                f"stage: {initial_stage}"
            )

    def stop_monitoring(self) -> None:
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

    def update_progress(self, items_processed: int, current_stage: str = "") -> None:
        """進捗を更新"""
        with self._lock:
            self.stats.items_processed = items_processed

            if current_stage and current_stage not in self.stats.processing_phases:
                self.stats.processing_phases.append(current_stage)

    def add_error(self) -> None:
        """エラーカウントを増加"""
        with self._lock:
            self.stats.errors_count += 1

    def add_warning(self) -> None:
        """警告カウントを増加"""
        with self._lock:
            self.stats.warnings_count += 1

    def add_alert_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
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
            disk_io_read_mb = 0.0
            disk_io_write_mb = 0.0
            if hasattr(self.process, "io_counters"):
                try:
                    io_counters = self.process.io_counters()
                    disk_io_read_mb = io_counters.read_bytes / 1024 / 1024
                    disk_io_write_mb = io_counters.write_bytes / 1024 / 1024
                except psutil.AccessDenied:
                    # AccessDenied is a specific psutil error, keep handling it
                    pass

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

    def _monitoring_loop(self) -> None:
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

    def _check_performance_alerts(self, snapshot: PerformanceSnapshot) -> None:
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
                    "message": (
                        f"高メモリ使用率: {snapshot.memory_percent:.1f}% "
                        f"({snapshot.memory_mb:.1f}MB)"
                    ),
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
                    callback(str(alert["type"]), alert)
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

        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        y = values

        # Calculate slope using least squares method
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x_squared = sum(x[i] ** 2 for i in range(n))

        denominator = n * sum_x_squared - sum_x**2
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def save_metrics_to_file(self, file_path: Optional[str] = None) -> None:
        """パフォーマンスメトリクスをファイルに保存"""
        # tmp/配下にファイルを作成
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        if not file_path:
            actual_path = (
                tmp_dir
                / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        else:
            # 既存パスがあってもtmp/配下に移動
            actual_path = tmp_dir / Path(file_path).name

        try:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "snapshots": [asdict(snapshot) for snapshot in self.snapshots],
                "stats": asdict(self.stats),
                "summary": self.get_performance_summary(),
            }

            with open(actual_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Performance metrics saved to {actual_path}")

        except Exception as e:
            self.logger.error(f"Failed to save metrics to file: {e}")


class PerformanceContext:
    """パフォーマンス監視コンテキストマネージャー"""

    def __init__(
        self, monitor: PerformanceMonitor, total_items: int, stage: str = "処理"
    ):
        self.monitor = monitor
        self.total_items = total_items
        self.stage = stage

    def __enter__(self) -> "PerformanceMonitor":
        self.monitor.start_monitoring(self.total_items, self.stage)
        return self.monitor

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        self.monitor.stop_monitoring()


def monitor_performance(
    arg: Union[str, Callable[..., Any]],
) -> Union[PerformanceContextManager, Callable[..., Any]]:
    """パフォーマンス監視デコレーター または コンテキストマネージャー生成"""

    # 文字列が渡された場合はコンテキストマネージャーを返す
    if isinstance(arg, str):
        monitor = PerformanceMonitor()
        return PerformanceContextManager(monitor, stage_name=arg)

    # 関数が渡された場合はデコレーターとして動作
    func = arg

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        monitor = PerformanceMonitor()
        monitor.start_monitoring(total_items=1, initial_stage=func.__name__)

        try:
            result = func(*args, **kwargs)
            monitor.update_progress(1)
            return result
        except Exception as e:
            monitor.logger.error(f"Performance monitoring failed: {e}")
            raise
        finally:
            monitor.stop_monitoring()

    return wrapper
