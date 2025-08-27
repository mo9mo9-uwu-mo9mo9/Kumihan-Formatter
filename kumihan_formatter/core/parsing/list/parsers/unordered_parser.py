"""非順序リストパーサー

非順序リスト・チェックリスト・定義リストの解析を担当
"""

import re
from typing import Any, Dict, List, Optional

from ....ast_nodes import Node, create_node


class UnorderedListParser:
    """無序リストパーサー - 統合版
    
    unordered_list_parser.py の詳細実装を統合
    機能: -, *, +マーカー、チェックリスト、定義リストの解析
    """

    def __init__(self) -> None:
        """初期化: 無序リストパターンを設定"""
        from kumihan_formatter.core.utilities.logger import get_logger
        
        self.logger = get_logger(__name__)
        self.unordered_patterns = {
            "bullet": re.compile(r"^([-*+])\s+(.*)$"),
            "checklist": re.compile(r"^([-*+])\s+\[([ xX])\]\s+(.*)$"),
            "definition": re.compile(r"^([^:]+):\s+(.*)$"),
        }

    def detect_unordered_type(self, line: str) -> str | None:
        """行から無序リストタイプを検出
        
        Args:
            line: 検査対象の行
            
        Returns:
            検出されたリストタイプ、検出されない場合はNone
        """
        line = line.strip()
        if not line:
            return None
        
        # チェックリストの優先検査
        if self.unordered_patterns["checklist"].match(line):
            return "checklist"
        
        # 通常のブレットリスト
        if self.unordered_patterns["bullet"].match(line):
            return "bullet"
        
        # 定義リスト
        if self.unordered_patterns["definition"].match(line):
            return "definition"
        
        return None

    def parse_unordered_list(self, lines: list[str]) -> dict[str, Any]:
        """無序リストを解析
        
        Args:
            lines: 解析対象の行リスト
            
        Returns:
            解析結果辞書
        """
        if not lines:
            return {"items": [], "type": "bullet", "valid": False}
        
        list_type = self.detect_unordered_type(lines[0])
        if not list_type:
            return {"items": [], "type": "bullet", "valid": False}
        
        return self.handle_unordered_list(lines, list_type)

    def parse_unordered_item(self, line: str, expected_marker: Optional[str] = None) -> dict[str, Any] | None:
        """個別の無序リストアイテムを解析
        
        Args:
            line: 解析対象の行
            expected_marker: 期待されるマーカー
            
        Returns:
            解析結果、解析失敗時はNone
        """
        line = line.strip()
        if not line:
            return None

        # チェックリストアイテムの解析
        checklist_match = self.unordered_patterns["checklist"].match(line)
        if checklist_match:
            marker = checklist_match.group(1)
            status = checklist_match.group(2)
            content = checklist_match.group(3).strip()
            
            if expected_marker and marker != expected_marker:
                return None
            
            return {
                "marker": marker,
                "content": content,
                "type": "checklist",
                "status": status.lower() == 'x',
                "raw_line": line,
                "valid": True
            }

        # 通常のブレットリストアイテムの解析
        bullet_match = self.unordered_patterns["bullet"].match(line)
        if bullet_match:
            marker = bullet_match.group(1)
            content = bullet_match.group(2).strip()
            
            if expected_marker and marker != expected_marker:
                return None
            
            return {
                "marker": marker,
                "content": content,
                "type": "bullet",
                "raw_line": line,
                "valid": True
            }

        # 定義リストアイテムの解析
        definition_match = self.unordered_patterns["definition"].match(line)
        if definition_match:
            term = definition_match.group(1).strip()
            definition = definition_match.group(2).strip()
            
            return {
                "term": term,
                "definition": definition,
                "type": "definition",
                "raw_line": line,
                "valid": True
            }
        
        return None

    def handle_unordered_list(self, lines: list[str], list_type: str) -> dict[str, Any]:
        """指定されたタイプの無序リストを処理
        
        Args:
            lines: 処理対象の行リスト  
            list_type: リストタイプ
            
        Returns:
            処理結果辞書
        """
        if list_type == "bullet":
            return self._handle_bullet_list(lines)
        elif list_type == "checklist":
            return self.handle_checklist(lines)
        elif list_type == "definition":
            return self.handle_definition_list(lines)
        
        return {"items": [], "type": list_type, "valid": False}

    def _handle_bullet_list(self, lines: list[str]) -> dict[str, Any]:
        """ブレットリストの処理"""
        items = []
        for line in lines:
            item = self.parse_unordered_item(line)
            if item and item["type"] == "bullet":
                items.append(item)
            else:
                break
        
        return {
            "items": items,
            "type": "bullet",
            "valid": len(items) == len(lines)
        }

    def handle_checklist(self, lines: list[str]) -> dict[str, Any]:
        """チェックリストの処理
        
        Args:
            lines: 処理対象の行リスト
            
        Returns:
            処理結果辞書
        """
        items = []
        checked_count = 0
        
        for line in lines:
            item = self.parse_unordered_item(line)
            if item and item["type"] == "checklist":
                items.append(item)
                if item.get("status", False):
                    checked_count += 1
            else:
                break
        
        return {
            "items": items,
            "type": "checklist",
            "checked_count": checked_count,
            "total_count": len(items),
            "completion_rate": checked_count / len(items) if items else 0.0,
            "valid": len(items) == len(lines)
        }

    def handle_definition_list(self, lines: list[str]) -> dict[str, Any]:
        """定義リストの処理
        
        Args:
            lines: 処理対象の行リスト
            
        Returns:
            処理結果辞書
        """
        items = []
        
        for line in lines:
            item = self.parse_unordered_item(line)
            if item and item["type"] == "definition":
                items.append(item)
            else:
                break
        
        return {
            "items": items,
            "type": "definition",
            "valid": len(items) == len(lines)
        }

    def extract_checklist_status(self, line: str) -> tuple[str, bool]:
        """チェックリスト行からステータスを抽出
        
        Args:
            line: チェックリスト行
            
        Returns:
            (内容, チェック状態) のタプル
        """
        match = self.unordered_patterns["checklist"].match(line.strip())
        if match:
            content = match.group(3).strip()
            status = match.group(2).lower() == 'x'
            return content, status
        
        # チェックリスト形式でない場合
        return line.strip(), False

    def toggle_checklist_item(self, line: str) -> str:
        """チェックリストアイテムの状態をトグル
        
        Args:
            line: 元のチェックリスト行
            
        Returns:
            状態をトグルした行
        """
        match = self.unordered_patterns["checklist"].match(line.strip())
        if match:
            marker = match.group(1)
            current_status = match.group(2)
            content = match.group(3)
            
            # ステータスをトグル
            new_status = ' ' if current_status.lower() == 'x' else 'x'
            return f"{marker} [{new_status}] {content}"
        
        # チェックリスト形式でない場合はそのまま返す
        return line

    def convert_to_bullet_list(self, lines: list[str]) -> list[str]:
        """チェックリストを通常のブレットリストに変換
        
        Args:
            lines: 変換対象の行リスト
            
        Returns:
            変換された行リスト
        """
        converted = []
        for line in lines:
            match = self.unordered_patterns["checklist"].match(line.strip())
            if match:
                marker = match.group(1)
                content = match.group(3)
                converted.append(f"{marker} {content}")
            else:
                # チェックリスト形式でなければそのまま保持
                converted.append(line)
        
        return converted

    def get_marker_from_line(self, line: str) -> str:
        """行からマーカーを抽出
        
        Args:
            line: 抽出対象の行
            
        Returns:
            抽出されたマーカー、見つからない場合は'-'
        """
        line = line.strip()
        
        # チェックリストマーカー
        checklist_match = self.unordered_patterns["checklist"].match(line)
        if checklist_match:
            return checklist_match.group(1)
        
        # 通常のブレットマーカー
        bullet_match = self.unordered_patterns["bullet"].match(line)
        if bullet_match:
            return bullet_match.group(1)
        
        return '-'  # デフォルトマーカー

    def normalize_marker(self, marker: str) -> str:
        """マーカーを正規化
        
        Args:
            marker: 正規化対象のマーカー
            
        Returns:
            正規化されたマーカー
        """
        # 有効なマーカーリスト
        valid_markers = ['-', '*', '+']
        
        if marker in valid_markers:
            return marker
        
        # 全角文字の正規化
        marker_mapping = {
            '－': '-',
            '＊': '*',
            '＋': '+',
            '・': '*',
        }
        
        normalized = marker_mapping.get(marker, marker)
        
        # 正規化後も無効な場合は '-' をデフォルトとする
        return normalized if normalized in valid_markers else '-'

    # API互換性メソッド（簡素版からの移行用）
    def can_handle(self, line: str) -> bool:
        """行が処理可能かどうかを判定"""
        return self.detect_unordered_type(line) is not None

    def extract_item_content(self, line: str) -> str:
        """アイテム内容を抽出"""
        item = self.parse_unordered_item(line)
        if item:
            return item.get("content", item.get("definition", ""))
        return ""

    def validate_marker_consistency(self, lines: list[str]) -> bool:
        """マーカーの一貫性を検証"""
        if not lines:
            return True
        
        first_marker = self.get_marker_from_line(lines[0])
        return all(self.get_marker_from_line(line) == first_marker for line in lines)

    def get_supported_types(self) -> list[str]:
        """サポート対象のタイプリストを返す"""
        return list(self.unordered_patterns.keys())
