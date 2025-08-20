"""統合リストパーサー - メインエントリーポイント（既存API互換性維持）"""

from typing import Any, Dict, List, Optional, Tuple

# 統一プロトコルインポート（重複定義を避けるため、純粋にtry-except分岐）
try:
    from ..base.parser_protocols import (
        BaseParserProtocol as BaseProtocol,
    )
    from ..base.parser_protocols import (
        ListParserProtocol as ListProtocol,
    )
    from ..base.parser_protocols import (
        ParseContext,
        ParseError,
        ParseResult,
    )
except ImportError:
    # フォールバック: 型安全性のため
    from dataclasses import dataclass
    from typing import Protocol

    class BaseProtocol(Protocol):  # type: ignore[no-redef]
        def parse(self, content: str, context: Any = None) -> Any: ...
        def validate(self, content: str, context: Any = None) -> List[str]: ...
        def get_parser_info(self) -> Dict[str, Any]: ...
        def supports_format(self, format_hint: str) -> bool: ...

    class ListProtocol(Protocol):  # type: ignore[no-redef]
        def parse_list_items(self, content: str, context: Any = None) -> List[Any]: ...

        def parse_nested_list(
            self, content: str, level: int = 0, context: Any = None
        ) -> List[Any]: ...
        def detect_list_type(self, line: str) -> Optional[str]: ...
        def get_list_nesting_level(self, line: str) -> int: ...

    @dataclass
    class ParseResult:  # type: ignore[no-redef]
        success: bool
        nodes: List[Any]
        errors: List[str]
        warnings: List[str]
        metadata: Dict[str, Any]

    @dataclass
    class ParseContext:  # type: ignore[no-redef]
        source_file: Optional[str] = None
        line_number: int = 1
        column_number: int = 1
        parser_state: Optional[Dict[str, Any]] = None
        config: Optional[Dict[str, Any]] = None

    class ParseError(Exception):  # type: ignore[no-redef]
        pass


# ノードインポート
try:
    from ....ast_nodes.node import Node  # type: ignore[import-not-found]
except ImportError:
    try:
        from ....ast_nodes import Node  # type: ignore[import-not-found]
    except ImportError:
        # フォールバック実装
        class Node:  # type: ignore[no-redef]
            def __init__(
                self,
                type: str,
                content: Any,
                attributes: Optional[Dict[str, Any]] = None,
            ):
                self.type = type
                self.content = content
                self.attributes = attributes or {}


from .parsers.nested_list_parser import NestedListParser

# 専用パーサーのインポート
from .parsers.ordered_list_parser import OrderedListParser
from .parsers.unordered_list_parser import UnorderedListParser
from .utilities.list_utilities import ListUtilities


