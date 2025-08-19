"""
Prometheusエクスポーターモジュール

Prometheus形式でのメトリクスエクスポート・HTTPエンドポイント・
メトリクスレジストリ・ラベル管理・パフォーマンス最適化を提供
"""

import json
import threading
import time
from collections import defaultdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional, Set, cast
from urllib.parse import parse_qs, urlparse

from kumihan_formatter.core.utilities.logger import get_logger

try:
    # Prometheus client imports
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )

    # from prometheus_client.core import CollectorRegistry as CoreCollectorRegistry
    # from prometheus_client.metrics import MetricWrapperBase

    PROMETHEUS_AVAILABLE = True
except ImportError as e:
    PROMETHEUS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class CustomCollector:
    """カスタムメトリクスコレクター"""

    def __init__(self, name: str, collect_func: Callable[[], Any]):
        self.name = name
        self.collect_func = collect_func

    def collect(self) -> List[Any]:
        """メトリクス収集実行"""
        try:
            result = self.collect_func()
            return result if isinstance(result, list) else []
        except Exception:
            return []


class PrometheusMetricsHandler(BaseHTTPRequestHandler):
    """Prometheusメトリクス配信HTTPハンドラ"""

    def __init__(
        self, exporter: "PrometheusExporter", *args: Any, **kwargs: Any
    ) -> None:
        self.exporter = exporter
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """GETリクエスト処理"""
        try:
            parsed_path = urlparse(self.path)

            if parsed_path.path == "/metrics":
                self._handle_metrics_request(parsed_path)
            elif parsed_path.path == "/health":
                self._handle_health_request()
            elif parsed_path.path == "/config":
                self._handle_config_request()
            else:
                self._handle_not_found()

        except Exception as e:
            self.exporter.logger.error(f"HTTPリクエスト処理エラー: {e}")
            self._send_error_response(500, f"Internal Server Error: {str(e)}")

    def _handle_metrics_request(self, parsed_path: Any) -> None:
        """メトリクスリクエスト処理"""
        try:
            # クエリパラメータ解析
            query_params = parse_qs(parsed_path.query)
            name_filter = query_params.get("name", [None])[0]

            # メトリクス生成
            metrics_data = self.exporter.generate_prometheus_metrics(name_filter)

            # レスポンス送信
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(metrics_data.encode("utf-8"))

        except Exception as e:
            self.exporter.logger.error(f"メトリクスリクエスト処理エラー: {e}")
            self._send_error_response(500, "メトリクス生成エラー")

    def _handle_health_request(self) -> None:
        """ヘルスチェックリクエスト処理"""
        try:
            health_data = self.exporter.get_exporter_health()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(health_data, indent=2).encode("utf-8"))

        except Exception as e:
            self.exporter.logger.error(f"ヘルスチェックエラー: {e}")
            self._send_error_response(500, "ヘルスチェックエラー")

    def _handle_config_request(self) -> None:
        """設定情報リクエスト処理"""
        try:
            config_data = self.exporter.get_configuration()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(config_data, indent=2).encode("utf-8"))

        except Exception as e:
            self.exporter.logger.error(f"設定情報取得エラー: {e}")
            self._send_error_response(500, "設定情報取得エラー")

    def _handle_not_found(self) -> None:
        """404エラー処理"""
        self._send_error_response(404, "Not Found")

    def _send_error_response(self, status_code: int, message: str) -> None:
        """エラーレスポンス送信"""
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """ログメッセージ（無効化）"""
        # HTTPサーバーのログを無効化（独自ロガーを使用）
        pass


