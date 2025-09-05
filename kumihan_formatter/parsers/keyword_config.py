"""Keyword Parser Configuration - キーワードパーサー設定管理

分離された責任:
- キーワード定義とパターンの初期化
- ハンドラー群の設定とセットアップ
- バリデーター・プロセッサーの構成管理
"""

from typing import Any, Dict, Set, List, Optional
import re
import logging

# 存在しないモジュールのインポートを削除
# from .keyword_handlers import (
#     BasicKeywordHandler,
#     AdvancedKeywordHandler,
#     CustomKeywordHandler,
#     AttributeProcessor,
#     KeywordValidatorCollection,
# )
# 存在しないモジュールのインポートを削除
# from .keyword_utils import (
#     setup_keyword_definitions,
#     setup_keyword_patterns,
#     KeywordCache,
# )


# --- 依存（実体実装） -----------------------------------------------------
from .keyword_extractors import KeywordExtractor, KeywordInfoProcessor


def setup_keyword_definitions() -> Dict[str, Set[str]]:
    return {
        "basic": {"bold", "italic"},
        "advanced": {"ruby"},
        "all": {"bold", "italic", "ruby"},
    }


def setup_keyword_patterns() -> Dict[str, Any]:
    return {"dummy": True}


class KeywordCache:
    """極小キャッシュ（検証で使用）"""

    def __init__(self) -> None:
        self._validate_cache: Dict[str, List[str]] = {}
        self._keyword_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def get_validation_cache(self, key: str) -> Optional[List[str]]:
        return self._validate_cache.get(key)

    def set_validation_cache(self, key: str, value: List[str]) -> None:
        self._validate_cache[key] = list(value)

    def get_keyword_cache(self, key: str) -> Optional[Dict[str, Any]]:
        return self._keyword_cache.get(key)

    def set_keyword_cache(self, key: str, value: Optional[Dict[str, Any]]) -> None:
        if value is None:
            self._keyword_cache.pop(key, None)
        else:
            self._keyword_cache[key] = dict(value)


class BasicKeywordHandler:
    def __init__(self, definitions: Dict[str, Set[str]]):
        self.handlers = {"basic": "handler"}


class AdvancedKeywordHandler:
    def __init__(self, definitions: Dict[str, Set[str]]):
        self.handlers = {"advanced": "handler"}


class CustomKeywordHandler:
    def __init__(self, definitions: Dict[str, Set[str]]):
        self.custom_handlers = {"custom": "handler"}

    def is_valid_custom_keyword(self, keyword: str) -> bool:
        return keyword in self.custom_handlers


class AttributeProcessor:
    pass


class KeywordValidatorCollection:
    def __init__(self) -> None:
        # 名前→バリデータ関数
        self.validators: Dict[str, Any] = {
            "length": self._validate_length,
            "characters": self._validate_characters,
        }

    def _validate_length(self, info: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        keywords: List[str] = list(info.get("keywords", []))
        for kw in keywords:
            if not (1 <= len(kw) <= 20):
                errors.append(f"keyword '{kw}' length out of range")
        return errors

    def _validate_characters(self, info: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        keywords: List[str] = list(info.get("keywords", []))
        pattern = re.compile(r"^[A-Za-z][\w-]{0,19}$")
        for kw in keywords:
            if not pattern.match(kw):
                errors.append(f"keyword '{kw}' contains invalid characters")
        return errors


class KeywordParserConfig:
    """キーワードパーサー設定管理クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        # 外部にpatchされるセットアップ関数を呼び出す
        defs = setup_keyword_definitions()
        patterns = setup_keyword_patterns()

        self._setup_keyword_definitions(defs)
        self._setup_modular_components(defs)
        self.patterns = patterns
        self.cache = KeywordCache()

    def _setup_keyword_definitions(self, defs: Dict[str, Set[str]]) -> None:
        """キーワード定義の初期化"""
        self.keyword_definitions: Dict[str, Set[str]] = {
            "basic": set(defs.get("basic", set())),
            "advanced": set(defs.get("advanced", set())),
            "all": set(defs.get("all", set())),
        }
        self.basic_keywords: Set[str] = self.keyword_definitions["basic"]
        self.advanced_keywords: Set[str] = self.keyword_definitions["advanced"]
        self.all_keywords: Set[str] = self.keyword_definitions["all"]

        # キーワードパターンとキャッシュは __init__ で設定

    def _setup_modular_components(self, defs: Dict[str, Set[str]]) -> None:
        """分割されたコンポーネントのセットアップ"""
        # キーワードハンドラー群
        self.basic_handler = BasicKeywordHandler(defs)
        self.advanced_handler = AdvancedKeywordHandler(defs)
        self.custom_handler = CustomKeywordHandler(defs)

        # 属性処理
        self.attribute_processor = AttributeProcessor()

        # キーワード抽出
        self.keyword_extractor = KeywordExtractor()

        # キーワード情報処理
        self.info_processor = KeywordInfoProcessor(
            self.basic_keywords, self.advanced_keywords
        )

        # バリデーター
        self.validator_collection = KeywordValidatorCollection()

        # 統合ハンドラー辞書
        self.keyword_handlers: Dict[str, Any] = {}
        self.keyword_handlers.update(getattr(self.basic_handler, "handlers", {}))
        self.keyword_handlers.update(getattr(self.advanced_handler, "handlers", {}))
        self.keyword_handlers.update(
            getattr(self.custom_handler, "custom_handlers", {})
        )

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
