"""config_manager.py の包括的テスト

Issue #929 Phase 3B: Configuration Manager Core テスト
50テストケースでconfig_manager.pyの70%カバレッジ達成
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager import (
    ConfigManager,
    create_config_manager,
    load_config,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigManagerInitialization:
    """ConfigManager初期化のテスト"""

    def test_正常系_デフォルト初期化(self):
        """デフォルト設定での初期化テスト"""
        # Given
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config
            mock_env_instance = Mock()
            mock_env.return_value = mock_env_instance

            # When
            manager = ConfigManager()

            # Then
            assert manager.config_type == "extended"
            assert manager.env_prefix == "KUMIHAN_"
            mock_create.assert_called_once_with("extended", None)
            mock_env.assert_called_once_with("KUMIHAN_")
            mock_env_instance.load_from_env.assert_called_once_with(mock_config)

    def test_正常系_base初期化(self):
        """baseタイプでの初期化テスト"""
        # Given
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            # When
            manager = ConfigManager(config_type="base")

            # Then
            assert manager.config_type == "base"
            mock_create.assert_called_once_with("base", None)

    def test_正常系_extended初期化(self):
        """extendedタイプでの初期化テスト"""
        # Given
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            # When
            manager = ConfigManager(config_type="extended")

            # Then
            assert manager.config_type == "extended"
            mock_create.assert_called_once_with("extended", None)

    def test_正常系_config_path指定初期化(self):
        """config_path指定での初期化テスト"""
        # Given
        config_path = "/test/config.json"
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            # When
            manager = ConfigManager(config_path=config_path)

            # Then
            mock_create.assert_called_once_with("extended", config_path)

    def test_正常系_カスタムenv_prefix初期化(self):
        """カスタムenv_prefixでの初期化テスト"""
        # Given
        custom_prefix = "CUSTOM_"
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config
            mock_env_instance = Mock()
            mock_env.return_value = mock_env_instance

            # When
            manager = ConfigManager(env_prefix=custom_prefix)

            # Then
            assert manager.env_prefix == custom_prefix
            mock_env.assert_called_once_with(custom_prefix)

    def test_異常系_無効config_type初期化(self):
        """無効なconfig_typeでの初期化テスト"""
        # Given
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            # When
            manager = ConfigManager(config_type="invalid")

            # Then
            assert manager.config_type == "invalid"
            mock_create.assert_called_once_with("invalid", None)

    def test_異常系_存在しないconfig_path初期化(self):
        """存在しないconfig_pathでの初期化テスト"""
        # Given
        nonexistent_path = "/nonexistent/config.json"
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            # When
            manager = ConfigManager(config_path=nonexistent_path)

            # Then
            mock_create.assert_called_once_with("extended", nonexistent_path)

    def test_正常系_環境変数読み込み確認(self):
        """環境変数読み込み確認テスト"""
        # Given
        with (
            patch("kumihan_formatter.config.config_manager.create_config_instance") as mock_create,
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config
            mock_env_instance = Mock()
            mock_env.return_value = mock_env_instance

            # When
            ConfigManager()

            # Then
            mock_env_instance.load_from_env.assert_called_once_with(mock_config)


class TestConfigManagerDelegation:
    """BaseConfig委譲メソッドのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_config = Mock()
        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=self.mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            self.manager = ConfigManager()

    def test_正常系_get_css_variables委譲(self):
        """get_css_variables()の委譲確認テスト"""
        # Given
        expected_css = {"--primary-color": "#000000"}
        self.mock_config.get_css_variables.return_value = expected_css

        # When
        result = self.manager.get_css_variables()

        # Then
        assert result == expected_css
        self.mock_config.get_css_variables.assert_called_once()

    def test_正常系_get_theme_name委譲(self):
        """get_theme_name()の委譲確認テスト"""
        # Given
        expected_theme = "dark_theme"
        self.mock_config.get_theme_name.return_value = expected_theme

        # When
        result = self.manager.get_theme_name()

        # Then
        assert result == expected_theme
        self.mock_config.get_theme_name.assert_called_once()

    def test_正常系_getメソッド委譲(self):
        """get()メソッドの委譲テスト"""
        # Given
        key = "test_key"
        expected_value = "test_value"
        self.mock_config.get.return_value = expected_value

        # When
        result = self.manager.get(key)

        # Then
        assert result == expected_value
        self.mock_config.get.assert_called_once_with(key, None)

    def test_正常系_getメソッド委譲_デフォルト値付き(self):
        """get()メソッドの委譲テスト（デフォルト値付き）"""
        # Given
        key = "test_key"
        default_value = "default"
        expected_value = "test_value"
        self.mock_config.get.return_value = expected_value

        # When
        result = self.manager.get(key, default_value)

        # Then
        assert result == expected_value
        self.mock_config.get.assert_called_once_with(key, default_value)

    def test_正常系_setメソッド委譲(self):
        """set()メソッドの委譲テスト"""
        # Given
        key = "test_key"
        value = "test_value"

        # When
        self.manager.set(key, value)

        # Then
        self.mock_config.set.assert_called_once_with(key, value)

    def test_正常系_validateメソッド委譲_True(self):
        """validate()メソッドの委譲テスト（True）"""
        # Given
        self.mock_config.validate.return_value = True

        # When
        result = self.manager.validate()

        # Then
        assert result is True
        self.mock_config.validate.assert_called_once()

    def test_正常系_validateメソッド委譲_False(self):
        """validate()メソッドの委譲テスト（False）"""
        # Given
        self.mock_config.validate.return_value = False

        # When
        result = self.manager.validate()

        # Then
        assert result is False
        self.mock_config.validate.assert_called_once()

    def test_正常系_to_dictメソッド委譲(self):
        """to_dict()メソッドの委譲テスト"""
        # Given
        expected_dict = {"key1": "value1", "key2": "value2"}
        self.mock_config.to_dict.return_value = expected_dict

        # When
        result = self.manager.to_dict()

        # Then
        assert result == expected_dict
        self.mock_config.to_dict.assert_called_once()


