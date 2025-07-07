#!/usr/bin/env python3
"""Debug entry point for macOS GUI issues"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ログファイルのパス
log_dir = Path.home() / ".kumihan_formatter_logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def log_message(msg):
    """ログメッセージを記録"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}\n"

    # ファイルに書き込み
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

    # コンソールにも出力（デバッグ用）
    print(log_entry.strip())


try:
    log_message("=== Kumihan Formatter Debug Start ===")
    log_message(f"Python version: {sys.version}")
    log_message(f"Platform: {sys.platform}")
    log_message(f"Executable: {sys.executable}")
    log_message(f"Working directory: {os.getcwd()}")
    log_message(f"Log file: {log_file}")

    # PyInstallerでの実行かチェック
    if getattr(sys, "frozen", False):
        log_message("Running in PyInstaller bundle")
        log_message(f"Bundle dir: {sys._MEIPASS}")
    else:
        log_message("Running in normal Python environment")

    # 環境変数の確認
    log_message("Environment variables:")
    for key in ["DISPLAY", "PYTHONPATH", "PATH"]:
        value = os.environ.get(key, "Not set")
        log_message(f"  {key}: {value}")

    # macOS固有の設定
    if sys.platform == "darwin":
        log_message("Applying macOS-specific configurations...")

        # macOSでTkinterを正しく初期化するための環境変数
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0.0"
            log_message("Set DISPLAY=:0.0")

    log_message("Attempting to import tkinter...")
    try:
        import tkinter

        log_message("tkinter imported successfully")

        # Tkinterのバージョン確認
        root = tkinter.Tk()
        tk_version = root.tk.eval("info patchlevel")
        log_message(f"Tk version: {tk_version}")
        root.destroy()

    except Exception as e:
        log_message(f"Failed to import/initialize tkinter: {e}")
        log_message(traceback.format_exc())
        raise

    log_message("Attempting to import kumihan_formatter modules...")
    try:
        # gui_launcherをインポートする前にパスを設定
        if getattr(sys, "frozen", False):
            # PyInstallerバンドル内
            base_path = sys._MEIPASS
        else:
            # 通常のPython環境
            base_path = Path(__file__).parent

        sys.path.insert(0, str(base_path))
        log_message(f"Added to sys.path: {base_path}")

        from kumihan_formatter.gui_launcher import main

        log_message("gui_launcher imported successfully")

    except Exception as e:
        log_message(f"Failed to import gui_launcher: {e}")
        log_message(traceback.format_exc())
        raise

    log_message("Starting GUI main()...")
    main()
    log_message("GUI main() completed")

except Exception as e:
    error_msg = f"Fatal error: {e}\n{traceback.format_exc()}"
    log_message(error_msg)

    # エラーダイアログを表示（可能な場合）
    try:
        import tkinter.messagebox as mb

        mb.showerror(
            "Kumihan Formatter Error",
            f"An error occurred. Please check the log file:\n{log_file}\n\nError: {str(e)}",
        )
    except:
        # Tkinterが使えない場合はコンソールに出力
        print(f"\nERROR: {e}")
        print(f"Check log file: {log_file}")

    sys.exit(1)

finally:
    log_message("=== Debug session end ===\n")
