"""
Kumihan記法キーワード定義 - Issue #476対応

キーワードの定義、設定、管理機能。
"""

from typing import Any

# デフォルトブロックキーワード定義
DEFAULT_BLOCK_KEYWORDS = {
    "太字": {"tag": "strong"},
    "イタリック": {"tag": "em"},
    "枠線": {"tag": "div", "class": "box"},
    "ハイライト": {"tag": "div", "class": "highlight"},
    "見出し1": {"tag": "h1"},
    "見出し2": {"tag": "h2"},
    "見出し3": {"tag": "h3"},
    "見出し4": {"tag": "h4"},
    "見出し5": {"tag": "h5"},
    "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
    "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
}

# キーワードネスト順序 (外側から内側へ)
NESTING_ORDER = [
    "details",  # 折りたたみ, ネタバレ
    "div",  # 枠線, ハイライト
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",  # 見出し
    "strong",  # 太字
    "em",  # イタリック
]


class KeywordDefinitions:
    """キーワード定義管理クラス"""

    def __init__(self, config: Any = None) -> None:
        """キーワード定義を初期化

        Args:
            config: 設定オブジェクト（現在未使用）
        """
        # 簡素化: 固定マーカーセットのみ使用
        self.BLOCK_KEYWORDS = DEFAULT_BLOCK_KEYWORDS.copy()
        self.nesting_order = NESTING_ORDER.copy()

    def get_all_keywords(self) -> list[str]:
        """全キーワードのリストを取得

        Returns:
            キーワード名のリスト
        """
        return list(self.BLOCK_KEYWORDS.keys())

    def is_valid_keyword(self, keyword: str) -> bool:
        """キーワードが有効かチェック

        Args:
            keyword: チェックするキーワード

        Returns:
            有効な場合True
        """
        return keyword in self.BLOCK_KEYWORDS

    def get_keyword_info(self, keyword: str) -> dict[str, Any] | None:
        """キーワードの定義情報を取得

        Args:
            keyword: キーワード名

        Returns:
            キーワード定義辞書、存在しない場合None
        """
        return self.BLOCK_KEYWORDS.get(keyword)

    def add_custom_keyword(self, keyword: str, definition: dict[str, Any]) -> None:
        """カスタムキーワードを追加

        Args:
            keyword: キーワード名
            definition: キーワード定義
        """
        self.BLOCK_KEYWORDS[keyword] = definition

    def remove_keyword(self, keyword: str) -> bool:
        """キーワードを削除

        Args:
            keyword: 削除するキーワード名

        Returns:
            削除成功時True
        """
        if keyword in self.BLOCK_KEYWORDS:
            del self.BLOCK_KEYWORDS[keyword]
            return True
        return False

    def get_nesting_order(self) -> list[str]:
        """ネスト順序を取得

        Returns:
            ネスト順序のリスト
        """
        return self.nesting_order.copy()

    def get_tag_for_keyword(self, keyword: str) -> str | None:
        """キーワードに対応するHTMLタグを取得

        Args:
            keyword: キーワード名

        Returns:
            HTMLタグ名、存在しない場合None
        """
        info = self.get_keyword_info(keyword)
        return info.get("tag") if info else None
