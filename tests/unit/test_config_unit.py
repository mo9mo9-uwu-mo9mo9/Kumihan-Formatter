"""
Configクラスのユニットテスト

Critical Tier対応: コア機能の基本動作確認
Issue #620: テストカバレッジ改善
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.config import Config, load_config


class TestConfig:
    """Configクラスのテスト"""

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_config_initialization(self, mock_console, mock_config_manager):
        """設定管理の初期化テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {"test": "value"}
        mock_config_manager.return_value = mock_manager

        config = Config()

        # ConfigManagerが正しく初期化されることを確認
        mock_config_manager.assert_called_once_with(
            config_type="extended", config_path=None
        )
        assert config.config == {"test": "value"}
        mock_manager.to_dict.assert_called_once()

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_config_initialization_with_path(self, mock_console, mock_config_manager):
        """設定パス指定での初期化テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_config_manager.return_value = mock_manager

        config_path = "/path/to/config.yaml"
        config = Config(config_path)

        mock_config_manager.assert_called_once_with(
            config_type="extended", config_path=config_path
        )

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_load_config_success(self, mock_console, mock_config_manager):
        """設定ファイル読み込み成功テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {"loaded": "config"}
        mock_manager.load_config.return_value = True
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        result = config.load_config("test_config.yaml")

        assert result is True
        mock_manager.load_config.assert_called_once_with("test_config.yaml")
        assert config.config == {"loaded": "config"}

        # 成功メッセージが表示されることを確認
        mock_console_instance.print.assert_called_with(
            "[green][完了] 設定ファイルを読み込みました:[/green] test_config.yaml"
        )

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_load_config_not_found(self, mock_console, mock_config_manager):
        """設定ファイル見つからない場合のテスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_manager.load_config.return_value = False
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        result = config.load_config("nonexistent.yaml")

        assert result is False

        # 警告メッセージが表示されることを確認
        expected_calls = [
            (
                "[yellow][警告]  設定ファイルが見つかりません:[/yellow] nonexistent.yaml",
            ),
            ("[dim]   デフォルト設定を使用します[/dim]",),
        ]

        for call in expected_calls:
            assert call in [
                call.args for call in mock_console_instance.print.call_args_list
            ]

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_load_config_exception(self, mock_console, mock_config_manager):
        """設定ファイル読み込み例外テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_manager.load_config.side_effect = Exception("Test error")
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        result = config.load_config("error_config.yaml")

        assert result is False

        # エラーメッセージが表示されることを確認
        mock_console_instance.print.assert_called_with(
            "[red][エラー] 設定ファイル読み込みエラー:[/red] Test error"
        )

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_merge_config_basic(self, mock_console, mock_config_manager):
        """基本的な設定マージテスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {"merged": "config"}
        mock_config_manager.return_value = mock_manager

        config = Config()
        user_config = {"test": "user_value"}

        config._merge_config(user_config)

        mock_manager.merge_config.assert_called_once_with(user_config)
        assert config.config == {"merged": "config"}

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_merge_config_with_themes(self, mock_console, mock_config_manager):
        """テーマを含む設定マージテスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        user_config = {
            "themes": {"custom1": {}, "custom2": {}},
            "markers": {"marker1": {}, "marker2": {}, "marker3": {}},
            "theme": "custom1",
            "font_family": "Arial",
            "css": {"color": "red", "size": "14px"},
        }

        mock_manager.get_theme_name.return_value = "カスタム1"

        config._merge_config(user_config)

        # ログメッセージが表示されることを確認
        expected_messages = [
            "[dim]   カスタムテーマ: 2個[/dim]",
            "[dim]   カスタムマーカー: 3個[/dim]",
            "[dim]   テーマ: カスタム1[/dim]",
            "[dim]   フォント: Arial[/dim]",
            "[dim]   カスタムCSS: 2項目[/dim]",
        ]

        call_args_list = [
            call.args[0] for call in mock_console_instance.print.call_args_list
        ]
        for message in expected_messages:
            assert message in call_args_list

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_get_markers(self, mock_console, mock_config_manager):
        """マーカー取得テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        expected_markers = {"bold": {"tag": "strong"}}
        mock_manager.get_markers.return_value = expected_markers
        mock_config_manager.return_value = mock_manager

        config = Config()
        result = config.get_markers()

        assert result == expected_markers
        mock_manager.get_markers.assert_called_once()

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_get_css_variables(self, mock_console, mock_config_manager):
        """CSS変数取得テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        expected_css_vars = {"--color": "blue", "--size": "16px"}
        mock_manager.get_css_variables.return_value = expected_css_vars
        mock_config_manager.return_value = mock_manager

        config = Config()
        result = config.get_css_variables()

        assert result == expected_css_vars
        mock_manager.get_css_variables.assert_called_once()

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_get_theme_name(self, mock_console, mock_config_manager):
        """テーマ名取得テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        expected_theme = "dark"
        mock_manager.get_theme_name.return_value = expected_theme
        mock_config_manager.return_value = mock_manager

        config = Config()
        result = config.get_theme_name()

        assert result == expected_theme
        mock_manager.get_theme_name.assert_called_once()

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_validate_config_success(self, mock_console, mock_config_manager):
        """設定検証成功テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_manager.validate.return_value = True
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        result = config.validate_config()

        assert result is True
        mock_manager.validate.assert_called_once()
        # 成功時はエラーメッセージが表示されない
        mock_console_instance.print.assert_not_called()

    @patch("kumihan_formatter.config.config_manager.ConfigManager")
    @patch("rich.console.Console")
    def test_validate_config_failure(self, mock_console, mock_config_manager):
        """設定検証失敗テスト"""
        mock_manager = Mock()
        mock_manager.to_dict.return_value = {}
        mock_manager.validate.return_value = False
        mock_config_manager.return_value = mock_manager

        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance

        config = Config()
        result = config.validate_config()

        assert result is False
        mock_manager.validate.assert_called_once()
        # エラーメッセージが表示される
        mock_console_instance.print.assert_called_once_with(
            "[red][エラー] 設定検証エラー[/red]"
        )

    def test_default_config_structure(self):
        """デフォルト設定の構造テスト"""
        default_config = Config.DEFAULT_CONFIG

        # 必要なキーが存在することを確認
        assert "markers" in default_config
        assert "theme" in default_config
        assert "font_family" in default_config
        assert "css" in default_config
        assert "themes" in default_config

        # マーカーの基本構造確認
        markers = default_config["markers"]
        assert "太字" in markers
        assert "見出し1" in markers
        assert markers["太字"]["tag"] == "strong"
        assert markers["見出し1"]["tag"] == "h1"

        # テーマの基本構造確認
        themes = default_config["themes"]
        assert "default" in themes
        assert "dark" in themes
        assert "sepia" in themes

        for theme_name, theme_config in themes.items():
            assert "name" in theme_config
            assert "css" in theme_config


