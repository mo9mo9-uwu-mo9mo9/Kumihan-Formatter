"""
統合API ユーティリティ関数モジュール
======================================

KumihanFormatterクラスの便利関数とラッパー関数を提供します。
unified_api.pyから分離してファイルサイズ最適化に貢献します。
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """クイック変換関数（統合システム）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.convert(input_file, output_file)


def quick_parse(text: str) -> Dict[str, Any]:
    """クイック解析関数（統合ParsingManager）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.parse_text(text)


def unified_parse(text: str, parser_type: str = "auto") -> Dict[str, Any]:
    """統合パーサーシステムによる最適化解析"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.parse_text(text, parser_type)


def validate_kumihan_syntax(text: str) -> Dict[str, Any]:
    """Kumihan記法構文の詳細検証（統合検証システム）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.validate_syntax(text)


def get_parser_system_info() -> Dict[str, Any]:
    """統合Managerシステムの詳細情報取得"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter() as formatter:
        return formatter.get_system_info()


# パフォーマンス最適化版関数（Issue #1229対応）
def optimized_quick_convert(
    input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """最適化クイック変換関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.convert(input_file, output_file)


def optimized_quick_parse(text: str) -> Dict[str, Any]:
    """最適化クイック解析関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.parse_text(text)


def optimized_convert_text(text: str, template: str = "default") -> str:
    """最適化テキスト変換関数（高性能版）"""
    from ...unified_api import KumihanFormatter

    with KumihanFormatter(performance_mode="optimized") as formatter:
        return formatter.convert_text(text, template)


# 後方互換性のためのエイリアス
parse = unified_parse
validate = validate_kumihan_syntax


def main() -> None:
    """CLI エントリーポイント - シンプル実装"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法: kumihan <入力ファイル> [出力ファイル]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        result = quick_convert(input_file, output_file)
        if result["status"] == "success":
            print(f"変換完了: {result['output_file']}")
        else:
            print(f"変換エラー: {result['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"実行エラー: {e}")
        sys.exit(1)


# === Parser Utilities (統合移行: parser_utils.py → api_utils.py) ===


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
