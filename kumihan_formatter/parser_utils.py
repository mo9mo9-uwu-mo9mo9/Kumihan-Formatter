"""
Parser utility functions for JSON path processing and string manipulation.
"""

import re
from typing import List, Optional, Tuple


def extract_json_path(json_path: str) -> List[str]:
    """
    JSONパスを解析して、パスの要素リストを返します。

    Args:
        json_path (str): 解析するJSONパス (例: "data.items[0].name")

    Returns:
        List[str]: パスの要素リスト (例: ["data", "items", "0", "name"])
    """
    if not json_path:
        return []

    # ドット記法とブラケット記法を統一的に処理
    # "data.items[0].name" -> ["data", "items", "0", "name"]
    path = json_path.replace("[", ".").replace("]", "")
    parts = [part.strip() for part in path.split(".") if part.strip()]

    return parts


def find_closing_brace(text: str, start_pos: int) -> int:
    """
    開始位置から対応する閉じ括弧の位置を見つけます。

    Args:
        text (str): 検索する文字列
        start_pos (int): 開始位置

    Returns:
        int: 閉じ括弧の位置。見つからない場合は-1
    """
    if start_pos >= len(text) or text[start_pos] != "{":
        return -1

    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start_pos, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return i

    return -1


def find_matching_quote(text: str, start_pos: int) -> int:
    """
    開始位置から対応する閉じクォートの位置を見つけます。

    Args:
        text (str): 検索する文字列
        start_pos (int): 開始位置

    Returns:
        int: 閉じクォートの位置。見つからない場合は-1
    """
    if start_pos >= len(text):
        return -1

    quote_char = text[start_pos]
    if quote_char not in ['"', "'"]:
        return -1

    escape_next = False

    for i in range(start_pos + 1, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == quote_char:
            return i

    return -1


def is_valid_json_path_character(char: str) -> bool:
    """
    文字がJSONパスで有効かどうかを判定します。

    Args:
        char (str): 判定する文字

    Returns:
        bool: 有効な場合はTrue
    """
    return char.isalnum() or char in ["_", "-", ".", "[", "]"]


def remove_quotes(text: str) -> str:
    """
    文字列の前後のクォートを除去します。

    Args:
        text (str): 処理する文字列

    Returns:
        str: クォートを除去した文字列
    """
    if not text:
        return text

    text = text.strip()

    if len(text) >= 2:
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("'") and text.endswith("'")
        ):
            return text[1:-1]

    return text
