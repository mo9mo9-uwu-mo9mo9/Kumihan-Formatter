"""
レンダリングキャッシュ - 統合クラス（後方互換性用）

HTML出力結果のキャッシュシステム
Issue #402対応 - パフォーマンス最適化
Issue #492 Phase 5A - 分割により300行制限対応

注意: このクラスは後方互換性のため保持。
新しい実装は分割されたモジュールを使用:
- RenderCacheCore: メイン機能
- RenderCacheMetadata: メタデータ管理
- RenderCacheAnalytics: 分析・統計
- RenderCacheValidators: バリデーション
"""

from pathlib import Path
from typing import Any, Union

from .render_cache_analytics import RenderCacheAnalytics
from .render_cache_core import RenderCacheCore


class RenderCache(RenderCacheCore):
    """レンダリング結果専用キャッシュ - 統合クラス（後方互換性）

    注意: このクラスは既存コードとの互換性のため保持。
    新規開発では分割されたモジュールを直接使用することを推奨。

    機能:
    - 分割されたコンポーネントの統合
    - 既存APIの維持
    - 統計・分析機能の提供
    """

    def __init__(
        self,
        cache_dir: Union[Path, None] = None,
        max_memory_mb: float = 150.0,
        max_entries: int = 500,
        default_ttl: int = 1800,  # 30分
    ):
        """レンダリングキャッシュを初期化（統合版）

        Args:
            cache_dir: キャッシュディレクトリ
            max_memory_mb: 最大メモリ使用量（MB）
            max_entries: 最大エントリ数
            default_ttl: デフォルト有効期限（秒）
        """
        # RenderCacheCoreで初期化（分離されたコンポーネントを含む）
        super().__init__(cache_dir, max_memory_mb, max_entries, default_ttl)

        # 分析モジュールを追加
        self.analytics = RenderCacheAnalytics()

    def get_render_statistics(self) -> dict[str, Any]:
        """レンダリングキャッシュの統計情報を取得（統合版）"""
        base_stats = self.get_stats()
        return self.analytics.generate_statistics(
            self.metadata.get_all_metadata(), base_stats
        )

    def optimize_for_templates(self) -> dict[str, Any]:
        """テンプレート使用パターンに基づく最適化（統合版）"""
        return self.analytics.optimize_for_templates(
            self.metadata.get_all_metadata(),
            invalidate_callback=self.invalidate_by_template,
        )

    def create_render_report(self) -> dict[str, Any]:
        """レンダリングキャッシュの詳細レポートを作成（統合版）"""
        stats = self.get_render_statistics()
        return self.analytics.create_render_report(
            stats, self.metadata.get_all_metadata()
        )

    # 後方互換性のための旧メソッド（非推奨）
    def _generate_render_cache_key(
        self,
        content_hash: str,
        template_name: str,
        render_options: Union[dict[str, Any], None] = None,
    ) -> str:
        """レンダリング用キャッシュキーを生成（非推奨）

        注意: このメソッドは後方互換性のため保持。
        新規コードでは self.validators.generate_cache_key() を使用。
        """
        return self.validators.generate_cache_key(
            content_hash, template_name, render_options, self._config_hash
        )

    def _calculate_render_ttl(
        self,
        output_size: int,
        render_time: float,
        node_count: int,
    ) -> int:
        """レンダリング結果に応じたTTLを計算（非推奨）

        注意: このメソッドは後方互換性のため保持。
        新規コードでは self.validators.calculate_ttl() を使用。
        """
        return self.validators.calculate_ttl(output_size, render_time, node_count)

    def _generate_optimization_suggestions(self) -> list[str]:
        """最適化提案を生成（非推奨）

        注意: このメソッドは後方互換性のため保持。
        新規コードでは self.analytics.generate_optimization_suggestions() を使用。
        """
        stats = self.get_render_statistics()
        return self.analytics.generate_optimization_suggestions(stats)

    def _analyze_template_usage(self) -> dict[str, Any]:
        """テンプレート使用パターンを分析（非推奨）

        注意: このメソッドは後方互換性のため保持。
        新規コードでは self.analytics.analyze_template_usage() を使用。
        """
        return self.analytics.analyze_template_usage(self.metadata.get_all_metadata())
