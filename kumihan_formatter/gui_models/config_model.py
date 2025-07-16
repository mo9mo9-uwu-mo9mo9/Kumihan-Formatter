"""Configuration model for Kumihan-Formatter GUI

Single Responsibility Principle適用: 設定管理モデルの分離
Issue #476 Phase2対応 - gui_models.py分割（1/3）
"""

from pathlib import Path
from tkinter import BooleanVar, DoubleVar, StringVar
from typing import Any, Dict


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
        """進捗率を取得"""
        return self.progress_var.get()

    def set_progress(self, value: float) -> None:
        """進捗率を設定"""
        self.progress_var.set(value)

    def get_status(self) -> str:
        """ステータスメッセージを取得"""
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