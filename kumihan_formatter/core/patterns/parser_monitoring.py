"""パーサー監視・ログシステム

Issue #1170: パーサー操作監視、詳細ログ出力、パフォーマンス計測の実装
"""

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ..utilities.logger import get_logger
from .parser_events import ParserEvent, ParserEventBus, ParserEventType, get_parser_event_bus

logger = get_logger(__name__)


@dataclass
class ParserMetrics:
    """パーサーメトリクス"""
    parser_name: str
    total_parses: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    max_processing_time: float = 0.0
    memory_usage_peak: int = 0
    error_count: int = 0
    last_active: Optional[datetime] = None
    
    def update_success(self, processing_time: float) -> None:
        """成功時のメトリクス更新"""
        self.total_parses += 1
        self.successful_parses += 1
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.total_parses
        self.min_processing_time = min(self.min_processing_time, processing_time)
        self.max_processing_time = max(self.max_processing_time, processing_time)
        self.last_active = datetime.now()
        
    def update_failure(self) -> None:
        """失敗時のメトリクス更新"""
        self.total_parses += 1
        self.failed_parses += 1
        self.error_count += 1
        self.last_active = datetime.now()
        
    def get_success_rate(self) -> float:
        """成功率取得"""
        if self.total_parses == 0:
            return 0.0
        return (self.successful_parses / self.total_parses) * 100


@dataclass
class ParserAlert:
    """パーサーアラート"""
    alert_type: str
    parser_name: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    details: Dict[str, Any]
    resolved: bool = False


