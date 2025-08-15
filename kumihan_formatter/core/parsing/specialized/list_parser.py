"""統一リストパーサー

Issue #880 Phase 2B: 既存のListParser系統を統合
- core/list_parser.py
- core/list_parser_core.py
- core/nested_list_parser.py
- core/list_parser_factory.py
の機能を統合・整理
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..protocols import ParserType


class UnifiedListParser(UnifiedParserBase, CompositeMixin):
    """統一リストパーサー

    各種リスト形式の解析:
    - 順序なしリスト: -, *, +
    - 順序付きリスト: 1., 2., 3.
    - ネストしたリスト
    - 定義リスト
    - チェックリスト
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.LIST)

        # リスト解析の設定
        self._setup_list_patterns()
        self._setup_list_handlers()

    def _setup_list_patterns(self) -> None:
        """リスト解析パターンの設定"""
        self.list_patterns = {
            # 順序なしリスト: - item, * item, + item
            "unordered": re.compile(r"^(\s*)[-*+]\s+(.+)$"),
            # 順序付きリスト: 1. item, 2. item
            "ordered": re.compile(r"^(\s*)(\d+)\.\s+(.+)$"),
            # 定義リスト: term :: definition
            "definition": re.compile(r"^(\s*)(.+?)\s*::\s*(.+)$"),
            # チェックリスト: - [ ] item, - [x] item
            "checklist": re.compile(r"^(\s*)[-*+]\s*\[([x\s])\]\s*(.+)$"),
            # アルファベットリスト: a. item, b. item
            "alpha": re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$"),
            # ローマ数字リスト: i. item, ii. item
            "roman": re.compile(
                r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x)\.\s+(.+)$", re.IGNORECASE
            ),
            # ネストレベル検出用
            "indent": re.compile(r"^(\s*)"),
        }

    def _setup_list_handlers(self) -> None:
        """リストタイプハンドラーの設定"""
        self.list_handlers = {
            "unordered": self._handle_unordered_list,
            "ordered": self._handle_ordered_list,
            "definition": self._handle_definition_list,
            "checklist": self._handle_checklist,
            "alpha": self._handle_alpha_list,
            "roman": self._handle_roman_list,
        }

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """リスト記法の解析可能性を判定"""
        if not super().can_parse(content):
            return False

        lines = content.split("\n") if isinstance(content, str) else content

        # リストパターンが含まれているかチェック
        list_line_count = 0
        for line in lines:
            if self._detect_list_type(line.rstrip()):
                list_line_count += 1

        # 最低2行のリスト項目があればリストとみなす
        return list_line_count >= 2

    def _detect_list_type(self, line: str) -> Optional[str]:
        """行のリストタイプを検出"""
        if not line.strip():
            return None

        for list_type, pattern in self.list_patterns.items():
            if list_type == "indent":
                continue

            if pattern.match(line):
                return list_type

        return None

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """リスト解析の実装"""
        self._start_timer("list_parsing")

        try:
            lines = content.split("\n") if isinstance(content, str) else content

            # 解析結果を格納するノード
            root_node = create_node("document", content="")

            i = 0
            while i < len(lines):
                line = lines[i].rstrip()

                if not line.strip():
                    i += 1
                    continue

                # リストタイプの検出
                list_type = self._detect_list_type(line)

                if list_type:
                    # リストブロックの解析
                    list_node, consumed_lines = self._parse_list_block(
                        lines[i:], list_type
                    )
                    if list_node:
                        if root_node.children is None:
                            root_node.children = []
                        root_node.children.append(list_node)
                    i += consumed_lines
                else:
                    # 非リスト行
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
        current_indent_level = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if not line.strip():
                i += 1
                continue

            # インデントレベルの取得
            indent_match = self.list_patterns["indent"].match(line)
            indent = len(indent_match.group(1)) if indent_match else 0

            # リストタイプの検出
            list_type = self._detect_list_type(line)

            if not list_type:
                # リストでない行に到達したらリスト終了
                break

            # 最初の項目のインデントレベルを基準に設定
            if i == 0:
                current_indent_level = indent

            # インデントレベルが基準より少ない場合はリスト終了
            if indent < current_indent_level:
                break

            # リスト項目の解析
            item_node = self._parse_list_item(line, list_type)
            if item_node:
                # ネストレベルの設定
                item_node.metadata["indent_level"] = indent
                item_node.metadata["relative_level"] = indent - current_indent_level
                list_items.append(item_node)

            i += 1

        if list_items:
            # リストノードの作成
            list_node = self._create_list_node(list_items, initial_type)
            return list_node, i

        return None, 0

    def _parse_list_item(self, line: str, list_type: str) -> Optional[Node]:
        """個別のリスト項目を解析"""
        handler = self.list_handlers.get(list_type)
        if handler:
            return handler(line)

        # デフォルトハンドラー
        return create_node("list_item", content=line.strip())

    def _handle_unordered_list(self, line: str) -> Node:
        """順序なしリストの処理"""
        match = self.list_patterns["unordered"].match(line)
        if match:
            indent = match.group(1)
            content = match.group(2)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {
                    "type": "unordered",
                    "marker": line.strip()[0],  # -, *, +
                    "indent": len(indent),
                }
            )
            return node

        return create_node("list_item", content=line.strip())

    def _handle_ordered_list(self, line: str) -> Node:
        """順序付きリストの処理"""
        match = self.list_patterns["ordered"].match(line)
        if match:
            indent = match.group(1)
            number = int(match.group(2))
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {"type": "ordered", "number": number, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def _handle_definition_list(self, line: str) -> Node:
        """定義リストの処理"""
        match = self.list_patterns["definition"].match(line)
        if match:
            indent = match.group(1)
            term = match.group(2)
            definition = match.group(3)

            node = create_node("definition_item", content=definition)
            node.metadata.update(
                {
                    "type": "definition",
                    "term": term,
                    "definition": definition,
                    "indent": len(indent),
                }
            )
            return node

        return create_node("list_item", content=line.strip())

    def _handle_checklist(self, line: str) -> Node:
        """チェックリストの処理"""
        match = self.list_patterns["checklist"].match(line)
        if match:
            indent = match.group(1)
            checked = match.group(2).lower() == "x"
            content = match.group(3)

            node = create_node("checklist_item", content=content)
            node.metadata.update(
                {"type": "checklist", "checked": checked, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def _handle_alpha_list(self, line: str) -> Node:
        """アルファベットリストの処理"""
        match = self.list_patterns["alpha"].match(line)
        if match:
            indent = match.group(1)
            letter = match.group(2)
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {"type": "alpha", "letter": letter, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def _handle_roman_list(self, line: str) -> Node:
        """ローマ数字リストの処理"""
        match = self.list_patterns["roman"].match(line)
        if match:
            indent = match.group(1)
            roman = match.group(2)
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {"type": "roman", "roman": roman, "indent": len(indent)}
            )
            return node

        return create_node("list_item", content=line.strip())

    def _create_list_node(self, items: List[Node], list_type: str) -> Node:
        """リストノードの作成（ネスト構造対応）"""
        if not items:
            return create_node("list", content="")

        # ネスト構造の構築
        nested_structure = self._build_nested_structure(items)

        # リストタイプの決定
        primary_type = self._determine_primary_list_type(items)

        list_node = create_node("list", content="")
        list_node.metadata.update(
            {
                "type": primary_type,
                "item_count": len(items),
                "has_nesting": self._has_nested_items(items),
            }
        )

        # ネスト構造をリストノードに追加
        list_node.children = nested_structure

        return list_node

    def _build_nested_structure(self, items: List[Node]) -> List[Node]:
        """ネスト構造の構築"""
        if not items:
            return []

        result = []
        stack: list[tuple[Node, int]] = []  # (node, level) のスタック

        for item in items:
            current_level = item.metadata.get("relative_level", 0)

            # スタックから現在のレベル以上の項目を削除
            while stack and stack[-1][1] >= current_level:
                stack.pop()

            if current_level == 0:
                # ルートレベルの項目
                result.append(item)
                stack.append((item, current_level))
            else:
                # ネストした項目
                if stack:
                    parent_node, parent_level = stack[-1]

                    # 親ノードの子リストを作成
                    if "children" not in parent_node.metadata:
                        parent_node.metadata["children"] = []

                    parent_node.metadata["children"].append(item)
                    stack.append((item, current_level))
                else:
                    # 親がない場合はルートレベルに追加
                    result.append(item)
                    stack.append((item, current_level))

        return result

    def _determine_primary_list_type(self, items: List[Node]) -> str:
        """主要なリストタイプを決定"""
        type_counts: dict[str, int] = {}

        for item in items:
            item_type = item.metadata.get("type", "unordered")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        # 最も多いタイプを返す
        if type_counts:
            return max(type_counts, key=type_counts.get)

        return "unordered"

    def _has_nested_items(self, items: List[Node]) -> bool:
        """ネストした項目があるかチェック"""
        for item in items:
            if item.metadata.get("relative_level", 0) > 0:
                return True
        return False

    # 外部API メソッド

    def parse_list_from_text(self, text: str, list_type: Optional[str] = None) -> Node:
        """テキストからリストを解析（外部API）"""
        if list_type and list_type in self.list_handlers:
            # 指定されたタイプでの解析
            lines = text.split("\n")
            items = []
            for line in lines:
                if line.strip():
                    item = self.list_handlers[list_type](line)
                    if item:
                        items.append(item)

            return self._create_list_node(items, list_type)
        else:
            # 自動判定での解析
            return (
                self.parse(text).children[0]
                if self.parse(text).children
                else create_node("list", content="")
            )

    def convert_list_type(self, list_node: Node, target_type: str) -> Node:
        """リストタイプの変換"""
        if target_type not in self.list_handlers:
            self.add_warning(f"未サポートのリストタイプ: {target_type}")
            return list_node

        # 新しいリストノードを作成
        new_list = create_node("list", content=list_node.content)
        new_list.metadata.update(list_node.metadata)
        new_list.metadata["type"] = target_type

        # 子項目のタイプを変更
        for child in list_node.children:
            if child.node_type == "list_item":
                child.metadata["type"] = target_type
                # タイプ固有のメタデータを更新
                if target_type == "ordered":
                    child.metadata["number"] = child.metadata.get("number", 1)
                elif target_type == "alpha":
                    child.metadata["letter"] = chr(
                        ord("a") + child.metadata.get("number", 1) - 1
                    )

        new_list.children = list_node.children
        return new_list

    def extract_checklist_status(self, list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出"""
        if list_node.metadata.get("type") != "checklist":
            return {"error": "Not a checklist"}

        total_items = 0
        checked_items = 0

        def count_items(node: Node):
            nonlocal total_items, checked_items

            if node.node_type == "checklist_item":
                total_items += 1
                if node.metadata.get("checked", False):
                    checked_items += 1

            # ネストした項目もカウント
            for child in node.metadata.get("children", []):
                count_items(child)

        count_items(list_node)

        completion_rate = (checked_items / total_items * 100) if total_items > 0 else 0

        return {
            "total_items": total_items,
            "checked_items": checked_items,
            "unchecked_items": total_items - checked_items,
            "completion_rate": completion_rate,
            "completed": checked_items == total_items and total_items > 0,
        }

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
