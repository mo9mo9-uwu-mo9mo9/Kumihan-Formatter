"""
UnifiedListParser - 統合リスト解析エンジン

Issue #914 Phase 2: 8個のListParserファイルを統合
- parsers/list_parser.py (プロトコル準拠ベース)
- core/list_parser.py (コア機能)
- core/nested_list_parser.py (ネスト処理)
- core/parsing/list/list_parser.py (統一リスト解析)
- core/parsing/list/parsers/ordered_list_parser.py (順序付き)
- core/parsing/list/parsers/unordered_list_parser.py (順序なし)
- core/parsing/list/parsers/nested_list_parser.py (ネスト)
- core/parsing/specialized/list_parser.py (特殊化処理)
"""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import (
        ParseResult,
        ParseContext,
        ListParserProtocol,
    )
    from ..core.ast_nodes.node import Node
else:
    ListParserProtocol = object


class UnifiedListParser(ListParserProtocol):
    """統合リスト解析エンジン - ListParserProtocol実装

    統合機能:
    - 順序付き・順序なしリスト解析
    - ネスト構造サポート（最大レベル制限なし）
    - チェックリスト・定義リスト対応
    - アルファベット・ローマ数字リスト
    - Kumihan # リスト # ブロック形式
    - 高度エラー処理・回復機能
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # Core parser initialization (fallback)
        self.core_parser = None
        try:
            from ..core.parsing.specialized.list_parser import (
                UnifiedListParser as CoreListParser,
            )

            self.core_parser = CoreListParser()
        except ImportError:
            self.logger.warning(
                "Core list parser not available, using built-in implementation"
            )

        # リスト解析パターンの設定
        self._setup_list_patterns()
        self._setup_list_handlers()

        self.logger.info("UnifiedListParser initialized with full functionality")

    def _setup_list_patterns(self) -> None:
        """リスト解析パターンの設定"""
        self.list_patterns = {
            # 基本パターン
            "unordered": re.compile(r"^(\s*)[-*+]\s+(?!\[)(.+)$"),
            "ordered_numeric": re.compile(r"^(\s*)(\d+)[.)]\s+(.+)$"),
            # 拡張パターン
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([xX\s])\]\s*(.+)$"),
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
            "alpha": re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$"),
            "roman": re.compile(
                r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x|xi{0,3}|xiv|xv|xvi{0,3}|xix|xx)\.\s+(.+)$",
                re.IGNORECASE,
            ),
            # Kumihan形式
            "kumihan_list": re.compile(r"^#\s*リスト\s*#\s*$"),
            "kumihan_end": re.compile(r"^##\s*$"),
            # ユーティリティ
            "indent": re.compile(r"^(\s*)"),
            "empty_line": re.compile(r"^\s*$"),
        }

    def _setup_list_handlers(self) -> None:
        """リストハンドラーの設定"""
        self.list_handlers = {
            "unordered": self._handle_unordered_item,
            "ordered_numeric": self._handle_ordered_numeric_item,
            "checklist": self._handle_checklist_item,
            "definition": self._handle_definition_item,
            "alpha": self._handle_alpha_item,
            "roman": self._handle_roman_item,
        }

    def parse(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> "ParseResult":
        """統一リスト解析 - ListParserProtocol準拠"""
        from ..core.parsing.base.parser_protocols import ParseResult
        from ..core.ast_nodes.node import Node

        try:
            # Core parser がある場合は優先使用
            if self.core_parser:
                try:
                    legacy_result = self.core_parser.parse(content)
                    return self._convert_to_parse_result(legacy_result)
                except Exception as e:
                    self.logger.warning(f"Core parser failed, using built-in: {e}")

            # 統合解析実装
            all_nodes = []

            # 1. Kumihanブロック形式の検出と処理
            if self._is_kumihan_list_block(content):
                kumihan_nodes = self._parse_kumihan_list_block(content)
                all_nodes.extend(kumihan_nodes)
            else:
                # 2. 通常のリスト解析
                regular_nodes = self._parse_regular_lists(content, context)
                all_nodes.extend(regular_nodes)

            return ParseResult(
                success=True,
                nodes=all_nodes,
                errors=[],
                warnings=[],
                metadata={
                    "total_items": len(all_nodes),
                    "parser_type": "unified_list",
                    "nesting_detected": self._has_nested_structure(all_nodes),
                },
            )

        except Exception as e:
            self.logger.error(f"List parsing error: {e}")
            return self._create_error_parse_result(str(e), content)

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """バリデーション - エラーリスト返却"""
        try:
            errors = []
            lines = content.strip().split("\n")

            # Kumihanブロック形式の検証
            if self._is_kumihan_list_block(content):
                errors.extend(self._validate_kumihan_list_block(content))
            else:
                # 通常のリスト検証
                errors.extend(self._validate_regular_lists(lines))

            return errors
        except Exception as e:
            return [f"Validation failed: {e}"]

    def _validate_regular_lists(self, lines: List[str]) -> List[str]:
        """通常のリスト検証"""
        errors = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            list_type = self.detect_list_type(line)
            if list_type:
                # リスト項目の基本検証
                if list_type == "unordered" and len(stripped) < 3:
                    errors.append(
                        f"Invalid unordered list item at line {i+1}: too short"
                    )
                elif list_type == "ordered_numeric" and len(stripped) < 4:
                    errors.append(f"Invalid ordered list item at line {i+1}: too short")
                elif list_type == "checklist":
                    # チェックリスト形式の検証
                    if not self._validate_checklist_format(stripped):
                        errors.append(f"Invalid checklist format at line {i+1}: {line}")
                elif list_type == "definition":
                    # 定義リスト形式の検証
                    if not self._validate_definition_format(stripped):
                        errors.append(
                            f"Invalid definition list format at line {i+1}: {line}"
                        )

        return errors

    def _validate_kumihan_list_block(self, content: str) -> List[str]:
        """Kumihanリストブロックの検証"""
        errors = []
        lines = content.split("\n")

        start_found = False
        end_found = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if self.list_patterns["kumihan_list"].match(stripped):
                if start_found:
                    errors.append(f"Duplicate list start marker at line {i+1}")
                start_found = True
            elif self.list_patterns["kumihan_end"].match(stripped):
                if not start_found:
                    errors.append(f"List end marker without start at line {i+1}")
                end_found = True

        if start_found and not end_found:
            errors.append("Unclosed Kumihan list block: missing ## marker")

        return errors

    def _validate_checklist_format(self, line: str) -> bool:
        """チェックリスト形式の検証"""
        match = self.list_patterns["checklist"].match(line)
        if not match:
            return False

        _, check_state, content = match.groups()
        return check_state in ["x", "X", " "] and len(content.strip()) > 0

    def _validate_definition_format(self, line: str) -> bool:
        """定義リスト形式の検証"""
        match = self.list_patterns["definition"].match(line)
        if not match:
            return False

        _, term, definition = match.groups()
        return len(term.strip()) > 0 and len(definition.strip()) > 0

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        return {
            "name": "UnifiedListParser",
            "version": "3.0.0",
            "supported_formats": [
                "kumihan",
                "list",
                "markdown",
                "checklist",
                "definition",
            ],
            "capabilities": [
                "list_parsing",
                "nested_list_support",
                "ordered_list_parsing",
                "unordered_list_parsing",
                "checklist_parsing",
                "definition_list_parsing",
                "alpha_list_parsing",
                "roman_list_parsing",
                "kumihan_block_format",
                "list_type_detection",
                "nesting_level_detection",
                "error_recovery",
                "mixed_format_support",
            ],
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = self.get_parser_info()["supported_formats"]
        return format_hint.lower() in supported

    def parse_list_items(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List["Node"]:
        """リストアイテムをパース"""
        from ..core.ast_nodes.node import Node

        try:
            nodes = []
            lines = content.strip().split("\n")

            for line in lines:
                stripped = line.strip()
                if stripped:
                    list_type = self.detect_list_type(line)
                    if list_type:
                        # リストアイテムとしてノード作成
                        content_text = self._extract_list_content(line)
                        node = Node(
                            type=f"{list_type}_item",
                            content=content_text,
                            attributes={
                                "nesting_level": self.get_list_nesting_level(line),
                                "original_line": line,
                            },
                        )
                        nodes.append(node)

            return nodes
        except Exception as e:
            self.logger.error(f"List item parsing error: {e}")
            return []

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional["ParseContext"] = None
    ) -> List["Node"]:
        """ネストリストをパース"""
        from ..core.ast_nodes.node import Node

        try:
            nodes = []
            lines = content.strip().split("\n")
            current_item = None
            child_lines = []

            for line in lines:
                nesting_level = self.get_list_nesting_level(line)

                if nesting_level == level:
                    # 現在のレベルのアイテム
                    if current_item and child_lines:
                        # 子要素を処理
                        child_nodes = self.parse_nested_list(
                            "\n".join(child_lines), level + 1, context
                        )
                        if current_item.children is None:
                            current_item.children = []
                        current_item.children.extend(child_nodes)
                        child_lines = []

                    # 新しいアイテム作成
                    list_type = self.detect_list_type(line)
                    content_text = self._extract_list_content(line)
                    current_item = Node(
                        type=f"{list_type}_item" if list_type else "list_item",
                        content=content_text,
                        attributes={
                            "nesting_level": nesting_level,
                            "original_line": line,
                        },
                    )
                    nodes.append(current_item)
                elif nesting_level > level:
                    # 子要素
                    child_lines.append(line)

            # 最後のアイテムの子要素処理
            if current_item and child_lines:
                child_nodes = self.parse_nested_list(
                    "\n".join(child_lines), level + 1, context
                )
                if current_item.children is None:
                    current_item.children = []
                current_item.children.extend(child_nodes)

            return nodes
        except Exception as e:
            self.logger.error(f"Nested list parsing error: {e}")
            return []

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出"""
        stripped = line.strip()
        if not stripped:
            return None

        # インデントを除去した実際のコンテンツ部分
        content_start = len(line) - len(line.lstrip())
        actual_content = line[content_start:]

        # 順序なしリスト
        if (
            actual_content.startswith("- ")
            or actual_content.startswith("* ")
            or actual_content.startswith("+ ")
        ):
            return "unordered"

        # 順序ありリスト
        if len(actual_content) > 1 and actual_content[0].isdigit():
            for i, char in enumerate(actual_content[1:], 1):
                if char == ".":
                    if i < len(actual_content) - 1 and actual_content[i + 1] == " ":
                        return "ordered"
                    break
                elif not char.isdigit():
                    break

        return None

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得"""
        # インデント数でネストレベルを判定
        content_start = len(line) - len(line.lstrip())

        # 通常は4スペースまたは1タブで1レベル
        if "\t" in line[:content_start]:
            return line[:content_start].count("\t")
        else:
            return content_start // 4

    def _extract_list_content(self, line: str) -> str:
        """リスト行からコンテンツ部分を抽出"""
        stripped = line.strip()

        # 順序なしリスト
        if stripped.startswith("- "):
            return stripped[2:].strip()
        elif stripped.startswith("* "):
            return stripped[2:].strip()
        elif stripped.startswith("+ "):
            return stripped[2:].strip()

        # 順序ありリスト
        if len(stripped) > 1 and stripped[0].isdigit():
            for i, char in enumerate(stripped[1:], 1):
                if char == ".":
                    if i < len(stripped) - 1 and stripped[i + 1] == " ":
                        return stripped[i + 2 :].strip()
                    break
                elif not char.isdigit():
                    break

        return stripped

    def _convert_to_parse_result(self, legacy_result: Any) -> "ParseResult":
        """Dict結果をParseResultに変換"""
        from ..core.parsing.base.parser_protocols import ParseResult

        if isinstance(legacy_result, dict):
            return ParseResult(
                success=not legacy_result.get("error"),
                nodes=[],  # TODO: 適切なNode変換
                errors=[legacy_result["error"]] if legacy_result.get("error") else [],
                warnings=[],
                metadata=legacy_result,
            )
        else:
            return ParseResult(
                success=True,
                nodes=[],
                errors=[],
                warnings=[],
                metadata={"raw_result": legacy_result},
            )

    def _create_error_parse_result(
        self, error_msg: str, original_content: str
    ) -> "ParseResult":
        """エラー結果作成"""
        from ..core.parsing.base.parser_protocols import ParseResult

        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "original_content": original_content,
                "parser_type": "unified_list",
            },
        )

    # === 統合機能実装メソッド ===

    def _is_kumihan_list_block(self, content: str) -> bool:
        """Kumihanリストブロック形式かどうか判定"""
        lines = content.strip().split("\n")
        return any(
            self.list_patterns["kumihan_list"].match(line.strip()) for line in lines
        )

    def _parse_kumihan_list_block(self, content: str) -> List["Node"]:
        """Kumihanリストブロック形式の解析"""
        from ..core.ast_nodes.node import Node

        nodes = []
        lines = content.split("\n")
        in_block = False
        block_content = []

        for line in lines:
            stripped = line.strip()

            if self.list_patterns["kumihan_list"].match(stripped):
                in_block = True
                continue
            elif self.list_patterns["kumihan_end"].match(stripped):
                if in_block and block_content:
                    # ブロック内容を解析
                    block_text = "\n".join(block_content)
                    block_nodes = self._parse_regular_lists(block_text)
                    nodes.extend(block_nodes)
                in_block = False
                block_content = []
            elif in_block:
                block_content.append(line)

        return nodes

    def _parse_regular_lists(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List["Node"]:
        """通常のリスト解析"""
        from ..core.ast_nodes.node import Node

        nodes = []
        lines = content.strip().split("\n") if isinstance(content, str) else content

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped or self.list_patterns["empty_line"].match(line):
                i += 1
                continue

            list_type = self._detect_full_list_type(line)
            if list_type:
                # リストブロックを抽出
                block_lines, consumed = self._extract_list_block(lines[i:], list_type)

                # ブロックを解析
                if list_type in ["unordered", "ordered_numeric"]:
                    block_nodes = self._parse_nested_structure(block_lines)
                else:
                    block_nodes = self._parse_specialized_list(block_lines, list_type)

                nodes.extend(block_nodes)
                i += consumed
            else:
                i += 1

        return nodes

    def _detect_full_list_type(self, line: str) -> Optional[str]:
        """拡張リストタイプ検出"""
        stripped = line.strip()
        if not stripped:
            return None

        for list_type, pattern in self.list_patterns.items():
            if list_type not in ["kumihan_list", "kumihan_end", "indent", "empty_line"]:
                if pattern.match(stripped):
                    return list_type

        return None

    def _extract_list_block(
        self, lines: List[str], initial_type: str
    ) -> Tuple[List[str], int]:
        """リストブロックを抽出"""
        block_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                # 空行は含めて継続
                block_lines.append(line)
                i += 1
                continue

            current_type = self._detect_full_list_type(line)
            if current_type and self._is_compatible_list_type(
                initial_type, current_type
            ):
                block_lines.append(line)
                i += 1
            else:
                break

        return block_lines, i

    def _is_compatible_list_type(self, initial_type: str, current_type: str) -> bool:
        """リストタイプの互換性判定"""
        # 基本タイプ（順序なし・順序ありは相互変換可能）
        basic_types = {"unordered", "ordered_numeric"}
        if initial_type in basic_types and current_type in basic_types:
            return True

        # 特殊タイプは単独
        return initial_type == current_type

    def _parse_nested_structure(self, lines: List[str]) -> List["Node"]:
        """ネスト構造の解析"""
        return self.parse_nested_list("\n".join(lines))

    def _parse_specialized_list(self, lines: List[str], list_type: str) -> List["Node"]:
        """特殊化リストの解析"""
        from ..core.ast_nodes.node import Node

        nodes = []
        for line in lines:
            stripped = line.strip()
            if stripped and self._detect_full_list_type(line) == list_type:
                handler = self.list_handlers.get(list_type)
                if handler:
                    node = handler(line)
                    if node:
                        nodes.append(node)

        return nodes

    def _has_nested_structure(self, nodes: List["Node"]) -> bool:
        """ネスト構造の存在確認"""
        for node in nodes:
            if hasattr(node, "children") and node.children:
                return True
            if (
                hasattr(node, "attributes")
                and node.attributes.get("nesting_level", 0) > 0
            ):
                return True
        return False

    # === リストハンドラー実装 ===

    def _handle_unordered_item(self, line: str) -> Optional["Node"]:
        """順序なしリストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["unordered"].match(line.strip())
        if not match:
            return None

        indent, content = match.groups()
        marker = line.strip()[len(indent) : len(indent) + 1]

        return Node(
            type="unordered_list_item",
            content=content.strip(),
            attributes={
                "marker": marker,
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )

    def _handle_ordered_numeric_item(self, line: str) -> Optional["Node"]:
        """順序付き数値リストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["ordered_numeric"].match(line.strip())
        if not match:
            return None

        indent, number, content = match.groups()

        return Node(
            type="ordered_list_item",
            content=content.strip(),
            attributes={
                "number": int(number),
                "marker": f"{number}.",
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )

    def _handle_checklist_item(self, line: str) -> Optional["Node"]:
        """チェックリストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["checklist"].match(line.strip())
        if not match:
            return None

        indent, check_state, content = match.groups()
        checked = check_state.lower() == "x"

        return Node(
            type="checklist_item",
            content=content.strip(),
            attributes={
                "checked": checked,
                "check_state": check_state,
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )

    def _handle_definition_item(self, line: str) -> Optional["Node"]:
        """定義リストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["definition"].match(line.strip())
        if not match:
            return None

        indent, term, definition = match.groups()

        return Node(
            type="definition_item",
            content=definition.strip(),
            attributes={
                "term": term.strip(),
                "definition": definition.strip(),
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )

    def _handle_alpha_item(self, line: str) -> Optional["Node"]:
        """アルファベットリストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["alpha"].match(line.strip())
        if not match:
            return None

        indent, letter, content = match.groups()

        return Node(
            type="alpha_list_item",
            content=content.strip(),
            attributes={
                "letter": letter,
                "marker": f"{letter}.",
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )

    def _handle_roman_item(self, line: str) -> Optional["Node"]:
        """ローマ数字リストアイテム処理"""
        from ..core.ast_nodes.node import Node

        match = self.list_patterns["roman"].match(line.strip())
        if not match:
            return None

        indent, roman, content = match.groups()

        return Node(
            type="roman_list_item",
            content=content.strip(),
            attributes={
                "roman": roman.lower(),
                "marker": f"{roman}.",
                "indent_level": len(indent),
                "nesting_level": self.get_list_nesting_level(line),
            },
        )


# Alias for backward compatibility
ListParser = UnifiedListParser
