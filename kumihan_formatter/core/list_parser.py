"""
リスト パーサー 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - list_parser.py分割
"""

# 分割されたモジュールからインポート
from .list_parser_core import ListParserCore
from .list_parser_factory import (
    ListParserComponents,
    create_list_parser,
    create_list_validator,
    create_nested_list_parser,
)
from .list_validator import ListValidator
from .nested_list_parser import NestedListParser

# 後方互換性のためのエイリアス
ListParser = ListParserCore

# モジュールレベルのエクスポート
__all__ = [
    "ListParser",
    "ListParserCore",
    "NestedListParser",
    "ListValidator",
    "create_list_parser",
    "create_nested_list_parser",
    "create_list_validator",
    "ListParserComponents",
]
