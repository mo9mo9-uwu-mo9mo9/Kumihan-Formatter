"""
OpenTelemetry統合セットアップモジュール

OpenTelemetry SDK初期化・設定管理・分散トレーシング・
メトリクス統合・ログ統合を提供するテレメトリシステム
"""

import os
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Union

from kumihan_formatter.core.utilities.logger import get_logger

try:
    # OpenTelemetry core imports
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (  # noqa: E501
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # noqa: E501
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.logging import (  # noqa: E501
        LoggingInstrumentor,
    )
    from opentelemetry.instrumentation.psutil import (
        PsutilInstrumentor,
    )
    from opentelemetry.instrumentation.threading import (  # noqa: E501
        ThreadingInstrumentor,
    )
    from opentelemetry.propagate import (
        set_global_textmap,
    )
    from opentelemetry.propagators.b3 import (
        B3MultiFormat,
    )
    from opentelemetry.sdk.metrics import (
        MeterProvider,
    )
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import (
        SERVICE_NAME,
        SERVICE_VERSION,
        Resource,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        SimpleSpanProcessor,
    )

    # from opentelemetry.semconv.trace import SpanAttributes

    OPENTELEMETRY_AVAILABLE = True
except ImportError as e:
    OPENTELEMETRY_AVAILABLE = False
    IMPORT_ERROR = str(e)

    # フォールバック実装（型チェック対応）
    metrics = None
    trace = None
    OTLPMetricExporter = None
    OTLPSpanExporter = None
    LoggingInstrumentor = None
    PsutilInstrumentor = None
    ThreadingInstrumentor = None
    set_global_textmap = None
    B3MultiFormat = None
    MeterProvider = None
    PeriodicExportingMetricReader = None
    SERVICE_NAME = "service.name"
    SERVICE_VERSION = "service.version"
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    SimpleSpanProcessor = None


class OpenTelemetrySetup:
    """OpenTelemetry統合セットアップシステム

    OpenTelemetry SDK初期化・設定管理・分散トレーシング・
    メトリクス統合・ログ統合を提供する
    """

    def __init__(
        self,
        service_name: str = "kumihan-formatter",
        service_version: str = "1.0.0",
        environment: str = "development",
        endpoint: Optional[str] = None,
        enable_console_exporter: bool = True,
        enable_auto_instrumentation: bool = True,
    ):
        """OpenTelemetry統合システム初期化

        Args:
            service_name: サービス名
            service_version: サービスバージョン
            environment: 実行環境
            endpoint: OTLP エンドポイント
            enable_console_exporter: コンソールエクスポート有効化
            enable_auto_instrumentation: 自動インストルメンテーション有効化
        """
        self.logger = get_logger(__name__)
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.endpoint = endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
        self.enable_console_exporter = enable_console_exporter
        self.enable_auto_instrumentation = enable_auto_instrumentation

        # 初期化状態管理
        self.initialized = False
        self.tracer_provider: Optional[Any] = None
        self.meter_provider: Optional[Any] = None
        self.tracer: Optional[Any] = None
        self.meter: Optional[Any] = None
        self.instrumentors: List[Any] = []
        self.setup_lock = threading.Lock()

        # OpenTelemetry利用可能性確認
        if not OPENTELEMETRY_AVAILABLE:
            self.logger.warning(f"OpenTelemetry利用不可: {IMPORT_ERROR}")
            self.logger.info(
                "pip install opentelemetry-api opentelemetry-sdk で利用可能になります"
            )
        else:
            self.logger.info(
                f"OpenTelemetryセットアップ準備完了 - サービス: {service_name}"
            )

    def initialize(self) -> bool:
        """OpenTelemetry初期化

        Returns:
            初期化成功フラグ
        """
        if not OPENTELEMETRY_AVAILABLE:
            self.logger.error("OpenTelemetryライブラリが利用できません")
            return False

        with self.setup_lock:
            if self.initialized:
                self.logger.info("OpenTelemetry既に初期化済み")
                return True

            try:
                # リソース設定
                resource = self._create_resource()

                # トレーシング設定
                self._setup_tracing(resource)

                # メトリクス設定
                self._setup_metrics(resource)

                # プロパゲーター設定
                self._setup_propagators()

                # 自動インストルメンテーション
                if self.enable_auto_instrumentation:
                    self._setup_auto_instrumentation()

                self.initialized = True
                self.logger.info("OpenTelemetry初期化完了")
                return True

            except Exception as e:
                self.logger.error(f"OpenTelemetry初期化エラー: {e}")
                return False

    def _create_resource(self) -> Any:
        """OpenTelemetryリソース作成

        Returns:
            作成されたリソース
        """
        attributes = {
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "service.environment": self.environment,
            "service.instance.id": f"{self.service_name}-{os.getpid()}",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        }

        return Resource.create(attributes)

    def _setup_tracing(self, resource: Any) -> None:
        """トレーシング設定

        Args:
            resource: OpenTelemetryリソース
        """
        # TracerProvider作成
        self.tracer_provider = TracerProvider(resource=resource)

        # OTLP Exporter設定
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.endpoint, insecure=True  # 開発環境用
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)

            self.logger.info(f"OTLPスパンエクスポーター設定完了: {self.endpoint}")
        except Exception as e:
            self.logger.warning(f"OTLPスパンエクスポーター設定失敗: {e}")

        # Console Exporter設定（開発用）
        if self.enable_console_exporter:
            try:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                console_exporter = ConsoleSpanExporter()
                console_processor = SimpleSpanProcessor(console_exporter)
                self.tracer_provider.add_span_processor(console_processor)

                self.logger.info("コンソールスパンエクスポーター設定完了")
            except Exception as e:
                self.logger.warning(f"コンソールスパンエクスポーター設定失敗: {e}")

        # グローバルTracerProvider設定
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer = trace.get_tracer(__name__)

        self.logger.info("トレーシング設定完了")

    def _setup_metrics(self, resource: Any) -> None:
        """メトリクス設定

        Args:
            resource: OpenTelemetryリソース
        """
        try:
            # OTLP Metric Exporter設定
            metric_exporter = OTLPMetricExporter(
                endpoint=self.endpoint, insecure=True  # 開発環境用
            )

            # Metric Reader設定
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter, export_interval_millis=30000  # 30秒間隔
            )

            # MeterProvider作成
            self.meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )

            # グローバルMeterProvider設定
            metrics.set_meter_provider(self.meter_provider)
            self.meter = metrics.get_meter(__name__)

            self.logger.info(f"メトリクス設定完了: {self.endpoint}")

        except Exception as e:
            self.logger.warning(f"メトリクス設定失敗: {e}")

    def _setup_propagators(self) -> None:
        """プロパゲーター設定"""
        try:
            # B3プロパゲーター設定（分散トレーシング用）
            set_global_textmap(B3MultiFormat())
            self.logger.info("B3プロパゲーター設定完了")
        except Exception as e:
            self.logger.warning(f"プロパゲーター設定失敗: {e}")

    def _setup_auto_instrumentation(self) -> None:
        """自動インストルメンテーション設定"""
        try:
            # ログインストルメンテーション
            if LoggingInstrumentor().is_instrumented_by_opentelemetry:
                self.logger.debug("ログインストルメンテーション既設定済み")
            else:
                logging_instrumentor = LoggingInstrumentor()
                logging_instrumentor.instrument(set_logging_format=True)
                self.instrumentors.append(logging_instrumentor)
                self.logger.info("ログインストルメンテーション設定完了")

            # スレッドインストルメンテーション
            if ThreadingInstrumentor().is_instrumented_by_opentelemetry:
                self.logger.debug("スレッドインストルメンテーション既設定済み")
            else:
                threading_instrumentor = ThreadingInstrumentor()
                threading_instrumentor.instrument()
                self.instrumentors.append(threading_instrumentor)
                self.logger.info("スレッドインストルメンテーション設定完了")

            # psutilインストルメンテーション（システムメトリクス）
            try:
                if PsutilInstrumentor().is_instrumented_by_opentelemetry:
                    self.logger.debug("psutilインストルメンテーション既設定済み")
                else:
                    psutil_instrumentor = PsutilInstrumentor()
                    psutil_instrumentor.instrument()
                    self.instrumentors.append(psutil_instrumentor)
                    self.logger.info("psutilインストルメンテーション設定完了")
            except Exception as e:
                self.logger.warning(f"psutilインストルメンテーション設定失敗: {e}")

        except Exception as e:
            self.logger.error(f"自動インストルメンテーション設定エラー: {e}")

    def get_tracer(self, name: Optional[str] = None) -> Optional[Any]:
        """Tracer取得

        Args:
            name: トレーサー名

        Returns:
            Tracerオブジェクト
        """
        if not self.initialized:
            self.logger.warning("OpenTelemetry未初期化状態でのTracer取得")
            return None

        if name:
            return trace.get_tracer(name)
        return self.tracer

    def get_meter(self, name: Optional[str] = None) -> Optional[Any]:
        """Meter取得

        Args:
            name: メーター名

        Returns:
            Meterオブジェクト
        """
        if not self.initialized:
            self.logger.warning("OpenTelemetry未初期化状態でのMeter取得")
            return None

        if name:
            return metrics.get_meter(name)
        return self.meter

    @contextmanager
    def trace_span(
        self, span_name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Any:
        """トレーススパンコンテキストマネージャ

        Args:
            span_name: スパン名
            attributes: スパン属性

        Yields:
            スパンオブジェクト
        """
        if not self.initialized or not self.tracer:
            # 初期化されていない場合は何もしない
            yield None
            return

        with self.tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            yield span

    def create_custom_instrumentor(
        self, name: str, instrument_func: Callable[[], None]
    ) -> bool:
        """カスタムインストルメンテーション作成

        Args:
            name: インストルメンター名
            instrument_func: インストルメンテーション関数

        Returns:
            作成成功フラグ
        """
        if not self.initialized:
            self.logger.error(
                "OpenTelemetry未初期化状態でのカスタムインストルメンテーション"
            )
            return False

        try:
            instrument_func()
            self.logger.info(f"カスタムインストルメンテーション作成完了: {name}")
            return True
        except Exception as e:
            self.logger.error(f"カスタムインストルメンテーション作成失敗 ({name}): {e}")
            return False

    def record_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str = "",
        description: str = "",
        attributes: Optional[Dict[str, str]] = None,
    ) -> bool:
        """メトリクス記録

        Args:
            metric_name: メトリクス名
            value: メトリクス値
            unit: 単位
            description: 説明
            attributes: 属性

        Returns:
            記録成功フラグ
        """
        if not self.initialized or not self.meter:
            self.logger.warning("OpenTelemetry未初期化状態でのメトリクス記録")
            return False

        try:
            # Counter作成・使用
            counter = self.meter.create_counter(
                name=metric_name, unit=unit, description=description
            )
            counter.add(value, attributes or {})

            return True
        except Exception as e:
            self.logger.error(f"メトリクス記録失敗 ({metric_name}): {e}")
            return False

    def record_histogram(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str = "",
        description: str = "",
        attributes: Optional[Dict[str, str]] = None,
    ) -> bool:
        """ヒストグラム記録

        Args:
            metric_name: メトリクス名
            value: メトリクス値
            unit: 単位
            description: 説明
            attributes: 属性

        Returns:
            記録成功フラグ
        """
        if not self.initialized or not self.meter:
            self.logger.warning("OpenTelemetry未初期化状態でのヒストグラム記録")
            return False

        try:
            # Histogram作成・使用
            histogram = self.meter.create_histogram(
                name=metric_name, unit=unit, description=description
            )
            histogram.record(value, attributes or {})

            return True
        except Exception as e:
            self.logger.error(f"ヒストグラム記録失敗 ({metric_name}): {e}")
            return False

    def get_configuration_status(self) -> Dict[str, Any]:
        """設定状態取得

        Returns:
            設定状態情報
        """
        return {
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "initialized": self.initialized,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "endpoint": self.endpoint,
            "console_exporter_enabled": self.enable_console_exporter,
            "auto_instrumentation_enabled": self.enable_auto_instrumentation,
            "active_instrumentors": len(self.instrumentors),
            "tracer_available": self.tracer is not None,
            "meter_available": self.meter is not None,
        }

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """強制フラッシュ

        Args:
            timeout_millis: タイムアウト（ミリ秒）

        Returns:
            フラッシュ成功フラグ
        """
        if not self.initialized:
            return False

        try:
            # TracerProvider フラッシュ
            if self.tracer_provider:
                self.tracer_provider.force_flush(timeout_millis)

            # MeterProvider フラッシュ
            if self.meter_provider:
                self.meter_provider.force_flush(timeout_millis)

            self.logger.info("OpenTelemetry強制フラッシュ完了")
            return True
        except Exception as e:
            self.logger.error(f"OpenTelemetry強制フラッシュエラー: {e}")
            return False

    def shutdown(self) -> None:
        """OpenTelemetryシャットダウン"""
        try:
            if not self.initialized:
                return

            # 最終フラッシュ
            self.force_flush()

            # インストルメンテーション無効化
            for instrumentor in self.instrumentors:
                try:
                    instrumentor.uninstrument()
                except Exception as e:
                    self.logger.warning(f"インストルメンテーション無効化エラー: {e}")

            # TracerProviderシャットダウン
            if self.tracer_provider:
                self.tracer_provider.shutdown()

            # MeterProviderシャットダウン
            if self.meter_provider:
                self.meter_provider.shutdown()

            self.initialized = False
            self.logger.info("OpenTelemetryシャットダウン完了")

        except Exception as e:
            self.logger.error(f"OpenTelemetryシャットダウンエラー: {e}")

    def __enter__(self) -> "OpenTelemetrySetup":
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()


