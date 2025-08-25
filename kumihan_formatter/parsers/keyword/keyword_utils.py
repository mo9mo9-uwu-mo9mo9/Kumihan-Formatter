"""Keyword Utilities - キーワード解析ユーティリティ群

責任分離による構造:
- パターンマッチング設定・正規表現管理
- キーワード抽出・解析ロジック
- キーワード情報処理・変換ユーティリティ
- キャッシュ管理・パフォーマンス最適化
"""

import re
from typing import Any, Dict, List, Optional, Set, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import ParseContext
else:
    try:
        from ...core.parsing.base.parser_protocols import ParseContext
    except ImportError:
        ParseContext = object

from ...core.utilities.logger import get_logger


def setup_keyword_definitions() -> Dict[str, Set[str]]:
    """キーワード定義のセットアップ"""
    basic_keywords = {
        "太字",
        "bold",
        "イタリック",
        "italic",
        "見出し",
        "heading",
        "コード",
        "code",
        "打消",
        "strikethrough",
        "下線",
        "underline",
    }

    advanced_keywords = {
        "リスト",
        "list",
        "表",
        "table",
        "引用",
        "blockquote",
        "脚注",
        "footnote",
        "リンク",
        "link",
        "画像",
        "image",
    }

    return {
        "basic": basic_keywords,
        "advanced": advanced_keywords,
        "all": basic_keywords | advanced_keywords,
    }


def setup_keyword_patterns() -> Dict[str, re.Pattern]:
    """パターンマッチング設定"""
    patterns = {
        # 基本Kumihanパターン
        "kumihan": re.compile(r"^#\s*([^#]+)\s*#([^#]*)##$"),
        "kumihan_opening": re.compile(r"^#\s*([^#]+)\s*#"),
        # キーワード抽出パターン
        "keyword": re.compile(r"([^\s,]+)"),
        # 属性パターン（AttributeParser相当）
        "attribute": re.compile(r"([a-zA-Z]+)=([\"'])([^\"']*)\2"),
        "css_class": re.compile(r"class=([\"'])([^\"']*)\1"),
        "style": re.compile(r"style=([\"'])([^\"']*)\1"),
        # マーカーパターン（MarkerParser相当）
        "marker": re.compile(r"([#]+)"),
        "delimiter": re.compile(r"([|,;:])"),
        # ネスト構造パターン
        "nest_open": re.compile(r"\{"),
        "nest_close": re.compile(r"\}"),
    }

    return patterns


class KeywordCache:
    """キーワード解析キャッシュ管理クラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._keyword_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._validation_cache: Dict[str, List[str]] = {}
        self._parse_cache: Dict[str, Any] = {}

    def get_keyword_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キーワードキャッシュから取得"""
        return self._keyword_cache.get(cache_key)

    def set_keyword_cache(
        self, cache_key: str, value: Optional[Dict[str, Any]]
    ) -> None:
        """キーワードキャッシュに保存"""
        self._keyword_cache[cache_key] = value

    def get_validation_cache(self, cache_key: str) -> Optional[List[str]]:
        """バリデーションキャッシュから取得"""
        return self._validation_cache.get(cache_key)

    def set_validation_cache(self, cache_key: str, errors: List[str]) -> None:
        """バリデーションキャッシュに保存"""
        self._validation_cache[cache_key] = errors

    def get_parse_cache(self, cache_key: str) -> Optional[Any]:
        """パースキャッシュから取得"""
        return self._parse_cache.get(cache_key)

    def set_parse_cache(self, cache_key: str, result: Any) -> None:
        """パースキャッシュに保存"""
        self._parse_cache[cache_key] = result

    def clear_all_caches(self) -> None:
        """全キャッシュクリア"""
        self._keyword_cache.clear()
        self._validation_cache.clear()
        self._parse_cache.clear()

    def clear_keyword_cache(self) -> None:
        """キーワードキャッシュクリア"""
        self._keyword_cache.clear()

    def clear_validation_cache(self) -> None:
        """バリデーションキャッシュクリア"""
        self._validation_cache.clear()

    def clear_parse_cache(self) -> None:
        """パースキャッシュクリア"""
        self._parse_cache.clear()


def create_cache_key(
    content: Union[str, List[str]],
    context: Optional["ParseContext"] = None,
    prefix: str = "",
) -> str:
    """キャッシュキー生成"""
    content_str = str(content) if isinstance(content, str) else str(content)
    context_id = id(context) if context else 0
    return f"{prefix}_{hash(content_str)}_{context_id}"


def validate_keyword_format(keyword: str) -> bool:
    """キーワードフォーマットの基本検証"""
    if not keyword or not isinstance(keyword, str):
        return False

    # 基本的な文字制約チェック
    return len(keyword.strip()) > 0 and not keyword.startswith("#")


def extract_keywords_from_text(text: str) -> List[str]:
    """シンプルなキーワード抽出（テキスト全体から）"""
    extractor = KeywordExtractor()
    keyword_info = extractor.extract_keyword_info(text)
    if keyword_info:
        return keyword_info["keywords"]
    return []


def get_keyword_category(
    keyword: str, keyword_definitions: Dict[str, Set[str]]
) -> Optional[str]:
    """キーワードのカテゴリを取得"""
    if keyword in keyword_definitions["basic"]:
        return "basic"
    elif keyword in keyword_definitions["advanced"]:
        return "advanced"
    return None
