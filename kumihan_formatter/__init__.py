"""Kumihan-Formatter - テキストファイルをHTMLに自動組版するCLIツール

Issue #1171 Manager統合最適化対応:
- 統合Manager/Parserシステム
- シンプルな統合API提供
"""

__version__ = "0.9.0-alpha.8"

# 統合API公開 (Issue #1146)
from .unified_api import KumihanFormatter, quick_convert, quick_parse

# 統合システム公開
from .managers import (
    ParseManager,
    RenderManager,
    ConfigManager,
    ValidationManager,
    ResourceManager,
)

from .parsers import (
    MainParser,
    BlockParser,
    KeywordParser,
    ListParser,
    ContentParser,
    MarkdownParser,
)

__all__ = [
    # メインAPI
    "KumihanFormatter",
    "quick_convert",
    "quick_parse",
    # Issue #1171対応 - 統合Managerシステム
    "ParseManager",
    "RenderManager",
    "ConfigManager",
    "ValidationManager",
    "ResourceManager",
    # 統合Parserシステム
    "MainParser",
    "BlockParser",
    "KeywordParser",
    "ListParser",
    "ContentParser",
    "MarkdownParser",
]
