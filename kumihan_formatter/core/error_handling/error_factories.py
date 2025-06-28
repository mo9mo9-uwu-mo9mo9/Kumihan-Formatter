"""
エラーファクトリー - 特定のエラータイプを生成するファクトリークラス
"""

from pathlib import Path
from typing import Any, Dict

from .error_types import ErrorCategory, ErrorLevel, ErrorSolution, UserFriendlyError
from .smart_suggestions import SmartSuggestions


class ErrorFactory:
    """エラーファクトリークラス - 様々なエラータイプを生成"""

    @staticmethod
    def create_file_not_found_error(file_path: str) -> UserFriendlyError:
        """ファイル未発見エラー"""
        return UserFriendlyError(
            error_code="E001",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📁 ファイル '{file_path}' が見つかりません",
            solution=ErrorSolution(
                quick_fix="ファイル名とパスを確認してください",
                detailed_steps=[
                    "1. ファイル名のスペルミスがないか確認",
                    "2. ファイルが正しい場所に保存されているか確認",
                    "3. 拡張子が .txt になっているか確認",
                    "4. ファイルが他のアプリケーションで開かれていないか確認",
                ],
                alternative_approaches=[
                    "ファイルをKumihan-Formatterのフォルダにコピーして再実行",
                    "フルパス（絶対パス）で指定して実行",
                ],
            ),
            context={"file_path": file_path},
        )

    @staticmethod
    def create_encoding_error(file_path: str) -> UserFriendlyError:
        """エンコーディングエラー"""
        suggestions = SmartSuggestions.suggest_file_encoding(Path(file_path))

        return UserFriendlyError(
            error_code="E002",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.ENCODING,
            user_message=f"📝 文字化けを検出しました（ファイル: {Path(file_path).name}）",
            solution=ErrorSolution(
                quick_fix="テキストファイルをUTF-8形式で保存し直してください",
                detailed_steps=(
                    suggestions[:3]
                    if suggestions
                    else [
                        "テキストエディタでファイルを開く",
                        "文字エンコーディングをUTF-8に変更して保存",
                        "再度変換を実行",
                    ]
                ),
                external_links=["UTF-8とは: https://ja.wikipedia.org/wiki/UTF-8"],
            ),
            context={"file_path": file_path},
        )

    @staticmethod
    def create_syntax_error(line_num: int, invalid_content: str, file_path: str = None) -> UserFriendlyError:
        """記法エラー"""
        suggestions = SmartSuggestions.suggest_keyword(invalid_content.strip(";"))

        suggestion_text = ""
        if suggestions:
            suggestion_text = f"もしかして: {', '.join(suggestions[:3])}"

        return UserFriendlyError(
            error_code="E003",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.SYNTAX,
            user_message=f"✏️ {line_num}行目: 記法エラーを検出しました",
            solution=ErrorSolution(
                quick_fix=suggestion_text if suggestion_text else "Kumihan記法ガイドを確認してください",
                detailed_steps=[
                    "1. マーカーは ;;; で開始し、;;; で終了する必要があります",
                    "2. マーカーは行頭に記述してください",
                    "3. 有効なキーワードを使用してください",
                    "4. 複合記法の場合は + で連結してください",
                ],
                external_links=["記法ガイド: SPEC.md を参照"],
            ),
            context={
                "line_number": line_num,
                "invalid_content": invalid_content,
                "file_path": file_path,
                "suggestions": suggestions,
            },
        )

    @staticmethod
    def create_permission_error(file_path: str, operation: str = "アクセス") -> UserFriendlyError:
        """権限エラー"""
        return UserFriendlyError(
            error_code="E004",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.PERMISSION,
            user_message=f"🔒 ファイルに{operation}できません（権限エラー）",
            solution=ErrorSolution(
                quick_fix="ファイルが他のアプリケーションで開かれていないか確認してください",
                detailed_steps=[
                    "1. ファイルを開いているアプリケーションをすべて閉じる",
                    "2. ファイルの読み取り専用属性を確認・解除",
                    "3. 管理者権限で実行を試す",
                    "4. ファイルを別の場所にコピーして実行",
                ],
                alternative_approaches=["ファイルをデスクトップにコピーして変換", "別名でファイルを保存して再実行"],
            ),
            context={"file_path": file_path, "operation": operation},
        )

    @staticmethod
    def create_empty_file_error(file_path: str) -> UserFriendlyError:
        """空ファイルエラー"""
        return UserFriendlyError(
            error_code="E005",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📄 ファイルが空です（ファイル: {Path(file_path).name}）",
            solution=ErrorSolution(
                quick_fix="ファイルに変換したい内容を記述してください",
                detailed_steps=[
                    "1. テキストエディタでファイルを開く",
                    "2. 変換したい内容をKumihan記法で記述",
                    "3. UTF-8形式で保存",
                    "4. 再度変換を実行",
                ],
                external_links=["Kumihan記法の基本: SPEC.md を参照", "サンプルファイル: examples/ フォルダを参照"],
            ),
            context={"file_path": file_path},
        )

    @staticmethod
    def create_file_size_error(file_path: str, size_mb: float, max_size_mb: float = 10) -> UserFriendlyError:
        """ファイルサイズエラー"""
        return UserFriendlyError(
            error_code="E006",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📊 ファイルサイズが大きすぎます（{size_mb:.1f}MB > {max_size_mb}MB）",
            solution=ErrorSolution(
                quick_fix="ファイルサイズを小さくするか、分割してください",
                detailed_steps=[
                    "1. ファイルを複数の小さなファイルに分割",
                    "2. 不要な内容を削除",
                    "3. 画像参照がある場合は画像ファイルサイズを縮小",
                    "4. 分割したファイルを個別に変換",
                ],
            ),
            context={"file_path": file_path, "size_mb": size_mb, "max_size_mb": max_size_mb},
        )

    @staticmethod
    def create_unknown_error(original_error: str, context: Dict[str, Any] = None) -> UserFriendlyError:
        """不明なエラー"""
        return UserFriendlyError(
            error_code="E999",
            level=ErrorLevel.CRITICAL,
            category=ErrorCategory.UNKNOWN,
            user_message="🚨 予期しないエラーが発生しました",
            solution=ErrorSolution(
                quick_fix="GitHubのIssueで詳細を報告してください",
                detailed_steps=[
                    "1. エラーメッセージの全文をコピー",
                    "2. 使用していたファイルと操作手順を記録",
                    "3. GitHubのIssueページで新しいIssueを作成",
                    "4. エラー詳細と再現手順を記載して投稿",
                ],
                external_links=["Issue報告: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues"],
            ),
            technical_details=original_error,
            context=context or {},
        )


# 後方互換性のためのエイリアス
ErrorCatalog = ErrorFactory


# 便利な関数群
def create_syntax_error_from_validation(validation_error, file_path: str = None) -> UserFriendlyError:
    """バリデーションエラーからユーザーフレンドリーエラーを作成"""
    if hasattr(validation_error, "line_number") and hasattr(validation_error, "message"):
        return ErrorFactory.create_syntax_error(
            line_num=validation_error.line_number, invalid_content=validation_error.message, file_path=file_path
        )

    return ErrorFactory.create_unknown_error(str(validation_error))


def format_file_size_error(file_path: str, size_mb: float, max_size_mb: float = 10) -> UserFriendlyError:
    """ファイルサイズエラーをフォーマット"""
    return ErrorFactory.create_file_size_error(file_path, size_mb, max_size_mb)
