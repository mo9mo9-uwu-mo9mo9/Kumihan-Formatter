"""Parser Core - パーサーコア専用モジュール

parser.py分割により抽出 (Phase3最適化)
メインParserクラスの実装
"""

import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any, Iterator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..common.error_base import GracefulSyntaxError

from ..ast_nodes import Node, error_node
import logging
from ..processing.parallel_processing_config import ParallelProcessingConfig
from ..processing.parallel_processing_errors import (
    ParallelProcessingError,
    ChunkProcessingError,
    MemoryMonitoringError,
)
from ...parsers.keyword.unified_keyword_parser import (
    UnifiedKeywordParser as KeywordParser,
)
from ...parsers.block import BlockParser
from ...block_handler import BlockHandler
from ...inline_handler import InlineHandler
from ...parallel_processor import ParallelProcessorHandler


class Parser:
    """統合パーサークラス - コア実装

    Phase3最適化により抽出されたメインパーサー
    元のparser.pyから分離し、機能を整理
    """

    def __init__(self, config: Optional[dict] = None):
        """パーサーを初期化"""
        self.config = config or {}
        self.lines = []
        self.current = 0
        self.errors = []
        self.logger = logging.getLogger(__name__)

        # Graceful error handling
        self.graceful_errors = []
        self.graceful_syntax_errors = []

        # 並列処理設定
        self.parallel_config = ParallelProcessingConfig()

        # 修正エンジン初期化
        try:
            from ..error_handling.analysis.correction_engine import CorrectionEngine

            self.correction_engine = CorrectionEngine()
        except ImportError:
            self.correction_engine = None

        # パーサー初期化
        self.keyword_parser = KeywordParser()

        # リスト・ブロックパーサー
        self.list_parser = None  # Lazy initialization
        self.block_parser = BlockParser()

        # 並列処理関連
        try:
            from ...parallel_processor import ParallelProcessorHandler

            self.parallel_processor = ParallelProcessorHandler()
        except ImportError:
            self.parallel_processor = None

        # しきい値設定
        self.parallel_threshold_lines = 1000
        self.parallel_threshold_size = 50000

        # ハンドラー
        self.block_handler = BlockHandler()
        self.inline_handler = InlineHandler()
        self.parallel_handler = (
            ParallelProcessorHandler() if self.parallel_processor else None
        )

        # スレッド制御
        self._cancelled = False

        # パフォーマンス統計
        self._thread_local = threading.local()

    @property
    def _thread_local_storage(self):
        """スレッドローカルストレージを取得"""
        return self._thread_local

    def parse(self, content: str, use_parallel: bool = True) -> List[Node]:
        """テキストを解析してASTノードのリストを返す"""
        if not content:
            return []

        start_time = time.time()
        self.lines = content.splitlines()
        self.current = 0
        self.errors = []
        self.graceful_errors = []
        self._cancelled = False

        try:
            # 並列処理の判定
            should_parallel = (
                use_parallel
                and self.parallel_processor
                and len(self.lines) >= self.parallel_threshold_lines
                and len(content.encode("utf-8")) >= self.parallel_threshold_size
            )

            if should_parallel:
                self.logger.debug(
                    f"並列処理開始: {len(self.lines)}行, {len(content.encode('utf-8'))}バイト"
                )
                result = self.parse_parallel_streaming(content)
            else:
                result = self.parse_streaming_from_text(content)

            # パフォーマンス統計記録
            processing_time = time.time() - start_time
            self.logger.info(
                f"解析完了: {len(self.lines)}行を{processing_time:.3f}秒で処理"
            )

            return result

        except Exception as e:
            self.logger.error(f"解析エラー: {e}")
            self.add_error(f"解析エラー: {str(e)}")
            return [error_node(f"解析エラー: {str(e)}")]

    def parse_optimized(self, content: str) -> List[Node]:
        """最適化された解析（シンプル版）"""
        if not content:
            return []

        self.lines = self._split_lines_optimized(content)
        self.current = 0
        self.errors = []

        results = []
        for i, line in enumerate(self.lines):
            if self._cancelled:
                break

            self.current = i
            try:
                node = self._parse_line(line)
                if node:
                    results.append(node)
            except Exception as e:
                self.add_error(f"行 {i+1}: {str(e)}")
                results.append(error_node(f"行 {i+1}: {str(e)}"))

        return results

    def _split_lines_optimized(self, content: str) -> List[str]:
        """最適化された行分割"""
        # 高速な行分割（改行文字を保持）
        if "\r\n" in content:
            return content.split("\r\n")
        elif "\r" in content:
            return content.split("\r")
        else:
            return content.split("\n")

    def parse_streaming_from_text(self, content: str) -> List[Node]:
        """ストリーミング解析（逐次処理）"""
        results = []
        self.lines = content.splitlines()

        for i, line in enumerate(self.lines):
            if self._cancelled:
                break

            self.current = i

            try:
                node = self._parse_line_with_graceful_errors(line)
                if node:
                    results.append(node)
            except Exception as e:
                error_msg = f"行 {i+1}: {str(e)}"
                self.add_error(error_msg)
                results.append(error_node(error_msg))

        return results

    def parse_parallel_streaming(self, content: str) -> List[Node]:
        """並列ストリーミング解析"""
        if not self.parallel_processor:
            return self.parse_streaming_from_text(content)

        try:
            return self.parallel_processor.process_parallel(content, self)
        except Exception as e:
            self.logger.warning(f"並列処理失敗、逐次処理にフォールバック: {e}")
            return self.parse_streaming_from_text(content)

    def cancel_parsing(self):
        """解析をキャンセル"""
        self._cancelled = True

    def get_performance_statistics(self) -> dict:
        """パフォーマンス統計を取得"""
        return {
            "total_lines": len(self.lines),
            "current_line": self.current + 1,
            "error_count": len(self.errors),
            "graceful_error_count": len(self.graceful_errors),
            "cancelled": self._cancelled,
        }

    def get_parallel_processing_metrics(self) -> dict:
        """並列処理メトリクスを取得"""
        return self.parallel_config.to_dict()

    def log_performance_summary(self):
        """パフォーマンスサマリーをログ出力"""
        stats = self.get_performance_statistics()
        self.logger.info(
            f"解析統計: {stats['total_lines']}行、エラー{stats['error_count']}件"
        )

    def _parse_line(self, line: str) -> Optional[Node]:
        """1行を解析（シンプル版）"""
        if not line.strip():
            return None

        try:
            return self._parse_line_traditional(line)
        except Exception as e:
            self.logger.error(f"行解析エラー: {e}")
            return error_node(f"解析エラー: {str(e)}")

    def _parse_line_traditional(self, line: str) -> Optional[Node]:
        """従来の行解析方法"""
        line = line.rstrip()

        if not line:
            return None

        # キーワード解析
        try:
            keyword_result = self.keyword_parser.parse(line)
            if keyword_result and keyword_result.node_type != "error":
                return keyword_result
        except Exception as e:
            self.logger.debug(f"キーワード解析失敗: {e}")

        # ブロック解析
        try:
            if self.block_parser:
                block_result = self.block_parser.parse(line)
                if block_result and block_result.node_type != "error":
                    return block_result
        except Exception as e:
            self.logger.debug(f"ブロック解析失敗: {e}")

        # デフォルト処理
        from ..ast_nodes import create_node

        return create_node("text", line)

    def _parse_line_with_graceful_errors(self, line: str) -> Optional[Node]:
        """Gracefulエラーハンドリング付き行解析"""
        try:
            return self._parse_line_traditional(line)
        except Exception as e:
            self._record_graceful_error(str(e), line)
            return error_node(f"Graceful error: {str(e)}")

    # === エラー処理 ===

    def get_errors(self) -> List[str]:
        """エラー一覧を取得"""
        return self.errors[:]

    def add_error(self, error_message: str):
        """エラーを追加"""
        self.errors.append(error_message)
        self.logger.error(error_message)

    def _record_graceful_error(self, error_message: str, line_content: str):
        """Gracefulエラーを記録"""
        error_info = {
            "line": self.current + 1,
            "content": line_content,
            "error": error_message,
            "timestamp": time.time(),
        }
        self.graceful_errors.append(error_info)

        # 修正エンジンに送信
        if self.correction_engine:
            try:
                suggestion = self.correction_engine.suggest_correction(
                    line_content, error_message
                )
                if suggestion:
                    error_info["suggestion"] = suggestion
            except Exception as e:
                self.logger.debug(f"修正提案失敗: {e}")

    def _create_error_node(self, error_message: str) -> Node:
        """エラーノードを作成"""
        return error_node(error_message)

    def get_graceful_errors(self) -> List[dict]:
        """Gracefulエラー一覧を取得"""
        return self.graceful_errors[:]

    def has_graceful_errors(self) -> bool:
        """Gracefulエラーが存在するかチェック"""
        return len(self.graceful_errors) > 0

    def get_graceful_error_summary(self) -> dict:
        """Gracefulエラーサマリーを取得"""
        if not self.graceful_errors:
            return {"count": 0, "lines": []}

        return {
            "count": len(self.graceful_errors),
            "lines": [e["line"] for e in self.graceful_errors],
            "most_common_error": self._get_most_common_error(),
        }

    def _get_most_common_error(self) -> str:
        """最も一般的なエラーを取得"""
        if not self.graceful_errors:
            return ""

        error_counts = {}
        for error_info in self.graceful_errors:
            error_type = error_info["error"].split(":")[0]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return max(error_counts, key=error_counts.get) if error_counts else ""

    def get_statistics(self) -> dict:
        """統計情報を取得"""
        return {
            **self.get_performance_statistics(),
            **self.get_graceful_error_summary(),
        }
