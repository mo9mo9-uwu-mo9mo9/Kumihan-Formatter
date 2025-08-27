"""Keyword Parser Module - Phase3統合完了

Phase3統合により9個のキーワード関連パーサーがCoreKeywordParserに統合:
- keyword_parser.py: UnifiedKeywordParser（275行）
- keyword_handlers.py: 処理ロジック（329行）
- keyword_config.py: 設定管理（87行）
- keyword_validation.py: バリデーション（93行）
- keyword_extractors.py: 抽出処理（117行）
- keyword_utils.py: ユーティリティ（178行）
- core/parsing/keyword/base_parser.py: BaseParser
- core/parsing/keyword/content_parser.py: ContentParser
- core/parsing/keyword/marker_parser.py: MarkerParser

→ CoreKeywordParser: 1個に統合（89%削減）
"""

from ...core.parsing.integrated.core_keyword_parser import CoreKeywordParser

# 後方互換性のためのエイリアス（Phase3統合後）
UnifiedKeywordParser = CoreKeywordParser
KeywordParser = CoreKeywordParser

# レガシーコンポーネント（統合済み - 互換性目的でのみ保持）
try:
    from .keyword_config import KeywordParserConfig
    from .keyword_validation import KeywordValidator
    from .keyword_extractors import KeywordExtractor, KeywordInfoProcessor
except ImportError:
    # 統合後は内部クラスとして実装済み
    KeywordParserConfig = None
    KeywordValidator = None
    KeywordExtractor = None
    KeywordInfoProcessor = None

__all__ = [
    "CoreKeywordParser",
    "UnifiedKeywordParser",  # 互換性
    "KeywordParser",  # 互換性
    "KeywordParserConfig",  # レガシー
    "KeywordValidator",  # レガシー
    "KeywordExtractor",  # レガシー
    "KeywordInfoProcessor",  # レガシー
]
