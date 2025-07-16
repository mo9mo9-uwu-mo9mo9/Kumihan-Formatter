"""ベンチマーク結果分析エンジン

Single Responsibility Principle適用: 結果分析・比較・レポート生成の責任分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

from ...utilities.logger import get_logger
from ..core.base import PerformanceMetric
from ..core.metrics import BenchmarkResult
from ..core.persistence import BaselineManager


class BenchmarkAnalyzer:
    """ベンチマーク結果分析エンジン

    機能:
    - ベンチマーク結果の統計分析
    - ベースラインとの比較
    - レポート生成
    """

    def __init__(self, baseline_manager: BaselineManager) -> None:
        """分析エンジンを初期化

        Args:
            baseline_manager: ベースライン管理インスタンス
        """
        self.baseline_manager = baseline_manager
        self.logger = get_logger(__name__)

    def analyze_results(
        self,
        name: str,
        times: List[float],
        total_time: float,
        memory_usage: Dict[str, float],
        cache_stats: Dict[str, Any],
    ) -> BenchmarkResult:
        """ベンチマーク結果を分析

        Args:
            name: ベンチマーク名
            times: 各イテレーションの実行時間
            total_time: 総実行時間
            memory_usage: メモリ使用量
            cache_stats: キャッシュ統計

        Returns:
            分析済みベンチマーク結果
        """
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # スループットの計算（必要に応じて）
        throughput = None
        if "operations" in cache_stats:
            throughput = cache_stats["operations"] / total_time

        return BenchmarkResult(
            name=name,
            iterations=len(times),
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cache_stats=cache_stats,
            throughput=throughput,
            regression_score=None,  # 回帰スコアは別途計算
        )

    def compare_with_baseline(
        self, results: List[BenchmarkResult], baseline_name: str
    ) -> Dict[str, Any]:
        """ベースラインと比較

        Args:
            results: 比較対象のベンチマーク結果
            baseline_name: ベースライン名

        Returns:
            比較結果
        """
        baseline_data = self.baseline_manager.load_baseline(baseline_name)
        if not baseline_data:
            self.logger.warning(f"Baseline '{baseline_name}' not found")
            return {}

        comparison_results = {}
        baseline_results = baseline_data.get("data", {}).get("results", [])

        for current_result in results:
            # 対応するベースライン結果を探す
            baseline_result = None
            for br in baseline_results:
                if br.get("name") == current_result.name:
                    baseline_result = br
                    break

            if baseline_result:
                comparison = self._compare_single_result(
                    current_result, baseline_result
                )
                comparison_results[current_result.name] = comparison

        return comparison_results

    def _compare_single_result(
        self, current: BenchmarkResult, baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """単一の結果を比較

        Args:
            current: 現在の結果
            baseline: ベースライン結果

        Returns:
            比較結果
        """
        baseline_avg = baseline.get("avg_time", 0)
        if baseline_avg == 0:
            return {}

        improvement = ((baseline_avg - current.avg_time) / baseline_avg) * 100
        speedup = baseline_avg / current.avg_time if current.avg_time > 0 else 0

        return {
            "improvement_percent": improvement,
            "speedup": speedup,
            "baseline_avg_time": baseline_avg,
            "current_avg_time": current.avg_time,
            "is_regression": improvement < -5,  # 5%以上遅くなったら回帰
        }

    def collect_metrics(
        self, results: List[BenchmarkResult]
    ) -> List[PerformanceMetric]:
        """メトリクスを収集

        Args:
            results: ベンチマーク結果のリスト

        Returns:
            収集されたメトリクス
        """
        metrics = []
        current_time = time.time()

        for result in results:
            # 実行時間メトリクス
            metrics.append(
                PerformanceMetric(
                    name=f"{result.name}_avg_time",
                    value=result.avg_time,
                    unit="seconds",
                    timestamp=current_time,
                    category="benchmark",
                    metadata={"benchmark_name": result.name},
                )
            )

            # メモリ使用量メトリクス
            if result.memory_usage:
                for mem_name, mem_value in result.memory_usage.items():
                    metrics.append(
                        PerformanceMetric(
                            name=f"{result.name}_{mem_name}",
                            value=mem_value,
                            unit="MB" if "_mb" in mem_name else "count",
                            timestamp=current_time,
                            category="benchmark_memory",
                            metadata={"benchmark_name": result.name},
                        )
                    )

        return metrics

    def generate_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """ベンチマークレポートを生成

        Args:
            results: ベンチマーク結果のリスト

        Returns:
            レポートデータ
        """
        if not results:
            return {"message": "No benchmark results available"}

        # 結果のサマリー
        summary = {
            "total_benchmarks": len(results),
            "total_time": sum(r.total_time for r in results),
            "fastest": min(results, key=lambda r: r.avg_time).name,
            "slowest": max(results, key=lambda r: r.avg_time).name,
        }

        # 詳細結果
        detailed_results = []
        for result in results:
            detailed_results.append(
                {
                    "name": result.name,
                    "avg_time": result.avg_time,
                    "min_time": result.min_time,
                    "max_time": result.max_time,
                    "std_dev": result.std_dev,
                    "memory_usage": result.memory_usage,
                    "cache_hit_rate": (
                        result.cache_stats.get("hit_rate", 0)
                        if result.cache_stats
                        else 0
                    ),
                }
            )

        return {
            "summary": summary,
            "results": detailed_results,
        }


class BaselineHelper:
    """ベースライン管理とシステム情報収集"""

    def __init__(self, baseline_manager: BaselineManager) -> None:
        """ベースライン管理を初期化

        Args:
            baseline_manager: ベースライン管理インスタンス
        """
        self.baseline_manager = baseline_manager
        self.logger = get_logger(__name__)

    def save_as_baseline(
        self, name: str, results: List[BenchmarkResult], config_dict: Dict[str, Any]
    ) -> Path:
        """現在の結果をベースラインとして保存

        Args:
            name: ベースライン名
            results: ベンチマーク結果のリスト
            config_dict: ベンチマーク設定の辞書

        Returns:
            保存したファイルのパス
        """
        baseline_data = {
            "results": [result.to_dict() for result in results],
            "config": config_dict,
            "system_info": self._get_system_info(),
        }

        return self.baseline_manager.save_baseline(name, baseline_data)

    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得

        Returns:
            システム情報
        """
        from ..core.base import SystemInfo

        return SystemInfo.capture().to_dict()