class PrometheusExporter:
    """Prometheusエクスポーターシステム

    Prometheus形式でのメトリクスエクスポート・HTTPエンドポイント・
    メトリクスレジストリ・ラベル管理・パフォーマンス最適化を提供
    """

    def __init__(
        self,
        port: int = 8000,
        host: str = "0.0.0.0",
        prefix: str = "kumihan_formatter",
        enable_builtin_metrics: bool = True,
        registry: Optional[CollectorRegistry] = None,
    ):
        """Prometheusエクスポーター初期化

        Args:
            port: HTTPサーバーポート
            host: HTTPサーバーホスト
            prefix: メトリクス名プレフィックス
            enable_builtin_metrics: ビルトインメトリクス有効化
            registry: カスタムレジストリ
        """
        self.logger = get_logger(__name__)
        self.port = port
        self.host = host
        self.prefix = prefix
        self.enable_builtin_metrics = enable_builtin_metrics

        # Prometheus利用可能性確認
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning(f"Prometheusクライアント利用不可: {IMPORT_ERROR}")
            self.logger.info("pip install prometheus-client で利用可能になります")
            self.available = False
            return

        self.available = True

        # レジストリ設定
        self.registry = registry or REGISTRY

        # メトリクス管理
        self.metrics: Dict[str, Any] = {}
        self.custom_collectors: Dict[str, CustomCollector] = {}
        self.labels_cache: Dict[str, Set[str]] = defaultdict(set)

        # HTTPサーバー管理
        self.http_server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()

        # パフォーマンス統計
        self.request_count = 0
        self.last_request_time = 0.0
        self.total_response_time = 0.0

        # ビルトインメトリクス作成
        if self.enable_builtin_metrics:
            self._create_builtin_metrics()

        self.logger.info(f"PrometheusExporter初期化完了 - {host}:{port}")

    def _create_builtin_metrics(self) -> None:
        """ビルトインメトリクス作成"""
        try:
            # HTTPリクエストメトリクス
            self.metrics["http_requests_total"] = Counter(
                f"{self.prefix}_http_requests_total",
                "HTTPリクエスト総数",
                ["method", "endpoint", "status"],
                registry=self.registry,
            )

            self.metrics["http_request_duration_seconds"] = Histogram(
                f"{self.prefix}_http_request_duration_seconds",
                "HTTPリクエスト処理時間",
                ["method", "endpoint"],
                registry=self.registry,
            )

            # システムメトリクス
            self.metrics["system_cpu_usage"] = Gauge(
                f"{self.prefix}_system_cpu_usage_percent",
                "システムCPU使用率",
                registry=self.registry,
            )

            self.metrics["system_memory_usage"] = Gauge(
                f"{self.prefix}_system_memory_usage_percent",
                "システムメモリ使用率",
                registry=self.registry,
            )

            # アプリケーションメトリクス
            self.metrics["app_info"] = Info(
                f"{self.prefix}_app_info",
                "アプリケーション情報",
                registry=self.registry,
            )

            self.metrics["metrics_export_count"] = Counter(
                f"{self.prefix}_metrics_export_total",
                "メトリクスエクスポート回数",
                registry=self.registry,
            )

            self.logger.info("ビルトインメトリクス作成完了")

        except Exception as e:
            self.logger.error(f"ビルトインメトリクス作成エラー: {e}")

    def create_counter(
        self, name: str, description: str = "", labelnames: Optional[List[str]] = None
    ) -> Optional[Counter]:
        """Counter作成

        Args:
            name: メトリクス名
            description: 説明
            labelnames: ラベル名リスト

        Returns:
            Counterオブジェクト
        """
        if not self.available:
            return None

        try:
            full_name = f"{self.prefix}_{name}"
            counter = Counter(
                full_name,
                description or f"{name} counter",
                labelnames or [],
                registry=self.registry,
            )
            self.metrics[name] = counter

            # ラベルキャッシュ更新
            if labelnames:
                self.labels_cache[name].update(labelnames)

            self.logger.debug(f"Counter作成: {full_name}")
            return counter

        except Exception as e:
            self.logger.error(f"Counter作成エラー ({name}): {e}")
            return None

    def create_gauge(
        self, name: str, description: str = "", labelnames: Optional[List[str]] = None
    ) -> Optional[Gauge]:
        """Gauge作成

        Args:
            name: メトリクス名
            description: 説明
            labelnames: ラベル名リスト

        Returns:
            Gaugeオブジェクト
        """
        if not self.available:
            return None

        try:
            full_name = f"{self.prefix}_{name}"
            gauge = Gauge(
                full_name,
                description or f"{name} gauge",
                labelnames or [],
                registry=self.registry,
            )
            self.metrics[name] = gauge

            # ラベルキャッシュ更新
            if labelnames:
                self.labels_cache[name].update(labelnames)

            self.logger.debug(f"Gauge作成: {full_name}")
            return gauge

        except Exception as e:
            self.logger.error(f"Gauge作成エラー ({name}): {e}")
            return None

    def create_histogram(
        self,
        name: str,
        description: str = "",
        labelnames: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Optional[Histogram]:
        """Histogram作成

        Args:
            name: メトリクス名
            description: 説明
            labelnames: ラベル名リスト
            buckets: ヒストグラムバケット

        Returns:
            Histogramオブジェクト
        """
        if not self.available:
            return None

        try:
            full_name = f"{self.prefix}_{name}"
            histogram = Histogram(
                full_name,
                description or f"{name} histogram",
                labelnames or [],
                buckets=buckets,
                registry=self.registry,
            )
            self.metrics[name] = histogram

            # ラベルキャッシュ更新
            if labelnames:
                self.labels_cache[name].update(labelnames)

            self.logger.debug(f"Histogram作成: {full_name}")
            return histogram

        except Exception as e:
            self.logger.error(f"Histogram作成エラー ({name}): {e}")
            return None

    def get_metric(self, name: str) -> Optional[Any]:
        """メトリクス取得

        Args:
            name: メトリクス名

        Returns:
            メトリクスオブジェクト
        """
        return self.metrics.get(name)

    def record_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Counter記録

        Args:
            name: メトリクス名
            value: 増加値
            labels: ラベル

        Returns:
            記録成功フラグ
        """
        if not self.available:
            return False

        try:
            metric = self.metrics.get(name)
            if not metric or not isinstance(metric, Counter):
                return False

            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

            return True
        except Exception as e:
            self.logger.error(f"Counter記録エラー ({name}): {e}")
            return False

    def record_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Gauge記録

        Args:
            name: メトリクス名
            value: 設定値
            labels: ラベル

        Returns:
            記録成功フラグ
        """
        if not self.available:
            return False

        try:
            metric = self.metrics.get(name)
            if not metric or not isinstance(metric, Gauge):
                return False

            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

            return True
        except Exception as e:
            self.logger.error(f"Gauge記録エラー ({name}): {e}")
            return False

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Histogram記録

        Args:
            name: メトリクス名
            value: 記録値
            labels: ラベル

        Returns:
            記録成功フラグ
        """
        if not self.available:
            return False

        try:
            metric = self.metrics.get(name)
            if not metric or not isinstance(metric, Histogram):
                return False

            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

            return True
        except Exception as e:
            self.logger.error(f"Histogram記録エラー ({name}): {e}")
            return False

    def register_custom_collector(
        self, name: str, collect_func: Callable[[], Any]
    ) -> bool:
        """カスタムコレクター登録

        Args:
            name: コレクター名
            collect_func: 収集関数

        Returns:
            登録成功フラグ
        """
        if not self.available:
            return False

        try:
            collector = CustomCollector(name, collect_func)
            self.registry.register(collector)
            self.custom_collectors[name] = collector

            self.logger.info(f"カスタムコレクター登録: {name}")
            return True
        except Exception as e:
            self.logger.error(f"カスタムコレクター登録エラー ({name}): {e}")
            return False

    def unregister_custom_collector(self, name: str) -> bool:
        """カスタムコレクター登録解除

        Args:
            name: コレクター名

        Returns:
            登録解除成功フラグ
        """
        if not self.available:
            return False

        try:
            if name in self.custom_collectors:
                collector = self.custom_collectors[name]
                self.registry.unregister(collector)
                del self.custom_collectors[name]

                self.logger.info(f"カスタムコレクター登録解除: {name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"カスタムコレクター登録解除エラー ({name}): {e}")
            return False

    def start_http_server(self) -> bool:
        """HTTPサーバー開始

        Returns:
            開始成功フラグ
        """
        if not self.available:
            self.logger.error(
                "Prometheusクライアント利用不可のためHTTPサーバー開始不可"
            )
            return False

        if self.http_server is not None:
            self.logger.warning("HTTPサーバー既に起動済み")
            return True

        try:
            # HTTPサーバー作成
            def handler_factory(*args: Any, **kwargs: Any) -> PrometheusMetricsHandler:
                return PrometheusMetricsHandler(self, *args, **kwargs)

            self.http_server = HTTPServer((self.host, self.port), handler_factory)

            # サーバースレッド開始
            self.shutdown_event.clear()
            self.server_thread = threading.Thread(
                target=self._run_http_server, name="PrometheusHTTPServer", daemon=True
            )
            self.server_thread.start()

            self.logger.info(
                f"Prometheus HTTPサーバー開始: http://{self.host}:{self.port}/metrics"
            )
            return True

        except Exception as e:
            self.logger.error(f"HTTPサーバー開始エラー: {e}")
            return False

    def _run_http_server(self) -> None:
        """HTTPサーバー実行"""
        try:
            while not self.shutdown_event.is_set():
                if self.http_server is not None:
                    self.http_server.handle_request()
        except Exception as e:
            if not self.shutdown_event.is_set():
                self.logger.error(f"HTTPサーバー実行エラー: {e}")

    def stop_http_server(self) -> None:
        """HTTPサーバー停止"""
        try:
            if self.http_server is None:
                return

            self.shutdown_event.set()

            # サーバー停止
            self.http_server.shutdown()
            self.http_server.server_close()

            # スレッド終了待機
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5.0)

            self.http_server = None
            self.server_thread = None

            self.logger.info("Prometheus HTTPサーバー停止")

        except Exception as e:
            self.logger.error(f"HTTPサーバー停止エラー: {e}")

    def generate_prometheus_metrics(self, name_filter: Optional[str] = None) -> str:
        """Prometheusメトリクス生成

        Args:
            name_filter: メトリクス名フィルタ

        Returns:
            Prometheus形式メトリクス文字列
        """
        if not self.available:
            return "# Prometheusクライアント利用不可\n"

        try:
            start_time = time.time()

            # 標準生成
            metrics_data_bytes = generate_latest(self.registry)
            metrics_data = metrics_data_bytes.decode("utf-8")

            # フィルタ適用
            if name_filter:
                lines = metrics_data.split("\n")
                filtered_lines = []

                for line in lines:
                    if (
                        line.startswith("#")
                        or name_filter in line
                        or line.strip() == ""
                    ):
                        filtered_lines.append(line)

                metrics_data = "\n".join(filtered_lines)

            # 統計更新
            self.request_count += 1
            self.last_request_time = time.time()
            generation_time = self.last_request_time - start_time
            self.total_response_time += generation_time

            # ビルトインメトリクス更新
            if self.enable_builtin_metrics and "metrics_export_count" in self.metrics:
                self.metrics["metrics_export_count"].inc()

            return str(metrics_data)

        except Exception as e:
            self.logger.error(f"Prometheusメトリクス生成エラー: {e}")
            return f"# メトリクス生成エラー: {str(e)}\n"

    def update_system_metrics(self, cpu_usage: float, memory_usage: float) -> None:
        """システムメトリクス更新

        Args:
            cpu_usage: CPU使用率
            memory_usage: メモリ使用率
        """
        if not self.available or not self.enable_builtin_metrics:
            return

        try:
            if "system_cpu_usage" in self.metrics:
                self.metrics["system_cpu_usage"].set(cpu_usage)

            if "system_memory_usage" in self.metrics:
                self.metrics["system_memory_usage"].set(memory_usage)

        except Exception as e:
            self.logger.error(f"システムメトリクス更新エラー: {e}")

    def set_app_info(self, info_dict: Dict[str, str]) -> None:
        """アプリケーション情報設定

        Args:
            info_dict: アプリケーション情報
        """
        if not self.available or not self.enable_builtin_metrics:
            return

        try:
            if "app_info" in self.metrics:
                self.metrics["app_info"].info(info_dict)
        except Exception as e:
            self.logger.error(f"アプリケーション情報設定エラー: {e}")

    def get_exporter_health(self) -> Dict[str, Any]:
        """エクスポーターヘルス状態取得

        Returns:
            ヘルス状態情報
        """
        return {
            "status": "healthy" if self.available else "unavailable",
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "http_server_running": self.http_server is not None,
            "metrics_count": len(self.metrics),
            "custom_collectors": len(self.custom_collectors),
            "request_count": self.request_count,
            "last_request_time": self.last_request_time,
            "avg_response_time": (
                self.total_response_time / self.request_count
                if self.request_count > 0
                else 0.0
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def get_configuration(self) -> Dict[str, Any]:
        """設定情報取得

        Returns:
            設定情報
        """
        return {
            "available": self.available,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "host": self.host,
            "port": self.port,
            "prefix": self.prefix,
            "builtin_metrics_enabled": self.enable_builtin_metrics,
            "metrics_registered": list(self.metrics.keys()),
            "custom_collectors": list(self.custom_collectors.keys()),
            "label_names": {
                name: list(labels) for name, labels in self.labels_cache.items()
            },
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクスサマリ取得

        Returns:
            メトリクスサマリ
        """
        try:
            summary = {
                "total_metrics": len(self.metrics),
                "custom_collectors": len(self.custom_collectors),
                "metric_types": defaultdict(int),
                "label_usage": {},
                "timestamp": datetime.now().isoformat(),
            }

            # メトリクス型分類
            for name, metric in self.metrics.items():
                metric_type = type(metric).__name__
                metric_types_dict = cast(Dict[str, int], summary["metric_types"])
                metric_types_dict[metric_type] += 1

            # ラベル使用状況
            label_usage_dict = cast(Dict[str, int], summary["label_usage"])
            for name, labels in self.labels_cache.items():
                if labels:
                    label_usage_dict[name] = len(labels)

            return summary

        except Exception as e:
            self.logger.error(f"メトリクスサマリ取得エラー: {e}")
            return {"error": str(e)}

    def shutdown(self) -> None:
        """Prometheusエクスポーター終了処理"""
        try:
            # HTTPサーバー停止
            self.stop_http_server()

            # カスタムコレクター登録解除
            for name in list(self.custom_collectors.keys()):
                self.unregister_custom_collector(name)

            self.logger.info("PrometheusExporter終了処理完了")

        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")

    def __enter__(self) -> "PrometheusExporter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
