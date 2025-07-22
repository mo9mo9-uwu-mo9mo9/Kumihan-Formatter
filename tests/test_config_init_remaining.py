"""config/__init__.py の未カバー部分テスト

Phase 1 最終目標18%達成のための補完テスト
未カバー関数: create_simple_config, get_default_config, reset_default_config
"""

from unittest.mock import Mock, patch

import pytest

import kumihan_formatter.config as config_module
from kumihan_formatter.config import (
    Config,
    ConfigManager,
    create_simple_config,
    get_default_config,
    reset_default_config,
)


class TestCreateSimpleConfig:
    """create_simple_config 関数のテスト"""

    @patch("kumihan_formatter.config.create_config_manager")
    def test_create_simple_config(self, mock_create):
        """create_simple_config 関数の基本動作テスト"""
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        result = create_simple_config()

        # 正しい引数でcreate_config_managerが呼ばれることを確認
        mock_create.assert_called_once_with(config_type="base")
        assert result == mock_manager


class TestDefaultConfigManagement:
    """デフォルト設定管理のテスト"""

    def setup_method(self):
        """各テスト前にデフォルト設定をリセット"""
        reset_default_config()

    def teardown_method(self):
        """各テスト後にデフォルト設定をリセット"""
        reset_default_config()

    @patch("kumihan_formatter.config.create_config_manager")
    def test_get_default_config_first_call(self, mock_create):
        """get_default_config 初回呼び出しのテスト"""
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        result = get_default_config()

        # create_config_managerが呼ばれることを確認
        mock_create.assert_called_once_with()
        assert result == mock_manager

    @patch("kumihan_formatter.config.create_config_manager")
    def test_get_default_config_cached(self, mock_create):
        """get_default_config キャッシュ動作のテスト"""
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        # 2回呼び出す
        result1 = get_default_config()
        result2 = get_default_config()

        # create_config_managerは1回のみ呼ばれることを確認
        mock_create.assert_called_once_with()
        assert result1 == mock_manager
        assert result2 == mock_manager
        assert result1 is result2  # 同じインスタンス

    @patch("kumihan_formatter.config.create_config_manager")
    def test_reset_default_config(self, mock_create):
        """reset_default_config 関数のテスト"""
        mock_manager1 = Mock()
        mock_manager2 = Mock()
        mock_create.side_effect = [mock_manager1, mock_manager2]

        # 最初の呼び出し
        result1 = get_default_config()
        assert result1 == mock_manager1

        # リセット
        reset_default_config()

        # リセット後の呼び出し
        result2 = get_default_config()
        assert result2 == mock_manager2

        # create_config_managerが2回呼ばれることを確認
        assert mock_create.call_count == 2

    def test_reset_default_config_multiple_times(self):
        """reset_default_config 複数回呼び出しのテスト"""
        # 複数回リセットしてもエラーが発生しない
        reset_default_config()
        reset_default_config()
        reset_default_config()

        # モジュールレベル変数が適切に設定されることを確認
        assert config_module._default_config is None


class TestModuleStructure:
    """モジュール構造のテスト"""

    def test_all_exports(self):
        """__all__ エクスポートの確認"""
        expected_exports = [
            "BaseConfig",
            "ExtendedConfig",
            "ConfigManager",
            "Config",
            "create_config_manager",
            "load_config",
        ]

        assert set(config_module.__all__) == set(expected_exports)

    def test_config_alias(self):
        """Config エイリアスの確認"""
        assert Config is ConfigManager

    def test_imports_availability(self):
        """インポート可能性の確認"""
        from kumihan_formatter.config import (
            BaseConfig,
            Config,
            ConfigManager,
            ExtendedConfig,
            create_config_manager,
            create_simple_config,
            get_default_config,
            load_config,
            reset_default_config,
        )

        # 全ての関数/クラスがインポート可能であることを確認
        assert BaseConfig is not None
        assert ExtendedConfig is not None
        assert ConfigManager is not None
        assert Config is not None
        assert create_config_manager is not None
        assert load_config is not None
        assert create_simple_config is not None
        assert get_default_config is not None
        assert reset_default_config is not None


class TestIntegrationWorkflow:
    """統合ワークフローテスト"""

    def setup_method(self):
        """テスト前にデフォルト設定をリセット"""
        reset_default_config()

    def teardown_method(self):
        """テスト後にデフォルト設定をリセット"""
        reset_default_config()

    @patch("kumihan_formatter.config.create_config_manager")
    def test_full_workflow(self, mock_create):
        """完全なワークフローテスト"""
        mock_simple = Mock()
        mock_default = Mock()
        mock_create.side_effect = [mock_simple, mock_default]

        # 簡易設定作成
        simple_config = create_simple_config()
        assert simple_config == mock_simple

        # デフォルト設定取得
        default_config = get_default_config()
        assert default_config == mock_default

        # 設定リセット
        reset_default_config()

        # create_config_managerの呼び出し履歴確認
        expected_calls = [
            ((), {"config_type": "base"}),  # create_simple_config
            ((), {}),  # get_default_config
        ]
        actual_calls = [(call.args, call.kwargs) for call in mock_create.call_args_list]
        assert actual_calls == expected_calls
