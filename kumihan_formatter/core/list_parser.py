"""
リスト パーサー 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - list_parser.py分割

⚠️  DEPRECATION NOTICE - Issue #880 Phase 2C:
このListParserは非推奨です。新しい統一パーサーシステムをご利用ください:
from kumihan_formatter.core.parsing import UnifiedListParser, get_global_coordinator
"""

import warnings

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
class ListParser(ListParserCore):
    """後方互換性ラッパー"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ListParserは非推奨です。kumihan_formatter.core.parsing.UnifiedListParserを使用してください。",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


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
