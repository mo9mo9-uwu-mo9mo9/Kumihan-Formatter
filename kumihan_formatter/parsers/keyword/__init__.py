"""Keyword Parser Module - キーワード解析専用パーサー

責任分離により以下の構造で分割:
- keyword_parser.py: メインクラス（275行）
- keyword_handlers.py: 処理ロジック（329行）
- keyword_config.py: 設定管理（87行）
- keyword_validation.py: バリデーション（93行）
- keyword_extractors.py: 抽出処理（117行）
- keyword_utils.py: ユーティリティ（178行）
"""

from .keyword_parser import UnifiedKeywordParser
from .keyword_config import KeywordParserConfig
from .keyword_validation import KeywordValidator
from .keyword_extractors import KeywordExtractor, KeywordInfoProcessor

# 後方互換性のためのエイリアス
KeywordParser = UnifiedKeywordParser

__all__ = [
    "UnifiedKeywordParser",
    "KeywordParser",
    "KeywordParserConfig",
    "KeywordValidator",
    "KeywordExtractor",
    "KeywordInfoProcessor",
]
