"""Kumihan-Formatter - テキストファイルをHTMLに自動組版するCLIツール

Issue #1146 アーキテクチャ簡素化対応:
- 統合Manager/Parserシステム
- シンプルな統合API提供
"""

__version__ = "0.9.0-alpha.8"

# 統合API公開 (Issue #1146)
from .unified_api import KumihanFormatter, quick_convert, quick_parse

# 統合システム公開
from .managers import (
    CoreManager,
    ParsingManager,
    OptimizationManager,
    PluginManager,
    DistributionManager
)

from .parsers import (
    MainParser,
    BlockParser,
    KeywordParser,
    ListParser,
    ContentParser,
    MarkdownParser
)

__all__ = [
    # メインAPI
    "KumihanFormatter",
    "quick_convert",
    "quick_parse",
    
    # 統合Managerシステム
    "CoreManager",
    "ParsingManager", 
    "OptimizationManager",
    "PluginManager",
    "DistributionManager",
    
    # 統合Parserシステム
    "MainParser",
    "BlockParser",
    "KeywordParser",
    "ListParser", 
    "ContentParser",
    "MarkdownParser",
]
