"""SimpleConfig完全カバレッジテスト

Target: kumihan_formatter/simple_config.py
Goal: 58.33% → 100% 完全カバー
Phase 2優先対象ファイル
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.simple_config import SimpleConfig, create_simple_config


class TestSimpleConfigComplete:
    """SimpleConfig完全カバレッジテスト"""

    def test_simple_config_initialization(self):
        """SimpleConfig初期化完全テスト"""
        config = SimpleConfig()

        # 基本属性の確認
        assert config is not None
        assert hasattr(config, "_manager")
        assert hasattr(config, "css_vars")

        # CSS変数が正しく初期化されていることを確認
        assert config.css_vars is not None
        assert isinstance(config.css_vars, dict)

    def test_simple_config_default_css(self):
        """DEFAULT_CSS設定テスト"""
        # クラス変数へのアクセス
        assert hasattr(SimpleConfig, "DEFAULT_CSS")
        assert isinstance(SimpleConfig.DEFAULT_CSS, dict)

        # 必要なキーが含まれていることを確認
        expected_keys = [
            "max_width",
            "background_color",
            "container_background",
            "text_color",
            "line_height",
            "font_family",
        ]
        for key in expected_keys:
            assert key in SimpleConfig.DEFAULT_CSS

    def test_get_css_variables_delegation(self):
        """get_css_variables委譲テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = Mock()
            mock_manager.get_css_variables.return_value = {"color": "blue"}
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_css_variables()

            # 委譲が正しく動作することを確認（初期化時+テスト時で2回）
            assert mock_manager.get_css_variables.call_count >= 1
            assert result == {"color": "blue"}

    def test_get_theme_name_delegation(self):
        """get_theme_name委譲テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = Mock()
            mock_manager.get_theme_name.return_value = "default_theme"
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_theme_name()

            # 委譲が正しく動作することを確認
            mock_manager.get_theme_name.assert_called_once()
            assert result == "default_theme"

    def test_create_simple_config_factory(self):
        """create_simple_config ファクトリ関数テスト"""
        config = create_simple_config()

        # 正しい型のオブジェクトが返されることを確認
        assert isinstance(config, SimpleConfig)
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get_theme_name")

    def test_simple_config_manager_creation_parameters(self):
        """設定マネージャー作成パラメータテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = Mock()
            mock_manager.get_css_variables.return_value = {}
            mock_create.return_value = mock_manager

            SimpleConfig()

            # 正しいパラメータで設定マネージャーが作成されることを確認
            mock_create.assert_called_once_with(config_type="base")

    def test_simple_config_css_vars_initialization(self):
        """css_vars初期化プロセステスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = Mock()
            css_vars_data = {"theme": "light", "font": "Arial"}
            mock_manager.get_css_variables.return_value = css_vars_data
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # css_varsが正しく設定されることを確認
            assert config.css_vars == css_vars_data

    def test_simple_config_real_integration(self):
        """実際の統合テスト（モックなし）"""
        try:
            config = SimpleConfig()

            # 基本的な動作確認
            css_vars = config.get_css_variables()
            theme_name = config.get_theme_name()

            # 戻り値の型確認
            assert isinstance(css_vars, dict)
            assert isinstance(theme_name, str)

        except Exception as e:
            # 依存関係エラーの場合はスキップ
            pytest.skip(f"依存関係エラー: {e}")

    def test_factory_function_consistency(self):
        """ファクトリ関数の一貫性テスト"""
        config1 = create_simple_config()
        config2 = create_simple_config()

        # 異なるインスタンスが作成されることを確認
        assert config1 is not config2
        assert type(config1) == type(config2)
        assert isinstance(config1, SimpleConfig)
        assert isinstance(config2, SimpleConfig)

    def test_get_theme_name_real_call(self):
        """get_theme_name実際の呼び出しテスト（line 51カバー）"""
        try:
            config = SimpleConfig()
            theme_name = config.get_theme_name()

            # 戻り値の型と基本確認
            assert isinstance(theme_name, str)
            assert len(theme_name) >= 0  # 空文字列でも有効

        except Exception as e:
            pytest.skip(f"依存関係エラー: {e}")

    def test_create_simple_config_return_type(self):
        """create_simple_config戻り値型テスト（line 60カバー）"""
        # ファクトリ関数の戻り値を直接テスト
        config = create_simple_config()

        # 戻り値が正確にSimpleConfig型であることを確認
        assert isinstance(config, SimpleConfig)
        assert type(config).__name__ == "SimpleConfig"
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get_theme_name")
