"""
レンダリングキャッシュ - 専用実装

HTML出力結果のキャッシュシステム
Issue #402対応 - パフォーマンス最適化
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
<<<<<<< HEAD
from typing import Any, Dict, List, Optional

from ..performance import get_global_monitor
from .cache_strategies import AdaptiveStrategy
from .smart_cache import SmartCache


class RenderCache(SmartCache):
    """レンダリング結果専用キャッシュ

    機能:
    - HTML出力のキャッシュ
    - テンプレート別キャッシュ管理
    - 設定変更による自動無効化
    - 段階的レンダリング対応
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_memory_mb: float = 150.0,
        max_entries: int = 500,
        default_ttl: int = 1800,  # 30分
    ):
        """レンダリングキャッシュを初期化

        Args:
            cache_dir: キャッシュディレクトリ
            max_memory_mb: 最大メモリ使用量（MB）
            max_entries: 最大エントリ数
            default_ttl: デフォルト有効期限（秒）
        """
        super().__init__(
            name="render_cache",
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=AdaptiveStrategy(frequency_weight=0.5, size_weight=0.5),
            cache_dir=cache_dir,
            enable_file_cache=True,
        )

        # レンダリングメタデータ
        self._render_metadata: Dict[str, Dict[str, Any]] = {}

        # 設定ハッシュ（設定変更検知用）
        self._config_hash: Optional[str] = None

    def get_rendered_html(
        self,
        content_hash: str,
        template_name: str,
        render_options: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """レンダリング結果をキャッシュから取得

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_options: レンダリングオプション

        Returns:
            キャッシュされたHTML文字列
        """
        # キャッシュキーを生成
        cache_key = self._generate_render_cache_key(
            content_hash, template_name, render_options
        )

        # キャッシュから取得
        with get_global_monitor().measure("render_cache_lookup"):
            cached_html = self.get(cache_key)

        if cached_html is not None:
            # メタデータを更新
            if cache_key in self._render_metadata:
                self._render_metadata[cache_key][
                    "last_accessed"
                ] = datetime.now().isoformat()

            return cached_html

        return None

    def cache_rendered_html(
        self,
        content_hash: str,
        template_name: str,
        html_output: str,
        render_options: Optional[Dict[str, Any]] = None,
        render_time: float = 0.0,
        node_count: int = 0,
    ) -> None:
        """レンダリング結果をキャッシュに保存

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            html_output: 生成されたHTML
            render_options: レンダリングオプション
            render_time: レンダリング時間
            node_count: 処理されたノード数
        """
        # キャッシュキーを生成
        cache_key = self._generate_render_cache_key(
            content_hash, template_name, render_options
        )

        # メタデータを記録
        self._render_metadata[cache_key] = {
            "content_hash": content_hash,
            "template_name": template_name,
            "render_time": render_time,
            "node_count": node_count,
            "output_size": len(html_output.encode("utf-8")),
            "cached_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
        }

        # TTLを動的に調整
        ttl = self._calculate_render_ttl(len(html_output), render_time, node_count)

        # キャッシュに保存
        with get_global_monitor().measure("render_cache_store"):
            self.set(cache_key, html_output, ttl=ttl)

    def get_render_or_compute(
        self,
        content_hash: str,
        template_name: str,
        render_func: callable,
        render_options: Optional[Dict[str, Any]] = None,
        **render_kwargs,
    ) -> str:
        """キャッシュから取得または新規レンダリング

        Args:
            content_hash: コンテンツのハッシュ値
            template_name: テンプレート名
            render_func: レンダリング関数
            render_options: レンダリングオプション
            **render_kwargs: レンダリング関数への追加引数

        Returns:
            レンダリングされたHTML
        """
        # キャッシュから取得を試行
        cached_html = self.get_rendered_html(
            content_hash, template_name, render_options
        )

        if cached_html is not None:
            return cached_html

        # レンダリングを実行
        import time

        start_time = time.perf_counter()

        with get_global_monitor().measure(
            "render_execution",
            node_count=render_kwargs.get("node_count", 0),
        ):
            if render_options:
                html_output = render_func(
                    render_options=render_options, **render_kwargs
                )
            else:
                html_output = render_func(**render_kwargs)

        end_time = time.perf_counter()
        render_time = end_time - start_time

        # 結果をキャッシュに保存
        self.cache_rendered_html(
            content_hash=content_hash,
            template_name=template_name,
            html_output=html_output,
            render_options=render_options,
            render_time=render_time,
            node_count=render_kwargs.get("node_count", 0),
        )

        return html_output

    def invalidate_by_template(self, template_name: str) -> int:
        """テンプレート名による無効化

        Args:
            template_name: 無効化するテンプレート名

        Returns:
            無効化されたエントリ数
        """
        invalidated_count = 0
        keys_to_invalidate = []

        # 該当するキーを特定
        for key, metadata in self._render_metadata.items():
            if metadata.get("template_name") == template_name:
                keys_to_invalidate.append(key)

        # 無効化実行
        for key in keys_to_invalidate:
            if self.delete(key):
                invalidated_count += 1
            self._render_metadata.pop(key, None)

        return invalidated_count

    def invalidate_by_content_hash(self, content_hash: str) -> int:
        """コンテンツハッシュによる無効化

        Args:
            content_hash: 無効化するコンテンツハッシュ

        Returns:
            無効化されたエントリ数
        """
        invalidated_count = 0
        keys_to_invalidate = []

        # 該当するキーを特定
        for key, metadata in self._render_metadata.items():
            if metadata.get("content_hash") == content_hash:
                keys_to_invalidate.append(key)

        # 無効化実行
        for key in keys_to_invalidate:
            if self.delete(key):
                invalidated_count += 1
            self._render_metadata.pop(key, None)

        return invalidated_count

    def invalidate_by_config_change(self, new_config_hash: str) -> int:
        """設定変更による全体無効化

        Args:
            new_config_hash: 新しい設定のハッシュ値

        Returns:
            無効化されたエントリ数
        """
        if self._config_hash == new_config_hash:
            return 0  # 設定変更なし

        # 全キャッシュを無効化
        invalidated_count = len(self._render_metadata)
        self.clear()
        self._render_metadata.clear()
        self._config_hash = new_config_hash

        return invalidated_count

    def get_render_statistics(self) -> Dict[str, Any]:
        """レンダリングキャッシュの統計情報を取得"""
        base_stats = self.get_stats()

        if not self._render_metadata:
            return base_stats

        # レンダリング時間の統計
        render_times = [
            metadata["render_time"]
            for metadata in self._render_metadata.values()
            if "render_time" in metadata
        ]

        # 出力サイズの統計
        output_sizes = [
            metadata["output_size"]
            for metadata in self._render_metadata.values()
            if "output_size" in metadata
        ]

        # テンプレート別統計
        template_stats = {}
        for metadata in self._render_metadata.values():
            template_name = metadata.get("template_name", "unknown")
            if template_name not in template_stats:
                template_stats[template_name] = 0
            template_stats[template_name] += 1

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

    def optimize_for_templates(self) -> Dict[str, Any]:
        """テンプレート使用パターンに基づく最適化"""
        optimization_report = {
            "actions_taken": [],
            "space_freed": 0,
            "entries_optimized": 0,
        }

        if not self._render_metadata:
            return optimization_report

        # テンプレート使用頻度を分析
        template_usage = {}
        for metadata in self._render_metadata.values():
            template_name = metadata.get("template_name", "unknown")
            if template_name not in template_usage:
                template_usage[template_name] = 0
            template_usage[template_name] += 1

        # 使用頻度の低いテンプレートのエントリを削除
        low_usage_templates = [
            template
            for template, count in template_usage.items()
            if count < 3  # 使用回数が3回未満
        ]

        for template in low_usage_templates:
            invalidated = self.invalidate_by_template(template)
            if invalidated > 0:
                optimization_report["entries_optimized"] += invalidated
                optimization_report["actions_taken"].append(
                    f"Removed {invalidated} entries for low-usage template: {template}"
                )

        return optimization_report

    def _generate_render_cache_key(
        self,
        content_hash: str,
        template_name: str,
        render_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """レンダリング用キャッシュキーを生成"""
        key_parts = [
            content_hash,
            template_name,
        ]

        # オプションハッシュ
        if render_options:
            options_str = json.dumps(render_options, sort_keys=True)
            options_hash = hashlib.md5(options_str.encode("utf-8")).hexdigest()[:8]
            key_parts.append(options_hash)

        # 設定ハッシュ
        if self._config_hash:
            key_parts.append(self._config_hash[:8])

        return "render_" + "_".join(key_parts)

    def _calculate_render_ttl(
        self,
        output_size: int,
        render_time: float,
        node_count: int,
    ) -> int:
        """レンダリング結果に応じたTTLを計算"""
        base_ttl = self.default_ttl

        # 大きな出力ほど長いTTL
        if output_size > 100000:  # 100KB以上
            base_ttl *= 2
        elif output_size > 10000:  # 10KB以上
            base_ttl *= 1.5

        # レンダリング時間が長いほど長いTTL
        if render_time > 2.0:  # 2秒以上
            base_ttl *= 3
        elif render_time > 0.5:  # 0.5秒以上
            base_ttl *= 2

        # ノード数が多いほど長いTTL
        if node_count > 500:
            base_ttl *= 1.5

        return int(base_ttl)

    def create_render_report(self) -> Dict[str, Any]:
        """レンダリングキャッシュの詳細レポートを作成"""
        stats = self.get_render_statistics()

        return {
            "timestamp": datetime.now().isoformat(),
            "cache_performance": stats,
            "optimization_suggestions": self._generate_optimization_suggestions(),
            "template_analysis": self._analyze_template_usage(),
        }

    def _generate_optimization_suggestions(self) -> List[str]:
        """最適化提案を生成"""
        suggestions = []

        stats = self.get_render_statistics()

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
        memory_usage_ratio = memory_stats.get("size_bytes", 0) / memory_stats.get(
            "max_bytes", 1
        )
        if memory_usage_ratio > 0.8:
            suggestions.append(
                f"メモリ使用率が高い ({memory_usage_ratio:.1%}): "
                "メモリ制限の増加またはキャッシュエントリの削減を検討"
            )

        return suggestions

    def _analyze_template_usage(self) -> Dict[str, Any]:
        """テンプレート使用パターンを分析"""
        template_stats = {}

        for metadata in self._render_metadata.values():
            template_name = metadata.get("template_name", "unknown")
            if template_name not in template_stats:
                template_stats[template_name] = {
                    "count": 0,
                    "total_render_time": 0,
                    "avg_output_size": 0,
                    "sizes": [],
                }

            stats = template_stats[template_name]
            stats["count"] += 1
            stats["total_render_time"] += metadata.get("render_time", 0)

            output_size = metadata.get("output_size", 0)
            stats["sizes"].append(output_size)

        # 平均値を計算
        for template_name, stats in template_stats.items():
            if stats["count"] > 0:
                stats["avg_render_time"] = stats["total_render_time"] / stats["count"]
                stats["avg_output_size"] = sum(stats["sizes"]) / len(stats["sizes"])
            del stats["sizes"]  # 不要なデータを削除

        return template_stats
