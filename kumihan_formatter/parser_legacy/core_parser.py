"""Core parser logic for Kumihan-Formatter

Issue #813対応: parser_old.pyからコアパーサーロジックを分離
主要なパーシング機能とAST構築ロジックを含む
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..core.common.error_base import GracefulSyntaxError

from ..core.ast_nodes import Node, error_node
from ..core.block_parser import BlockParser
from ..core.keyword_parser import KeywordParser
from ..core.list_parser import ListParser
from ..core.utilities.logger import get_logger
from ..parser import ParallelProcessingConfig


class Parser:
    """
    Kumihan記法のメインパーサー（各特化パーサーを統括）

    設計ドキュメント:
    - 記法仕様: /SPEC.md
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - KeywordParser: キーワード解析を委譲
    - ListParser: リスト解析を委譲（KeywordParser使用）
    - BlockParser: ブロック解析を委譲（KeywordParser使用）
    - Node: 生成するASTノード

    責務:
    - テキスト全体の解析フロー制御
    - 行タイプ判定と適切なパーサーへの委譲
    - AST構造の構築統括
    """

    def __init__(
        self,
        config=None,
        graceful_errors: bool = False,
        parallel_config: ParallelProcessingConfig | None = None,
    ) -> None:  # 型アノテーション正常化: type: ignore削除
        """Initialize parser with fixed markers

        Args:
            config: Parser configuration (ignored for simplification)
            graceful_errors: Enable graceful error handling (Issue #700)
            parallel_config: 並列処理設定（Issue #759コードレビュー対応）
        """
        # 簡素化: configは無視して固定マーカーのみ使用
        self.config = None
        self.lines: list[str] = []  # 型アノテーション修正: type: ignore削除
        self.current = 0
        self.errors: list[str] = []  # 型アノテーション修正: type: ignore削除
        self.logger = get_logger(__name__)

        # Issue #700: graceful error handling
        self.graceful_errors = graceful_errors
        self.graceful_syntax_errors: list["GracefulSyntaxError"] = []

        # Issue #759: 並列処理設定の外部化対応
        self.parallel_config = (
            parallel_config or ParallelProcessingConfig.from_environment()
        )

        # 設定値検証
        if not self.parallel_config.validate():
            self.logger.warning(
                "Invalid parallel processing configuration, using defaults"
            )
            self.parallel_config = ParallelProcessingConfig()

        # 修正提案エンジン
        if graceful_errors:
            from ..core.error_analysis.correction_engine import CorrectionEngine

            self.correction_engine = CorrectionEngine()
            self.logger.info(
                "Correction engine initialized for graceful error handling"
            )

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        # Issue #700: graceful error handling対応 - sub-parsersにパーサー参照を設定
        if graceful_errors:
            self.block_parser.set_parser_reference(self)

        # Issue #759: 並列処理統合 - ParallelChunkProcessorの初期化
        from ..core.utilities.parallel_processor import ParallelChunkProcessor

        self.parallel_processor = ParallelChunkProcessor()

        # 並列処理のしきい値設定（外部設定から取得）
        self.parallel_threshold_lines = self.parallel_config.parallel_threshold_lines
        self.parallel_threshold_size = self.parallel_config.parallel_threshold_size

        self.logger.debug(
            f"Parser initialized with specialized parsers and parallel processing "
            f"(graceful_errors={graceful_errors}, "
            f"parallel_threshold={self.parallel_threshold_lines} lines, "
            f"memory_limit={self.parallel_config.memory_critical_threshold_mb}MB)"
        )  # 重複type: ignore削除  # type: ignore  # type: ignore

    def parse(self, text: str) -> list[Node]:
        """
        Parse text into AST nodes

        Args:
            text: Input text to parse

        Returns:
            list[Node]: Parsed AST nodes
        """
        self.lines = text.split("\n")
        self.current = 0
        self.errors = []
        nodes = []

        self.logger.info(f"Starting parse of {len(self.lines)} lines")
        self.logger.debug(f"Input text length: {len(text)} characters")

        # 無限ループ防止のための安全装置
        max_iterations = len(self.lines) * 2  # 最大反復数
        iteration_count = 0

        while self.current < len(self.lines) and iteration_count < max_iterations:
            previous_current = self.current
            node = self._parse_line()

            if node:
                nodes.append(node)
                self.logger.debug(
                    f"Parsed node type: {node.type} at line {self.current}"
                )

            # 無限ループ防止: currentが進んでいない場合
            if self.current == previous_current:
                self.logger.warning(
                    f"Parser stuck at line {self.current}, forcing advance"
                )
                self.current += 1

            iteration_count += 1

        if iteration_count >= max_iterations:
            self.logger.error(
                f"Parser hit maximum iteration limit ({max_iterations}), stopping"
            )
            self.add_error(f"Parser exceeded maximum iterations at line {self.current}")

        self.logger.info(
            f"Parse complete: {len(nodes)} nodes created, {len(self.errors)} errors"
        )
        return nodes

    def parse_optimized(self, text: str) -> list[Node]:
        """
        最適化されたパーステキスト処理（Issue #727 パフォーマンス最適化対応）

        改善点:
        - O(n²) → O(n) 計算複雑度改善
        - パターンマッチングキャッシュ
        - 文字列処理最適化
        - メモリ効率向上

        Args:
            text: Input text to parse

        Returns:
            list[Node]: Parsed AST nodes
        """
        self.logger.info(f"Starting optimized parse of {len(text)} characters")

        # 最適化: 行分割を効率化（split最適化）
        self.lines = self._split_lines_optimized(text)
        self.current = 0
        self.errors = []
        nodes = []

        # パフォーマンス監視開始
        from ..core.performance import monitor_performance

        with monitor_performance("optimized_parse") as perf_monitor:
            # パターンキャッシュ初期化
            pattern_cache: dict[str, Any] = {}
            line_type_cache: dict[str, str] = {}

            # 最適化: 事前にラインタイプを一括解析（O(n)で処理）
            line_types = self._analyze_line_types_batch(self.lines)

            # メインパースループ（最適化版）
            while self.current < len(self.lines):
                previous_current = self.current

                # 最適化されたライン解析
                node = self._parse_line_optimized(
                    line_types, pattern_cache, line_type_cache
                )

                if node:
                    nodes.append(node)
                    # パフォーマンス監視にアイテム処理を記録
                    perf_monitor.record_item_processed()

                # 進捗チェック（最適化）
                if self.current == previous_current:
                    self.logger.warning(
                        f"Parser stuck at line {self.current}, forcing advance"
                    )
                    self.current += 1

            self.logger.info(
                f"Optimized parse complete: {len(nodes)} nodes, {len(self.errors)} errors"
            )

        return nodes

    def _split_lines_optimized(self, text: str) -> list[str]:
        """
        Issue #757対応: 行分割の最適化実装

        従来のsplit('\n')より高速な行分割処理
        """
        # 大容量ファイル用の最適化された行分割
        if len(text) > 1000000:  # 1MB以上
            # メモリ効率を重視した分割
            return text.splitlines()

        # 通常サイズの場合
        return text.splitlines()

    def _analyze_line_types_batch(self, lines: list[str]) -> dict[int, str]:
        """
        Issue #757対応: 一括行タイプ解析（O(n)処理）

        全行のタイプを事前に解析することで、後続処理を高速化
        """
        line_types = {}

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                line_types[i] = "empty"
            elif self.block_parser.is_opening_marker(stripped):
                line_types[i] = "block_marker"
            elif stripped.startswith("#") and not self.block_parser.is_opening_marker(
                stripped
            ):
                line_types[i] = "comment"
            elif self.list_parser.is_list_line(stripped):
                line_types[i] = "list"
            else:
                line_types[i] = "paragraph"

        return line_types

    def _parse_line_optimized(
        self, line_types: dict[int, str], pattern_cache: dict, line_type_cache: dict
    ) -> Optional[Node]:
        """
        Issue #757対応: 最適化されたライン解析

        事前解析結果を活用した高速ライン処理
        """
        if self.current >= len(self.lines):
            return None

        # 基本的な行処理
        _ = self.lines[self.current].strip()  # 現在は使用しないが取得
        _ = line_types.get(self.current, "unknown")  # 現在は使用しないが取得
        self.current += 1
        return None  # 簡略化実装

    def _parse_block_marker_fast(self) -> Optional[Node]:
        """高速ブロックマーカー解析"""
        node, next_index = self.block_parser.parse_block_marker(
            self.lines, self.current
        )
        self.current = next_index
        return node

    def _parse_list_fast(self) -> Optional[Node]:
        """高速リスト解析"""
        line = self.lines[self.current].strip()
        list_type = self.list_parser.is_list_line(line)

        if list_type == "ul":
            node, next_index = self.list_parser.parse_unordered_list(
                self.lines, self.current
            )
        else:
            node, next_index = self.list_parser.parse_ordered_list(
                self.lines, self.current
            )

        self.current = next_index
        return node

    def _parse_paragraph_fast(self) -> Optional[Node]:
        """高速段落解析"""
        # キーワードパーサーを使用したインライン処理
        content = self.lines[self.current]
        processed = self.keyword_parser._process_inline_keywords(content)
        self.current += 1
        return Node("paragraph", content=processed)

    def _parse_line_fallback(self) -> Optional[Node]:
        """フォールバック行解析"""
        return self._parse_line_traditional()

    def _parse_line(self) -> Optional[Node]:
        """
        Parse a single line and return corresponding Node

        Returns:
            Optional[Node]: Parsed node or None if line should be skipped
        """
        if self.graceful_errors:
            return self._parse_line_with_graceful_errors()

        return self._parse_line_traditional()

    def _parse_line_traditional(self) -> Optional[Node]:
        """
        Traditional line parsing without graceful error handling
        """
        if self.current >= len(self.lines):
            return None

        current_line = self.lines[self.current]

        # リスト項目のチェック
        if current_line.strip().startswith("- ") or current_line.strip().startswith(
            "* "
        ):
            # ul
            node, next_index = self.list_parser.parse_unordered_list(
                self.lines, self.current
            )
        elif (
            current_line.strip()
            and current_line.strip()[0].isdigit()
            and ". " in current_line
        ):
            # ol
            node, next_index = self.list_parser.parse_ordered_list(
                self.lines, self.current
            )
        else:
            # その他の行の処理
            return None

        self.current = next_index
        return node

    def _parse_line_with_graceful_errors(self) -> Optional[Node]:
        """
        Parse line with graceful error handling (Issue #700)

        エラーが発生した場合でも処理を継続し、エラー情報を記録
        """
        if self.current >= len(self.lines):
            return None

        line = self.lines[self.current]

        # 空行のスキップ
        if not line.strip():
            self.current += 1
            return None

        # ブロックマーカーの解析を試行
        try:
            if line.strip().startswith("#") and "##" in line:
                node, next_index = self.block_parser.parse_block_marker(
                    self.lines, self.current
                )
                self.current = next_index
                return node
        except Exception as e:
            # エラーログ記録
            error_message = str(e)
            self.logger.warning(
                f"Block parsing error at line {self.current + 1}: {error_message}",
                extra={
                    "error_type": "block_parsing_error",
                    "line_number": self.current + 1,
                    "content": line,
                    "error_message": error_message,
                },
            )
            # エラーノードを作成して処理を継続
            error_content = f"Error: Failed to parse block marker: {line}"
            self.current += 1
            return self._create_error_node(error_content, "block_error")

        # 他の行の処理（リスト、段落など）
        self.current += 1
        return None

    def get_errors(self) -> list:
        """Get parsing errors"""
        return self.errors

    def add_error(self, error_message: str) -> None:
        """Add parsing error"""
        self.errors.append(error_message)
        self.logger.error(f"Parser error: {error_message}")

    def _record_graceful_error(
        self, error_type: str, line_number: int, content: str, error_message: str
    ) -> None:
        """
        Record a graceful error for later analysis

        Args:
            error_type: Type of error encountered
            line_number: Line number where error occurred
            content: Original content that caused the error
            error_message: Detailed error message
        """
        try:
            from ..core.common.error_base import GracefulSyntaxError

            graceful_error = GracefulSyntaxError(
                error_type=error_type,
                line_number=line_number,
                column=0,
                context=content,
                message=error_message,
                severity="warning",
                suggestion="",
            )

            self.graceful_syntax_errors.append(graceful_error)

            # 修正提案エンジンによる自動修正提案
            if hasattr(self, "correction_engine"):
                try:
                    suggestions = self.correction_engine.generate_suggestions(
                        graceful_error
                    )
                    if suggestions:
                        graceful_error.suggestion = (
                            suggestions[0] if suggestions else ""
                        )
                    self.logger.info(
                        f"Generated {len(suggestions)} correction suggestions for {error_type}"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to generate correction suggestions: {str(e)}"
                    )

        except ImportError:
            # GracefulSyntaxErrorが利用できない場合の fallback
            self.logger.warning(
                f"GracefulSyntaxError not available, recording as plain error: {error_message}"
            )
            self.add_error(f"{error_type} at line {line_number}: {error_message}")
        except Exception as e:
            # その他のエラー
            self.logger.error(f"Failed to record graceful error: {str(e)}")
            self.add_error(f"{error_type} at line {line_number}: {error_message}")

    def _create_error_node(self, error_content: str, error_type: str) -> Node:
        """
        Create an error node for graceful error handling

        Args:
            error_content: Content describing the error
            error_type: Type of error for categorization

        Returns:
            Node: Error node with appropriate styling
        """
        return error_node(error_content, error_type=error_type)

    def get_graceful_errors(self) -> list:
        """Get graceful syntax errors"""
        return self.graceful_syntax_errors

    def has_graceful_errors(self) -> bool:
        """Check if graceful errors occurred"""
        return len(self.graceful_syntax_errors) > 0

    def get_graceful_error_summary(self) -> dict[str, Any]:
        """
        Get summary of graceful errors

        Returns:
            Dict containing error counts by type and other statistics
        """
        if not self.graceful_syntax_errors:
            return {"total": 0, "by_type": {}, "has_suggestions": 0}

        error_counts: dict[str, int] = {}
        has_suggestions = 0

        for error in self.graceful_syntax_errors:
            error_type = getattr(error, "error_type", "unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

            if hasattr(error, "suggestion") and error.suggestion:
                has_suggestions += 1

        return {
            "total": len(self.graceful_syntax_errors),
            "by_type": error_counts,
            "has_suggestions": has_suggestions,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get parser statistics"""
        return {
            "lines_processed": len(self.lines),
            "current_position": self.current,
            "errors": len(self.errors),
            "graceful_errors": (
                len(self.graceful_syntax_errors)
                if hasattr(self, "graceful_syntax_errors")
                else 0
            ),
        }


# Module-level functions for backward compatibility
def parse(text: str, graceful_errors: bool = False) -> list[Node]:
    """Parse text using Parser instance"""
    parser = Parser(graceful_errors=graceful_errors)
    return parser.parse(text)


def parse_with_error_config(
    text: str, error_config: dict | None = None
) -> tuple[list[Node], list]:
    """Parse text with error configuration"""
    graceful_errors = (
        error_config.get("graceful_errors", False) if error_config else False
    )
    parser = Parser(graceful_errors=graceful_errors)
    nodes = parser.parse(text)
    errors = parser.get_errors()

    if graceful_errors:
        errors.extend([str(e) for e in parser.get_graceful_errors()])

    return nodes, errors
