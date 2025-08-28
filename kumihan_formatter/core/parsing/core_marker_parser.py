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
    from ..base.parser_protocols import KeywordParserProtocol
    from ..keyword.attribute_parser import AttributeParser
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
        from ..processors.new_format_processor import NewFormatProcessor
        from ..processors.ruby_format_processor import RubyFormatProcessor
        from ..processors.inline_marker_processor import InlineMarkerProcessor

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
