"""後方互換性レイヤー

Issue #914 Phase 2: 既存コードが動作し続けるための互換レイヤー
"""

from typing import Any

from .parsing.main_parser import MainParser
from .parsing.specialized.block_parser import UnifiedBlockParser as BlockParser
from .parsing.specialized.keyword_parser import UnifiedKeywordParser as KeywordParser
from .parsing.specialized.list_parser import UnifiedListParser as ListParser
from .rendering.formatters.html_formatter import HtmlFormatter
from .rendering.formatters.markdown_formatter import MarkdownFormatter
from .rendering.main_renderer import MainRenderer as HTMLRenderer


# 旧ファクトリー関数の互換版
def create_keyword_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式キーワードパーサー作成"""
    from .patterns.factories import create_parser

    return create_parser("keyword", **kwargs)


def create_list_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式リストパーサー作成"""
    from .patterns.factories import create_parser

    return create_parser("list", **kwargs)


def create_block_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式ブロックパーサー作成"""
    from .patterns.factories import create_parser

    return create_parser("block", **kwargs)


def create_markdown_parser(**kwargs: Any) -> Any:
    """後方互換: 旧式Markdownパーサー作成"""
    from .patterns.factories import create_parser

    return create_parser("markdown", **kwargs)


def create_html_renderer(**kwargs: Any) -> HtmlFormatter:
    """後方互換: 旧式HTMLレンダラー作成"""
    return HtmlFormatter(**kwargs)


def create_markdown_renderer(**kwargs: Any) -> MarkdownFormatter:
    """後方互換: 旧式Markdownレンダラー作成"""
    return MarkdownFormatter(**kwargs)


# 旧インポートパス互換性のための__all__設定
__all__ = [
    "KeywordParser",
    "ListParser",
    "BlockParser",
    "MainParser",
    "HTMLRenderer",
    "HtmlFormatter",
    "MarkdownFormatter",
    "create_keyword_parser",
    "create_list_parser",
    "create_block_parser",
    "create_markdown_parser",
    "create_html_renderer",
    "create_markdown_renderer",
]
