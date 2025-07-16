"""
メモリ監視データ型定義 - 基本データ構造

MemorySnapshotとMemoryLeakのデータクラス定義
Issue #402対応 - パフォーマンス最適化
"""

from dataclasses import dataclass, field
from typing import Dict

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# メモリ監視の定数
MEMORY_ALERT_THRESHOLDS = {
    "warning": 0.80,  # 80%でwarning
    "critical": 0.90,  # 90%でcritical
}

LEAK_SEVERITY_THRESHOLDS = {
    "low": 10,      # オブジェクト数増加
    "medium": 50,   
    "high": 100,    
    "critical": 500,
}

GC_OPTIMIZATION_THRESHOLDS = {
    "generation_0": 700,    # デフォルト700
    "generation_1": 10,     # デフォルト10
    "generation_2": 10,     # デフォルト10
}


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""

    timestamp: float
    total_memory: int  # バイト
    available_memory: int
    process_memory: int
    gc_objects: int
    gc_collections: list[int]  # 各世代のGC回数
    custom_objects: Dict[str, int] = field(default_factory=dict)

    @property
    def memory_mb(self) -> float:
        """メモリ使用量（MB）"""
        return self.process_memory / 1024 / 1024

    @property
    def available_mb(self) -> float:
        """利用可能メモリ（MB）"""
        return self.available_memory / 1024 / 1024

    @property
    def memory_usage_ratio(self) -> float:
        """メモリ使用率（0.0-1.0）"""
        if self.total_memory > 0:
            return (self.total_memory - self.available_memory) / self.total_memory
        return 0.0

    @property
    def is_memory_critical(self) -> bool:
        """メモリ使用量がクリティカルレベルか"""
        return self.memory_usage_ratio >= MEMORY_ALERT_THRESHOLDS["critical"]

    @property
    def is_memory_warning(self) -> bool:
        """メモリ使用量がワーニングレベルか"""
        return self.memory_usage_ratio >= MEMORY_ALERT_THRESHOLDS["warning"]


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
        return 0.0

    @property
    def severity_score(self) -> int:
        """深刻度スコア（数値）"""
        severity_scores = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
            "unknown": 0,
        }
        return severity_scores.get(self.severity, 0)

    @property
    def size_estimate_mb(self) -> float:
        """推定サイズ（MB）"""
        return self.size_estimate / 1024 / 1024

    def is_critical_leak(self) -> bool:
        """クリティカルなリークかどうか"""
        return (
            self.severity == "critical" 
            or self.count_increase >= LEAK_SEVERITY_THRESHOLDS["critical"]
            or self.estimated_leak_rate > 10.0  # 10オブジェクト/秒以上
        )


# 便利な型エイリアス
MemoryStats = Dict[str, float]
ObjectCounts = Dict[str, int]
GCStats = Dict[str, int]