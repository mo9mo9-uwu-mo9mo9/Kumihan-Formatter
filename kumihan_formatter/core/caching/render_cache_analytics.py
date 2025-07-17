"""
レンダリングキャッシュ - 分析・統計・最適化

統計情報生成・レポート作成・最適化
Issue #492 Phase 5A - render_cache.py分割
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Union


class RenderCacheAnalytics:
    """レンダリングキャッシュの分析・統計・最適化

    責任:
    - 統計情報の生成
    - 最適化提案の作成
    - レポート生成
    - テンプレート使用パターンの分析
    """

    def __init__(self) -> None:
        """分析モジュールを初期化"""
        pass

    def generate_statistics(
        self,
        metadata: dict[str, dict[str, Any]],
        base_stats: Union[dict[str, Any], None] = None,
    ) -> dict[str, Any]:
        """レンダリングキャッシュの統計情報を生成

        Args:
            metadata: レンダリングメタデータ
            base_stats: ベース統計情報

        Returns:
            統計情報辞書
        """
        if base_stats is None:
            base_stats = {}

        if not metadata:
            return base_stats

        # レンダリング時間の統計
        render_times = [
            meta["render_time"] for meta in metadata.values() if "render_time" in meta
        ]

        # 出力サイズの統計
        output_sizes = [
            meta["output_size"] for meta in metadata.values() if "output_size" in meta
        ]

        # テンプレート別統計
        template_stats: Dict[str, Any] = {}
        for meta in metadata.values():
            template_name = meta.get("template_name", "unknown")
            template_stats[template_name] = template_stats.get(template_name, 0) + 1

        render_stats = {
            "template_distribution": template_stats,
        }

        if render_times:
            render_stats.update(
                {
                    "avg_render_time": sum(render_times) / len(render_times),
                    "max_render_time": max(render_times),
                    "min_render_time": min(render_times),
                    "total_render_time_saved": sum(render_times)
                    * base_stats.get("hits", 0),
                }
            )

        if output_sizes:
            render_stats.update(
                {
                    "avg_output_size": sum(output_sizes) / len(output_sizes),
                    "max_output_size": max(output_sizes),
                    "total_output_size": sum(output_sizes),
                }
            )

        base_stats.update(render_stats)
        return base_stats

    def optimize_for_templates(
        self,
        metadata: dict[str, dict[str, Any]],
        invalidate_callback: Union[Callable[[str], int], None] = None,
    ) -> dict[str, Any]:
        """テンプレート使用パターンに基づく最適化

        Args:
            metadata: レンダリングメタデータ
            invalidate_callback: 無効化を実行するコールバック関数

        Returns:
            最適化レポート
        """
        optimization_report = {
            "actions_taken": [],
            "space_freed": 0,
            "entries_optimized": 0,
        }

        if not metadata:
            return optimization_report

        # テンプレート使用頻度を分析
        template_usage: Dict[str, int] = {}
        for meta in metadata.values():
            template_name = meta.get("template_name", "unknown")
            template_usage[template_name] = template_usage.get(template_name, 0) + 1

        # 使用頻度の低いテンプレートのエントリを削除
        low_usage_templates = [
            template
            for template, count in template_usage.items()
            if count < 3  # 使用回数が3回未満
        ]

        for template in low_usage_templates:
            if invalidate_callback:
                invalidated = invalidate_callback(template)
                if invalidated > 0:
                    optimization_report["entries_optimized"] += invalidated  # type: ignore
                    optimization_report["actions_taken"].append(  # type: ignore
                        f"Removed {invalidated} entries for low-usage template: {template}"
                    )

        return optimization_report

    def create_render_report(
        self,
        statistics: dict[str, Any],
        metadata: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """レンダリングキャッシュの詳細レポートを作成

        Args:
            statistics: 統計情報
            metadata: レンダリングメタデータ

        Returns:
            詳細レポート
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "cache_performance": statistics,
            "optimization_suggestions": self.generate_optimization_suggestions(
                statistics
            ),
            "template_analysis": self.analyze_template_usage(metadata),
        }

    def generate_optimization_suggestions(self, stats: dict[str, Any]) -> list[str]:
        """最適化提案を生成

        Args:
            stats: 統計情報

        Returns:
            最適化提案のリスト
        """
        suggestions = []

        # キャッシュヒット率の分析
        hit_rate = stats.get("hit_rate", 0)
        if hit_rate < 0.5:
            suggestions.append(
                f"低いキャッシュヒット率 ({hit_rate:.1%}): TTL設定の見直しを検討"
            )

        # 平均レンダリング時間の分析
        avg_render_time = stats.get("avg_render_time", 0)
        if avg_render_time > 1.0:
            suggestions.append(
                f"平均レンダリング時間が長い ({avg_render_time:.2f}s): "
                "テンプレート最適化またはキャッシュ戦略の見直しを検討"
            )

        # メモリ使用量の分析
        memory_stats = stats.get("memory_stats", {})
        if memory_stats:
            memory_usage_ratio = memory_stats.get("size_bytes", 0) / max(
                memory_stats.get("max_bytes", 1), 1
            )
            if memory_usage_ratio > 0.8:
                suggestions.append(
                    f"メモリ使用率が高い ({memory_usage_ratio:.1%}): "
                    "メモリ制限の増加またはキャッシュエントリの削減を検討"
                )

        return suggestions

    def analyze_template_usage(
        self, metadata: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """テンプレート使用パターンを分析

        Args:
            metadata: レンダリングメタデータ

        Returns:
            テンプレート分析結果
        """
        template_stats = {}

        for meta in metadata.values():
            template_name = meta.get("template_name", "unknown")
            if template_name not in template_stats:
                template_stats[template_name] = {
                    "count": 0,
                    "total_render_time": 0,
                    "avg_output_size": 0,
                    "sizes": [],
                }

            stats = template_stats[template_name]
            stats["count"] += 1  # type: ignore
            stats["total_render_time"] += meta.get("render_time", 0)

            output_size = meta.get("output_size", 0)
            stats["sizes"].append(output_size)  # type: ignore

        # 平均値を計算
        for template_name, stats in template_stats.items():
            if stats["count"] > 0:  # type: ignore
                stats["avg_render_time"] = stats["total_render_time"] / stats["count"]  # type: ignore
                stats["avg_output_size"] = sum(stats["sizes"]) / len(stats["sizes"])  # type: ignore
            del stats["sizes"]  # 不要なデータを削除

        return template_stats

    def identify_optimization_opportunities(
        self,
        metadata: dict[str, dict[str, Any]],
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        """最適化機会を特定

        Args:
            metadata: レンダリングメタデータ
            stats: 統計情報

        Returns:
            最適化機会の分析結果
        """
        opportunities: Dict[str, List[Dict[str, Any]]] = {
            "high_impact": [],
            "medium_impact": [],
            "low_impact": [],
        }

        # 高コストなレンダリングの特定
        render_times = [
            (key, meta["render_time"])
            for key, meta in metadata.items()
            if "render_time" in meta
        ]

        if render_times:
            avg_render_time = sum(time for _, time in render_times) / len(render_times)

            # 平均の2倍以上の時間がかかるレンダリングを特定
            expensive_renders = [
                key for key, time in render_times if time > avg_render_time * 2
            ]

            if expensive_renders:
                opportunities["high_impact"].append(
                    f"高コストレンダリング {len(expensive_renders)} 件の最適化"
                )

        # 大きな出力サイズの特定
        output_sizes = [
            (key, meta["output_size"])
            for key, meta in metadata.items()
            if "output_size" in meta
        ]

        if output_sizes:
            large_outputs = [
                key for key, size in output_sizes if size > 100000  # 100KB以上
            ]

            if large_outputs:
                opportunities["medium_impact"].append(
                    f"大容量出力 {len(large_outputs)} 件の圧縮検討"
                )

        return opportunities
