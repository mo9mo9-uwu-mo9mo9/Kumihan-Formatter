"""File operations and utilities for Kumihan-Formatter

This module contains file handling logic, validation, and utilities
that are shared across different parts of the application.
"""

import os
import shutil
import fnmatch
import base64
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Protocol


class UIProtocol(Protocol):
    """UI interface protocol to avoid circular dependency"""
    def warning(self, message: str, details: str = None) -> None: ...
    def file_copied(self, count: int) -> None: ...
    def files_missing(self, files: list) -> None: ...
    def duplicate_files(self, duplicates: dict) -> None: ...
    def info(self, message: str, details: str = None) -> None: ...
    def hint(self, message: str, details: str = None) -> None: ...
    def file_error(self, file_path: str, message: str) -> None: ...
    def encoding_error(self, file_path: str) -> None: ...
    def permission_error(self, error: str) -> None: ...
    def unexpected_error(self, error: str) -> None: ...


class FileOperations:
    """File operations utility class"""
    
    def __init__(self, ui: Optional[UIProtocol] = None):
        """Initialize with optional UI instance for dependency injection"""
        self.ui = ui
    
    @staticmethod
    def load_distignore_patterns() -> List[str]:
        """
        Load exclusion patterns from .distignore file
        
        Returns:
            list: List of exclusion patterns
        """
        patterns = []
        distignore_path = Path(".distignore")
        
        if distignore_path.exists():
            with open(distignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comment lines and empty lines
                    if line and not line.startswith("#"):
                        patterns.append(line)
        
        return patterns

    @staticmethod
    def should_exclude(path: Path, patterns: List[str], base_path: Path) -> bool:
        """
        Check if the specified path matches exclusion patterns
        
        Args:
            path: Path to check
            patterns: List of exclusion patterns
            base_path: Base path for relative calculation
        
        Returns:
            bool: True if should be excluded
        """
        relative_path = path.relative_to(base_path)
        relative_str = str(relative_path)
        
        for pattern in patterns:
            # Directory pattern handling
            if pattern.endswith('/'):
                # Check files under directory
                dir_pattern = pattern.rstrip('/')
                
                # Complete path matching
                if relative_str.startswith(dir_pattern + '/') or relative_str == dir_pattern:
                    return True
                
                # Partial matching (directory name)
                for part in relative_path.parts:
                    if fnmatch.fnmatch(part, dir_pattern):
                        return True
            else:
                # File pattern handling
                if fnmatch.fnmatch(relative_str, pattern):
                    return True
                # Match by filename only
                if fnmatch.fnmatch(path.name, pattern):
                    return True
        
        return False

    def copy_images(self, input_path: Path, output_path: Path, ast: List[Any]) -> None:
        """Copy image files to output directory"""
        # Extract image nodes from AST
        image_nodes = [node for node in ast if getattr(node, 'type', None) == 'image']
        
        if not image_nodes:
            return
        
        # Check images folder in input file directory
        source_images_dir = input_path.parent / "images"
        
        if not source_images_dir.exists():
            if self.ui:
                self.ui.warning(f"images フォルダが見つかりません: {source_images_dir}")
            return
        
        # Create output images directory
        dest_images_dir = output_path / "images"
        dest_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy each image file
        copied_files = []
        missing_files = []
        duplicate_files = {}
        
        for node in image_nodes:
            filename = node.content
            source_file = source_images_dir / filename
            dest_file = dest_images_dir / filename
            
            if source_file.exists():
                # Check for filename duplicates
                if filename in copied_files:
                    if filename not in duplicate_files:
                        duplicate_files[filename] = 2
                    else:
                        duplicate_files[filename] += 1
                else:
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(filename)
            else:
                missing_files.append(filename)
        
        # Report results
        if copied_files and self.ui:
            self.ui.file_copied(len(copied_files))
        
        if missing_files and self.ui:
            self.ui.files_missing(missing_files)
        
        if duplicate_files and self.ui:
            self.ui.duplicate_files(duplicate_files)

    @staticmethod
    def create_sample_images(images_dir: Path, sample_images: Dict[str, str]) -> None:
        """Create sample images from base64 data"""
        images_dir.mkdir(exist_ok=True)
        
        for filename, base64_data in sample_images.items():
            image_path = images_dir / filename
            image_data = base64.b64decode(base64_data)
            with open(image_path, "wb") as f:
                f.write(image_data)

    @staticmethod
    def copy_directory_with_exclusions(source_path: Path, dest_path: Path, 
                                     exclude_patterns: List[str]) -> Tuple[int, int]:
        """
        Copy directory contents with exclusion patterns
        
        Args:
            source_path: Source directory
            dest_path: Destination directory
            exclude_patterns: List of exclusion patterns
        
        Returns:
            tuple: (copied_count, excluded_count)
        """
        copied_count = 0
        excluded_count = 0
        
        for item in source_path.rglob("*"):
            if item.is_file():
                # Exclusion check
                if FileOperations.should_exclude(item, exclude_patterns, source_path):
                    excluded_count += 1
                    continue
                
                relative_path = item.relative_to(source_path)
                dest_file = dest_path / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                copied_count += 1
        
        return copied_count, excluded_count

    @staticmethod
    def find_preview_file(directory: Path) -> Optional[Path]:
        """
        Find a suitable preview file in the directory
        
        Args:
            directory: Directory to search
        
        Returns:
            Path to preview file or None if not found
        """
        preview_files = ["index.html", "README.html", "readme.html"]
        for filename in preview_files:
            candidate = directory / filename
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Ensure directory exists"""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write_text_file(path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text file with proper encoding"""
        with open(path, "w", encoding=encoding) as f:
            f.write(content)

    @staticmethod
    def read_text_file(path: Path, encoding: str = "utf-8") -> str:
        """Read text file with proper encoding"""
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def get_file_size_info(path: Path) -> Dict[str, Any]:
        """Get file size information"""
        if path.exists():
            size = path.stat().st_size
            return {
                'size_bytes': size,
                'size_mb': size / (1024 * 1024),
                'size_formatted': f"{size:,}",
                'is_large': size > 10 * 1024 * 1024  # 10MB以上
            }
        return {'size_bytes': 0, 'size_mb': 0.0, 'size_formatted': '0', 'is_large': False}

    def check_large_file_warning(self, path: Path, max_size_mb: float = 50.0) -> bool:
        """
        大規模ファイルの警告表示とユーザー確認
        
        Args:
            path: チェック対象ファイル
            max_size_mb: 警告を表示するサイズ（MB）
            
        Returns:
            bool: 続行するかどうか
        """
        size_info = self.get_file_size_info(path)
        
        if size_info['size_mb'] > max_size_mb:
            if self.ui:
                self.ui.warning(
                    f"大規模ファイルを検出: {size_info['size_mb']:.1f}MB",
                    f"処理に時間がかかる可能性があります（推奨: {max_size_mb}MB以下）"
                )
                
                # 自動的に続行（バッチ処理対応）
                self.ui.info("大規模ファイル処理を開始します")
            return True
        
        return True

    @staticmethod
    def estimate_processing_time(size_mb: float) -> str:
        """
        ファイルサイズから処理時間を推定
        
        Args:
            size_mb: ファイルサイズ（MB）
            
        Returns:
            str: 推定時間の説明
        """
        if size_mb < 1:
            return "数秒"
        elif size_mb < 10:
            return "10-30秒"
        elif size_mb < 50:
            return "1-3分"
        else:
            return "3分以上"


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
    
    def __init__(self, ui: Optional[UIProtocol] = None):
        """Initialize with optional UI instance"""
        self.ui = ui
    
    def handle_file_not_found(self, file_path: str) -> None:
        """Handle file not found error"""
        if self.ui:
            self.ui.file_error(file_path, "ファイルが見つかりません")
    
    def handle_encoding_error(self, file_path: str) -> None:
        """Handle encoding error"""
        if self.ui:
            self.ui.encoding_error(file_path)
    
    def handle_permission_error(self, error: str) -> None:
        """Handle permission error"""
        if self.ui:
            self.ui.permission_error(error)
    
    def handle_unexpected_error(self, error: str) -> None:
        """Handle unexpected error"""
        if self.ui:
            self.ui.unexpected_error(error)