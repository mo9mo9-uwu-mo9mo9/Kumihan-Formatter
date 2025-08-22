"""統一リストパーサー - 最適化版"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    ListParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType
from .parsers.nested_parser import NestedListParser
from .parsers.ordered_parser import OrderedListParser
from .parsers.unordered_parser import UnorderedListParser


class UnifiedListParser(UnifiedParserBase, CompositeMixin, ListParserProtocol):
    """統一リストパーサー - 各専用パーサーを統合してAPI互換性維持"""

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.LIST)

        # 専用パーサーの初期化
        self.ordered_parser = OrderedListParser()
        self.unordered_parser = UnorderedListParser()
        self.nested_parser = NestedListParser()

        # パターンとハンドラー設定
        self._setup_patterns_and_handlers()

    def _setup_patterns_and_handlers(self) -> None:
        """パターンとハンドラーの設定"""
        self.list_patterns = {
            "unordered": re.compile(r"^(\s*)[-*+]\s+(.+)$"),
            "ordered": re.compile(r"^(\s*)(\d+)\.\s+(.+)$"),
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([x\s])\]\s*(.+)$"),
            "alpha": re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$"),
            "roman": re.compile(
                r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x)\.\s+(.+)$", re.IGNORECASE
            ),
            "indent": re.compile(r"^(\s*)"),
        }

        self.list_handlers = {
            "unordered": self.unordered_parser.handle_unordered_list,
            "ordered": self.ordered_parser.handle_ordered_list,
            "definition": self.unordered_parser.handle_definition_list,
            "checklist": self.unordered_parser.handle_checklist,
            "alpha": self.ordered_parser.handle_alpha_list,
            "roman": self.ordered_parser.handle_roman_list,
        }

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """リスト記法の解析可能性を判定"""
        if not super().can_parse(content):
            return False

        lines = content.split("\n") if isinstance(content, str) else content
        list_count = sum(1 for line in lines if self._detect_list_type(line.rstrip()))
        return list_count >= 2

    def _detect_list_type(self, line: str) -> Optional[str]:
        """行のリストタイプを検出"""
        if not line.strip():
            return None

        for list_type, pattern in self.list_patterns.items():
            if list_type != "indent" and pattern.match(line):
                return list_type
        return None

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """リスト解析の実装"""
        self._start_timer("list_parsing")

        try:
            lines = content.split("\n") if isinstance(content, str) else content
            root_node = create_node("document", content="")

            i = 0
            while i < len(lines):
                line = lines[i].rstrip()

                if not line.strip():
                    i += 1
                    continue

                list_type = self._detect_list_type(line)
                if list_type:
                    list_node, consumed = self._parse_list_block(lines[i:], list_type)
                    if list_node:
                        if root_node.children is None:
                            root_node.children = []
                        root_node.children.append(list_node)
                    i += consumed
                else:
                    text_node = create_node("text", content=line)
                    if root_node.children is None:
                        root_node.children = []
                    root_node.children.append(text_node)
                    i += 1

            self._end_timer("list_parsing")
            return root_node

        except Exception as e:
            self.add_error(f"リスト解析エラー: {str(e)}")
            return create_node("error", content=f"List parse error: {e}")

    def _parse_list_block(
        self, lines: List[str], initial_type: str
    ) -> Tuple[Optional[Node], int]:
        """リストブロックの解析"""
        if not lines:
            return None, 0

        list_items = []
        i = 0
        base_indent = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if not line.strip():
                i += 1
                continue

            # インデント取得
            indent_match = self.list_patterns["indent"].match(line)
            indent = len(indent_match.group(1)) if indent_match else 0

            list_type = self._detect_list_type(line)
            if not list_type:
                break

            # 基準インデント設定
            if i == 0:
                base_indent = indent
            elif indent < base_indent:
                break

            # リスト項目解析
            item_node = self._parse_list_item(line, list_type)
            if item_node:
                item_node.metadata["indent_level"] = indent
                item_node.metadata["relative_level"] = indent - base_indent
                list_items.append(item_node)

            i += 1

        if list_items:
            return self._create_list_node(list_items, initial_type), i
        return None, 0

    def _parse_list_item(self, line: str, list_type: str) -> Optional[Node]:
        """個別のリスト項目を解析"""
        handler = self.list_handlers.get(list_type)
        return (
            handler(line) if handler else create_node("list_item", content=line.strip())
        )

    def _create_list_node(self, items: List[Node], list_type: str) -> Node:
        """リストノードの作成"""
        if not items:
            return create_node("list", content="")

        # ネスト構造構築
        nested_structure = self.nested_parser.build_nested_structure_list(items)

        # リストタイプ決定
        primary_type = self._determine_primary_list_type(items)

        list_node = create_node("list", content="")
        list_node.metadata.update(
            {
                "type": primary_type,
                "item_count": len(items),
                "has_nesting": self.nested_parser.has_nested_items(items),
            }
        )
        list_node.children = nested_structure
        return list_node

    def _determine_primary_list_type(self, items: List[Node]) -> str:
        """主要なリストタイプを決定"""
        type_counts: Dict[str, int] = {}
        for item in items:
            item_type = item.metadata.get("type", "unordered")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        return (
            max(type_counts, key=lambda x: type_counts.get(x, 0))
            if type_counts
            else "unordered"
        )

    # 外部API メソッド（互換性維持）
    def parse_list_from_text(self, text: str, list_type: Optional[str] = None) -> Node:
        """テキストからリストを解析"""
        if list_type and list_type in self.list_handlers:
            lines = text.split("\n")
            items = [
                self.list_handlers[list_type](line) for line in lines if line.strip()
            ]
            return self._create_list_node([item for item in items if item], list_type)
        else:
            parse_result = self.parse_with_result(text)
            if parse_result.success and parse_result.nodes:
                return (
                    parse_result.nodes[0]
                    if parse_result.nodes[0].children
                    else create_node("list", content="")
                )
            else:
                return create_node("list", content="")

    def convert_list_type(self, list_node: Node, target_type: str) -> Node:
        """リストタイプの変換"""
        if target_type not in self.list_handlers:
            self.add_warning(f"未サポートのリストタイプ: {target_type}")
            return list_node

        new_list = create_node("list", content=list_node.content)
        new_list.metadata.update(list_node.metadata)
        new_list.metadata["type"] = target_type
        new_list.children = list_node.children
        return new_list

    def extract_checklist_status(self, list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出"""
        return self.unordered_parser.extract_checklist_status(list_node)

    def get_list_statistics(self) -> Dict[str, Any]:
        """リスト解析統計を取得"""
        stats = self._get_performance_stats()
        stats.update(
            {
                "supported_list_types": list(self.list_handlers.keys()),
                "parser_type": self.parser_type,
            }
        )
        return stats

    # プロトコル準拠メソッド
    # UnifiedParserBase.parseメソッドを使用（オーバーライドしない）
    # ParseResultを返すプロトコル用のエイリアスメソッド
    def parse_with_result(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """ParseResultを返す解析インターフェース（プロトコル準拠）"""
        try:
            # 基底クラスのparseメソッドを使用
            node_result = super().parse(content)
            return create_parse_result(nodes=[node_result], success=True)
        except Exception as e:
            parse_result = create_parse_result(success=False)
            parse_result.add_error(f"リストパース失敗: {e}")
            return parse_result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション実装"""
        errors = []
        try:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip() and not self._is_valid_list_item(line):
                    errors.append(f"行{i+1}: 無効なリスト項目形式")
        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報"""
        return {
            "name": "UnifiedListParser",
            "version": "2.0.0",
            "supported_formats": ["list", "ordered", "unordered", "checklist"],
            "capabilities": ["nested_lists", "block_format", "character_parsing"],
            "parser_type": self.parser_type,
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定"""
        return format_hint in [
            "list",
            "ordered",
            "unordered",
            "checklist",
            "definition",
        ]

    def _is_valid_list_item(self, line: str) -> bool:
        """リスト項目の有効性チェック"""
        for pattern in self.list_patterns.values():
            if pattern.match(line):
                return True
        return False

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得（抽象メソッド実装）"""
        # インデント数でネストレベル判定
        stripped = line.lstrip()
        if not stripped:
            return 0
        
        indent_count = len(line) - len(stripped)
        # 2スペースまたは1タブで1レベル
        return max(0, indent_count // 2)

    # 継続互換性メソッド（プロトコル準拠のシグネチャに変更）
    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """ネストリストをパース（プロトコル準拠）"""
        return self.nested_parser.parse_nested_list(content, level)

    def parse_list_items(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """リストアイテムをパース（プロトコル準拠）"""
        lines = content.split("\n")
        items = []
        for line in lines:
            if line.strip():
                list_type = self._detect_list_type(line.strip())
                if list_type:
                    item = self._parse_list_item(line.strip(), list_type)
                    if item is not None:
                        items.append(item)
        return items

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出"""
        return self._detect_list_type(line)

    def parse_legacy(self, text: str) -> List[Node]:
        """レガシーparse メソッドのエイリアス"""
        result = self._parse_implementation(text)
        return [result] if isinstance(result, Node) else result

    # inline_handler.py互換性メソッド
    def is_list_line(self, line: str) -> Optional[str]:
        """リスト行判定 - inline_handler.py互換"""
        return self._detect_list_type(line.strip())

    def parse_unordered_list(
        self, lines: List[str], current: int
    ) -> Tuple[Optional[Node], int]:
        """順序なしリスト解析 - inline_handler.py互換"""
        if current >= len(lines):
            return None, current + 1

        # 順序なしリストを検出して解析
        start_line = lines[current].strip()
        if not self.list_patterns["unordered"].match(start_line):
            return None, current + 1

        # リストブロック全体を取得
        end_index = current + 1
        while end_index < len(lines):
            line = lines[end_index].strip()
            if not line or not self._detect_list_type(line):
                break
            end_index += 1

        # リストブロックを解析
        list_content = "\n".join(lines[current:end_index])
        try:
            list_node = self.unordered_parser.handle_unordered_list(list_content)
            return list_node, end_index
        except Exception:
            return None, current + 1

    def parse_ordered_list(
        self, lines: List[str], current: int
    ) -> Tuple[Optional[Node], int]:
        """順序付きリスト解析 - inline_handler.py互換"""
        if current >= len(lines):
            return None, current + 1

        # 順序付きリストを検出して解析
        start_line = lines[current].strip()
        if not self.list_patterns["ordered"].match(start_line):
            return None, current + 1

        # リストブロック全体を取得
        end_index = current + 1
        while end_index < len(lines):
            line = lines[end_index].strip()
            if not line or not self._detect_list_type(line):
                break
            end_index += 1

        # リストブロックを解析
        list_content = "\n".join(lines[current:end_index])
        try:
            list_node = self.ordered_parser.handle_ordered_list(list_content)
            return list_node, end_index
        except Exception:
            return None, current + 1
