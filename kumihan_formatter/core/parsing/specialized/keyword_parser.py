"""統一キーワードパーサー

Issue #912: Parser系統合リファクタリング
3つの重複KeywordParserを完全統合:
- core/keyword_parser.py (518行、DEFAULT_BLOCK_KEYWORDS、非推奨マーク)
- core/keyword_parsing/parsers/keyword_parser.py (基本実装、マーカー解析)
- core/parsing/specialized/keyword_parser.py (統一実装、最も完全)

統合機能:
- キーワード定義・検証
- マーカー解析・属性解析
- 複合キーワード分割
- ルビ記法処理
- インライン記法マッピング
- 後方互換性維持
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ...ast_nodes import (
    Node,
    NodeBuilder,
    create_node,
    emphasis,
    error_node,
    highlight,
    strong,
)
from ..base import CompositeMixin, UnifiedParserBase
from ..base.parser_protocols import (
    KeywordParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType


class UnifiedKeywordParser(UnifiedParserBase, CompositeMixin, KeywordParserProtocol):
    """統一キーワードパーサー

    3つの重複KeywordParserを統合:
    - DEFAULT_BLOCK_KEYWORDS (core/keyword_parser.py から)
    - マーカー解析機能 (keyword_parsing/parsers/ から)
    - 統一パーサー機能 (existing implementation)

    機能:
    - キーワード定義・検証
    - マーカー解析・属性解析
    - 複合キーワード分割・ネスト構造構築
    - ルビ記法・インライン記法処理
    - 後方互換性維持
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.KEYWORD)

        # キーワード管理
        self._setup_keyword_registry()
        self._setup_keyword_patterns()
        self._setup_attribute_handlers()

        # 統合機能: core/keyword_parser.py からの機能
        self._setup_legacy_compatibility()
        self._setup_inline_mapping()
        self._setup_nesting_order()

    def _setup_keyword_registry(self) -> None:
        """キーワードレジストリの設定"""
        # デフォルトキーワード定義
        self.default_keywords = {
            # 基本装飾
            "太字": {"type": "decoration", "html_tag": "strong"},
            "斜体": {"type": "decoration", "html_tag": "em"},
            "下線": {"type": "decoration", "html_tag": "u"},
            "取消": {"type": "decoration", "html_tag": "del"},
            # 色・スタイル
            "赤": {"type": "color", "color": "red"},
            "青": {"type": "color", "color": "blue"},
            "緑": {"type": "color", "color": "green"},
            "黄": {"type": "color", "color": "yellow"},
            # 特殊ブロック
            "重要": {"type": "block", "class": "important"},
            "注意": {"type": "block", "class": "warning"},
            "情報": {"type": "block", "class": "info"},
            "エラー": {"type": "block", "class": "error"},
            # コンテンツ
            "画像": {"type": "media", "tag": "img"},
            "リンク": {"type": "link", "tag": "a"},
            "コード": {"type": "code", "tag": "code"},
            # 構造要素
            "見出し": {"type": "heading", "levels": [1, 2, 3, 4, 5, 6]},
            "リスト": {"type": "list", "variants": ["ul", "ol"]},
            "表": {"type": "table", "tag": "table"},
        }

        # カスタムキーワード（ユーザー定義）
        self.custom_keywords: Dict[str, Dict[str, Any]] = {}

        # 非推奨キーワード
        self.deprecated_keywords: Set[str] = set()

    def _setup_keyword_patterns(self) -> None:
        """キーワード解析パターンの設定"""
        self.keyword_patterns = {
            # キーワード分割パターン
            "split": re.compile(r"[+\-,]"),
            # 複合キーワードパターン: 太字+赤
            "compound": re.compile(r"^([^+\-,]+)([+\-,])(.+)$"),
            # 属性付きキーワードパターン: 太字[color:red]
            "with_attributes": re.compile(r"^([^[\]]+)(\[.+\])$"),
            # レベル指定パターン: 見出し1, 見出し2
            "with_level": re.compile(r"^(.+?)(\d+)$"),
            # 否定パターン: -太字
            "negation": re.compile(r"^-(.+)$"),
        }

    def _setup_attribute_handlers(self) -> None:
        """属性ハンドラーの設定"""
        self.attribute_handlers = {
            "color": self._handle_color_attribute,
            "size": self._handle_size_attribute,
            "align": self._handle_align_attribute,
            "class": self._handle_class_attribute,
            "id": self._handle_id_attribute,
            "style": self._handle_style_attribute,
        }

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """キーワード記法の解析可能性を判定"""
        if not super().can_parse(content):
            return False

        text = content if isinstance(content, str) else "\n".join(content)

        # Kumihanキーワード記法の特徴を検出
        return self._contains_keywords(text)

    def _contains_keywords(self, text: str) -> bool:
        """既知のキーワードが含まれているかチェック"""
        all_keywords = set(self.default_keywords.keys()) | set(
            self.custom_keywords.keys()
        )

        for keyword in all_keywords:
            if keyword in text:
                return True

        # パターンベースの検出
        if re.search(r"#[^#]+#[^#]*##", text):
            return True

        return False

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """キーワード解析の実装"""
        self._start_timer("keyword_parsing")

        try:
            text = content if isinstance(content, str) else "\n".join(content)

            # 解析結果を格納するノード
            root_node = create_node("keyword_document", content=text)

            # テキスト内のキーワードを解析
            keywords_found = self._extract_all_keywords(text)

            for keyword_info in keywords_found:
                keyword_node = self._create_keyword_node(keyword_info)
                root_node.children.append(keyword_node)

            self._end_timer("keyword_parsing")
            return root_node

        except Exception as e:
            self.add_error(f"キーワード解析エラー: {str(e)}")
            return create_node("error", content=f"Keyword parse error: {e}")

    def _extract_all_keywords(self, text: str) -> List[Dict[str, Any]]:
        """テキストからすべてのキーワードを抽出"""
        keywords_found = []

        # ブロック内キーワードの抽出
        block_matches = re.finditer(r"#([^#]+)#([^#]*)##", text)
        for match in block_matches:
            keyword_text = match.group(1).strip()
            content = match.group(2).strip()

            keyword_info = self._parse_keyword_string(keyword_text)
            keyword_info.update(
                {"content": content, "position": match.span(), "context": "block"}
            )
            keywords_found.append(keyword_info)

        # インライン単体キーワードの抽出
        all_keywords = set(self.default_keywords.keys()) | set(
            self.custom_keywords.keys()
        )
        for keyword in all_keywords:
            # ブロック外での単体使用を検出
            pattern = rf"\b{re.escape(keyword)}\b"
            for match in re.finditer(pattern, text):
                # ブロック内でないかチェック
                if not self._is_in_block_context(text, match.span()):
                    keyword_info = {
                        "keyword": keyword,
                        "attributes": {},
                        "position": match.span(),
                        "context": "inline",
                    }
                    keywords_found.append(keyword_info)

        return keywords_found

    def _parse_keyword_string(self, keyword_text: str) -> Dict[str, Any]:
        """キーワード文字列の解析"""
        result = {
            "keyword": "",
            "attributes": {},
            "modifiers": [],
            "level": None,
            "negated": False,
        }

        # 否定の処理
        negation_match = self.keyword_patterns["negation"].match(keyword_text)
        if negation_match:
            result["negated"] = True
            keyword_text = negation_match.group(1)

        # 属性付きキーワードの処理
        attr_match = self.keyword_patterns["with_attributes"].match(keyword_text)
        if attr_match:
            keyword_text = attr_match.group(1).strip()
            attr_text = attr_match.group(2)
            result["attributes"] = self._parse_attributes(attr_text)

        # レベル指定の処理
        level_match = self.keyword_patterns["with_level"].match(keyword_text)
        if level_match:
            keyword_text = level_match.group(1).strip()
            result["level"] = int(level_match.group(2))

        # 複合キーワードの処理
        compound_match = self.keyword_patterns["compound"].match(keyword_text)
        if compound_match:
            primary = compound_match.group(1).strip()
            separator = compound_match.group(2)
            secondary = compound_match.group(3).strip()

            result["keyword"] = primary
            if separator == "+":
                result["modifiers"].append(secondary)
            elif separator == "-":
                result["exclusions"] = [secondary]
        else:
            result["keyword"] = keyword_text.strip()

        return result

    def _parse_attributes(self, attr_text: str) -> Dict[str, str]:
        """属性文字列の解析"""
        attributes = {}

        # [key:value] 形式の属性を抽出
        attr_pattern = re.compile(r"\[([^\]]+)\]")
        for match in attr_pattern.finditer(attr_text):
            attr_content = match.group(1)

            if ":" in attr_content:
                key, value = attr_content.split(":", 1)
                attributes[key.strip()] = value.strip()
            else:
                # 値なしの属性（フラグ）
                attributes[attr_content.strip()] = True

        return attributes

    def _create_keyword_node(self, keyword_info: Dict[str, Any]) -> Node:
        """キーワード情報からノードを作成"""
        keyword = keyword_info["keyword"]
        content = keyword_info.get("content", "")

        # キーワード定義の取得
        definition = self._get_keyword_definition(keyword)

        if definition:
            node_type = definition.get("type", "keyword")
            node = create_node(node_type, content=content)

            # 基本メタデータの設定
            node.metadata.update(
                {
                    "keyword": keyword,
                    "definition": definition,
                    "attributes": keyword_info["attributes"],
                    "context": keyword_info["context"],
                    "position": keyword_info["position"],
                }
            )

            # 特殊処理
            if "level" in keyword_info and keyword_info["level"]:
                node.metadata["level"] = keyword_info["level"]

            if "modifiers" in keyword_info:
                node.metadata["modifiers"] = keyword_info["modifiers"]

            if keyword_info.get("negated"):
                node.metadata["negated"] = True

            # 属性ハンドラーの適用
            self._apply_attribute_handlers(node, keyword_info["attributes"])

        else:
            # 未定義キーワード
            node = create_node("unknown_keyword", content=content)
            node.metadata.update(
                {
                    "keyword": keyword,
                    "context": keyword_info["context"],
                    "warning": f"未定義のキーワード: {keyword}",
                }
            )
            self.add_warning(f"未定義のキーワード: {keyword}")

        return node

    def _get_keyword_definition(self, keyword: str) -> Optional[Dict[str, Any]]:
        """キーワード定義を取得"""
        if keyword in self.custom_keywords:
            return self.custom_keywords[keyword]
        elif keyword in self.default_keywords:
            return self.default_keywords[keyword]
        else:
            return None

    def _apply_attribute_handlers(self, node: Node, attributes: Dict[str, Any]) -> None:
        """属性ハンドラーを適用"""
        for attr_name, attr_value in attributes.items():
            if attr_name in self.attribute_handlers:
                handler = self.attribute_handlers[attr_name]
                handler(node, attr_value)

    def _handle_color_attribute(self, node: Node, value: Any) -> None:
        """色属性のハンドラー"""
        node.metadata["color"] = value
        if "styles" not in node.metadata:
            node.metadata["styles"] = {}
        node.metadata["styles"]["color"] = value

    def _handle_size_attribute(self, node: Node, value: Any) -> None:
        """サイズ属性のハンドラー"""
        node.metadata["size"] = value
        if "styles" not in node.metadata:
            node.metadata["styles"] = {}
        node.metadata["styles"]["font-size"] = value

    def _handle_align_attribute(self, node: Node, value: Any) -> None:
        """配置属性のハンドラー"""
        node.metadata["align"] = value
        if "styles" not in node.metadata:
            node.metadata["styles"] = {}
        node.metadata["styles"]["text-align"] = value

    def _handle_class_attribute(self, node: Node, value: Any) -> None:
        """クラス属性のハンドラー"""
        if "classes" not in node.metadata:
            node.metadata["classes"] = []

        if isinstance(value, str):
            classes = value.split()
            node.metadata["classes"].extend(classes)
        else:
            node.metadata["classes"].append(str(value))

    def _handle_id_attribute(self, node: Node, value: Any) -> None:
        """ID属性のハンドラー"""
        node.metadata["id"] = str(value)

    def _handle_style_attribute(self, node: Node, value: Any) -> None:
        """スタイル属性のハンドラー"""
        if "styles" not in node.metadata:
            node.metadata["styles"] = {}

        # CSS形式のスタイル文字列を解析
        if isinstance(value, str):
            style_pairs = value.split(";")
            for pair in style_pairs:
                if ":" in pair:
                    prop, val = pair.split(":", 1)
                    node.metadata["styles"][prop.strip()] = val.strip()

    def _is_in_block_context(self, text: str, position: tuple) -> bool:
        """指定位置がブロックコンテキスト内かチェック"""
        start, end = position

        # 前後のテキストでブロックパターンを確認
        before = text[:start]
        after = text[end:]

        # ブロック開始がposition前にあり、終了がposition後にあるかチェック
        block_start = before.rfind("#")
        block_end = after.find("##")

        return block_start != -1 and block_end != -1

    # 外部API メソッド

    def register_keyword(self, keyword: str, definition: Dict[str, Any]) -> None:
        """カスタムキーワードを登録"""
        self.custom_keywords[keyword] = definition
        self.logger.info(f"Registered custom keyword: {keyword}")

    def unregister_keyword(self, keyword: str) -> bool:
        """カスタムキーワードの登録解除"""
        if keyword in self.custom_keywords:
            del self.custom_keywords[keyword]
            self.logger.info(f"Unregistered custom keyword: {keyword}")
            return True
        return False

    def deprecate_keyword(self, keyword: str) -> None:
        """キーワードを非推奨にマーク"""
        self.deprecated_keywords.add(keyword)
        self.logger.warning(f"Keyword marked as deprecated: {keyword}")

    def get_keyword_suggestions(self, partial: str) -> List[str]:
        """部分文字列にマッチするキーワード候補を取得"""
        all_keywords = set(self.default_keywords.keys()) | set(
            self.custom_keywords.keys()
        )
        suggestions = [kw for kw in all_keywords if partial.lower() in kw.lower()]
        return sorted(suggestions)

    def validate_keyword(self, keyword: str) -> Dict[str, Any]:
        """キーワードの妥当性を検証"""
        result = {
            "valid": False,
            "type": None,
            "definition": None,
            "deprecated": False,
            "suggestions": [],
        }

        definition = self._get_keyword_definition(keyword)
        if definition:
            result["valid"] = True
            result["type"] = definition.get("type")
            result["definition"] = definition
            result["deprecated"] = keyword in self.deprecated_keywords
        else:
            # 類似キーワードの提案
            result["suggestions"] = self.get_keyword_suggestions(keyword)

        return result

    def get_keyword_statistics(self) -> Dict[str, Any]:
        """キーワード統計情報を取得"""
        stats = self._get_performance_stats()
        stats.update(
            {
                "default_keywords": len(self.default_keywords),
                "custom_keywords": len(self.custom_keywords),
                "deprecated_keywords": len(self.deprecated_keywords),
                "total_keywords": len(self.default_keywords)
                + len(self.custom_keywords),
                "parser_type": self.parser_type,
            }
        )
        return stats

    # ==========================================
    # 統合機能: 3つのKeywordParserからの機能統合
    # ==========================================

    def _setup_legacy_compatibility(self) -> None:
        """core/keyword_parser.py からの後方互換性機能"""
        # DEFAULT_BLOCK_KEYWORDS の統合（core/keyword_parser.pyから）
        self.DEFAULT_BLOCK_KEYWORDS = {
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

        # 既存のdefault_keywordsとマージ
        for keyword, definition in self.DEFAULT_BLOCK_KEYWORDS.items():
            if keyword not in self.default_keywords:
                self.default_keywords[keyword] = {"type": "legacy_block", **definition}

        # 後方互換性プロパティ
        self.BLOCK_KEYWORDS = self.DEFAULT_BLOCK_KEYWORDS

        # core/keyword_parser.pyからの設定とメソッドを統合
        from ...keyword import KeywordDefinitions, KeywordValidator, MarkerParser

        # 分割されたコンポーネントを初期化（後方互換性のため）
        try:
            self.definitions = KeywordDefinitions(None)
            self.marker_parser = MarkerParser(self.definitions)
            self.validator = KeywordValidator(self.definitions)
        except Exception:
            # フォールバック：基本的な実装を使用
            self.definitions = None
            self.marker_parser = None
            self.validator = None

    def _setup_inline_mapping(self) -> None:
        """インライン記法マッピングの設定"""
        self._inline_pattern = re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##")
        self._inline_keyword_mapping = {
            "太字": strong,
            "イタリック": emphasis,
            "ハイライト": highlight,
            "下線": lambda text: NodeBuilder("u").content(text).build(),
            "コード": lambda text: NodeBuilder("code").content(text).build(),
            "取り消し線": lambda text: NodeBuilder("del").content(text).build(),
            "ルビ": self._create_ruby_node,
        }

    def _setup_nesting_order(self) -> None:
        """キーワードネスト順序の設定"""
        self.NESTING_ORDER = [
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

    def parse_marker_keywords(
        self, marker_content: str
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析

        keyword_parsing/parsers/keyword_parser.py からの統合機能

        Args:
            marker_content: マーカーコンテンツ

        Returns:
            (キーワードリスト, 属性辞書, エラーリスト)
        """
        if not isinstance(marker_content, str):
            return [], {}, ["Invalid marker content type"]

        keywords: List[str] = []
        attributes: Dict[str, Any] = {}
        errors: List[str] = []

        marker_content = marker_content.strip()
        if not marker_content:
            return keywords, attributes, errors

        try:
            # ルビ記法の特別処理
            if marker_content.startswith("ルビ "):
                ruby_content = marker_content[3:].strip()
                ruby_result = self._parse_ruby_content(ruby_content)
                if ruby_result:
                    attributes["ruby"] = ruby_result
                    return keywords, attributes, errors

            # 複合キーワードの処理
            if "+" in marker_content or "＋" in marker_content:
                compound_keywords = self.split_compound_keywords(marker_content)
                for part in compound_keywords:
                    if part and self._is_valid_keyword(part):
                        keywords.append(part)
            else:
                # 単一キーワード
                keyword = marker_content.strip()
                if keyword and self._is_valid_keyword(keyword):
                    keywords.append(keyword)

        except Exception as e:
            errors.append(f"マーカー解析エラー: {str(e)}")

        return keywords, attributes, errors

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別のキーワードに分割

        Args:
            keyword_content: 分割対象のキーワード文字列

        Returns:
            個別キーワードのリスト
        """
        if not isinstance(keyword_content, str):
            return []

        keywords: List[str] = []

        # 複合キーワード記号での分割
        if "+" in keyword_content or "＋" in keyword_content:
            parts = re.split(r"[+＋]", keyword_content)
            for part in parts:
                part = part.strip()
                if part and self._is_valid_keyword(part):
                    keywords.append(part)
        else:
            # 単一キーワード
            keyword = keyword_content.strip()
            if keyword and self._is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords

    def parse_keywords(self, content: str) -> List[str]:
        """コンテンツからキーワードを抽出

        KeywordParserProtocol の実装
        """
        if not content:
            return []

        keywords = []

        # ブロック記法からのキーワード抽出
        block_matches = re.finditer(r"#([^#]+)#[^#]*##", content)
        for match in block_matches:
            keyword_text = match.group(1).strip()
            if self._is_valid_keyword(keyword_text):
                keywords.append(keyword_text)

        return keywords

    def _is_valid_keyword(self, keyword: str) -> bool:
        """キーワードの有効性チェック"""
        if not keyword or not isinstance(keyword, str):
            return False

        keyword = keyword.strip()

        # デフォルトキーワードまたはカスタムキーワードに存在するか
        return (
            keyword in self.default_keywords
            or keyword in self.custom_keywords
            or keyword in self.DEFAULT_BLOCK_KEYWORDS
        )

    def _parse_ruby_content(self, ruby_content: str) -> Optional[Dict[str, str]]:
        """ルビ記法の解析"""
        if not ruby_content:
            return None

        # ルビ記法: base|ruby 形式
        if "|" in ruby_content:
            parts = ruby_content.split("|", 1)
            if len(parts) == 2:
                return {"base": parts[0].strip(), "ruby": parts[1].strip()}

        # 単純なルビ
        return {"base": ruby_content, "ruby": ""}

    def _create_ruby_node(self, text: str) -> Node:
        """ルビノードの作成"""
        ruby_info = self._parse_ruby_content(text)
        if ruby_info:
            return (
                NodeBuilder("ruby")
                .content(ruby_info["base"])
                .attribute("data-ruby", ruby_info["ruby"])
                .build()
            )
        else:
            return NodeBuilder("span").content(text).build()

    def _normalize_marker_syntax(self, marker_content: str) -> str:
        """マーカー記法の正規化（レガシー機能）"""
        if not marker_content:
            return ""

        # 記号の正規化
        marker_content = marker_content.replace("＋", "+")
        marker_content = marker_content.replace("－", "-")

        return marker_content.strip()

    # ==========================================
    # core/keyword_parser.py からの統合メソッド群
    # ==========================================

    def create_single_block(
        self, keyword: str, content: str, attributes: Dict[str, Any]
    ) -> Node:
        """単一ブロックノードの作成（core/keyword_parser.pyから統合）"""
        if keyword not in self.BLOCK_KEYWORDS:
            return error_node(f"不明なキーワード: {keyword}")

        # Create builder for the block
        builder = NodeBuilder(node_type=self.BLOCK_KEYWORDS[keyword]["tag"]).content(
            content
        )

        # Add attributes if provided
        if attributes:
            for key, value in attributes.items():
                builder.attribute(key, value)

        return builder.build()

    def create_compound_block(
        self, keywords: List[str], content: str, attributes: Dict[str, Any]
    ) -> Node:
        """複合ブロック構造の作成（core/keyword_parser.pyから統合）"""
        if not keywords:
            return error_node("キーワードが指定されていません")

        # Sort keywords by nesting order
        sorted_keywords = self._sort_keywords_by_nesting_order(keywords)

        root_node = None
        current_node = None

        # Build nested structure from outer to inner
        for i, keyword in enumerate(sorted_keywords):
            if keyword not in self.BLOCK_KEYWORDS:
                return error_node(f"不明なキーワード: {keyword}")

            block_def = self.BLOCK_KEYWORDS[keyword]
            builder = NodeBuilder(block_def["tag"])

            # Add CSS class if specified
            if "class" in block_def:
                builder.css_class(block_def["class"])

            # Add summary for details elements
            if "summary" in block_def:
                builder.attribute("summary", block_def["summary"])

            # Handle special attributes for the outermost element
            if i == 0:
                # Handle color attribute for highlight
                if keyword == "ハイライト" and "color" in attributes:
                    color = attributes["color"]
                    color = self._normalize_color_value(color)
                    builder.style(f"background-color:{color}")

                # Add other attributes
                for key, value in attributes.items():
                    if key not in ["color"]:
                        builder.attribute(key, value)

            # Set content for the innermost element
            if i == len(sorted_keywords) - 1:
                parsed_content = self._parse_block_content(content)
                builder.content(parsed_content)
            else:
                # This will be set when we build the nested structure
                builder.content([""])

            # Build the node
            node = builder.build()

            if root_node is None:
                root_node = node
                current_node = node
            else:
                # Find the content and replace it with the new node
                if (
                    current_node
                    and hasattr(current_node, "content")
                    and current_node.content
                ):
                    current_node.content = [node]
                current_node = node

        return root_node or error_node("ノード作成に失敗しました")

    def _parse_block_content(self, content: str) -> List[Any]:
        """ブロックコンテンツの解析（core/keyword_parser.pyから統合）"""
        if not content.strip():
            return [""]

        # ブロックコンテンツの解析を実装
        return [content]

    def _normalize_color_value(self, color: str) -> str:
        """色値を正規化（core/keyword_parser.pyから統合）"""
        # 既に16進数形式の場合はそのまま返す
        if color.startswith("#"):
            return color

        # その他の場合はそのまま返す（将来の拡張のため）
        return color

    def _sort_keywords_by_nesting_order(self, keywords: List[str]) -> List[str]:
        """ネスト順序でキーワードをソート（core/keyword_parser.pyから統合）"""
        # Map keywords to their tags
        keyword_tags = {}
        for keyword in keywords:
            if keyword in self.BLOCK_KEYWORDS:
                tag = self.BLOCK_KEYWORDS[keyword]["tag"]
                keyword_tags[keyword] = tag

        # Sort by nesting order
        def get_nesting_index(keyword: str) -> int:
            tag = keyword_tags.get(keyword)
            if tag in self.NESTING_ORDER:
                return self.NESTING_ORDER.index(tag)
            return 999  # 不明なタグは最後に

        return sorted(keywords, key=get_nesting_index)

    def parse_new_format(self, line: str) -> Dict[str, Any]:
        """新形式マーカーの解析（後方互換用）"""
        # 基本的な解析結果を返す
        return {"keywords": [], "content": line, "attributes": {}}

    def get_node_factory(self, keywords: Union[str, Tuple[Any, ...]]) -> Any:
        """ノードファクトリーの取得（後方互換用）"""
        # NodeBuilderインスタンスを返す
        return NodeBuilder(node_type="div")

    # ==========================================
    # プロトコル準拠メソッド（KeywordParserProtocol実装）
    # ==========================================

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース（プロトコル準拠）"""
        try:
            # 既存の parse_keywords ロジックを活用
            keywords = self.parse_keywords(content)
            nodes = [self._create_keyword_node_from_text(kw) for kw in keywords]
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"キーワードパース失敗: {e}")
            return result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            keywords = self.parse_keywords(content)
            for keyword in keywords:
                if not self.validate_keyword(keyword):
                    errors.append(f"無効なキーワード: {keyword}")
        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedKeywordParser",
            "version": "2.0.0",
            "supported_formats": ["kumihan", "keyword"],
            "capabilities": ["keyword_extraction", "attribute_parsing"],
            "parser_type": self.parser_type,
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["kumihan", "keyword", "text"]

    def _create_keyword_node_from_text(self, keyword: str) -> Node:
        """テキストからキーワードノードを作成"""
        return create_node("keyword", content=keyword, metadata={"keyword": keyword})

    # 後方互換性エイリアス
    def parse_legacy(self, text: str) -> List[Node]:
        """レガシーparse メソッドのエイリアス"""
        result = self._parse_implementation(text)
        return [result] if isinstance(result, Node) else result
