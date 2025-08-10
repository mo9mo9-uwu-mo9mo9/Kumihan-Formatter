"""Core syntax validation logic

This module contains the main validation logic for Kumihan markup syntax,
including block validation, keyword validation, and line-by-line checking.
"""

from pathlib import Path

from .syntax_errors import ErrorTypes, SyntaxError, ErrorSeverity
from ..error_analysis.error_config import ErrorHandlingLevel

# from .syntax_rules import SyntaxRules  # 下部で再定義されているため削除


class UserFriendlyError:
    """Simple error class for user-friendly error messages"""

    def __init__(self, message: str, details: str = "", severity: str = "error"):
        self.message = message
        self.details = details
        self.severity = severity


class ErrorCatalog:
    """Simple error catalog for creating user-friendly errors"""

    @staticmethod
    def create_encoding_error(file_path: str) -> UserFriendlyError:
        return UserFriendlyError(
            f"エラー: {file_path} のエンコーディングが UTF-8 ではありません",
            "ファイルを UTF-8 エンコーディングで保存し直してください。",
            "error",
        )

    @staticmethod
    def create_file_not_found_error(file_path: str) -> UserFriendlyError:
        return UserFriendlyError(
            f"エラー: ファイル {file_path} が見つかりません",
            "ファイルパスを確認してください。",
            "error",
        )

    @staticmethod
    def create_syntax_error(
        line_num: int, invalid_content: str, file_path: str
    ) -> UserFriendlyError:
        return UserFriendlyError(
            f"構文エラー: {file_path} の {line_num} 行目",
            f"無効な内容: {invalid_content}",
            "error",
        )


