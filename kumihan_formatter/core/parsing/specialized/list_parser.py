"""統一リストパーサー

Issue #912: Parser系統合リファクタリング
重複ListParserを完全統合:
- core/list_parser.py (126行、基本リスト解析)
- core/list_parser_core.py (363行、新記法ブロック形式)
- core/nested_list_parser.py (69行、ネスト構造)
- core/list_parser_factory.py (61行、ファクトリーパターン)
- core/parsing/specialized/list_parser.py (統一実装、最も完全)

統合機能:
- 順序付き・順序なしリスト解析
- ネストリスト構造（最大3レベル）
- 定義リスト・チェックリスト
- # リスト # ブロック形式
- 文字単位解析（スタック）
- ファクトリーパターン
- 後方互換性維持
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ...ast_nodes import Node, create_node, list_item, ordered_list, unordered_list
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    ListParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType


class UnifiedListParser(UnifiedParserBase, CompositeMixin, ListParserProtocol):
    """統一リストパーサー

    重複ListParserを統合した包括的リスト解析機能:

    基本リスト形式:
    - 順序なしリスト: -, *, +
    - 順序付きリスト: 1., 2., 3.
    - 定義リスト: term :: definition
    - チェックリスト: - [ ] item, - [x] item
    - アルファベット・ローマ数字リスト

    ネストリスト:
    - 最大3レベルのインデント
    - スペース・タブ混在対応
    - 動的ネスト構造構築

    新記法ブロック:
    - # リスト # ～ ## 形式
    - ネスト対応（スペース1個で1レベル下）

    文字単位解析:
    - スタックベース解析
    - [,] 区切り文字対応

    ファクトリーパターン:
    - リストタイプ自動判定
    - 適切なパーサー選択
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.LIST)

        # リスト解析の設定
        self._setup_list_patterns()
        self._setup_list_handlers()

        # 統合機能: 重複ListParserからの機能
        self._setup_stack_parser()
        self._setup_block_parser()
        self._setup_factory_methods()

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
        nested_structure = self._build_nested_structure_list(items)

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

    def _build_nested_structure_list(self, items: List[Node]) -> List[Node]:
        """ネスト構造の構築（リスト版）"""
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

    # ==========================================
    # 統合機能: 重複ListParserからの機能統合
    # ==========================================

    def _setup_stack_parser(self) -> None:
        """スタックベース解析器の設定（core/list_parser.py から）"""
        self.stack: List[List[Any]] = [[]]
        self.current_string: str = ""

    def _setup_block_parser(self) -> None:
        """ブロック形式解析器の設定（core/list_parser_core.py から）"""
        # ブロック形式解析用パターン
        self.block_patterns = {
            "list_header": re.compile(r"^#\s*リスト\s*#\s*$"),
            "list_end": re.compile(r"^##\s*$"),
            "nested_item": re.compile(r"^(\s*)(.+)$"),
        }

    def _setup_factory_methods(self) -> None:
        """ファクトリーメソッドの設定（core/list_parser_factory.py から）"""
        # パーサー選択ルール
        self.parser_selection_rules = {
            "block_format": self._should_use_block_parser,
            "nested_format": self._should_use_nested_parser,
            "stack_format": self._should_use_stack_parser,
        }

    def parse_char(self, char: str) -> None:
        """文字単位解析（core/list_parser.py から統合）

        Args:
            char: 解析する文字
        """
        if char == "[":
            self.start_list()
        elif char == "]":
            self.end_list()
        elif char == ",":
            self.add_string()
        else:
            self.current_string += char

    def start_list(self) -> None:
        """新しいリストを開始"""
        self.add_string()
        new_list: List[Any] = []
        self.stack[-1].append(new_list)
        self.stack.append(new_list)

    def end_list(self) -> None:
        """現在のリストを終了"""
        self.add_string()
        if len(self.stack) > 1:
            self.stack.pop()
        else:
            raise ValueError("Unmatched closing bracket ]")

    def add_string(self) -> None:
        """現在の文字列をリストに追加"""
        if self.current_string:
            self.stack[-1].append(self.current_string.strip())
            self.current_string = ""

    def get_result(self) -> List[Any]:
        """解析結果を取得"""
        self.add_string()
        return self.stack[0] if self.stack else []

    def parse_list_block(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
        """# リスト # ブロック形式の解析（core/list_parser_core.py から統合）

        Args:
            lines: 全行リスト
            start_index: 開始インデックス

        Returns:
            (解析されたノード, 次のインデックス)
        """
        current_index = start_index + 1  # # リスト # 行をスキップ
        list_items = []

        while current_index < len(lines):
            line = lines[current_index]

            # 終了マーカーをチェック
            if self.block_patterns["list_end"].match(line):
                break

            # 空行はスキップ
            if not line.strip():
                current_index += 1
                continue

            # ネストレベルと内容を解析
            match = self.block_patterns["nested_item"].match(line)
            if match:
                indent = match.group(1)
                content = match.group(2)

                # インデントレベルを計算（スペース1個 = レベル1）
                nest_level = len(indent)

                # リストアイテムノードを作成
                item_node = list_item(content)
                item_node.metadata["nest_level"] = nest_level
                item_node.metadata["indent"] = indent

                list_items.append(item_node)

            current_index += 1

        # ネスト構造を構築
        root_node = self._build_nested_structure(list_items)

        return root_node, current_index + 1

    def parse_nested_list(self, content: str, level: int = 0) -> List[Node]:
        """ネストリストをパース（ListParserProtocol実装）

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル

        Returns:
            パースされたネストリストのノードリスト
        """
        if level > 3:  # 最大3レベル制限
            self.add_warning(f"ネストレベル{level}は制限を超えています（最大3レベル）")
            return []

        lines = content.split("\n")
        nodes = []

        for line in lines:
            if not line.strip():
                continue

            # インデントでネストレベルを判定
            indent_match = self.list_patterns["indent"].match(line)
            if indent_match:
                current_indent = len(indent_match.group(1))
                expected_indent = level * 2  # 2スペース = 1レベル

                if current_indent == expected_indent:
                    # 現在のレベルのアイテム
                    list_type = self.detect_list_type(line.strip())
                    if list_type:
                        node = self._create_list_item_node(
                            line.strip(), list_type, level
                        )
                        nodes.append(node)
                elif current_indent > expected_indent:
                    # より深いネストは再帰処理
                    nested_nodes = self.parse_nested_list(line, level + 1)
                    nodes.extend(nested_nodes)

        return nodes

    def parse_list_items(self, content: str) -> List[Node]:
        """リストアイテムをパース（ListParserProtocol実装）

        Args:
            content: リストコンテンツ

        Returns:
            パースされたリストアイテムのノードリスト
        """
        lines = content.split("\n")
        items = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            list_type = self.detect_list_type(line)
            if list_type:
                item_node = self._create_list_item_node(line, list_type, 0)
                items.append(item_node)

        return items

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出（ListParserProtocol実装）

        Args:
            line: 検査対象の行

        Returns:
            検出されたリストタイプ
        """
        return self._detect_list_type(line)

    def _should_use_block_parser(self, content: str) -> bool:
        """ブロック形式パーサーを使用すべきか判定"""
        return bool(self.block_patterns["list_header"].search(content))

    def _should_use_nested_parser(self, content: str) -> bool:
        """ネスト形式パーサーを使用すべきか判定"""
        lines = content.split("\n")
        indent_levels = set()

        for line in lines:
            if line.strip() and self._detect_list_type(line):
                indent_match = self.list_patterns["indent"].match(line)
                if indent_match:
                    indent_levels.add(len(indent_match.group(1)))

        return len(indent_levels) > 1  # 複数のインデントレベルがある

    def _should_use_stack_parser(self, content: str) -> bool:
        """スタック形式パーサーを使用すべきか判定"""
        return "[" in content and "]" in content and "," in content

    def _build_nested_structure(self, items: List[Node]) -> Node:
        """フラットなアイテムリストからネスト構造を構築"""
        if not items:
            return unordered_list([])

        root_items = []
        stack = []

        for item in items:
            level = item.metadata.get("nest_level", 0)

            # スタックを現在のレベルに調整
            while len(stack) > level:
                stack.pop()

            if level == 0:
                # ルートレベル
                root_items.append(item)
                stack = [item]
            else:
                # ネストレベル
                if stack:
                    parent = stack[-1]
                    if "children" not in parent.metadata:
                        parent.metadata["children"] = []
                    parent.metadata["children"].append(item)
                    stack.append(item)

        return unordered_list(root_items)

    def _create_list_item_node(self, line: str, list_type: str, level: int) -> Node:
        """リストアイテムノードを作成"""
        content = self._extract_item_content(line, list_type)

        if list_type == "checklist":
            # チェックリストの特別処理
            checked = "[x]" in line.lower() or "[✓]" in line
            node = list_item(content)
            node.metadata.update(
                {"type": "checklist_item", "checked": checked, "level": level}
            )
        else:
            # 通常のリストアイテム
            node = list_item(content)
            node.metadata.update({"type": list_type, "level": level})

        return node

    def _extract_item_content(self, line: str, list_type: str) -> str:
        """リストアイテムからコンテンツを抽出"""
        for pattern in self.list_patterns.values():
            if pattern == self.list_patterns["indent"]:
                continue

            match = pattern.match(line)
            if match:
                # パターンによって内容の位置が異なる
                if list_type == "ordered":
                    return (
                        match.group(3) if len(match.groups()) >= 3 else match.group(2)
                    )
                elif list_type == "checklist":
                    return (
                        match.group(3) if len(match.groups()) >= 3 else match.group(2)
                    )
                else:
                    return (
                        match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    )

        return line.strip()

    # ==========================================
    # プロトコル準拠メソッド（ListParserProtocol実装）
    # ==========================================

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース（プロトコル準拠）"""
        try:
            result = self._parse_implementation(content)
            nodes = [result] if isinstance(result, Node) else result
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"リストパース失敗: {e}")
            return result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
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
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedListParser",
            "version": "2.0.0",
            "supported_formats": ["list", "ordered", "unordered", "checklist"],
            "capabilities": ["nested_lists", "block_format", "character_parsing"],
            "parser_type": self.parser_type,
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
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

    # 後方互換性エイリアス
    def parse_legacy(self, text: str) -> List[Node]:
        """レガシーparse メソッドのエイリアス"""
        result = self._parse_implementation(text)
        return [result] if isinstance(result, Node) else result
