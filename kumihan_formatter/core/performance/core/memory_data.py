"""メモリ関連のデータクラス

Single Responsibility Principle適用: メモリメトリクス構造
Issue #476 Phase2対応 - パフォーマンスモジュール統合（クラス数制限対応）
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""

    timestamp: float
    total_memory: int  # バイト
    available_memory: int
    process_memory: int
    gc_objects: int
    gc_collections: List[int]  # 各世代のGC回数
    custom_objects: Dict[str, int] = field(default_factory=dict)

    @property
    def memory_mb(self) -> float:
        """メモリ使用量（MB）"""
        return self.process_memory / 1024 / 1024

    @property
    def available_mb(self) -> float:
        """利用可能メモリ（MB）"""
        return self.available_memory / 1024 / 1024

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "total_memory": self.total_memory,
            "available_memory": self.available_memory,
            "process_memory": self.process_memory,
            "memory_mb": self.memory_mb,
            "available_mb": self.available_mb,
            "gc_objects": self.gc_objects,
            "gc_collections": self.gc_collections,
            "custom_objects": self.custom_objects,
        }


@dataclass
class MemoryLeak:
    """メモリリーク情報"""

    object_type: str
    count_increase: int
    size_estimate: int
    first_detected: float
    last_detected: float
    severity: str = "unknown"  # low, medium, high, critical

    @property
    def age_seconds(self) -> float:
        """リーク検出からの経過時間"""
        return self.last_detected - self.first_detected

    @property
    def estimated_leak_rate(self) -> float:
        """推定リーク率（オブジェクト/秒）"""
        if self.age_seconds > 0:
            return self.count_increase / self.age_seconds
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "object_type": self.object_type,
            "count_increase": self.count_increase,
            "size_estimate": self.size_estimate,
            "first_detected": self.first_detected,
            "last_detected": self.last_detected,
            "severity": self.severity,
            "age_seconds": self.age_seconds,
            "estimated_leak_rate": self.estimated_leak_rate,
        }
