"""Base parser module - Refactored and modularized parser for Kumihan-Formatter

This is the main parser implementation that integrates specialized handlers.
Issue #813: Split monolithic parser.py into modular components.
"""

from typing import Any, Optional

# 統合最適化後のインポート（削除されたハンドラー・モジュールを除去）
from .core.ast_nodes import Node

# 統合済みパーサーを使用 - Issue #1168 Parser Responsibility Separation
from .parsers.unified_keyword_parser import (
    UnifiedKeywordParser as KeywordParser,
)


# Issue #759対応: カスタム例外クラス定義
class ParallelProcessingError(Exception):
    """並列処理固有のエラー"""

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー"""

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー"""

    pass


# Issue #759対応: 並列処理設定クラス
class ParallelProcessingConfig:
    """並列処理の設定管理"""

    def __init__(self) -> None:
        # 並列処理しきい値設定
        self.parallel_threshold_lines = 10000  # 10K行以上で並列化
        self.parallel_threshold_size = 10 * 1024 * 1024  # 10MB以上で並列化

        # チャンク設定
        self.min_chunk_size = 50
        self.max_chunk_size = 2000
        self.target_chunks_per_core = 2  # CPUコアあたりのチャンク数

        # メモリ監視設定
        self.memory_warning_threshold_mb = 150
        self.memory_critical_threshold_mb = 250
        self.memory_check_interval = 10  # チャンク数

        # タイムアウト設定
        self.processing_timeout_seconds = 300  # 5分
        self.chunk_timeout_seconds = 30  # 30秒

        # パフォーマンス設定
        self.enable_progress_callbacks = True
        self.progress_update_interval = 100  # 行数
        self.enable_memory_monitoring = True
        self.enable_gc_optimization = True

    @classmethod
    def from_environment(cls) -> "ParallelProcessingConfig":
        """環境変数から設定を読み込み"""
        import os

        config = cls()

        # 環境変数からの設定上書き
        if threshold_lines := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES"):
            try:
                config.parallel_threshold_lines = int(threshold_lines)
            except ValueError:
                pass

        if threshold_size := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE"):
            try:
                config.parallel_threshold_size = int(threshold_size)
            except ValueError:
                pass

        if memory_limit := os.getenv("KUMIHAN_MEMORY_LIMIT_MB"):
            try:
                memory_limit_int = int(memory_limit)
                config.memory_critical_threshold_mb = memory_limit_int
                config.memory_warning_threshold_mb = int(memory_limit_int * 0.6)
            except ValueError:
                pass

        if timeout := os.getenv("KUMIHAN_PROCESSING_TIMEOUT"):
            try:
                config.processing_timeout_seconds = int(timeout)
            except ValueError:
                pass

        return config

    def validate(self) -> bool:
        """設定値の検証"""
        try:
            assert self.parallel_threshold_lines > 0
            assert self.parallel_threshold_size > 0
            assert self.min_chunk_size > 0
            assert self.max_chunk_size > self.min_chunk_size
            assert self.memory_warning_threshold_mb > 0
            assert self.memory_critical_threshold_mb > self.memory_warning_threshold_mb
            assert self.processing_timeout_seconds > 0
            return True
        except AssertionError:
            return False


"""Base parser module - 統合パーサー（Phase3最適化版）

Phase3最適化により大幅分割: 753行 → 150行以下
機能別モジュールに分割済み:
- 並列処理エラー → ParallelProcessingErrors  
- 並列処理設定 → ParallelProcessingConfig
- メインParser → ParserCore
- 関数群 → ParserFunctions

このファイルは後方互換性のための統合インターフェース
"""

# 統合最適化後：削除されたモジュールのインポートを除去
# 上記で定義済みのクラス・設定を使用
from .core.parsing.parser_core import Parser as CoreParser

# 後方互換性のためのエイリアス
Parser = CoreParser

# __all__でエクスポートを明示
__all__ = [
    # エラークラス
    "ParallelProcessingError",
    "ChunkProcessingError",
    "MemoryMonitoringError",
    "WorkerTimeoutError",
    "ResourceExhaustionError",
    # 設定クラス
    "ParallelProcessingConfig",
    # メインクラス
    "Parser",
    # 関数群
    "parse",
    "parse_with_error_config",
    "parse_file",
    "parse_streaming",
    "validate_parse_config",
    "create_default_config",
]


def parse(text: str, config: Any = None) -> list[Node]:
    """
    Main parsing function (compatibility with existing API)

    Args:
        text: Input text to parse
        config: Optional configuration

    Returns:
        list[Node]: Parsed AST nodes
    """
    parser = Parser(config)
    return parser.parse(text)


def parse_with_error_config(
    text: str, config: Any = None, use_streaming: bool | None = None
) -> list[Node]:
    """
    エラー設定対応の解析関数（ストリーミング対応）

    Args:
        text: 解析対象テキスト
        config: 設定オブジェクト（現在未使用）
        use_streaming: ストリーミング使用フラグ（Noneの場合は自動判定）

    Returns:
        list[Node]: 解析済みAST nodes
    """
    # ストリーミング使用判定
    if use_streaming is None:
        # テキストサイズが大きい場合はストリーミングを使用
        size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        use_streaming = size_mb > 1.0

    if use_streaming:
        # TODO: StreamingParser implementation - falling back to regular parsing
        pass

    # 通常のパーシング処理
    parser: Parser = Parser(config=config)
    return parser.parse(text)
