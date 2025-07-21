"""Parse cache core functionality extracted from parse_cache.py

This module contains the core parsing cache operations
to maintain the 300-line limit for parse_cache.py.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..ast_nodes import Node
from ..performance import get_global_monitor
from .cache_strategies import PerformanceAwareStrategy
from .smart_cache import SmartCache


class ParseCacheCore(SmartCache):
    """パース結果専用キャッシュのコア機能"""

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
        super().__init__(
            name="parse_cache",
            max_memory_entries=max_entries,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl,
            strategy=PerformanceAwareStrategy(),
            cache_dir=cache_dir,
        )

        self.monitor = get_global_monitor()
        self.parse_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_parse_time": 0.0,
            "avg_parse_time": 0.0,
            "total_nodes_cached": 0,
        }

    def get_parsed_ast(
        self,
        content: str,
        file_path: Path | None = None,
        parse_options: dict[str, Any] | None = None,
    ) -> Node | None:
        """パース済みASTを取得

        Args:
            content: パース対象のコンテンツ
            file_path: ファイルパス（オプション）
            parse_options: パースオプション

        Returns:
            Node | None: キャッシュされたAST、またはNone
        """
        cache_key = self._generate_parse_cache_key(content, file_path, parse_options)

        # キャッシュから取得を試行
        cached_result = self.get(cache_key)
        if cached_result is not None:
            self.parse_stats["cache_hits"] += 1
            self.monitor.record_cache_hit()
            return cached_result  # type: ignore[no-any-return]

        self.parse_stats["cache_misses"] += 1
        self.monitor.record_cache_miss()
        return None

    def cache_parsed_ast(
        self,
        content: str,
        ast_node: Node,
        file_path: Path | None = None,
        parse_options: dict[str, Any] | None = None,
        parse_time: float = 0.0,
    ) -> bool:
        """パース済みASTをキャッシュ

        Args:
            content: パース対象のコンテンツ
            ast_node: パース済みAST
            file_path: ファイルパス（オプション）
            parse_options: パースオプション
            parse_time: パース時間（秒）

        Returns:
            bool: キャッシュ成功かどうか
        """
        cache_key = self._generate_parse_cache_key(content, file_path, parse_options)

        # TTLを動的に計算
        node_count = self._count_nodes(ast_node)
        ttl = self._calculate_parse_ttl(node_count, parse_time)

        # キャッシュに保存
        success = self.set(cache_key, ast_node, ttl=ttl)

        if success:
            # 統計情報を更新
            self.parse_stats["total_parse_time"] += parse_time
            self.parse_stats["total_nodes_cached"] += node_count
            self._update_average_parse_time()

            self.monitor.record_cache_set()

        return success

    def get_parse_or_compute(
        self,
        content: str,
        parser_func: Callable[..., Any],
        file_path: Path | None = None,
        parse_options: dict[str, Any] | None = None,
    ) -> Node:
        """パース結果を取得、なければ計算してキャッシュ

        Args:
            content: パース対象のコンテンツ
            parser_func: パーサー関数
            file_path: ファイルパス（オプション）
            parse_options: パースオプション

        Returns:
            Node: パース済みAST
        """
        # キャッシュから取得を試行
        cached_ast = self.get_parsed_ast(content, file_path, parse_options)
        if cached_ast is not None:
            return cached_ast

        # キャッシュにない場合は計算
        start_time = datetime.now()

        try:
            ast_node = parser_func(content, **(parse_options or {}))
        except Exception as e:
            self.monitor.record_error()
            raise

        end_time = datetime.now()
        parse_time = (end_time - start_time).total_seconds()

        # 結果をキャッシュ
        self.cache_parsed_ast(content, ast_node, file_path, parse_options, parse_time)

        return ast_node  # type: ignore[no-any-return]

    def _generate_parse_cache_key(
        self,
        content: str,
        file_path: Path | None = None,
        parse_options: dict[str, Any] | None = None,
    ) -> str:
        """パースキャッシュキーを生成"""
        # コンテンツのハッシュを計算
        content_hash = self._calculate_content_hash(content)

        # ファイルパスを含める（相対パスに変換）
        path_str = str(file_path) if file_path else "no_path"

        # パースオプションを含める
        options_str = str(sorted((parse_options or {}).items()))

        # 全体のキーを生成
        full_key = f"parse:{content_hash}:{path_str}:{options_str}"
        return hashlib.md5(full_key.encode()).hexdigest()

    def _calculate_content_hash(self, content: str) -> str:
        """コンテンツのハッシュ値を計算"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _calculate_parse_ttl(self, node_count: int, parse_time: float) -> int:
        """パース時間とノード数に基づいてTTLを計算"""
        # 基本TTL
        base_ttl = 3600  # 1時間

        # ノード数が多いほど長く保持
        node_factor = min(node_count / 100, 10)  # 最大10倍

        # パース時間が長いほど長く保持
        time_factor = min(parse_time, 60)  # 最大60秒

        return int(base_ttl * (1 + node_factor * 0.1 + time_factor * 0.01))

    def _count_nodes(self, node: Node) -> int:
        """ASTノードの総数を計算"""
        count = 1
        if hasattr(node, "content") and isinstance(node.content, list):
            for child in node.content:
                if isinstance(child, Node):
                    count += self._count_nodes(child)
        return count

    def _update_average_parse_time(self) -> None:
        """平均パース時間を更新"""
        total_operations = (
            self.parse_stats["cache_hits"] + self.parse_stats["cache_misses"]
        )
        if total_operations > 0:
            self.parse_stats["avg_parse_time"] = (
                self.parse_stats["total_parse_time"] / total_operations
            )
