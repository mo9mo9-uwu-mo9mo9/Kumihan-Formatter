"""Console encoding setup utilities for Kumihan-Formatter

Handles platform-specific encoding configuration.
"""

import io
import sys


class ConsoleEncodingSetup:
    """Console encoding setup for different platforms"""

    @staticmethod
    def setup_encoding() -> None:
        """Setup proper encoding for different platforms"""
        import locale
        import os

        # Set environment variable first
        os.environ["PYTHONIOENCODING"] = "utf-8"

        # macOS encoding fix
        if sys.platform == "darwin":
            ConsoleEncodingSetup._setup_macos_encoding()

        # Windows encoding setup
        elif sys.platform == "win32":
            ConsoleEncodingSetup._setup_windows_encoding(locale)

    @staticmethod
    def _setup_macos_encoding() -> None:
        """Setup encoding for macOS"""
        # Force UTF-8 encoding for stdout/stderr
        if sys.stdout and sys.stdout.encoding != "utf-8":
            try:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace"
                )
            except AttributeError:
                # Already wrapped or no buffer attribute
                pass

        if sys.stderr and sys.stderr.encoding != "utf-8":
            try:
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, encoding="utf-8", errors="replace"
                )
            except AttributeError:
                pass

    @staticmethod
    def _setup_windows_encoding(locale) -> None:
        """Setup encoding for Windows"""
        # Try multiple methods to ensure UTF-8 support

        # Method 1: reconfigure (Python 3.7+)
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                # Fallback to method 2
                pass

        # Method 2: Wrap streams
        if sys.stdout and sys.stdout.encoding != "utf-8":
            try:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding="utf-8",
                    errors="replace",
                    line_buffering=True,
                )
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding="utf-8",
                    errors="replace",
                    line_buffering=True,
                )
            except Exception:
                pass

        # Method 3: Windows console code page
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # Set console code page to UTF-8
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

        # Set locale
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception:
            try:
                # Fallback to specific UTF-8 locale
                locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
            except Exception:
                pass
