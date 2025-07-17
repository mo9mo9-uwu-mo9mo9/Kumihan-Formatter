"""ファイル操作メインクラス

ファイルのコピー、読み書き、大規模ファイル処理などの
中核的なファイル操作機能を提供。
"""

import base64
import fnmatch
import shutil
import sys
from pathlib import Path
from typing import Any

from .encoding_detector import EncodingDetector
from .file_protocol import UIProtocol
from .utilities.logger import get_logger


class FileOperations:
    """File operations utility class"""

    def __init__(self, ui: UIProtocol | None = None):
        """Initialize with optional UI instance for dependency injection"""
        self.ui = ui
        self.logger = get_logger(__name__)
        self.logger.debug("FileOperations initialized")

    @staticmethod
    def load_distignore_patterns() -> list[str]:
        """
        Load exclusion patterns from .distignore file

        Returns:
            list: List of exclusion patterns
        """
        logger = get_logger(__name__)
        patterns = []
        distignore_path = Path(".distignore")

        if distignore_path.exists():
            logger.debug(f"Loading exclusion patterns from {distignore_path}")
            with open(distignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comment lines and empty lines
                    if line and not line.startswith("#"):
                        patterns.append(line)

        logger.debug(f"Loaded {len(patterns)} exclusion patterns")
        return patterns

    @staticmethod
    def should_exclude(path: Path, patterns: list[str], base_path: Path) -> bool:
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
            if pattern.endswith("/"):
                # Check files under directory
                dir_pattern = pattern.rstrip("/")

                # Complete path matching
                if (
                    relative_str.startswith(dir_pattern + "/")
                    or relative_str == dir_pattern
                ):
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
    ) -> tuple[int, int]:
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
    def find_preview_file(directory: Path) -> Path | None:
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
        """Write text file with proper encoding and error handling"""
        logger = get_logger(__name__)
        logger.debug(f"Writing file: {path} with encoding: {encoding}")

        try:
            # Try with UTF-8 first
            with open(path, "w", encoding=encoding, errors="replace") as f:
                f.write(content)
        except UnicodeEncodeError:
            # Fallback with error replacement
            logger.warning(f"Unicode encode error for {path}, using error replacement")
            with open(path, "w", encoding=encoding, errors="replace") as f:
                f.write(content)
        except Exception as e:
            # For Windows, try with BOM
            if encoding.lower() == "utf-8":
                try:
                    logger.debug(f"Trying UTF-8 with BOM for {path}")
                    with open(path, "w", encoding="utf-8-sig", errors="replace") as f:
                        f.write(content)
                except Exception:
                    logger.error(f"Failed to write file {path}: {e}")
                    raise e
            else:
                logger.error(f"Failed to write file {path}: {e}")
                raise

    @staticmethod
    def read_text_file(path: Path, encoding: str = "utf-8") -> str:
        """Read text file with proper encoding and error handling

        Uses efficient encoding detection:
        1. Check for BOM
        2. Try specified encoding
        3. Try platform-specific common encodings
        4. Fallback to UTF-8 with error replacement
        """
        logger = get_logger(__name__)
        logger.debug(f"Reading file: {path}")

        # Use encoding detector for efficiency
        detected_encoding, is_confident = EncodingDetector.detect(path)
        logger.debug(
            f"Detected encoding: {detected_encoding} (confident: {is_confident})"
        )

        # If confident in detection or no encoding specified, use detected
        if is_confident or encoding == "utf-8":
            try:
                with open(path, "r", encoding=detected_encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with {detected_encoding}")
                pass

        # Try specified encoding if different from detected
        if encoding != detected_encoding:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with specified encoding: {encoding}")
                pass

        # Platform-specific fallbacks (minimal set)
        if sys.platform == "win32":
            fallback_encodings: list[str] = ["cp932"]
        else:
            fallback_encodings: list[str] = []

        for enc in fallback_encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with {enc}")
                continue

        # Last resort: UTF-8 with error replacement
        logger.warning(f"Using UTF-8 with error replacement for {path}")
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    @staticmethod
    def get_file_size_info(path: Path) -> dict[str, Any]:
        """Get file size information"""
        if path.exists():
            size = path.stat().st_size
            return {
                "size_bytes": size,
                "size_mb": size / (1024 * 1024),
                "size_formatted": f"{size:,}",
                "is_large": size > 10 * 1024 * 1024,  # 10MB以上
            }
        return {
            "size_bytes": 0,
            "size_mb": 0.0,
            "size_formatted": "0",
            "is_large": False,
        }

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
