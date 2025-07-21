"""
ファイル I/O ハンドラー

ファイル読み書き・エンコーディング処理機能
Issue #492 Phase 5A - file_operations.py分割
"""

import sys
from pathlib import Path
from typing import Any

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

        # Try detected encoding first if confident
        content = FileIOHandler._try_detected_encoding(
            path, detected_encoding, is_confident, encoding, logger
        )
        if content is not None:
            return content

        # Try specified encoding if different
        content = FileIOHandler._try_specified_encoding(
            path, encoding, detected_encoding, logger
        )
        if content is not None:
            return content

        # Try platform-specific fallbacks
        content = FileIOHandler._try_platform_fallbacks(path, logger)
        if content is not None:
            return content

        # Last resort: UTF-8 with error replacement
        return FileIOHandler._read_with_error_replacement(path, logger)

    @staticmethod
    def _try_detected_encoding(
        path: Path,
        detected_encoding: str,
        is_confident: bool,
        encoding: str,
        logger: Any,
    ) -> str | None:
        """検出されたエンコーディングで読み取りを試行"""
        if is_confident or encoding == "utf-8":
            try:
                with open(path, "r", encoding=detected_encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with {detected_encoding}")
        return None

    @staticmethod
    def _try_specified_encoding(
        path: Path, encoding: str, detected_encoding: str, logger: Any
    ) -> str | None:
        """指定されたエンコーディングで読み取りを試行"""
        if encoding != detected_encoding:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with specified encoding: {encoding}")
        return None

    @staticmethod
    def _try_platform_fallbacks(path: Path, logger: Any) -> str | None:
        """プラットフォーム固有のフォールバックエンコーディングで読み取りを試行"""
        fallback_encodings: list[str] = ["cp932"] if sys.platform == "win32" else []

        for enc in fallback_encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with {enc}")
        return None

    @staticmethod
    def _read_with_error_replacement(path: Path, logger: Any) -> str:
        """エラー置換付きUTF-8で読み取り"""
        logger.warning(f"Using UTF-8 with error replacement for {path}")
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
