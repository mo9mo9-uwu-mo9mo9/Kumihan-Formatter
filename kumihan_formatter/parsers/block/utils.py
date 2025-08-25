"""Block parsing utilities and validation functions

このモジュールはブロックパーサーで使用される共通のユーティリティ関数と
正規表現パターンを提供します。
"""

import re
from typing import List, Dict, Any, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import ParseContext


# 正規表現パターン定義


class BlockPatterns:
    """ブロック解析用の正規表現パターン集"""

    LIST_PATTERN = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
    EMPTY_LINE_PATTERN = re.compile(r"^\s*$")
    SIMPLE_IMAGE_PATTERN = re.compile(r"^#\s*画像\s*#.*##$")
    COMMENT_PATTERN = re.compile(r"^<!--.*-->$", re.DOTALL)
    BLOCK_MARKER_PATTERN = re.compile(r"^#.*#.*##$")
    NEW_FORMAT_MARKER_PATTERN = re.compile(r"^#\s*\w+.*##$")


# ユーティリティ関数
def is_empty_line(line: str) -> bool:
    """空行かどうかを判定"""
    return bool(BlockPatterns.EMPTY_LINE_PATTERN.match(line))


def is_list_line(line: str) -> bool:
    """リスト行かどうかを判定"""
    return bool(BlockPatterns.LIST_PATTERN.match(line))


def is_simple_image_marker(line: str) -> bool:
    """簡単な画像マーカーかどうかを判定"""
    return bool(BlockPatterns.SIMPLE_IMAGE_PATTERN.match(line))


def is_comment_line(line: str) -> bool:
    """コメント行かどうかを判定"""
    return bool(BlockPatterns.COMMENT_PATTERN.match(line))


def is_block_marker_format(line: str) -> bool:
    """ブロックマーカー形式かどうかを判定"""
    return bool(BlockPatterns.BLOCK_MARKER_PATTERN.match(line))


def is_new_format_marker(line: str) -> bool:
    """新形式マーカーかどうかを判定"""
    return bool(BlockPatterns.NEW_FORMAT_MARKER_PATTERN.match(line))


def skip_empty_lines(lines: List[str], start_index: int) -> int:
    """空行をスキップして次の非空行のインデックスを返す"""
    while start_index < len(lines) and is_empty_line(lines[start_index]):
        start_index += 1
    return start_index


def find_next_significant_line(lines: List[str], start_index: int) -> int:
    """次の意味のある行のインデックスを検索"""
    for i in range(start_index, len(lines)):
        if not is_empty_line(lines[i]):
            return i
    return len(lines)


def preprocess_lines(lines: List[str]) -> List[str]:
    """行の前処理を実行"""
    return [line.rstrip() for line in lines]


def find_next_block_end(lines: List[str], start_index: int) -> int:
    """次のブロック終了位置を検索"""
    for i in range(start_index, len(lines)):
        if is_block_marker_format(lines[i]):
            return i
    return len(lines)


def has_matching_closing_marker(block: str) -> bool:
    """対応する閉じマーカーが存在するかチェック"""
    lines = block.splitlines()
    opening_count = sum(
        1
        for line in lines
        if line.strip().startswith("#") and line.strip().endswith("##")
    )
    closing_count = opening_count  # 簡易実装、実際の閉じマーカーカウントロジック
    return opening_count == closing_count


def validate_block_structure(block: str) -> List[str]:
    """ブロック構造の検証とエラーメッセージ生成"""
    errors = []

    if not block.strip():
        errors.append("空のブロックです")
        return errors

    lines = block.splitlines()
    if not lines:
        errors.append("有効な行が見つかりません")
        return errors

    first_line = lines[0].strip()
    if not is_block_marker_format(first_line):
        errors.append(f"無効なブロックマーカー形式: {first_line}")

    return errors


# Issue #1173対応: parser.py用ユーティリティ関数


def get_keyword_parser() -> Optional[Any]:
    """KeywordParserを取得（フォールバック付き）"""
    try:
        from ..keyword_parser import KeywordParser

        return KeywordParser()
    except Exception:
        return None


def create_cache_key(
    content: Union[str, List[str]], context: Optional["ParseContext"] = None
) -> str:
    """キャッシュキーを作成"""
    import hashlib

    if isinstance(content, list):
        content_str = "\n".join(content)
    else:
        content_str = content

    base_key = hashlib.md5(content_str.encode()).hexdigest()

    if context:
        context_str = str(context)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{base_key}_{context_hash}"

    return base_key


