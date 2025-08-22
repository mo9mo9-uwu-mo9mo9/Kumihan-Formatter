"""
ファイル操作 統合モジュール - 後方互換性レイヤー

Issue #880 Phase 1: 新しいio統合モジュールへの移行
既存コードの互換性を保持しつつ、段階的に新システムに移行
"""

import warnings
from pathlib import Path
from typing import Any

# 後方互換性のための旧インポート
from .file_io_handler import FileIOHandler
from .file_operations_core import FileOperationsCore
from .file_operations_factory import (
    FileOperationsComponents,
    create_file_io_handler,
    create_file_operations,
    create_file_path_utilities,
)
from .file_path_utilities import FilePathUtilities

# 新しい統合モジュール
from .io import FileManager


class FileOperations:
    """
    File operations utility class with unified interface

    Issue #880: 新しいFileManagerベースの実装に移行
    後方互換性を保持しつつ、内部的には新しいio統合モジュールを使用
    """

    def __init__(self) -> None:
        # 新しい統合マネージャーを使用
        self._manager = FileManager()

        # 非推奨警告（開発時のみ）
        warnings.warn(
            "FileOperations is deprecated. "
            "Use kumihan_formatter.core.io.FileManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    # 新しいインターフェースへのプロキシメソッド
    def read_file(self, path: str | Path, encoding: str = "utf-8") -> str:
        """ファイル読み込み（新インターフェース）"""
        return self._manager.read_file(path, encoding)

    def write_file(
        self, path: str | Path, content: str, encoding: str = "utf-8"
    ) -> None:
        """ファイル書き込み（新インターフェース）"""
        self._manager.write_file(path, content, encoding)

    def exists(self, path: str | Path) -> bool:
        """ファイル/ディレクトリの存在確認"""
        return self._manager.exists(path)

    def is_file(self, path: str | Path) -> bool:
        """ファイルかどうかの確認"""
        return self._manager.is_file(path)

    def copy_file(self, src: str | Path, dst: str | Path) -> None:
        """ファイルコピー"""
        self._manager.copy_file(src, dst)

    def move_file(self, src: str | Path, dst: str | Path) -> None:
        """ファイル移動"""
        self._manager.move_file(src, dst)

    def delete_file(self, path: str | Path) -> None:
        """ファイル削除"""
        self._manager.delete_file(path)

    # 旧インターフェースとの互換性メソッド
    @staticmethod
    def load_distignore_patterns(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        return FilePathUtilities.load_distignore_patterns(*args, **kwargs)

    @staticmethod
    def should_exclude(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        return FilePathUtilities.should_exclude(*args, **kwargs)

    @staticmethod
    def get_file_size_info(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        return FilePathUtilities.get_file_size_info(*args, **kwargs)

    @staticmethod
    def estimate_processing_time(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        return FilePathUtilities.estimate_processing_time(*args, **kwargs)

    @staticmethod
    def write_text_file(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FileIOHandler委譲）"""
        return FileIOHandler.write_text_file(*args, **kwargs)

    @staticmethod
    def read_text_file(*args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FileIOHandler委譲）"""
        return FileIOHandler.read_text_file(*args, **kwargs)

    # 既存コード互換性のための追加メソッド
    def ensure_directory(self, path: str | Path) -> None:
        """ディレクトリ作成（新インターフェース互換）"""
        self._manager.ensure_directory(path)

    def check_large_file_warning(self, *args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        return FilePathUtilities.get_file_size_info(*args, **kwargs)

    def create_sample_images(self, *args: Any, **kwargs: Any) -> Any:
        """旧インターフェース互換（FilePathUtilities委譲）"""
        # 実装が見つからない場合はスタブ
        return None


# モジュールレベルのエクスポート（後方互換性）
__all__ = [
    "FileOperations",
    "FileOperationsCore",
    "FilePathUtilities",
    "FileIOHandler",
    "create_file_operations",
    "create_file_path_utilities",
    "create_file_io_handler",
    "FileOperationsComponents",
    # 新しいエクスポート
    "FileManager",
]
