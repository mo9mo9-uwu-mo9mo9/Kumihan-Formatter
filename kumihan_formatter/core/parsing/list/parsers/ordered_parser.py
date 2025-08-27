"""順序付きリストパーサー

順序付きリスト・アルファベットリスト・ローマ数字リストの解析を担当
"""

import re
from typing import Any, List, Optional

from ....ast_nodes import Node, create_node


class OrderedListParser:
    """順序付きリストパーサー - 統合版
    
    ordered_list_parser.py の詳細実装を統合
    機能: 数字、アルファベット、ローマ数字のリスト解析
    """

    def __init__(self) -> None:
        """初期化: 順序付きリストパターンを設定"""
        from kumihan_formatter.core.utilities.logger import get_logger
        
        self.logger = get_logger(__name__)
        
        # パターン設定の統合
        self.ordered_patterns = {
            "numeric": re.compile(r"^(\d+)\.\s+(.*)$"),
            "alpha_lower": re.compile(r"^([a-z])\.\s+(.*)$"),
            "alpha_upper": re.compile(r"^([A-Z])\.\s+(.*)$"),
            "roman_lower": re.compile(r"^([ivxlcdm]+)\.\s+(.*)$"),
            "roman_upper": re.compile(r"^([IVXLCDM]+)\.\s+(.*)$"),
        }

    def _get_pattern(self, ordered_type: str) -> re.Pattern[str]:
        """指定された順序付きタイプのパターンを取得
        
        Args:
            ordered_type: 順序付きリストのタイプ
            
        Returns:
            対応する正規表現パターン
        """
        return self.ordered_patterns.get(ordered_type, self.ordered_patterns["numeric"])

    def detect_ordered_type(self, line: str) -> str | None:
        """行から順序付きリストタイプを検出
        
        Args:
            line: 検査対象の行
            
        Returns:
            検出されたリストタイプ、検出されない場合はNone
        """
        for list_type, pattern in self.ordered_patterns.items():
            if pattern.match(line.strip()):
                return list_type
        return None

    def parse_ordered_list(self, lines: list[str]) -> dict[str, Any]:
        """順序付きリストを解析
        
        Args:
            lines: 解析対象の行リスト
            
        Returns:
            解析結果辞書
        """
        if not lines:
            return {"items": [], "type": "numeric", "valid": False}
        
        list_type = self.detect_ordered_type(lines[0])
        if not list_type:
            return {"items": [], "type": "numeric", "valid": False}
        
        return self.handle_ordered_list(lines, list_type)

    def parse_ordered_item(self, line: str, expected_marker: Optional[str] = None) -> dict[str, Any] | None:
        """個別の順序付きリストアイテムを解析
        
        Args:
            line: 解析対象の行
            expected_marker: 期待されるマーカー
            
        Returns:
            解析結果、解析失敗時はNone
        """
        line = line.strip()
        if not line:
            return None

        # 各パターンでマッチを試行
        for list_type, pattern in self.ordered_patterns.items():
            match = pattern.match(line)
            if match:
                marker = match.group(1)
                content = match.group(2).strip()
                
                # 期待されるマーカーとの比較
                if expected_marker and marker != expected_marker:
                    continue
                
                return {
                    "marker": marker,
                    "content": content,
                    "type": list_type,
                    "raw_line": line,
                    "valid": True
                }
        
        return None

    def handle_ordered_list(self, lines: list[str], list_type: str) -> dict[str, Any]:
        """指定されたタイプの順序付きリストを処理
        
        Args:
            lines: 処理対象の行リスト  
            list_type: リストタイプ
            
        Returns:
            処理結果辞書
        """
        if list_type in ["numeric"]:
            return self._handle_numeric_list(lines)
        elif list_type in ["alpha_lower", "alpha_upper"]:
            return self.handle_alpha_list(lines, list_type)
        elif list_type in ["roman_lower", "roman_upper"]:
            return self.handle_roman_list(lines, list_type)
        
        return {"items": [], "type": list_type, "valid": False}

    def _handle_numeric_list(self, lines: list[str]) -> dict[str, Any]:
        """数値順序リストの処理"""
        items = []
        for i, line in enumerate(lines):
            item = self.parse_ordered_item(line, str(i + 1))
            if item:
                items.append(item)
            else:
                break
        
        return {
            "items": items,
            "type": "numeric",
            "valid": len(items) == len(lines)
        }

    def handle_alpha_list(self, lines: list[str], list_type: str) -> dict[str, Any]:
        """アルファベット順序リストの処理
        
        Args:
            lines: 処理対象の行リスト
            list_type: alpha_lower または alpha_upper
            
        Returns:
            処理結果辞書
        """
        items = []
        is_upper = list_type == "alpha_upper"
        base_ord = ord('A') if is_upper else ord('a')
        
        for i, line in enumerate(lines):
            expected_char = chr(base_ord + i)
            item = self.parse_ordered_item(line, expected_char)
            if item:
                items.append(item)
            else:
                break
        
        return {
            "items": items,
            "type": list_type,
            "valid": self.validate_sequence([item["marker"] for item in items], list_type)
        }

    def handle_roman_list(self, lines: list[str], list_type: str) -> dict[str, Any]:
        """ローマ数字順序リストの処理
        
        Args:
            lines: 処理対象の行リスト
            list_type: roman_lower または roman_upper
            
        Returns:
            処理結果辞書
        """
        items = []
        roman_numerals = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
        if list_type == "roman_upper":
            roman_numerals = [r.upper() for r in roman_numerals]
        
        for i, line in enumerate(lines):
            if i >= len(roman_numerals):
                break
            expected_roman = roman_numerals[i]
            item = self.parse_ordered_item(line, expected_roman)
            if item:
                items.append(item)
            else:
                break
        
        return {
            "items": items,
            "type": list_type,
            "valid": self.validate_sequence([item["marker"] for item in items], list_type)
        }

    def validate_sequence(self, markers: list[str], list_type: str) -> bool:
        """マーカー序列の妥当性を検証
        
        Args:
            markers: マーカーのリスト
            list_type: リストタイプ
            
        Returns:
            序列が妥当な場合True
        """
        if not markers:
            return False
        
        if list_type == "numeric":
            try:
                nums = [int(m) for m in markers]
                return nums == list(range(1, len(nums) + 1))
            except ValueError:
                return False
        
        elif list_type in ["alpha_lower", "alpha_upper"]:
            base_ord = ord('A') if list_type == "alpha_upper" else ord('a')
            expected = [chr(base_ord + i) for i in range(len(markers))]
            return markers == expected
        
        elif list_type in ["roman_lower", "roman_upper"]:
            roman_sequence = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
            if list_type == "roman_upper":
                roman_sequence = [r.upper() for r in roman_sequence]
            expected = roman_sequence[:len(markers)]
            return markers == expected
        
        return False

    def convert_to_numeric(self, marker: str, list_type: str) -> int:
        """マーカーを数値に変換
        
        Args:
            marker: 変換対象のマーカー
            list_type: リストタイプ
            
        Returns:
            数値表現、変換できない場合は0
        """
        try:
            if list_type == "numeric":
                return int(marker)
            
            elif list_type in ["alpha_lower", "alpha_upper"]:
                base_ord = ord('A') if list_type == "alpha_upper" else ord('a')
                return ord(marker) - base_ord + 1
            
            elif list_type in ["roman_lower", "roman_upper"]:
                # ローマ数字変換の簡易実装
                roman_values = {
                    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
                    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10
                }
                return roman_values.get(marker.lower(), 0)
            
        except (ValueError, KeyError):
            pass
        
        return 0

    def get_next_marker(self, current_marker: str, list_type: str) -> str:
        """現在のマーカーから次のマーカーを生成
        
        Args:
            current_marker: 現在のマーカー
            list_type: リストタイプ
            
        Returns:
            次のマーカー
        """
        try:
            if list_type == "numeric":
                current_num = int(current_marker)
                return str(current_num + 1)
            
            elif list_type in ["alpha_lower", "alpha_upper"]:
                if len(current_marker) == 1:
                    next_char = chr(ord(current_marker) + 1)
                    # Z/zを超えた場合の処理
                    if list_type == "alpha_upper" and next_char > 'Z':
                        return 'A'
                    elif list_type == "alpha_lower" and next_char > 'z':
                        return 'a'
                    return next_char
            
            elif list_type in ["roman_lower", "roman_upper"]:
                roman_sequence = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
                if list_type == "roman_upper":
                    roman_sequence = [r.upper() for r in roman_sequence]
                
                try:
                    current_index = roman_sequence.index(current_marker)
                    if current_index + 1 < len(roman_sequence):
                        return roman_sequence[current_index + 1]
                except ValueError:
                    pass
                
                return roman_sequence[0]  # フォールバック
            
        except (ValueError, IndexError):
            pass
        
        # フォールバック: 元のマーカーを返す
        return current_marker

    # API互換性メソッド（簡素版からの移行用）
    def can_handle(self, line: str) -> bool:
        """行が処理可能かどうかを判定"""
        return self.detect_ordered_type(line) is not None

    def extract_item_content(self, line: str) -> str:
        """アイテム内容を抽出"""
        item = self.parse_ordered_item(line)
        return item["content"] if item else ""

    def validate_ordered_sequence(self, markers: list[str]) -> bool:
        """順序シーケンスの妥当性検証（API互換）"""
        if not markers:
            return False
        
        # 最初のマーカーからタイプを推定
        first_line_mock = f"{markers[0]}. test"
        list_type = self.detect_ordered_type(first_line_mock)
        
        if list_type:
            return self.validate_sequence(markers, list_type)
        return False

    def get_supported_types(self) -> list[str]:
        """サポート対象のタイプリストを返す"""
        return list(self.ordered_patterns.keys())
