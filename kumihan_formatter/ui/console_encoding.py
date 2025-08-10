"""Console encoding setup utilities for Kumihan-Formatter

Handles platform-specific encoding configuration.
"""

import io
import sys
from typing import Any


class ConsoleEncodingSetup:
    """Console encoding setup for different platforms"""

    @staticmethod
    def setup_encoding() -> None:
        """Setup proper encoding for different platforms"""
        import locale

        # Note: Removed os.environ["PYTHONIOENCODING"] = "utf-8"
        # to avoid global environment variable modification
        # Applications should set this externally if needed
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
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            except AttributeError:
                # Already wrapped or no buffer attribute
                pass

        if sys.stderr and sys.stderr.encoding != "utf-8":
            try:
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
            except AttributeError:
                pass

    @staticmethod
    def _setup_windows_encoding(locale: Any) -> None:
        """Setup encoding for Windows"""
        # 複数の方法を試してUTF-8サポートを確実にする

        # Method 1: reconfigure（Python 3.7以降）
        ConsoleEncodingSetup._try_reconfigure_streams()

        # Method 2: ストリームをラップ
        ConsoleEncodingSetup._try_wrap_streams()

        # Method 3: Windowsコンソールコードページ
        ConsoleEncodingSetup._try_set_console_codepage()

        # ロケール設定
        ConsoleEncodingSetup._try_set_locale(locale)

    @staticmethod
    def _try_reconfigure_streams() -> None:
        """ストリームの再設定を試行"""
        if hasattr(sys.stdout, "reconfigure"):
            try:
                if hasattr(sys.stdout, "reconfigure"):
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                if hasattr(sys.stderr, "reconfigure"):
                    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                # フォールバック処理継続
                pass

    @staticmethod
    def _try_wrap_streams() -> None:
        """ストリームのラップを試行"""
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

    @staticmethod
    def _try_set_console_codepage() -> None:
        """Windowsコンソールコードページの設定を試行"""
        try:
            import ctypes

            if hasattr(ctypes, "windll"):
                kernel32 = ctypes.windll.kernel32
                # UTF-8用コンソールコードページ設定
                kernel32.SetConsoleCP(65001)
                kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    @staticmethod
    def _try_set_locale(locale: Any) -> None:
        """ロケール設定を試行"""
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception:
            try:
                # UTF-8ロケールにフォールバック
                locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
            except Exception:
                pass
