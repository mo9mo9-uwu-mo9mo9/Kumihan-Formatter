"""統合ファイル操作マネージャー

すべてのファイル操作の統一エントリーポイント
"""

from pathlib import Path
from typing import Any, Dict, List

from .operations import FileOperations, PathOperations
from .validators import FileValidator, PathValidator


class FileManager:
    """統合ファイル操作マネージャー

    すべてのファイル操作機能を統合したファサードクラス
    既存のfile_operations*.py系統の機能をすべて包含
    """

    def __init__(self) -> None:
        self.file_ops = FileOperations()
        self.path_ops = PathOperations()
        self.file_validator = FileValidator()
        self.path_validator = PathValidator()

    # ファイル読み書き操作
    def read_file(self, path: str | Path, encoding: str = "utf-8") -> str:
        """ファイル読み込み（統一インターフェース）"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.read_text(path, encoding)

    def write_file(
        self, path: str | Path, content: str, encoding: str = "utf-8"
    ) -> None:
        """ファイル書き込み（統一インターフェース）"""
        path = self.path_ops.resolve_path(path)
        self.file_ops.write_text(path, content, encoding)

    def read_binary(self, path: str | Path) -> bytes:
        """バイナリファイル読み込み"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.read_binary(path)

    def write_binary(self, path: str | Path, data: bytes) -> None:
        """バイナリファイル書き込み"""
        path = self.path_ops.resolve_path(path)
        self.file_ops.write_binary(path, data)

    # ファイル操作
    def copy_file(self, src: str | Path, dst: str | Path) -> None:
        """ファイルコピー"""
        src_path = self.path_ops.resolve_path(src)
        dst_path = self.path_ops.resolve_path(dst)
        self.file_ops.copy_file(src_path, dst_path)

    def move_file(self, src: str | Path, dst: str | Path) -> None:
        """ファイル移動"""
        src_path = self.path_ops.resolve_path(src)
        dst_path = self.path_ops.resolve_path(dst)
        self.file_ops.move_file(src_path, dst_path)

    def delete_file(self, path: str | Path) -> None:
        """ファイル削除"""
        path = self.path_ops.resolve_path(path)
        self.file_ops.delete_file(path)

    # 存在確認・情報取得
    def exists(self, path: str | Path) -> bool:
        """ファイル/ディレクトリの存在確認"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.exists(path)

    def is_file(self, path: str | Path) -> bool:
        """ファイルかどうかの確認"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.is_file(path)

    def is_directory(self, path: str | Path) -> bool:
        """ディレクトリかどうかの確認"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.is_dir(path)

    def get_file_info(self, path: str | Path) -> Dict[str, Any]:
        """ファイル情報取得"""
        path = self.path_ops.resolve_path(path)
        return self.file_ops.get_file_info(path)

    def list_files(
        self, directory: str | Path, pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """ディレクトリ内のファイル一覧取得"""
        directory = self.path_ops.resolve_path(directory)
        return self.file_ops.list_files(directory, pattern, recursive)

    # パス操作
    def resolve_path(self, path: str | Path) -> Path:
        """パスの正規化・解決"""
        return self.path_ops.resolve_path(path)

    def ensure_directory(self, path: str | Path) -> None:
        """ディレクトリの作成（存在しない場合）"""
        path = self.path_ops.resolve_path(path)
        self.path_ops.ensure_parent_dir(path / "dummy")  # parent作成のためのダミー

    def get_relative_path(self, path: str | Path, base: str | Path) -> Path:
        """相対パス取得"""
        path = self.path_ops.resolve_path(path)
        base = self.path_ops.resolve_path(base)
        return self.path_ops.get_relative_path(path, base)

    def join_paths(self, *parts: str) -> Path:
        """パス結合"""
        return self.path_ops.join_paths(*parts)

    def get_safe_filename(self, filename: str) -> str:
        """安全なファイル名生成"""
        return self.path_ops.get_safe_filename(filename)

    # 検証機能
    def validate_readable(self, path: str | Path) -> tuple[bool, List[str]]:
        """読み込み可能性の検証"""
        path = self.path_ops.resolve_path(path)
        result = self.file_validator.validate_readable(path)
        errors = self.file_validator.get_errors()
        return result, errors

    def validate_writable(self, path: str | Path) -> tuple[bool, List[str]]:
        """書き込み可能性の検証"""
        path = self.path_ops.resolve_path(path)
        result = self.file_validator.validate_writable(path)
        errors = self.file_validator.get_errors()
        return result, errors

    def validate_file_size(
        self, path: str | Path, max_size_mb: int = 100
    ) -> tuple[bool, List[str]]:
        """ファイルサイズの検証"""
        path = self.path_ops.resolve_path(path)
        result = self.file_validator.validate_file_size(path, max_size_mb)
        errors = self.file_validator.get_errors()
        return result, errors

    def validate_extension(
        self, path: str | Path, allowed_extensions: List[str]
    ) -> tuple[bool, List[str]]:
        """拡張子の検証"""
        path = self.path_ops.resolve_path(path)
        result = self.path_validator.validate_extension(path, allowed_extensions)
        errors = self.path_validator.get_errors()
        return result, errors

    def validate_path_safety(
        self, path: str | Path, base_dir: str | Path
    ) -> tuple[bool, List[str]]:
        """パス安全性の検証"""
        path = self.path_ops.resolve_path(path)
        base_dir = self.path_ops.resolve_path(base_dir)
        result = self.path_validator.validate_path_safety(path, base_dir)
        errors = self.path_validator.get_errors()
        return result, errors

    # 便利メソッド
    def ensure_file_writable(self, path: str | Path) -> Path:
        """書き込み可能なファイルパスの確保"""
        path = self.path_ops.resolve_path(path)
        self.path_ops.ensure_parent_dir(path)
        return path

    def backup_file(self, path: str | Path, suffix: str = ".backup") -> Path:
        """ファイルのバックアップ作成"""
        path = self.path_ops.resolve_path(path)
        if not self.file_ops.exists(path):
            raise FileNotFoundError(f"バックアップ対象ファイルが存在しません: {path}")

        backup_path = path.with_suffix(path.suffix + suffix)
        self.file_ops.copy_file(path, backup_path)
        return backup_path

    def create_temp_file(
        self, directory: str | Path, prefix: str = "temp_", suffix: str = ".tmp"
    ) -> Path:
        """一時ファイルの作成"""
        import time

        directory = self.path_ops.resolve_path(directory)
        self.path_ops.ensure_parent_dir(directory / "dummy")

        timestamp = str(int(time.time() * 1000))
        filename = f"{prefix}{timestamp}{suffix}"
        temp_path = directory / filename

        # 空ファイル作成
        self.file_ops.write_text(temp_path, "")
        return temp_path
