"""Block Parser - 統合ブロック解析エンジン（分割最適化版）

責任分離による構造:
- このファイル: メインクラス・コア解析ロジック・プロトコル準拠
- block_handlers.py: 各種ブロック処理ハンドラー・バリデーター
- block_utils.py: ユーティリティ・抽出・検出・キャッシュ

統合機能:
- 全種類のブロック解析 (Kumihan・テキスト・マーカー・画像・特殊)
- ブロック抽出・検証・変換
- ネストブロック対応・エラー回復
- プロトコル準拠 (BlockParserProtocol)
- 後方互換性維持
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import (
        ParseResult,
        ParseContext,
        BlockParserProtocol,
    )
    from ...core.ast_nodes import Node
else:
    try:
        from ...core.parsing.base.parser_protocols import (
            ParseResult,
            ParseContext,
            BlockParserProtocol,
        )
        from ...core.ast_nodes import Node, create_node
    except ImportError:
        BlockParserProtocol = object
        Node = None
        create_node = None

from ...core.parsing.base import UnifiedParserBase, CompositeMixin
from ...core.parsing.base.parser_protocols import create_parse_result
from ...core.parsing.protocols import ParserType
from ...core.utilities.logger import get_logger

from .block_handlers import BlockHandlerCollection
from .block_utils import (
    BlockExtractor,
    BlockTypeDetector,
    BlockProcessor,
    BlockCache,
    BlockLineProcessor,
    create_cache_key,
    get_parser_info,
    supports_format,
)


class UnifiedBlockParser(UnifiedParserBase, CompositeMixin, BlockParserProtocol):
    """統合ブロックパーサー - 分割最適化版

    分割されたコンポーネントを統合し、既存API完全互換性を維持:
    - BlockHandlerCollection: 各種ブロックハンドラー・バリデーター統合
    - BlockExtractor: ブロック抽出・解析ロジック
    - BlockTypeDetector: ブロックタイプ検出・判定
    - BlockProcessor: ブロック処理・変換・最終化
    - BlockCache: パフォーマンス最適化キャッシュ
    - BlockLineProcessor: 行処理・ヘルパー機能

    機能:
    - Kumihanブロック記法 (# keyword #content##)
    - テキストブロック・段落処理
    - 画像・メディアブロック
    - 特殊・カスタムブロック
    - ネストブロック構造
    - ブロック抽出・変換・検証
    - エラー回復・修正提案
    - プロトコル準拠
    """

    def __init__(self, keyword_parser: Optional[Any] = None) -> None:
        super().__init__(parser_type=ParserType.BLOCK)

        self.logger = get_logger(__name__)

        # KeywordParserの依存関係注入
        self.keyword_parser = keyword_parser or self._get_keyword_parser()

        # 分割されたコンポーネント初期化
        self._setup_modular_components()

        # パーサー参照
        self.parser_ref = None

    def _get_keyword_parser(self) -> Optional[Any]:
        """KeywordParserを取得（フォールバック付き）"""
        try:
            from ..keyword_parser import KeywordParser

            return KeywordParser()
        except Exception as e:
            self.logger.warning(f"KeywordParser取得失敗、None使用: {e}")
            return None

    def _setup_modular_components(self) -> None:
        """分割されたコンポーネントのセットアップ"""
        # ブロックハンドラー集合
        self.handler_collection = BlockHandlerCollection()

        # ブロック処理コンポーネント
        self.block_extractor = BlockExtractor()
        self.block_detector = BlockTypeDetector()
        self.block_processor = BlockProcessor()
        self.block_cache = BlockCache()
        self.line_processor = BlockLineProcessor()

        # 基本設定
        self.heading_counter = 0

        # ハンドラー辞書への参照
        self.block_handlers = self.handler_collection.handlers
        self.validators = self.handler_collection.validator_collection.validators

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> "Node":
        """基底クラス用の解析実装（UnifiedParserBase準拠）"""
        text = self.block_processor.normalize_content(content)

        try:
            # ブロック抽出
            blocks = self.block_extractor.extract_blocks(text)
            if not blocks:
                return create_node("empty", content="")

            # 各ブロック解析
            block_nodes = []
            for block in blocks:
                try:
                    block_node = self._parse_single_block(block)
                    if block_node:
                        block_nodes.append(block_node)
                except Exception as e:
                    self.logger.warning(f"ブロック解析失敗: {e}")
                    error_node = create_node(
                        "error_block", content=block, attributes={"error": str(e)}
                    )
                    block_nodes.append(error_node)

            # 統合ノード作成
            return self.block_processor.finalize_block_parsing(block_nodes)

        except Exception as e:
            self.logger.error(f"Block parsing failed: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def _parse_single_block(self, block: str) -> Optional["Node"]:
        """単一ブロックを解析"""
        block_type = self.block_detector.detect_block_type(block)
        if not block_type:
            return create_node("text", content=block.strip())

        # 対応するハンドラーを実行
        handler = self.handler_collection.get_handler(block_type)
        return handler(block)

    def parse(
        self,
        content: Union[str, List[str]],
        context: Optional["ParseContext"] = None,
        **kwargs: Any,
    ) -> "ParseResult":
        """統一パースメソッド - BlockParserProtocol準拠"""
        try:
            # キャッシュ確認
            cache_key = create_cache_key(content, context)
            cached_result = self.block_cache.get_processed_content_cache(cache_key)
            if cached_result:
                return cached_result

            self._clear_errors_warnings()

            # 基本パース実行
            if isinstance(content, list):
                nodes = self.block_processor.parse_content_lines(
                    content, self.block_extractor, self._parse_single_block
                )
            else:
                nodes = [self._parse_implementation(content)]

            # ParseResult作成
            result = create_parse_result(
                nodes=[n for n in nodes if n is not None],
                success=True,
                errors=self.get_errors(),
                warnings=self.get_warnings(),
                metadata={
                    "parser_type": "block",
                    "block_count": len(nodes) if nodes else 0,
                },
            )

            # キャッシュ保存
            self.block_cache.set_processed_content_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.error(f"Block parsing error: {e}")
            return create_parse_result(
                nodes=[],
                success=False,
                errors=[f"Block parsing failed: {e}"],
                warnings=[],
                metadata={"parser_type": "block"},
            )

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return getattr(self, "_errors", [])

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return getattr(self, "_warnings", [])

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """ブロック構文チェック"""
        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            return errors

        if not content.strip():
            return errors  # 空コンテンツは有効

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
        """パーサー情報（プロトコル準拠）"""
        info = get_parser_info()
        info["parser_type"] = self.parser_type
        return info

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        return supports_format(format_hint)

    # === BlockParserProtocol実装 ===

    def parse_block(
        self, block: str, context: Optional["ParseContext"] = None
    ) -> "Node":
        """単一ブロックをパース（プロトコル準拠）"""
        try:
            return self._parse_single_block(block) or create_node("empty", content="")
        except Exception as e:
            self.logger.error(f"Single block parsing error: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def extract_blocks(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """テキストからブロックを抽出（プロトコル準拠）"""
        return self.block_extractor.extract_blocks(text, context)

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出（プロトコル準拠）"""
        return self.block_detector.detect_block_type(block)

    # === ヘルパーメソッド・後方互換性 ===

    def set_parser_reference(self, parser: Any) -> None:
        """パーサー参照設定"""
        self.parser_ref = parser

    def is_block_marker_line(self, line: str) -> bool:
        """ブロックマーカー行判定"""
        return self.line_processor.is_block_marker_line(
            line, self.block_cache, self.block_detector
        )

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカー判定"""
        return self.line_processor.is_opening_marker(line)

    def is_closing_marker(self, line: str) -> bool:
        """終了マーカー判定"""
        return self.line_processor.is_closing_marker(line)

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """空行をスキップ"""
        return self.line_processor.skip_empty_lines(lines, start_index)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """次の意味のある行を検索"""
        return self.line_processor.find_next_significant_line(lines, start_index)


# 後方互換性のためのエイリアス
BlockParser = UnifiedBlockParser
