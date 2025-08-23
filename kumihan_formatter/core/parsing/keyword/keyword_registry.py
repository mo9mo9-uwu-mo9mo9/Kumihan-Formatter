"""
キーワード登録・管理システム
国際化対応とキーワード抽象化
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class KeywordType(Enum):
    """キーワードタイプの列挙"""

    DECORATION = "decoration"  # 装飾系（太字、下線等）
    LAYOUT = "layout"  # レイアウト系（中央寄せ、注意等）
    STRUCTURE = "structure"  # 構造系（見出し、リスト等）
    CONTENT = "content"  # コンテンツ系（コード、引用等）


@dataclass
class KeywordDefinition:
    """キーワード定義のデータクラス"""

    keyword_id: str  # 内部識別子（言語非依存）
    display_names: Dict[str, str]  # 言語別表示名
    tag: str  # HTMLタグ
    keyword_type: KeywordType  # キーワードタイプ
    attributes: Optional[Dict[str, Any]] = None  # HTML属性
    special_options: Optional[Dict[str, Any]] = None  # 特別なオプション
    css_requirements: Optional[List[str]] = None  # 必要なCSSクラス
    description: Optional[Dict[str, str]] = None  # 言語別説明


class KeywordRegistry:
    """多言語対応キーワード登録システム"""

    def __init__(self, default_language: str = "ja"):
        """初期化

        Args:
            default_language: デフォルト言語コード
        """
        self.default_language = default_language
        self.keywords: Dict[str, KeywordDefinition] = {}
        self._language_mappings: Dict[str, Dict[str, str]] = (
            {}
        )  # 言語 -> {表示名: keyword_id}

        # Phase 2キーワードの登録
        self._register_advanced_keywords()

    def _register_advanced_keywords(self) -> None:
        """高度なキーワードを登録"""

        # 高度な基本装飾キーワード
        self.register_keyword(
            KeywordDefinition(
                keyword_id="underline",
                display_names={"ja": "下線", "en": "underline"},
                tag="u",
                keyword_type=KeywordType.DECORATION,
                description={
                    "ja": "テキストに下線を追加",
                    "en": "Add underline to text",
                },
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="strikethrough",
                display_names={"ja": "取り消し線", "en": "strikethrough"},
                tag="del",
                keyword_type=KeywordType.DECORATION,
                description={
                    "ja": "テキストに取り消し線を追加",
                    "en": "Add strikethrough to text",
                },
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="inline_code",
                display_names={"ja": "コード", "en": "code"},
                tag="code",
                keyword_type=KeywordType.CONTENT,
                description={"ja": "インラインコード", "en": "Inline code"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="blockquote",
                display_names={"ja": "引用", "en": "quote"},
                tag="blockquote",
                keyword_type=KeywordType.CONTENT,
                description={"ja": "引用ブロック", "en": "Quote block"},
            )
        )

        # 高度なレイアウトキーワード
        self.register_keyword(
            KeywordDefinition(
                keyword_id="center_align",
                display_names={"ja": "中央寄せ", "en": "center"},
                tag="div",
                keyword_type=KeywordType.LAYOUT,
                attributes={"style": "text-align: center"},
                description={"ja": "テキストを中央揃え", "en": "Center align text"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="warning_alert",
                display_names={"ja": "注意", "en": "warning"},
                tag="div",
                keyword_type=KeywordType.LAYOUT,
                attributes={"class": "alert warning"},
                css_requirements=["alert", "warning"],
                description={"ja": "注意・警告メッセージ", "en": "Warning message"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="info_alert",
                display_names={"ja": "情報", "en": "info"},
                tag="div",
                keyword_type=KeywordType.LAYOUT,
                attributes={"class": "alert info"},
                css_requirements=["alert", "info"],
                description={"ja": "情報メッセージ", "en": "Information message"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="code_block",
                display_names={"ja": "コードブロック", "en": "codeblock"},
                tag="pre",
                keyword_type=KeywordType.CONTENT,
                special_options={"wrap_with_code": True},
                description={"ja": "コードブロック", "en": "Code block"},
            )
        )

        # 既存キーワードの追加（互換性のため）
        self._register_existing_keywords()

    def _register_existing_keywords(self) -> None:
        """既存キーワードを登録（後方互換性）"""
        existing_keywords = [
            ("bold", {"ja": "太字", "en": "bold"}, "strong", KeywordType.DECORATION),
            (
                "italic",
                {"ja": "イタリック", "en": "italic"},
                "em",
                KeywordType.DECORATION,
            ),
            (
                "italic_alt",
                {"ja": "斜体", "en": "oblique"},
                "em",
                KeywordType.DECORATION,
            ),
            (
                "heading1",
                {"ja": "見出し1", "en": "heading1"},
                "h1",
                KeywordType.STRUCTURE,
            ),
            (
                "heading2",
                {"ja": "見出し2", "en": "heading2"},
                "h2",
                KeywordType.STRUCTURE,
            ),
            (
                "heading3",
                {"ja": "見出し3", "en": "heading3"},
                "h3",
                KeywordType.STRUCTURE,
            ),
            (
                "heading4",
                {"ja": "見出し4", "en": "heading4"},
                "h4",
                KeywordType.STRUCTURE,
            ),
            (
                "heading5",
                {"ja": "見出し5", "en": "heading5"},
                "h5",
                KeywordType.STRUCTURE,
            ),
            ("list", {"ja": "リスト", "en": "list"}, "ul", KeywordType.STRUCTURE),
        ]

        for keyword_id, names, tag, kw_type in existing_keywords:
            self.register_keyword(
                KeywordDefinition(
                    keyword_id=keyword_id,
                    display_names=names,
                    tag=tag,
                    keyword_type=kw_type,
                )
            )

        # 特別な属性を持つキーワード
        self.register_keyword(
            KeywordDefinition(
                keyword_id="box_border",
                display_names={"ja": "枠線", "en": "border"},
                tag="div",
                keyword_type=KeywordType.LAYOUT,
                attributes={"class": "box"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="highlight",
                display_names={"ja": "ハイライト", "en": "highlight"},
                tag="div",
                keyword_type=KeywordType.LAYOUT,
                attributes={"class": "highlight"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="collapsible",
                display_names={"ja": "折りたたみ", "en": "collapsible"},
                tag="details",
                keyword_type=KeywordType.STRUCTURE,
                attributes={"summary": "詳細を表示"},
            )
        )

        self.register_keyword(
            KeywordDefinition(
                keyword_id="spoiler",
                display_names={"ja": "ネタバレ", "en": "spoiler"},
                tag="details",
                keyword_type=KeywordType.STRUCTURE,
                attributes={"summary": "ネタバレを表示"},
            )
        )

    def register_keyword(self, definition: KeywordDefinition) -> None:
        """キーワードを登録

        Args:
            definition: キーワード定義
        """
        self.keywords[definition.keyword_id] = definition
        self._update_language_mappings(definition)

    def register(
        self, keyword_id: str, definition: Optional[Dict[str, Any]] = None
    ) -> str:
        """キーワードを登録（テスト互換用エイリアス）

        Args:
            keyword_id: キーワードID
            definition: キーワード定義辞書

        Returns:
            str: 登録結果 ("success" または "error")
        """
        try:
            # 簡易KeywordDefinitionを作成（同じファイル内で定義済み）
            if definition is None:
                definition = {}

            # より堅牢な実装
            display_names = definition.get("display_names", {"en": keyword_id, "ja": keyword_id})
            if not display_names:
                display_names = {"en": keyword_id, "ja": keyword_id}

            keyword_def = KeywordDefinition(
                keyword_id=keyword_id,
                display_names=display_names,
                tag=definition.get("tag", "span"),
                keyword_type=definition.get("type", KeywordType.DECORATION),
            )

            self.register_keyword(keyword_def)

            # 確実に登録されているかチェック
            if keyword_id in self.keywords:
                return "success"
            else:
                return "error"
        except Exception as e:
            # デバッグ情報をログ出力（本番では削除）
            import logging
            logging.debug(f"KeywordRegistry.register failed: {e}")
            return "error"

    def get(self, keyword_id: str) -> str:
        """キーワードを取得（テスト互換用エイリアス）

        Args:
            keyword_id: キーワードID

        Returns:
            str: 取得結果 ("retrieval" または "not_found")
        """
        if self.is_registered(keyword_id):
            return "retrieval"
        else:
            return "not_found"

    def bulk_register(self, keywords: List[Dict[str, Any]]) -> bool:
        """複数キーワードの一括登録（テスト互換用）

        Args:
            keywords: キーワード定義のリスト

        Returns:
            bool: 全ての登録が成功した場合True
        """
        try:
            for keyword_data in keywords:
                keyword_id = keyword_data.get("id", keyword_data.get("keyword_id", ""))
                if keyword_id:
                    result = self.register(keyword_id, keyword_data)
                    if result != "success":
                        return False
            return True
        except Exception:
            return False

    def bulk_get(self, keyword_ids: List[str]) -> Dict[str, str]:
        """複数キーワードの一括取得（テスト互換用）

        Args:
            keyword_ids: キーワードIDのリスト

        Returns:
            Dict[str, str]: キーワードID -> 取得結果のマッピング
        """
        results = {}
        for keyword_id in keyword_ids:
            results[keyword_id] = self.get(keyword_id)
        return results

    def _update_language_mappings(self, definition: KeywordDefinition) -> None:
        """言語別マッピングを更新

        Args:
            definition: キーワード定義
        """
        # 言語別マッピングを更新
        for language, display_name in definition.display_names.items():
            if language not in self._language_mappings:
                self._language_mappings[language] = {}
            self._language_mappings[language][display_name] = definition.keyword_id

    def get_keyword_by_display_name(
        self, display_name: str, language: Optional[str] = None
    ) -> Optional[KeywordDefinition]:
        """表示名からキーワード定義を取得

        Args:
            display_name: 表示名
            language: 言語コード（省略時はデフォルト言語）

        Returns:
            KeywordDefinition: キーワード定義（見つからない場合None）
        """
        if language is None:
            language = self.default_language

        language_mapping = self._language_mappings.get(language, {})
        keyword_id = language_mapping.get(display_name)

        if keyword_id:
            return self.keywords.get(keyword_id)

        return None

    def get_keyword_by_id(self, keyword_id: str) -> Optional[KeywordDefinition]:
        """IDからキーワード定義を取得

        Args:
            keyword_id: キーワードID

        Returns:
            KeywordDefinition: キーワード定義（見つからない場合None）
        """
        return self.keywords.get(keyword_id)

    def is_registered(self, keyword_id: str) -> bool:
        """キーワードが登録済みかチェック

        Args:
            keyword_id: キーワードID

        Returns:
            bool: 登録済みの場合True
        """
        return keyword_id in self.keywords

    def get_all_display_names(self, language: Optional[str] = None) -> List[str]:
        """指定言語の全表示名を取得

        Args:
            language: 言語コード（省略時はデフォルト言語）

        Returns:
            List[str]: 表示名のリスト
        """
        if language is None:
            language = self.default_language

        return list(self._language_mappings.get(language, {}).keys())

    def get_keywords_by_type(
        self, keyword_type: KeywordType
    ) -> List[KeywordDefinition]:
        """タイプ別キーワード一覧を取得

        Args:
            keyword_type: キーワードタイプ

        Returns:
            List[KeywordDefinition]: キーワード定義のリスト
        """
        return [kw for kw in self.keywords.values() if kw.keyword_type == keyword_type]

    def convert_to_legacy_format(
        self, language: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """従来形式の辞書に変換（後方互換性）

        Args:
            language: 言語コード（省略時はデフォルト言語）

        Returns:
            Dict: 従来形式のキーワード辞書
        """
        if language is None:
            language = self.default_language

        legacy_dict = {}

        for keyword_def in self.keywords.values():
            display_name = keyword_def.display_names.get(language)
            if not display_name:
                continue

            # 従来形式の辞書エントリを構築
            entry = {"tag": keyword_def.tag}

            if keyword_def.attributes:
                entry.update(keyword_def.attributes)

            if keyword_def.special_options:
                entry.update(keyword_def.special_options)

            legacy_dict[display_name] = entry

        return legacy_dict

    def get_supported_languages(self) -> List[str]:
        """サポート対象言語のリストを取得

        Returns:
            List[str]: 言語コードのリスト
        """
        return list(self._language_mappings.keys())

    def switch_language(self, language: str) -> bool:
        """デフォルト言語を切り替え

        Args:
            language: 新しいデフォルト言語コード

        Returns:
            bool: 切り替え成功時True
        """
        if language in self._language_mappings:
            self.default_language = language
            return True

        return False
