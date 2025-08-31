"""Keyword Definitions - キーワード定義

Phase2最適化により作成された統合キーワード定義
"""

from typing import Dict, List, Any, Optional

# デフォルトのブロックキーワード
DEFAULT_BLOCK_KEYWORDS = [
    "太字",
    "bold",
    "イタリック",
    "italic",
    "見出し",
    "heading",
    "脚注",
    "footnote",
    "リンク",
    "link",
    "画像",
    "image",
]


class KeywordDefinitions:
    """キーワード定義管理クラス"""

    def __init__(self, custom_keywords: Optional[Dict[str, Any]] = None) -> None:
        self.keywords = custom_keywords or {}
        self.default_keywords = DEFAULT_BLOCK_KEYWORDS

    def get_keyword(self, keyword: str) -> Any:
        """キーワード定義を取得"""
        return self.keywords.get(keyword, keyword)

    def add_keyword(self, keyword: str, definition: Any) -> None:
        """キーワード定義を追加"""
        self.keywords[keyword] = definition

    def get_all_keywords(self) -> List[str]:
        """全キーワードを取得"""
        return list(self.keywords.keys()) + self.default_keywords
