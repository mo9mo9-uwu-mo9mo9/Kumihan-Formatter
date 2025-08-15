"""統一キーワードパーサー

Issue #880 Phase 2B: 既存のKeywordParser系統を統合
- core/keyword_parser.py
- core/keyword_parsing/parsers/keyword_parser.py
- core/keyword_parsing/marker_parser.py
の機能を統合・整理
"""

import re
from typing import Any, Dict, List, Optional, Set, Union

from ...ast_nodes import Node, create_node
from ..base import CompositeMixin, UnifiedParserBase
from ..protocols import ParserType


class UnifiedKeywordParser(UnifiedParserBase, CompositeMixin):
    """統一キーワードパーサー

    Kumihan記法のキーワード解析:
    - キーワード定義・検証
    - マーカー解析
    - 属性解析
    - キーワードレジストリ管理
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.KEYWORD)

        # キーワード管理
        self._setup_keyword_registry()
        self._setup_keyword_patterns()
        self._setup_attribute_handlers()

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
