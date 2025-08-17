"""
リスト パーサー ファクトリー

リストパーサー関連コンポーネントの作成・初期化
Issue #492 Phase 5A - list_parser.py分割
"""

from typing import Optional

from .list_parser_core import ListParserCore
from .list_validator import ListValidator
from .nested_list_parser import NestedListParser
from .parsing.keyword.keyword_parser import KeywordParser


def create_list_parser(keyword_parser: KeywordParser) -> ListParserCore:
    """リストパーサーコア作成"""
    return ListParserCore(keyword_parser)


def create_nested_list_parser(keyword_parser: KeywordParser) -> NestedListParser:
    """ネストリストパーサー作成"""
    list_parser = create_list_parser(keyword_parser)
    return NestedListParser(list_parser)


def create_list_validator(keyword_parser: KeywordParser) -> ListValidator:
    """リストバリデーター作成"""
    list_parser = create_list_parser(keyword_parser)
    return ListValidator(list_parser)


class ListParserComponents:
    """リストパーサー関連コンポーネントの統合管理"""

    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser
        self._list_parser: Optional[ListParserCore] = None
        self._nested_parser: Optional[NestedListParser] = None
        self._validator: Optional[ListValidator] = None

    @property
    def list_parser(self) -> ListParserCore:
        """リストパーサーコア取得（遅延初期化）"""
        if self._list_parser is None:
            self._list_parser = create_list_parser(self.keyword_parser)
        return self._list_parser

    @property
    def nested_parser(self) -> NestedListParser:
        """ネストリストパーサー取得（遅延初期化）"""
        if self._nested_parser is None:
            self._nested_parser = NestedListParser(self.list_parser)
        return self._nested_parser

    @property
    def validator(self) -> ListValidator:
        """リストバリデーター取得（遅延初期化）"""
        if self._validator is None:
            self._validator = ListValidator(self.list_parser)
        return self._validator
