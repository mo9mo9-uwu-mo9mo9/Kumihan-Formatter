"""
ファイル I/O ハンドラー

ファイル読み書き・エンコーディング処理機能
Issue #492 Phase 5A - file_operations.py分割
"""

import sys
from pathlib import Path

from .encoding_detector import EncodingDetector
from .utilities.logger import get_logger


class FileIOHandler:
    """File input/output operations with proper encoding handling"""

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
