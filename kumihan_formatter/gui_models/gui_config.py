"""GUI configuration management for Kumihan-Formatter

Single Responsibility Principle適用: GUI設定管理の分離
Issue #476対応 - config_model.py分割（関数数過多解消）
"""

from pathlib import Path
from typing import Any, Dict, Type


# Tkinterが利用できない場合のフォールバック
class MockVar:
    def __init__(self, value: Any = None) -> None:
        self._value = value

    def get(self) -> Any:
        return self._value

    def set(self, value: Any) -> None:
        self._value = value


try:
    from tkinter import BooleanVar, StringVar

    _TKINTER_AVAILABLE = True
except (ImportError, RuntimeError):
    _TKINTER_AVAILABLE = False
    BooleanVar = MockVar  # type: ignore[misc,assignment]
    StringVar = MockVar  # type: ignore[misc,assignment]


def _safe_create_var(var_class: Type[Any], value: Any = None) -> Any:
    """安全にTkinter変数を作成"""
    try:
        if _TKINTER_AVAILABLE:
            return var_class(value=value)
        else:
            return MockVar(value=value)
    except Exception:
        return MockVar(value=value)


class GuiConfig:
    """GUI設定管理クラス

    ユーザーの設定項目（ファイルパス、オプション等）を管理
    """

    def __init__(self) -> None:
        """設定項目の初期化"""
        # ファイル関連設定
        self.input_file_var = _safe_create_var(StringVar, "")
        self.output_dir_var = _safe_create_var(StringVar, "./dist")

        # テンプレート設定
        self.template_var = _safe_create_var(StringVar, "base.html.j2")
        self.available_templates = ["base.html.j2", "base-with-source-toggle.html.j2"]

        # オプション設定
        self.include_source_var = _safe_create_var(BooleanVar, False)
        self.no_preview_var = _safe_create_var(BooleanVar, False)

    def get_input_file(self) -> str:
        """入力ファイルパスを取得"""
        value = self.input_file_var.get()
        return str(value).strip() if value is not None else ""

    def set_input_file(self, path: str) -> None:
        """入力ファイルパスを設定"""
        self.input_file_var.set(path)

    def get_output_dir(self) -> str:
        """出力ディレクトリを取得"""
        value = self.output_dir_var.get()
        return str(value).strip() if value is not None else "./dist"

    def set_output_dir(self, path: str) -> None:
        """出力ディレクトリを設定"""
        self.output_dir_var.set(path)

    def get_template(self) -> str:
        """選択されたテンプレートを取得"""
        value = self.template_var.get()
        return str(value) if value is not None else "base.html.j2"

    def set_template(self, template: str) -> None:
        """テンプレートを設定"""
        if template in self.available_templates:
            self.template_var.set(template)

    def get_include_source(self) -> bool:
        """ソース表示オプションを取得"""
        value = self.include_source_var.get()
        return bool(value) if value is not None else False

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
        value = self.no_preview_var.get()
        return bool(value) if value is not None else False

    def set_no_preview(self, value: bool) -> None:
        """プレビュー無効化オプションを設定"""
        self.no_preview_var.set(value)

    def validate_input_file(self) -> bool:
        """入力ファイルの妥当性チェック"""
        input_file = self.get_input_file()
        if not input_file:
            return False

        path = Path(input_file)
        return path.exists() and path.is_file()

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
