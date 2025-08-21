"""config/__init__.py の包括的テスト

Issue #929 Phase 3C: __init__.py テスト
10テストケースで設定APIエイリアスと便利関数の70%カバレッジ達成
"""

import warnings
from unittest.mock import Mock, patch

import pytest

# テスト対象のインポート
from kumihan_formatter.config import (
    Config,
    ConfigManager,
    __all__,
    create_simple_config,
    get_default_config,
    reset_default_config,
)


class TestModuleImports:
    """モジュールインポートとエクスポートのテスト"""

    def test_正常系_モジュール__all__エクスポート確認(self):
        """__all__リストに適切なエクスポート項目が含まれることを確認"""
        # Given: __all__リスト
        expected_exports = [
            "BaseConfig",
            "ExtendedConfig",
            "ConfigManager",
            "Config",
            "create_config_manager",
            "load_config",
        ]

        # When: __all__の内容を確認
        # Then: 期待される項目が全て含まれる
        for item in expected_exports:
            assert item in __all__

    def test_正常系_Configエイリアス確認(self):
        """ConfigがConfigManagerのエイリアスであることを確認"""
        # Given: ConfigとConfigManagerのインポート
        # When: エイリアスを確認
        # Then: ConfigはConfigManagerと同じオブジェクト
        assert Config is ConfigManager


class TestCreateSimpleConfig:
    """create_simple_config 関数のテスト"""

    @patch("kumihan_formatter.config.create_config_manager")
    @patch("warnings.warn")
    def test_正常系_create_simple_config_関数呼び出し(
        self, mock_warn, mock_create_config_manager
    ):
        """create_simple_config関数が適切に呼び出されることを確認"""
        # Given: モックされたcreate_config_manager
        mock_config = Mock()
        mock_create_config_manager.return_value = mock_config

        # When: create_simple_config関数を呼び出し
        result = create_simple_config()

        # Then: create_config_managerがbaseタイプで呼び出される
        mock_create_config_manager.assert_called_once_with(config_type="base")
        assert result == mock_config

    @patch("kumihan_formatter.config.create_config_manager")
    @patch("warnings.warn")
    def test_正常系_create_simple_config_baseタイプ返却(
        self, mock_warn, mock_create_config_manager
    ):
        """create_simple_configがbaseタイプの設定を返すことを確認"""
        # Given: モックされた設定オブジェクト
        mock_config = Mock()
        mock_create_config_manager.return_value = mock_config

        # When: simple configを作成
        result = create_simple_config()

        # Then: baseタイプで設定が作成される
        mock_create_config_manager.assert_called_once_with(config_type="base")
        assert result == mock_config

    @patch("kumihan_formatter.config.create_config_manager")
    def test_正常系_create_simple_config_deprecation警告(
        self, mock_create_config_manager
    ):
        """create_simple_config呼び出し時にdeprecation警告が出ることを確認"""
        # Given: モックされたcreate_config_manager
        mock_create_config_manager.return_value = Mock()

        # When: deprecation警告をキャッチしてcreate_simple_configを呼び出し
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            create_simple_config()

            # Then: DeprecationWarningが出力される
            assert len(caught_warnings) == 1
            assert issubclass(caught_warnings[0].category, DeprecationWarning)
            assert "create_simple_config()は非推奨です" in str(
                caught_warnings[0].message
            )


class TestGetDefaultConfig:
    """get_default_config 関数のテスト"""

    def setup_method(self):
        """各テストメソッド前のセットアップ"""
        # デフォルト設定をリセット
        reset_default_config()

    @patch("kumihan_formatter.config.create_config_manager")
    def test_正常系_get_default_config_初回呼び出し(self, mock_create_config_manager):
        """初回呼び出し時に新しい設定が作成されることを確認"""
        # Given: モックされたcreate_config_manager
        mock_config = Mock()
        mock_create_config_manager.return_value = mock_config

        # When: 初回でデフォルト設定を取得
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = get_default_config()

        # Then: create_config_managerが呼び出される
        mock_create_config_manager.assert_called_once()
        assert result == mock_config

    @patch("kumihan_formatter.config.create_config_manager")
    def test_正常系_get_default_config_2回目キャッシュ(
        self, mock_create_config_manager
    ):
        """2回目の呼び出しでキャッシュされた設定が返されることを確認"""
        # Given: 初回呼び出し後の状態
        mock_config = Mock()
        mock_create_config_manager.return_value = mock_config

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            first_call = get_default_config()

            # When: 2回目の呼び出し
            second_call = get_default_config()

        # Then: create_config_managerは1回のみ呼び出され、同じオブジェクトが返される
        mock_create_config_manager.assert_called_once()
        assert first_call is second_call
        assert second_call == mock_config

    @patch("kumihan_formatter.config.create_config_manager")
    def test_正常系_get_default_config_deprecation警告(
        self, mock_create_config_manager
    ):
        """get_default_config呼び出し時にdeprecation警告が出ることを確認"""
        # Given: モックされたcreate_config_manager
        mock_create_config_manager.return_value = Mock()

        # When: deprecation警告をキャッチしてget_default_configを呼び出し
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            get_default_config()

            # Then: DeprecationWarningが出力される
            assert len(caught_warnings) == 1
            assert issubclass(caught_warnings[0].category, DeprecationWarning)
            assert "get_default_config()は非推奨です" in str(caught_warnings[0].message)


class TestResetDefaultConfig:
    """reset_default_config 関数のテスト"""

    def test_正常系_reset_default_config_グローバルリセット(self):
        """reset_default_configがグローバル変数をリセットすることを確認"""
        # Given: デフォルト設定が既に存在する状態
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # 最初にデフォルト設定を作成
            first_config = get_default_config()
            assert first_config is not None

            # When: デフォルト設定をリセット
            reset_default_config()

            # Then: 次回の呼び出しで新しい設定が作成される
            second_config = get_default_config()

        # リセット後は異なるインスタンスが返される
        assert first_config is not second_config

    def test_正常系_reset_default_config_リセット後再作成(self):
        """リセット後に再度get_default_configを呼び出せることを確認"""
        # Given: リセット後の状態
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # 初回作成
            first_config = get_default_config()

            # When: リセット
            reset_default_config()

            # リセット後に再作成
            second_config = get_default_config()

        # Then: 異なるオブジェクトが返される（正しく新しいインスタンスが作成される）
        assert first_config is not second_config
        assert second_config is not None
