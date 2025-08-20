"""統一リストパーサー - Issue #920 分割最適化版

Issue #912: Parser系統合リファクタリング
Issue #920: 大型ファイル分割リファクタリング

分割されたコンポーネント:
- BasicListHandler: 基本リスト処理
- AdvancedListHandler: 高度リスト処理
- ListUtilities: 共通ユーティリティ

統合機能:
- 順序付き・順序なしリスト解析
- ネストリスト構造（最大3レベル）
- 定義リスト・チェックリスト
- # リスト # ブロック形式
- 文字単位解析（スタック）
- ファクトリーパターン
- 後方互換性維持
"""

from typing import Any, Dict, List, Optional, Union, cast

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    ListParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType
from .list_components import AdvancedListHandler, BasicListHandler, ListUtilities


class UnifiedListParser(UnifiedParserBase, CompositeMixin, ListParserProtocol):
    """統一リストパーサー - Issue #920 分割最適化版

    分割されたコンポーネントを統合し、既存API完全互換性を維持:
    - BasicListHandler: 基本リスト解析
    - AdvancedListHandler: 高度リスト解析
    - ListUtilities: 共通ユーティリティ

    機能:
    - 順序なし/順序付きリスト
    - 定義リスト・チェックリスト
    - アルファベット・ローマ数字リスト
    - ネスト構造（最大3レベル）
    - # リスト # ブロック形式
    - 文字区切り解析
    - ファクトリーパターン
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.LIST)

        # 分割されたコンポーネントを初期化
        self.basic_handler = BasicListHandler()
        self.advanced_handler = AdvancedListHandler()
        self.utilities = ListUtilities()

        # 統合ハンドラー辞書を作成
        self._setup_combined_handlers()

    def _setup_combined_handlers(self) -> None:
        """分割されたハンドラーを統合"""
        # 基本ハンドラーと高度ハンドラーを統合
        self.list_handlers = {}
        self.list_handlers.update(self.basic_handler.get_handlers())
        self.list_handlers.update(self.advanced_handler.get_handlers())

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """基底クラス用の解析実装（UnifiedParserBase準拠）"""
        # List[str]が渡された場合は結合する
        if isinstance(content, list):
            text = "\n".join(str(line) for line in content)
        else:
            text = str(content)

        try:
            lines = text.strip().split("\n")
            if not lines or not any(line.strip() for line in lines):
                return create_node("list", content=[])

            # ブロック形式の検出
            if text.strip().startswith("# リスト #"):
                block_items = self.advanced_handler.parse_block_format(text)
                if block_items:
                    return self.utilities.create_list_node(block_items, "block")

            # 文字区切り形式の検出
            if text.strip().startswith("[") and text.strip().endswith("]"):
                char_items = self.advanced_handler.parse_character_delimited(text)
                if char_items:
                    return self.utilities.create_list_node(
                        char_items, "character_delimited"
                    )

            # 通常のリスト解析
            list_items = []
            current_indent_level = None

            for line in lines:
                if not line.strip():
                    continue

                # リストタイプの検出
                list_type = self._detect_list_type(line)
                if not list_type:
                    continue

                # 最初の項目のインデントレベルを設定
                if current_indent_level is None:
                    import re

                    indent_match = re.match(r"^(\s*)", line)
                    current_indent_level = (
                        len(indent_match.group(1)) if indent_match else 0
                    )

                # リスト項目の解析
                item_node = self._parse_list_item(line, list_type)
                if item_node:
                    list_items.append(item_node)

            if list_items:
                # ネスト構造の解析
                if self.utilities.has_nested_items(list_items):
                    nested_items = self.advanced_handler.parse_nested_structure(
                        [item.content for item in list_items]
                    )
                    list_items = nested_items

                # リストタイプの決定
                primary_type = self.utilities.determine_primary_list_type(list_items)
                return self.utilities.create_list_node(list_items, primary_type)

            return create_node("list", content=[])

        except Exception as e:
            self.logger.error(f"List parsing failed: {e}")
            return create_node("error", content=f"List parsing failed: {e}")

    # ParseResultを返すプロトコル用のエイリアスメソッド
    def parse_with_result(
        self, text: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """ParseResultを返す解析インターフェース（プロトコル準拠）"""
        try:
            # 基底クラスのparseメソッドを使用
            result = super().parse(text)
            return create_parse_result(nodes=[result], success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"List parsing failed: {e}")
            return result

    def _detect_list_type(self, line: str) -> Optional[str]:
        """行からリストタイプを検出"""
        # 基本リストタイプの検出
        basic_type = self.basic_handler.detect_list_type(line)
        if basic_type:
            return basic_type

        # 高度リストタイプの検出
        advanced_type = self.advanced_handler.detect_advanced_list_type(line)
        if advanced_type:
            return advanced_type

        return None

    def _parse_list_item(self, line: str, list_type: str) -> Optional[Node]:
        """個別のリスト項目を解析"""
        handler = self.list_handlers.get(list_type)
        if handler:
            return cast(Optional[Node], handler(line))

        # デフォルトハンドラー
        return create_node("list_item", content=line.strip())

    # 外部API メソッド（既存API互換性維持）

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

            return self.utilities.create_list_node(items, list_type)
        else:
            # 自動判定での解析
            result = self.parse(text)
            if result.success and result.nodes:
                return result.nodes[0]
            return create_node("list", content="")

    def convert_list_type(self, list_node: Node, target_type: str) -> Node:
        """リストタイプの変換"""
        return self.utilities.convert_list_type(list_node, target_type)

    def extract_checklist_status(self, list_node: Node) -> Dict[str, Any]:
        """チェックリストの完了状況を抽出"""
        return self.utilities.extract_checklist_status(list_node)

    def validate_list_structure(self, list_node: Node) -> List[str]:
        """リスト構造の妥当性をチェック"""
        return self.utilities.validate_list_structure(list_node)

    def get_list_statistics(self, list_node: Node) -> Dict[str, Any]:
        """リストの統計情報を取得"""
        return self.utilities.get_list_statistics(list_node)

    # プロトコル準拠メソッド

    def validate(self, text: str, context: Optional[ParseContext] = None) -> List[str]:
        """入力テキストの妥当性を検証"""
        errors = []
        try:
            if not text or not text.strip():
                errors.append("Empty input text")
                return errors

            # 基本的な構文チェック
            lines = text.strip().split("\n")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    list_type = self._detect_list_type(line)
                    if not list_type:
                        # リストの項目でない行があるかチェック
                        if not any(
                            marker in line for marker in ["-", "*", "+", ".", "::"]
                        ):
                            continue  # 通常のテキスト行として許可
                        errors.append(f"Line {i}: Unrecognized list format")

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def get_supported_formats(self) -> List[str]:
        """サポートされているリスト形式を返す"""
        return [
            "unordered",
            "ordered",
            "definition",
            "checklist",
            "alpha",
            "roman",
            "block",
            "character_delimited",
        ]
