"""カバレッジ向上テスト - Issue #554対応

実際のコード実行によるカバレッジ向上を目指すテスト
CI/CD正常化のため、基本的な機能の動作確認を行う
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


def test_actual_config_execution() -> None:
    """実際の設定処理実行テスト"""
    from kumihan_formatter.config.base_config import BaseConfig

    # デフォルト設定での実行
    config = BaseConfig()
    css_vars: Dict[str, Any] = config.get_css_variables()

    # 各CSS変数の取得と検証
    assert css_vars["max_width"] == "800px"
    assert css_vars["background_color"] == "#f9f9f9"
    assert css_vars["container_background"] == "white"
    assert css_vars["text_color"] == "#333"
    assert css_vars["line_height"] == "1.8"

    # カスタム設定での実行
    custom_data: Dict[str, Dict[str, str]] = {
        "css": {"max_width": "1200px", "custom_property": "custom_value"}
    }
    custom_config = BaseConfig(custom_data)
    custom_css = custom_config.get_css_variables()

    # カスタム設定の適用確認
    assert custom_css["max_width"] == "1200px"
    assert custom_css["custom_property"] == "custom_value"
    # デフォルト値の維持確認
    assert custom_css["background_color"] == "#f9f9f9"


def test_console_ui_execution() -> None:
    """コンソールUIの実際の実行テスト"""
    from kumihan_formatter.ui.console_ui import ConsoleUI

    ui = ConsoleUI()

    # メソッドの存在確認と実行
    assert hasattr(ui, "info")
    assert hasattr(ui, "error")
    assert hasattr(ui, "warning")
    assert hasattr(ui, "success")

    # 実際のメソッド呼び出し（エラーが発生しないことを確認）
    try:
        # これらの呼び出しは出力を生成するが、例外は発生させない
        ui.info("Test", "Test message")
        ui.error("Test", "Test error message")
        ui.warning("Test", "Test warning message")
        ui.success("Test", "Test success message")
    except Exception as e:
        pytest.fail(f"Console UI method failed: {e}")


def test_file_operations_execution() -> None:
    """ファイル操作の実際の実行テスト"""
    from kumihan_formatter.core.file_operations import FileOperations

    file_ops = FileOperations()

    # インスタンス作成の確認
    assert file_ops.ui is None  # デフォルトでNone
    assert file_ops.logger is not None

    # 基本メソッドの存在確認
    assert hasattr(file_ops, "copy_images")
    assert callable(file_ops.copy_images)


def test_version_import_execution() -> None:
    """バージョン情報の実際の取得テスト"""
    import kumihan_formatter

    # __init__.pyの実行によるカバレッジ向上
    version = kumihan_formatter.__version__

    # バージョン文字列の詳細検証
    assert isinstance(version, str)
    assert len(version) > 0

    # セマンティックバージョニングパターンの確認
    version_parts: list[str] = version.split(".")
    assert len(version_parts) >= 2

    # メジャーバージョンの確認
    major_version = version_parts[0]
    assert major_version.isdigit() or major_version == "0"


def test_config_module_init() -> None:
    """config モジュールの __init__.py 実行テスト"""
    from kumihan_formatter.config import BaseConfig, ConfigManager

    # モジュールの初期化によるカバレッジ向上
    assert BaseConfig is not None
    assert ConfigManager is not None

    # 各クラスのインスタンス化
    base_config = BaseConfig()
    assert base_config is not None

    config_manager = ConfigManager()
    assert config_manager is not None


def test_ui_module_init() -> None:
    """ui モジュールの __init__.py 実行テスト"""
    from kumihan_formatter.ui.console_ui import ConsoleUI

    # モジュールの初期化によるカバレッジ向上
    ui = ConsoleUI()
    assert ui is not None

    # プロパティのアクセス
    assert hasattr(ui, "console")  # richのConsoleインスタンス


@pytest.mark.unit
def test_integrated_functionality() -> None:
    """統合機能テスト - 複数モジュール連携"""
    # 設定の作成
    from kumihan_formatter.config.base_config import BaseConfig

    config = BaseConfig()

    # UIの作成
    from kumihan_formatter.ui.console_ui import ConsoleUI

    ui = ConsoleUI()

    # ファイル操作の作成
    from kumihan_formatter.core.file_operations import FileOperations

    file_ops = FileOperations(ui=ui)  # UIを注入

    # 統合確認
    assert config is not None
    assert ui is not None
    assert file_ops is not None
    assert file_ops.ui is ui

    # 設定の実際の使用
    css_vars: Dict[str, Any] = config.get_css_variables()
    assert len(css_vars) > 0

    # UIの実際の使用
    ui.info("Integration", "Test completed successfully")
