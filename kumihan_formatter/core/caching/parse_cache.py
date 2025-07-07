"""
パースキャッシュ - 専用実装

AST解析結果のキャッシュシステム
Issue #402対応 - パフォーマンス最適化
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ast_nodes import Node
from ..performance import get_global_monitor
from .cache_strategies import PerformanceAwareStrategy
from .smart_cache import SmartCache


class ParseCache(SmartCache):
    """パース結果専用キャッシュ

    機能:
    - AST解析結果のキャッシュ
    - 構文ツリーの高速復元
    - 依存関係の追跡
    - 部分的な無効化
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
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
        super().__init__(
            name="parse_cache",
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=PerformanceAwareStrategy(),
            cache_dir=cache_dir,
            enable_file_cache=True,
        )

        # パースメタデータ
        self._parse_metadata: Dict[str, Dict[str, Any]] = {}

    def get_parsed_ast(
        self,
        source_content: str,
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Node]]:
        """パース結果をキャッシュから取得

        Args:
            source_content: ソースコンテンツ
            parse_options: パースオプション

        Returns:
            パース結果のNodeリスト
        """
        # キャッシュキーを生成
        cache_key = self._generate_parse_cache_key(source_content, parse_options)

        # キャッシュから取得を試行
        with get_global_monitor().measure("parse_cache_lookup"):
            cached_result = self.get(cache_key)

        if cached_result is not None:
            # キャッシュヒット
            return cached_result  # type: ignore

        return None

    def cache_parsed_ast(
        self,
        source_content: str,
        ast_nodes: List[Node],
        parse_options: Optional[Dict[str, Any]] = None,
        parse_time: float = 0.0,
    ) -> None:
        """パース結果をキャッシュに保存

        Args:
            source_content: ソースコンテンツ
            ast_nodes: パース結果のNodeリスト
            parse_options: パースオプション
            parse_time: パースにかかった時間
        """
        # キャッシュキーを生成
        cache_key = self._generate_parse_cache_key(source_content, parse_options)

        # メタデータを記録
        self._parse_metadata[cache_key] = {
            "node_count": len(ast_nodes),
            "parse_time": parse_time,
            "content_hash": self._calculate_content_hash(source_content),
            "cached_at": datetime.now().isoformat(),
        }

        # TTLを動的に調整
        ttl = self._calculate_parse_ttl(len(ast_nodes), parse_time)

        # キャッシュに保存
        with get_global_monitor().measure("parse_cache_store"):
            self.set(cache_key, ast_nodes, ttl=ttl)

    def get_parse_or_compute(
        self,
        source_content: str,
        parse_func: callable,  # type: ignore
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> List[Node]:
        """キャッシュから取得または新規パース

        Args:
            source_content: ソースコンテンツ
            parse_func: パース関数
            parse_options: パースオプション

        Returns:
            パース結果のNodeリスト
        """
        # キャッシュから取得を試行
        cached_result = self.get_parsed_ast(source_content, parse_options)

        if cached_result is not None:
            return cached_result

        # パースを実行
        import time

        start_time = time.perf_counter()

        with get_global_monitor().measure(
            "parse_execution",
            node_count=None,
            file_size=len(source_content.encode("utf-8")),
        ):
            if parse_options:
                ast_nodes = parse_func(source_content, **parse_options)  # type: ignore
            else:
                ast_nodes = parse_func(source_content)  # type: ignore

        end_time = time.perf_counter()
        parse_time = end_time - start_time

        # 結果をキャッシュに保存
        self.cache_parsed_ast(source_content, ast_nodes, parse_options, parse_time)

        return ast_nodes  # type: ignore

    def invalidate_by_content_hash(self, content_hash: str) -> int:
        """コンテンツハッシュによる無効化

        Args:
            content_hash: コンテンツのハッシュ値

        Returns:
            無効化されたエントリ数
        """
        invalidated_count = 0
        keys_to_invalidate = []

        # 該当するキーを特定
        for key, metadata in self._parse_metadata.items():
            if metadata.get("content_hash") == content_hash:
                keys_to_invalidate.append(key)

        # 無効化実行
        for key in keys_to_invalidate:
            if self.delete(key):
                invalidated_count += 1
            self._parse_metadata.pop(key, None)

        return invalidated_count

    def get_parse_statistics(self) -> Dict[str, Any]:
        """パースキャッシュの統計情報を取得"""
        base_stats = self.get_stats()

        if not self._parse_metadata:
            return base_stats

        # パース時間の統計
        parse_times = [
            metadata["parse_time"]
            for metadata in self._parse_metadata.values()
            if "parse_time" in metadata
        ]

        # ノード数の統計
        node_counts = [
            metadata["node_count"]
            for metadata in self._parse_metadata.values()
            if "node_count" in metadata
        ]

        parse_stats = {}

        if parse_times:
            parse_stats.update(
                {
                    "avg_parse_time": sum(parse_times) / len(parse_times),
                    "max_parse_time": max(parse_times),
                    "min_parse_time": min(parse_times),
                    "total_parse_time_saved": sum(parse_times)
                    * (base_stats.get("hits", 0)),
                }
            )

        if node_counts:
            parse_stats.update(
                {
                    "avg_node_count": sum(node_counts) / len(node_counts),
                    "max_node_count": max(node_counts),
                    "total_nodes_cached": sum(node_counts),
                }
            )

        base_stats.update(parse_stats)
        return base_stats

    def optimize_cache_for_patterns(self) -> Dict[str, Any]:
        """使用パターンに基づいてキャッシュを最適化"""
        optimization_report = {
            "actions_taken": [],
            "space_freed": 0,
            "entries_optimized": 0,
        }

        if not self._parse_metadata:
            return optimization_report

        # 使用頻度の低いエントリを特定
        low_usage_keys = []
        for key, metadata in self._parse_metadata.items():
            # アクセス頻度が低く、パース時間が短いものを優先削除
            if metadata.get("parse_time", 0) < 0.1:  # 100ms未満
                low_usage_keys.append(key)

        # 低使用頻度エントリの削除
        for key in low_usage_keys[:10]:  # 最大10個削除
            if self.delete(key):
                optimization_report["entries_optimized"] += 1  # type: ignore
                optimization_report["actions_taken"].append(  # type: ignore
                    f"Removed low-usage entry: {key[:16]}..."
                )
                self._parse_metadata.pop(key, None)

        # 期限切れエントリの手動削除
        expired_count = self.invalidate_expired()
        if expired_count > 0:
            optimization_report["entries_optimized"] += expired_count  # type: ignore
            optimization_report["actions_taken"].append(  # type: ignore
                f"Removed {expired_count} expired entries"
            )

        return optimization_report

    def _generate_parse_cache_key(
        self,
        source_content: str,
        parse_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """パース用キャッシュキーを生成"""
        # コンテンツハッシュ
        content_hash = self._calculate_content_hash(source_content)

        # オプションハッシュ
        if parse_options:
            options_str = str(sorted(parse_options.items()))
            options_hash = hashlib.md5(options_str.encode("utf-8")).hexdigest()[:8]
        else:
            options_hash = "default"

        return f"parse_{content_hash}_{options_hash}"

    def _calculate_content_hash(self, content: str) -> str:
        """コンテンツのハッシュ値を計算"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _calculate_parse_ttl(self, node_count: int, parse_time: float) -> int:
        """パース結果に応じたTTLを計算"""
        base_ttl = self.default_ttl

        # 複雑なパース結果ほど長いTTL
        if node_count > 1000:
            base_ttl *= 2
        elif node_count > 100:
            base_ttl *= 1.5  # type: ignore

        # パース時間が長いほど長いTTL
        if parse_time > 1.0:  # 1秒以上
            base_ttl *= 2
        elif parse_time > 0.5:  # 0.5秒以上
            base_ttl *= 1.5  # type: ignore

        return int(base_ttl)

    def create_cache_snapshot(self) -> Dict[str, Any]:
        """キャッシュのスナップショットを作成"""
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_parse_statistics(),
            "metadata_count": len(self._parse_metadata),
            "memory_usage": self.storage.get_memory_stats(),
        }
