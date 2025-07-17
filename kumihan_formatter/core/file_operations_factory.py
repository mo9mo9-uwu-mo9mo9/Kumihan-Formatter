"""
ファイル操作 ファクトリー

ファイル操作関連コンポーネントの作成・初期化
Issue #492 Phase 5A - file_operations.py分割
"""

from typing import Optional

from .file_io_handler import FileIOHandler
from .file_operations_core import FileOperationsCore
from .file_path_utilities import FilePathUtilities
from .file_protocol import UIProtocol


def create_file_operations(ui: Optional[UIProtocol] = None) -> FileOperationsCore:
    """ファイル操作コア作成"""
    return FileOperationsCore(ui)


def create_file_path_utilities() -> FilePathUtilities:
    """ファイルパスユーティリティ作成"""
    return FilePathUtilities()


def create_file_io_handler() -> FileIOHandler:
    """ファイルI/Oハンドラー作成"""
    return FileIOHandler()


class FileOperationsComponents:
    """ファイル操作関連コンポーネントの統合管理"""

    def __init__(self, ui: Optional[UIProtocol] = None):
        self.ui = ui
        self._core: Optional[FileOperationsCore] = None
        self._path_utils: Optional[FilePathUtilities] = None
        self._io_handler: Optional[FileIOHandler] = None

    @property
    def core(self) -> FileOperationsCore:
        """ファイル操作コア取得（遅延初期化）"""
        if self._core is None:
            self._core = create_file_operations(self.ui)
        return self._core

    @property
    def path_utils(self) -> FilePathUtilities:
        """ファイルパスユーティリティ取得（遅延初期化）"""
        if self._path_utils is None:
            self._path_utils = create_file_path_utilities()
        return self._path_utils

    @property
    def io_handler(self) -> FileIOHandler:
        """ファイルI/Oハンドラー取得（遅延初期化）"""
        if self._io_handler is None:
            self._io_handler = create_file_io_handler()
        return self._io_handler