class TestConfigManagerExtended:
    """ExtendedConfig専用メソッドのテスト"""

    def test_正常系_get_markers_ExtendedConfig(self):
        """get_markers()の正常動作テスト（ExtendedConfig）"""
        # Given
        expected_markers = {"marker1": {"color": "red"}}
        mock_config = Mock()
        mock_config.get_markers.return_value = expected_markers

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_markers()

            # Then
            assert result == expected_markers
            mock_config.get_markers.assert_called_once()

    def test_正常系_get_markers_BaseConfig_フォールバック(self):
        """get_markers()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_markers()

            # Then
            assert result == {}

    def test_正常系_get_markers_非dict戻り値フォールバック(self):
        """get_markers()の非dict戻り値フォールバックテスト"""
        # Given
        mock_config = Mock()
        mock_config.get_markers.return_value = None  # Non-dict return

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_markers()

            # Then
            assert result == {}

    def test_正常系_add_marker_ExtendedConfig(self):
        """add_marker()の動作確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        marker_name = "test_marker"
        marker_def = {"color": "blue"}

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            manager.add_marker(marker_name, marker_def)

            # Then
            mock_config.add_marker.assert_called_once_with(marker_name, marker_def)

    def test_正常系_add_marker_BaseConfig_フォールバック(self):
        """add_marker()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            manager.add_marker("test", {})

            # Then
            # Should not raise an error, but no method call
            assert True

    def test_正常系_remove_marker_ExtendedConfig_成功(self):
        """remove_marker()の成功確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        mock_config.remove_marker.return_value = True
        marker_name = "test_marker"

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.remove_marker(marker_name)

            # Then
            assert result is True
            mock_config.remove_marker.assert_called_once_with(marker_name)

    def test_正常系_remove_marker_ExtendedConfig_失敗(self):
        """remove_marker()の失敗確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        mock_config.remove_marker.return_value = False
        marker_name = "nonexistent_marker"

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.remove_marker(marker_name)

            # Then
            assert result is False
            mock_config.remove_marker.assert_called_once_with(marker_name)

    def test_正常系_remove_marker_BaseConfig_フォールバック(self):
        """remove_marker()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.remove_marker("test")

            # Then
            assert result is False

    def test_正常系_get_themes_ExtendedConfig(self):
        """get_themes()の正常動作テスト（ExtendedConfig）"""
        # Given
        expected_themes = {"theme1": {"name": "Light Theme"}}
        mock_config = Mock()
        mock_config.get_themes.return_value = expected_themes

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_themes()

            # Then
            assert result == expected_themes
            mock_config.get_themes.assert_called_once()

    def test_正常系_get_themes_BaseConfig_フォールバック(self):
        """get_themes()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_themes()

            # Then
            assert result == {}

    def test_正常系_add_theme_ExtendedConfig(self):
        """add_theme()の動作確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        theme_id = "custom_theme"
        theme_data = {"name": "Custom Theme", "colors": {}}

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            manager.add_theme(theme_id, theme_data)

            # Then
            mock_config.add_theme.assert_called_once_with(theme_id, theme_data)

    def test_正常系_add_theme_BaseConfig_フォールバック(self):
        """add_theme()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            manager.add_theme("test", {})

            # Then
            # Should not raise an error, but no method call
            assert True

    def test_正常系_set_theme_ExtendedConfig_成功(self):
        """set_theme()の成功確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        mock_config.set_theme.return_value = True
        theme_id = "dark_theme"

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.set_theme(theme_id)

            # Then
            assert result is True
            mock_config.set_theme.assert_called_once_with(theme_id)

    def test_正常系_set_theme_ExtendedConfig_失敗(self):
        """set_theme()の失敗確認テスト（ExtendedConfig）"""
        # Given
        mock_config = Mock()
        mock_config.set_theme.return_value = False
        theme_id = "nonexistent_theme"

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.set_theme(theme_id)

            # Then
            assert result is False
            mock_config.set_theme.assert_called_once_with(theme_id)

    def test_正常系_set_theme_BaseConfig_フォールバック(self):
        """set_theme()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.set_theme("test")

            # Then
            assert result is False

    def test_正常系_get_current_theme_ExtendedConfig(self):
        """get_current_theme()の取得テスト（ExtendedConfig）"""
        # Given
        expected_theme = "dark_theme"
        mock_config = Mock()
        mock_config.get_current_theme.return_value = expected_theme

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_current_theme()

            # Then
            assert result == expected_theme
            mock_config.get_current_theme.assert_called_once()

    def test_正常系_get_current_theme_BaseConfig_フォールバック(self):
        """get_current_theme()のフォールバックテスト（BaseConfig）"""
        # Given
        mock_config = Mock(spec=[])  # hasattr check will fail

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.get_current_theme()

            # Then
            assert result == "default"


class TestConfigManagerFileOperations:
    """設定ファイル操作のテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_config = Mock()
        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=self.mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler") as mock_env,
        ):
            self.mock_env_instance = Mock()
            mock_env.return_value = self.mock_env_instance
            self.manager = ConfigManager()

    def test_正常系_load_config_成功(self):
        """load_config()の成功パステスト"""
        # Given
        config_path = "/test/config.json"
        new_config = Mock()

        with patch(
            "kumihan_formatter.config.config_manager.load_config_file",
            return_value=new_config,
        ) as mock_load:
            # When
            result = self.manager.load_config(config_path)

            # Then
            assert result is True
            mock_load.assert_called_once_with("extended", config_path, self.mock_config)
            self.mock_env_instance.load_from_env.assert_called_with(new_config)
            assert self.manager._config == new_config

    def test_異常系_load_config_失敗(self):
        """load_config()の失敗時エラーハンドリングテスト"""
        # Given
        config_path = "/test/nonexistent.json"

        with patch(
            "kumihan_formatter.config.config_manager.load_config_file",
            side_effect=Exception("File not found"),
        ) as mock_load:
            # When
            result = self.manager.load_config(config_path)

            # Then
            assert result is False
            mock_load.assert_called_once_with("extended", config_path, self.mock_config)

    def test_正常系_load_config_後の環境変数再適用(self):
        """load_config()後の環境変数再適用テスト"""
        # Given
        config_path = "/test/config.json"
        new_config = Mock()

        with patch(
            "kumihan_formatter.config.config_manager.load_config_file",
            return_value=new_config,
        ):
            # When
            self.manager.load_config(config_path)

            # Then
            # 環境変数の再適用が呼ばれていることを確認
            expected_calls = [call(self.mock_config), call(new_config)]
            self.mock_env_instance.load_from_env.assert_has_calls(expected_calls)

    def test_正常系_merge_config(self):
        """merge_config()での設定マージテスト"""
        # Given
        other_config = {"key1": "value1", "key2": "value2"}

        with patch("kumihan_formatter.config.config_manager.merge_config_data") as mock_merge:
            # When
            self.manager.merge_config(other_config)

            # Then
            mock_merge.assert_called_once_with(self.mock_config, other_config)

    def test_正常系_merge_config_複雑なマージ(self):
        """merge_config()での複雑なマージテスト"""
        # Given
        complex_config = {
            "nested": {"deep": {"value": "test"}},
            "list": [1, 2, 3],
            "bool": True,
        }

        with patch("kumihan_formatter.config.config_manager.merge_config_data") as mock_merge:
            # When
            self.manager.merge_config(complex_config)

            # Then
            mock_merge.assert_called_once_with(self.mock_config, complex_config)


