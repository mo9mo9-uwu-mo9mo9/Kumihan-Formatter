"""
Jaegerトレーサーモジュール

Jaegerトレーシング・スパン管理・分散トレース相関・
パフォーマンス分析・設定管理を提供する分散トレーシングシステム
"""

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from kumihan_formatter.core.utilities.logger import get_logger

try:
    # Jaeger/OpenTelemetry imports
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # from opentelemetry.trace import SpanKind, Status, StatusCode
    # from opentelemetry.util.types import AttributeValue

    JAEGER_AVAILABLE = True
except ImportError as e:
    JAEGER_AVAILABLE = False
    IMPORT_ERROR = str(e)


@dataclass
class SpanData:
    """スパンデータクラス"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float]
    duration_ms: Optional[float]
    status: str
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]


@dataclass
class TraceAnalysis:
    """トレース分析結果"""

    trace_id: str
    total_duration_ms: float
    span_count: int
    error_count: int
    critical_path_ms: float
    bottleneck_spans: List[Dict[str, Any]]
    performance_score: float
    suggestions: List[str]


class JaegerTracer:
    """Jaegerトレーサーシステム

    Jaegerトレーシング・スパン管理・分散トレース相関・
    パフォーマンス分析・設定管理を提供する
    """

    def __init__(
        self,
        service_name: str = "kumihan-formatter",
        service_version: str = "1.0.0",
        jaeger_endpoint: Optional[str] = None,
        sampling_rate: float = 1.0,
        enable_performance_analysis: bool = True,
        max_trace_retention: int = 1000,
    ):
        """Jaegerトレーサー初期化

        Args:
            service_name: サービス名
            service_version: サービスバージョン
            jaeger_endpoint: Jaegerエンドポイント
            sampling_rate: サンプリング率 (0.0-1.0)
            enable_performance_analysis: パフォーマンス分析有効化
            max_trace_retention: 最大トレース保持数
        """
        self.logger = get_logger(__name__)
        self.service_name = service_name
        self.service_version = service_version
        self.jaeger_endpoint = jaeger_endpoint or os.getenv(
            "JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
        )
        self.sampling_rate = sampling_rate
        self.enable_performance_analysis = enable_performance_analysis
        self.max_trace_retention = max_trace_retention

        # Jaeger利用可能性確認
        if not JAEGER_AVAILABLE:
            self.logger.warning(f"Jaegerクライアント利用不可: {IMPORT_ERROR}")
            self.logger.info(
                "pip install opentelemetry-exporter-jaeger で利用可能になります"
            )
            self.available = False
            return

        self.available = True

        # トレーシング設定
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.initialized = False

        # スパンデータ管理
        self.active_spans: Dict[str, SpanData] = {}
        self.completed_traces: Dict[str, List[SpanData]] = {}
        self.trace_analyses: Dict[str, TraceAnalysis] = {}
        self.spans_lock = threading.Lock()

        # パフォーマンス統計
        self.total_spans = 0
        self.total_traces = 0
        self.average_span_duration = 0.0
        self.error_rate = 0.0

        # 設定初期化
        if self.available:
            self._initialize_tracer()

        self.logger.info(
            f"JaegerTracer初期化完了 - エンドポイント: {self.jaeger_endpoint}"
        )

    def _initialize_tracer(self) -> bool:
        """Jaegerトレーサー初期化

        Returns:
            初期化成功フラグ
        """
        try:
            # リソース作成
            resource = Resource.create(
                {
                    SERVICE_NAME: self.service_name,
                    SERVICE_VERSION: self.service_version,
                    "service.instance.id": f"{self.service_name}-{os.getpid()}",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.language": "python",
                }
            )

            # TracerProvider作成
            self.tracer_provider = TracerProvider(resource=resource)

            # Jaeger Exporter設定
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",  # Jaegerエージェントホスト
                agent_port=6831,  # Jaegerエージェントポート
                collector_endpoint=(self.jaeger_endpoint or "").replace(
                    "/api/traces", ""
                ),  # コレクターエンドポイント
            )

            # SpanProcessor設定
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self.tracer_provider.add_span_processor(span_processor)

            # グローバル設定
            trace.set_tracer_provider(self.tracer_provider)
            self.tracer = trace.get_tracer(__name__)

            self.initialized = True
            self.logger.info("Jaegerトレーサー初期化完了")
            return True

        except Exception as e:
            self.logger.error(f"Jaegerトレーサー初期化エラー: {e}")
            return False

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        span_kind: str = "INTERNAL",
    ) -> Optional[str]:
        """スパン開始

        Args:
            operation_name: オペレーション名
            parent_span_id: 親スパンID
            tags: スパンタグ
            span_kind: スパン種別

        Returns:
            スパンID
        """
        if not self.available or not self.initialized:
            return None

        try:
            # スパンID生成
            span_id = str(uuid.uuid4())

            # スパン開始
            tracer = self.tracer
            if tracer is None:
                return None

            with tracer.start_as_current_span(operation_name) as span:
                # スパン属性設定
                if tags:
                    for key, value in tags.items():
                        span.set_attribute(key, str(value))

                span.set_attribute("span.id", span_id)
                if parent_span_id:
                    span.set_attribute("parent.span.id", parent_span_id)

                # スパンデータ作成
                span_data = SpanData(
                    trace_id=str(span.get_span_context().trace_id),
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    operation_name=operation_name,
                    start_time=time.time(),
                    end_time=None,
                    duration_ms=None,
                    status="RUNNING",
                    tags=tags or {},
                    logs=[],
                )

                # アクティブスパン登録
                with self.spans_lock:
                    self.active_spans[span_id] = span_data

                self.logger.debug(f"スパン開始: {operation_name} (ID: {span_id})")
                return span_id

        except Exception as e:
            self.logger.error(f"スパン開始エラー ({operation_name}): {e}")
            return None

    def finish_span(
        self,
        span_id: str,
        status: str = "OK",
        tags: Optional[Dict[str, Any]] = None,
        logs: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """スパン終了

        Args:
            span_id: スパンID
            status: ステータス
            tags: 追加タグ
            logs: ログエントリ

        Returns:
            終了成功フラグ
        """
        if not self.available or not self.initialized:
            return False

        try:
            with self.spans_lock:
                if span_id not in self.active_spans:
                    self.logger.warning(f"未知のスパンID: {span_id}")
                    return False

                span_data = self.active_spans[span_id]

                # スパン終了処理
                end_time = time.time()
                duration_ms = (end_time - span_data.start_time) * 1000

                span_data.end_time = end_time
                span_data.duration_ms = duration_ms
                span_data.status = status

                # 追加データ設定
                if tags:
                    span_data.tags.update(tags)
                if logs:
                    span_data.logs.extend(logs)

                # 完了トレースに移動
                trace_id = span_data.trace_id
                if trace_id not in self.completed_traces:
                    self.completed_traces[trace_id] = []

                self.completed_traces[trace_id].append(span_data)

                # アクティブスパンから削除
                del self.active_spans[span_id]

                # 統計更新
                self.total_spans += 1
                self._update_statistics(duration_ms, status)

                # パフォーマンス分析
                if self.enable_performance_analysis:
                    self._analyze_trace_if_complete(trace_id)

                self.logger.debug(
                    f"スパン終了: {span_data.operation_name} (時間: {duration_ms:.2f}ms)"
                )
                return True

        except Exception as e:
            self.logger.error(f"スパン終了エラー ({span_id}): {e}")
            return False

    def add_span_log(self, span_id: str, log_entry: Dict[str, Any]) -> bool:
        """スパンログ追加

        Args:
            span_id: スパンID
            log_entry: ログエントリ

        Returns:
            追加成功フラグ
        """
        if not self.available:
            return False

        try:
            with self.spans_lock:
                if span_id in self.active_spans:
                    log_entry["timestamp"] = time.time()
                    self.active_spans[span_id].logs.append(log_entry)
                    return True

            return False
        except Exception as e:
            self.logger.error(f"スパンログ追加エラー ({span_id}): {e}")
            return False

    def add_span_tag(self, span_id: str, key: str, value: Any) -> bool:
        """スパンタグ追加

        Args:
            span_id: スパンID
            key: タグキー
            value: タグ値

        Returns:
            追加成功フラグ
        """
        if not self.available:
            return False

        try:
            with self.spans_lock:
                if span_id in self.active_spans:
                    self.active_spans[span_id].tags[key] = value
                    return True

            return False
        except Exception as e:
            self.logger.error(f"スパンタグ追加エラー ({span_id}): {e}")
            return False

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        tags: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
    ) -> Any:
        """オペレーショントレーシングコンテキストマネージャ

        Args:
            operation_name: オペレーション名
            tags: スパンタグ
            parent_span_id: 親スパンID

        Yields:
            スパンID
        """
        span_id = None
        try:
            span_id = self.start_span(operation_name, parent_span_id, tags)
            yield span_id
        except Exception as e:
            if span_id:
                self.add_span_tag(span_id, "error", True)
                self.add_span_log(
                    span_id, {"level": "error", "message": str(e), "event": "exception"}
                )
            raise
        finally:
            if span_id:
                status = "OK"
                if span_id and span_id in self.active_spans:
                    span_data = self.active_spans[span_id]
                    if isinstance(span_data, SpanData) and span_data.tags.get("error"):
                        status = "ERROR"
                self.finish_span(span_id, status)

    def _update_statistics(self, duration_ms: float, status: str) -> None:
        """統計更新

        Args:
            duration_ms: スパン実行時間
            status: スパンステータス
        """
        try:
            # 平均実行時間更新
            if self.total_spans > 1:
                self.average_span_duration = (
                    self.average_span_duration * (self.total_spans - 1) + duration_ms
                ) / self.total_spans
            else:
                self.average_span_duration = duration_ms

            # エラー率更新
            if status == "ERROR":
                error_count = sum(
                    1
                    for trace_spans in self.completed_traces.values()
                    for span in trace_spans
                    if span.status == "ERROR"
                )
                self.error_rate = (
                    error_count / self.total_spans if self.total_spans > 0 else 0.0
                )

        except Exception as e:
            self.logger.error(f"統計更新エラー: {e}")

    def _analyze_trace_if_complete(self, trace_id: str) -> None:
        """トレース完了時の分析実行

        Args:
            trace_id: トレースID
        """
        try:
            trace_spans = self.completed_traces.get(trace_id, [])
            if not trace_spans:
                return

            # アクティブスパンが残っている場合はまだ完了していない
            active_spans_in_trace = [
                span
                for span in self.active_spans.values()
                if hasattr(span, "trace_id") and span.trace_id == trace_id
            ]

            if active_spans_in_trace:
                return  # まだ完了していない

            # トレース分析実行
            analysis = self._perform_trace_analysis(trace_id, trace_spans)
            if analysis:
                self.trace_analyses[trace_id] = analysis

                # 古い分析データクリーンアップ
                if len(self.trace_analyses) > self.max_trace_retention:
                    oldest_trace = min(self.trace_analyses.keys())
                    del self.trace_analyses[oldest_trace]

                self.total_traces += 1
                self.logger.debug(
                    f"トレース分析完了: {trace_id} (スコア: {analysis.performance_score:.2f})"
                )

        except Exception as e:
            self.logger.error(f"トレース分析エラー ({trace_id}): {e}")

    def _perform_trace_analysis(
        self, trace_id: str, spans: List[SpanData]
    ) -> Optional[TraceAnalysis]:
        """トレース分析実行

        Args:
            trace_id: トレースID
            spans: スパンリスト

        Returns:
            分析結果
        """
        try:
            if not spans:
                return None

            # 基本統計
            total_duration = max(span.duration_ms or 0 for span in spans)
            span_count = len(spans)
            error_count = sum(1 for span in spans if span.status == "ERROR")

            # クリティカルパス計算（最長実行パス）
            critical_path_ms = sum(span.duration_ms or 0 for span in spans)

            # ボトルネックスパン特定
            avg_duration = sum(span.duration_ms or 0 for span in spans) / span_count
            bottleneck_spans = []

            for span in spans:
                if (span.duration_ms or 0) > avg_duration * 2:  # 平均の2倍以上
                    bottleneck_spans.append(
                        {
                            "operation_name": span.operation_name,
                            "duration_ms": span.duration_ms,
                            "span_id": span.span_id,
                        }
                    )

            # パフォーマンススコア計算 (0-100)
            performance_score = 100.0

            # エラー率によるペナルティ
            if error_count > 0:
                performance_score -= (error_count / span_count) * 50

            # 実行時間によるペナルティ
            if total_duration > 1000:  # 1秒以上
                performance_score -= min(30, (total_duration - 1000) / 1000 * 10)

            # ボトルネック数によるペナルティ
            performance_score -= len(bottleneck_spans) * 5

            performance_score = max(0, performance_score)

            # 改善提案生成
            suggestions = []

            if error_count > 0:
                suggestions.append(
                    f"{error_count}個のエラーが発生しました。エラーハンドリングを確認してください。"
                )

            if total_duration > 5000:  # 5秒以上
                suggestions.append(
                    "実行時間が長すぎます。処理の最適化を検討してください。"
                )

            if len(bottleneck_spans) > 0:
                suggestions.append(
                    f"{len(bottleneck_spans)}個のボトルネックスパンが検出されました。"
                )

            if span_count > 50:
                suggestions.append(
                    "スパン数が多すぎます。トレースの粒度を調整してください。"
                )

            return TraceAnalysis(
                trace_id=trace_id,
                total_duration_ms=total_duration,
                span_count=span_count,
                error_count=error_count,
                critical_path_ms=critical_path_ms,
                bottleneck_spans=bottleneck_spans,
                performance_score=performance_score,
                suggestions=suggestions,
            )

        except Exception as e:
            self.logger.error(f"トレース分析実行エラー: {e}")
            return None

    def get_trace_analysis(self, trace_id: str) -> Optional[TraceAnalysis]:
        """トレース分析結果取得

        Args:
            trace_id: トレースID

        Returns:
            分析結果
        """
        return self.trace_analyses.get(trace_id)

    def get_active_spans(self) -> List[Dict[str, Any]]:
        """アクティブスパン一覧取得

        Returns:
            アクティブスパン一覧
        """
        try:
            with self.spans_lock:
                return [
                    {
                        "span_id": span_id,
                        "operation_name": span_data.operation_name,
                        "start_time": span_data.start_time,
                        "duration_ms": (time.time() - span_data.start_time) * 1000,
                        "trace_id": span_data.trace_id,
                        "tags": span_data.tags,
                    }
                    for span_id, span_data in self.active_spans.items()
                ]
        except Exception as e:
            self.logger.error(f"アクティブスパン取得エラー: {e}")
            return []

    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリ取得

        Returns:
            パフォーマンスサマリ
        """
        try:
            # 最近の分析結果統計
            recent_analyses = list(self.trace_analyses.values())[-10:]  # 最新10件

            avg_performance_score = 0.0
            if recent_analyses:
                avg_performance_score = sum(
                    a.performance_score for a in recent_analyses
                ) / len(recent_analyses)

            return {
                "total_spans": self.total_spans,
                "total_traces": self.total_traces,
                "active_spans": len(self.active_spans),
                "average_span_duration_ms": self.average_span_duration,
                "error_rate_percent": self.error_rate * 100,
                "average_performance_score": avg_performance_score,
                "recent_analyses_count": len(recent_analyses),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"パフォーマンスサマリ取得エラー: {e}")
            return {"error": str(e)}

    def export_trace_data(
        self, trace_id: Optional[str] = None, output_file: Optional[str] = None
    ) -> Optional[str]:
        """トレースデータエクスポート

        Args:
            trace_id: エクスポート対象トレースID（省略時は全て）
            output_file: 出力ファイル名

        Returns:
            出力ファイルパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if output_file is None:
                filename = f"trace_export_{trace_id or 'all'}_{timestamp}.json"
                output_file = os.path.join("tmp", filename)

            # エクスポートデータ構築
            export_data: Dict[str, Any] = {
                "export_timestamp": datetime.now().isoformat(),
                "service_name": self.service_name,
                "service_version": self.service_version,
                "traces": {},
                "analyses": {},
            }

            with self.spans_lock:
                if trace_id:
                    # 特定トレース
                    traces_dict = cast(Dict[str, Any], export_data["traces"])
                    analyses_dict = cast(Dict[str, Any], export_data["analyses"])

                    if trace_id in self.completed_traces:
                        traces_dict[trace_id] = [
                            asdict(span) for span in self.completed_traces[trace_id]
                        ]
                    if trace_id in self.trace_analyses:
                        analyses_dict[trace_id] = asdict(self.trace_analyses[trace_id])
                else:
                    # 全トレース
                    traces_dict = cast(Dict[str, Any], export_data["traces"])
                    analyses_dict = cast(Dict[str, Any], export_data["analyses"])

                    for tid, spans in self.completed_traces.items():
                        traces_dict[tid] = [asdict(span) for span in spans]
                    for tid, analysis in self.trace_analyses.items():
                        analyses_dict[tid] = asdict(analysis)

            # JSONファイル出力
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"トレースデータエクスポート完了: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"トレースデータエクスポートエラー: {e}")
            return None

    def cleanup_old_traces(self, max_age_hours: int = 24) -> int:
        """古いトレースデータクリーンアップ

        Args:
            max_age_hours: 最大保持時間（時間）

        Returns:
            削除されたトレース数
        """
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            deleted_count = 0

            with self.spans_lock:
                # 古いトレース削除
                for trace_id in list(self.completed_traces.keys()):
                    trace_spans = self.completed_traces[trace_id]
                    if trace_spans and trace_spans[0].start_time < cutoff_time:
                        del self.completed_traces[trace_id]
                        if trace_id in self.trace_analyses:
                            del self.trace_analyses[trace_id]
                        deleted_count += 1

            if deleted_count > 0:
                self.logger.info(
                    f"古いトレースクリーンアップ完了: {deleted_count}個削除"
                )

            return deleted_count

        except Exception as e:
            self.logger.error(f"トレースクリーンアップエラー: {e}")
            return 0

    def get_configuration_status(self) -> Dict[str, Any]:
        """設定状態取得

        Returns:
            設定状態情報
        """
        return {
            "jaeger_available": JAEGER_AVAILABLE,
            "initialized": self.initialized,
            "available": self.available,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "jaeger_endpoint": self.jaeger_endpoint,
            "sampling_rate": self.sampling_rate,
            "performance_analysis_enabled": self.enable_performance_analysis,
            "max_trace_retention": self.max_trace_retention,
            "active_spans_count": len(self.active_spans),
            "completed_traces_count": len(self.completed_traces),
            "trace_analyses_count": len(self.trace_analyses),
        }

    def force_flush(self, timeout_seconds: int = 30) -> bool:
        """強制フラッシュ

        Args:
            timeout_seconds: タイムアウト（秒）

        Returns:
            フラッシュ成功フラグ
        """
        if not self.available or not self.initialized or not self.tracer_provider:
            return False

        try:
            self.tracer_provider.force_flush(timeout_seconds * 1000)  # ミリ秒変換
            self.logger.info("Jaegerトレーサー強制フラッシュ完了")
            return True
        except Exception as e:
            self.logger.error(f"Jaegerトレーサー強制フラッシュエラー: {e}")
            return False

    def shutdown(self) -> None:
        """Jaegerトレーサー終了処理"""
        try:
            if not self.available:
                return

            # アクティブスパンを強制終了
            with self.spans_lock:
                for span_id in list(self.active_spans.keys()):
                    self.finish_span(span_id, status="SHUTDOWN")

            # 最終エクスポート
            if self.completed_traces:
                export_file = self.export_trace_data()
                if export_file:
                    self.logger.info(f"終了時トレースエクスポート: {export_file}")

            # 強制フラッシュ
            self.force_flush()

            # TracerProviderシャットダウン
            if self.tracer_provider:
                self.tracer_provider.shutdown()

            self.initialized = False
            self.logger.info("JaegerTracer終了処理完了")

        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")

    def __enter__(self) -> "JaegerTracer":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
