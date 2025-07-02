"""Encoding detection utilities for Kumihan-Formatter

Provides efficient encoding detection for text files.
"""

from pathlib import Path
from typing import Optional, Tuple


class EncodingDetector:
    """Efficient encoding detection for text files"""

    # BOM signatures
    BOMS = {
        b"\xff\xfe\x00\x00": "utf-32-le",
        b"\x00\x00\xfe\xff": "utf-32-be",
        b"\xff\xfe": "utf-16-le",
        b"\xfe\xff": "utf-16-be",
        b"\xef\xbb\xbf": "utf-8-sig",
    }

    @classmethod
    def detect_bom(cls, path: Path) -> Optional[str]:
        """Detect encoding from BOM (Byte Order Mark)

        Args:
            path: Path to the file

        Returns:
            Detected encoding or None if no BOM found
        """
        with open(path, "rb") as f:
            raw = f.read(4)

        # Check BOMs in order of size (larger first)
        for bom, encoding in cls.BOMS.items():
            if raw.startswith(bom):
                return encoding

        return None

    @staticmethod
    def detect_encoding_sample(path: Path, sample_size: int = 8192) -> Optional[str]:
        """Detect encoding by sampling file content

        Args:
            path: Path to the file
            sample_size: Number of bytes to sample

        Returns:
            Detected encoding or None if cannot determine
        """
        try:
            with open(path, "rb") as f:
                sample = f.read(sample_size)

            # Simple heuristic detection
            # Check for null bytes (likely UTF-16/32)
            if b"\x00" in sample:
                if b"\x00\x00" in sample:
                    return "utf-32"
                else:
                    return "utf-16"

            # Try UTF-8
            try:
                sample.decode("utf-8")
                return "utf-8"
            except UnicodeDecodeError:
                pass

            # Check for common Japanese encodings
            # Look for Shift_JIS patterns
            if any(0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF for b in sample):
                try:
                    sample.decode("shift_jis")
                    return "shift_jis"
                except UnicodeDecodeError:
                    pass

            return None

        except Exception:
            return None

    @classmethod
    def detect(cls, path: Path) -> Tuple[str, bool]:
        """Detect file encoding

        Args:
            path: Path to the file

        Returns:
            Tuple of (encoding, is_confident)
        """
        # First check BOM
        bom_encoding = cls.detect_bom(path)
        if bom_encoding:
            return bom_encoding, True

        # Try sample-based detection
        sample_encoding = cls.detect_encoding_sample(path)
        if sample_encoding:
            return sample_encoding, True

        # Default fallback
        return "utf-8", False
