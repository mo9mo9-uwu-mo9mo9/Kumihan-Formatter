"""Parser Module - 統合パーサーシステム

Issue #1215対応完了版：11個のParserを統合管理
"""

# 統合パーサーシステム
from .main_parser import MainParser

# 個別パーサー（必要時直接アクセス用）
from .unified_list_parser import UnifiedListParser
from .unified_keyword_parser import UnifiedKeywordParser
from .unified_markdown_parser import UnifiedMarkdownParser

# プロトコル・ユーティリティ
from .parser_protocols import ParserProtocol

__all__ = [
    "MainParser",
    "UnifiedListParser",
    "UnifiedKeywordParser",
    "UnifiedMarkdownParser",
    "ParserProtocol",
]


# 便利な統合関数
def parse(content, parser_type="auto", config=None):
    """統合パーシング関数（簡易アクセス）"""
    main_parser = MainParser(config)
    return main_parser.parse(content, parser_type)