class ListParser:
    """
    ListParser クラスは、リスト形式の文字列を解析し、
    ネストされたリスト構造を構築するためのクラスです。（統合版）
    """

    def __init__(self) -> None:
        """
        ListParser の新しいインスタンスを初期化します。
        """
        self.stack: List[List[Any]] = [[]]
        self.current_string: str = ""

        # 専用パーサーの初期化
        self.ordered_parser = OrderedListParser()
        self.unordered_parser = UnorderedListParser()
        self.nested_parser = NestedListParser()
        self.utilities = ListUtilities()

    def parse_char(self, char: str) -> None:
        """
        入力文字列の次の文字を解析します。

        Args:
            char (str): 解析する文字。
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
        """
        新しいリストを開始します。
        """
        self.add_string()
        new_list: List[Any] = []
        self.stack[-1].append(new_list)
        self.stack.append(new_list)

    def end_list(self) -> None:
        """
        現在のリストを終了します。
        """
        self.add_string()
        if len(self.stack) > 1:
            self.stack.pop()
        else:
            raise ValueError("Unmatched closing bracket ]")

    def add_string(self) -> None:
        """
        現在の文字列を現在のリストに追加します。
        """
        if self.current_string:
            self.stack[-1].append(self.current_string.strip())
            self.current_string = ""

    def get_result(self) -> List[Any]:
        """
        解析結果のリストを返します。

        Returns:
            List[Any]: 解析結果のリスト。
        """
        if len(self.stack) > 1:
            raise ValueError("Unclosed list")
        return self.stack[0]

    def parse_string(self, input_string: str) -> List[Any]:
        """
        入力文字列全体を解析します（既存API互換用）。

        Args:
            input_string (str): 解析する文字列。

        Returns:
            List[Any]: 解析結果のリスト。
        """
        for char in input_string:
            self.parse_char(char)
        return self.get_result()

    # === 統一プロトコル実装: BaseParserProtocol ===

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース - 既存parse_string()をラップ

        Args:
            content: パース対象のコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            ParseResult: 統一パース結果
        """
        try:
            # 直接パース実行（無限ループ回避のため）
            parsed_data = parse_list_string(content)

            # ノード作成
            nodes = self.utilities.create_nodes_from_parsed_data(parsed_data)

            # ParseResult作成 - フォールバック実装対応
            if hasattr(ParseResult, "__dataclass_fields__"):
                return ParseResult(
                    success=True,
                    nodes=nodes,
                    errors=[],
                    warnings=[],
                    metadata={
                        "parser": "ListParser",
                        "list_depth": self.utilities.calculate_list_depth(parsed_data),
                        "total_items": self.utilities.count_total_items(parsed_data),
                    },
                )
            else:
                # フォールバック: 辞書で返却
                return {  # type: ignore
                    "success": True,
                    "nodes": nodes,
                    "errors": [],
                    "warnings": [],
                    "metadata": {
                        "parser": "ListParser",
                        "list_depth": self.utilities.calculate_list_depth(parsed_data),
                        "total_items": self.utilities.count_total_items(parsed_data),
                    },
                }
        except Exception as e:
            if hasattr(ParseResult, "__dataclass_fields__"):
                return ParseResult(
                    success=False,
                    nodes=[],
                    errors=[f"List parsing failed: {str(e)}"],
                    warnings=[],
                    metadata={"parser": "ListParser"},
                )
            else:
                return {  # type: ignore
                    "success": False,
                    "nodes": [],
                    "errors": [f"List parsing failed: {str(e)}"],
                    "warnings": [],
                    "metadata": {"parser": "ListParser"},
                }

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション - ブラケット整合性・構文チェック

        Args:
            content: 検証対象のコンテンツ
            context: 検証コンテキスト（オプション）

        Returns:
            List[str]: エラーメッセージリスト（空リストは成功）
        """
        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            return errors

        if not content.strip():
            errors.append("Empty content provided")
            return errors

        # ブラケット整合性チェック
        open_count = content.count("[")
        close_count = content.count("]")

        if open_count != close_count:
            errors.append(f"Mismatched brackets: {open_count} '[' vs {close_count} ']'")

        # 実際のパース試行で構文エラー検出
        try:
            parse_list_string(content)
        except Exception as e:
            errors.append(f"Parse validation failed: {str(e)}")

        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得

        Returns:
            Dict[str, Any]: パーサーメタデータ
        """
        return {
            "name": "ListParser",
            "version": "2.0",
            "supported_formats": ["list", "array", "nested_list", "bracket"],
            "capabilities": [
                "list_parsing",
                "nested_parsing",
                "bracket_parsing",
                "validation",
                "depth_calculation",
            ],
            "description": "Nested list structure parser with bracket notation",
            "author": "Kumihan-Formatter Project",
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定

        Args:
            format_hint: フォーマットヒント文字列

        Returns:
            bool: 対応可能かどうか
        """
        supported = {"list", "array", "nested_list", "bracket"}
        return format_hint.lower() in supported

    # === 統一プロトコル実装: ListParserProtocol ===

    def parse_list_items(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """リストアイテムをパース - Nodeリスト返却

        Args:
            content: リストコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたリストアイテムのノードリスト
        """
        try:
            parsed_data = parse_list_string(content)
            return self.utilities.create_nodes_from_parsed_data(
                parsed_data, create_items=True
            )
        except Exception:
            # エラー時は空リスト返却
            return []

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """ネストリストをパース - レベル指定対応

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル
            context: パースコンテキスト（オプション）

        Returns:
            List[Node]: パースされたネストリストのノードリスト
        """
        return self.nested_parser.parse_nested_list(content, level, context)

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプ検出（bracket, json, etc.）

        Args:
            line: 検査対象の行

        Returns:
            Optional[str]: 検出されたリストタイプ (bracket/json/None)
        """
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            return "bracket"
        if line.startswith("{") and line.endswith("}"):
            return "json"
        return None

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得（ブラケット深度計算）

        Args:
            line: 検査対象の行

        Returns:
            int: ネストレベル（0=ルートレベル）
        """
        return self.nested_parser.get_list_nesting_level(line)


class ListParserProtocol(ListParser):
    """統一プロトコル対応ListParser"""

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース - 親クラスの実装を使用"""
        return super().parse(content, context)

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション - 親クラスの実装を使用"""
        return super().validate(content, context)

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得 - 親クラスの実装を使用"""
        return super().get_parser_info()

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定 - 親クラスの実装を使用"""
        return super().supports_format(format_hint)

    def parse_list_items(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """リストアイテムをパース - 親クラスの実装を使用"""
        return super().parse_list_items(content, context)

    def parse_nested_list(
        self, content: str, level: int = 0, context: Optional[ParseContext] = None
    ) -> List[Node]:
        """ネストリストをパース - 親クラスの実装を使用"""
        return super().parse_nested_list(content, level, context)

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプ検出 - 親クラスの実装を使用"""
        return super().detect_list_type(line)

    def get_list_nesting_level(self, line: str) -> int:
        """リストのネストレベルを取得 - 親クラスの実装を使用"""
        return super().get_list_nesting_level(line)


def parse_list_string(input_string: str) -> List[Any]:
    """
    リスト形式の文字列を解析して、ネストされたリスト構造を返します。

    Args:
        input_string (str): 解析するリスト形式の文字列。

    Returns:
        List[Any]: 解析結果のリスト。
    """
    parser = ListParser()
    return parser.parse_string(input_string)


def find_outermost_list(input_string: str) -> Tuple[int, int]:
    """
    文字列中の最も外側のリストの開始インデックスと終了インデックスを検索します。

    Args:
        input_string (str): 検索する文字列。

    Returns:
        Tuple[int, int]: 最も外側のリストの開始インデックスと終了インデックス。
                         リストが見つからない場合は (-1, -1) を返します。
    """
    start_index = -1
    end_index = -1
    bracket_count = 0

    for i, char in enumerate(input_string):
        if char == "[":
            if bracket_count == 0:
                start_index = i
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0:
                end_index = i
                break

    return start_index, end_index
