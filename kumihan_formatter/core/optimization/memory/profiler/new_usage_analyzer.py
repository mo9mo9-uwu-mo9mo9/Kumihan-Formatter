"""新しい統合メモリ使用量分析器"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger
from .analysis import (
    MemoryGCAnalyzer,
    MemoryObjectAnalyzer,
    MemoryOptimizationAdvisor,
    MemoryTrendAnalyzer,
)
from .snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryUsageAnalyzerNew:
    """
    新しいメモリ使用量分析器クラス

    各種分析コンポーネントを統合してメモリ使用パターンの詳細分析を提供します。
    """

    def __init__(self, memory_monitor: Optional[Any] = None) -> None:
        """
        メモリ使用量分析器を初期化します。

        Args:
            memory_monitor: メモリ監視インスタンス（オプション）
        """
        try:
            self._memory_monitor = memory_monitor

            # 分析コンポーネント初期化
            self._trend_analyzer = MemoryTrendAnalyzer()
            self._object_analyzer = MemoryObjectAnalyzer()
            self._gc_analyzer = MemoryGCAnalyzer()
            self._optimization_advisor = MemoryOptimizationAdvisor()

            logger.info("MemoryUsageAnalyzerNew初期化完了")

        except Exception as e:
            logger.error(f"MemoryUsageAnalyzerNew初期化エラー: {str(e)}")
            raise

    def analyze_usage_patterns(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """使用パターン分析（メインエントリーポイント）"""
        try:
            if not snapshots:
                logger.warning("スナップショットが存在しません")
                return {}

            logger.info(f"{len(snapshots)}個のスナップショットを分析中...")

            # 各種分析の実行
            analysis_results = {
                "memory_trend": self._trend_analyzer.analyze_memory_trend(snapshots),
                "memory_stability": self._trend_analyzer.analyze_memory_stability(
                    snapshots
                ),
                "peak_analysis": self._trend_analyzer.analyze_peaks(snapshots),
                "fragmentation_analysis": self._object_analyzer.analyze_fragmentation(
                    snapshots
                ),
                "object_distribution": self._object_analyzer.analyze_object_distribution(
                    snapshots
                ),
                "memory_patterns": self._object_analyzer.analyze_memory_patterns(
                    snapshots
                ),
                "gc_efficiency": self._gc_analyzer.analyze_gc_efficiency(snapshots),
                "gc_patterns": self._gc_analyzer.analyze_gc_patterns(snapshots),
                "optimization_opportunities": self._optimization_advisor.identify_optimization_opportunities(
                    snapshots
                ),
            }

            # 分析サマリー
            summary = self._create_analysis_summary(analysis_results)
            analysis_results["analysis_summary"] = summary

            logger.info("メモリ使用パターン分析完了")
            return analysis_results

        except Exception as e:
            logger.error(f"使用パターン分析エラー: {str(e)}")
            return {}

    def generate_comprehensive_report(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """包括的な分析レポートを生成"""
        try:
            return self._optimization_advisor.generate_comprehensive_report(snapshots)

        except Exception as e:
            logger.error(f"包括的レポート生成エラー: {str(e)}")
            return {}

    # 旧APIとの互換性維持のためのメソッド群

    def _analyze_memory_trend(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """メモリトレンド分析（互換性メソッド）"""
        return self._trend_analyzer.analyze_memory_trend(snapshots)

    def _analyze_peaks(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """ピーク分析（互換性メソッド）"""
        return self._trend_analyzer.analyze_peaks(snapshots)

    def _analyze_fragmentation(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """断片化分析（互換性メソッド）"""
        return self._object_analyzer.analyze_fragmentation(snapshots)

    def _analyze_object_distribution(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """オブジェクト分布分析（互換性メソッド）"""
        return self._object_analyzer.analyze_object_distribution(snapshots)

    def _analyze_gc_efficiency(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GC効率分析（互換性メソッド）"""
        return self._gc_analyzer.analyze_gc_efficiency(snapshots)

    def _calculate_gc_efficiency_score(self, snapshots: List[MemorySnapshot]) -> float:
        """GC効率スコア計算（互換性メソッド）"""
        try:
            gc_analysis = self._gc_analyzer.analyze_gc_efficiency(snapshots)
            return float(gc_analysis.get("gc_efficiency_score", 0.5))

        except Exception as e:
            logger.error(f"GC効率スコア計算エラー: {str(e)}")
            return 0.5

    def _identify_optimization_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """最適化機会特定（互換性メソッド）"""
        return self._optimization_advisor.identify_optimization_opportunities(snapshots)

    def _create_analysis_summary(
        self, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析結果のサマリーを作成"""
        try:
            summary: Dict[str, Any] = {
                "total_analyses_completed": len(
                    [k for k, v in analysis_results.items() if v]
                ),
                "memory_health_indicators": {},
                "key_findings": [],
                "recommendation_count": len(
                    analysis_results.get("optimization_opportunities", [])
                ),
            }

            # メモリヘルス指標
            trend = analysis_results.get("memory_trend", {})
            if trend:
                summary["memory_health_indicators"]["trend_direction"] = trend.get(
                    "trend_direction", "unknown"
                )
                summary["memory_health_indicators"]["memory_volatility"] = trend.get(
                    "memory_volatility", 0
                )

            stability = analysis_results.get("memory_stability", {})
            if stability:
                summary["memory_health_indicators"]["stability_score"] = stability.get(
                    "stability_score", 0
                )
                summary["memory_health_indicators"]["is_stable"] = stability.get(
                    "is_stable", False
                )

            fragmentation = analysis_results.get("fragmentation_analysis", {})
            if fragmentation:
                summary["memory_health_indicators"]["fragmentation_severity"] = (
                    fragmentation.get("fragmentation_severity", "unknown")
                )

            gc_efficiency = analysis_results.get("gc_efficiency", {})
            if gc_efficiency:
                summary["memory_health_indicators"]["gc_performance_level"] = (
                    gc_efficiency.get("gc_performance_level", "unknown")
                )

            # 主要な発見事項
            findings = []

            if trend.get("trend_direction") == "increasing":
                findings.append("メモリ使用量の継続的増加を検出")

            if not stability.get("is_stable", True):
                findings.append("メモリ使用量の不安定性を検出")

            if fragmentation.get("fragmentation_severity") in ["high", "critical"]:
                findings.append("深刻なメモリ断片化を検出")

            patterns = analysis_results.get("memory_patterns", {})
            if patterns.get("memory_leaks"):
                findings.append(
                    f"{len(patterns['memory_leaks'])}個の潜在的メモリリークを検出"
                )

            summary["key_findings"] = findings

            return summary

        except Exception as e:
            logger.error(f"分析サマリー作成エラー: {str(e)}")
            return {}

    @property
    def trend_analyzer(self) -> MemoryTrendAnalyzer:
        """トレンド分析器"""
        return self._trend_analyzer

    @property
    def object_analyzer(self) -> MemoryObjectAnalyzer:
        """オブジェクト分析器"""
        return self._object_analyzer

    @property
    def gc_analyzer(self) -> MemoryGCAnalyzer:
        """GC分析器"""
        return self._gc_analyzer

    @property
    def optimization_advisor(self) -> MemoryOptimizationAdvisor:
        """最適化アドバイザー"""
        return self._optimization_advisor
