"""Block parsing core utilities and patterns

このモジュールはブロックパーサーで使用される基本パターンとコア機能を提供します。
"""

import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.parsing.protocols import (
        ParseResult,
    )  # ParseContextが見つからないため一時的にParseResultを使用


class BlockPatterns:
    """ブロック解析用の正規表現パターン集"""

    LIST_PATTERN = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
    EMPTY_LINE_PATTERN = re.compile(r"^\s*$")
    SIMPLE_IMAGE_PATTERN = re.compile(r"^#\s*画像\s*#.*##$")
    COMMENT_PATTERN = re.compile(r"^<!--.*-->$", re.DOTALL)
    BLOCK_MARKER_PATTERN = re.compile(r"^#.*#.*##$")
    NEW_FORMAT_MARKER_PATTERN = re.compile(r"^#\s*\w+.*##$")


class BlockExtractor:
    """ブロック抽出の基本機能"""

    def __init__(self) -> None:
        self.patterns = BlockPatterns()

    def extract_block_content(
        self, lines: List[str], start_index: int
    ) -> Dict[str, Any]:
        """ブロック内容を抽出"""
        # 基本実装は元ファイルから移動
        return {"content": "", "end_index": start_index + 1}


class BlockTypeDetector:
    """ブロックタイプ検出機能"""

    def __init__(self) -> None:
        self.patterns = BlockPatterns()

    def detect_block_type(self, line: str) -> str:
        """ブロックタイプを検出"""
        # 基本実装は元ファイルから移動
        return "unknown"


class BlockCache:
    """ブロック処理キャッシュ管理"""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """キャッシュから取得"""
        return self._cache.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """キャッシュに設定"""
        self._cache[key] = value

    def clear(self) -> None:
        """キャッシュクリア"""
        self._cache.clear()


def setup_block_patterns() -> BlockPatterns:
    """ブロックパターンを初期化"""
    return BlockPatterns()


def setup_keyword_patterns() -> Dict[str, Any]:
    """キーワード抽出用のパターンを初期化"""

    return {
        "kumihan": re.compile(r"^#\s*([^#]*)\s*#\s*(.*?)\s*##$"),
        "kumihan_opening": re.compile(r"^#\s*([^#]*)\s*#\s*$"),
        "keyword": re.compile(r"(\w+)"),
    }


def create_cache_key(content: str, parser_type: str) -> str:
    """キャッシュキーを作成"""
    import hashlib

    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{parser_type}:{content_hash}"


def get_parser_info(parser_type: str) -> Dict[str, Any]:
    """パーサー情報を取得"""
    parser_info = {
        "block": {"description": "Block parser", "version": "1.0"},
        "content": {"description": "Content parser", "version": "1.0"},
        "list": {"description": "List parser", "version": "1.0"},
    }
    return parser_info.get(parser_type, {"description": "Unknown", "version": "0.0"})


def supports_format(parser_type: str, format_type: str) -> bool:
    """指定フォーマットをサポートしているかチェック"""
    support_matrix = {
        "block": ["kumihan", "markdown"],
        "content": ["kumihan", "text"],
        "list": ["kumihan", "markdown", "text"],
    }
    return format_type in support_matrix.get(parser_type, [])
