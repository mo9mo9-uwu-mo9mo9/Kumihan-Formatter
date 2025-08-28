#!/usr/bin/env python3
"""Kumihan-Formatter GUI Application Entry Point

GUIアプリケーションのメインエントリーポイント
詳細なログ・デバッグ機能付き
"""

import sys
import traceback
from pathlib import Path


def main_with_logging() -> None:
    """ログ機能付きメインエントリーポイント"""
    try:
        # 早期ログ初期化
        Path("tmp").mkdir(exist_ok=True)

        # インポートログ
        print("🔄 Starting GUI application with logging...")

        # 重要なインポートを段階的に実行
        print("📦 Importing GUI components...")
        from kumihan_formatter.gui.debug_logger import create_gui_logger

        # デバッグロガー初期化
        debug_logger = create_gui_logger(verbose=True, console_output=True)
        debug_logger.logger.info("🎨 GUI Entry Point - ログ初期化完了")

        print("📦 Importing main application...")
        from kumihan_formatter.gui.app import KumihanFormatterApp

        debug_logger.logger.info("🚀 Creating GUI application instance...")
        app = KumihanFormatterApp(verbose_logging=True)

        debug_logger.logger.info("▶️  Starting GUI main loop...")
        app.run()

        debug_logger.logger.info("🏁 GUI application terminated normally")

    except ImportError as e:
        error_msg = f"Import Error: {e}"
        print(f"❌ {error_msg}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")

        # ログファイルにも記録
        try:
            with open("tmp/gui_crash.log", "a", encoding="utf-8") as f:
                f.write(f"IMPORT ERROR - {error_msg}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
                f.write("-" * 60 + "\n")
        except:
            pass

        sys.exit(1)

    except Exception as e:
        error_msg = f"Unexpected Error: {e}"
        print(f"💥 {error_msg}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")

        # 詳細クラッシュログ
        try:
            with open("tmp/gui_crash.log", "a", encoding="utf-8") as f:
                f.write(f"CRASH - {error_msg}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
                f.write(f"Python Version: {sys.version}\n")
                f.write(f"Platform: {sys.platform}\n")
                f.write("-" * 60 + "\n")
        except:
            pass

        sys.exit(1)


def main() -> None:
    """GUIアプリケーションのメインエントリーポイント"""
    main_with_logging()


if __name__ == "__main__":
    main_with_logging()
