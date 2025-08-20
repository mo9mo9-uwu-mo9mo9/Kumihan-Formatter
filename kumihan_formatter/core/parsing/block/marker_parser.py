"""Marker block parser for block marker detection and analysis.

Handles:
- Block marker detection
- Marker format parsing
- New format marker processing
- Image marker detection

Created: 2025-08-10 (Error問題修正 - BlockParser分割)
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, cast

from .base_parser import BaseBlockParser

if TYPE_CHECKING:
    from kumihan_formatter.core.ast_nodes import Node

    from ..base.parser_protocols import KeywordParserProtocol
else:
    try:
        from ..base.parser_protocols import KeywordParserProtocol
    except ImportError:
        from typing import Protocol

        KeywordParserProtocol = Protocol


class MarkerBlockParser(BaseBlockParser):
    """Specialized parser for block markers and marker analysis.

    Issue #914 Phase 2: 循環参照解消
    - KeywordParser直接依存から依存関係注入パターンに変更
    """

    def __init__(
        self, keyword_parser: Optional["KeywordParserProtocol"] = None
    ) -> None:
        """Initialize marker block parser.

        Args:
            keyword_parser: Optional keyword parser instance (protocol-based)
        """
        super().__init__(keyword_parser)

    def parse_new_format_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple["Node", int]:
        """Parse new format marker from lines.

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed node, next index)
        """
        if start_index >= len(lines):
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    f"マーカー解析エラー: 開始インデックス {start_index} が行数 {len(lines)} を超えています",
                    start_index,
                ),
                start_index + 1,
            )

        try:
            # Get opening line for parsing
            opening_line = lines[start_index]

            # Parse marker using keyword parser
            if not self.keyword_parser:
                from kumihan_formatter.core.ast_nodes import error_node

                return (
                    error_node(
                        "パーサーエラー: キーワードパーサーが利用できません",
                        start_index,
                    ),
                    start_index + 1,
                )

            parse_result = self.keyword_parser.parse_new_format(opening_line)
            if not parse_result:
                from kumihan_formatter.core.ast_nodes import error_node

                return (
                    error_node(
                        f"マーカー解析エラー: 新形式マーカーの解析に失敗しました: {opening_line}",
                        start_index,
                    ),
                    start_index + 1,
                )

            # Extract parse results
            keywords, attributes, parse_errors = parse_result

            if parse_errors:
                self.logger.warning(f"Parse errors in marker: {parse_errors}")

            # Check for inline content
            inline_content = self._extract_inline_content(
                opening_line, [keywords] if isinstance(keywords, str) else keywords
            )
            if inline_content:
                # Process as inline format
                return self._parse_inline_format(
                    [keywords] if isinstance(keywords, str) else keywords,
                    (
                        {"content": attributes}
                        if isinstance(attributes, str)
                        else attributes
                    ),
                    inline_content,
                    start_index,
                )

            # Default fallback for non-inline markers
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "マーカー解析エラー: ブロック形式のマーカー処理が未実装です",
                    start_index,
                ),
                start_index + 1,
            )
        except Exception as e:
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    f"マーカー解析エラー: 解析中にエラーが発生しました: {e}",
                    start_index,
                ),
                start_index + 1,
            )

    def _extract_inline_content(self, line: str, keywords: List[str]) -> str:
        """Extract inline content from marker line.

        Args:
            line: Marker line
            keywords: Parsed keywords

        Returns:
            Inline content if present, empty string otherwise
        """
        # Simple inline content detection
        # This is a simplified implementation - actual logic may be more complex
        if " #" in line and line.strip().endswith("#"):
            # Find content between keywords and closing #
            parts = line.split("#")
            if len(parts) >= 3:
                return parts[-2].strip()

        return ""

    def _parse_inline_format(
        self,
        keywords: List[str],
        attributes: Dict[str, Any],
        content: str,
        start_index: int,
    ) -> Tuple["Node", int]:
        """Parse inline format marker.

        Args:
            keywords: Parsed keywords
            attributes: Parsed attributes
            content: Inline content
            start_index: Starting index

        Returns:
            Tuple of (parsed node, next index)
        """
        if not keywords:
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "インライン解析エラー: キーワードが指定されていません",
                    start_index,
                ),
                start_index + 1,
            )

        # Get primary keyword
        primary_keyword = keywords[0]

        # Create node for keyword
        node = self._create_node_for_keyword(primary_keyword, content)
        if node:
            self._apply_attributes_to_node(node, attributes)

        return node or self._create_error_node(start_index), start_index + 1

    def _create_node_for_keyword(self, keyword: str, content: str) -> Optional["Node"]:
        """Create appropriate node for given keyword and content.

        Args:
            keyword: Primary keyword
            content: Node content

        Returns:
            Created node or None if keyword not recognized
        """
        # Keyword to node type mapping
        keyword_mapping = {
            "太字": "BoldNode",
            "イタリック": "ItalicNode",
            "見出し1": "HeadingNode",
            "見出し2": "HeadingNode",
            "見出し3": "HeadingNode",
            "見出し4": "HeadingNode",
            "見出し5": "HeadingNode",
            "ハイライト": "HighlightNode",
        }

        if keyword in keyword_mapping:
            # Get factory function for the keyword
            factory_func = (
                self.keyword_parser.get_node_factory() if self.keyword_parser else None
            )

            if factory_func:
                return cast("Node | None", factory_func(content))

        return None

    def _apply_attributes_to_node(
        self, node: "Node", attributes: Dict[str, Any]
    ) -> None:
        """Apply attributes to node.

        Args:
            node: Target node
            attributes: Attributes to apply
        """
        for key, value in attributes.items():
            if hasattr(node, key):
                setattr(node, key, value)

    def parse_block_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple["Node", int]:
        """Parse block marker (main entry point).

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed node, next index)
        """
        # Delegate to new format parser
        return self.parse_new_format_marker(lines, start_index)

    def _is_simple_image_marker(self, line: str) -> bool:
        """Check if line is a simple image marker.

        Args:
            line: Line to check

        Returns:
            True if line is a simple image marker
        """
        if not self.keyword_parser:
            return False

        # Check for image file extensions
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
        return any(line.lower().endswith(ext) for ext in image_extensions)

    def _create_error_node(self, start_index: int) -> "Node":
        """Create error node for parsing failures.

        Args:
            start_index: Index where error occurred

        Returns:
            Error node
        """
        from kumihan_formatter.core.ast_nodes import error_node

        return error_node("マーカー解析エラー: ノード作成に失敗しました", start_index)