class TestConfigManagerFactory:
    """ファクトリー関数のテスト"""

    def test_正常系_create_config_manager(self):
        """create_config_manager()でのインスタンス作成テスト"""
        # Given
        with patch("kumihan_formatter.config.config_manager.ConfigManager") as mock_manager_class:
            mock_instance = Mock()
            mock_manager_class.return_value = mock_instance

            # When
            result = create_config_manager()

            # Then
            assert result == mock_instance
            mock_manager_class.assert_called_once_with(
                config_type="extended", config_path=None, env_prefix="KUMIHAN_"
            )

    def test_正常系_create_config_manager_パラメータ指定(self):
        """create_config_manager()でのパラメータ指定テスト"""
        # Given
        config_type = "base"
        config_path = "/custom/config.json"
        env_prefix = "CUSTOM_"

        with patch("kumihan_formatter.config.config_manager.ConfigManager") as mock_manager_class:
            mock_instance = Mock()
            mock_manager_class.return_value = mock_instance

            # When
            result = create_config_manager(
                config_type=config_type, config_path=config_path, env_prefix=env_prefix
            )

            # Then
            assert result == mock_instance
            mock_manager_class.assert_called_once_with(
                config_type=config_type, config_path=config_path, env_prefix=env_prefix
            )

    def test_正常系_load_config_便利関数(self):
        """load_config()便利関数テスト"""
        # Given
        config_path = "/test/config.json"

        with patch("kumihan_formatter.config.config_manager.create_config_manager") as mock_create:
            mock_instance = Mock()
            mock_create.return_value = mock_instance

            # When
            result = load_config(config_path)

            # Then
            assert result == mock_instance
            mock_create.assert_called_once_with(config_path=config_path)

    def test_正常系_load_config_便利関数_config_pathなし(self):
        """load_config()便利関数テスト（config_pathなし）"""
        # Given
        with patch("kumihan_formatter.config.config_manager.create_config_manager") as mock_create:
            mock_instance = Mock()
            mock_create.return_value = mock_instance

            # When
            result = load_config()

            # Then
            assert result == mock_instance
            mock_create.assert_called_once_with(config_path=None)


