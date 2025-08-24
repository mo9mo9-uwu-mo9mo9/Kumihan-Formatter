"""
統合Parser システム - Issue #1146 アーキテクチャ簡素化
====================================================

従来の41個のParserファイルを10個に統合:
1. MainParser - メイン解析エンジン
2. BlockParser - ブロック処理
3. KeywordParser - キーワード処理
4. ListParser - リスト処理
5. ContentParser - コンテンツ処理
6. MarkdownParser - Markdown処理
7. SpecializedParser - 特殊処理
8. StreamingParser - ストリーミング処理
9. ParserUtils - ユーティリティ
10. ParserProtocols - インターフェース
"""

from .main_parser import UnifiedMainParser as MainParser
from .block_parser import UnifiedBlockParser as BlockParser
from .keyword_parser import UnifiedKeywordParser as KeywordParser
from .list_parser import UnifiedListParser as ListParser
from .content_parser import UnifiedContentParser as ContentParser
from .markdown_parser import UnifiedMarkdownParser as MarkdownParser
from .specialized_parser import SpecializedParser
from .streaming_parser import UnifiedStreamingParser as StreamingParser
from .parser_utils import ParserUtils
from .parser_protocols import ParserProtocols

__all__ = [
    "MainParser",
    "BlockParser", 
    "KeywordParser",
    "ListParser",
    "ContentParser",
    "MarkdownParser",
    "SpecializedParser",
    "StreamingParser",
    "ParserUtils",
    "ParserProtocols",
]