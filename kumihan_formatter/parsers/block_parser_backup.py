"""統合ブロックパーサー - Issue #1156 分割最適化版

Issue #914: Parser系統合リファクタリング
Issue #1156: ブロックパーサー統合 (7個→1個)

統合対象コンポーネント:
- BaseBlockParser: 基本ブロック処理・マーカー検出
- SpecialBlockParser: 特殊ブロック処理
- ImageBlockParser: 画像ブロック処理
- ContentParser: コンテンツ処理
- MarkerBlockParser: マーカーブロック処理
- TextBlockParser: テキストブロック処理
- BlockValidator: ブロック検証

統合機能:
- 全種類のブロック解析 (Kumihan・テキスト・マーカー・画像・特殊)
- ブロック抽出・検証・変換
- ネストブロック対応・エラー回復
- プロトコル準拠 (BlockParserProtocol)
- 後方互換性維持
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

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
    from ..core.parsing.base.parser_protocols import BlockParserProtocol


class UnifiedBlockParser(UnifiedParserBase, CompositeMixin):
    """統合ブロックパーサー - Issue #1156 分割最適化版

    分割されたコンポーネントを統合し、既存API完全互換性を維持:
    - BaseBlockParser: 基本ブロック処理・マーカー検出・キャッシュ
    - SpecialBlockParser: 特殊ブロック・カスタムブロック処理
    - ImageBlockParser: 画像ブロック・メディア処理
    - ContentParser: コンテンツ処理・パース結果生成
    - MarkerBlockParser: マーカーブロック・Kumihan記法処理
    - TextBlockParser: テキストブロック・段落処理
    - BlockValidator: ブロック検証・エラー検出

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

        # 統合コンポーネント初期化
        self._setup_integrated_components()

        # キャッシュとパフォーマンス最適化
        self._block_end_indices: Dict[int, int] = {}
        self._lines_cache: List[str] = []
        self._is_marker_cache: Dict[str, bool] = {}
        self._is_list_cache: Dict[str, bool] = {}
        self._processed_content_cache: Dict[str, ParseResult] = {}

        # パターンマッチング
        self._setup_patterns()

        # パーサー参照
        self.parser_ref = None

    def _get_keyword_parser(self) -> Optional[Any]:
        """KeywordParserを取得（フォールバック付き）"""
        try:
            from ..parsers.keyword_parser import KeywordParser

            return KeywordParser()
        except Exception as e:
            self.logger.warning(f"KeywordParser取得失敗、None使用: {e}")
            return None

    def _setup_integrated_components(self) -> None:
        """統合コンポーネントのセットアップ"""
        # 基本設定
        self.heading_counter = 0

        # ブロック処理ハンドラー辞書
        self.block_handlers = {
            "kumihan": self._handle_kumihan_block,
            "text": self._handle_text_block,
            "image": self._handle_image_block,
            "special": self._handle_special_block,
            "marker": self._handle_marker_block,
            "content": self._handle_content_block,
            "list": self._handle_list_block,
        }

        # 検証機能
        self.validators = {
            "syntax": self._validate_block_syntax,
            "structure": self._validate_block_structure,
            "content": self._validate_block_content,
        }

    def _setup_patterns(self) -> None:
        """パターンマッチング設定"""
        # Kumihanブロック記法パターン
        self.kumihan_pattern = re.compile(r"^#\s*([^#]+)\s*#([^#]*)##$")
        self.kumihan_opening_pattern = re.compile(r"^#\s*([^#]+)\s*#")

        # テキストブロックパターン
        self.list_pattern = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
        self.empty_line_pattern = re.compile(r"^\s*$")

        # 画像ブロックパターン
        self.image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

        # 特殊ブロックパターン
        self.code_block_pattern = re.compile(r"^```(\w+)?")
        self.quote_block_pattern = re.compile(r"^>\s+")

        # マーカーブロックパターン
        self.marker_pattern = re.compile(r"^#\s*[^#]+\s*#[^#]*##")

        # コメントパターン
        self.comment_pattern = re.compile(r"^\s*#")

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """基底クラス用の解析実装（UnifiedParserBase準拠）"""
        text = self._normalize_content(content)

        try:
            # ブロック抽出
            blocks = self.extract_blocks(text)
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
            return self._finalize_block_parsing(block_nodes)

        except Exception as e:
            self.logger.error(f"Block parsing failed: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def _normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化して文字列として返す"""
        if isinstance(content, list):
            return "\n".join(str(line) for line in content)
        return str(content)

    def _parse_single_block(self, block: str) -> Optional[Node]:
        """単一ブロックを解析"""
        block_type = self.detect_block_type(block)
        if not block_type:
            return create_node("text", content=block.strip())

        # 対応するハンドラーを実行
        handler = self.block_handlers.get(block_type, self._handle_text_block)
        return handler(block)

    def _finalize_block_parsing(self, block_nodes: List[Node]) -> Node:
        """ブロック解析の最終処理"""
        if len(block_nodes) == 1:
            return block_nodes[0]

        # 複数ブロックをコンテナノードで包む
        return create_node(
            "block_container",
            content="",
            attributes={"block_count": len(block_nodes)},
            children=block_nodes,
        )

    def parse(
        self,
        content: Union[str, List[str]],
        context: Optional[ParseContext] = None,
        **kwargs: Any,
    ) -> ParseResult:
        """統一パースメソッド - BlockParserProtocol準拠"""
        try:
            # キャッシュ確認
            cache_key = f"{hash(str(content))}_{id(context) if context else 0}"
            if cache_key in self._processed_content_cache:
                return self._processed_content_cache[cache_key]

            self._clear_errors_warnings()

            # 基本パース実行
            if isinstance(content, list):
                combined_content = "\n".join(content)
                nodes = self._parse_content_lines(content)
            else:
                combined_content = content
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
            self._processed_content_cache[cache_key] = result
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

    def _parse_content_lines(self, lines: List[str]) -> List[Node]:
        """行リストから複数ブロックを解析"""
        text = "\n".join(lines)
        blocks = self.extract_blocks(text)

        nodes = []
        for block in blocks:
            node = self._parse_single_block(block)
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
                line_errors = self._validate_line(line, i)
                errors.extend(line_errors)

            # ブロック構造検証
            try:
                blocks = self.extract_blocks(content)
                for j, block in enumerate(blocks, 1):
                    block_errors = self._validate_block(block, j)
                    errors.extend(block_errors)
            except Exception as e:
                errors.append(f"Block structure validation failed: {e}")

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        return errors

    def _validate_line(self, line: str, line_number: int) -> List[str]:
        """行レベルの検証"""
        errors = []

        # Kumihanブロック記法の検証
        if line.strip().startswith("#") and "##" in line:
            if not self._validate_kumihan_syntax(line):
                errors.append(f"Line {line_number}: Invalid Kumihan block syntax")

        return errors

    def _validate_block(self, block: str, block_number: int) -> List[str]:
        """ブロックレベルの検証"""
        errors = []

        # ブロック構造検証を各バリデーターで実行
        for validator_name, validator in self.validators.items():
            try:
                validator_errors = validator(block)
                for error in validator_errors:
                    errors.append(f"Block {block_number} ({validator_name}): {error}")
            except Exception as e:
                errors.append(
                    f"Block {block_number} validation error ({validator_name}): {e}"
                )

        return errors

    def _validate_kumihan_syntax(self, line: str) -> bool:
        """Kumihan記法の構文チェック"""
        return bool(self.kumihan_pattern.match(line.strip()))

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedBlockParser",
            "version": "3.0.0",
            "supported_formats": ["kumihan", "block", "markdown", "text"],
            "capabilities": [
                "kumihan_block_parsing",
                "text_block_parsing",
                "image_block_parsing",
                "special_block_parsing",
                "marker_block_parsing",
                "content_block_parsing",
                "list_block_parsing",
                "nested_block_support",
                "block_extraction",
                "block_validation",
                "error_recovery",
                "syntax_checking",
            ],
            "parser_type": self.parser_type,
            "architecture": "統合分割型",
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = {"kumihan", "block", "markdown", "text"}
        return format_hint.lower() in supported

    # === BlockParserProtocol実装 ===

    def parse_block(self, block: str, context: Optional[ParseContext] = None) -> Node:
        """単一ブロックをパース（プロトコル準拠）"""
        try:
            return self._parse_single_block(block) or create_node("empty", content="")
        except Exception as e:
            self.logger.error(f"Single block parsing error: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def extract_blocks(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """テキストからブロックを抽出（プロトコル準拠）"""
        if not text.strip():
            return []

        blocks = []
        lines = text.split("\n")
        current_block: List[str] = []
        in_kumihan_block = False

        for line in lines:
            stripped = line.strip()

            # Kumihanブロック記法の処理
            if self._is_kumihan_opening(stripped):
                # 新しいKumihanブロック開始
                if current_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
                current_block.append(line)
                in_kumihan_block = not stripped.endswith("##")
            elif in_kumihan_block:
                # Kumihanブロック内容
                current_block.append(line)
                if stripped.endswith("##"):
                    in_kumihan_block = False
                    blocks.append("\n".join(current_block))
                    current_block = []
            elif stripped == "" and current_block:
                # 空行でブロック区切り
                blocks.append("\n".join(current_block))
                current_block = []
            elif stripped:
                # 通常行
                current_block.append(line)

        # 最後のブロック処理
        if current_block:
            blocks.append("\n".join(current_block))

        return [block.strip() for block in blocks if block.strip()]

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出（プロトコル準拠）"""
        if not block.strip():
            return None

        lines = block.split("\n")
        first_line = lines[0].strip()

        # Kumihanブロック記法
        if self.kumihan_pattern.match(first_line) or self._is_kumihan_opening(
            first_line
        ):
            return "kumihan"

        # 画像ブロック
        if self.image_pattern.search(first_line):
            return "image"

        # リストブロック
        if self.list_pattern.match(first_line):
            return "list"

        # コードブロック
        if self.code_block_pattern.match(first_line):
            return "special"

        # 引用ブロック
        if self.quote_block_pattern.match(first_line):
            return "special"

        # マーカーブロック
        if self._is_marker_line(first_line):
            return "marker"

        # デフォルトはテキストブロック
        return "text"

    # === ブロックハンドラー ===

    def _handle_kumihan_block(self, block: str) -> Node:
        """Kumihanブロック処理"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # 単行形式: # keyword #content##
        match = self.kumihan_pattern.match(first_line)
        if match:
            keyword, content = match.groups()
            return create_node(
                "kumihan_block",
                content=content.strip(),
                attributes={"keyword": keyword.strip(), "format": "inline"},
            )

        # 複数行形式: # keyword # ... ##
        match = self.kumihan_opening_pattern.match(first_line)
        if match:
            keyword = match.group(1).strip()
            content_lines = []

            for line in lines[1:]:
                if line.strip() == "##":
                    break
                content_lines.append(line)

            return create_node(
                "kumihan_block",
                content="\n".join(content_lines).strip(),
                attributes={"keyword": keyword, "format": "multiline"},
            )

        # フォールバック
        return create_node("text", content=block)

    def _handle_text_block(self, block: str) -> Node:
        """テキストブロック処理"""
        return create_node(
            "text_block", content=block.strip(), attributes={"type": "paragraph"}
        )

    def _handle_image_block(self, block: str) -> Node:
        """画像ブロック処理"""
        match = self.image_pattern.search(block)
        if match:
            alt_text, url = match.groups()
            return create_node(
                "image_block",
                content=url,
                attributes={"alt_text": alt_text, "type": "image"},
            )

        return create_node("text", content=block)

    def _handle_special_block(self, block: str) -> Node:
        """特殊ブロック処理"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # コードブロック
        code_match = self.code_block_pattern.match(first_line)
        if code_match:
            language = code_match.group(1) or "text"
            content = "\n".join(lines[1:]).rstrip().rstrip("```")
            return create_node(
                "code_block", content=content, attributes={"language": language}
            )

        # 引用ブロック
        if self.quote_block_pattern.match(first_line):
            content = "\n".join(line.lstrip("> ") for line in lines)
            return create_node(
                "quote_block",
                content=content.strip(),
                attributes={"type": "blockquote"},
            )

        # その他の特殊ブロック
        return create_node(
            "special_block", content=block.strip(), attributes={"type": "unknown"}
        )

    def _handle_marker_block(self, block: str) -> Node:
        """マーカーブロック処理"""
        return create_node(
            "marker_block", content=block.strip(), attributes={"type": "marker"}
        )

    def _handle_content_block(self, block: str) -> Node:
        """コンテンツブロック処理"""
        return create_node(
            "content_block", content=block.strip(), attributes={"type": "generic"}
        )

    def _handle_list_block(self, block: str) -> Node:
        """リストブロック処理"""
        return create_node(
            "list_block", content=block.strip(), attributes={"type": "list"}
        )

    # === バリデーター ===

    def _validate_block_syntax(self, block: str) -> List[str]:
        """ブロック構文検証"""
        errors = []

        block_type = self.detect_block_type(block)
        if block_type == "kumihan":
            if not self._validate_kumihan_block_syntax(block):
                errors.append("Invalid Kumihan block syntax")

        return errors

    def _validate_block_structure(self, block: str) -> List[str]:
        """ブロック構造検証"""
        errors = []

        lines = block.split("\n")
        if not lines:
            errors.append("Empty block")

        return errors

    def _validate_block_content(self, block: str) -> List[str]:
        """ブロックコンテンツ検証"""
        errors = []

        if len(block.strip()) == 0:
            errors.append("Empty content")

        return errors

    def _validate_kumihan_block_syntax(self, block: str) -> bool:
        """Kumihanブロック構文の詳細検証"""
        lines = block.split("\n")
        first_line = lines[0].strip()

        # 単行形式チェック
        if self.kumihan_pattern.match(first_line):
            return True

        # 複数行形式チェック
        if self.kumihan_opening_pattern.match(first_line):
            # 終了マーカー確認
            for line in lines[1:]:
                if line.strip() == "##":
                    return True

        return False

    # === ヘルパーメソッド ===

    def _is_kumihan_opening(self, line: str) -> bool:
        """Kumihan開始行かチェック"""
        return bool(self.kumihan_opening_pattern.match(line))

    def _is_marker_line(self, line: str) -> bool:
        """マーカー行かチェック"""
        return bool(self.marker_pattern.match(line))

    def set_parser_reference(self, parser: Any) -> None:
        """パーサー参照設定"""
        self.parser_ref = parser

    def is_block_marker_line(self, line: str) -> bool:
        """ブロックマーカー行判定"""
        if line in self._is_marker_cache:
            return self._is_marker_cache[line]

        result = self._is_marker_line(line.strip())
        self._is_marker_cache[line] = result
        return result

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカー判定"""
        return self._is_kumihan_opening(line.strip())

    def is_closing_marker(self, line: str) -> bool:
        """終了マーカー判定"""
        return line.strip() == "##"

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """空行をスキップ"""
        for i in range(start_index, len(lines)):
            if lines[i].strip():
                return i
        return len(lines)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """次の意味のある行を検索"""
        for i in range(start_index, len(lines)):
            line = lines[i]
            if line.strip() and not self.comment_pattern.match(line):
                return i
        return len(lines)


# 後方互換性エイリアス
BlockParser = UnifiedBlockParser
