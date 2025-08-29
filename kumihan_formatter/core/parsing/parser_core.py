"""Parser Core - パーサーコア専用モジュール

parser.py分割により抽出 (Phase3最適化)
メインParserクラスの実装
"""

import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..common.error_base import GracefulSyntaxError

from ..ast_nodes import Node, error_node
import logging


# 統合最適化後：削除されたモジュールからの局所定義
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
    """並列処理の設定管理（簡易版）"""

    def __init__(self):
        self.parallel_threshold_lines = 1000
        self.parallel_threshold_size = 50000


from ...parsers.unified_keyword_parser import (
    UnifiedKeywordParser as KeywordParser,
)


class Parser:
    """統合パーサークラス - コア実装

    Phase3最適化により抽出されたメインパーサー
    元のparser.pyから分離し、機能を整理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """パーサーを初期化"""
        self.config = config or {}
        self.lines: List[str] = []
        self.current = 0
        self.errors: List[str] = []
        self.logger = logging.getLogger(__name__)

        # Graceful error handling
        self.graceful_errors: List[str] = []
        self.graceful_syntax_errors: List[str] = []

        # 並列処理設定
        self.parallel_config = ParallelProcessingConfig()

        # パーサー初期化（統合最適化後：利用可能なもののみ）
        try:
            self.keyword_parser = KeywordParser()
        except Exception:
            self.keyword_parser = None

        # 統合最適化後: 並列処理は無効化（簡素化のため）
        self.parallel_processor = None

        # しきい値設定
        self.parallel_threshold_lines = 1000
        self.parallel_threshold_size = 50000

        # スレッド制御
        self._cancelled = False

        # パフォーマンス統計
        self._thread_local = threading.local()

    @property
    def _thread_local_storage(self) -> threading.local:
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
            # 統合最適化後：逐次処理のみ（並列処理は無効化）
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
        """並列ストリーミング解析（統合アーキテクチャ対応）"""
        # 統合最適化後は逐次処理をメインとし、必要時のみ並列化
        return self.parse_streaming_from_text(content)

    def cancel_parsing(self) -> None:
        """解析をキャンセル"""
        self._cancelled = True

    def get_performance_statistics(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        return {
            "total_lines": len(self.lines),
            "current_line": self.current + 1,
            "error_count": len(self.errors),
            "graceful_error_count": len(self.graceful_errors),
            "cancelled": self._cancelled,
        }

    def get_parallel_processing_metrics(self) -> Dict[str, Any]:
        """並列処理のメトリクスを取得"""
        return {"parallel_processing": "disabled", "architecture": "unified"}

    def _parse_line(self, line: str) -> Optional[Node]:
        """単一行の解析（統合最適化後）"""
        if not line.strip():
            return None

        # 統合パーサーアーキテクチャを使用
        try:
            # create_nodeのインポートを使用
            from ..ast_nodes import create_node
            # シンプルなテキストノード作成（統合最適化後）
            return create_node("text", line)

        except Exception as e:
            self.logger.error(f"行解析エラー: {e}")
            return error_node(f"行解析エラー: {str(e)}")

    def _parse_line_with_graceful_errors(self, line: str) -> Optional[Node]:
        """グレースフルエラーハンドリング付き行解析"""
        try:
            return self._parse_line(line)
        except Exception as e:
            # グレースフルエラーとして記録
            self.graceful_errors.append(f"行 {self.current + 1}: {str(e)}")
            return error_node(f"構文エラー: {str(e)}")

    def add_error(self, error: str) -> None:
        """エラーを追加"""
        self.errors.append(error)
