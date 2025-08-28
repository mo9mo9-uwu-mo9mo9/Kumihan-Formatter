"""Block Utilities - ブロック解析ユーティリティ群

責任分離による構造:
- ブロック抽出・検出ロジック
- パターンマッチング設定・正規表現管理
- ブロック解析・変換ユーティリティ
- キャッシュ管理・パフォーマンス最適化
- ヘルパーメソッド・補助機能
"""

import re
from typing import Any, Dict, List, Optional, Union, Pattern, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import ParseContext
    from ...core.ast_nodes import Node
else:
    try:
        from ...core.parsing.base.parser_protocols import ParseContext
        from ...core.ast_nodes import Node
    except ImportError:
        ParseContext = object
        Node = None

# create_node関数のインポート
from ...core.ast_nodes.factories import create_node

import logging


def setup_block_patterns() -> Dict[str, re.Pattern]:
    """ブロック解析用パターンのセットアップ"""
    patterns = {
        # Kumihanブロック記法パターン
        "kumihan": re.compile(r"^#\s*([^#]+)\s*#([^#]*)##$"),
        "kumihan_opening": re.compile(r"^#\s*([^#]+)\s*#"),
        # テキストブロックパターン
        "list": re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+"),
        "empty_line": re.compile(r"^\s*$"),
        # 画像ブロックパターン
        "image": re.compile(r"!\[([^\]]*)\]\(([^)]+)\)"),
        # 特殊ブロックパターン
        "code_block": re.compile(r"^```(\w+)?"),
        "quote_block": re.compile(r"^>\s+"),
        # マーカーブロックパターン
        "marker": re.compile(r"^#\s*[^#]+\s*#[^#]*##"),
        # コメントパターン
        "comment": re.compile(r"^\s*#"),
    }

    return patterns


class BlockExtractor:
    """ブロック抽出クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.patterns = setup_block_patterns()

    def extract_blocks(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """テキストからブロックを抽出"""
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

    def _is_kumihan_opening(self, line: str) -> bool:
        """Kumihan開始行かチェック"""
        return bool(self.patterns["kumihan_opening"].match(line))


class BlockTypeDetector:
    """ブロックタイプ検出クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.patterns = setup_block_patterns()

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出"""
        if not block.strip():
            return None

        lines = block.split("\n")
        first_line = lines[0].strip()

        # Kumihanブロック記法
        if self.patterns["kumihan"].match(first_line) or self._is_kumihan_opening(
            first_line
        ):
            return "kumihan"

        # 画像ブロック
        if self.patterns["image"].search(first_line):
            return "image"

        # リストブロック
        if self.patterns["list"].match(first_line):
            return "list"

        # コードブロック
        if self.patterns["code_block"].match(first_line):
            return "special"

        # 引用ブロック
        if self.patterns["quote_block"].match(first_line):
            return "special"

        # マーカーブロック
        if self._is_marker_line(first_line):
            return "marker"

        # デフォルトはテキストブロック
        return "text"

    def _is_kumihan_opening(self, line: str) -> bool:
        """Kumihan開始行かチェック"""
        return bool(self.patterns["kumihan_opening"].match(line))

    def _is_marker_line(self, line: str) -> bool:
        """マーカー行かチェック"""
        return bool(self.patterns["marker"].match(line))


class BlockProcessor:
    """ブロック処理・変換クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化して文字列として返す"""
        if isinstance(content, list):
            return "\n".join(str(line) for line in content)
        return str(content)

    def finalize_block_parsing(self, block_nodes: List["Node"]) -> "Node":
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

    def parse_content_lines(
        self, lines: List[str], extractor: BlockExtractor, parse_single_block_func: Any
    ) -> List["Node"]:
        """行リストから複数ブロックを解析"""
        text = "\n".join(lines)
        blocks = extractor.extract_blocks(text)

        nodes = []
        for block in blocks:
            node = parse_single_block_func(block)
            if node:
                nodes.append(node)

        return nodes


class BlockCache:
    """ブロック解析キャッシュ管理クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # キャッシュとパフォーマンス最適化
        self._block_end_indices: Dict[int, int] = {}
        self._lines_cache: List[str] = []
        self._is_marker_cache: Dict[str, bool] = {}
        self._is_list_cache: Dict[str, bool] = {}
        self._processed_content_cache: Dict[str, Any] = {}

    def get_processed_content_cache(self, cache_key: str) -> Optional[Any]:
        """処理済みコンテンツキャッシュから取得"""
        return self._processed_content_cache.get(cache_key)

    def set_processed_content_cache(self, cache_key: str, result: Any) -> None:
        """処理済みコンテンツキャッシュに保存"""
        self._processed_content_cache[cache_key] = result

    def get_marker_cache(self, line: str) -> Optional[bool]:
        """マーカーキャッシュから取得"""
        return self._is_marker_cache.get(line)

    def set_marker_cache(self, line: str, is_marker: bool) -> None:
        """マーカーキャッシュに保存"""
        self._is_marker_cache[line] = is_marker

    def clear_all_caches(self) -> None:
        """全キャッシュクリア"""
        self._block_end_indices.clear()
        self._lines_cache.clear()
        self._is_marker_cache.clear()
        self._is_list_cache.clear()
        self._processed_content_cache.clear()


class BlockLineProcessor:
    """ブロック行処理ヘルパークラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.patterns = setup_block_patterns()

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
            if line.strip() and not self.patterns["comment"].match(line):
                return i
        return len(lines)

    def is_block_marker_line(
        self, line: str, cache: BlockCache, detector: BlockTypeDetector
    ) -> bool:
        """ブロックマーカー行判定（キャッシュ付き）"""
        cached = cache.get_marker_cache(line)
        if cached is not None:
            return cached

        result = detector._is_marker_line(line.strip())
        cache.set_marker_cache(line, result)
        return result

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカー判定"""
        return bool(self.patterns["kumihan_opening"].match(line.strip()))


def create_cache_key(
    content: Union[str, List[str]], context: Optional["ParseContext"] = None
) -> str:
    """キャッシュキー生成"""
    content_str = str(content) if isinstance(content, str) else str(content)
    context_id = id(context) if context else 0
    return f"{hash(content_str)}_{context_id}"


def get_parser_info() -> Dict[str, Any]:
    """ブロックパーサー情報取得"""
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
        "architecture": "分割最適化型",
    }


def supports_format(format_hint: str) -> bool:
    """対応フォーマット判定"""
    supported = {"kumihan", "block", "markdown", "text"}
    return format_hint.lower() in supported
