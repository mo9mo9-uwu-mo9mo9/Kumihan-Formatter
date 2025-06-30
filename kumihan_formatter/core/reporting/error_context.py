"""
エラーコンテキスト管理

エラー発生箇所のコンテキスト情報収集の責任を担当
Issue #319対応 - error_reporting.py から分離
"""

from pathlib import Path
from typing import List, Optional


class ErrorContextManager:
    """エラーコンテキスト管理クラス

    責任: エラー発生箇所の周辺情報収集・管理
    """

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path
        self._file_lines: Optional[List[str]] = None

    def load_file(self, file_path: Path) -> None:
        """ファイルを読み込み"""
        self.file_path = file_path
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._file_lines = f.readlines()
        except Exception:
            self._file_lines = None

    def get_context_lines(self, line_number: int, context_range: int = 2) -> List[str]:
        """指定行の周辺コンテキストを取得"""
        if not self._file_lines:
            return []

        start = max(0, line_number - context_range - 1)
        end = min(len(self._file_lines), line_number + context_range)

        context_lines = []
        for i in range(start, end):
            line_content = self._file_lines[i].rstrip("\n")
            line_prefix = f"{i+1:3d}:"

            # 問題行をマーク
            if i == line_number - 1:
                context_lines.append(f">>> {line_prefix} {line_content}")
            else:
                context_lines.append(f"    {line_prefix} {line_content}")

        return context_lines

    def get_highlighted_line(self, line_number: int) -> Optional[str]:
        """指定行をハイライト表示用に取得"""
        if (
            not self._file_lines
            or line_number <= 0
            or line_number > len(self._file_lines)
        ):
            return None

        return self._file_lines[line_number - 1].rstrip("\n")

    def extract_problem_section(
        self, line_number: int, column: Optional[int] = None
    ) -> str:
        """問題箇所を視覚的に強調表示"""
        line = self.get_highlighted_line(line_number)
        if not line:
            return ""

        if column is not None and 0 <= column < len(line):
            # カラム位置を ^ でマーク
            pointer = " " * column + "^"
            return f"{line}\n{pointer}"

        return line

    def is_file_loaded(self) -> bool:
        """ファイルが読み込まれているかチェック"""
        return self._file_lines is not None

    def get_line_count(self) -> int:
        """ファイルの総行数を取得"""
        return len(self._file_lines) if self._file_lines else 0
