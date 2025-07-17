"""
ファイル操作 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - file_operations.py分割
"""

from .file_io_handler import FileIOHandler

# 分割されたモジュールからインポート
from .file_operations_core import FileOperationsCore
from .file_operations_factory import (
    FileOperationsComponents,
    create_file_io_handler,
    create_file_operations,
    create_file_path_utilities,
)
from .file_path_utilities import FilePathUtilities


class FileOperations(FileOperationsCore):
    """
    File operations utility class with unified interface

    Provides backward compatibility by inheriting from FileOperationsCore
    and adding static methods from other components.
    """

    # 静的メソッドを委譲して後方互換性を確保
    load_distignore_patterns = FilePathUtilities.load_distignore_patterns
    should_exclude = FilePathUtilities.should_exclude
    get_file_size_info = FilePathUtilities.get_file_size_info
    estimate_processing_time = FilePathUtilities.estimate_processing_time

    write_text_file = FileIOHandler.write_text_file
    read_text_file = FileIOHandler.read_text_file


# モジュールレベルのエクスポート
__all__ = [
    "FileOperations",
    "FileOperationsCore",
    "FilePathUtilities",
    "FileIOHandler",
    "create_file_operations",
    "create_file_path_utilities",
    "create_file_io_handler",
    "FileOperationsComponents",
]
