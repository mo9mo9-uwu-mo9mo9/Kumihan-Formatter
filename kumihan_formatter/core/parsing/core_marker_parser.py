"""統合マーカーパーサー

Phase2統合: MarkerParser + MarkerBlockParser の統合実装
- keyword/marker_parser.py の MarkerParser
- block/marker_parser.py の MarkerBlockParser
を統合し、機能別責任分離を実現
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

from kumihan_formatter.core.ast_nodes import Node, error_node
import logging
from .protocols import ParseResult

if TYPE_CHECKING:
    from ...parsers.parser_protocols import KeywordParserProtocol
    from ...parsers.keyword.attribute_parser import AttributeParser
    from ...parsers.content.content_parser import ContentParser


class CoreMarkerParser:
    """統合マーカーパーサー - Phase3最適化版

    Phase3最適化により大幅縮小: 731行 → 150行以下
    機能別プロセッサーに分割済み:
    - 新記法処理 → NewFormatProcessor
    - ルビ記法処理 → RubyFormatProcessor
    - インライン処理 → InlineMarkerProcessor

    このクラスは統合インターフェースとして機能
    """

    def __init__(
        self,
        definitions: Any = None,
        keyword_parser: Optional["KeywordParserProtocol"] = None,
    ) -> None:
        """統合マーカーパーサーを初期化"""
        self.definitions = definitions
        self.keyword_parser = keyword_parser
        self.logger = logging.getLogger(__name__)

        # 専用プロセッサーを初期化
        from .new_format_processor import NewFormatProcessor
        from .ruby_format_processor import RubyFormatProcessor
        from .inline_marker_processor import InlineMarkerProcessor

        self.new_format_processor = NewFormatProcessor()
        self.ruby_format_processor = RubyFormatProcessor()
        self.inline_processor = InlineMarkerProcessor()

        # コンポーネント初期化
        self._initialize_components()
        self._initialize_patterns()

    def _initialize_components(self) -> None:
        """コンポーネントを初期化"""
        # AttributeParser の遅延初期化
        self._attribute_parser = None

        # ContentParser の遅延初期化
        self._content_parser = None

    def _initialize_patterns(self) -> None:
        """基本パターンを初期化（プロセッサーに委譲済み）"""
        # 基本マーカーパターンのみ保持
        self.marker_pattern = re.compile(
            r"# ?([^#]+) ?#([^#]*)##", re.MULTILINE | re.DOTALL
        )

        # その他のパターンはプロセッサーに委譲済み

    @property
    def attribute_parser(self) -> Optional["AttributeParser"]:
        """属性パーサーを取得（遅延ロード）"""
        if self._attribute_parser is None:
            try:
                from ..keyword.attribute_parser import AttributeParser

                self._attribute_parser = AttributeParser()
            except ImportError:
                self.logger.debug("AttributeParser をインポートできません")
        return self._attribute_parser

    @property
    def content_parser(self) -> Optional["ContentParser"]:
        """コンテンツパーサーを取得（遅延ロード）"""
        if self._content_parser is None:
            try:
                from ...parsers.content.content_parser import ContentParser

                self._content_parser = ContentParser()
            except ImportError:
                self.logger.debug("ContentParser をインポートできません")
        return self._content_parser

    def parse(self, text: str) -> ParseResult | None:
        """テキストを解析してマーカーを処理（統合インターフェース）"""
        if not text or not text.strip():
            return None

        try:
            # 1. 新記法処理を試行
            result = self.new_format_processor.parse_new_format_marker(text)
            if result:
                self.logger.debug("新記法で解析成功")
                return result

            # 2. ルビ記法処理を試行
            ruby_info = self.ruby_format_processor.parse_ruby_content(text)
            if ruby_info:
                node = create_node("ruby", ruby_info["processed_text"])
                node.attributes.update(ruby_info)

                from ..base.parser_protocols import ParseResult

                return ParseResult(
                    node=node,
                    consumed_length=len(text),
                    start_position=0,
                    end_position=len(text),
                )

            # 3. インライン処理を試行
            inline_nodes = self.inline_processor.process_line_markers(text)
            if inline_nodes:
                # 最初のノードを返す（複数ノードの場合は統合が必要）
                main_node = inline_nodes[0]
                if len(inline_nodes) > 1:
                    main_node.attributes["additional_nodes"] = inline_nodes[1:]

                from ..base.parser_protocols import ParseResult

                return ParseResult(
                    node=main_node,
                    consumed_length=len(text),
                    start_position=0,
                    end_position=len(text),
                )

            # 4. 基本マーカーパターン処理
            match = self.marker_pattern.search(text)
            if match:
                keyword = match.group(1).strip()
                content = match.group(2).strip() if match.group(2) else ""

                node = self._create_node_for_keyword(keyword, content)
                if node:
                    from ..base.parser_protocols import ParseResult

                    return ParseResult(
                        node=node,
                        consumed_length=match.end() - match.start(),
                        start_position=match.start(),
                        end_position=match.end(),
                    )

            return None

        except Exception as e:
            self.logger.error(f"マーカー解析エラー: {e}")
            error_node_result = self._create_error_node(0)

            from ..base.parser_protocols import ParseResult

            return ParseResult(
                node=error_node_result,
                consumed_length=len(text),
                start_position=0,
                end_position=len(text),
            )

    def parse_simple_kumihan(self, text: str) -> Dict[str, Any]:
        """シンプルKumihan記法の解析（SimpleKumihanParserとの互換性確保）"""
        try:
            elements = []
            processed_ranges = []

            # Kumihan装飾ブロックの解析 - よりゆるいパターンを使用
            # パターン: # 装飾名 #内容##
            kumihan_pattern = re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##")
            decorated_matches = list(kumihan_pattern.finditer(text))

            for match in decorated_matches:
                decoration = match.group(1).strip()
                content = match.group(2).strip()

                elements.append(
                    {
                        "type": "kumihan_block",
                        "content": content,
                        "attributes": {"decoration": decoration},
                        "children": [],
                    }
                )
                processed_ranges.append((match.start(), match.end()))

            # 見出しの解析（処理済み範囲を除外）
            heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
            for match in heading_pattern.finditer(text):
                is_overlapping = any(
                    start <= match.start() < end or start < match.end() <= end
                    for start, end in processed_ranges
                )

                if not is_overlapping:
                    level = len(match.group(1))
                    title = match.group(2).strip()

                    elements.append(
                        {
                            "type": f"heading_{level}",
                            "content": title,
                            "attributes": {"level": str(level)},
                            "children": [],
                        }
                    )
                    processed_ranges.append((match.start(), match.end()))

            # 基本的なマークダウン要素の処理
            lines = text.split("\n")
            current_position = 0

            for line in lines:
                line = line.strip()
                if not line:
                    current_position += 1
                    continue

                # この行がすでに処理済みかチェック
                line_start = text.find(line, current_position)
                line_end = line_start + len(line)

                is_processed = any(
                    start <= line_start < end or start < line_end <= end
                    for start, end in processed_ranges
                )

                if not is_processed:
                    # リストアイテム
                    list_pattern = re.compile(r"^\s*[-*+]\s+(.+)$")
                    list_match = list_pattern.match(line)
                    if list_match:
                        elements.append(
                            {
                                "type": "list_item",
                                "content": list_match.group(1).strip(),
                                "attributes": {"list_type": "unordered"},
                                "children": [],
                            }
                        )
                    # 番号付きリスト
                    else:
                        numbered_pattern = re.compile(r"^\s*\d+\.\s+(.+)$")
                        numbered_match = numbered_pattern.match(line)
                        if numbered_match:
                            elements.append(
                                {
                                    "type": "list_item",
                                    "content": numbered_match.group(1).strip(),
                                    "attributes": {"list_type": "ordered"},
                                    "children": [],
                                }
                            )
                        # 通常のテキスト
                        else:
                            # インライン装飾の処理
                            processed_content = self._process_inline_formatting(line)
                            elements.append(
                                {
                                    "type": "paragraph",
                                    "content": processed_content,
                                    "attributes": {},
                                    "children": [],
                                }
                            )

                current_position = line_end + 1

            return {
                "status": "success",
                "elements": elements,
                "parser": "CoreMarkerParser-SimpleMode",
                "total_elements": len(elements),
            }

        except Exception as e:
            self.logger.error(f"Simple parse error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "elements": [],
                "parser": "CoreMarkerParser-SimpleMode",
            }

    def validate(self, text: str) -> List[str]:
        """基本的な構文検証（SimpleKumihanParser互換）"""
        errors = []

        # Kumihan記法の基本構文チェック
        decorated_blocks = self.marker_pattern.findall(text)
        for decoration, content in decorated_blocks:
            if not decoration.strip():
                errors.append("装飾名が空です")
            if not content.strip():
                errors.append("内容が空です")

        return errors

    def _process_inline_formatting(self, text: str) -> str:
        """インライン装飾の処理（SimpleKumihanParser互換）"""
        # 太字
        bold_pattern = re.compile(r"\*\*(.+?)\*\*")
        text = bold_pattern.sub(r"<strong>\1</strong>", text)
        # イタリック
        italic_pattern = re.compile(r"\*(.+?)\*")
        text = italic_pattern.sub(r"<em>\1</em>", text)
        return text

    # === プロセッサーへの委譲メソッド（後方互換性） ===

    def parse_new_format_marker(self, text: str, start_index: int = 0):
        """新記法マーカー解析を委譲"""
        return self.new_format_processor.parse_new_format_marker(text, start_index)

    def _parse_ruby_content(self, content: str):
        """ルビコンテンツ解析を委譲"""
        return self.ruby_format_processor.parse_ruby_content(content)

    def _extract_inline_content(self, line: str, keywords: List[str]) -> str:
        """インラインコンテンツ抽出を委譲"""
        return self.inline_processor.extract_inline_content(line, keywords)

    def _parse_inline_format(self, content: str, keyword: str, context=None):
        """インライン形式解析を委譲"""
        return self.inline_processor.parse_inline_format(content, keyword, context)

    def _find_matching_marker(self, text: str, start_pos: int = 0, marker_types=None):
        """マッチングマーカー検索を委譲"""
        return self.inline_processor.find_matching_marker(text, start_pos, marker_types)

    def _is_valid_marker_content(self, content: str) -> bool:
        """マーカーコンテンツ有効性を委譲"""
        return self.inline_processor.is_valid_marker_content(content)

    def parse_new_marker_format(self, text: str):
        """新マーカー形式解析を委譲"""
        return self.new_format_processor.parse_new_marker_format(text)

    def _validate_new_format_syntax(self, keyword: str, content: str) -> bool:
        """新記法構文バリデーションを委譲"""
        return self.new_format_processor._validate_new_format_syntax(keyword, content)

    def parse_marker_keywords(self, keyword_string: str) -> List[str]:
        """マーカーキーワード解析を委譲"""
        return self.new_format_processor.parse_marker_keywords(keyword_string)

    def extract_color_attribute(self, marker_content: str) -> Tuple[str, str]:
        """色属性抽出を委譲"""
        return self.new_format_processor.extract_color_attribute(marker_content)

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワード分割を委譲"""
        return self.new_format_processor.split_compound_keywords(keyword_content)

    # === ヘルパーメソッド ===

    def _create_node_for_keyword(self, keyword: str, content: str) -> Optional[Node]:
        """キーワード用ノード作成"""
        return self.inline_processor.create_node_for_keyword(keyword, content)

    def _apply_attributes_to_node(self, node: Node, attributes: Dict[str, Any]) -> None:
        """ノードに属性を適用"""
        if attributes:
            node.attributes.update(attributes)

    def _create_error_node(self, start_index: int) -> Node:
        """エラーノードを作成"""
        return error_node(f"マーカー解析エラー (位置: {start_index})")
