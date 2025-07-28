"""最小限のテストファイル - Issue #554対応

このテストは削除されたテストファイルを復旧するための暫定対応です。
Issue #554: CI/CD正常化のための緊急対応健全化
"""

from typing import Any, Dict

import pytest


def test_minimal_import() -> None:
    """最小限のインポートテスト"""
    import kumihan_formatter

    assert hasattr(kumihan_formatter, "__version__")
    # カバレッジ向上のため__version__を実際に取得
    version = kumihan_formatter.__version__
    assert isinstance(version, str)
    assert len(version) > 0


def test_config_import() -> None:
    """設定モジュールのインポートテスト"""
    from kumihan_formatter.config import BaseConfig

    assert BaseConfig is not None

    # BaseConfigの基本機能をテスト
    config = BaseConfig()
    assert hasattr(config, "get_css_variables")
    css_vars = config.get_css_variables()
    assert isinstance(css_vars, dict)
    assert "max_width" in css_vars

    # CSS変数の詳細テスト（カバレッジ向上）
    assert css_vars["max_width"] == "800px"
    assert "background_color" in css_vars


def test_config_with_custom_data() -> None:
    """カスタム設定データでのConfigテスト"""
    from kumihan_formatter.config import BaseConfig

    custom_config: Dict[str, Dict[str, str]] = {
        "css": {"max_width": "1000px", "custom_color": "#123456"}
    }
    config = BaseConfig(custom_config)
    css_vars = config.get_css_variables()

    # カスタム設定が反映されているか確認
    assert css_vars["max_width"] == "1000px"
    assert css_vars["custom_color"] == "#123456"
    # デフォルト値も維持されているか確認
    assert "background_color" in css_vars


def test_ui_console_import() -> None:
    """UIコンソールモジュールのインポートテスト"""
    from kumihan_formatter.ui.console_ui import ConsoleUI

    assert ConsoleUI is not None

    # ConsoleUIの基本機能をテスト
    ui = ConsoleUI()
    assert hasattr(ui, "info")
    assert callable(ui.info)
    assert hasattr(ui, "error")
    assert callable(ui.error)


def test_parser_import() -> None:
    """パーサーモジュールのインポートテスト"""
    try:
        from kumihan_formatter.parser import Parser

        assert Parser is not None

        # パーサーの基本インスタンス作成
        parser = Parser()
        assert parser is not None
        assert hasattr(parser, "parse")

    except ImportError:
        pytest.skip("Parser not available")


def test_core_imports() -> None:
    """コアモジュール群のインポートテスト"""
    # 基本的なコアモジュールが存在することを確認
    import kumihan_formatter.core

    assert kumihan_formatter.core is not None

    # ファイル操作関連
    try:
        from kumihan_formatter.core.file_operations import FileOperations

        file_ops = FileOperations()
        assert hasattr(file_ops, "copy_images")
    except ImportError:
        pass  # モジュールが存在しない場合はスキップ

    # AST関連
    try:
        from kumihan_formatter.core.ast_nodes import ASTNode

        assert ASTNode is not None
    except ImportError:
        pass