class ParserMonitor:
    """パーサー監視システム"""
    
    def __init__(self, event_bus: Optional[ParserEventBus] = None):
        self.event_bus = event_bus or get_parser_event_bus()
        self._metrics: Dict[str, ParserMetrics] = {}
        self._alerts: List[ParserAlert] = []
        self._monitoring_enabled = True
        self._alert_thresholds = {
            "max_processing_time": 5.0,  # 5秒
            "max_error_rate": 10.0,  # 10%
            "max_memory_usage": 100 * 1024 * 1024,  # 100MB
            "min_success_rate": 95.0  # 95%
        }
        self._setup_event_handlers()
        
    def _setup_event_handlers(self) -> None:
        """イベントハンドラー設定"""
        self.event_bus.subscribe(ParserEventType.PARSE_STARTED, self)
        self.event_bus.subscribe(ParserEventType.PARSE_COMPLETED, self)
        self.event_bus.subscribe(ParserEventType.PARSE_FAILED, self)
        self.event_bus.subscribe(ParserEventType.RECOVERABLE_ERROR, self)
        self.event_bus.subscribe(ParserEventType.CRITICAL_ERROR, self)
        self.event_bus.subscribe(ParserEventType.PERFORMANCE_METRIC, self)
        
    def handle_parser_event(self, event: ParserEvent) -> None:
        """パーサーイベント処理"""
        if not self._monitoring_enabled:
            return
            
        parser_name = event.data.parser_name
        
        # メトリクス初期化
        if parser_name not in self._metrics:
            self._metrics[parser_name] = ParserMetrics(parser_name=parser_name)
            
        metrics = self._metrics[parser_name]
        
        # イベント種別ごとの処理
        if event.event_type == ParserEventType.PARSE_COMPLETED:
            processing_time = event.data.processing_time or 0.0
            metrics.update_success(processing_time)
            self._check_performance_alerts(parser_name, processing_time)
            
        elif event.event_type in [ParserEventType.PARSE_FAILED, ParserEventType.RECOVERABLE_ERROR, ParserEventType.CRITICAL_ERROR]:
            metrics.update_failure()
            self._create_error_alert(parser_name, event)
            
        elif event.event_type == ParserEventType.PERFORMANCE_METRIC:
            self._handle_performance_metric(parser_name, event)
            
        # 成功率チェック
        self._check_success_rate_alerts(parser_name)
        
    def _check_performance_alerts(self, parser_name: str, processing_time: float) -> None:
        """パフォーマンスアラートチェック"""
        if processing_time > self._alert_thresholds["max_processing_time"]:
            alert = ParserAlert(
                alert_type="performance",
                parser_name=parser_name,
                message=f"Processing time exceeded threshold: {processing_time:.2f}s",
                severity="warning",
                timestamp=datetime.now(),
                details={"processing_time": processing_time, "threshold": self._alert_thresholds["max_processing_time"]}
            )
            self._add_alert(alert)
            
    def _check_success_rate_alerts(self, parser_name: str) -> None:
        """成功率アラートチェック"""
        metrics = self._metrics[parser_name]
        success_rate = metrics.get_success_rate()
        
        if success_rate < self._alert_thresholds["min_success_rate"] and metrics.total_parses >= 10:
            alert = ParserAlert(
                alert_type="success_rate",
                parser_name=parser_name,
                message=f"Success rate below threshold: {success_rate:.1f}%",
                severity="error",
                timestamp=datetime.now(),
                details={"success_rate": success_rate, "threshold": self._alert_thresholds["min_success_rate"]}
            )
            self._add_alert(alert)
            
    def _create_error_alert(self, parser_name: str, event: ParserEvent) -> None:
        """エラーアラート作成"""
        severity = "critical" if event.event_type == ParserEventType.CRITICAL_ERROR else "warning"
        error_details = event.data.error_details or {}
        
        alert = ParserAlert(
            alert_type="error",
            parser_name=parser_name,
            message=f"Parser error: {error_details.get('error_message', 'Unknown error')}",
            severity=severity,
            timestamp=datetime.now(),
            details=error_details
        )
        self._add_alert(alert)
        
    def _handle_performance_metric(self, parser_name: str, event: ParserEvent) -> None:
        """パフォーマンス指標処理"""
        metadata = event.data.metadata or {}
        metric_name = metadata.get("metric_name")
        metric_value = metadata.get("metric_value")
        
        if metric_name == "memory_usage" and isinstance(metric_value, (int, float)):
            metrics = self._metrics[parser_name]
            metrics.memory_usage_peak = max(metrics.memory_usage_peak, int(metric_value))
            
            if metric_value > self._alert_thresholds["max_memory_usage"]:
                alert = ParserAlert(
                    alert_type="memory",
                    parser_name=parser_name,
                    message=f"Memory usage exceeded threshold: {metric_value / 1024 / 1024:.1f}MB",
                    severity="warning",
                    timestamp=datetime.now(),
                    details={"memory_usage": metric_value, "threshold": self._alert_thresholds["max_memory_usage"]}
                )
                self._add_alert(alert)
                
    def _add_alert(self, alert: ParserAlert) -> None:
        """アラート追加"""
        self._alerts.append(alert)
        
        # ログ出力
        log_level = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical
        }.get(alert.severity, logger.info)
        
        log_level(f"Parser Alert [{alert.alert_type}] {alert.parser_name}: {alert.message}")
        
        # 古いアラートの削除（最大1000件）
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
            
    def get_metrics(self, parser_name: Optional[str] = None) -> Dict[str, Any]:
        """メトリクス取得"""
        if parser_name:
            return self._metrics.get(parser_name, ParserMetrics(parser_name=parser_name)).__dict__
        else:
            return {name: metrics.__dict__ for name, metrics in self._metrics.items()}
            
    def get_alerts(self, 
                  parser_name: Optional[str] = None,
                  severity: Optional[str] = None,
                  unresolved_only: bool = True,
                  limit: Optional[int] = None) -> List[ParserAlert]:
        """アラート取得"""
        alerts = self._alerts
        
        if parser_name:
            alerts = [a for a in alerts if a.parser_name == parser_name]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        if limit:
            alerts = alerts[-limit:]
            
        return alerts
        
    def get_system_summary(self) -> Dict[str, Any]:
        """システム概要取得"""
        total_parsers = len(self._metrics)
        total_alerts = len([a for a in self._alerts if not a.resolved])
        critical_alerts = len([a for a in self._alerts if a.severity == "critical" and not a.resolved])
        
        # 最もアクティブなパーサー
        most_active = max(self._metrics.items(), 
                         key=lambda x: x[1].total_parses,
                         default=(None, None))
        
        # 平均成功率
        if self._metrics:
            avg_success_rate = sum(m.get_success_rate() for m in self._metrics.values()) / len(self._metrics)
        else:
            avg_success_rate = 0.0
            
        return {
            "total_parsers": total_parsers,
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "most_active_parser": most_active[0] if most_active[0] else None,
            "avg_success_rate": avg_success_rate,
            "monitoring_enabled": self._monitoring_enabled
        }
        
    def resolve_alert(self, alert_index: int) -> bool:
        """アラート解決"""
        try:
            if 0 <= alert_index < len(self._alerts):
                self._alerts[alert_index].resolved = True
                return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
        return False
        
    def clear_resolved_alerts(self) -> int:
        """解決済みアラートクリア"""
        initial_count = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.resolved]
        return initial_count - len(self._alerts)
        
    def set_alert_threshold(self, threshold_name: str, value: float) -> None:
        """アラート閾値設定"""
        if threshold_name in self._alert_thresholds:
            self._alert_thresholds[threshold_name] = value
            logger.info(f"Alert threshold updated: {threshold_name} = {value}")
        else:
            logger.warning(f"Unknown threshold: {threshold_name}")
            
    def enable_monitoring(self) -> None:
        """監視有効化"""
        self._monitoring_enabled = True
        logger.info("Parser monitoring enabled")
        
    def disable_monitoring(self) -> None:
        """監視無効化"""
        self._monitoring_enabled = False
        logger.info("Parser monitoring disabled")
        
    def get_handled_event_types(self) -> List[ParserEventType]:
        """処理対象イベント種別"""
        return [
            ParserEventType.PARSE_STARTED,
            ParserEventType.PARSE_COMPLETED,
            ParserEventType.PARSE_FAILED,
            ParserEventType.RECOVERABLE_ERROR,
            ParserEventType.CRITICAL_ERROR,
            ParserEventType.PERFORMANCE_METRIC
        ]


