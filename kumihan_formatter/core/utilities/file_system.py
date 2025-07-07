"""File system utilities

This module provides file system operation utilities including
directory management, file hashing, and safe filename generation.
"""

import hashlib
from pathlib import Path
from typing import Iterator


class FileSystemHelper:
    """File system operation utilities"""

    @staticmethod
    def ensure_directory(path: str | Path) -> Path:
        """Ensure directory exists, create if necessary"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_hash(file_path: str | Path, algorithm: str = "md5") -> str:
        """Get file hash for change detection"""
        hash_func = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    @staticmethod
    def get_safe_filename(filename: str, replacement: str = "_") -> str:
        """Get safe filename by replacing invalid characters"""
        # Characters that are problematic in filenames
        invalid_chars = r'<>:"/\\|?*'
        safe_name = filename

        for char in invalid_chars:
            safe_name = safe_name.replace(char, replacement)

        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip(". ")

        # Ensure it's not empty
        if not safe_name:
            safe_name = "untitled"

        return safe_name

    @staticmethod
    def find_files(
        directory: str | Path, pattern: str = "*", recursive: bool = True
    ) -> Iterator[Path]:
        """Find files matching pattern"""
        directory = Path(directory)

        if recursive:
            return directory.rglob(pattern)
        else:
            return directory.glob(pattern)
