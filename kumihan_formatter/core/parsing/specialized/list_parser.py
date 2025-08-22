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

from typing import Any, Dict, List, Optional, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    ParseContext,
    ParseResult,
)
from ..protocols import ParserType
from .list_components import AdvancedListHandler, BasicListHandler, ListUtilities


class UnifiedListParser(UnifiedParserBase, CompositeMixin):
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
        text = self._normalize_content(content)

        try:
            lines = text.strip().split("\n")
            if not lines or not any(line.strip() for line in lines):
                return create_node("list", content=[])

            # 特別な形式の検出と処理
            special_result = self._try_parse_special_formats(text)
            if special_result:
                return special_result

            # 通常のリスト解析
            list_items = self._parse_regular_list_items(lines)

            if list_items:
                return self._finalize_list_parsing(list_items)

            return create_node("list", content=[])

        except Exception as e:
            self.logger.error(f"List parsing failed: {e}")
            return create_node("error", content=f"List parsing failed: {e}")

    def _normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化して文字列として返す"""
        if isinstance(content, list):
            return "\n".join(str(line) for line in content)
        return str(content)

    def _try_parse_special_formats(self, text: str) -> Optional[Node]:
        """特別な形式の解析を試行"""
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

        return None

    def _parse_regular_list_items(self, lines: List[str]) -> List[Node]:
        """通常のリスト項目を解析"""
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
                current_indent_level = self._get_indent_level(line)

            # リスト項目の解析
            item_node = self._parse_list_item(line, list_type)
            if item_node:
                list_items.append(item_node)

        return list_items

    def _get_indent_level(self, line: str) -> int:
        """行のインデントレベルを取得"""
        import re

        indent_match = re.match(r"^(\s*)", line)
        return len(indent_match.group(1)) if indent_match else 0

    def _finalize_list_parsing(self, list_items: List[Node]) -> Node:
        """リスト解析の最終処理"""
        # ネスト構造の解析
        if self.utilities.has_nested_items(list_items):
            nested_items = self.advanced_handler.parse_nested_structure(
                [item.content for item in list_items]
            )
            list_items = nested_items

        # リストタイプの決定
        primary_type = self.utilities.determine_primary_list_type(list_items)
        return self.utilities.create_list_node(list_items, primary_type)

    def parse(
        self,
        content: Union[str, List[str]],
        **kwargs: Any,
    ) -> Node:
        """統一パースメソッド - UnifiedParserBase互換"""
        if isinstance(content, list):
            # UnifiedParserBase互換: List[str] -> Node
            combined_content = "\n".join(content)
            return self.parse_list_from_text(combined_content)
        else:
            # str -> Node
            try:
                self._clear_errors_warnings()

                # 既存のparse_list_from_textメソッドを活用
                node = self.parse_list_from_text(content)
                return node if node else create_node("empty", "")
            except Exception as e:
                # エラー時は空のNodeを返す
                return create_node("error", f"List parsing failed: {e}")

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return getattr(self, "_errors", [])

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return getattr(self, "_warnings", [])

    def detect_list_type(self, content: str) -> str:
        """リストタイプ検出（抽象メソッド実装）"""
        lines = content.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "+ ")):
                return "unordered"
            elif stripped and stripped[0].isdigit() and ". " in stripped:
                return "ordered"
        return "unordered"

    def get_list_nesting_level(self, line: str) -> int:
        """リストネストレベル取得（抽象メソッド実装）"""
        return len(line) - len(line.lstrip())

    def parse_list_items(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """リストアイテム解析（抽象メソッド実装）"""
        try:
            node = self.parse_list_from_text(content)
            return [node] if node else []
        except Exception:
            return []

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """ネストリスト解析（抽象メソッド実装）"""
        try:
            node = self.parse_list_from_text(content)
            return [node] if node else []
        except Exception:
            return []

    def supports_format(self, content: str) -> bool:
        """フォーマットサポート確認（抽象メソッド実装）"""
        lines = content.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "+ ")) or (
                stripped and stripped[0].isdigit() and ". " in stripped
            ):
                return True
        return False

    # ParseResultを返すプロトコル用のエイリアスメソッド
    def parse_with_result(
        self, text: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """ParseResultを返す解析インターフェース（プロトコル準拠）"""
        try:
            # 新しいparseメソッドを使用してNodeを取得
            node = self.parse(text, context=context)
            return ParseResult(
                success=True,
                nodes=[node],
                errors=[],
                warnings=[],
                metadata={"parser_type": "list"},
            )
        except Exception as e:
            return ParseResult(
                success=False,
                nodes=[],
                errors=[f"List parsing failed: {e}"],
                warnings=[],
                metadata={"parser_type": "list"},
            )

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
            result = self.parse_with_result(text)
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

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedListParser",
            "version": "2.1.0",
            "supported_formats": self.get_supported_formats(),
            "capabilities": [
                "ordered_lists",
                "unordered_lists",
                "definition_lists",
                "checklist",
                "alpha_lists",
                "roman_lists",
                "block_format",
                "character_delimited",
                "nested_structure",
                "type_conversion",
            ],
            "parser_type": self.parser_type,
            "architecture": "分割統合型",
        }
