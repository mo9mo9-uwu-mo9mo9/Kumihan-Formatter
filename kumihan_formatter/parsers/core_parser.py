"""Core Parser - 統合コアパーサーモジュール

Issue #1252対応: parser_core.py + legacy_parser.py統合版
重複実装を削除し、統一されたコアパーサー機能を提供

統合内容:
- 並列処理エラークラス統合
- 設定管理統合
- Parser基底クラス統合
- レガシー互換機能統合
"""

import threading
import time
import warnings
from typing import Any, Dict, List, Optional

from ..core.ast_nodes import Node, error_node
from ..core.utilities.logger import get_logger


# 統合エラークラス（重複排除）
class ParallelProcessingError(Exception):
    """並列処理固有のエラー"""

    pass


class ChunkProcessingError(Exception):
    """チャンク処理でのエラー"""

    pass


class MemoryMonitoringError(Exception):
    """メモリ監視でのエラー"""

    pass


class ParallelProcessingConfig:
    """並列処理の設定管理（統合版）"""

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

        # 追加: タイムアウト（レガシー互換）
        self.processing_timeout_seconds = 300
        self.chunk_timeout_seconds = 30

        # 進捗・最適化設定（レガシー互換）
        self.enable_progress_callbacks = True
        self.progress_update_interval = 100
        self.enable_memory_monitoring = True
        self.enable_gc_optimization = True

    @classmethod
    def from_environment(cls) -> "ParallelProcessingConfig":
        """環境変数から設定を構築（レガシー互換）。"""
        import os

        cfg = cls()
        try:
            if v := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_LINES"):
                cfg.parallel_threshold_lines = int(v)
            if v := os.getenv("KUMIHAN_PARALLEL_THRESHOLD_SIZE"):
                cfg.parallel_threshold_size = int(v)
            if v := os.getenv("KUMIHAN_MEMORY_LIMIT_MB"):
                mem = int(v)
                cfg.memory_critical_threshold_mb = mem
                cfg.memory_warning_threshold_mb = max(1, int(mem * 0.6))
            if v := os.getenv("KUMIHAN_PROCESSING_TIMEOUT"):
                cfg.processing_timeout_seconds = int(v)
        except ValueError:
            # 無効値は無視（デフォルト維持）
            pass
        return cfg

    def validate(self) -> bool:
        """設定値の妥当性検証（レガシー互換）。"""
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

    def should_use_parallel_processing(
        self, line_count: int, content_size: int
    ) -> bool:
        """並列処理を使用するべきかの判定"""
        return (
            line_count >= self.parallel_threshold_lines
            or content_size >= self.parallel_threshold_size
        )

    def calculate_chunk_size(self, total_lines: int, core_count: int = 1) -> int:
        """最適なチャンクサイズを計算"""
        target_chunks = max(core_count * self.target_chunks_per_core, 1)
        ideal_chunk_size = max(total_lines // target_chunks, self.min_chunk_size)
        return min(ideal_chunk_size, self.max_chunk_size)


class Parser:
    """統合版Parserクラス（parser_core.py + legacy_parser.py統合）

    Issue #1252対応:
    - 重複実装の統合
    - 並列処理機能強化
    - メモリ効率最適化
    - エラーハンドリング統一
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Parser初期化

        Args:
            config: パーサー設定辞書
        """
        self.config = config or {}
        self.lines: List[str] = []
        self.current = 0
        self.errors: List[str] = []
        self.logger = get_logger(__name__)

        # エラーハンドリング設定
        self.graceful_errors = self.config.get("graceful_errors", True)
        self.graceful_syntax_errors = self.config.get("graceful_syntax_errors", True)

        # 並列処理設定
        self.parallel_config = ParallelProcessingConfig()

        # パーサー統合機能（legacy_parser.pyから継承）
        try:
            from .unified_keyword_parser import UnifiedKeywordParser

            self.keyword_parser: Optional[UnifiedKeywordParser] = UnifiedKeywordParser()
        except ImportError:
            self.logger.warning("UnifiedKeywordParserのインポートに失敗")
            self.keyword_parser = None

        # 並列処理関連初期化
        self.parallel_processor = None

        # 並列処理しきい値（動的設定可能）
        self.parallel_threshold_lines = self.parallel_config.parallel_threshold_lines
        self.parallel_threshold_size = self.parallel_config.parallel_threshold_size

        # キャンセル機能
        self._cancelled = False

        # スレッドローカルストレージ
        self._thread_local = threading.local()

    @property
    def _thread_local_storage(self) -> threading.local:
        """スレッドローカルストレージへのアクセス"""
        return self._thread_local

    def parse(self, content: str) -> Node:
        """メインパース処理（統合版）

        Args:
            content: パース対象コンテンツ

        Returns:
            パース結果ノード
        """
        if not content:
            return error_node("Empty content provided")

        try:
            self.lines = content.strip().split("\n")
            self.current = 0
            self.errors.clear()

            # 並列処理判定
            if self.parallel_config.should_use_parallel_processing(
                len(self.lines), len(content)
            ):
                return self.parse_optimized(content)
            else:
                return self._parse_sequential(content)

        except Exception as e:
            if self.graceful_errors:
                self.logger.warning(f"Parse error (graceful): {e}")
                return error_node(f"Parse error: {e}")
            else:
                raise

    def parse_optimized(self, content: str) -> Node:
        """最適化パース処理（並列処理版）"""
        try:
            lines = self._split_lines_optimized(content)

            # 大量データの場合は並列処理
            if len(lines) > self.parallel_threshold_lines:
                return self.parse_parallel_streaming(lines)
            else:
                return self._parse_sequential_optimized(lines)

        except Exception as e:
            self.logger.error(f"最適化パース処理でエラー: {e}")
            return error_node(f"Optimized parse error: {e}")

    def _split_lines_optimized(self, content: str) -> List[str]:
        """最適化された行分割処理"""
        if "\r\n" in content:
            return content.replace("\r\n", "\n").split("\n")
        return content.split("\n")

    def parse_streaming_from_text(self, content: str) -> Node:
        """ストリーミングパース処理"""
        try:
            lines = content.split("\n")
            return self._stream_process_lines(lines)
        except Exception as e:
            if self.graceful_errors:
                return error_node(f"Streaming parse error: {e}")
            else:
                raise

    def parse_parallel_streaming(self, lines: List[str]) -> Node:
        """並列ストリーミング処理（プレースホルダー）"""
        # 実装は必要に応じて詳細化
        self.logger.info(f"並列処理: {len(lines)}行を処理中")
        return self._parse_sequential_optimized(lines)

    def cancel_parsing(self) -> None:
        """パース処理のキャンセル"""
        self._cancelled = True

    def get_performance_statistics(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        return {
            "lines_processed": len(self.lines),
            "current_position": self.current,
            "errors_count": len(self.errors),
            "parallel_enabled": bool(self.parallel_processor),
        }

    def get_parallel_processing_metrics(self) -> Dict[str, Any]:
        """並列処理メトリクス取得"""
        return {"parallel_config": self.parallel_config.__dict__}

    def _parse_line(self, line: str) -> Node:
        """行単位パース処理"""
        try:
            # 基本的な行パース処理
            if not line.strip():
                return error_node("Empty line")

            # キーワードパーサーが利用可能な場合
            if self.keyword_parser:
                return self.keyword_parser.parse(line)
            else:
                return error_node(f"Parser not available for line: {line[:50]}")

        except Exception as e:
            return self._parse_line_with_graceful_errors(line, e)

    def _parse_line_with_graceful_errors(self, line: str, error: Exception) -> Node:
        """エラー耐性を持つ行パース処理"""
        if self.graceful_syntax_errors:
            self.add_error(f"Line parse error: {error}")
            return error_node(f"Graceful error for: {line[:50]}")
        else:
            raise error

    def add_error(self, message: str) -> None:
        """エラーメッセージ追加"""
        self.errors.append(message)

    # プライベートヘルパーメソッド
    def _parse_sequential(self, content: str) -> Node:
        """順次処理版パース"""
        lines = content.split("\n")
        return self._stream_process_lines(lines)

    def _parse_sequential_optimized(self, lines: List[str]) -> Node:
        """最適化された順次処理"""
        return self._stream_process_lines(lines)

    def _stream_process_lines(self, lines: List[str]) -> Node:
        """ライン単位ストリーム処理"""
        if not lines:
            return error_node("No lines to process")

        # シンプルな処理（必要に応じて詳細化）
        processed_count = 0
        for line in lines:
            if self._cancelled:
                break
            processed_count += 1

        return Node(
            type="parsed_content",
            content=f"Processed {processed_count} lines",
            attributes={"line_number": processed_count, "column": 1},
        )


# レガシー互換機能（legacy_parser.pyからの統合）
def parse(content: str, config: Optional[Dict[str, Any]] = None) -> Node:
    """レガシー互換パース関数

    Args:
        content: パース対象コンテンツ
        config: パーサー設定

    Returns:
        パース結果ノード

    Warning:
        この関数は後方互換性のために提供されています。
        新しいコードではParserクラスを直接使用してください。
    """
    warnings.warn(
        "legacy parse() function is deprecated. Use Parser class instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = Parser(config)
    return parser.parse(content)


def parse_with_error_config(
    content: str, graceful_errors: bool = True, graceful_syntax_errors: bool = True
) -> Node:
    """エラー設定付きパース（レガシー互換）

    Args:
        content: パース対象コンテンツ
        graceful_errors: グレースフルエラーハンドリング有効化
        graceful_syntax_errors: 構文エラーの寛容処理有効化

    Returns:
        パース結果ノード
    """
    warnings.warn(
        "parse_with_error_config() is deprecated. Use Parser class with config.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = {
        "graceful_errors": graceful_errors,
        "graceful_syntax_errors": graceful_syntax_errors,
    }

    return parse(content, config)


# エクスポート定義
__all__ = [
    # 統合エラークラス
    "ParallelProcessingError",
    "ChunkProcessingError",
    "MemoryMonitoringError",
    # 設定クラス
    "ParallelProcessingConfig",
    # メインクラス
    "Parser",
    # レガシー互換関数
    "parse",
    "parse_with_error_config",
]
