"""ファイル操作統合インターフェース - 後方互換性

分割されたファイル操作モジュールの統合インターフェース。
既存コードとの互換性を維持。
"""

# 後方互換性のためのインポート
from .file_operations import FileOperations
from .file_protocol import UIProtocol
from .file_validators import ErrorHandler, PathValidator

__all__ = ["FileOperations", "UIProtocol", "ErrorHandler", "PathValidator"]