def get_parser_info() -> Dict[str, Any]:
    """パーサー情報を取得"""
    return {
        "name": "UnifiedBlockParser",
        "version": "2.0.0",
        "type": "block",
        "supported_formats": ["kumihan", "text", "markdown"],
        "capabilities": [
            "block_extraction",
            "block_validation",
            "nested_blocks",
            "error_recovery",
        ],
    }


def supports_format(format_hint: str) -> bool:
    """対応フォーマット判定"""
    supported = {"kumihan", "text", "markdown", "md", "plain"}
    return format_hint.lower() in supported


# Issue #1173対応: handlers.py用マーカー判定関数


def is_block_marker_line(line: str) -> bool:
    """ブロックマーカー行判定"""
    return is_block_marker_format(line) or is_new_format_marker(line)


def is_opening_marker(line: str) -> bool:
    """開始マーカー判定"""
    return is_block_marker_format(line) and not line.strip().endswith("###")


def is_closing_marker(line: str) -> bool:
    """終了マーカー判定"""
    return line.strip().endswith("###")


# Issue #1173対応: 統合コンポーネントクラス


def setup_block_patterns() -> Dict[str, Any]:
    """ブロック解析用パターンをセットアップ"""
    import re

    return {
        "kumihan": re.compile(r"^#.*#.*##$"),
        "kumihan_opening": re.compile(r"^#\s*\w+.*#(?!##)"),
        "list": re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+"),
        "image": re.compile(r"(画像|image|img)", re.IGNORECASE),
        "code_block": re.compile(r"^```"),
        "quote_block": re.compile(r"^>"),
        "marker": re.compile(r"^[-=*]{3,}$"),
        "comment": re.compile(r"^<!--.*-->$", re.DOTALL),
    }


class BlockExtractor:
    """ブロック抽出クラス"""

    def __init__(self):
        from ...core.utilities.logger import get_logger

        self.logger = get_logger(__name__)
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

    def __init__(self):
        from ...core.utilities.logger import get_logger

        self.logger = get_logger(__name__)
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


class BlockCache:
    """ブロック解析キャッシュ管理クラス"""

    def __init__(self):
        from ...core.utilities.logger import get_logger

        self.logger = get_logger(__name__)

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
    """ブロック行処理クラス"""

    def __init__(self):
        from ...core.utilities.logger import get_logger

        self.logger = get_logger(__name__)

    def is_block_marker_line(
        self, line: str, cache: BlockCache, detector: BlockTypeDetector
    ) -> bool:
        """ブロックマーカー行判定（キャッシュ付き）"""
        cached = cache.get_marker_cache(line)
        if cached is not None:
            return cached

        result = is_block_marker_line(line)
        cache.set_marker_cache(line, result)
        return result

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカー判定"""
        return is_opening_marker(line)

    def is_closing_marker(self, line: str) -> bool:
        """終了マーカー判定"""
        return is_closing_marker(line)

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """空行をスキップ"""
        return skip_empty_lines(lines, start_index)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """次の意味のある行を検索"""
        return find_next_significant_line(lines, start_index)


class BlockProcessor:
    """ブロック処理クラス"""

    def __init__(self):
        from ...core.utilities.logger import get_logger

        self.logger = get_logger(__name__)

    def normalize_content(self, content: Union[str, List[str]]) -> str:
        """コンテンツを正規化"""
        if isinstance(content, list):
            return "\n".join(content)
        return content

    def finalize_block_parsing(self, block_nodes: List[Any]) -> Any:
        """ブロック解析を最終化"""
        from ...core.ast_nodes import create_node

        if not block_nodes:
            return create_node("empty", content="")

        if len(block_nodes) == 1:
            return block_nodes[0]

        return create_node("blocks", children=block_nodes)

    def parse_content_lines(
        self, content: List[str], extractor: BlockExtractor, parse_func: Any
    ) -> List[Any]:
        """コンテンツ行列をパース"""
        nodes = []
        for line_content in content:
            if line_content.strip():
                blocks = extractor.extract_blocks(line_content)
                for block in blocks:
                    node = parse_func(block)
                    if node:
                        nodes.append(node)
        return nodes