class KumihanSyntaxValidator:
    """Core Kumihan markup syntax validator"""

    def __init__(self) -> None:
        self.errors: list[SyntaxError] = []
        self.current_file = ""

    def validate_text(self, text: str) -> list[SyntaxError]:
        """テキスト内容を直接検証（テスト互換性のため）

        Args:
            text: 検証対象のテキスト

        Returns:
            list[SyntaxError]: 検出されたエラーのリスト
        """
        self.errors.clear()
        self.current_file = "<text>"

        lines = text.splitlines()
        self._validate_syntax(lines)

        return self.errors

    def get_friendly_errors(self) -> list[UserFriendlyError]:
        """Convert SyntaxError to UserFriendlyError instances"""
        friendly_errors = []

        for error in self.errors:
            if error.error_type == ErrorTypes.ENCODING:
                friendly_error = ErrorCatalog.create_encoding_error(self.current_file)
            elif error.error_type == ErrorTypes.FILE_NOT_FOUND:
                friendly_error = ErrorCatalog.create_file_not_found_error(self.current_file)
            elif error.error_type in [
                ErrorTypes.INVALID_KEYWORD,
                ErrorTypes.UNKNOWN_KEYWORD,
            ]:
                # Extract invalid content from context
                invalid_content = error.context.strip()
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=invalid_content,
                    file_path=self.current_file,
                )
            else:
                # Other errors as general syntax errors
                friendly_error = ErrorCatalog.create_syntax_error(
                    line_num=error.line_number,
                    invalid_content=error.message,
                    file_path=self.current_file,
                )

            friendly_errors.append(friendly_error)

        return friendly_errors

    def validate_file(self, file_path: Path) -> list[SyntaxError]:
        """Validate a single file for syntax errors"""
        self.errors.clear()
        self.current_file = str(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            self._add_error(
                1,
                1,
                ErrorHandlingLevel.STRICT,
                ErrorTypes.ENCODING,
                "ファイルのエンコーディングが UTF-8 ではありません",
                str(file_path),
            )
            return self.errors
        except FileNotFoundError:
            self._add_error(
                1,
                1,
                ErrorHandlingLevel.STRICT,
                ErrorTypes.FILE_NOT_FOUND,
                "ファイルが見つかりません",
                str(file_path),
            )
            return self.errors

        lines = content.splitlines()
        self._validate_syntax(lines)

        return self.errors

    def validate_files(self, file_paths: list[str]) -> list[SyntaxError]:
        """複数ファイルをバッチ検証（テスト互換性のため）

        Args:
            file_paths: 検証するファイルパスのリスト

        Returns:
            list[SyntaxError]: 全ファイルからの検証エラーリスト
        """
        from pathlib import Path

        all_errors = []

        for file_path in file_paths:
            try:
                # str型をPath型に変換
                path_obj = Path(file_path)
                errors = self.validate_file(path_obj)
                all_errors.extend(errors)
            except Exception as e:
                # ファイル読み取りエラーなどの場合
                from kumihan_formatter.core.syntax.syntax_errors import SyntaxError
                from kumihan_formatter.core.error_analysis.error_config import (
                    ErrorSeverity,
                )

                error = SyntaxError(
                    line_number=0,
                    column=0,
                    error_type="FileError",
                    message=f"ファイル読み取りエラー: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    context=file_path,  # context引数を追加
                )
                all_errors.append(error)

        return all_errors

    def _validate_syntax(self, lines: list[str]) -> None:
        """Validate syntax for all lines (新記法対応)"""
        import re

        # in_block = False  # 未使用変数
        # block_start_line = 0  # 未使用変数
        # block_keywords = []  # 未使用変数
        in_new_block = False
        new_block_start_line = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # 新記法のブロック検証
            if stripped == "#" or stripped == "＃":
                if in_new_block:
                    in_new_block = False
                else:
                    # 開始されていないブロック終了
                    self._add_error(
                        line_num,
                        1,
                        ErrorHandlingLevel.STRICT,
                        ErrorTypes.UNMATCHED_BLOCK_END,
                        "ブロック開始マーカーなしに # が見つかりました",
                        line,
                    )
            elif re.match(r"^[#＃][^#＃\s]+$", stripped):
                # 新記法ブロック開始
                if in_new_block:
                    # 前のブロックが閉じられていない
                    self._add_error(
                        new_block_start_line,
                        1,
                        ErrorHandlingLevel.STRICT,
                        ErrorTypes.UNCLOSED_BLOCK,
                        "ブロックが # で閉じられていません",
                        (
                            lines[new_block_start_line - 1]
                            if new_block_start_line <= len(lines)
                            else ""
                        ),
                    )
                in_new_block = True
                new_block_start_line = line_num

            # 新記法の個別行検証
            self._validate_new_notation(line_num, line)

            # ;;;記法は削除されました（Phase 1完了）
            # 新記法のチェックは _validate_new_notation で実行されます

            # Check for other syntax issues
            self._validate_line_syntax(line_num, line)

        # ;;;記法のuncloded blockチェックは削除されました（Phase 1完了）

        # Check for unclosed blocks (新記法)
        if in_new_block:
            self._add_error(
                new_block_start_line,
                1,
                ErrorHandlingLevel.STRICT,
                ErrorTypes.UNCLOSED_BLOCK,
                "ブロックが # で閉じられていません",
                (lines[new_block_start_line - 1] if new_block_start_line <= len(lines) else ""),
                "ブロックの最後に # を追加してください",
            )

    def _validate_new_notation(self, line_num: int, line: str) -> None:
        """新記法（#記法#）の検証"""
        import re

        stripped = line.strip()

        # ブロック形式の開始/終了マーカーをスキップ
        # 単独の # はブロック終了マーカー
        if stripped == "#" or stripped == "＃":
            return

        # ブロック形式と未完了インライン形式を区別
        # ブロック形式: #キーワード（単語のみ、空白なし）
        # 未完了インライン: #キーワード 内容（空白がある）
        if re.match(r"^[#＃][^#＃\s]+$", stripped):
            # 空白がない場合はブロック開始マーカーとして有効
            return

        # インライン形式の未完了マーカーを検出
        # パターン: 行に # があるが、適切にペアになっていない
        if "#" in stripped or "＃" in stripped:
            # 完全なインライン形式 #キーワード 内容# があるかチェック
            # ルビ記法も含むパターンを考慮: #ルビ 内容(読み)#
            has_complete_inline = bool(re.search(r"[#＃][^#＃]+[#＃]", stripped))

            if not has_complete_inline:
                # # があるが完全なインライン形式ではない場合はエラー
                if re.search(r"[#＃][^#＃]+", stripped):
                    self._add_error(
                        line_num,
                        1,
                        ErrorHandlingLevel.STRICT,
                        ErrorTypes.UNCLOSED_BLOCK,
                        "未完了のマーカー: 終了マーカー # が見つかりません",
                        line,
                        "マーカーの最後に # を追加してください",
                    )

    def _validate_mixing_rules(self, line_num: int, line: str) -> None:
        """混在禁止ルールの検証（Phase 1）"""
        from kumihan_formatter.core.syntax.syntax_rules import SyntaxRules

        # マーカー混在チェック
        marker_violations = SyntaxRules.check_marker_mixing(line)
        for violation in marker_violations:
            self._add_error(
                line_num,
                1,
                ErrorHandlingLevel.STRICT,
                ErrorTypes.SYNTAX_ERROR,
                violation,
                line,
                "同一テキスト内では半角（#）または全角（＃）のいずれかのマーカーに統一してください",
            )

        # color属性混在チェック
        color_violations = SyntaxRules.check_color_case_mixing(line)
        for violation in color_violations:
            self._add_error(
                line_num,
                1,
                ErrorHandlingLevel.STRICT,
                ErrorTypes.SYNTAX_ERROR,
                violation,
                line,
                "color属性は大文字・小文字・混在表記のいずれかに統一してください",
            )

    def _validate_block_keywords(self, line_num: int, line: str) -> None:
        """ブロックキーワードの妥当性をチェック（;;;記法削除により未使用）"""
        # ;;;記法は削除されました（Phase 1完了）
        return

    def _check_multiline_syntax(
        self, line_num: int, line: str, block_start_line: int, block_keywords: list[str]
    ) -> None:
        """マルチライン構文エラーをチェック"""
        self._add_error(
            line_num,
            1,
            ErrorHandlingLevel.STRICT,
            ErrorTypes.INVALID_SYNTAX,
            "ブロック内で新しいブロックが開始されています",
            line,
            f"ブロックは{block_start_line}行目で開始されていますが、まだ閉じられていません",
        )

    def _add_error(
        self,
        line_number: int,
        column: int,
        severity: ErrorHandlingLevel,
        error_type: ErrorTypes | str,
        message: str,
        context: str,
        suggestion: str = "",
    ) -> None:
        """エラーをエラーリストに追加"""
        from kumihan_formatter.core.syntax.syntax_errors import ErrorSeverity

        # Convert ErrorHandlingLevel to ErrorSeverity
        if severity == ErrorHandlingLevel.STRICT:
            converted_severity = ErrorSeverity.ERROR
        elif severity == ErrorHandlingLevel.LENIENT:
            converted_severity = ErrorSeverity.WARNING
        elif severity == ErrorHandlingLevel.IGNORE:
            converted_severity = ErrorSeverity.INFO
        else:  # NORMAL
            converted_severity = ErrorSeverity.ERROR

        error = SyntaxError(
            line_number=line_number,
            column=column,
            severity=converted_severity,
            error_type=getattr(error_type, "value", str(error_type)),
            message=message,
            context=context,
            suggestion=suggestion,
        )
        self.errors.append(error)

    def _validate_line_syntax(self, line_num: int, line: str) -> None:
        """行単位の構文チェック"""
        # Phase 1: 混在禁止ルールを追加
        self._validate_mixing_rules(line_num, line)

        # 基本的な構文チェック（簡易実装）
        stripped = line.strip()

        # 無効な文字パターンをチェック
        if "(((" in stripped or ")))" in stripped:
            self._add_error(
                line_num,
                1,
                ErrorHandlingLevel.LENIENT,
                ErrorTypes.INVALID_SYNTAX,
                "無効な括弧パターンが検出されました",
                line,
                "脚注記法は # 脚注 #内容## を使用してください",
            )

    def _is_inline_notation(self, line: str) -> bool:
        """インライン記法かどうかを判定

        ;;;記法は削除されました（Phase 1）
        この機能は新記法で置き換えられます
        """
        return False
