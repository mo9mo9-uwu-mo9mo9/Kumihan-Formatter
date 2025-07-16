"""State and logging models for Kumihan-Formatter GUI

Single Responsibility Principle適用: 状態・ログ管理モデルの分離
Issue #476 Phase2対応 - gui_models.py分割（3/3）
"""

import os
from pathlib import Path
from typing import Dict, Optional

from .gui_config import GuiConfig
from .conversion_state import ConversionState
from .file_model import FileManager


class LogManager:
    """ログ管理クラス

    GUIログの管理、メッセージレベル、タイムスタンプ処理
    """

    LOG_LEVELS = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}

    def __init__(self) -> None:
        """ログ管理の初期化"""
        self.messages: list[Dict[str, str]] = []

    @staticmethod
    def format_log_message(message: str, level: str = "info") -> str:
        """ログメッセージのフォーマット"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = LogManager.LOG_LEVELS.get(level, "ℹ️")
        return f"[{timestamp}] {prefix} {message}"

    def add_message(self, message: str, level: str = "info") -> str:
        """ログメッセージを追加してフォーマットされたメッセージを返す"""
        formatted = self.format_log_message(message, level)
        self.messages.append(
            {
                "message": message,
                "level": level,
                "formatted": formatted,
                "timestamp": self._get_timestamp(),
            }
        )
        return formatted

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        import datetime

        return datetime.datetime.now().isoformat()

    def get_recent_messages(self, count: int = 50) -> list[str]:
        """最新のメッセージを取得"""
        return [msg["formatted"] for msg in self.messages[-count:]]

    def clear_messages(self) -> None:
        """ログメッセージをクリア"""
        self.messages.clear()

    def clear_log(self) -> None:
        """ログをクリア（互換性メソッド）"""
        self.clear_messages()


class AppState:
    """アプリケーション全体の状態管理クラス

    GUI、変換、ファイル、ログの各管理クラスを統合
    """

    def __init__(self) -> None:
        """アプリケーション状態の初期化"""
        self.config = GuiConfig()
        self.conversion_state = ConversionState()
        self.file_manager = FileManager()
        self.log_manager = LogManager()

        # デバッグモード
        self.debug_mode = self._check_debug_mode()

    def _check_debug_mode(self) -> bool:
        """デバッグモードの確認"""
        return os.environ.get("KUMIHAN_GUI_DEBUG", "false").lower() == "true"

    def is_ready_for_conversion(self) -> tuple[bool, str]:
        """変換実行可能かチェック"""
        if self.conversion_state.is_processing:
            return False, "処理中です"

        if not self.config.validate_input_file():
            return False, "入力ファイルを選択してください"

        if not self.file_manager.validate_directory_writable(
            self.config.get_output_dir()
        ):
            return False, "出力ディレクトリが無効です"

        return True, "変換可能"

    def get_output_file_path(self) -> Optional[Path]:
        """出力ファイルパスを取得"""
        try:
            return self.file_manager.get_output_html_path(
                self.config.get_input_file(), self.config.get_output_dir()
            )
        except ValueError:
            return None