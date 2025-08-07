"""
Phase B.4-Beta自律制御システム（統合インポート）

後方互換性維持のための統合インポートファイル
元の1704行ファイルを3つのモジュールに分割：
- autonomous/monitoring.py: SystemMonitor + データ定義
- autonomous/recovery.py: AutoRecoveryEngine + RecoveryAction
- autonomous/controller.py: AutonomousController

24時間365日自律最適化・異常検出・自動復旧
- 完全自律的最適化制御・人間介入最小化
- 異常検出・即座対応・自動復旧・ロールバック
- システム性能継続監視・維持・効率低下検出
- 自動復旧機能・安定性確保・1.0-1.5%削減効果
"""

# 後方互換性維持のため、分割されたモジュールから全てインポート
from .autonomous import (  # Data Classes; Core Components
    AnomalyEvent,
    AnomalyType,
    AutonomousController,
    AutoRecoveryEngine,
    RecoveryAction,
    SystemMetrics,
    SystemMonitor,
    SystemState,
)

# 元のインポートパターンを維持
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

# バージョン情報
__version__ = "1.0.0-split"
__description__ = "Phase B.4-Beta Autonomous Control System (Modularized)"

# 分割完了情報
__split_info__ = {
    "original_size": "1704 lines",
    "split_date": "2025-01-08",
    "modules": {
        "monitoring.py": "~530 lines - SystemMonitor + Data Classes",
        "recovery.py": "~514 lines - AutoRecoveryEngine + RecoveryAction",
        "controller.py": "~660 lines - AutonomousController",
        "__init__.py": "Integration imports",
    },
    "benefits": [
        "Improved maintainability",
        "Reduced file complexity",
        "Enhanced modularity",
        "Better code organization",
        "Preserved backward compatibility",
    ],
}
