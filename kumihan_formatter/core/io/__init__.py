"""統合ファイル操作モジュール

Issue #880 Phase 1: 分散していたファイル操作機能を統合
- file_operations*.py系統
- file_io_handler.py
- file_ops.py
- file_validators.py
- file_path_utilities.py
- utilities/file_system.py

すべてをこのモジュールに統合し、明確なインターフェースを提供
"""

from .manager import FileManager
from .operations import FileOperations
from .protocols import FileProtocol, PathProtocol
from .validators import FileValidator, PathValidator

__all__ = [
    "FileManager",
    "FileOperations",
    "FileProtocol",
    "PathProtocol",
    "FileValidator",
    "PathValidator",
]
