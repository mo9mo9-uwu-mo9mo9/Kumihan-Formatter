"""State and logging models for Kumihan-Formatter GUI

Single Responsibility Principle適用: 状態・ログ管理モデルの分離
Issue #476 Phase2対応 - gui_models.py分割（3/3）
Issue #516 Phase 5A対応 - Thread-Safe設計とエラーハンドリング強化
"""

import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from .conversion_state import ConversionState
from .file_model import FileManager
from .gui_config import GuiConfig


class LogManager:
    """ログ管理クラス（Thread-Safe対応）

    GUIログの管理、メッセージレベル、タイムスタンプ処理
    マルチスレッド環境での安全なログ操作を保証
    """

    LOG_LEVELS = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}

    def __init__(self, max_messages: int = 1000) -> None:
        """ログ管理の初期化"""
        self.messages: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        self._max_messages = max_messages

    @staticmethod
    def format_log_message(message: str, level: str = "info") -> str:
        """ログメッセージのフォーマット（エラーハンドリング強化）"""
        try:
            import datetime

            if not isinstance(message, str):
                message = str(message)
            if not isinstance(level, str):
                level = "info"

            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = LogManager.LOG_LEVELS.get(level, "ℹ️")
            return f"[{timestamp}] {prefix} {message}"
        except Exception as e:
            logging.error(f"ログメッセージフォーマットエラー: {e}")
            return f"[ERROR] {message}"

    def add_message(self, message: str, level: str = "info") -> str:
        """ログメッセージを追加してフォーマットされたメッセージを返す（Thread-Safe）"""
        try:
            with self._lock:
                formatted = self.format_log_message(message, level)

                # メッセージ情報の作成
                msg_info = {
                    "message": message,
                    "level": level,
                    "formatted": formatted,
                    "timestamp": self._get_timestamp(),
                }

                self.messages.append(msg_info)

                # メッセージ数制限の適用
                if len(self.messages) > self._max_messages:
                    # 古いメッセージを削除（半分まで減らす）
                    remove_count = len(self.messages) - (self._max_messages // 2)
                    self.messages = self.messages[remove_count:]

                return formatted
        except Exception as e:
            logging.error(f"ログメッセージ追加エラー: {e}")
            return f"[ERROR] {message}"

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        try:
            import datetime

            return datetime.datetime.now().isoformat()
        except Exception:
            return "unknown"

    def get_recent_messages(self, count: int = 50) -> List[str]:
        """最新のメッセージを取得（Thread-Safe）"""
        try:
            with self._lock:
                if count <= 0:
                    return []
                return [msg["formatted"] for msg in self.messages[-count:]]
        except Exception as e:
            logging.error(f"最新メッセージ取得エラー: {e}")
            return []

    def get_messages_by_level(self, level: str) -> List[Dict[str, str]]:
        """指定レベルのメッセージを取得（Thread-Safe）"""
        try:
            with self._lock:
                return [msg for msg in self.messages if msg.get("level") == level]
        except Exception as e:
            logging.error(f"レベル別メッセージ取得エラー: {e}")
            return []

    def clear_messages(self) -> None:
        """ログメッセージをクリア（Thread-Safe）"""
        try:
            with self._lock:
                self.messages.clear()
        except Exception as e:
            logging.error(f"ログメッセージクリアエラー: {e}")

    def clear_log(self) -> None:
        """ログをクリア（互換性メソッド）"""
        self.clear_messages()

    def get_message_count(self) -> int:
        """メッセージ総数を取得（Thread-Safe）"""
        with self._lock:
            return len(self.messages)


class AppState:
    """アプリケーション全体の状態管理クラス（Thread-Safe対応）

    GUI、変換、ファイル、ログの各管理クラスを統合
    マルチスレッド環境での安全な状態管理を保証
    """

    def __init__(self) -> None:
        """アプリケーション状態の初期化"""
        self._lock = threading.Lock()

        try:
            self.config = GuiConfig()
            self.conversion_state = ConversionState()
            self.file_manager = FileManager()
            self.log_manager = LogManager()

            # デバッグモード
            self.debug_mode = self._check_debug_mode()

            # エラー状態管理
            self._error_count = 0
            self._last_error: Optional[str] = None

        except Exception as e:
            logging.error(f"AppState初期化エラー: {e}")
            # 基本的な初期化を試行
            self._initialize_fallback()

    def _initialize_fallback(self) -> None:
        """フォールバック初期化"""
        try:
            self.config = GuiConfig()
            self.conversion_state = ConversionState()
            self.file_manager = FileManager()
            self.log_manager = LogManager()
            self.debug_mode = False
            self._error_count = 0
            self._last_error = None
        except Exception as e:
            logging.critical(f"フォールバック初期化も失敗: {e}")

    def _check_debug_mode(self) -> bool:
        """デバッグモードの確認（エラーハンドリング強化）"""
        try:
            return os.environ.get("KUMIHAN_GUI_DEBUG", "false").lower() == "true"
        except Exception as e:
            logging.warning(f"デバッグモード確認エラー: {e}")
            return False

    def is_ready_for_conversion(self) -> tuple[bool, str]:
        """変換実行可能かチェック（Thread-Safe）"""
        try:
            with self._lock:
                if self.conversion_state.is_processing:
                    return False, "処理中です"

                if not self.config.validate_input_file():
                    self._record_error("入力ファイルが無効です")
                    return False, "入力ファイルを選択してください"

                if not self.file_manager.validate_directory_writable(
                    self.config.get_output_dir()
                ):
                    self._record_error("出力ディレクトリが無効です")
                    return False, "出力ディレクトリが無効です"

                return True, "変換可能"
        except Exception as e:
            logging.error(f"変換準備チェックエラー: {e}")
            self._record_error(f"変換準備チェックエラー: {e}")
            return False, "システムエラーが発生しました"

    def get_output_file_path(self) -> Optional[Path]:
        """出力ファイルパスを取得（Thread-Safe）"""
        try:
            with self._lock:
                return self.file_manager.get_output_html_path(
                    self.config.get_input_file(), self.config.get_output_dir()
                )
        except Exception as e:
            logging.error(f"出力ファイルパス取得エラー: {e}")
            self._record_error(f"出力ファイルパス取得エラー: {e}")
            return None

    def _record_error(self, error_message: str) -> None:
        """エラーを記録（ロック済み前提）"""
        try:
            self._error_count += 1
            self._last_error = error_message
            if hasattr(self, "log_manager"):
                self.log_manager.add_message(error_message, "error")
        except Exception as e:
            logging.error(f"エラー記録失敗: {e}")

    def get_error_info(self) -> Dict[str, Any]:
        """エラー情報を取得（Thread-Safe）"""
        try:
            with self._lock:
                return {
                    "error_count": self._error_count,
                    "last_error": self._last_error,
                    "has_errors": self._error_count > 0,
                }
        except Exception as e:
            logging.error(f"エラー情報取得エラー: {e}")
            return {"error_count": 0, "last_error": None, "has_errors": False}

    def reset_errors(self) -> None:
        """エラー状態をリセット（Thread-Safe）"""
        try:
            with self._lock:
                self._error_count = 0
                self._last_error = None
        except Exception as e:
            logging.error(f"エラー状態リセットエラー: {e}")


# 後方互換性のためのStateModelクラス定義
class StateModel(AppState):
    """後方互換性のためのStateModelクラス

    AppStateの機能をそのまま継承し、既存コードとの互換性を維持
    新規実装ではAppStateの使用を推奨
    """

    def __init__(self) -> None:
        """StateModel初期化（AppStateと同一）"""
        super().__init__()
