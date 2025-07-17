"""ファイル操作バリデーション・エラーハンドリング

パスの検証とエラー処理を専門に扱うモジュール。
"""

from pathlib import Path

from .file_protocol import UIProtocol
from .utilities.logger import get_logger


class PathValidator:
    """Path validation utilities"""

    @staticmethod
    def validate_input_file(file_path: str) -> Path:
        """Validate input file exists and is readable"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Input path is not a file: {file_path}")
        return path

    @staticmethod
    def validate_output_directory(dir_path: str) -> Path:
        """Validate output directory and create if needed"""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def validate_source_directory(dir_path: str) -> Path:
        """Validate source directory exists"""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Source directory not found: {dir_path}")
        if not path.is_dir():
            raise ValueError(f"Source path is not a directory: {dir_path}")
        return path


class ErrorHandler:
    """Centralized error handling for file operations"""

    def __init__(self, ui: UIProtocol | None = None):
        """Initialize with optional UI instance"""
        self.ui = ui
        self.logger = get_logger(__name__)
        self.logger.debug("ErrorHandler initialized")

    def handle_file_not_found(self, file_path: str) -> None:
        """Handle file not found error"""
        self.logger.error(f"File not found: {file_path}")
        if self.ui:
            self.ui.file_error(file_path, "ファイルが見つかりません")

    def handle_encoding_error(self, file_path: str, encoding: str = "utf-8") -> None:
        """Handle encoding error with helpful suggestions"""
        self.logger.error(f"Encoding error in file: {file_path} (tried: {encoding})")
        if self.ui:
            self.ui.encoding_error(file_path)
            self.ui.hint(
                "エンコーディングの問題を解決するには:",
                "1. ファイルをUTF-8で保存し直してください\n"
                "   2. テキストエディタで開き、「UTF-8」として保存\n"
                "   3. Windowsの場合は「UTF-8 (BOM付き)」も試してください",
            )

    def handle_permission_error(self, error: str) -> None:
        """Handle permission error"""
        self.logger.error(f"Permission error: {error}")
        if self.ui:
            self.ui.permission_error(error)

    def handle_unexpected_error(self, error: str) -> None:
        """Handle unexpected error"""
        self.logger.error(f"Unexpected error: {error}")
        if self.ui:
            self.ui.unexpected_error(error)
