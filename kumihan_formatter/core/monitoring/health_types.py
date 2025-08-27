"""
ヘルスチェックシステム - 基本型・データクラス定義

ヘルス状態、アラート、チェック結果のデータ型群
health_checker.pyから分離（Issue: 巨大ファイル分割 - 909行→200行程度）
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class HealthStatus(Enum):
    """ヘルス状態列挙型"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """アラート重要度列挙型"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果データ"""

    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration_ms: float
    details: Dict[str, Any]
    suggestions: List[str]


@dataclass
class HealthAlert:
    """ヘルスアラートデータ"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: float
    resolved: bool
    resolution_time: Optional[float]
    metadata: Dict[str, Any]


__all__ = ["HealthStatus", "AlertSeverity", "HealthCheckResult", "HealthAlert"]