"""Base block parser with common functionality.

Base class for block parsers providing:
- Caching mechanisms
- Line preprocessing
- Common utilities
- Pattern matching

Created: 2025-08-10 (Error問題修正 - BlockParser分割)
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..base.parser_protocols import KeywordParserProtocol
    from ..keyword.keyword_parser import KeywordParser
else:
    try:
        from ..base.parser_protocols import KeywordParserProtocol
    except ImportError:
        from typing import Protocol

        KeywordParserProtocol = Protocol


class BaseBlockParser:
    """Base class for block parsers with common functionality.

    Issue #914 Phase 2: 循環参照解消
    - KeywordParser直接依存から依存関係注入パターンに変更
    - プロトコルベースのインターフェース使用
    """

    def __init__(
        self, keyword_parser: Optional["KeywordParserProtocol"] = None
    ) -> None:
        """Initialize base block parser.

        Args:
            keyword_parser: Optional keyword parser instance (protocol-based)
        """
        self.logger = get_logger(__name__)

        # 依存関係注入: KeywordParserをDIコンテナから取得
        if keyword_parser is None:
            self.keyword_parser = self._get_keyword_parser()
        else:
            self.keyword_parser = keyword_parser

        self.heading_counter = 0

        # Performance optimization caches
        self._block_end_indices: Dict[int, int] = {}
        self._lines_cache: List[str] = []

        # Pattern caches
        self._list_pattern = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
        self._empty_line_pattern = re.compile(r"^\s*$")

        # Marker detection cache
        self._is_marker_cache: Dict[str, bool] = {}
        self._is_list_cache: Dict[str, bool] = {}

        # Parser reference
        self.parser_ref = None

    def _get_keyword_parser(self) -> Optional["KeywordParserProtocol"]:
        """DIコンテナからKeywordParserを取得

        Issue #914 Phase 2: 依存関係注入パターン

        Returns:
            KeywordParserProtocol instance or None
        """
        try:
            from ...patterns.dependency_injection import get_container

            container = get_container()
            # Note: container.resolve expects a concrete class, not a protocol
            # This is a known limitation that would need DI container fixes
            return None  # Fallback to next option
        except Exception as e:
            self.logger.warning(f"KeywordParser取得失敗、フォールバック使用: {e}")
            # フォールバック: specialized/keyword_parser.pyから直接インポート
            try:
                from ..specialized.keyword_parser import UnifiedKeywordParser
                from typing import cast

                parser = UnifiedKeywordParser()
                # Cast to protocol type since UnifiedKeywordParser should implement the interface
                return cast(Optional[KeywordParserProtocol], parser)
            except Exception as fallback_error:
                self.logger.error(f"フォールバックも失敗: {fallback_error}")
                return None

    def _is_marker_internal(self, line: str) -> bool:
        """Internal marker detection."""
        # Kumihanマーカー形式の簡易検出: # keyword #content##
        import re

        marker_pattern = re.compile(r"^#\s*[^#]+\s*#[^#]*##")
        return bool(marker_pattern.match(line.strip()))

    def _is_list_internal(self, line: str) -> bool:
        """Internal list detection."""
        return bool(self._list_pattern.match(line))

    def set_parser_reference(self, parser: Any) -> None:
        """Set reference to main parser for recursive calls.

        Args:
            parser: Main parser instance for recursive calls
        """
        self.parser_ref = parser

    def _preprocess_lines(self, lines: List[str]) -> List[str]:
        """Preprocess lines for parsing optimization.

        Args:
            lines: Raw input lines

        Returns:
            Preprocessed lines for efficient parsing
        """
        if not lines:
            return []

        processed_lines = []
        max_preprocess_lines = 10000  # 設定可能な上限

        try:
            for i, line in enumerate(lines):
                if i >= max_preprocess_lines:
                    self.logger.warning(
                        f"Preprocessing limited to {max_preprocess_lines} lines"
                    )
                    processed_lines.extend(lines[i:])
                    break

                # Basic line normalization
                stripped = line.rstrip()
                processed_lines.append(stripped)

        except Exception as e:
            self.logger.error(f"Error during line preprocessing: {e}")
            return lines  # Return original lines on error

        return processed_lines

    def _find_next_block_end(self, start_index: int) -> int:
        """Find the end index of the next block with caching.

        Args:
            start_index: Starting position for search

        Returns:
            End index of the next block, or len(lines) if not found
        """
        if not self._lines_cache:
            return start_index

        # Check cache first
        if start_index in self._block_end_indices:
            return self._block_end_indices[start_index]

        # Search for block end
        for i in range(start_index + 1, len(self._lines_cache)):
            if self.is_block_marker_line(self._lines_cache[i]):
                self._block_end_indices[start_index] = i
                return i

        # If no block end found, return end of lines
        end_pos = len(self._lines_cache)
        self._block_end_indices[start_index] = end_pos
        return end_pos

    def _is_block_marker_cached(
        self, line: str, keyword_parser: Optional["KeywordParser"] = None
    ) -> bool:
        """Check if line is block marker with caching.

        Args:
            line: Line to check
            keyword_parser: Optional keyword parser

        Returns:
            True if line is a block marker
        """
        # Use internal cache for performance
        if line in self._is_marker_cache:
            return self._is_marker_cache[line]

        def _cached_marker_check() -> bool:
            # 内部のマーカー検出メソッドを使用
            return self._is_marker_internal(line)

        result = _cached_marker_check()
        self._is_marker_cache[line] = result
        return result

    def is_block_marker_line(self, line: str) -> bool:
        """Check if line is a block marker line.

        Args:
            line: Line to check

        Returns:
            True if line is a block marker
        """
        if not line.strip():
            return False

        return self._is_block_marker_cached(line)

    def is_opening_marker(self, line: str) -> bool:
        """Check if line is an opening marker.

        Args:
            line: Line to check

        Returns:
            True if line is an opening marker
        """
        return self.is_block_marker_line(line) and not self.is_closing_marker(line)

    def is_closing_marker(self, line: str) -> bool:
        """Check if line is a closing marker.

        Args:
            line: Line to check

        Returns:
            True if line is a closing marker
        """
        stripped = line.strip()
        return stripped.endswith("##") and len(stripped) >= 3

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """Skip empty lines and return next non-empty index.

        Args:
            lines: List of lines
            start_index: Starting index

        Returns:
            Index of next non-empty line, or len(lines) if none found
        """
        for i in range(start_index, len(lines)):
            if lines[i].strip():
                return i
        return len(lines)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """Find next significant (non-empty, non-comment) line.

        Args:
            lines: List of lines
            start_index: Starting index

        Returns:
            Index of next significant line, or len(lines) if none found
        """
        for i in range(start_index, len(lines)):
            line = lines[i]
            if line.strip() and not self._is_comment_line(line):
                return i
        return len(lines)

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment line.

        Args:
            line: 判定対象の行

        Returns:
            コメント行の場合True
        """
        return line.strip().startswith("#")
