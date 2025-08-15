"""ファイル操作用バリデーター

統合されたファイル・パス検証機能
"""

import os
from pathlib import Path
from typing import List


class FileValidator:
    """ファイル検証クラス"""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate_readable(self, path: Path) -> bool:
        """読み込み可能かの検証"""
        self._errors.clear()

        if not path.exists():
            self._errors.append(f"ファイルが存在しません: {path}")
            return False

        if not path.is_file():
            self._errors.append(f"ファイルではありません: {path}")
            return False

        if not os.access(path, os.R_OK):
            self._errors.append(f"読み込み権限がありません: {path}")
            return False

        return True

    def validate_writable(self, path: Path) -> bool:
        """書き込み可能かの検証"""
        self._errors.clear()

        # 親ディレクトリの存在確認
        parent = path.parent
        if not parent.exists():
            self._errors.append(f"親ディレクトリが存在しません: {parent}")
            return False

        # 既存ファイルの場合は書き込み権限確認
        if path.exists():
            if not path.is_file():
                self._errors.append(f"ファイルではありません: {path}")
                return False

            if not os.access(path, os.W_OK):
                self._errors.append(f"書き込み権限がありません: {path}")
                return False
        else:
            # 新規ファイルの場合は親ディレクトリの書き込み権限確認
            if not os.access(parent, os.W_OK):
                self._errors.append(
                    f"親ディレクトリに書き込み権限がありません: {parent}"
                )
                return False

        return True

    def validate_file_size(self, path: Path, max_size_mb: int = 100) -> bool:
        """ファイルサイズの検証"""
        if not path.exists():
            self._errors.append(f"ファイルが存在しません: {path}")
            return False

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            self._errors.append(
                f"ファイルサイズが上限を超えています: {size_mb:.1f}MB > {max_size_mb}MB"
            )
            return False

        return True

    def get_errors(self) -> List[str]:
        """エラーメッセージを取得"""
        return self._errors.copy()


class PathValidator:
    """パス検証クラス"""

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate_path_format(self, path: str) -> bool:
        """パス形式の検証"""
        self._errors.clear()

        if not path:
            self._errors.append("パスが空です")
            return False

        # 禁止文字のチェック
        forbidden_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in forbidden_chars:
            if char in path:
                self._errors.append(f"禁止文字が含まれています: {char}")
                return False

        # パス長のチェック（Windows制限考慮）
        if len(path) > 260:
            self._errors.append(f"パスが長すぎます: {len(path)} > 260文字")
            return False

        return True

    def validate_extension(self, path: Path, allowed_extensions: List[str]) -> bool:
        """拡張子の検証"""
        self._errors.clear()

        extension = path.suffix.lower()
        allowed_extensions = [ext.lower() for ext in allowed_extensions]

        if extension not in allowed_extensions:
            self._errors.append(
                f"許可されていない拡張子です: {extension} "
                f"(許可: {', '.join(allowed_extensions)})"
            )
            return False

        return True

    def validate_path_safety(self, path: Path, base_dir: Path) -> bool:
        """パスの安全性検証（ディレクトリトラバーサル対策）"""
        self._errors.clear()

        try:
            resolved_path = path.resolve()
            resolved_base = base_dir.resolve()

            # ベースディレクトリ配下かどうかチェック
            if not str(resolved_path).startswith(str(resolved_base)):
                self._errors.append(
                    f"許可されていないディレクトリです: {resolved_path}"
                )
                return False

        except (OSError, ValueError) as e:
            self._errors.append(f"パスの解決に失敗しました: {e}")
            return False

        return True

    def validate_input_file(self, path: Path) -> bool:
        """入力ファイルの検証（既存コード互換）"""
        self._errors.clear()

        if not self.validate_path_format(str(path)):
            return False

        if not path.exists():
            self._errors.append(f"ファイルが存在しません: {path}")
            return False

        if not path.is_file():
            self._errors.append(f"ファイルではありません: {path}")
            return False

        return True

    def get_errors(self) -> List[str]:
        """エラーメッセージを取得"""
        return self._errors.copy()
