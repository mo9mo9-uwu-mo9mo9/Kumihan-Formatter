"""
Kumihan記法キーワード定義 - Issue #476対応

キーワードの定義、設定、管理機能。
"""

from typing import Any

# デフォルトブロックキーワード定義
DEFAULT_BLOCK_KEYWORDS = {
    "太字": {"tag": "strong"},
    "イタリック": {"tag": "em"},
    "下線": {"tag": "u"},
    "取り消し線": {"tag": "del"},
    "コード": {"tag": "code"},
    "引用": {"tag": "blockquote"},
    "枠線": {"tag": "div", "class": "box"},
    "ハイライト": {"tag": "div", "class": "highlight"},
    "見出し1": {"tag": "h1"},
    "見出し2": {"tag": "h2"},
    "見出し3": {"tag": "h3"},
    "見出し4": {"tag": "h4"},
    "見出し5": {"tag": "h5"},
    "折りたたみ": {"tag": "details"},
    "ネタバレ": {"tag": "details", "class": "spoiler"},
    "中央寄せ": {"tag": "div", "style": "text-align: center"},
    "注意": {"tag": "div", "class": "warning"},
    "情報": {"tag": "div", "class": "info"},
    "コードブロック": {"tag": "pre", "class": "code-block"},
    "テスト": {"tag": "div", "class": "test"},
    "ルビ": {"tag": "ruby", "content_parser": "ruby"},
    "脚注": {"tag": "span", "class": "footnote", "special_handler": "footnote"},
}

# キーワードネスト順序 (外側から内側へ)
NESTING_ORDER = [
    "details",  # 折りたたみ, ネタバレ
    "div",  # 枠線, ハイライト, 中央寄せ, 注意, 情報
    "pre",  # コードブロック
    "blockquote",  # 引用
    "ul",  # リスト
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",  # 見出し
    "strong",  # 太字
    "u",  # 下線
    "del",  # 取り消し線
    "em",  # イタリック
    "code",  # コード
    "ruby",  # ルビ
    "span",  # 脚注
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

    def add_custom_keyword(self, keyword: str, definition: Any) -> None:
        """カスタムキーワードを追加

        Args:
            keyword: キーワード名
            definition: キーワード定義

        Raises:
            ValueError: 無効なキーワード名またはキーワード定義の場合
        """
        # キーワード名の検証
        validation_error = self._validate_keyword_name(keyword)
        if validation_error:
            raise ValueError(validation_error)

        # キーワード定義の検証
        definition_error = self._validate_keyword_definition(definition)
        if definition_error:
            raise ValueError(definition_error)

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

    def normalize_keyword(self, keyword: str) -> str:
        """キーワード名を正規化（テスト互換性のため）

        Args:
            keyword: 正規化するキーワード

        Returns:
            str: 正規化されたキーワード
        """
        return keyword.strip()

    def get_keyword_registry(self) -> Any:
        """多言語対応キーワードレジストリを取得

        Returns:
            KeywordRegistry: キーワードレジストリインスタンス
        """
        from .keyword_registry import KeywordRegistry

        if not hasattr(self, "_registry"):
            self._registry = KeywordRegistry()

        return self._registry

    def switch_language(self, language: str) -> bool:
        """使用言語を変更（国際化対応）

        Args:
            language: 言語コード（ja, en等）

        Returns:
            bool: 変更成功時True
        """
        registry = self.get_keyword_registry()
        if registry.switch_language(language):
            # レジストリから新しい言語のキーワード辞書を取得
            self.BLOCK_KEYWORDS = registry.convert_to_legacy_format(language)
            return True

    def get_supported_languages(self) -> list[str]:
        """サポート対象言語一覧を取得

        Returns:
            list[str]: 言語コードのリスト
        """
        registry = self.get_keyword_registry()
        # 明示的に list[str] として型を指定
        languages: list[str] = registry.get_supported_languages()
        return languages

    def is_css_dependent(self, keyword: str) -> bool:
        """キーワードがCSS依存かどうかを判定

        Args:
            keyword: キーワード名

        Returns:
            bool: CSS依存の場合True
        """
        registry = self.get_keyword_registry()
        keyword_def = registry.get_keyword_by_display_name(keyword)

        if keyword_def and keyword_def.css_requirements:
            return len(keyword_def.css_requirements) > 0

    def get_css_requirements(self, keyword: str) -> list[str]:
        """キーワードのCSS要件を取得

        Args:
            keyword: キーワード名

        Returns:
            list[str]: 必要なCSSクラス名のリスト
        """
        registry = self.get_keyword_registry()
        keyword_def = registry.get_keyword_by_display_name(keyword)

        if keyword_def and keyword_def.css_requirements:
            # 明示的に list[str] として型を指定
            css_reqs: list[str] = keyword_def.css_requirements[:]
            return css_reqs

    def _validate_keyword_name(self, keyword: str) -> str | None:
        """
        キーワード名の妥当性を検証

        Args:
            keyword: 検証するキーワード名

        Returns:
            str | None: エラーメッセージ（問題ない場合はNone）
        """
        if not keyword or not keyword.strip():
            return "キーワード名が空です"

    def _validate_keyword_definition(self, definition: Any) -> str | None:
        """
        キーワード定義の妥当性を検証

        Args:
            definition: 検証するキーワード定義

        Returns:
            str | None: エラーメッセージ（問題ない場合はNone）
        """
        if not isinstance(definition, dict):
            return "キーワード定義は辞書である必要があります"

        # 必須フィールドのチェック
        if "tag" not in definition:
            return "キーワード定義にtagフィールドが必要です"

        tag = definition["tag"]
        if not isinstance(tag, str):
            return "tagフィールドは文字列である必要があります"

        # 有効なHTMLタグのチェック
        valid_tags = {
            "strong",
            "em",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "details",
            "u",
            "code",
            "del",
            "ruby",
            "span",
            "p",
        }

        if tag not in valid_tags:
            return f"無効なHTMLタグです: '{tag}'"

        return None
