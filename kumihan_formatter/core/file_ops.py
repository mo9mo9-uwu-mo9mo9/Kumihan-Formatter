"""ファイル操作統合インターフェース - 後方互換性

Issue #880 Phase 1: 新しいio統合モジュールへの移行
分割されたファイル操作モジュールの統合インターフェース。
既存コードとの互換性を維持。
"""

import warnings
from pathlib import Path
from typing import Any

# 後方互換性のためのインポート（非推奨）
from .file_protocol import UIProtocol
from .file_validators import ErrorHandler

# 新しい統合モジュール（推奨）
from .io import FileManager, FileProtocol, FileValidator, PathProtocol, PathValidator


# 非推奨警告付きの後方互換エイリアス
class FileOperations:
    """後方互換性のためのFileOperationsラッパー"""

    def __init__(self, ui: Any = None) -> None:
        # uiパラメータを受け入れるが無視（後方互換）
        self._manager = FileManager()
        warnings.warn(
            "file_ops.FileOperations is deprecated. "
            "Use kumihan_formatter.core.io.FileManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def ensure_directory(self, path: str | Path) -> None:
        """ディレクトリ作成"""
        self._manager.ensure_directory(path)

    def check_large_file_warning(self, *args: Any, **kwargs: Any) -> Any:
        """大きなファイル警告チェック（スタブ）"""
        return None

    def create_sample_images(self, *args: Any, **kwargs: Any) -> Any:
        """サンプル画像作成（スタブ）"""
        return None


# エクスポート（新旧両対応）
__all__ = [
    # 推奨（新）
    "FileManager",
    "FileProtocol",
    "PathProtocol",
    "FileValidator",
    "PathValidator",
    # 後方互換性（旧）
    "FileOperations",
    "UIProtocol",
    "ErrorHandler",
]