# グローバルOpenTelemetryセットアップインスタンス
_global_otel_setup: Optional[OpenTelemetrySetup] = None
_setup_lock = threading.Lock()


def get_global_otel_setup() -> Optional[OpenTelemetrySetup]:
    """グローバルOpenTelemetryセットアップ取得

    Returns:
        グローバルOpenTelemetryセットアップ
    """
    return _global_otel_setup


def initialize_global_otel(
    service_name: str = "kumihan-formatter",
    service_version: str = "1.0.0",
    environment: str = "development",
    **kwargs: Any,
) -> bool:
    """グローバルOpenTelemetry初期化

    Args:
        service_name: サービス名
        service_version: サービスバージョン
        environment: 実行環境
        **kwargs: その他設定

    Returns:
        初期化成功フラグ
    """
    global _global_otel_setup

    with _setup_lock:
        if _global_otel_setup is not None:
            return _global_otel_setup.initialized

        _global_otel_setup = OpenTelemetrySetup(
            service_name=service_name,
            service_version=service_version,
            environment=environment,
            **kwargs,
        )

        return _global_otel_setup.initialize()


def shutdown_global_otel() -> None:
    """グローバルOpenTelemetryシャットダウン"""
    global _global_otel_setup

    with _setup_lock:
        if _global_otel_setup:
            _global_otel_setup.shutdown()
            _global_otel_setup = None
