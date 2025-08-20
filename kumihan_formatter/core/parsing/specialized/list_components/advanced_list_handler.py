"""高度リストハンドラー - specialized list_parser分割

高度なリスト処理機能を提供:
- アルファベット・ローマ数字リスト
- ネストリスト構造解析
- ブロック形式リスト
- 文字単位解析（スタック）
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ....ast_nodes import Node, create_node


class AdvancedListHandler:
    """高度リスト処理ハンドラー"""

    def __init__(self) -> None:
        self._setup_advanced_patterns()

    def _setup_advanced_patterns(self) -> None:
        """高度リスト解析パターンの設定"""
        self.patterns = {
            # アルファベットリスト: a. item, b. item
            "alpha": re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$"),
            # ローマ数字リスト: i. item, ii. item
            "roman": re.compile(
                r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x)\.\s+(.+)$", re.IGNORECASE
            ),
            # ネストレベル検出用
            "indent": re.compile(r"^(\s*)"),
            # ブロック形式: # リスト # content ##
            "block": re.compile(r"^#\s*リスト\s*#\s*(.*)##"),
        }

    def handle_alpha_list(self, line: str) -> Node:
        """アルファベットリストの処理"""
        match = self.patterns["alpha"].match(line)
        if match:
            indent = match.group(1)
            letter = match.group(2)
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {
                    "type": "alpha",
                    "letter": letter.lower(),
                    "indent": len(indent),
                }
            )
            return node

        return create_node("list_item", content=line.strip())

    def handle_roman_list(self, line: str) -> Node:
        """ローマ数字リストの処理"""
        match = self.patterns["roman"].match(line)
        if match:
            indent = match.group(1)
            roman = match.group(2)
            content = match.group(3)

            node = create_node("list_item", content=content)
            node.metadata.update(
                {
                    "type": "roman",
                    "roman": roman.lower(),
                    "indent": len(indent),
                }
            )
            return node

        return create_node("list_item", content=line.strip())

    def parse_nested_structure(self, lines: List[str]) -> List[Node]:
        """ネスト構造の解析"""
        result = []
        stack: List[Tuple[Node, int]] = []

        for line in lines:
            if not line.strip():
                continue

            # インデントレベルの取得
            indent_match = self.patterns["indent"].match(line)
            current_level = len(indent_match.group(1)) if indent_match else 0

            # リスト項目の作成（基本的な処理）
            item = create_node("list_item", content=line.strip())
            item.metadata["indent_level"] = current_level

            # スタックから現在のレベル以上の項目を削除
            while stack and stack[-1][1] >= current_level:
                stack.pop()

            # 親子関係の設定
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

    def parse_block_format(self, text: str) -> Optional[List[Node]]:
        """ブロック形式リストの解析"""
        match = self.patterns["block"].match(text)
        if not match:
            return None

        content = match.group(1).strip()
        if not content:
            return []

        # ブロック内容を行に分割
        lines = content.split("\n")
        items = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # ネストレベルの判定（スペース1個で1レベル）
                indent_level = 0
                while line.startswith(" "):
                    indent_level += 1
                    line = line[1:]

                item = create_node("list_item", content=line)
                item.metadata["indent_level"] = indent_level
                item.metadata["block_format"] = True
                items.append(item)

        return items

    def parse_character_delimited(self, text: str) -> List[Node]:
        """文字単位解析（[,] 区切り）"""
        # [,] 区切りのリスト解析
        if not text.startswith("[") or not text.endswith("]"):
            return []

        content = text[1:-1]  # [ ] を除去
        items = [item.strip() for item in content.split(",") if item.strip()]

        result = []
        for i, item in enumerate(items):
            node = create_node("list_item", content=item)
            node.metadata.update(
                {
                    "type": "character_delimited",
                    "index": i,
                    "delimiter": ",",
                }
            )
            result.append(node)

        return result

    def detect_advanced_list_type(self, line: str) -> Optional[str]:
        """高度リストタイプの検出"""
        if self.patterns["alpha"].match(line):
            return "alpha"
        elif self.patterns["roman"].match(line):
            return "roman"
        elif self.patterns["block"].match(line):
            return "block"
        return None

    def has_nested_items(self, items: List[Node]) -> bool:
        """ネストした項目があるかチェック"""
        for item in items:
            if item.metadata.get("indent_level", 0) > 0:
                return True
        return False

    def get_handlers(self) -> Dict[str, Any]:
        """高度ハンドラー辞書を返す"""
        return {
            "alpha": self.handle_alpha_list,
            "roman": self.handle_roman_list,
        }
