"""プロファイラー設定管理"""

from __future__ import annotations

from dataclasses import dataclass

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProfilerConfig:
    """プロファイラー設定"""

    snapshot_interval: int = 30  # スナップショット間隔（秒）
    leak_detection_window: int = 300  # リーク検出ウィンドウ（秒）
    memory_threshold_mb: float = 1000.0  # メモリ閾値（MB）
    fragmentation_threshold: float = 0.3  # 断片化閾値（30%）
    enable_tracemalloc: bool = True
    tracemalloc_limit: int = 100
