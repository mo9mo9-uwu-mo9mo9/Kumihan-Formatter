"""メモリ最適化アドバイザー"""

from __future__ import annotations

from typing import Any, Dict, List

from kumihan_formatter.core.utilities.logger import get_logger
from ..snapshot import MemorySnapshot
from .trend_analyzer import MemoryTrendAnalyzer
from .object_analyzer import MemoryObjectAnalyzer
from .gc_analyzer import MemoryGCAnalyzer

logger = get_logger(__name__)


class MemoryOptimizationAdvisor:
    """
    メモリ最適化アドバイザークラス

    各種分析結果を統合して具体的な最適化提案を生成します。
    """

    def __init__(self) -> None:
        """最適化アドバイザーを初期化します。"""
        try:
            self._trend_analyzer = MemoryTrendAnalyzer()
            self._object_analyzer = MemoryObjectAnalyzer()
            self._gc_analyzer = MemoryGCAnalyzer()

            logger.info("MemoryOptimizationAdvisor初期化完了")

        except Exception as e:
            logger.error(f"MemoryOptimizationAdvisor初期化エラー: {str(e)}")
            raise

    def identify_optimization_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """最適化機会を特定"""
        try:
            opportunities: List[str] = []

            if not snapshots:
                return opportunities

            # トレンド分析に基づく推奨
            trend_recommendations = self._analyze_trend_opportunities(snapshots)
            opportunities.extend(trend_recommendations)

            # オブジェクト分析に基づく推奨
            object_recommendations = self._analyze_object_opportunities(snapshots)
            opportunities.extend(object_recommendations)

            # GC分析に基づく推奨
            gc_recommendations = self._analyze_gc_opportunities(snapshots)
            opportunities.extend(gc_recommendations)

            # パターン分析に基づく推奨
            pattern_recommendations = self._analyze_pattern_opportunities(snapshots)
            opportunities.extend(pattern_recommendations)

            return opportunities

        except Exception as e:
            logger.error(f"最適化機会特定エラー: {str(e)}")
            return []

    def generate_comprehensive_report(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """包括的な最適化レポートを生成"""
        try:
            if not snapshots:
                return {}

            # 各種分析実行
            trend_analysis = self._trend_analyzer.analyze_memory_trend(snapshots)
            stability_analysis = self._trend_analyzer.analyze_memory_stability(
                snapshots
            )
            fragmentation_analysis = self._object_analyzer.analyze_fragmentation(
                snapshots
            )
            object_analysis = self._object_analyzer.analyze_object_distribution(
                snapshots
            )
            gc_analysis = self._gc_analyzer.analyze_gc_efficiency(snapshots)

            # 総合スコア計算
            overall_score = self._calculate_overall_performance_score(
                {
                    "trend": trend_analysis,
                    "stability": stability_analysis,
                    "fragmentation": fragmentation_analysis,
                    "objects": object_analysis,
                    "gc": gc_analysis,
                }
            )

            # 優先度付き推奨事項
            prioritized_recommendations = self._prioritize_recommendations(snapshots)

            return {
                "overall_performance_score": overall_score,
                "performance_grade": self._get_performance_grade(overall_score),
                "analysis_summary": {
                    "memory_trend": trend_analysis,
                    "memory_stability": stability_analysis,
                    "fragmentation_analysis": fragmentation_analysis,
                    "object_distribution": object_analysis,
                    "gc_efficiency": gc_analysis,
                },
                "prioritized_recommendations": prioritized_recommendations,
                "quick_wins": self._identify_quick_wins(snapshots),
                "long_term_strategies": self._identify_long_term_strategies(snapshots),
            }

        except Exception as e:
            logger.error(f"包括的レポート生成エラー: {str(e)}")
            return {}

    def _analyze_trend_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """トレンド分析に基づく最適化機会"""
        try:
            recommendations = []

            trend_analysis = self._trend_analyzer.analyze_memory_trend(snapshots)

            # 継続的な成長パターン
            slope = trend_analysis.get("trend_slope_mb_per_snapshot", 0)
            if slope > 1.0:
                recommendations.append(
                    f"継続的なメモリ増加が検出されました（{slope:.2f}MB/スナップショット）。"
                    "メモリリークの調査を推奨します。"
                )

            # メモリ変動性
            volatility = trend_analysis.get("memory_volatility", 0)
            if volatility > 0.3:
                recommendations.append(
                    f"メモリ使用量の変動が激しいです（変動係数: {volatility:.2f}）。"
                    "メモリ使用パターンの安定化を検討してください。"
                )

            # 成長率
            growth_rate = trend_analysis.get("growth_rate_percent", 0)
            if growth_rate > 50:
                recommendations.append(
                    f"メモリ使用量が大幅に増加しています（{growth_rate:.1f}%）。"
                    "キャッシュサイズや一時オブジェクトの管理を見直してください。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"トレンド最適化機会分析エラー: {str(e)}")
            return []

    def _analyze_object_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """オブジェクト分析に基づく最適化機会"""
        try:
            recommendations = []

            fragmentation_analysis = self._object_analyzer.analyze_fragmentation(
                snapshots
            )
            object_analysis = self._object_analyzer.analyze_object_distribution(
                snapshots
            )

            # 断片化の深刻度
            fragmentation_severity = fragmentation_analysis.get(
                "fragmentation_severity", "low"
            )
            if fragmentation_severity in ["high", "critical"]:
                recommendations.append(
                    f"メモリ断片化が深刻です（レベル: {fragmentation_severity}）。"
                    "オブジェクトプールやメモリプールの導入を推奨します。"
                )

            # オブジェクト集中度
            concentration_ratio = object_analysis.get("concentration_ratio", 0)
            if concentration_ratio > 0.8:
                top_types = object_analysis.get("top_object_types", [])[:3]
                type_names = [name for name, _ in top_types]
                recommendations.append(
                    f"特定のオブジェクトタイプに偏っています（集中度: {concentration_ratio:.1%}）。"
                    f"主要タイプ: {', '.join(type_names)}。オブジェクトリサイクルを検討してください。"
                )

            # オブジェクトダイバーシティ
            diversity_score = object_analysis.get("diversity_score", 1.0)
            if diversity_score < 0.3:
                recommendations.append(
                    "オブジェクトタイプの多様性が低いです。"
                    "特定タイプのオブジェクト最適化に注力することで効果的な改善が期待できます。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"オブジェクト最適化機会分析エラー: {str(e)}")
            return []

    def _analyze_gc_opportunities(self, snapshots: List[MemorySnapshot]) -> List[str]:
        """GC分析に基づく最適化機会"""
        try:
            recommendations = []

            gc_analysis = self._gc_analyzer.analyze_gc_efficiency(snapshots)
            gc_recommendations = self._gc_analyzer.generate_gc_recommendations(
                snapshots
            )

            # GC効率スコア
            efficiency_score = gc_analysis.get("gc_efficiency_score", 1.0)
            if efficiency_score < 0.5:
                recommendations.append(
                    f"ガベージコレクションの効率が低下しています（スコア: {efficiency_score:.2f}）。"
                    "弱参照の活用や不要な参照の削除を推奨します。"
                )

            # GC頻度
            gc_frequency = gc_analysis.get("gc_frequency_per_second", 0)
            if gc_frequency > 10:
                recommendations.append(
                    f"GC頻度が高すぎます（{gc_frequency:.1f}回/秒）。"
                    "オブジェクト生成の削減やメモリプールの使用を検討してください。"
                )

            # GC推奨事項を追加
            recommendations.extend(gc_recommendations)

            return recommendations

        except Exception as e:
            logger.error(f"GC最適化機会分析エラー: {str(e)}")
            return []

    def _analyze_pattern_opportunities(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """パターン分析に基づく最適化機会"""
        try:
            recommendations = []

            pattern_analysis = self._object_analyzer.analyze_memory_patterns(snapshots)

            # 継続成長パターン
            if pattern_analysis.get("steady_growth", False):
                recommendations.append(
                    "継続的なメモリ成長パターンが検出されました。"
                    "定期的なメモリクリーンアップの実装を推奨します。"
                )

            # 周期的スパイク
            if pattern_analysis.get("periodic_spikes", False):
                recommendations.append(
                    "周期的なメモリスパイクが検出されました。"
                    "バッチ処理やキャッシュクリアのタイミング最適化を検討してください。"
                )

            # 潜在的リーク
            potential_leaks = pattern_analysis.get("memory_leaks", [])
            if potential_leaks:
                leak_types = ", ".join(potential_leaks[:5])
                recommendations.append(
                    f"潜在的なメモリリークが検出されました: {leak_types}。"
                    "これらのオブジェクトの生存期間を確認してください。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"パターン最適化機会分析エラー: {str(e)}")
            return []

    def _calculate_overall_performance_score(self, analyses: Dict[str, Any]) -> float:
        """総合性能スコアを計算"""
        try:
            scores = {}

            # トレンドスコア（安定性重視）
            trend_direction = analyses.get("trend", {}).get("trend_direction", "stable")
            volatility = analyses.get("trend", {}).get("memory_volatility", 0)
            trend_score = 1.0 if trend_direction == "stable" else 0.5
            trend_score *= max(0.0, 1.0 - volatility)
            scores["trend"] = trend_score

            # 安定性スコア
            stability_score = analyses.get("stability", {}).get("stability_score", 0.5)
            scores["stability"] = stability_score

            # 断片化スコア
            fragmentation = analyses.get("fragmentation", {}).get(
                "average_fragmentation", 0.5
            )
            fragmentation_score = max(0.0, 1.0 - fragmentation)
            scores["fragmentation"] = fragmentation_score

            # オブジェクト分散スコア
            diversity = analyses.get("objects", {}).get("diversity_score", 0.5)
            concentration = analyses.get("objects", {}).get("concentration_ratio", 0.5)
            object_score = (diversity + (1.0 - concentration)) / 2
            scores["objects"] = object_score

            # GCスコア
            gc_score = analyses.get("gc", {}).get("gc_efficiency_score", 0.5)
            scores["gc"] = gc_score

            # 重み付き平均
            weights = {
                "trend": 0.25,
                "stability": 0.20,
                "fragmentation": 0.20,
                "objects": 0.15,
                "gc": 0.20,
            }

            overall_score = sum(
                scores.get(key, 0.5) * weight for key, weight in weights.items()
            )

            return float(min(max(overall_score, 0.0), 1.0))

        except Exception as e:
            logger.error(f"総合性能スコア計算エラー: {str(e)}")
            return 0.5

    def _get_performance_grade(self, score: float) -> str:
        """性能グレードを取得"""
        try:
            if score >= 0.9:
                return "A+"
            elif score >= 0.8:
                return "A"
            elif score >= 0.7:
                return "B+"
            elif score >= 0.6:
                return "B"
            elif score >= 0.5:
                return "C+"
            elif score >= 0.4:
                return "C"
            elif score >= 0.3:
                return "D"
            else:
                return "F"

        except Exception as e:
            logger.error(f"性能グレード取得エラー: {str(e)}")
            return "N/A"

    def _prioritize_recommendations(
        self, snapshots: List[MemorySnapshot]
    ) -> List[Dict[str, Any]]:
        """推奨事項を優先度順に整理"""
        try:
            all_recommendations = self.identify_optimization_opportunities(snapshots)

            prioritized = []
            for i, recommendation in enumerate(all_recommendations):
                priority = self._calculate_recommendation_priority(recommendation)
                prioritized.append(
                    {
                        "recommendation": recommendation,
                        "priority": priority,
                        "category": self._categorize_recommendation(recommendation),
                    }
                )

            # 優先度順にソート
            def _get_priority(item: Dict[str, Any]) -> float:
                priority = item.get("priority", 0.0)
                return float(priority) if isinstance(priority, (int, float)) else 0.0
            
            prioritized.sort(key=_get_priority, reverse=True)

            return prioritized

        except Exception as e:
            logger.error(f"推奨事項優先度付けエラー: {str(e)}")
            return []

    def _calculate_recommendation_priority(self, recommendation: str) -> int:
        """推奨事項の優先度を計算"""
        try:
            high_priority_keywords = ["critical", "リーク", "深刻", "頻繁"]
            medium_priority_keywords = ["high", "推奨", "検討", "増加"]

            priority = 1  # デフォルト低優先度

            for keyword in high_priority_keywords:
                if keyword in recommendation:
                    priority = 3
                    break

            if priority == 1:
                for keyword in medium_priority_keywords:
                    if keyword in recommendation:
                        priority = 2
                        break

            return priority

        except Exception as e:
            logger.error(f"推奨事項優先度計算エラー: {str(e)}")
            return 1

    def _categorize_recommendation(self, recommendation: str) -> str:
        """推奨事項をカテゴリ分類"""
        try:
            if "GC" in recommendation or "ガベージコレクション" in recommendation:
                return "garbage_collection"
            elif "断片化" in recommendation or "fragmentation" in recommendation:
                return "fragmentation"
            elif "リーク" in recommendation or "leak" in recommendation:
                return "memory_leak"
            elif "オブジェクト" in recommendation or "object" in recommendation:
                return "object_management"
            elif "トレンド" in recommendation or "trend" in recommendation:
                return "usage_pattern"
            else:
                return "general"

        except Exception as e:
            logger.error(f"推奨事項カテゴリ分類エラー: {str(e)}")
            return "general"

    def _identify_quick_wins(self, snapshots: List[MemorySnapshot]) -> List[str]:
        """即効性のある改善案を特定"""
        try:
            quick_wins: List[str] = []

            if not snapshots:
                return quick_wins

            latest = snapshots[-1]

            # 強制GCで改善可能かチェック
            if latest.gc_stats:
                quick_wins.append("定期的な手動ガベージコレクションの実行")

            # 大量オブジェクトの簡単な削減
            if latest.object_counts:
                total_objects = sum(latest.object_counts.values())
                if total_objects > 100000:
                    quick_wins.append("一時オブジェクトの生存期間短縮")

            return quick_wins

        except Exception as e:
            logger.error(f"即効改善案特定エラー: {str(e)}")
            return []

    def _identify_long_term_strategies(
        self, snapshots: List[MemorySnapshot]
    ) -> List[str]:
        """長期的な戦略を特定"""
        try:
            strategies = []

            # アーキテクチャレベルの改善
            strategies.append("オブジェクトプールパターンの導入")
            strategies.append("メモリ効率的なデータ構造への移行")
            strategies.append("弱参照を活用したキャッシュシステムの実装")
            strategies.append("プロファイリング結果に基づく定期的な最適化レビュー")

            return strategies

        except Exception as e:
            logger.error(f"長期戦略特定エラー: {str(e)}")
            return []
