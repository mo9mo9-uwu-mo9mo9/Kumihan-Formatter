"""パフォーマンス監視システムのメトリクスデータクラス

Single Responsibility Principle適用: メトリクスデータ構造の定義
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


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


@dataclass
class OptimizationMetrics:
    """最適化メトリクス"""

    name: str
    before_value: float
    after_value: float
    improvement_percent: float
    improvement_absolute: float
    significance: str  # low, medium, high, critical
    category: str  # performance, memory, cache, etc.

    @property
    def is_improvement(self) -> bool:
        """改善があったかどうか"""
        return self.improvement_percent > 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "improvement_percent": self.improvement_percent,
            "improvement_absolute": self.improvement_absolute,
            "significance": self.significance,
            "category": self.category,
            "is_improvement": self.is_improvement,
        }


@dataclass
class OptimizationReport:
    """最適化レポート"""

    timestamp: str
    optimization_name: str
    total_improvement_score: float
    metrics: List[OptimizationMetrics]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    regression_warnings: List[str]

    def get_metrics_by_category(self, category: str) -> List[OptimizationMetrics]:
        """カテゴリ別メトリクスを取得"""
        return [m for m in self.metrics if m.category == category]

    def get_significant_improvements(self) -> List[OptimizationMetrics]:
        """重要な改善を取得"""
        return [
            m
            for m in self.metrics
            if m.significance in ["high", "critical"] and m.is_improvement
        ]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "optimization_name": self.optimization_name,
            "total_improvement_score": self.total_improvement_score,
            "metrics": [m.to_dict() for m in self.metrics],
            "performance_summary": self.performance_summary,
            "recommendations": self.recommendations,
            "regression_warnings": self.regression_warnings,
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


# メトリクス操作のユーティリティ関数
def merge_cache_stats(stats_list: List[CacheStats]) -> CacheStats:
    """複数のキャッシュ統計をマージ

    Args:
        stats_list: マージするキャッシュ統計のリスト

    Returns:
        マージされたキャッシュ統計
    """
    if not stats_list:
        return CacheStats()

    merged = CacheStats()
    for stats in stats_list:
        merged.hits += stats.hits
        merged.misses += stats.misses
        merged.evictions += stats.evictions
        merged.size += stats.size
        merged.max_size = max(merged.max_size, stats.max_size)

    return merged


def calculate_improvement_percentage(before: float, after: float) -> float:
    """改善率を計算

    Args:
        before: 最適化前の値
        after: 最適化後の値

    Returns:
        改善率（パーセント）
    """
    if before == 0:
        return 0.0
    return ((before - after) / before) * 100.0


def determine_significance(improvement_percent: float) -> str:
    """改善の重要度を判定

    Args:
        improvement_percent: 改善率

    Returns:
        重要度レベル
    """
    abs_improvement = abs(improvement_percent)
    if abs_improvement >= 50:
        return "critical"
    elif abs_improvement >= 20:
        return "high"
    elif abs_improvement >= 5:
        return "medium"
    else:
        return "low"
