"""Content parser for block content processing and error recovery.

Handles:
- Block content processing
- Error recovery mechanisms
- Content fix suggestions
- List block parsing

Created: 2025-08-10 (Error問題修正 - BlockParser分割)
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .base_parser import BaseBlockParser

if TYPE_CHECKING:
    from kumihan_formatter.core.ast_nodes import Node

    from ..keyword_parser import KeywordParser


class ContentParser(BaseBlockParser):
    """Specialized parser for content processing and error recovery."""

    def __init__(self, keyword_parser: Optional["KeywordParser"] = None) -> None:
        """Initialize content parser.

        Args:
            keyword_parser: Optional keyword parser instance
        """
        super().__init__(keyword_parser)

    def _parse_new_format_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple["Node", int]:
        """Parse new format block content.

        Args:
            lines: List of input lines
            start_index: Starting index
            keywords: Parsed keywords
            attributes: Parsed attributes

        Returns:
            Tuple of (parsed node, next index)
        """
        if not keywords:
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "ブロック解析エラー", "キーワードが指定されていません", start_index
                ),
                start_index + 1,
            )

        # Find block end
        end_index = self._find_next_block_end(start_index + 1)

        # Handle missing closing marker
        if end_index >= len(lines) or not self.is_closing_marker(lines[end_index]):
            self.logger.warning(
                f"Missing closing marker for block starting at line {start_index + 1}"
            )

            # Try error recovery
            if end_index < len(lines):
                opening_line = lines[start_index]
                suggested_fix = self._generate_block_fix_suggestions(
                    opening_line, keywords
                )
                self.logger.info(f"Suggested fix: {suggested_fix}")

                # Attempt content recovery
                recovered_content = self._attempt_content_recovery(lines, start_index)
                if recovered_content:
                    self.logger.info("Content recovery successful")

                    # Create node with recovered content
                    node = self._create_node_for_keyword(keywords[0], recovered_content)
                    if node:
                        self._apply_attributes_to_node(node, attributes)
                        return node, end_index

    def _generate_block_fix_suggestions(
        self, opening_line: str, keywords: List[str]
    ) -> str:
        """Generate fix suggestions for malformed blocks.

        Args:
            opening_line: Opening line of the block
            keywords: Parsed keywords

        Returns:
            Suggested fix string
        """
        if not keywords:
            return "キーワードを指定してください"

        primary_keyword = keywords[0]
        return f"ブロックの終端マーカー '##' を追加してください: # {primary_keyword} #内容##"

    def _attempt_content_recovery(self, lines: List[str], start_index: int) -> str:
        """Attempt to recover content from malformed block.

        Args:
            lines: List of input lines
            start_index: Starting index of the block

        Returns:
            Recovered content string, empty if recovery failed
        """
        if start_index + 1 >= len(lines):
            return ""

        content_lines = []

        try:
            for i in range(start_index + 1, len(lines)):
                line = lines[i]

                # Stop at next block marker
                if self.is_opening_marker(line):
                    break

                # Stop at closing marker
                if self.is_closing_marker(line):
                    break

                content_lines.append(line)

            return "\n".join(content_lines).strip()

        except Exception as e:
            self.logger.error(f"Error during content recovery: {e}")
            return ""

    def _parse_list_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple["Node", int]:
        """Parse list block using list parser.

        Args:
            lines: List of input lines
            start_index: Starting index
            keywords: Parsed keywords
            attributes: Parsed attributes

        Returns:
            Tuple of (parsed list node, next index)
        """
        # Check if parser reference has list parser
        if not self.parser_ref or not hasattr(self.parser_ref, "list_parser"):
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "リスト解析エラー", "リストパーサーが利用できません", start_index
                ),
                start_index + 1,
            )

        try:
            # Use list parser from main parser
            list_parser = self.parser_ref.list_parser
            list_node, next_index = list_parser.parse_list_block(
                lines, start_index, keywords, attributes
            )
            return list_node, next_index

        except Exception as e:
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "リスト解析エラー", f"予期しないエラー: {str(e)}", start_index
                ),
                start_index + 1,
            )

    def _create_node_for_keyword(self, keyword: str, content: str) -> Optional["Node"]:
        """Create appropriate node for given keyword and content.

        Args:
            keyword: Primary keyword
            content: Node content

        Returns:
            Created node or None if keyword not recognized
        """
        if not self.keyword_parser:
            return None

        try:
            # Get node factory for keyword
            factory_func = self.keyword_parser.get_node_factory(keyword)
            if factory_func:
                return factory_func(content)

        except Exception as e:
            self.logger.error(f"Error creating node for keyword '{keyword}': {e}")

        return None

    def _apply_attributes_to_node(
        self, node: "Node", attributes: Dict[str, Any]
    ) -> None:
        """Apply attributes to node.

        Args:
            node: Target node
            attributes: Attributes to apply
        """
        try:
            for key, value in attributes.items():
                if hasattr(node, key):
                    setattr(node, key, value)
                else:
                    self.logger.debug(f"Node does not have attribute '{key}', skipping")

        except Exception as e:
            self.logger.error(f"Error applying attributes to node: {e}")

    def _process_block_content(self, content_lines: List[str]) -> str:
        """Process block content lines into final content.

        Args:
            content_lines: Raw content lines

        Returns:
            Processed content string
        """
        if not content_lines:
            return ""

        # Join content lines and strip leading/trailing whitespace
        content = "\n".join(content_lines).strip()

        # Remove excessive blank lines
        import re

        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        return content

    def _validate_block_structure(
        self, lines: List[str], start_index: int, end_index: int
    ) -> bool:
        """Validate block structure integrity.

        Args:
            lines: List of input lines
            start_index: Block start index
            end_index: Block end index

        Returns:
            True if structure is valid
        """
        if start_index >= len(lines) or end_index > len(lines):
            return False

        # Check if start_index has opening marker
        if not self.is_opening_marker(lines[start_index]):
            return False

        # Check if end_index has closing marker (if not at end of file)
        if end_index < len(lines) and not self.is_closing_marker(lines[end_index]):
            return False

        return True
