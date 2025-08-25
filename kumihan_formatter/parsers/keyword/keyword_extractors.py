"""Keyword Extractors - キーワード抽出・情報処理

分離された責任:
- キーワード情報の抽出と解析
- キーワードテキストのパース処理
- キーワード情報の変換と正規化
"""

from typing import Any, Dict, List, Optional, Set, Union, TYPE_CHECKING
from ...core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import ParseContext

from .keyword_utils import setup_keyword_patterns


class KeywordExtractor:
    """キーワード抽出・解析クラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.patterns = setup_keyword_patterns()

    def extract_keyword_info(self, text: str) -> Optional[Dict[str, Any]]:
        """テキストからキーワード情報を抽出"""
        # Kumihanパターンマッチング
        match = self.patterns["kumihan"].match(text.strip())
        if match:
            keywords_text, content = match.groups()
            return {
                "keywords": self.parse_keywords_text(keywords_text),
                "content": content.strip(),
                "format": "inline",
            }

        # Kumihan開始パターン（複数行形式）
        lines = text.split("\n")
        first_line = lines[0].strip()
        match = self.patterns["kumihan_opening"].match(first_line)
        if match:
            keywords_text = match.group(1)
            content_lines = []

            for line in lines[1:]:
                if line.strip() == "##":
                    break
                content_lines.append(line)

            return {
                "keywords": self.parse_keywords_text(keywords_text),
                "content": "\n".join(content_lines).strip(),
                "format": "multiline",
            }

        return None

    def parse_keywords_text(self, keywords_text: str) -> List[str]:
        """キーワードテキストから個別キーワードを抽出"""
        keywords = []
        for match in self.patterns["keyword"].finditer(keywords_text):
            keyword = match.group(1).strip()
            if keyword:
                keywords.append(keyword)
        return keywords


class KeywordInfoProcessor:
    """キーワード情報処理・変換クラス"""

    def __init__(self, basic_keywords: Set[str], advanced_keywords: Set[str]):
        self.logger = get_logger(__name__)
        self.basic_keywords = basic_keywords
        self.advanced_keywords = advanced_keywords
        self.all_keywords = basic_keywords | advanced_keywords
        self._keyword_info_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化して文字列として返す"""
        if isinstance(content, list):
            return "\n".join(str(line) for line in content)
        return str(content)

    def get_keyword_info(
        self, keyword: str, context: Optional["ParseContext"] = None
    ) -> Optional[Dict[str, Any]]:
        """キーワード情報を取得"""
        # キャッシュ確認
        cache_key = f"info_{keyword}_{id(context) if context else 0}"
        if cache_key in self._keyword_info_cache:
            return self._keyword_info_cache[cache_key]

        # キーワード情報作成
        info = None
        if keyword in self.basic_keywords:
            info = {
                "category": "basic",
                "description": f"Basic keyword: {keyword}",
                "attributes": self._get_default_attributes(),
            }
        elif keyword in self.advanced_keywords:
            info = {
                "category": "advanced",
                "description": f"Advanced keyword: {keyword}",
                "attributes": self._get_default_attributes(),
            }

        # キャッシュ保存
        self._keyword_info_cache[cache_key] = info
        return info

    def _get_default_attributes(self) -> Dict[str, Set[str]]:
        """デフォルト属性定義を取得"""
        return {
            "style": {"color", "background", "font-size", "font-weight"},
            "class": {"highlight", "emphasis", "note", "warning", "info"},
            "data": {"id", "ref", "target", "source"},
        }
