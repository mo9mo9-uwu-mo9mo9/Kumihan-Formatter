"""ベンチマーク関連のデータクラス

Single Responsibility Principle適用: ベンチマークメトリクス構造
Issue #476 Phase2対応 - パフォーマンスモジュール統合（クラス数制限対応）
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    memory_usage: Dict[str, float]
    cache_stats: Dict[str, Any]
    throughput: float | None = None
    regression_score: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "std_dev": self.std_dev,
            "memory_usage": self.memory_usage,
            "cache_stats": self.cache_stats,
            "throughput": self.throughput,
            "regression_score": self.regression_score,
        }


@dataclass
class BenchmarkConfig:
    """ベンチマーク設定"""

    iterations: int = 5
    warmup_iterations: int = 2
    enable_profiling: bool = True
    enable_memory_monitoring: bool = True
    cache_enabled: bool = True
    baseline_file: str | None = None  # Pathではなく文字列に変更

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "enable_profiling": self.enable_profiling,
            "enable_memory_monitoring": self.enable_memory_monitoring,
            "cache_enabled": self.cache_enabled,
            "baseline_file": self.baseline_file,
        }


@dataclass
class CacheStats:
    """キャッシュ統計"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """ヒット率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """ミス率"""
        return 1.0 - self.hit_rate

    @property
    def utilization(self) -> float:
        """キャッシュ使用率"""
        return self.size / self.max_size if self.max_size > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "utilization": self.utilization,
        }


@dataclass
class ProfileData:
    """プロファイリングデータ"""

    function_name: str
    total_time: float
    call_count: int
    avg_time: float
    file_path: str
    line_number: int

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "function_name": self.function_name,
            "total_time": self.total_time,
            "call_count": self.call_count,
            "avg_time": self.avg_time,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }
