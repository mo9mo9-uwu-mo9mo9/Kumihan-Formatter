"""メモリ使用パターン分析器"""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from kumihan_formatter.core.utilities.logger import get_logger

from .snapshot import MemorySnapshot

if TYPE_CHECKING:
    from .core_profiler import MemoryProfiler

logger = get_logger(__name__)


class MemoryUsageAnalyzer:
    """
    メモリ使用量分析器（互換性ラッパー）

    新しい分割されたコンポーネントを使用して既存APIの互換性を保持します。
    """

    def __init__(self, memory_monitor: Optional[Any] = None) -> None:
        """
        メモリ使用量分析器を初期化します。

        Args:
            memory_monitor: メモリ監視インスタンス（オプション）
        """
        try:
            from .new_usage_analyzer import MemoryUsageAnalyzerNew

            # 新しい統合アナライザーを使用
            self._new_analyzer = MemoryUsageAnalyzerNew(memory_monitor)
            self._memory_monitor = memory_monitor

            logger.info("MemoryUsageAnalyzer（互換ラッパー）初期化完了")

        except Exception as e:
            logger.error(f"MemoryUsageAnalyzer初期化エラー: {str(e)}")
            raise

    def analyze_usage_patterns(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """使用パターン分析（メインエントリーポイント）"""
        try:
            return self._new_analyzer.analyze_usage_patterns(snapshots)

        except Exception as e:
            logger.error(f"使用パターン分析エラー: {str(e)}")
            return {}

    # 旧API互換メソッド群

    def _analyze_memory_trend(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """メモリトレンド分析"""
        return self._new_analyzer._analyze_memory_trend(snapshots)

    def _analyze_peaks(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """ピーク分析"""
        return self._new_analyzer._analyze_peaks(snapshots)

    def _analyze_fragmentation(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """断片化分析"""
        return self._new_analyzer._analyze_fragmentation(snapshots)

    def _analyze_object_distribution(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """オブジェクト分布分析"""
        return self._new_analyzer._analyze_object_distribution(snapshots)

    def _analyze_gc_efficiency(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """GC効率分析"""
        return self._new_analyzer._analyze_gc_efficiency(snapshots)

    def _calculate_gc_efficiency_score(self, snapshots: List[MemorySnapshot]) -> float:
        """GC効率スコア計算"""
        return self._new_analyzer._calculate_gc_efficiency_score(snapshots)

    def _identify_optimization_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """最適化機会を特定"""
        return self._new_analyzer._identify_optimization_opportunities(snapshots)

    # 新機能への橋渡し
    def generate_comprehensive_report(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """包括的な分析レポートを生成"""
        return self._new_analyzer.generate_comprehensive_report(snapshots)

    @property
    def trend_analyzer(self) -> Any:
        """トレンド分析器"""
        return self._new_analyzer.trend_analyzer

    @property
    def object_analyzer(self) -> Any:
        """オブジェクト分析器"""
        return self._new_analyzer.object_analyzer

    @property
    def gc_analyzer(self) -> Any:
        """GC分析器"""
        return self._new_analyzer.gc_analyzer

    @property
    def optimization_advisor(self) -> Any:
        """最適化アドバイザー"""
        return self._new_analyzer.optimization_advisor
