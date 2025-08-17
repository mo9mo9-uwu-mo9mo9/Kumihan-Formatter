"""パーサープロトコル定義

Issue #912: Parser系統合リファクタリング
全パーサーが実装すべきインターフェースを定義
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple, Union

from ...ast_nodes import Node


class ParserProtocol(Protocol):
    """基本パーサープロトコル

    全てのパーサーが実装すべき基本的なインターフェース
    """

    def parse(self, text: str) -> List[Node]:
        """テキストをパースしてノードリストを返す

        Args:
            text: パース対象のテキスト

        Returns:
            パース結果のノードリスト
        """
        ...

    def validate(self, text: str) -> bool:
        """テキストの妥当性を検証

        Args:
            text: 検証対象のテキスト

        Returns:
            妥当性判定結果
        """
        ...


class BlockParserProtocol(ParserProtocol):
    """ブロックパーサープロトコル

    ブロック要素の解析に特化したインターフェース
    """

    def parse_block(self, block: str) -> Node:
        """単一ブロックをパース

        Args:
            block: パース対象のブロック

        Returns:
            パース結果のノード
        """
        ...

    def extract_blocks(self, text: str) -> List[str]:
        """テキストからブロックを抽出

        Args:
            text: 抽出対象のテキスト

        Returns:
            抽出されたブロックのリスト
        """
        ...


class KeywordParserProtocol(ParserProtocol):
    """キーワードパーサープロトコル

    Kumihanキーワードの解析に特化したインターフェース
    """

    def parse_keywords(self, content: str) -> List[str]:
        """コンテンツからキーワードを抽出

        Args:
            content: キーワード抽出対象のコンテンツ

        Returns:
            抽出されたキーワードのリスト
        """
        ...

    def parse_marker_keywords(
        self, marker_content: str
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析

        Args:
            marker_content: マーカーコンテンツ

        Returns:
            (キーワードリスト, 属性辞書, エラーリスト)
        """
        ...

    def validate_keyword(self, keyword: str) -> bool:
        """キーワードの妥当性を検証

        Args:
            keyword: 検証対象のキーワード

        Returns:
            妥当性判定結果
        """
        ...


class ListParserProtocol(ParserProtocol):
    """リストパーサープロトコル

    リスト要素の解析に特化したインターフェース
    """

    def parse_list_items(self, content: str) -> List[Node]:
        """リストアイテムをパース

        Args:
            content: リストコンテンツ

        Returns:
            パースされたリストアイテムのノードリスト
        """
        ...

    def parse_nested_list(self, content: str, level: int = 0) -> List[Node]:
        """ネストリストをパース

        Args:
            content: ネストリストコンテンツ
            level: ネストレベル

        Returns:
            パースされたネストリストのノードリスト
        """
        ...

    def detect_list_type(self, line: str) -> Optional[str]:
        """リストタイプを検出

        Args:
            line: 検査対象の行

        Returns:
            検出されたリストタイプ (ordered/unordered/None)
        """
        ...


class MarkdownParserProtocol(ParserProtocol):
    """Markdownパーサープロトコル

    Markdown要素の解析に特化したインターフェース
    """

    def parse_markdown_elements(self, text: str) -> List[Node]:
        """Markdown要素をパース

        Args:
            text: Markdownテキスト

        Returns:
            パースされたMarkdown要素のノードリスト
        """
        ...

    def convert_to_kumihan(self, markdown_text: str) -> str:
        """MarkdownをKumihan記法に変換

        Args:
            markdown_text: 変換対象のMarkdownテキスト

        Returns:
            変換されたKumihan記法テキスト
        """
        ...


class StreamingParserProtocol(Protocol):
    """ストリーミングパーサープロトコル

    ストリーミング処理に特化したインターフェース
    """

    def parse_streaming(self, stream: Iterator[str]) -> Iterator[Node]:
        """ストリーミングパース

        Args:
            stream: 入力ストリーム

        Yields:
            パース結果のノード
        """
        ...

    def process_chunk(self, chunk: str, context: Any = None) -> List[Node]:
        """チャンクを処理

        Args:
            chunk: 処理対象のチャンク
            context: 処理コンテキスト

        Returns:
            処理結果のノードリスト
        """
        ...


class CompositeParserProtocol(Protocol):
    """複合パーサープロトコル

    複数のパーサーを組み合わせるためのインターフェース
    """

    def add_parser(self, parser: ParserProtocol, priority: int = 0) -> None:
        """パーサーを追加

        Args:
            parser: 追加するパーサー
            priority: 優先度
        """
        ...

    def remove_parser(self, parser: ParserProtocol) -> bool:
        """パーサーを削除

        Args:
            parser: 削除するパーサー

        Returns:
            削除成功の可否
        """
        ...

    def get_parsers(self) -> List[ParserProtocol]:
        """登録されたパーサーリストを取得

        Returns:
            パーサーリスト
        """
        ...


# 型エイリアス
AnyParser = Union[
    ParserProtocol,
    BlockParserProtocol,
    KeywordParserProtocol,
    ListParserProtocol,
    MarkdownParserProtocol,
    StreamingParserProtocol,
    CompositeParserProtocol,
]

ParserResult = Union[Node, List[Node], Iterator[Node]]
