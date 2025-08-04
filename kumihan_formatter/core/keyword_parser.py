"""Keyword parsing utilities for Kumihan-Formatter（分割後統合インポート）

This module handles the parsing and validation of Kumihan syntax keywords,
including compound keywords and error suggestions.

このファイルは技術的負債解消（Issue #476）により分割されました：
- keyword_parsing/definitions.py: キーワード定義
- keyword_parsing/marker_parser.py: マーカー解析
- keyword_parsing/validator.py: キーワード検証
"""

from typing import Any

from .ast_nodes import Node, NodeBuilder, emphasis, error_node, highlight, strong
from .keyword_parsing import KeywordDefinitions, KeywordValidator, MarkerParser


class KeywordParser:
    """
    Kumihan記法キーワードパーサー（記法解析の中核）

    設計ドキュメント:
    - 記法仕様: /SPEC.md (基本記法)
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - NodeBuilder: ASTノード構築
    - Node: 生成するASTノード
    - error_node: エラー時のノード生成
    - Parser: このクラスを使用する上位パーサー

    責務:
    - Kumihan記法キーワードの解析
    - 複合キーワードの分解とネスト構造構築
    - ハイライト色属性など特殊属性の処理
    - 不正キーワードのエラー処理とサジェスト
    """

    # Default block keyword definitions
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

    # Keyword nesting order (outer to inner)
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

    def __init__(self, config: Any = None) -> None:
        """Initialize keyword parser with fixed keywords"""
        # 分割されたコンポーネントを初期化
        self.definitions = KeywordDefinitions(config)
        self.marker_parser = MarkerParser(self.definitions)
        self.validator = KeywordValidator(self.definitions)

        # 後方互換性のため既存プロパティを維持
        self.BLOCK_KEYWORDS = self.definitions.BLOCK_KEYWORDS

        # パフォーマンス改善: 正規表現パターンを事前コンパイル
        import re

        # インライン記法: #keyword content## のパターン（##で終わる）
        self._inline_pattern = re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##")

        # インライン記法キーワードマッピング

        self._inline_keyword_mapping = {
            "太字": strong,
            "イタリック": emphasis,
            "ハイライト": highlight,
            "下線": lambda text: NodeBuilder("u").content(text).build(),
            "コード": lambda text: NodeBuilder("code").content(text).build(),
            "取り消し線": lambda text: NodeBuilder("del").content(text).build(),
            "ルビ": self._create_ruby_node,  # ルビ記法用の特殊処理
        }

    def _normalize_marker_syntax(self, marker_content: str) -> str:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.marker_parser.normalize_marker_syntax(marker_content)

    def parse_marker_keywords(
        self, marker_content: str
    ) -> tuple[list[str], dict[str, Any], list[str]]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.marker_parser.parse_marker_keywords(marker_content)

    def validate_keywords(self, keywords: list[str]) -> tuple[list[str], list[str]]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.validator.validate_keywords(keywords)

    def _get_keyword_suggestions(
        self, invalid_keyword: str, max_suggestions: int = 3
    ) -> list[str]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.validator.get_keyword_suggestions(invalid_keyword, max_suggestions)

    def create_single_block(
        self, keyword: str, content: str, attributes: dict[str, Any]
    ) -> Node:
        """Create a single block node from keyword"""
        if keyword not in self.BLOCK_KEYWORDS:
            return error_node(f"不明なキーワード: {keyword}")

        block_def = self.BLOCK_KEYWORDS[keyword]
        tag = block_def["tag"]

        # Parse content - for single blocks, use content directly if provided
        if content.strip():
            parsed_content = self._parse_block_content(content)
        else:
            parsed_content = [""]

        # Create node with appropriate builder
        builder = NodeBuilder(tag).content(parsed_content)

        # Add class if specified
        if "class" in block_def:
            builder.css_class(block_def["class"])

        # Add summary for details elements
        if "summary" in block_def:
            builder.attribute("summary", block_def["summary"])

        # Handle color attribute for highlight
        if keyword == "ハイライト" and "color" in attributes:
            color = attributes["color"]
            color = self._normalize_color_value(color)
            builder.style(f"background-color:{color}")

        # Add other attributes
        for key, value in attributes.items():
            if key not in ["color"]:  # Skip already handled attributes
                builder.attribute(key, value)

        return builder.build()

    def _normalize_color_value(self, color: str) -> str:
        """色値を正規化（色名を16進数に変換）"""
        # 色名から16進数への変換マッピング
        color_map = {
            # 基本色（ハイライト用淡い色）
            "red": "#ffcccc",
            "green": "#ccffcc",
            "blue": "#ccccff",
            "yellow": "#ffff00",
            "orange": "#ffa500",
            "purple": "#800080",
            "pink": "#ffc0cb",
            "brown": "#a52a2a",
            "black": "#000000",
            "white": "#ffffff",
            "gray": "#808080",
            "grey": "#808080",
            # 追加色
            "navy": "#000080",
            "maroon": "#800000",
            "olive": "#808000",
            "lime": "#00ff00",
            "aqua": "#00ffff",
            "teal": "#008080",
            "silver": "#c0c0c0",
            "fuchsia": "#ff00ff",
            "cyan": "#00ffff",
            "magenta": "#ff00ff",
            # 日本語色名（ハイライト用淡い色）
            "赤": "#ffcccc",
            "緑": "#ccffcc",
            "青": "#ccccff",
            "黄": "#ffff00",
            "オレンジ": "#ffa500",
            "紫": "#800080",
            "ピンク": "#ffc0cb",
            "茶": "#a52a2a",
            "黒": "#000000",
            "白": "#ffffff",
            "灰": "#808080",
        }

        # 既に16進数形式の場合はそのまま返す
        if color.startswith("#"):
            return color

        # 色名の場合は16進数に変換
        color_lower = color.lower()
        if color_lower in color_map:
            return color_map[color_lower]
        elif color in color_map:  # 日本語色名の場合
            return color_map[color]
        else:
            # 不明な色名の場合は#を付けて返す（従来の動作）
            return f"#{color}"

    def create_compound_block(
        self, keywords: list[str], content: str, attributes: dict[str, Any]
    ) -> Node:
        """Create nested block structure from compound keywords"""
        if not keywords:
            return error_node("キーワードが指定されていません")

        # Validate all keywords first
        valid_keywords, error_messages = self.validate_keywords(keywords)
        if error_messages:
            return error_node("; ".join(error_messages))

        # Sort keywords by nesting order
        sorted_keywords = self._sort_keywords_by_nesting_order(valid_keywords)

        # Build nested structure from outer to inner
        root_node = None
        current_node = None

        for i, keyword in enumerate(sorted_keywords):
            block_def = self.BLOCK_KEYWORDS[keyword]
            tag = block_def["tag"]

            # Create builder for this level
            builder = NodeBuilder(tag)

            # Add class if specified
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

    def _parse_block_content(self, content: str) -> list[Any]:
        """Parse block content, handling inline keywords"""
        if not content.strip():
            return [""]

        # Check for inline keywords in content
        processed_content = self._process_inline_keywords(content)

        # 処理結果が配列の場合は、そのまま配列として返す
        if isinstance(processed_content, list):
            return processed_content
        else:
            return [processed_content]

    def _process_inline_keywords(self, content: str, nesting_level: int = 0) -> Any:
        """Process inline keywords within content (# keyword content # format)

        仕様:
        - インライン記法: #keyword content# のパターン
        - 単一行内で完結（複数行は現時点では非対応）
        - 制限付きネスト（1レベルまで）対応
        - 最適化: SIMD・正規表現キャッシュ・並列処理統合

        Args:
            content: 処理対象のコンテンツ
            nesting_level: 現在のネストレベル（0=トップレベル、1=1レベルネスト）
        """

        # 空文字列チェック（高速化）
        if not content or not content.strip():
            return content

        # 最適化: 正規表現キャッシュを活用
        from .utilities.performance_metrics import RegexOptimizer
        regex_optimizer = getattr(self, '_regex_optimizer', None)
        if regex_optimizer is None:
            self._regex_optimizer = RegexOptimizer()
            regex_optimizer = self._regex_optimizer

        # 事前チェック: インライン記法が含まれていない場合は早期リターン
        if not regex_optimizer.optimized_search(r"#\s*([^#]+?)\s*#([^#]+?)##", content):
            return content

        # 最適化: SIMD処理（大容量コンテンツの場合）
        if len(content) > 10000:  # 10KB以上の場合
            simd_optimizer = getattr(self, '_simd_optimizer', None)
            if simd_optimizer is None:
                from .utilities.performance_metrics import SIMDOptimizer
                self._simd_optimizer = SIMDOptimizer()
                simd_optimizer = self._simd_optimizer

            # 大容量テキストをSIMD処理
            if simd_optimizer._numpy_available:
                try:
                    return self._process_inline_keywords_simd(content, nesting_level)
                except Exception as e:
                    # SIMD処理失敗時は通常処理にフォールバック
                    pass

        # Process inline notations
        parts = []
        last_end = 0

        for match in regex_optimizer.get_compiled_pattern(r"#\s*([^#]+?)\s*#([^#]+?)##").finditer(content):
            # Add text before the match
            if match.start() > last_end:
                text_before = content[last_end : match.start()]
                if text_before.strip():
                    parts.append(text_before)

            full_keyword = match.group(1).strip()
            text_content = match.group(2).strip()

            # ネストレベルチェック（最大1レベルまで）
            if nesting_level >= 1:
                # 1レベルを超えるネストは禁止、そのまま返す
                parts.append(match.group(0))
                last_end = match.end()
                continue

            # ルビ記法の特殊処理
            if full_keyword.startswith("ルビ "):
                # ルビ記法の場合は、"ルビ "を除去した残りがコンテンツ
                ruby_content = full_keyword[3:].strip()  # "ルビ "を除去
                if ruby_content:
                    ruby_node = self._create_ruby_node(ruby_content)
                    # ルビ解析が失敗した場合（文字列が返ってきた）は元のマーカー付きテキストを使用
                    if isinstance(ruby_node, str):
                        parts.append(match.group(0))  # 元のマーカー付きテキスト
                    else:
                        parts.append(ruby_node)
                else:
                    parts.append(match.group(0))  # 解析失敗時は元のまま
                last_end = match.end()
                continue

            # 通常のキーワードの場合は、スペースで分割
            keyword_parts = full_keyword.split(" ", 1)
            keyword = keyword_parts[0]
            # text_contentは既にmatch.group(2)から取得済み

            # テキストコンテンツ内でのネストした記法を再帰処理
            if (
                nesting_level == 0
                and text_content
                and regex_optimizer.optimized_search(r"#\s*([^#]+?)\s*#([^#]+?)##", text_content)
            ):
                text_content = self._process_inline_keywords(
                    text_content, nesting_level + 1
                )

            # ノード作成（改善されたキーワードマッピング使用）
            base_keyword = keyword.split(" ")[0]  # 色属性を除いた基本キーワード

            if base_keyword in self._inline_keyword_mapping:
                node = self._create_styled_inline_node(
                    self._inline_keyword_mapping[base_keyword], text_content, keyword
                )
                parts.append(node)
            elif keyword == "見出し3":
                # For h3 in list items, use strong styling instead
                parts.append(NodeBuilder("strong").content(text_content).build())
            else:
                # Unknown keyword - return original text with markers
                parts.append(match.group(0))

            last_end = match.end()

        # Add remaining text after last match
        if last_end < len(content):
            remaining = content[last_end:]
            if remaining.strip():
                parts.append(remaining)

        # Return normalized result - 修正: 配列の場合の適切な処理
        if len(parts) == 0:
            return content  # 何も処理されなかった場合は元のコンテンツを返す
        elif len(parts) == 1:
            return parts[0]  # 単一要素の場合はそのまま返す
        else:
            # 複数要素の場合: 文字列とNodeの混合配列を適切に処理
            # レンダラーが処理できるよう、配列としてそのまま返す
            # ただし、すべてが文字列の場合は結合する
            if all(isinstance(part, str) for part in parts):
                return "".join(parts)
            else:
                return parts

    def _process_inline_keywords_simd(self, content: str, nesting_level: int = 0) -> Any:
        """SIMD最適化版インライン記法処理（大容量テキスト用）"""

        # SIMD最適化バージョン（簡略化実装）
        simd_optimizer = self._simd_optimizer

        # 大容量テキストを効率的に分割
        lines = content.split('\n')

        # 並列処理関数
        def process_line_optimized(line: str) -> str:
            if not line or '#' not in line:
                return line
            return self._process_inline_keywords(line, nesting_level)

        # SIMDベクトル化処理
        processed_lines = simd_optimizer.vectorized_line_processing(
            lines,
            [process_line_optimized]
        )

        return '\n'.join(processed_lines) if isinstance(processed_lines, list) else processed_lines

    def _create_ruby_node(self, content: str) -> Any:
        """
        ルビ記法専用のノード作成メソッド

        Args:
            content: ルビのコンテンツ（例: "海砂利水魚(かいじゃりすいぎょ)"）

        Returns:
            Node: rubyノード
        """

        # MarkerParserのルビ解析機能を使用
        ruby_info = self.marker_parser._parse_ruby_content(content)

        if ruby_info and "ruby_base" in ruby_info and "ruby_text" in ruby_info:
            # ルビノードを作成（attributeメソッドを使用）
            return (
                NodeBuilder("ruby")
                .attribute("ruby_base", ruby_info["ruby_base"])
                .attribute("ruby_text", ruby_info["ruby_text"])
                .build()
            )
        else:
            # 解析失敗時は元のコンテンツを返す
            return content

    def _sort_keywords_by_nesting_order(self, keywords: list[str]) -> list[str]:
        """Sort keywords by their nesting order (outer to inner)"""
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
            return len(self.NESTING_ORDER)  # Unknown tags go last

        return sorted(keywords, key=get_nesting_index)

    def _create_styled_inline_node(
        self, node_factory, text_content: str, keyword: str
    ) -> Any:
        """色属性付きインライン記法ノード作成のヘルパーメソッド

        Args:
            node_factory: ノード生成関数（strong, emphasis等）
            text_content: ノードの内容
            keyword: キーワード（色属性含む可能性）

        Returns:
            Node: 作成されたノード（色属性適用済み）
        """
        node = node_factory(text_content)

        # 色属性の処理
        if " color=" in keyword:
            color_part = keyword.split(" color=")[1]
            color_value = self._normalize_color_value(color_part)

            # ハイライトは背景色、それ以外は文字色
            if keyword.startswith("ハイライト"):
                if hasattr(node, "attributes"):
                    node.attributes["style"] = f"background-color: {color_value}"
            else:
                if hasattr(node, "attributes"):
                    node.attributes["style"] = f"color: {color_value}"

        return node
