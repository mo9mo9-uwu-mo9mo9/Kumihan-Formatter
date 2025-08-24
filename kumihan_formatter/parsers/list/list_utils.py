"""List Parser Utilities - リスト解析ユーティリティ

分離された責任:
- パターン設定・初期化
- リストハンドラーのセットアップ
- 共通ユーティリティ関数
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from ...core.utilities.logger import get_logger


def setup_list_patterns() -> Dict[str, re.Pattern[str]]:
    """リストパターンの設定"""
    return {
        "unordered": re.compile(r"^\s*[-*+]\s+(.+)$"),
        "ordered_numeric": re.compile(r"^\s*\d+\.\s+(.+)$"),
        "ordered_alpha": re.compile(r"^\s*[a-zA-Z]\.\s+(.+)$"),
        "ordered_roman": re.compile(r"^\s*[ivxlcdm]+\.\s+(.+)$", re.IGNORECASE),
        "checklist": re.compile(r"^\s*- \[[ x]\]\s+(.+)$"),
        "definition": re.compile(r"^(.+):\s*$"),
        "definition_item": re.compile(r"^\s+(.+)$"),
        "kumihan_list": re.compile(r"^# リスト #(.*)##$"),
        "nested_indent": re.compile(r"^(\s*)(.*)$"),
        "list_continuation": re.compile(r"^\s{2,}(.+)$"),
    }


def setup_list_handlers() -> Dict[str, str]:
    """リストハンドラーの設定"""
    return {
        "unordered": "_handle_unordered_item",
        "ordered": "_handle_ordered_numeric_item",
        "checklist": "_handle_checklist_item",
        "definition": "_handle_definition_item",
        "alpha": "_handle_alpha_item",
        "roman": "_handle_roman_item",
    }


def detect_list_type(line: str) -> Optional[str]:
    """リストタイプの検出"""
    line = line.strip()

    if re.match(r"^\s*[-*+]\s+", line):
        return "unordered"
    elif re.match(r"^\s*\d+\.\s+", line):
        return "ordered"
    elif re.match(r"^\s*[a-zA-Z]\.\s+", line):
        return "alpha"
    elif re.match(r"^\s*[ivxlcdm]+\.\s+", line, re.IGNORECASE):
        return "roman"
    elif re.match(r"^\s*- \[[ x]\]\s+", line):
        return "checklist"
    elif line.endswith(":") and not line.startswith(" "):
        return "definition"
    else:
        return None


def get_list_nesting_level(line: str) -> int:
    """リストのネストレベルを取得"""
    if not line.strip():
        return 0

    # インデントを測定
    leading_spaces = len(line) - len(line.lstrip())

    # 2スペースまたは1タブを1レベルとして計算
    if "\t" in line[:leading_spaces]:
        return leading_spaces.count("\t")
    else:
        return leading_spaces // 2


def extract_list_content(content: str) -> List[str]:
    """リストコンテンツの抽出"""
    lines = content.split("\n")
    list_lines = []

    for line in lines:
        # 空行をスキップ
        if not line.strip():
            continue

        # リスト行かどうかチェック
        if detect_list_type(line) or line.startswith(("  ", "\t")):
            list_lines.append(line)

    return list_lines


def is_kumihan_list_block(content: str) -> bool:
    """Kumihanリストブロックの判定"""
    return bool(re.search(r"^# リスト #", content, re.MULTILINE))


def detect_full_list_type(content: str) -> str:
    """コンテンツ全体のリストタイプを検出"""
    lines = content.split("\n")
    type_counts = {
        "unordered": 0,
        "ordered": 0,
        "checklist": 0,
        "definition": 0,
        "alpha": 0,
        "roman": 0,
    }

    for line in lines:
        list_type = detect_list_type(line)
        if list_type in type_counts:
            type_counts[list_type] += 1

    # 最も多いタイプを返す
    max_type = max(type_counts, key=type_counts.get)
    return max_type if type_counts[max_type] > 0 else "mixed"


def extract_list_block(content: str, start_line: int) -> Tuple[List[str], int]:
    """リストブロックの抽出"""
    lines = content.split("\n")
    list_block = []
    current_line = start_line

    # 最初のリストアイテムのインデントレベルを基準とする
    base_indent = (
        get_list_nesting_level(lines[start_line]) if start_line < len(lines) else 0
    )

    while current_line < len(lines):
        line = lines[current_line]

        # 空行は継続
        if not line.strip():
            list_block.append(line)
            current_line += 1
            continue

        # リストアイテムまたは継続行かチェック
        line_indent = get_list_nesting_level(line)
        is_list_item = detect_list_type(line) is not None
        is_continuation = line_indent > base_indent

        if is_list_item or is_continuation:
            list_block.append(line)
            current_line += 1
        else:
            # リストブロック終了
            break

    return list_block, current_line


def is_compatible_list_type(type1: str, type2: str) -> bool:
    """リストタイプの互換性チェック"""
    compatible_groups = [
        {"unordered"},
        {"ordered", "alpha", "roman"},
        {"checklist"},
        {"definition"},
    ]

    for group in compatible_groups:
        if type1 in group and type2 in group:
            return True

    return False


def has_nested_structure(content: str) -> bool:
    """ネスト構造を持つかチェック"""
    lines = content.split("\n")
    indent_levels = set()

    for line in lines:
        if line.strip():
            indent_level = get_list_nesting_level(line)
            indent_levels.add(indent_level)

    return len(indent_levels) > 1


def validate_regular_lists(content: str) -> List[str]:
    """通常のリスト形式の検証"""
    errors = []
    lines = content.split("\n")

    current_list_type = None
    list_numbers = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        list_type = detect_list_type(line)

        if list_type:
            # リストタイプの一貫性チェック
            if current_list_type is None:
                current_list_type = list_type
            elif not is_compatible_list_type(current_list_type, list_type):
                errors.append(
                    f"行 {i}: リストタイプが一貫していません ({current_list_type} vs {list_type})"
                )

            # 順序付きリストの番号チェック
            if list_type == "ordered":
                number_match = re.match(r"^\s*(\d+)\.", line)
                if number_match:
                    number = int(number_match.group(1))
                    list_numbers.append(number)

    # 順序付きリストの連続性チェック
    if list_numbers:
        expected = 1
        for i, number in enumerate(list_numbers):
            if number != expected:
                errors.append(
                    f"順序付きリストの番号が不連続です: 期待値 {expected}, 実際 {number}"
                )
            expected = number + 1

    return errors


def validate_kumihan_list_block(content: str) -> List[str]:
    """Kumihanリストブロックの検証"""
    errors = []

    # Kumihanリストブロックのパターン
    kumihan_pattern = re.compile(r"^# リスト #(.*)##$", re.MULTILINE)
    matches = kumihan_pattern.findall(content)

    for match in matches:
        list_content = match.strip()
        if not list_content:
            errors.append("Kumihanリストブロックの内容が空です")
        else:
            # 内部のリスト構造を検証
            inner_errors = validate_regular_lists(list_content)
            errors.extend(
                [f"Kumihanリストブロック内: {error}" for error in inner_errors]
            )

    return errors


def validate_checklist_format(content: str) -> List[str]:
    """チェックリスト形式の検証"""
    errors = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        if re.match(r"^\s*- \[", line):
            if not re.match(r"^\s*- \[[ x]\]\s+", line):
                errors.append(f"行 {i}: チェックリストの形式が不正です")

    return errors


def validate_definition_format(content: str) -> List[str]:
    """定義リスト形式の検証"""
    errors = []
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().endswith(":") and not line.startswith(" "):
            # 定義項目が見つかった
            i += 1
            has_definition = False

            # 次の行から定義内容をチェック
            while i < len(lines) and (
                lines[i].startswith((" ", "\t")) or not lines[i].strip()
            ):
                if lines[i].strip():
                    has_definition = True
                i += 1

            if not has_definition:
                errors.append(
                    f"定義項目 '{line.strip()}' に対応する定義内容がありません"
                )
        else:
            i += 1

    return errors
