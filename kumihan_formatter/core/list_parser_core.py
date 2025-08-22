"""
リスト パーサー コア

基本的なリスト解析機能（順序付き・順序なしリスト）
Issue #492 Phase 5A - list_parser.py分割

⚠️  DEPRECATION NOTICE - Issue #880 Phase 2C:
このListParserCoreは非推奨です。新しい統一パーサーシステムをご利用ください:
from kumihan_formatter.core.parsing import UnifiedListParser, get_global_coordinator
"""

import logging
import warnings
from typing import Tuple

from .ast_nodes import Node, list_item, ordered_list, unordered_list
from .parsing.keyword.keyword_parser import KeywordParser


class ListParserCore:
    """
    新リスト記法パーサー（# リスト # ブロック形式）

    新記法仕様:
    # リスト #
    項目1
    項目2
    項目3
    ##

    出力形式: ・項目1、・項目2、・項目3
    """

    def __init__(self, keyword_parser: KeywordParser):
        warnings.warn(
            "ListParserCoreは非推奨です。"
            "kumihan_formatter.core.parsing.UnifiedListParserを使用してください。",
            DeprecationWarning,
            stacklevel=2,
        )
        self.keyword_parser = keyword_parser

    def parse_list_block(self, lines: list[str], start_index: int) -> Tuple[Node, int]:
        """
        新記法 # リスト # ブロックの解析（ネスト対応）

        仕様:
        - スペース1個でレベル1下げ（最大3レベル）
        - 半角・全角スペース両対応
        - タブ禁止

        Args:
            lines: 全行
            start_index: リストブロック開始インデックス

        Returns:
            tuple: (list_node, next_index)
        """
        items = self._parse_nested_items(lines, start_index + 1)
        list_node = unordered_list(items)
        end_index = self._find_block_end(lines, start_index + 1)
        return list_node, end_index

    def _parse_nested_items(self, lines: list[str], start_index: int) -> list[Node]:
        """ネスト構造を考慮したアイテム解析（修正版）"""
        items = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index]

            # ブロック終了マーカー検出
            if line.strip() == "##" or line.strip() == "＃＃":
                break

            # 空行をスキップ
            if not line.strip():
                current_index += 1
                continue

            # インデントレベルを計算
            indent_level = self._calculate_indent_level(line)

            # タブ文字チェック
            if indent_level == -1:
                # タブ文字が含まれているため、スキップ
                continue

            # 4レベル以上のネストは無視（警告）
            if indent_level > 3:
                logging.getLogger(__name__).warning(
                    f"ネストレベル{indent_level}は最大値3を超えています。無視されます: {line.strip()}"
                )
                current_index += 1
                continue

            # トップレベル項目のみここで処理
            if indent_level == 0:
                content = line.strip()
                processed_content = self.keyword_parser._process_inline_keywords(
                    content
                )
                item_node = list_item(processed_content)

                # 次の行から子項目をチェック
                child_items, consumed = self._parse_child_items(
                    lines, current_index + 1, 1
                )
                if child_items:
                    # 子項目がある場合はネストしたリストを追加
                    nested_list = unordered_list(child_items)
                    if item_node.children is not None:
                        item_node.children.append(nested_list)
                    current_index += consumed

                items.append(item_node)

            current_index += 1

        return items

    def is_list_line(self, line: str) -> str | None:
        """
        旧記法互換性のためのis_list_lineメソッド

        Args:
            line: チェックする行

        Returns:
            str | None: リストタイプ（'unordered', 'ordered'）または None
        """
        line = line.strip()
        if not line:
            return None

        # 順序なしリストのチェック
        if line.startswith(("- ", "• ", "* ", "+ ")):
            return "unordered"

        # 順序ありリストのチェック
        import re

        if re.match(r"^\d+\.\s", line):
            return "ordered"

        return None

    def parse_unordered_list(
        self, lines: list[str], start_index: int
    ) -> tuple[Node, int]:
        """
        旧記法互換性のための順序なしリストパーサー

        Args:
            lines: 全行
            start_index: リスト開始インデックス

        Returns:
            tuple: (list_node, next_index)
        """

        items = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index].strip()

            # 空行または非リスト行で終了
            if not line or not line.startswith(("- ", "• ", "* ", "+ ")):
                break

            # リスト項目を解析
            content = line[2:].strip()  # プレフィックスを除去
            processed_content = self.keyword_parser._process_inline_keywords(content)
            item_node = list_item(processed_content)
            items.append(item_node)

            current_index += 1

        list_node = unordered_list(items)
        return list_node, current_index

    def parse_ordered_list(
        self, lines: list[str], start_index: int
    ) -> tuple[Node, int]:
        """
        旧記法互換性のための順序ありリストパーサー

        Args:
            lines: 全行
            start_index: リスト開始インデックス

        Returns:
            tuple: (list_node, next_index)
        """

        import re

        items = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index].strip()

            # 空行または非順序リスト行で終了
            if not line or not re.match(r"^\d+\.\s", line):
                break

            # リスト項目を解析
            match = re.match(r"^\d+\.\s(.+)", line)
            if match:
                content = match.group(1)
                processed_content = self.keyword_parser._process_inline_keywords(
                    content
                )
                item_node = list_item(processed_content)
                items.append(item_node)

            current_index += 1

        list_node = ordered_list(items)
        return list_node, current_index

    def _parse_child_items(
        self, lines: list[str], start_index: int, target_level: int
    ) -> tuple[list[Node], int]:
        """指定レベルの子項目を解析"""
        child_items = []
        current_index = start_index
        consumed_lines = 0

        while current_index < len(lines):
            line = lines[current_index]

            # ブロック終了または空行
            if not line.strip() or line.strip() in ["##", "＃＃"]:
                break

            indent_level = self._calculate_indent_level(line)

            # タブ文字チェック
            if indent_level == -1:
                # タブ文字が含まれているため、スキップ
                continue

            if indent_level < target_level:
                # より上のレベルに戻った
                break
            elif indent_level == target_level:
                # 同じレベルの項目
                content = line.strip()
                processed_content = self.keyword_parser._process_inline_keywords(
                    content
                )
                item_node = list_item(processed_content)

                # さらに深い子項目をチェック
                if target_level < 3:  # 最大3レベル制限
                    grand_child_items, grand_consumed = self._parse_child_items(
                        lines, current_index + 1, target_level + 1
                    )
                    if grand_child_items:
                        nested_list = unordered_list(grand_child_items)
                        if item_node.children is None:
                            item_node.children = []
                        item_node.children.append(nested_list)
                        current_index += grand_consumed
                        consumed_lines += grand_consumed

                child_items.append(item_node)
                consumed_lines += 1
            elif indent_level > target_level:
                # より深いレベル（次の項目で処理される）
                current_index += 1
                consumed_lines += 1
                continue

            current_index += 1

        return child_items, consumed_lines

    def _calculate_indent_level(self, line: str) -> int:
        """インデントレベルを計算（スペース1個=レベル1）

        タブ文字は0を返す（タブは禁止）
        """
        # インデント処理実装（スペース・タブ混在対応）
        spaces = 0
        tabs = 0
        for char in line:
            if char == " ":
                spaces += 1
            elif char == "\t":
                tabs += 1
            else:
                break

        # タブ1つ = スペース4つとして正規化
        normalized_indent = spaces + (tabs * 4)
        return normalized_indent // 4

    def _find_block_end(self, lines: list[str], start_index: int) -> int:
        """ブロック終了位置を検索"""
        for i in range(start_index, len(lines)):
            if lines[i].strip() in ["##", "＃＃"]:
                return i + 1

        # 終了マーカーが見つからない場合は末尾を返す
        return len(lines)

    def is_list_block_start(self, line: str) -> bool:
        """
        行が新リスト記法の開始か判定

        Args:
            line: 判定対象の行

        Returns:
            bool: リストブロック開始の場合True
        """
        stripped = line.strip()
        # # リスト # または ＃リスト＃ パターン
        import re

        return bool(re.match(r"^[#＃]\s*リスト\s*[#＃]", stripped))

    def contains_list(self, content: str) -> bool:
        """
        コンテンツが新リスト記法を含むかチェック

        Args:
            content: チェック対象コンテンツ

        Returns:
            bool: 新リスト記法を含む場合True
        """
        lines = content.split("\n")
        for line in lines:
            if self.is_list_block_start(line):
                return True

        return False

    def extract_list_items(self, content: str) -> list[str]:
        """
        新記法からリスト項目を抽出

        Args:
            content: リストブロックを含むコンテンツ

        Returns:
            list[str]: 抽出された項目リスト
        """
        items = []
        lines = content.split("\n")
        in_list_block = False

        for line in lines:
            stripped = line.strip()

            if self.is_list_block_start(line):
                in_list_block = True
                continue

            if in_list_block:
                if stripped == "##" or stripped == "＃＃":
                    break
                elif stripped:  # 空行以外
                    items.append(stripped)

        return items
