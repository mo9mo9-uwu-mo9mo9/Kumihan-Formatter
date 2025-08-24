"""メモリスナップショット関連のデータクラス"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""

    timestamp: float
    process_memory_mb: float
    virtual_memory_mb: float
    memory_percent: float
    gc_stats: List[Dict[str, Any]]
    object_counts: Dict[str, int]
    top_objects: List[Tuple[str, int, int]]  # (type, count, size)
    fragmentation_ratio: float


@dataclass
class MemoryLeakInfo:
    """メモリリーク情報"""

    object_type: str
    leak_rate_mb_per_sec: float
    total_leaked_mb: float
    detection_time: float
    confidence_score: float
    growth_pattern: List[float]
