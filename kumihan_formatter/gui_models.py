"""GUI Models for Kumihan-Formatter

Model層: データ・設定管理とビジネスロジック
MVCパターンでのModel部分を担当し、UIから独立したデータ処理を提供
"""

from pathlib import Path
from tkinter import BooleanVar, DoubleVar, StringVar
from typing import Any, Dict, Optional


class GuiConfig:
    """GUI設定管理クラス

    ユーザーの設定項目（ファイルパス、オプション等）を管理
    """

    def __init__(self) -> None:
        """設定項目の初期化"""
        # ファイル関連設定
        self.input_file_var = StringVar()
        self.output_dir_var = StringVar(value="./dist")

        # テンプレート設定
        self.template_var = StringVar(value="base.html.j2")
        self.available_templates = ["base.html.j2", "base-with-source-toggle.html.j2"]

        # オプション設定
        self.include_source_var = BooleanVar(value=False)
        self.no_preview_var = BooleanVar(value=False)

    def get_input_file(self) -> str:
        """入力ファイルパスを取得"""
        return self.input_file_var.get().strip()

    def set_input_file(self, path: str) -> None:
        """入力ファイルパスを設定"""
        self.input_file_var.set(path)

    def get_output_dir(self) -> str:
        """出力ディレクトリを取得"""
        return self.output_dir_var.get().strip()

    def set_output_dir(self, path: str) -> None:
        """出力ディレクトリを設定"""
        self.output_dir_var.set(path)

    def get_template(self) -> str:
        """選択されたテンプレートを取得"""
        return self.template_var.get()

    def set_template(self, template: str) -> None:
        """テンプレートを設定"""
        if template in self.available_templates:
            self.template_var.set(template)

    def get_include_source(self) -> bool:
        """ソース表示オプションを取得"""
        return self.include_source_var.get()

    def set_include_source(self, value: bool) -> None:
        """ソース表示オプションを設定"""
        self.include_source_var.set(value)
        # ソース表示が有効な場合、自動でテンプレートを切り替え
        if value:
            self.set_template("base-with-source-toggle.html.j2")
        else:
            self.set_template("base.html.j2")

    def get_no_preview(self) -> bool:
        """プレビュー無効化オプションを取得"""
        return self.no_preview_var.get()

    def set_no_preview(self, value: bool) -> None:
        """プレビュー無効化オプションを設定"""
        self.no_preview_var.set(value)

    def validate_input_file(self) -> bool:
        """入力ファイルの妥当性チェック"""
        input_file = self.get_input_file()
        if not input_file:
            return False
        return Path(input_file).exists()

    def get_conversion_params(self) -> Dict[str, Any]:
        """変換実行用のパラメータを取得"""
        return {
            "input_file": self.get_input_file(),
            "output": self.get_output_dir(),
            "template_name": self.get_template(),
            "include_source": self.get_include_source(),
            "no_preview": self.get_no_preview(),
            "watch": False,
            "config": None,
            "show_test_cases": False,
            "syntax_check": True,
        }


class ConversionState:
    """変換処理の状態管理クラス

    進捗状況、ステータスメッセージ、処理状態を管理
    """

    def __init__(self) -> None:
        """状態管理変数の初期化"""
        self.progress_var = DoubleVar()
        self.status_var = StringVar(value="準備完了")
        self.is_processing = False

    def get_progress(self) -> float:
        """現在の進捗値を取得"""
        return self.progress_var.get()

    def set_progress(self, value: float) -> None:
        """進捗値を設定（0-100）"""
        self.progress_var.set(max(0, min(100, value)))

    def get_status(self) -> str:
        """現在のステータスメッセージを取得"""
        return self.status_var.get()

    def set_status(self, message: str) -> None:
        """ステータスメッセージを設定"""
        self.status_var.set(message)

    def update_progress(self, value: float, status: str = "") -> None:
        """進捗とステータスを同時更新"""
        self.set_progress(value)
        if status:
            self.set_status(status)

    def start_processing(self) -> None:
        """処理開始"""
        self.is_processing = True
        self.set_progress(0)
        self.set_status("処理中...")

    def finish_processing(self, success: bool = True) -> None:
        """処理完了"""
        self.is_processing = False
        if success:
            self.set_progress(100)
            self.set_status("完了")
        else:
            self.set_progress(0)
            self.set_status("エラー")

    def reset(self) -> None:
        """状態をリセット"""
        self.is_processing = False
        self.set_progress(0)
        self.set_status("準備完了")


class FileManager:
    """ファイル操作管理クラス

    ファイル選択、パス管理、出力パス生成等のファイル関連処理
    """

    @staticmethod
    def get_output_html_path(input_file: str, output_dir: str) -> Path:
        """入力ファイルから出力HTMLファイルのパスを生成"""
        if not input_file:
            raise ValueError("入力ファイルが指定されていません")

        input_path = Path(input_file)
        output_path = Path(output_dir) / f"{input_path.stem}.html"
        return output_path

    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """ファイルの存在確認"""
        if not file_path:
            return False
        return Path(file_path).exists()

    @staticmethod
    def validate_directory_writable(dir_path: str) -> bool:
        """ディレクトリの書き込み可能性確認"""
        try:
            directory = Path(dir_path)
            directory.mkdir(parents=True, exist_ok=True)
            return directory.is_dir()
        except (OSError, PermissionError):
            return False

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """ファイルサイズをMB単位で取得"""
        try:
            return Path(file_path).stat().st_size / (1024 * 1024)
        except (OSError, FileNotFoundError):
            return 0.0

    @staticmethod
    def get_sample_output_path(output_dir: str = "kumihan_sample") -> Path:
        """サンプル生成用の出力パスを取得"""
        return Path(output_dir)


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
        import os

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
