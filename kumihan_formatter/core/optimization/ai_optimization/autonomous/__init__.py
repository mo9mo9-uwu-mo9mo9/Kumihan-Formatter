"""
Autonomous Control System Package

自律制御システムパッケージ統合インポート
Phase B.4-Beta自律制御システムの後方互換性維持
"""

# 制御システム
from .controller import (
    AutonomousController,
)

# 監視システム・データクラス
from .monitoring import (
    AnomalyEvent,
    AnomalyType,
    SystemMetrics,
    SystemMonitor,
    SystemState,
)

# 復旧システム
from .recovery import (
    AutoRecoveryEngine,
    RecoveryAction,
)

# 後方互換性のための統合インポート
__all__ = [
    # Data Classes
    "SystemState",
    "AnomalyType",
    "SystemMetrics",
    "AnomalyEvent",
    "RecoveryAction",
    # Core Components
    "SystemMonitor",
    "AutoRecoveryEngine",
    "AutonomousController",
]

# パッケージ情報
__version__ = "1.0.0"
__description__ = "Phase B.4-Beta Autonomous Control System"
