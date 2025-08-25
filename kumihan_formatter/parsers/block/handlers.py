"""Block parsing handler functions

このモジュールはブロックの種類別解析処理を提供します。
各ブロックタイプに対応した専用ハンドラーを実装しています。
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from ...core.ast_nodes.node import Node
from ...core.ast_nodes import create_node
from ...core.parsing.base.parser_protocols import (
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ...core.utilities.logger import get_logger

from .utils import (
    BlockPatterns,
    is_block_marker_format,
    is_comment_line,
    is_list_line,
    is_new_format_marker,
    is_simple_image_marker,
    skip_empty_lines,
    validate_block_structure,
)

if TYPE_CHECKING:
    from ..keyword.keyword_parser import KeywordParser


class BlockHandler:
    """ブロック解析処理を統括するハンドラークラス"""

    def __init__(self, keyword_parser: Optional["KeywordParser"] = None):
        """Initialize block handler

        Args:
            keyword_parser: キーワードパーサーインスタンス
        """
        from kumihan_formatter.core.utilities.logger import get_logger

        self.logger = get_logger(__name__)
        self.keyword_parser = keyword_parser

        # キャッシュ
        self._is_marker_cache: Dict[str, bool] = {}
        self._is_list_cache: Dict[str, bool] = {}

    def parse_block_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple[Optional[Node], int]:
        """ブロックマーカーを解析

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス

        Returns:
            Tuple[Optional[Node], int]: 解析されたノードと次のインデックス
        """
        if start_index >= len(lines):
            return None, start_index

        line = lines[start_index]
        if not is_block_marker_format(line):
            return None, start_index + 1

        # マーカーブロックの解析実装
        node = Node(type="block_marker", content=line.strip())
        return node, start_index + 1

    def parse_new_format_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple[Optional[Node], int]:
        """新形式マーカーを解析

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス

        Returns:
            Tuple[Optional[Node], int]: 解析されたノードと次のインデックス
        """
        if start_index >= len(lines):
            return None, start_index

        line = lines[start_index]
        if not is_new_format_marker(line):
            return None, start_index + 1

        node = Node(type="new_format_marker", content=line.strip())
        return node, start_index + 1

    def parse_paragraph(
        self, lines: List[str], start_index: int
    ) -> Tuple[Optional[Node], int]:
        """段落を解析

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス

        Returns:
            Tuple[Optional[Node], int]: 解析されたノードと次のインデックス
        """
        if start_index >= len(lines):
            return None, start_index

        # 空行をスキップ
        start_index = skip_empty_lines(lines, start_index)
        if start_index >= len(lines):
            return None, start_index

        # 段落内容を収集
        paragraph_lines = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index]
            if line.strip() == "":
                break
            paragraph_lines.append(line)
            current_index += 1

        if paragraph_lines:
            content = "\n".join(paragraph_lines)
            node = Node(type="paragraph", content=content)
            return node, current_index

        return None, start_index

    def parse_inline_format(self, line: str) -> Dict[str, Any]:
        """インライン形式の解析

        Args:
            line: 解析対象の行

        Returns:
            Dict[str, Any]: 解析結果の辞書
        """
        keywords = []
        attributes = {}
        content = line
        start_index = 0

        # 簡易実装 - 実際のキーワード解析は keyword_parser に委譲
        if self.keyword_parser:
            try:
                result = self.keyword_parser.parse_line(line)
                if hasattr(result, "keywords"):
                    keywords = result.keywords
                if hasattr(result, "attributes"):
                    attributes = result.attributes
                if hasattr(result, "content"):
                    content = result.content
            except Exception as e:
                self.logger.warning(f"キーワード解析失敗: {e}")

        return {
            "keywords": keywords,
            "attributes": attributes,
            "content": content,
            "start_index": start_index,
        }

    def create_node_for_keyword(self, keyword: str, content: str) -> Node:
        """キーワードに対応するノードを作成

        Args:
            keyword: キーワード名
            content: コンテンツ

        Returns:
            Node: 作成されたノード
        """
        return Node(type=keyword, content=content)

    def apply_attributes_to_node(self, node: Node, attributes: Dict[str, Any]) -> None:
        """ノードに属性を適用

        Args:
            node: 対象ノード
            attributes: 適用する属性
        """
        if attributes:
            node.attributes.update(attributes)

    def parse_new_format_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple[Optional[Node], int]:
        """新形式ブロックの解析

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス
            keywords: キーワードリスト
            attributes: 属性辞書

        Returns:
            Tuple[Optional[Node], int]: 解析されたノードと次のインデックス
        """
        if start_index >= len(lines):
            return None, start_index

        # 新形式ブロックの解析実装
        line = lines[start_index]
        node = Node(type="new_format_block", content=line.strip())
        self.apply_attributes_to_node(node, attributes)

        return node, start_index + 1

    def generate_block_fix_suggestions(
        self, opening_line: str, keywords: List[str]
    ) -> List[str]:
        """ブロック修正提案を生成

        Args:
            opening_line: 開始行
            keywords: キーワードリスト

        Returns:
            List[str]: 修正提案のリスト
        """
        suggestions = []

        if not keywords:
            suggestions.append(
                "キーワードが見つかりません。正しい形式で記述してください。"
            )

        if not opening_line.strip().endswith("##"):
            suggestions.append("ブロックマーカーは ## で終了する必要があります。")

        return suggestions

    def attempt_content_recovery(
        self, lines: List[str], start_index: int
    ) -> Optional[str]:
        """コンテンツ復旧を試行

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス

        Returns:
            Optional[str]: 復旧されたコンテンツ
        """
        if start_index >= len(lines):
            return None

        # 復旧ロジックの実装
        recovery_lines = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index]
            if is_block_marker_format(line):
                break
            recovery_lines.append(line)
            current_index += 1

        return "\n".join(recovery_lines) if recovery_lines else None

    def parse_list_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple[Optional[Node], int]:
        """リストブロックの解析

        Args:
            lines: 解析対象の行リスト
            start_index: 開始インデックス
            keywords: キーワードリスト
            attributes: 属性辞書

        Returns:
            Tuple[Optional[Node], int]: 解析されたノードと次のインデックス
        """
        if start_index >= len(lines):
            return None, start_index

        list_lines = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index]
            if is_list_line(line):
                list_lines.append(line)
                current_index += 1
            else:
                break

        if list_lines:
            content = "\n".join(list_lines)
            node = Node(type="list_block", content=content)
            self.apply_attributes_to_node(node, attributes)
            return node, current_index

        return None, start_index

    def is_marker_cached(
        self, line: str, keyword_parser: Optional["KeywordParser"]
    ) -> bool:
        """キャッシュを使用したマーカー判定

        Args:
            line: 判定対象の行
            keyword_parser: キーワードパーサー

        Returns:
            bool: マーカー行かどうか
        """
        if line in self._is_marker_cache:
            return self._is_marker_cache[line]

        result = is_block_marker_format(line)
        self._is_marker_cache[line] = result
        return result

    def is_list_cached(self, line: str) -> bool:
        """キャッシュを使用したリスト行判定

        Args:
            line: 判定対象の行

        Returns:
            bool: リスト行かどうか
        """
        if line in self._is_list_cache:
            return self._is_list_cache[line]

        result = is_list_line(line)
        self._is_list_cache[line] = result
        return result

    def extract_blocks(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """テキストからブロックを抽出

        Args:
            text: 抽出対象のテキスト
            context: 抽出コンテキスト（オプション）

        Returns:
            List[str]: 抽出されたブロックのリスト
        """
        blocks = []
        lines = text.split("\n")
        current_block: List[str] = []
        in_block = False

        for line in lines:
            if self.is_opening_marker(line):
                # 新しいブロック開始
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
                in_block = True
            elif self.is_closing_marker(line):
                # ブロック終了
                current_block.append(line)
                blocks.append("\n".join(current_block))
                current_block = []
                in_block = False
            elif in_block:
                # ブロック内容
                current_block.append(line)
            else:
                # 通常テキスト
                if line.strip():  # 空行でない場合
                    if current_block:
                        current_block.append(line)
                    else:
                        current_block = [line]
                else:
                    # 空行でブロック区切り
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []

        # 最後のブロック処理
        if current_block:
            blocks.append("\n".join(current_block))

        return [block for block in blocks if block.strip()]

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカーかどうかを判定"""
        return is_block_marker_format(line) and not line.strip().endswith("###")

    def is_closing_marker(self, line: str) -> bool:
        """閉じマーカーかどうかを判定"""
        return line.strip().endswith("###")