class DetailedParserLogger:
    """詳細パーサーログ出力システム"""
    
    def __init__(self, event_bus: Optional[ParserEventBus] = None):
        self.event_bus = event_bus or get_parser_event_bus()
        self._log_enabled = True
        self._log_level_filter = set(["info", "warning", "error", "critical"])
        self._setup_event_handlers()
        
    def _setup_event_handlers(self) -> None:
        """イベントハンドラー設定"""
        # 全イベント種別を監視
        for event_type in ParserEventType:
            self.event_bus.subscribe(event_type, self)
            
    def handle_parser_event(self, event: ParserEvent) -> None:
        """パーサーイベントの詳細ログ出力"""
        if not self._log_enabled:
            return
            
        timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parser_name = event.data.parser_name
        event_type = event.event_type.value
        
        # 基本情報
        log_message = f"[{timestamp}] {parser_name}:{event_type}"
        
        # イベント種別ごとの詳細情報
        if event.event_type == ParserEventType.PARSE_STARTED:
            content_hash = event.data.content_hash
            log_message += f" | Content: {content_hash or 'N/A'}"
            
        elif event.event_type == ParserEventType.PARSE_COMPLETED:
            processing_time = event.data.processing_time
            metadata = event.data.metadata or {}
            log_message += f" | Time: {processing_time:.4f}s"
            if "line_count" in metadata:
                log_message += f" | Lines: {metadata['line_count']}"
                
        elif event.event_type in [ParserEventType.RECOVERABLE_ERROR, ParserEventType.CRITICAL_ERROR]:
            error_details = event.data.error_details or {}
            error_type = error_details.get("error_type", "Unknown")
            error_message = error_details.get("error_message", "")
            log_message += f" | Error: {error_type} - {error_message}"
            
        elif event.event_type == ParserEventType.PERFORMANCE_METRIC:
            metadata = event.data.metadata or {}
            metric_name = metadata.get("metric_name", "unknown")
            metric_value = metadata.get("metric_value", 0)
            unit = metadata.get("unit", "")
            log_message += f" | {metric_name}: {metric_value}{unit}"
            
        # 協調イベント
        if event.source_parser or event.target_parser:
            source = event.source_parser or "unknown"
            target = event.target_parser or "unknown"
            log_message += f" | {source} -> {target}"
            
        # 優先度
        if event.priority > 1:
            log_message += f" | Priority: {event.priority}"
            
        logger.info(log_message)
        
    def get_handled_event_types(self) -> List[ParserEventType]:
        """処理対象イベント種別（全て）"""
        return list(ParserEventType)
        
    def set_log_level_filter(self, levels: List[str]) -> None:
        """ログレベルフィルター設定"""
        self._log_level_filter = set(levels)
        
    def enable_logging(self) -> None:
        """ログ出力有効化"""
        self._log_enabled = True
        
    def disable_logging(self) -> None:
        """ログ出力無効化"""
        self._log_enabled = False


# グローバル監視システム
_global_parser_monitor: Optional[ParserMonitor] = None
_global_parser_logger: Optional[DetailedParserLogger] = None


def get_parser_monitor() -> ParserMonitor:
    """グローバルパーサー監視システム取得"""
    global _global_parser_monitor
    if _global_parser_monitor is None:
        _global_parser_monitor = ParserMonitor()
    return _global_parser_monitor


def get_parser_logger() -> DetailedParserLogger:
    """グローバルパーサーログシステム取得"""
    global _global_parser_logger
    if _global_parser_logger is None:
        _global_parser_logger = DetailedParserLogger()
    return _global_parser_logger


def initialize_parser_monitoring() -> None:
    """パーサー監視システム初期化"""
    monitor = get_parser_monitor()
    logger_system = get_parser_logger()
    logger.info("Parser monitoring system initialized")