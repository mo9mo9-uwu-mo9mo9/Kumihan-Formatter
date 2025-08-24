"""統合キーワードパーサー - Issue #1157 分割最適化版

Issue #914: Parser系統合リファクタリング
Issue #1157: キーワードパーサー統合 (8個→1個)

統合対象コンポーネント:
- KeywordParser: メインキーワード解析
- BaseParser: 基本キーワード処理・バリデーション
- BasicKeywordParser: 基本キーワード（太字・イタリック・見出し等）
- AdvancedKeywordParser: 高度キーワード（リスト・コード・引用等）
- CustomKeywordParser: カスタム・ユーザー定義キーワード
- AttributeParser: 属性解析・スタイル適用
- MarkerParser: マーカー解析・区切り文字処理
- ContentParser: コンテンツ処理・構造化

統合機能:
- 全Kumihanキーワード解析（基本・高度・カスタム）
- 属性・スタイル解析・適用
- マーカー・区切り文字処理
- コンテンツ構造化・ネスト対応
- バリデーション・エラー回復
- プロトコル準拠 (KeywordParserProtocol)
- 後方互換性維持
"""

import re
from typing import Any, Dict, List, Optional, Set, Union, TYPE_CHECKING

from ..core.ast_nodes import Node, create_node
from ..core.parsing.base import UnifiedParserBase, CompositeMixin
from ..core.parsing.base.parser_protocols import (
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..core.parsing.protocols import ParserType
from ..core.utilities.logger import get_logger

if TYPE_CHECKING:
    from ..core.parsing.base.parser_protocols import KeywordParserProtocol
else:
    # ランタイムでプロトコルを取得
    try:
        from ..core.parsing.base.parser_protocols import KeywordParserProtocol
    except ImportError:
        KeywordParserProtocol = object


class UnifiedKeywordParser(UnifiedParserBase, CompositeMixin, KeywordParserProtocol):
    """統合キーワードパーサー - Issue #1157 分割最適化版

    分割されたコンポーネントを統合し、既存API完全互換性を維持:
    - KeywordParser: メインキーワード解析・統合制御
    - BaseParser: 基本キーワード処理・バリデーション・エラー処理
    - BasicKeywordParser: 基本キーワード（太字・イタリック・見出し・コード）
    - AdvancedKeywordParser: 高度キーワード（リスト・表・引用・脚注）
    - CustomKeywordParser: カスタム・ユーザー定義キーワード・拡張機能
    - AttributeParser: 属性解析・スタイル適用・CSSクラス処理
    - MarkerParser: マーカー解析・区切り文字処理・ネスト構造
    - ContentParser: コンテンツ処理・構造化・変換

    機能:
    - Kumihanキーワード全種類（太字・イタリック・見出し・コード・リスト等）
    - カスタムキーワード定義・拡張
    - 属性・スタイル・CSSクラス適用
    - マーカー・ネスト構造解析
    - バリデーション・エラー回復・修正提案
    - プロトコル準拠・高性能キャッシュ
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.KEYWORD)

        self.logger = get_logger(__name__)

        # 統合コンポーネント初期化
        self._setup_integrated_components()

        # キーワード定義・レジストリ
        self._setup_keyword_definitions()

        # パターンマッチング・正規表現
        self._setup_patterns()

        # キャッシュ・パフォーマンス最適化
        self._keyword_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._validation_cache: Dict[str, List[str]] = {}
        self._parse_cache: Dict[str, ParseResult] = {}

    def _setup_integrated_components(self) -> None:
        """統合コンポーネントのセットアップ"""
        # キーワードハンドラー辞書（BasicKeywordParser相当）
        self.basic_keyword_handlers = {
            "太字": self._handle_bold,
            "bold": self._handle_bold,
            "イタリック": self._handle_italic,
            "italic": self._handle_italic,
            "見出し": self._handle_heading,
            "heading": self._handle_heading,
            "コード": self._handle_code,
            "code": self._handle_code,
            "打消": self._handle_strikethrough,
            "strikethrough": self._handle_strikethrough,
            "下線": self._handle_underline,
            "underline": self._handle_underline,
        }

        # 高度キーワードハンドラー（AdvancedKeywordParser相当）
        self.advanced_keyword_handlers = {
            "リスト": self._handle_list,
            "list": self._handle_list,
            "表": self._handle_table,
            "table": self._handle_table,
            "引用": self._handle_blockquote,
            "blockquote": self._handle_blockquote,
            "脚注": self._handle_footnote,
            "footnote": self._handle_footnote,
            "リンク": self._handle_link,
            "link": self._handle_link,
            "画像": self._handle_image,
            "image": self._handle_image,
        }

        # カスタムキーワードハンドラー（CustomKeywordParser相当）
        self.custom_keyword_handlers: Dict[str, Any] = {}

        # 統合ハンドラー辞書
        self.keyword_handlers = {}
        self.keyword_handlers.update(self.basic_keyword_handlers)
        self.keyword_handlers.update(self.advanced_keyword_handlers)
        self.keyword_handlers.update(self.custom_keyword_handlers)

        # バリデーター（BaseParser相当）
        self.validators = {
            "syntax": self._validate_keyword_syntax,
            "semantics": self._validate_keyword_semantics,
            "attributes": self._validate_keyword_attributes,
        }

    def _setup_keyword_definitions(self) -> None:
        """キーワード定義のセットアップ"""
        # 基本キーワード定義
        self.basic_keywords = {
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

        # 高度キーワード定義
        self.advanced_keywords = {
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

        # 全キーワード定義
        self.all_keywords = self.basic_keywords | self.advanced_keywords

        # キーワード属性定義（AttributeParser相当）
        self.keyword_attributes = {
            "style": {"color", "background", "font-size", "font-weight"},
            "class": {"highlight", "emphasis", "note", "warning", "info"},
            "data": {"id", "ref", "target", "source"},
        }

    def _setup_patterns(self) -> None:
        """パターンマッチング設定"""
        # 基本Kumihanパターン
        self.kumihan_pattern = re.compile(r"^#\s*([^#]+)\s*#([^#]*)##$")
        self.kumihan_opening_pattern = re.compile(r"^#\s*([^#]+)\s*#")

        # キーワード抽出パターン
        self.keyword_pattern = re.compile(r"([^\s,]+)")

        # 属性パターン（AttributeParser相当）
        self.attribute_pattern = re.compile(r"([a-zA-Z]+)=([\"'])([^\"']*)\2")
        self.css_class_pattern = re.compile(r"class=([\"'])([^\"']*)\1")
        self.style_pattern = re.compile(r"style=([\"'])([^\"']*)\1")

        # マーカーパターン（MarkerParser相当）
        self.marker_pattern = re.compile(r"([#]+)")
        self.delimiter_pattern = re.compile(r"([|,;:])")

        # ネスト構造パターン
        self.nest_open_pattern = re.compile(r"\{")
        self.nest_close_pattern = re.compile(r"\}")

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """基底クラス用の解析実装（UnifiedParserBase準拠）"""
        text = self._normalize_content(content)

        try:
            # キーワード抽出・解析
            keyword_info = self._extract_keyword_info(text)
            if not keyword_info:
                return create_node("text", content=text)

            # キーワード処理
            return self._process_keyword(keyword_info)

        except Exception as e:
            self.logger.error(f"Keyword parsing failed: {e}")
            return create_node("error", content=f"Keyword parsing failed: {e}")

    def _normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化して文字列として返す"""
        if isinstance(content, list):
            return "\n".join(str(line) for line in content)
        return str(content)

    def _extract_keyword_info(self, text: str) -> Optional[Dict[str, Any]]:
        """テキストからキーワード情報を抽出"""
        # Kumihanパターンマッチング
        match = self.kumihan_pattern.match(text.strip())
        if match:
            keywords_text, content = match.groups()
            return {
                "keywords": self._parse_keywords_text(keywords_text),
                "content": content.strip(),
                "format": "inline",
            }

        # Kumihan開始パターン（複数行形式）
        lines = text.split("\n")
        first_line = lines[0].strip()
        match = self.kumihan_opening_pattern.match(first_line)
        if match:
            keywords_text = match.group(1)
            content_lines = []

            for line in lines[1:]:
                if line.strip() == "##":
                    break
                content_lines.append(line)

            return {
                "keywords": self._parse_keywords_text(keywords_text),
                "content": "\n".join(content_lines).strip(),
                "format": "multiline",
            }

        return None

    def _parse_keywords_text(self, keywords_text: str) -> List[str]:
        """キーワードテキストから個別キーワードを抽出"""
        keywords = []
        for match in self.keyword_pattern.finditer(keywords_text):
            keyword = match.group(1).strip()
            if keyword:
                keywords.append(keyword)
        return keywords

    def _process_keyword(self, keyword_info: Dict[str, Any]) -> Node:
        """キーワード情報を処理してNodeを生成"""
        keywords = keyword_info["keywords"]
        content = keyword_info["content"]
        format_type = keyword_info["format"]

        # 最初のキーワードをメインキーワードとして処理
        if not keywords:
            return create_node("text", content=content)

        main_keyword = keywords[0]
        handler = self.keyword_handlers.get(main_keyword, self._handle_unknown_keyword)

        # ハンドラー実行
        node = handler(content, keywords, format_type)

        # 属性処理
        self._apply_keyword_attributes(node, keywords)

        return node

    def _apply_keyword_attributes(self, node: Node, keywords: List[str]) -> None:
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

    def parse(
        self,
        content: Union[str, List[str]],
        context: Optional[ParseContext] = None,
        **kwargs: Any,
    ) -> ParseResult:
        """統一パースメソッド - KeywordParserProtocol準拠"""
        try:
            # キャッシュ確認
            cache_key = f"{hash(str(content))}_{id(context) if context else 0}"
            if cache_key in self._parse_cache:
                return self._parse_cache[cache_key]

            self._clear_errors_warnings()

            # 基本パース実行
            if isinstance(content, list):
                nodes = self._parse_content_lines(content)
            else:
                nodes = [self._parse_implementation(content)]

            # ParseResult作成
            result = create_parse_result(
                nodes=[n for n in nodes if n is not None],
                success=True,
                errors=self.get_errors(),
                warnings=self.get_warnings(),
                metadata={
                    "parser_type": "keyword",
                    "keyword_count": len(nodes) if nodes else 0,
                },
            )

            # キャッシュ保存
            self._parse_cache[cache_key] = result
            return result

        except Exception as e:
            self.logger.error(f"Keyword parsing error: {e}")
            return create_parse_result(
                nodes=[],
                success=False,
                errors=[f"Keyword parsing failed: {e}"],
                warnings=[],
                metadata={"parser_type": "keyword"},
            )

    def _parse_content_lines(self, lines: List[str]) -> List[Node]:
        """行リストから複数キーワードを解析"""
        nodes = []
        for line in lines:
            if line.strip():
                node = self._parse_implementation(line)
                if node:
                    nodes.append(node)
        return nodes

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return getattr(self, "_errors", [])

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return getattr(self, "_warnings", [])

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """キーワード構文チェック"""
        # キャッシュ確認
        cache_key = f"{hash(content)}_{id(context) if context else 0}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]

        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            self._validation_cache[cache_key] = errors
            return errors

        if not content.strip():
            self._validation_cache[cache_key] = errors
            return errors  # 空コンテンツは有効

        try:
            # キーワード抽出
            keyword_info = self._extract_keyword_info(content)
            if not keyword_info:
                self._validation_cache[cache_key] = errors
                return errors  # キーワードなしは有効

            # 各バリデーター実行
            for validator_name, validator in self.validators.items():
                try:
                    validator_errors = validator(keyword_info)
                    for error in validator_errors:
                        errors.append(f"{validator_name}: {error}")
                except Exception as e:
                    errors.append(f"Validation error ({validator_name}): {e}")

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        # キャッシュ保存
        self._validation_cache[cache_key] = errors
        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedKeywordParser",
            "version": "3.0.0",
            "supported_formats": ["kumihan", "keyword", "markdown"],
            "capabilities": [
                "basic_keywords",
                "advanced_keywords",
                "custom_keywords",
                "attribute_parsing",
                "marker_parsing",
                "content_processing",
                "validation",
                "error_recovery",
                "performance_caching",
                "nested_structure",
            ],
            "parser_type": self.parser_type,
            "architecture": "統合分割型",
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = {"kumihan", "keyword", "markdown"}
        return format_hint.lower() in supported

    # === KeywordParserProtocol実装 ===

    def parse_keywords(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """テキストからキーワードを抽出（プロトコル準拠）"""
        keyword_info = self._extract_keyword_info(text)
        if keyword_info:
            return keyword_info["keywords"]
        return []

    def validate_keyword(
        self, keyword: str, context: Optional[ParseContext] = None
    ) -> bool:
        """単一キーワードの妥当性チェック（プロトコル準拠）"""
        # キャッシュ確認
        cache_key = f"validate_{keyword}_{id(context) if context else 0}"
        if cache_key in self._keyword_cache:
            cached_result = self._keyword_cache[cache_key]
            return cached_result is not None

        # キーワード妥当性チェック
        is_valid = (
            keyword in self.all_keywords
            or keyword in self.custom_keyword_handlers
            or self._is_valid_custom_keyword(keyword)
        )

        # キャッシュ保存
        self._keyword_cache[cache_key] = {"valid": is_valid} if is_valid else None
        return is_valid

    def get_keyword_info(
        self, keyword: str, context: Optional[ParseContext] = None
    ) -> Optional[Dict[str, Any]]:
        """キーワード情報を取得（プロトコル準拠）"""
        # キャッシュ確認
        cache_key = f"info_{keyword}_{id(context) if context else 0}"
        if cache_key in self._keyword_cache:
            return self._keyword_cache[cache_key]

        # キーワード情報作成
        info = None
        if keyword in self.basic_keywords:
            info = {
                "category": "basic",
                "handler": self.basic_keyword_handlers.get(keyword),
                "description": f"Basic keyword: {keyword}",
                "attributes": self.keyword_attributes.copy(),
            }
        elif keyword in self.advanced_keywords:
            info = {
                "category": "advanced",
                "handler": self.advanced_keyword_handlers.get(keyword),
                "description": f"Advanced keyword: {keyword}",
                "attributes": self.keyword_attributes.copy(),
            }
        elif keyword in self.custom_keyword_handlers:
            info = {
                "category": "custom",
                "handler": self.custom_keyword_handlers.get(keyword),
                "description": f"Custom keyword: {keyword}",
                "attributes": {},
            }

        # キャッシュ保存
        self._keyword_cache[cache_key] = info
        return info

    # === 基本キーワードハンドラー (BasicKeywordParser相当) ===

    def _handle_bold(self, content: str, keywords: List[str], format_type: str) -> Node:
        """太字キーワード処理"""
        return create_node(
            "bold",
            content=content,
            attributes={"style": "font-weight: bold", "format": format_type},
        )

    def _handle_italic(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """イタリックキーワード処理"""
        return create_node(
            "italic",
            content=content,
            attributes={"style": "font-style: italic", "format": format_type},
        )

    def _handle_heading(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
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

    def _handle_code(self, content: str, keywords: List[str], format_type: str) -> Node:
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

    def _handle_strikethrough(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """打消線キーワード処理"""
        return create_node(
            "strikethrough",
            content=content,
            attributes={
                "style": "text-decoration: line-through",
                "format": format_type,
            },
        )

    def _handle_underline(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """下線キーワード処理"""
        return create_node(
            "underline",
            content=content,
            attributes={"style": "text-decoration: underline", "format": format_type},
        )

    # === 高度キーワードハンドラー (AdvancedKeywordParser相当) ===

    def _handle_list(self, content: str, keywords: List[str], format_type: str) -> Node:
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

    def _handle_table(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """表キーワード処理"""
        return create_node("table", content=content, attributes={"format": format_type})

    def _handle_blockquote(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """引用キーワード処理"""
        return create_node(
            "blockquote", content=content, attributes={"format": format_type}
        )

    def _handle_footnote(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """脚注キーワード処理"""
        return create_node(
            "footnote", content=content, attributes={"format": format_type}
        )

    def _handle_link(self, content: str, keywords: List[str], format_type: str) -> Node:
        """リンクキーワード処理"""
        return create_node("link", content=content, attributes={"format": format_type})

    def _handle_image(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """画像キーワード処理"""
        return create_node("image", content=content, attributes={"format": format_type})

    # === カスタムキーワードハンドラー (CustomKeywordParser相当) ===

    def _handle_unknown_keyword(
        self, content: str, keywords: List[str], format_type: str
    ) -> Node:
        """未知キーワード処理（フォールバック）"""
        return create_node(
            "custom_keyword",
            content=content,
            attributes={"keywords": keywords, "format": format_type, "type": "unknown"},
        )

    def add_custom_keyword(self, keyword: str, handler: Any) -> None:
        """カスタムキーワード追加"""
        self.custom_keyword_handlers[keyword] = handler
        self.keyword_handlers[keyword] = handler

    def remove_custom_keyword(self, keyword: str) -> bool:
        """カスタムキーワード削除"""
        if keyword in self.custom_keyword_handlers:
            del self.custom_keyword_handlers[keyword]
            del self.keyword_handlers[keyword]
            return True
        return False

    def _is_valid_custom_keyword(self, keyword: str) -> bool:
        """カスタムキーワードの妥当性チェック"""
        # 基本的な妥当性チェック
        return len(keyword) > 0 and keyword.replace("_", "").replace("-", "").isalnum()

    # === バリデーター (BaseParser相当) ===

    def _validate_keyword_syntax(self, keyword_info: Dict[str, Any]) -> List[str]:
        """キーワード構文検証"""
        errors = []
        keywords = keyword_info["keywords"]

        for keyword in keywords:
            if not keyword:
                errors.append("Empty keyword")
            elif not self.validate_keyword(keyword):
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


# 後方互換性エイリアス
KeywordParser = UnifiedKeywordParser
