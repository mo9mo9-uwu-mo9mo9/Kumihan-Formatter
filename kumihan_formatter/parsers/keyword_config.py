"""Keyword Parser Configuration - キーワードパーサー設定管理

分離された責任:
- キーワード定義とパターンの初期化
- ハンドラー群の設定とセットアップ
- バリデーター・プロセッサーの構成管理
"""

from typing import Any, Dict, Set
import logging
from .keyword_handlers import (
    BasicKeywordHandler,
    AdvancedKeywordHandler,
    CustomKeywordHandler,
    AttributeProcessor,
    KeywordValidatorCollection,
)
from .keyword_utils import (
    setup_keyword_definitions,
    setup_keyword_patterns,
    KeywordCache,
)
from .keyword_extractors import KeywordExtractor, KeywordInfoProcessor


class KeywordParserConfig:
    """キーワードパーサー設定管理クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._setup_keyword_definitions()
        self._setup_modular_components()

    def _setup_keyword_definitions(self) -> None:
        """キーワード定義の初期化"""
        self.keyword_definitions = setup_keyword_definitions()
        self.basic_keywords = self.keyword_definitions["basic"]
        self.advanced_keywords = self.keyword_definitions["advanced"]
        self.all_keywords = self.keyword_definitions["all"]

        # キーワードパターンとキャッシュ
        self.patterns = setup_keyword_patterns()
        self.cache = KeywordCache()

    def _setup_modular_components(self) -> None:
        """分割されたコンポーネントのセットアップ"""
        # キーワードハンドラー群
        self.basic_handler = BasicKeywordHandler()
        self.advanced_handler = AdvancedKeywordHandler()
        self.custom_handler = CustomKeywordHandler()

        # 属性処理
        self.attribute_processor = AttributeProcessor()

        # キーワード抽出
        self.keyword_extractor = KeywordExtractor()

        # キーワード情報処理
        self.info_processor = KeywordInfoProcessor(
            self.basic_keywords, self.advanced_keywords
        )

        # バリデーター
        self.validator_collection = KeywordValidatorCollection(
            self.basic_keywords, self.advanced_keywords, self.custom_handler
        )

        # 統合ハンドラー辞書
        self.keyword_handlers: Dict[str, Any] = {}
        self.keyword_handlers.update(self.basic_handler.handlers)
        self.keyword_handlers.update(self.advanced_handler.handlers)
        self.keyword_handlers.update(self.custom_handler.custom_handlers)

    def get_handlers(self) -> Dict[str, Any]:
        """統合ハンドラー辞書を取得"""
        return self.keyword_handlers

    def get_basic_keywords(self) -> Set[str]:
        """基本キーワード定義を取得"""
        return self.basic_keywords

    def get_advanced_keywords(self) -> Set[str]:
        """高度キーワード定義を取得"""
        return self.advanced_keywords

    def get_all_keywords(self) -> Set[str]:
        """全キーワード定義を取得"""
        return self.all_keywords
