"""
ファイル系エラーの回復戦略 - Issue #401対応

ファイルエンコーディング、権限、未発見エラーの回復戦略。
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..error_types import ErrorCategory, UserFriendlyError
from .base import RecoveryStrategy


class FileEncodingRecoveryStrategy(RecoveryStrategy):
    """ファイルエンコーディングエラーの回復戦略"""

    def __init__(self) -> None:
        super().__init__("FileEncodingRecovery", priority=2)
        self.encoding_candidates = [
            "utf-8",
            "shift_jis",
            "cp932",
            "euc-jp",
            "iso-2022-jp",
        ]

    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """エンコーディングエラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.ENCODING
            or "encoding" in error.error_code.lower()
            or "文字化け" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """エンコーディング自動検出・変換による回復"""
        file_path = context.get("file_path")
        if not file_path or not Path(file_path).exists():
            return False, "対象ファイルが見つかりません"

        self.logger.info(f"Attempting encoding recovery for: {file_path}")

        try:
            # 各エンコーディングで読み取りを試行
            for encoding in self.encoding_candidates:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()

                    # UTF-8で一時ファイルを作成
                    temp_file = Path(file_path).with_suffix(".utf8.tmp")
                    with open(temp_file, "w", encoding="utf-8") as f:
                        f.write(content)

                    # 元ファイルをバックアップ
                    backup_file = Path(file_path).with_suffix(".backup")
                    shutil.copy2(file_path, backup_file)

                    # UTF-8版で置き換え
                    shutil.move(str(temp_file), file_path)

                    self.logger.info(
                        f"Successfully converted {file_path} from {encoding} to UTF-8"
                    )
                    return (
                        True,
                        f"ファイルを{encoding}からUTF-8に自動変換しました（バックアップ: {backup_file.name}）",
                    )

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.warning(f"Failed to convert with {encoding}: {e}")
                    continue

            return False, "サポートされているエンコーディングでの読み取りに失敗しました"

        except Exception as e:
            self.logger.error(f"Encoding recovery failed: {e}")
            return False, f"エンコーディング回復に失敗: {str(e)}"


class FilePermissionRecoveryStrategy(RecoveryStrategy):
    """ファイル権限エラーの回復戦略"""

    def __init__(self) -> None:
        super().__init__("FilePermissionRecovery", priority=3)

    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """権限エラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.PERMISSION
            or "permission" in error.error_code.lower()
            or "権限" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """一時ファイルでの処理継続による回復"""
        file_path = context.get("file_path")
        if not file_path:
            return False, "対象ファイルが指定されていません"

        self.logger.info(f"Attempting permission recovery for: {file_path}")

        try:
            original_path = Path(file_path)

            # 一時ディレクトリに読み取り可能なコピーを作成
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / original_path.name

                try:
                    # ファイルコピーを試行
                    shutil.copy2(original_path, temp_file)

                    # 一時ファイルの権限を設定
                    temp_file.chmod(0o644)

                    # コンテキストを更新（後続処理で一時ファイルを使用）
                    context["original_file_path"] = file_path
                    context["file_path"] = str(temp_file)
                    context["temp_file_recovery"] = True

                    self.logger.info(f"Created temporary accessible copy: {temp_file}")
                    return True, f"一時ファイルでの処理を継続します: {temp_file.name}"

                except Exception as copy_error:
                    self.logger.warning(
                        f"Failed to create temporary copy: {copy_error}"
                    )

                    # 読み取り専用でもコンテンツが取得できるか試行
                    try:
                        content = original_path.read_text()
                        temp_file.write_text(content)

                        context["original_file_path"] = file_path
                        context["file_path"] = str(temp_file)
                        context["temp_file_recovery"] = True

                        return (
                            True,
                            f"読み取り専用モードで一時ファイルを作成しました: {temp_file.name}",
                        )

                    except Exception as read_error:
                        self.logger.error(f"Failed to read file content: {read_error}")
                        return False, "ファイルの読み取りに失敗しました"

        except Exception as e:
            self.logger.error(f"Permission recovery failed: {e}")
            return False, f"権限回復に失敗: {str(e)}"


class FileNotFoundRecoveryStrategy(RecoveryStrategy):
    """ファイル未発見エラーの回復戦略"""

    def __init__(self) -> None:
        super().__init__("FileNotFoundRecovery", priority=3)

    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """ファイル未発見エラーを処理できるかチェック"""
        return error.category == ErrorCategory.FILE_SYSTEM and (
            "not found" in error.error_code.lower()
            or "見つかりません" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """類似ファイル名の検索による回復"""
        file_path = context.get("file_path")
        if not file_path:
            return False, "対象ファイルパスが指定されていません"

        self.logger.info(f"Attempting file recovery for: {file_path}")

        try:
            path = Path(file_path)
            parent_dir = path.parent
            target_name = path.name

            if not parent_dir.exists():
                return False, "親ディレクトリが存在しません"

            # 類似ファイルを検索
            similar_files = self._find_similar_files(parent_dir, target_name)

            if similar_files:
                best_match = similar_files[0]

                # コンテキストを更新
                context["original_file_path"] = file_path
                context["file_path"] = str(best_match)
                context["file_recovery"] = True

                self.logger.info(f"Found similar file: {best_match}")
                return True, f"類似ファイルで処理を継続します: {best_match.name}"

            return False, "類似ファイルが見つかりませんでした"

        except Exception as e:
            self.logger.error(f"File recovery failed: {e}")
            return False, f"ファイル回復に失敗: {str(e)}"

    def _find_similar_files(self, directory: Path, target_name: str) -> list[Path]:
        """類似ファイル名を検索"""
        import difflib

        similar_files = []
        target_stem = Path(target_name).stem.lower()
        target_suffix = Path(target_name).suffix.lower()

        for file_path in directory.iterdir():
            if file_path.is_file():
                file_stem = file_path.stem.lower()
                file_suffix = file_path.suffix.lower()

                # 拡張子が同じまたは.txt
                if file_suffix == target_suffix or file_suffix == ".txt":
                    # ファイル名の類似度を計算
                    similarity = difflib.SequenceMatcher(
                        None, target_stem, file_stem
                    ).ratio()
                    if similarity > 0.6:  # 60%以上の類似度
                        similar_files.append((similarity, file_path))

        # 類似度でソート
        similar_files.sort(key=lambda x: x[0], reverse=True)
        return [file_path for _, file_path in similar_files[:3]]