class BlockProcessingEngine:
    """ブロック処理エンジン - Issue #1173対応 責任分離版

    処理ロジック・バリデーション・キャッシュ管理（200-300行目標）
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # ハンドラーコレクション
        from .block_handlers import BlockHandlerCollection

        self.handler_collection = BlockHandlerCollection()

        # 処理コンポーネント
        from .utils import BlockExtractor, BlockTypeDetector, BlockCache

        self.block_extractor = BlockExtractor()
        self.block_detector = BlockTypeDetector()
        self.block_cache = BlockCache()

        # エラー・警告管理
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def clear_errors_warnings(self) -> None:
        """エラー・警告をクリア"""
        self._errors.clear()
        self._warnings.clear()

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return self._errors.copy()

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return self._warnings.copy()

    def get_cached_result(self, cache_key: str) -> Optional["ParseResult"]:
        """キャッシュ結果取得"""
        return self.block_cache.get_processed_content_cache(cache_key)

    def set_cached_result(self, cache_key: str, result: "ParseResult") -> None:
        """キャッシュ結果保存"""
        self.block_cache.set_processed_content_cache(cache_key, result)

    def parse_implementation(self, content: str) -> "Node":
        """基底クラス用の解析実装"""
        text = self.normalize_content(content)

        try:
            # ブロック抽出
            blocks = self.block_extractor.extract_blocks(text)
            if not blocks:
                return create_node("empty", content="")

            # 各ブロック解析
            block_nodes = []
            for block in blocks:
                try:
                    block_node = self.parse_single_block(block)
                    if block_node:
                        block_nodes.append(block_node)
                except Exception as e:
                    self._warnings.append(f"ブロック解析失敗: {e}")
                    error_node = create_node(
                        "error_block", content=block, attributes={"error": str(e)}
                    )
                    block_nodes.append(error_node)

            # 統合ノード作成
            return self.finalize_block_parsing(block_nodes)

        except Exception as e:
            self._errors.append(f"Block parsing failed: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def parse_single_block(self, block: str) -> Optional["Node"]:
        """単一ブロックを解析"""
        block_type = self.block_detector.detect_block_type(block)
        if not block_type:
            return create_node("text", content=block.strip())

        # 対応するハンドラーを実行
        handler = self.handler_collection.get_handler(block_type)
        return handler(block)

    def extract_blocks(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """テキストからブロックを抽出"""
        return self.block_extractor.extract_blocks(text, context)

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出"""
        return self.block_detector.detect_block_type(block)

    def normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化"""
        if isinstance(content, list):
            return "\n".join(content)
        return content

    def finalize_block_parsing(self, block_nodes: List["Node"]) -> "Node":
        """ブロック解析を最終化"""
        if not block_nodes:
            return create_node("empty", content="")

        if len(block_nodes) == 1:
            return block_nodes[0]

        return create_node("blocks", children=block_nodes)

    def parse_content_lines(self, content: List[str]) -> List["Node"]:
        """コンテンツ行列のパース"""
        nodes = []
        for line_content in content:
            if line_content.strip():
                node = self.parse_implementation(line_content)
                if node:
                    nodes.append(node)
        return nodes

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """ブロック構文チェック"""
        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            return errors

        if not content.strip():
            return errors

        try:
            # 基本構文検証
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                line_errors = self.handler_collection.validate_line(line, i)
                errors.extend(line_errors)

            # ブロック構造検証
            try:
                blocks = self.block_extractor.extract_blocks(content)
                for j, block in enumerate(blocks, 1):
                    block_errors = self.handler_collection.validate_block(block, j)
                    errors.extend(block_errors)
            except Exception as e:
                errors.append(f"Block structure validation failed: {e}")

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得"""
        from .utils import get_parser_info

        info = get_parser_info()
        info["parser_type"] = "block"
        return info

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        from .utils import supports_format

        return supports_format(format_hint)

    def set_parser_reference(self, parser: Any) -> None:
        """パーサー参照を設定"""
        if hasattr(self.handler_collection, "set_parser_reference"):
            self.handler_collection.set_parser_reference(parser)
