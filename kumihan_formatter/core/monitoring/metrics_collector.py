"""
システムメトリクス収集モジュール

システムメトリクス・アプリケーションメトリクス・カスタムメトリクスの
包括的収集・アグリゲーション・永続化システム
"""

import json
import platform
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Callable, Dict, List, Optional, Union, cast

import psutil

from kumihan_formatter.core.utilities.logger import get_logger


@dataclass
class MetricData:
    """メトリクスデータクラス"""

    name: str
    value: Union[float, int]
    unit: str
    timestamp: float
    labels: Dict[str, str]
    metadata: Dict[str, Any]


@dataclass
class AggregatedMetric:
    """アグリゲート済みメトリクスデータ"""

    name: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    sum_value: float
    std_dev: Optional[float]
    percentiles: Dict[str, float]
    first_timestamp: float
    last_timestamp: float
    labels: Dict[str, str]


class MetricsBuffer:
    """スレッドセーフメトリクスバッファ"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer: deque[MetricData] = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add(self, metric: MetricData) -> None:
        """メトリクス追加"""
        with self.lock:
            self.buffer.append(metric)

    def drain(self) -> List[MetricData]:
        """バッファからメトリクス取得・クリア"""
        with self.lock:
            metrics = list(self.buffer)
            self.buffer.clear()
            return metrics

    def size(self) -> int:
        """バッファサイズ取得"""
        with self.lock:
            return len(self.buffer)


class MetricsCollector:
    """システムメトリクス収集システム

    システムメトリクス・アプリケーションメトリクス・カスタムメトリクスの
    収集・アグリゲーション・永続化を管理する
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        collection_interval: float = 10.0,
        buffer_size: int = 10000,
        enable_auto_collection: bool = False,
    ):
        """メトリクス収集システム初期化

        Args:
            output_dir: メトリクス出力ディレクトリ
            collection_interval: 自動収集間隔（秒）
            buffer_size: メトリクスバッファサイズ
            enable_auto_collection: 自動収集有効化
        """
        self.logger = get_logger(__name__)
        self.output_dir = output_dir or Path("tmp")
        self.collection_interval = collection_interval
        self.enable_auto_collection = enable_auto_collection

        # バッファとストレージ
        self.buffer = MetricsBuffer(buffer_size)
        self.metrics_storage: Dict[str, List[MetricData]] = defaultdict(list)
        self.custom_collectors: Dict[str, Callable[[], Dict[str, Any]]] = {}

        # スレッド制御
        self.collection_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metrics")
        self.shutdown_event = threading.Event()
        self.storage_lock = threading.Lock()

        # メトリクス設定
        self.retention_hours = 24
        self.max_metrics_per_name = 1000

        # 出力ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 自動収集開始
        if self.enable_auto_collection:
            self.start_auto_collection()

        self.logger.info(f"MetricsCollector初期化完了 - 出力先: {self.output_dir}")

    def start_auto_collection(self) -> None:
        """自動メトリクス収集開始"""
        if self.collection_thread and self.collection_thread.is_alive():
            return

        self.shutdown_event.clear()
        self.collection_thread = threading.Thread(
            target=self._auto_collection_loop, name="MetricsAutoCollector", daemon=True
        )
        self.collection_thread.start()
        self.logger.info(f"自動メトリクス収集開始 - 間隔: {self.collection_interval}秒")

    def stop_auto_collection(self) -> None:
        """自動メトリクス収集停止"""
        self.shutdown_event.set()
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5.0)
        self.logger.info("自動メトリクス収集停止")

    def _auto_collection_loop(self) -> None:
        """自動収集ループ"""
        while not self.shutdown_event.is_set():
            try:
                # システムメトリクス収集
                self.collect_system_metrics()

                # アプリケーションメトリクス収集
                self.collect_application_metrics()

                # カスタムメトリクス収集
                self.collect_custom_metrics()

                # 待機（中断可能）
                if self.shutdown_event.wait(self.collection_interval):
                    break

            except Exception as e:
                self.logger.error(f"自動メトリクス収集エラー: {e}")
                # エラー時は短縮間隔で継続
                if self.shutdown_event.wait(5.0):
                    break

    def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集

        Returns:
            収集したシステムメトリクス
        """
        try:
            timestamp = time.time()
            metrics: Dict[str, Any] = {}

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1.0)
            self._add_metric(
                "system.cpu.usage_percent", cpu_percent, "percent", timestamp
            )
            metrics["cpu_usage_percent"] = cpu_percent

            # CPU詳細情報
            cpu_times = psutil.cpu_times()
            self._add_metric(
                "system.cpu.user_time", cpu_times.user, "seconds", timestamp
            )
            self._add_metric(
                "system.cpu.system_time", cpu_times.system, "seconds", timestamp
            )
            self._add_metric(
                "system.cpu.idle_time", cpu_times.idle, "seconds", timestamp
            )

            # メモリ使用量
            memory = psutil.virtual_memory()
            self._add_metric("system.memory.total", memory.total, "bytes", timestamp)
            self._add_metric(
                "system.memory.available", memory.available, "bytes", timestamp
            )
            self._add_metric("system.memory.used", memory.used, "bytes", timestamp)
            self._add_metric(
                "system.memory.usage_percent", memory.percent, "percent", timestamp
            )
            metrics["memory_usage_percent"] = memory.percent
            metrics["memory_available_mb"] = memory.available / 1024 / 1024

            # スワップメモリ
            swap = psutil.swap_memory()
            self._add_metric("system.swap.total", swap.total, "bytes", timestamp)
            self._add_metric("system.swap.used", swap.used, "bytes", timestamp)
            self._add_metric(
                "system.swap.usage_percent", swap.percent, "percent", timestamp
            )

            # ディスクI/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._add_metric(
                    "system.disk.read_bytes", disk_io.read_bytes, "bytes", timestamp
                )
                self._add_metric(
                    "system.disk.write_bytes", disk_io.write_bytes, "bytes", timestamp
                )
                self._add_metric(
                    "system.disk.read_count",
                    disk_io.read_count,
                    "operations",
                    timestamp,
                )
                self._add_metric(
                    "system.disk.write_count",
                    disk_io.write_count,
                    "operations",
                    timestamp,
                )
                metrics["disk_read_mb"] = disk_io.read_bytes / 1024 / 1024
                metrics["disk_write_mb"] = disk_io.write_bytes / 1024 / 1024

            # ディスク使用量
            disk_usage = psutil.disk_usage("/")
            self._add_metric("system.disk.total", disk_usage.total, "bytes", timestamp)
            self._add_metric("system.disk.used", disk_usage.used, "bytes", timestamp)
            self._add_metric("system.disk.free", disk_usage.free, "bytes", timestamp)
            self._add_metric(
                "system.disk.usage_percent", disk_usage.percent, "percent", timestamp
            )
            metrics["disk_usage_percent"] = disk_usage.percent

            # ネットワーク統計
            net_io = psutil.net_io_counters()
            if net_io:
                self._add_metric(
                    "system.network.bytes_sent", net_io.bytes_sent, "bytes", timestamp
                )
                self._add_metric(
                    "system.network.bytes_recv", net_io.bytes_recv, "bytes", timestamp
                )
                self._add_metric(
                    "system.network.packets_sent",
                    net_io.packets_sent,
                    "packets",
                    timestamp,
                )
                self._add_metric(
                    "system.network.packets_recv",
                    net_io.packets_recv,
                    "packets",
                    timestamp,
                )
                metrics["network_sent_mb"] = net_io.bytes_sent / 1024 / 1024
                metrics["network_recv_mb"] = net_io.bytes_recv / 1024 / 1024

            # システム情報
            metrics["platform"] = str(platform.system())
            metrics["architecture"] = str(platform.machine())
            metrics["python_version"] = str(platform.python_version())
            metrics["boot_time"] = float(psutil.boot_time())

            self.logger.debug("システムメトリクス収集完了")
            return metrics

        except Exception as e:
            self.logger.error(f"システムメトリクス収集エラー: {e}")
            return {"error": str(e)}

    def collect_application_metrics(self) -> Dict[str, Any]:
        """アプリケーションメトリクス収集

        Returns:
            収集したアプリケーションメトリクス
        """
        try:
            timestamp = time.time()
            metrics: Dict[str, Any] = {}

            # 現在のプロセス情報
            process = psutil.Process()

            # プロセスメモリ使用量
            memory_info = process.memory_info()
            self._add_metric("app.memory.rss", memory_info.rss, "bytes", timestamp)
            self._add_metric("app.memory.vms", memory_info.vms, "bytes", timestamp)
            metrics["app_memory_rss_mb"] = memory_info.rss / 1024 / 1024
            metrics["app_memory_vms_mb"] = memory_info.vms / 1024 / 1024

            # プロセスCPU使用率
            cpu_percent = process.cpu_percent()
            self._add_metric("app.cpu.usage_percent", cpu_percent, "percent", timestamp)
            metrics["app_cpu_usage_percent"] = cpu_percent

            # プロセス統計
            self._add_metric("app.process.pid", process.pid, "id", timestamp)
            self._add_metric(
                "app.process.threads", process.num_threads(), "count", timestamp
            )

            try:
                open_files = len(process.open_files())
                self._add_metric(
                    "app.process.open_files", open_files, "count", timestamp
                )
                metrics["app_open_files"] = open_files
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # アプリケーション実行時間
            create_time = process.create_time()
            uptime = timestamp - create_time
            self._add_metric("app.uptime", uptime, "seconds", timestamp)
            metrics["app_uptime_hours"] = uptime / 3600

            # Python GC統計
            import gc

            gc_stats = gc.get_stats()
            for i, stat in enumerate(gc_stats):
                self._add_metric(
                    f"app.gc.generation_{i}.collections",
                    stat["collections"],
                    "count",
                    timestamp,
                )
                self._add_metric(
                    f"app.gc.generation_{i}.collected",
                    stat["collected"],
                    "count",
                    timestamp,
                )
                self._add_metric(
                    f"app.gc.generation_{i}.uncollectable",
                    stat["uncollectable"],
                    "count",
                    timestamp,
                )

            # スレッド数
            active_threads = threading.active_count()
            self._add_metric("app.threads.active", active_threads, "count", timestamp)
            metrics["active_threads"] = active_threads

            self.logger.debug("アプリケーションメトリクス収集完了")
            return metrics

        except Exception as e:
            self.logger.error(f"アプリケーションメトリクス収集エラー: {e}")
            return {"error": str(e)}

    def collect_custom_metrics(self) -> Dict[str, Any]:
        """カスタムメトリクス収集

        Returns:
            収集したカスタムメトリクス
        """
        try:
            timestamp = time.time()
            all_metrics: Dict[str, Any] = {}

            for name, collector in self.custom_collectors.items():
                try:
                    metrics = collector()
                    if isinstance(metrics, dict):
                        for key, value in metrics.items():
                            if isinstance(value, (int, float)):
                                metric_name = f"custom.{name}.{key}"
                                self._add_metric(
                                    metric_name, value, "custom", timestamp
                                )
                                all_metrics[f"{name}_{key}"] = value

                except Exception as e:
                    self.logger.error(f"カスタムメトリクス収集エラー ({name}): {e}")

            self.logger.debug(
                f"カスタムメトリクス収集完了 - {len(all_metrics)}個のメトリクス"
            )
            return all_metrics

        except Exception as e:
            self.logger.error(f"カスタムメトリクス収集エラー: {e}")
            return {"error": str(e)}

    def register_custom_collector(
        self, name: str, collector: Callable[[], Dict[str, Any]]
    ) -> None:
        """カスタムメトリクスコレクター登録

        Args:
            name: コレクター名
            collector: メトリクス収集関数
        """
        self.custom_collectors[name] = collector
        self.logger.info(f"カスタムメトリクスコレクター登録: {name}")

    def unregister_custom_collector(self, name: str) -> None:
        """カスタムメトリクスコレクター登録解除

        Args:
            name: コレクター名
        """
        if name in self.custom_collectors:
            del self.custom_collectors[name]
            self.logger.info(f"カスタムメトリクスコレクター登録解除: {name}")

    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        unit: str = "count",
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """手動メトリクス記録

        Args:
            name: メトリクス名
            value: メトリクス値
            unit: 単位
            labels: メトリクスラベル
        """
        timestamp = time.time()
        self._add_metric(name, value, unit, timestamp, labels or {})

    def _add_metric(
        self,
        name: str,
        value: Union[float, int],
        unit: str,
        timestamp: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """メトリクス追加（内部）"""
        metric = MetricData(
            name=name,
            value=float(value),
            unit=unit,
            timestamp=timestamp,
            labels=labels or {},
            metadata={},
        )

        # バッファに追加
        self.buffer.add(metric)

        # ストレージに追加
        with self.storage_lock:
            self.metrics_storage[name].append(metric)
            # 保存数制限
            if len(self.metrics_storage[name]) > self.max_metrics_per_name:
                self.metrics_storage[name] = self.metrics_storage[name][
                    -self.max_metrics_per_name :
                ]

    def aggregate_metrics(
        self, metric_name: str, time_range_hours: Optional[float] = None
    ) -> Optional[AggregatedMetric]:
        """メトリクスアグリゲーション

        Args:
            metric_name: アグリゲート対象メトリクス名
            time_range_hours: 時間範囲（時間）

        Returns:
            アグリゲート済みメトリクス
        """
        try:
            with self.storage_lock:
                if metric_name not in self.metrics_storage:
                    return None

                metrics = self.metrics_storage[metric_name]

                # 時間範囲フィルタ
                if time_range_hours is not None:
                    cutoff_time = time.time() - (time_range_hours * 3600)
                    metrics = [m for m in metrics if m.timestamp >= cutoff_time]

                if not metrics:
                    return None

                values = [m.value for m in metrics]
                count = len(values)

                return AggregatedMetric(
                    name=metric_name,
                    count=count,
                    min_value=min(values),
                    max_value=max(values),
                    mean_value=mean(values),
                    sum_value=sum(values),
                    std_dev=stdev(values) if count > 1 else None,
                    percentiles=self._calculate_percentiles(values),
                    first_timestamp=metrics[0].timestamp,
                    last_timestamp=metrics[-1].timestamp,
                    labels=metrics[-1].labels,  # 最新のラベルを使用
                )

        except Exception as e:
            self.logger.error(f"メトリクスアグリゲーションエラー ({metric_name}): {e}")
            return None

    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """パーセンタイル計算"""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        percentiles = {}
        for p in [50, 75, 90, 95, 99]:
            index = int((p / 100) * (n - 1))
            percentiles[f"p{p}"] = sorted_values[index]

        return percentiles

    def get_metrics_summary(self, time_range_hours: float = 1.0) -> Dict[str, Any]:
        """メトリクス概要取得

        Args:
            time_range_hours: 集計時間範囲（時間）

        Returns:
            メトリクス概要
        """
        try:
            cutoff_time = time.time() - (time_range_hours * 3600)
            summary = {
                "time_range_hours": time_range_hours,
                "timestamp": datetime.now().isoformat(),
                "metrics_count": 0,
                "unique_metrics": 0,
                "aggregated_metrics": {},
                "top_metrics": [],
            }

            with self.storage_lock:
                # 期間内のメトリクス数
                total_metrics = 0
                for name, metrics in self.metrics_storage.items():
                    recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
                    total_metrics += len(recent_metrics)

                summary["metrics_count"] = total_metrics
                summary["unique_metrics"] = len(self.metrics_storage)

                # 主要メトリクスのアグリゲーション
                key_metrics = [
                    "system.cpu.usage_percent",
                    "system.memory.usage_percent",
                    "system.disk.usage_percent",
                    "app.memory.rss",
                ]

                for metric_name in key_metrics:
                    agg = self.aggregate_metrics(metric_name, time_range_hours)
                    if agg:
                        aggregated_metrics = cast(Dict[str, Any], summary["aggregated_metrics"])
                        aggregated_metrics[metric_name] = asdict(agg)

                # トップメトリクス（データポイント数順）
                metric_counts = []
                for name, metrics in self.metrics_storage.items():
                    recent_count = len(
                        [m for m in metrics if m.timestamp >= cutoff_time]
                    )
                    if recent_count > 0:
                        metric_counts.append({"name": name, "count": recent_count})

                summary["top_metrics"] = sorted(
                    metric_counts, key=lambda x: cast(int, x["count"]), reverse=True
                )[:10]

            return summary

        except Exception as e:
            self.logger.error(f"メトリクス概要取得エラー: {e}")
            return {"error": str(e)}

    def export_metrics_json(
        self,
        output_file: Optional[Path] = None,
        time_range_hours: Optional[float] = None,
    ) -> Path:
        """メトリクスJSON出力

        Args:
            output_file: 出力ファイルパス
            time_range_hours: 出力時間範囲（時間）

        Returns:
            出力ファイルパス
        """
        try:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.output_dir / f"metrics_export_{timestamp}.json"

            export_data: Dict[str, Any] = {
                "export_timestamp": datetime.now().isoformat(),
                "time_range_hours": time_range_hours,
                "metrics": {},
            }

            cutoff_time = None
            if time_range_hours is not None:
                cutoff_time = time.time() - (time_range_hours * 3600)

            with self.storage_lock:
                for name, metrics in self.metrics_storage.items():
                    filtered_metrics = metrics
                    if cutoff_time is not None:
                        filtered_metrics = [
                            m for m in metrics if m.timestamp >= cutoff_time
                        ]

                    if filtered_metrics:
                        metrics_dict = cast(Dict[str, Any], export_data["metrics"])
                        metrics_dict[name] = [
                            asdict(m) for m in filtered_metrics
                        ]

            # JSON出力
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"メトリクスJSONエクスポート完了: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"メトリクスJSONエクスポートエラー: {e}")
            raise

    def cleanup_old_metrics(self) -> int:
        """古いメトリクスデータクリーンアップ

        Returns:
            削除されたメトリクス数
        """
        try:
            cutoff_time = time.time() - (self.retention_hours * 3600)
            deleted_count = 0

            with self.storage_lock:
                for name in list(self.metrics_storage.keys()):
                    original_count = len(self.metrics_storage[name])
                    self.metrics_storage[name] = [
                        m
                        for m in self.metrics_storage[name]
                        if m.timestamp >= cutoff_time
                    ]
                    deleted_count += original_count - len(self.metrics_storage[name])

                    # 空のメトリクスエントリ削除
                    if not self.metrics_storage[name]:
                        del self.metrics_storage[name]

            if deleted_count > 0:
                self.logger.info(
                    f"古いメトリクスクリーンアップ完了: {deleted_count}個削除"
                )

            return deleted_count

        except Exception as e:
            self.logger.error(f"メトリクスクリーンアップエラー: {e}")
            return 0

    def get_health_status(self) -> Dict[str, Any]:
        """メトリクス収集システムヘルス状態

        Returns:
            ヘルス状態情報
        """
        try:
            # current_time = time.time()  # Unused variable removed

            # バッファ状態
            buffer_size = self.buffer.size()
            buffer_usage = (buffer_size / self.buffer.max_size) * 100

            # ストレージ状態
            with self.storage_lock:
                total_metrics = sum(
                    len(metrics) for metrics in self.metrics_storage.values()
                )
                unique_names = len(self.metrics_storage)

            # 自動収集状態
            auto_collection_active = (
                self.collection_thread is not None
                and self.collection_thread.is_alive()
                and not self.shutdown_event.is_set()
            )

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "buffer": {
                    "size": buffer_size,
                    "max_size": self.buffer.max_size,
                    "usage_percent": round(buffer_usage, 2),
                },
                "storage": {
                    "total_metrics": total_metrics,
                    "unique_names": unique_names,
                    "retention_hours": self.retention_hours,
                },
                "collection": {
                    "auto_enabled": self.enable_auto_collection,
                    "auto_active": auto_collection_active,
                    "interval_seconds": self.collection_interval,
                    "custom_collectors": len(self.custom_collectors),
                },
                "output_dir": str(self.output_dir),
            }

        except Exception as e:
            self.logger.error(f"ヘルス状態取得エラー: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def shutdown(self) -> None:
        """メトリクス収集システム終了処理"""
        try:
            # 自動収集停止
            self.stop_auto_collection()

            # 最終エクスポート
            if self.metrics_storage:
                export_file = self.export_metrics_json()
                self.logger.info(f"終了時メトリクスエクスポート: {export_file}")

            # スレッドプール終了
            self.executor.shutdown(wait=True)

            self.logger.info("MetricsCollector終了処理完了")

        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")

    def __enter__(self) -> "MetricsCollector":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
