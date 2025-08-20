"""順序付きリストパーサー

順序付きリスト・アルファベットリスト・ローマ数字リストの解析を担当
"""

import re
from typing import List

from ....ast_nodes import Node, create_node


class OrderedListParser:
    """順序付きリスト解析専用クラス

    担当機能:
    - 順序付きリスト (1., 2., 3.)
    - アルファベットリスト (a., b., c.)
    - ローマ数字リスト (i., ii., iii.)
    """

    def __init__(self) -> None:
        """初期化"""
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """順序付きリスト用パターンの設定"""
        self.patterns = {
            # 順序付きリスト: 1. item, 2. item
            "ordered": re.compile(r"^(\s*)(\d+)\.\s+(.+)$"),
            # アルファベットリスト: a. item, b. item
            "alpha": re.compile(r"^(\s*)([a-zA-Z])\.\s+(.+)$"),
            # ローマ数字リスト: i. item, ii. item
            "roman": re.compile(
                r"^(\s*)(i{1,3}|iv|v|vi{0,3}|ix|x)\.\s+(.+)$", re.IGNORECASE
            ),
        }

    def can_handle(self, line: str, list_type: str) -> bool:
        """指定された行とリストタイプを処理可能か判定"""
        return list_type in ["ordered", "alpha", "roman"] and bool(
            self.patterns[list_type].match(line)
        )

    def handle_ordered_list(self, line: str) -> Node:
        """順序付きリストの処理"""
        match = self.patterns["ordered"].match(line)
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

    def handle_alpha_list(self, line: str) -> Node:
        """アルファベットリストの処理"""
        match = self.patterns["alpha"].match(line)
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

    def handle_roman_list(self, line: str) -> Node:
        """ローマ数字リストの処理"""
        match = self.patterns["roman"].match(line)
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

    def extract_item_content(self, line: str, list_type: str) -> str:
        """順序付きリストアイテムからコンテンツを抽出"""
        pattern = self.patterns.get(list_type)
        if pattern:
            match = pattern.match(line)
            if match:
                if list_type == "ordered":
                    return match.group(3)
                elif list_type in ["alpha", "roman"]:
                    return match.group(3)

        return line.strip()

    def validate_ordered_sequence(self, items: List[Node]) -> List[str]:
        """順序付きリストの連番チェック"""
        errors = []
        expected_numbers = {}

        for i, item in enumerate(items):
            if item.metadata.get("type") == "ordered":
                number = item.metadata.get("number", 0)
                list_level = item.metadata.get("indent", 0)

                if list_level not in expected_numbers:
                    expected_numbers[list_level] = 1

                if number != expected_numbers[list_level]:
                    errors.append(
                        f"項目{i+1}: 期待される番号{expected_numbers[list_level]}、実際は{number}"
                    )

                expected_numbers[list_level] += 1

        return errors

    def get_supported_types(self) -> List[str]:
        """サポートするリストタイプを取得"""
        return list(self.patterns.keys())