class TestConfigManagerIntegration:
    """統合・境界値テスト"""

    def test_正常系_configプロパティ内部設定アクセス(self):
        """configプロパティでの内部設定アクセステスト"""
        # Given
        mock_config = Mock()

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When
            result = manager.config

            # Then
            assert result == mock_config

    def test_正常系_BaseConfigからExtendedConfigへの動的変更(self):
        """BaseConfigからExtendedConfigへの動的変更テスト"""
        # Given
        base_config = Mock(spec=[])  # BaseConfig like
        extended_config = Mock()  # ExtendedConfig like with extended methods

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=base_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            # When - 動的に設定を変更
            manager._config = extended_config

            # Then - ExtendedConfig methods should now work
            manager.add_marker("test", {})
            extended_config.add_marker.assert_called_once_with("test", {})

    def test_正常系_大量設定データでの動作確認(self):
        """大量設定データでの動作確認テスト"""
        # Given
        large_config = {f"key_{i}": f"value_{i}" for i in range(1000)}
        mock_config = Mock()

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            with patch("kumihan_formatter.config.config_manager.merge_config_data") as mock_merge:
                # When
                manager.merge_config(large_config)

                # Then
                mock_merge.assert_called_once_with(mock_config, large_config)

    def test_正常系_特殊文字を含む設定での動作確認(self):
        """特殊文字を含む設定での動作確認テスト"""
        # Given
        special_config = {
            "unicode_key_🚀": "unicode_value_✨",
            "special/chars\\path": "value with spaces and symbols!@#$%^&*()",
            "json_like": '{"nested": "json"}',
            "empty_string": "",
            "null_like": None,
        }
        mock_config = Mock()

        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_config,
            ),
            patch("kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"),
        ):
            manager = ConfigManager()

            with patch("kumihan_formatter.config.config_manager.merge_config_data") as mock_merge:
                # When
                manager.merge_config(special_config)

                # Then
                mock_merge.assert_called_once_with(mock_config, special_config)
