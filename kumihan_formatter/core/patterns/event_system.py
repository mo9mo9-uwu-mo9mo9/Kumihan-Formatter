"""イベント駆動アーキテクチャ統合システム

Issue #1170: パーサー間通信をイベント駆動で実現し疎結合化を促進する統合システム
"""

import asyncio
from typing import Any, Dict, List, Optional

from ..utilities.logger import get_logger
from .parser_events import ParserEventBus, get_parser_event_bus
from .parser_monitoring import ParserMonitor, DetailedParserLogger, get_parser_monitor, get_parser_logger
from .event_driven_parser import ParserCollaborationManager
from .async_parser import AsyncParserOrchestrator, get_async_orchestrator

logger = get_logger(__name__)


class EventDrivenArchitectureSystem:
    """イベント駆動アーキテクチャ統合システム"""
    
    def __init__(self):
        # コアコンポーネント
        self.event_bus = get_parser_event_bus()
        self.monitor = get_parser_monitor()
        self.logger_system = get_parser_logger()
        self.collaboration_manager = ParserCollaborationManager(self.event_bus)
        self.async_orchestrator = get_async_orchestrator()
        
        # システム状態
        self._initialized = False
        self._async_enabled = False
        
    async def initialize(self, async_workers: int = 3, enable_monitoring: bool = True) -> None:
        """システム初期化"""
        try:
            logger.info("Initializing Event-Driven Architecture System...")
            
            # 監視システム初期化
            if enable_monitoring:
                self.monitor.enable_monitoring()
                self.logger_system.enable_logging()
                
            # 協調システム初期化
            self.collaboration_manager.setup_event_handlers()
            
            # 非同期システム初期化
            if async_workers > 0:
                await self.async_orchestrator.start_workers(async_workers)
                self._async_enabled = True
                
            self._initialized = True
            
            # 初期化完了イベント発行
            from .parser_events import ParserEvent, ParserEventType, ParserEventData
            init_event = ParserEvent(
                event_type=ParserEventType.DEBUG_TRACE,
                data=ParserEventData(
                    parser_name="EventDrivenArchitectureSystem",
                    parser_type="system",
                    metadata={
                        "action": "system_initialized",
                        "async_workers": async_workers,
                        "monitoring_enabled": enable_monitoring
                    }
                )
            )
            self.event_bus.publish(init_event)
            
            logger.info("Event-Driven Architecture System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Event-Driven Architecture System: {e}")
            raise
            
    async def shutdown(self) -> None:
        """システム終了"""
        try:
            logger.info("Shutting down Event-Driven Architecture System...")
            
            # 非同期システム終了
            if self._async_enabled:
                await self.async_orchestrator.stop_workers()
                self._async_enabled = False
                
            # 監視システム終了
            self.monitor.disable_monitoring()
            self.logger_system.disable_logging()
            
            self._initialized = False
            
            logger.info("Event-Driven Architecture System shut down successfully")
            
        except Exception as e:
            logger.error(f"Failed to shutdown Event-Driven Architecture System: {e}")
            
    def register_parser(self, name: str, parser_instance: Any, 
                       enable_collaboration: bool = True,
                       enable_async: bool = True) -> None:
        """パーサー登録"""
        try:
            # 協調システムに登録
            if enable_collaboration:
                self.collaboration_manager.register_parser(name, parser_instance)
                
            # 非同期システムに登録
            if enable_async and self._async_enabled:
                self.async_orchestrator.register_parser(name, parser_instance)
                
            logger.info(f"Parser registered: {name} "
                       f"(collaboration: {enable_collaboration}, async: {enable_async})")
                       
        except Exception as e:
            logger.error(f"Failed to register parser {name}: {e}")
            
    def set_collaboration_rules(self, rules: Dict[str, List[str]]) -> None:
        """協調ルール設定"""
        for source, targets in rules.items():
            self.collaboration_manager.set_collaboration_rule(source, targets)
            
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "initialized": self._initialized,
            "async_enabled": self._async_enabled,
            "event_bus_status": self.event_bus.get_system_status(),
            "monitor_summary": self.monitor.get_system_summary(),
            "async_queue_status": self.async_orchestrator.get_queue_status() if self._async_enabled else None,
            "performance_metrics": self.event_bus.get_performance_metrics()
        }
        
    def get_health_report(self) -> Dict[str, Any]:
        """システムヘルスレポート"""
        status = self.get_system_status()
        alerts = self.monitor.get_alerts(unresolved_only=True, limit=10)
        
        # ヘルス判定
        health_score = 100
        issues = []
        
        if not status["initialized"]:
            health_score -= 50
            issues.append("System not initialized")
            
        if len(alerts) > 10:
            health_score -= 20
            issues.append(f"High alert count: {len(alerts)}")
            
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            health_score -= 30
            issues.append(f"Critical alerts: {len(critical_alerts)}")
            
        # ヘルス状態
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 70:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        else:
            health_status = "poor"
            
        return {
            "health_status": health_status,
            "health_score": health_score,
            "issues": issues,
            "alerts_count": len(alerts),
            "critical_alerts_count": len(critical_alerts),
            "system_uptime": status.get("uptime", "unknown"),
            "recommendations": self._generate_recommendations(issues, alerts)
        }
        
    def _generate_recommendations(self, issues: List[str], alerts: List[Any]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        if "System not initialized" in issues:
            recommendations.append("Initialize the system with initialize() method")
            
        if len(alerts) > 5:
            recommendations.append("Review and resolve active alerts")
            
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append("Address critical alerts immediately")
            
        return recommendations
        
    def enable_debug_mode(self) -> None:
        """デバッグモード有効化"""
        # より詳細なログ出力
        self.logger_system.set_log_level_filter(["debug", "info", "warning", "error", "critical"])
        
        # より厳しい監視閾値
        self.monitor.set_alert_threshold("max_processing_time", 2.0)
        self.monitor.set_alert_threshold("min_success_rate", 98.0)
        
        logger.info("Debug mode enabled")
        
    def disable_debug_mode(self) -> None:
        """デバッグモード無効化"""
        # 通常ログレベル
        self.logger_system.set_log_level_filter(["info", "warning", "error", "critical"])
        
        # 通常監視閾値
        self.monitor.set_alert_threshold("max_processing_time", 5.0)
        self.monitor.set_alert_threshold("min_success_rate", 95.0)
        
        logger.info("Debug mode disabled")


# グローバルシステムインスタンス
_global_event_system: Optional[EventDrivenArchitectureSystem] = None


def get_event_system() -> EventDrivenArchitectureSystem:
    """グローバルイベント駆動システム取得"""
    global _global_event_system
    if _global_event_system is None:
        _global_event_system = EventDrivenArchitectureSystem()
    return _global_event_system


async def initialize_event_driven_architecture(
    async_workers: int = 3,
    enable_monitoring: bool = True,
    collaboration_rules: Optional[Dict[str, List[str]]] = None
) -> EventDrivenArchitectureSystem:
    """イベント駆動アーキテクチャ初期化"""
    system = get_event_system()
    
    await system.initialize(async_workers, enable_monitoring)
    
    if collaboration_rules:
        system.set_collaboration_rules(collaboration_rules)
        
    logger.info("Event-driven architecture fully initialized")
    return system


def create_parser_collaboration_rules() -> Dict[str, List[str]]:
    """パーサー協調ルール例"""
    return {
        "UnifiedContentParser": ["UnifiedKeywordParser", "UnifiedBlockParser"],
        "UnifiedListParser": ["UnifiedContentParser"],
        "UnifiedKeywordParser": ["UnifiedBlockParser"],
        "UnifiedBlockParser": ["UnifiedKeywordParser"]
    }


# 便利関数
def setup_parser_with_events(parser_instance: Any, parser_name: str) -> Any:
    """パーサーにイベント機能を追加"""
    from .event_driven_parser import EventDrivenParserMixin
    
    # ミックスインを動的に追加
    class EventEnabledParser(EventDrivenParserMixin, parser_instance.__class__):
        pass
    
    # インスタンス変換
    enhanced_parser = EventEnabledParser()
    
    # 既存の属性をコピー
    for attr_name in dir(parser_instance):
        if not attr_name.startswith('_'):
            try:
                setattr(enhanced_parser, attr_name, getattr(parser_instance, attr_name))
            except (AttributeError, TypeError):
                pass
                
    # システムに登録
    system = get_event_system()
    system.register_parser(parser_name, enhanced_parser)
    
    return enhanced_parser