"""
コンテンツ系エラーの回復戦略 - Issue #401対応

構文エラー、メモリ不足エラーの回復戦略。
"""

import shutil
from pathlib import Path
from typing import Any

from ..error_types import ErrorCategory, UserFriendlyError
from .base import RecoveryStrategy


class SyntaxErrorRecoveryStrategy(RecoveryStrategy):
    """構文エラーの回復戦略"""

    def __init__(self) -> None:
        super().__init__("SyntaxErrorRecovery", priority=4)
        # よくある修正パターン
        self.correction_patterns = {
            ";;;太字": ";;;太字;;;",
            ";;;見出し": ";;;見出し1;;;",
            ";;太字;;": ";;;太字;;;",
            ";;;;太字;;;;": ";;;太字;;;",
        }

    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """構文エラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.SYNTAX
            or "syntax" in error.error_code.lower()
            or "記法" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """構文エラーの自動修正による回復"""
        file_path = context.get("file_path")
        line_number = context.get("line_number")

        if not file_path or not line_number:
            return False, "エラー位置の特定に失敗しました"

        self.logger.info(f"Attempting syntax recovery for: {file_path}:{line_number}")

        try:
            path = Path(file_path)
            lines = path.read_text(encoding="utf-8").splitlines()

            if line_number > len(lines):
                return False, "行番号が範囲外です"

            error_line = lines[line_number - 1]
            original_line = error_line

            # 修正パターンを適用
            corrected = False
            for pattern, replacement in self.correction_patterns.items():
                if pattern in error_line:
                    error_line = error_line.replace(pattern, replacement)
                    corrected = True
                    break

            if not corrected:
                # 一般的な修正を試行
                error_line = self._apply_general_corrections(error_line)
                corrected = error_line != original_line

            if corrected:
                # バックアップを作成
                backup_path = path.with_suffix(".backup")
                if not backup_path.exists():
                    shutil.copy2(path, backup_path)

                # 修正版を保存
                lines[line_number - 1] = error_line
                path.write_text("\n".join(lines), encoding="utf-8")

                self.logger.info(
                    f"Applied syntax correction: '{original_line}' → '{error_line}'"
                )
                return (
                    True,
                    f"構文エラーを自動修正しました: {line_number}行目（バックアップ: {backup_path.name}）",
                )

            return False, "自動修正パターンが見つかりませんでした"

        except Exception as e:
            self.logger.error(f"Syntax recovery failed: {e}")
            return False, f"構文回復に失敗: {str(e)}"

    def _apply_general_corrections(self, line: str) -> str:
        """一般的な構文修正を適用"""
        corrected = line

        # マーカーの修正
        if ";;" in corrected and not corrected.count(";;;") >= 2:
            # ;;;の数を修正
            corrected = corrected.replace(";;", ";;;")

        # 開始マーカーのみの場合、終了マーカーを追加
        if corrected.count(";;;") == 1 and corrected.endswith(";;;"):
            # 単語の終端を探して終了マーカーを追加
            words = corrected.split()
            if len(words) >= 2:
                corrected = corrected + ";;;"

        return corrected


class MemoryErrorRecoveryStrategy(RecoveryStrategy):
    """メモリ不足エラーの回復戦略"""

    def __init__(self) -> None:
        super().__init__("MemoryErrorRecovery", priority=1)

    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """メモリエラーを処理できるかチェック"""
        return (
            "memory" in error.error_code.lower()
            or "メモリ" in error.user_message
            or isinstance(context.get("original_exception"), MemoryError)
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """メモリ使用量の削減による回復"""
        self.logger.info("Attempting memory recovery")

        try:
            # ガベージコレクションを実行
            import gc

            collected = gc.collect()

            # ファイル分割処理の提案
            file_path = context.get("file_path")
            if file_path:
                path = Path(file_path)
                if path.exists():
                    file_size = path.stat().st_size
                    if file_size > 10 * 1024 * 1024:  # 10MB以上
                        context["suggest_file_split"] = True
                        return (
                            True,
                            f"メモリを解放しました（{collected}オブジェクト）。大きなファイルの分割処理を推奨します。",
                        )

            if collected > 0:
                return True, f"メモリを解放しました（{collected}オブジェクト）"

            return False, "メモリ回復効果がありませんでした"

        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")
            return False, f"メモリ回復に失敗: {str(e)}"
