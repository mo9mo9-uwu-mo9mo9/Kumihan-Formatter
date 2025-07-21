"""
パースキャッシュ - 統合モジュール

AST解析結果のキャッシュシステム
Issue #402対応 - パフォーマンス最適化

分割されたモジュール:
- parse_cache_core: コア機能（キャッシュ操作）
- parse_cache_analytics: 分析・最適化機能
"""

from pathlib import Path
from typing import Any

from .parse_cache_analytics import ParseCacheAnalytics
from .parse_cache_core import ParseCacheCore


class ParseCache(ParseCacheCore):
    """パース結果専用キャッシュ（統合クラス）

    機能:
    - AST解析結果のキャッシュ
    - 構文ツリーの高速復元
    - 依存関係の追跡
    - 部分的な無効化
    - パフォーマンス分析
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_memory_mb: float = 100.0,
        max_entries: int = 1000,
        default_ttl: int = 3600,  # 1時間
    ):
        """パースキャッシュを初期化

        Args:
            cache_dir: キャッシュディレクトリ
            max_memory_mb: 最大メモリ使用量（MB）
            max_entries: 最大エントリ数
            default_ttl: デフォルト有効期限（秒）
        """
        super().__init__(cache_dir, max_memory_mb, max_entries, default_ttl)

        # 分析機能を初期化
        self.analytics = ParseCacheAnalytics(self)

    # 分析機能へのデリゲート
    def get_parse_statistics(self) -> dict[str, Any]:
        """パースキャッシュの統計情報を取得"""
        return self.analytics.get_parse_statistics()

    def optimize_cache_for_patterns(self) -> dict[str, Any]:
        """使用パターンに基づいてキャッシュを最適化"""
        return self.analytics.optimize_cache_for_patterns()

    def invalidate_by_content_hash(self, content_hash: str) -> int:
        """コンテンツハッシュによる無効化"""
        return self.analytics.invalidate_by_content_hash(content_hash)

    def create_cache_snapshot(self) -> dict[str, Any]:
        """キャッシュの現在の状態のスナップショットを作成"""
        return self.analytics.create_cache_snapshot()


# 後方互換性のため、クラスをエクスポート
__all__ = ["ParseCache", "ParseCacheCore", "ParseCacheAnalytics"]
