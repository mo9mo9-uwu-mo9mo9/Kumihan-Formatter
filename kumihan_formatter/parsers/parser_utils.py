"""
ParserUtils - 統合パーサーユーティリティ

統合対象:
- kumihan_formatter/parser_utils.py
- kumihan_formatter/core/parsing/base/parser_protocols.py（一部）
"""

from typing import Any, Dict, List, Optional, Union
import re
import json
from ..parser_utils import (
    extract_json_path,
    remove_quotes,
    find_closing_brace,
    is_valid_json_path_character,
    find_matching_quote,
)
from ..core.utilities.logger import get_logger


class ParserUtils:
    """統合パーサーユーティリティクラス"""

    def __init__(self):
        self.logger = get_logger(__name__)

    # 既存ユーティリティ関数のラッパー
    @staticmethod
    def extract_json_path(data: Dict[str, Any], path: str) -> Any:
        """JSONパス抽出"""
        return extract_json_path(data, path)

    @staticmethod
    def remove_quotes(text: str) -> str:
        """クォート削除"""
        return remove_quotes(text)

    @staticmethod
    def find_closing_brace(text: str, start_pos: int) -> int:
        """終了ブレース検索"""
        return find_closing_brace(text, start_pos)

    @staticmethod
    def is_valid_json_path_character(char: str) -> bool:
        """JSONパス文字検証"""
        return is_valid_json_path_character(char)

    @staticmethod
    def find_matching_quote(text: str, start_pos: int) -> int:
        """対応クォート検索"""
        return find_matching_quote(text, start_pos)

    # 新規ユーティリティメソッド
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """空白正規化"""
        return re.sub(r"\s+", " ", text.strip())

    @staticmethod
    def split_by_delimiter(
        text: str, delimiter: str, max_split: Optional[int] = None
    ) -> List[str]:
        """区切り文字による分割"""
        if max_split is not None:
            return text.split(delimiter, max_split)
        return text.split(delimiter)

    @staticmethod
    def escape_special_chars(text: str) -> str:
        """特殊文字エスケープ"""
        return (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

    @staticmethod
    def unescape_special_chars(text: str) -> str:
        """特殊文字アンエスケープ"""
        return (
            text.replace("\\\\", "\\")
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\r", "\r")
        )

    @classmethod
    def validate_syntax_pattern(cls, text: str, pattern: str) -> bool:
        """構文パターン検証"""
        try:
            return bool(re.match(pattern, text))
        except re.error:
            return False

    @classmethod
    def extract_patterns(cls, text: str, pattern: str) -> List[str]:
        """パターン抽出"""
        try:
            return re.findall(pattern, text)
        except re.error:
            return []

    @classmethod
    def count_nested_levels(
        cls, text: str, open_char: str = "{", close_char: str = "}"
    ) -> int:
        """ネスト深度計算"""
        level = 0
        max_level = 0
        for char in text:
            if char == open_char:
                level += 1
                max_level = max(max_level, level)
            elif char == close_char:
                level -= 1
        return max_level

    @classmethod
    def safe_json_parse(cls, text: str) -> Optional[Dict[str, Any]]:
        """安全なJSON解析"""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    def format_error_message(
        cls, error: str, line: int = None, column: int = None
    ) -> str:
        """エラーメッセージフォーマット"""
        if line is not None and column is not None:
            return f"Line {line}, Column {column}: {error}"
        elif line is not None:
            return f"Line {line}: {error}"
        else:
            return error
