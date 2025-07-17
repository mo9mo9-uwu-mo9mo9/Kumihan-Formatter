"""
ファイル操作 コア

基本的なファイル操作・ディレクトリ管理機能
Issue #492 Phase 5A - file_operations.py分割
"""

import base64
import shutil
from pathlib import Path
from typing import Any, Optional, Tuple

from .file_path_utilities import FilePathUtilities
from .file_protocol import UIProtocol
from .utilities.logger import get_logger


class FileOperationsCore:
    """File operations utility class"""

    def __init__(self, ui: Optional[UIProtocol] = None):
        """Initialize with optional UI instance for dependency injection"""
        self.ui = ui
        self.logger = get_logger(__name__)
        self.logger.debug("FileOperationsCore initialized")

    def copy_images(self, input_path: Path, output_path: Path, ast: list[Any]) -> None:
        """Copy image files to output directory"""
        # Extract image nodes from AST
        image_nodes = [node for node in ast if getattr(node, "type", None) == "image"]

        if not image_nodes:
            self.logger.debug("No image nodes found in AST")
            return

        self.logger.info(
            f"Copying {len(image_nodes)} images from {input_path} to {output_path}"
        )

        # Check images folder in input file directory
        source_images_dir = input_path.parent / "images"

        if not source_images_dir.exists():
            self.logger.warning(f"Images directory not found: {source_images_dir}")
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
                    self.logger.debug(f"Copied image: {filename}")
            else:
                missing_files.append(filename)
                self.logger.warning(f"Image file not found: {filename}")

        # Report results
        if copied_files:
            self.logger.info(f"Successfully copied {len(copied_files)} image files")
            if self.ui:
                self.ui.file_copied(len(copied_files))

        if missing_files:
            self.logger.warning(f"{len(missing_files)} image files were missing")
            if self.ui:
                self.ui.files_missing(missing_files)

        if duplicate_files:
            self.logger.warning(
                f"Found {len(duplicate_files)} duplicate image filenames"
            )
            if self.ui:
                self.ui.duplicate_files(duplicate_files)

    @staticmethod
    def create_sample_images(images_dir: Path, sample_images: dict[str, str]) -> None:
        """Create sample images from base64 data"""
        images_dir.mkdir(exist_ok=True)

        for filename, base64_data in sample_images.items():
            image_path = images_dir / filename
            image_data = base64.b64decode(base64_data)
            with open(image_path, "wb") as f:
                f.write(image_data)

    @staticmethod
    def copy_directory_with_exclusions(
        source_path: Path, dest_path: Path, exclude_patterns: list[str]
    ) -> Tuple[int, int]:
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
                if FilePathUtilities.should_exclude(
                    item, exclude_patterns, source_path
                ):
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

    def check_large_file_warning(self, path: Path, max_size_mb: float = 50.0) -> bool:
        """
        大規模ファイルの警告表示とユーザー確認

        Args:
            path: チェック対象ファイル
            max_size_mb: 警告を表示するサイズ（MB）

        Returns:
            bool: 続行するかどうか
        """
        size_info = FilePathUtilities.get_file_size_info(path)

        if size_info["size_mb"] > max_size_mb:
            self.logger.warning(
                f"Large file detected: {path} ({size_info['size_mb']:.1f}MB)"
            )
            if self.ui:
                self.ui.warning(
                    f"大規模ファイルを検出: {size_info['size_mb']:.1f}MB",
                    f"処理に時間がかかる可能性があります（推奨: {max_size_mb}MB以下）",
                )

                # 自動的に続行（バッチ処理対応）
                self.ui.info("大規模ファイル処理を開始します")
            return True

        return True