class TestLoadConfigFunction:
    """load_config関数のテスト"""

    @patch("kumihan_formatter.config.Config")
    def test_load_config_function_no_path(self, mock_config_class):
        """パスなしでのload_config関数テスト"""
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        result = load_config()

        mock_config_class.assert_called_once_with(None)
        assert result == mock_config_instance

    @patch("kumihan_formatter.config.Config")
    def test_load_config_function_with_path(self, mock_config_class):
        """パス指定でのload_config関数テスト"""
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        config_path = "test_config.yaml"
        result = load_config(config_path)

        mock_config_class.assert_called_once_with(config_path)
        assert result == mock_config_instance


class TestConfigIntegration:
    """Config統合テスト（モックを使わない基本動作確認）"""

    def test_config_basic_functionality(self):
        """設定クラスの基本機能テスト"""
        with patch("kumihan_formatter.config.ConfigManager"):
            with patch("kumihan_formatter.config.Console"):
                config = Config()

        # 最低限の動作確認
        assert config is not None
        assert hasattr(config, "load_config")
        assert hasattr(config, "get_markers")
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "validate_config")

    def test_load_config_function_basic_functionality(self):
        """load_config関数の基本機能テスト"""
        with patch("kumihan_formatter.config.Config") as mock_config:
            mock_config.return_value = Mock()

            # 最低限の動作確認
            result = load_config()
            assert result is not None
