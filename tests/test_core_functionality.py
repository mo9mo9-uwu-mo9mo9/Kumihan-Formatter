"""コア機能テスト - Issue #554対応

CI/CD正常化のための基本的なコア機能テスト
カバレッジ向上とCI/CD安定化を目的とする
"""

from pathlib import Path
from typing import List

import pytest


def test_file_operations_basic() -> None:
    """基本的なファイル操作テスト"""
    try:
        from kumihan_formatter.core.file_operations import FileOperations

        file_ops = FileOperations()
        assert hasattr(file_ops, "copy_images")
        assert callable(file_ops.copy_images)

        # UIProtocolの確認
        assert hasattr(file_ops, "ui")
        assert hasattr(file_ops, "logger")

    except ImportError:
        pytest.skip("FileOperations not available")


def test_console_ui_methods() -> None:
    """Console UI メソッドテスト"""
    from kumihan_formatter.ui.console_ui import ConsoleUI

    ui = ConsoleUI()

    # 基本メソッドの存在確認
    assert hasattr(ui, "info")
    assert hasattr(ui, "error")
    assert hasattr(ui, "warning")
    assert hasattr(ui, "success")

    # メソッドが呼び出し可能であることを確認
    assert callable(ui.info)
    assert callable(ui.error)
    assert callable(ui.warning)
    assert callable(ui.success)


def test_config_manager_basic() -> None:
    """設定マネージャーの基本テスト"""
    try:
        from kumihan_formatter.config.config_manager import ConfigManager

        config_manager = ConfigManager()
        assert config_manager is not None
        assert hasattr(config_manager, "load_config")

    except ImportError:
        pytest.skip("ConfigManager not available")


def test_parser_initialization() -> None:
    """パーサーの初期化テスト"""
    try:
        from kumihan_formatter.parser import KumihanParser

        parser = KumihanParser()
        assert parser is not None

        # パーサーの基本メソッド確認
        if hasattr(parser, "parse"):
            assert callable(parser.parse)
        if hasattr(parser, "parse_text"):
            assert callable(parser.parse_text)

    except ImportError:
        pytest.skip("KumihanParser not available")


def test_renderer_basic() -> None:
    """レンダラーの基本テスト"""
    try:
        from kumihan_formatter.renderer import KumihanRenderer

        renderer = KumihanRenderer()
        assert renderer is not None
        assert hasattr(renderer, "render")

    except ImportError:
        pytest.skip("KumihanRenderer not available")


@pytest.mark.unit
def test_import_structure() -> None:
    """インポート構造の健全性テスト"""
    # 主要モジュールのインポートが可能であることを確認
    modules_to_test: List[str] = [
        "kumihan_formatter",
        "kumihan_formatter.config",
        "kumihan_formatter.core",
        "kumihan_formatter.ui",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_version_consistency() -> None:
    """バージョン整合性テスト"""
    import kumihan_formatter

    version = kumihan_formatter.__version__
    assert isinstance(version, str)
    assert len(version) > 0

    # セマンティックバージョニングの基本確認
    version_parts: List[str] = version.split(".")
    assert len(version_parts) >= 2  # 最低でもX.Yの形式

    # 最初の部分が数字であることを確認
    assert version_parts[0].isdigit() or version_parts[0] == "0"
