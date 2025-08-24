"""Keyword Handlers - キーワード処理ハンドラー群

責任分離による構造:
- BasicKeywordHandler: 基本キーワード処理（太字・イタリック・見出し等）
- AdvancedKeywordHandler: 高度キーワード処理（リスト・表・引用等）
- CustomKeywordHandler: カスタムキーワード処理・拡張機能
- AttributeProcessor: 属性処理・スタイル適用
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.ast_nodes import Node
    from ...core.parsing.base.parser_protocols import ParseContext
else:
    try:
        from ...core.ast_nodes import Node, create_node
        from ...core.parsing.base.parser_protocols import ParseContext
    except ImportError:
        Node = None
        create_node = None
        ParseContext = object

from ...core.utilities.logger import get_logger


class BasicKeywordHandler:
    """基本キーワード処理ハンドラー - BasicKeywordParser相当"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_basic_handlers()

    def _setup_basic_handlers(self) -> None:
        """基本キーワードハンドラー辞書の設定"""
        self.handlers = {
            "太字": self.handle_bold,
            "bold": self.handle_bold,
            "イタリック": self.handle_italic,
            "italic": self.handle_italic,
            "見出し": self.handle_heading,
            "heading": self.handle_heading,
            "コード": self.handle_code,
            "code": self.handle_code,
            "打消": self.handle_strikethrough,
            "strikethrough": self.handle_strikethrough,
            "下線": self.handle_underline,
            "underline": self.handle_underline,
        }

    def handle_bold(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """太字キーワード処理"""
        return create_node(
            "bold",
            content=content,
            attributes={"style": "font-weight: bold", "format": format_type},
        )

    def handle_italic(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """イタリックキーワード処理"""
        return create_node(
            "italic",
            content=content,
            attributes={"style": "font-style: italic", "format": format_type},
        )

    def handle_heading(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """見出しキーワード処理"""
        # レベル決定（キーワードから推定）
        level = 1
        for keyword in keywords:
            if keyword.isdigit():
                level = int(keyword)
                break
            elif keyword in {"h2", "h3", "h4", "h5", "h6"}:
                level = int(keyword[1])
                break

        return create_node(
            "heading",
            content=content,
            attributes={"level": level, "format": format_type},
        )

    def handle_code(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """コードキーワード処理"""
        # 言語決定
        language = "text"
        for keyword in keywords:
            if keyword in {"python", "javascript", "java", "cpp", "html", "css"}:
                language = keyword
                break

        return create_node(
            "code",
            content=content,
            attributes={"language": language, "format": format_type},
        )

    def handle_strikethrough(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """打消線キーワード処理"""
        return create_node(
            "strikethrough",
            content=content,
            attributes={
                "style": "text-decoration: line-through",
                "format": format_type,
            },
        )

    def handle_underline(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """下線キーワード処理"""
        return create_node(
            "underline",
            content=content,
            attributes={"style": "text-decoration: underline", "format": format_type},
        )


class AdvancedKeywordHandler:
    """高度キーワード処理ハンドラー - AdvancedKeywordParser相当"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_advanced_handlers()

    def _setup_advanced_handlers(self) -> None:
        """高度キーワードハンドラー辞書の設定"""
        self.handlers = {
            "リスト": self.handle_list,
            "list": self.handle_list,
            "表": self.handle_table,
            "table": self.handle_table,
            "引用": self.handle_blockquote,
            "blockquote": self.handle_blockquote,
            "脚注": self.handle_footnote,
            "footnote": self.handle_footnote,
            "リンク": self.handle_link,
            "link": self.handle_link,
            "画像": self.handle_image,
            "image": self.handle_image,
        }

    def handle_list(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """リストキーワード処理"""
        list_type = "unordered"
        for keyword in keywords:
            if keyword in {"ordered", "numbered"}:
                list_type = "ordered"
                break

        return create_node(
            "list",
            content=content,
            attributes={"list_type": list_type, "format": format_type},
        )

    def handle_table(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """表キーワード処理"""
        return create_node("table", content=content, attributes={"format": format_type})

    def handle_blockquote(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """引用キーワード処理"""
        return create_node(
            "blockquote", content=content, attributes={"format": format_type}
        )

    def handle_footnote(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """脚注キーワード処理"""
        return create_node(
            "footnote", content=content, attributes={"format": format_type}
        )

    def handle_link(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """リンクキーワード処理"""
        return create_node("link", content=content, attributes={"format": format_type})

    def handle_image(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """画像キーワード処理"""
        return create_node("image", content=content, attributes={"format": format_type})


class CustomKeywordHandler:
    """カスタムキーワード処理ハンドラー - CustomKeywordParser相当"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.custom_handlers: Dict[str, Any] = {}

    def handle_unknown_keyword(
        self, content: str, keywords: List[str], format_type: str
    ) -> "Node":
        """未知キーワード処理（フォールバック）"""
        return create_node(
            "custom_keyword",
            content=content,
            attributes={"keywords": keywords, "format": format_type, "type": "unknown"},
        )

    def add_custom_keyword(self, keyword: str, handler: Any) -> None:
        """カスタムキーワード追加"""
        self.custom_handlers[keyword] = handler

    def remove_custom_keyword(self, keyword: str) -> bool:
        """カスタムキーワード削除"""
        if keyword in self.custom_handlers:
            del self.custom_handlers[keyword]
            return True
        return False

    def is_valid_custom_keyword(self, keyword: str) -> bool:
        """カスタムキーワードの妥当性チェック"""
        # 基本的な妥当性チェック
        return len(keyword) > 0 and keyword.replace("_", "").replace("-", "").isalnum()


class AttributeProcessor:
    """属性処理・スタイル適用 - AttributeParser相当"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self._setup_attribute_definitions()

    def _setup_attribute_definitions(self) -> None:
        """キーワード属性定義"""
        self.keyword_attributes = {
            "style": {"color", "background", "font-size", "font-weight"},
            "class": {"highlight", "emphasis", "note", "warning", "info"},
            "data": {"id", "ref", "target", "source"},
        }

    def apply_keyword_attributes(self, node: "Node", keywords: List[str]) -> None:
        """キーワードに基づいて属性を適用"""
        if not hasattr(node, "attributes") or node.attributes is None:
            node.attributes = {}

        # キーワードリストを属性に保存
        node.attributes["keywords"] = keywords

        # 特別な属性処理
        for keyword in keywords[1:]:  # メインキーワード以外を属性として処理
            if keyword in {"highlight", "emphasis", "note", "warning", "info"}:
                if "class" not in node.attributes:
                    node.attributes["class"] = []
                node.attributes["class"].append(keyword)


class KeywordValidatorCollection:
    """キーワードバリデーター集合 - BaseParser相当"""

    def __init__(
        self,
        basic_keywords: set,
        advanced_keywords: set,
        custom_handler: CustomKeywordHandler,
    ):
        self.logger = get_logger(__name__)
        self.basic_keywords = basic_keywords
        self.advanced_keywords = advanced_keywords
        self.custom_handler = custom_handler

        self.validators = {
            "syntax": self._validate_keyword_syntax,
            "semantics": self._validate_keyword_semantics,
            "attributes": self._validate_keyword_attributes,
        }

    def _validate_keyword_syntax(self, keyword_info: Dict[str, Any]) -> List[str]:
        """キーワード構文検証"""
        errors = []
        keywords = keyword_info["keywords"]

        for keyword in keywords:
            if not keyword:
                errors.append("Empty keyword")
            elif not self._is_valid_keyword(keyword):
                errors.append(f"Unknown keyword: {keyword}")

        return errors

    def _validate_keyword_semantics(self, keyword_info: Dict[str, Any]) -> List[str]:
        """キーワード意味検証"""
        errors = []
        keywords = keyword_info["keywords"]

        # 矛盾するキーワードの検出
        if "太字" in keywords and "bold" in keywords:
            errors.append("Duplicate bold keywords (太字 and bold)")

        return errors

    def _validate_keyword_attributes(self, keyword_info: Dict[str, Any]) -> List[str]:
        """キーワード属性検証"""
        errors = []
        # 属性バリデーション（将来の拡張用）
        return errors

    def _is_valid_keyword(self, keyword: str) -> bool:
        """キーワードの妥当性チェック"""
        return (
            keyword in self.basic_keywords
            or keyword in self.advanced_keywords
            or keyword in self.custom_handler.custom_handlers
            or self.custom_handler.is_valid_custom_keyword(keyword)
        )
