"""config_manager.py 効率化テスト - Issue #1115

ConfigManager（70%カバレッジ）の重要機能をパラメータ化により20テストに集約。
初期化パターン、設定取得・更新、環境変数処理、ファクトリ関数を効率的にテスト。
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager import (
    ConfigManager,
    create_config_manager,
    load_config,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigManagerInitialization:
    """ConfigManager初期化パターンテスト"""

    @pytest.mark.parametrize(
        "config_type,config_path,env_prefix,expected_type,expected_prefix",
        [
            # デフォルト初期化
            (None, None, None, "extended", "KUMIHAN_"),
            # 各config_type
            ("base", None, None, "base", "KUMIHAN_"),
            ("extended", None, None, "extended", "KUMIHAN_"),
            ("invalid", None, None, "invalid", "KUMIHAN_"),  # 無効タイプも受け入れ
            # config_path指定
            (None, "/test/config.json", None, "extended", "KUMIHAN_"),
            # カスタムenv_prefix
            (None, None, "CUSTOM_", "extended", "CUSTOM_"),
            # 全パラメータ指定
            ("base", "/test/config.yaml", "APP_", "base", "APP_"),
        ],
    )
    def test_initialization_patterns(
        self,
        config_type: Optional[str],
        config_path: Optional[str],
        env_prefix: Optional[str],
        expected_type: str,
        expected_prefix: str,
    ):
        """初期化パターンテスト"""
        with (
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance"
            ) as mock_create,
            patch(
                "kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"
            ) as mock_env,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config
            mock_env_instance = Mock()
            mock_env.return_value = mock_env_instance

            # 初期化パラメータ準備
            kwargs = {}
            if config_type is not None:
                kwargs["config_type"] = config_type
            if config_path is not None:
                kwargs["config_path"] = config_path
            if env_prefix is not None:
                kwargs["env_prefix"] = env_prefix

            # When
            manager = ConfigManager(**kwargs)

            # Then
            assert manager.config_type == expected_type
            assert manager.env_prefix == expected_prefix

            mock_create.assert_called_once_with(expected_type, config_path)
            mock_env.assert_called_once_with(expected_prefix)
            mock_env_instance.load_from_env.assert_called_once_with(mock_config)


class TestConfigManagerOperations:
    """ConfigManager操作テスト"""

    def test_get_config_delegation(self):
        """設定取得の委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            mock_config.get.return_value = "test_value"
            mock_create.return_value = mock_config

            manager = ConfigManager()
            result = manager.get_config("test_key", "default")

            mock_config.get.assert_called_once_with("test_key", "default")
            assert result == "test_value"

    def test_set_config_delegation(self):
        """設定更新の委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            mock_create.return_value = mock_config

            manager = ConfigManager()
            manager.set_config("test_key", "test_value")

            mock_config.set.assert_called_once_with("test_key", "test_value")

    def test_validate_delegation(self):
        """バリデーションの委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            mock_config.validate.return_value = True
            mock_create.return_value = mock_config

            manager = ConfigManager()
            result = manager.validate()

            mock_config.validate.assert_called_once()
            assert result is True

    def test_get_css_variables_delegation(self):
        """CSS変数取得の委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            expected_css = {"color": "red", "font-size": "14px"}
            mock_config.get_css_variables.return_value = expected_css
            mock_create.return_value = mock_config

            manager = ConfigManager()
            result = manager.get_css_variables()

            mock_config.get_css_variables.assert_called_once()
            assert result == expected_css

    def test_to_dict_delegation(self):
        """辞書変換の委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            expected_dict = {"key": "value", "nested": {"inner": "data"}}
            mock_config.to_dict.return_value = expected_dict
            mock_create.return_value = mock_config

            manager = ConfigManager()
            result = manager.to_dict()

            mock_config.to_dict.assert_called_once()
            assert result == expected_dict


class TestConfigManagerExtendedFeatures:
    """ConfigManager拡張機能テスト（ExtendedConfig使用時）"""

    @pytest.mark.parametrize(
        "method_name,args,expected_result",
        [
            ("get_markers", (), {"太字": {"tag": "strong"}}),
            ("get_themes", (), {"default": {"name": "デフォルト"}}),
            ("get_current_theme", (), "default"),
            ("get_theme_name", (), "デフォルト"),
        ],
    )
    def test_extended_methods_delegation(
        self, method_name: str, args: tuple, expected_result: Any
    ):
        """拡張メソッドの委譲テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            getattr(mock_config, method_name).return_value = expected_result
            mock_create.return_value = mock_config

            manager = ConfigManager(config_type="extended")
            result = getattr(manager, method_name)(*args)

            getattr(mock_config, method_name).assert_called_once_with(*args)
            assert result == expected_result

    def test_extended_modification_methods(self):
        """拡張修正メソッドのテスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            mock_config.add_marker.return_value = None
            mock_config.add_theme.return_value = None
            mock_config.set_theme.return_value = None
            mock_create.return_value = mock_config

            manager = ConfigManager(config_type="extended")

            # マーカー追加
            manager.add_marker("test_marker", {"tag": "span"})
            mock_config.add_marker.assert_called_once_with(
                "test_marker", {"tag": "span"}
            )

            # テーマ追加
            manager.add_theme("test_theme", {"name": "テスト"})
            mock_config.add_theme.assert_called_once_with(
                "test_theme", {"name": "テスト"}
            )

            # テーマ設定
            manager.set_theme("dark")
            mock_config.set_theme.assert_called_once_with("dark")


class TestConfigFactoryFunctions:
    """設定ファクトリ関数テスト"""

    @pytest.mark.parametrize(
        "config_type,config_path,expected_class",
        [
            ("base", None, "BaseConfig"),
            ("extended", None, "ExtendedConfig"),
            # パスありパターンは実際のファイルアクセスが必要なため省略
        ],
    )
    def test_create_config_manager_patterns(
        self, config_type: str, config_path: Optional[str], expected_class: str
    ):
        """create_config_manager関数テスト"""
        with (
            patch("kumihan_formatter.config.config_manager.BaseConfig") as mock_base,
            patch(
                "kumihan_formatter.config.config_manager.ExtendedConfig"
            ) as mock_extended,
        ):
            # モックの設定
            if expected_class == "BaseConfig":
                mock_instance = Mock()
                mock_base.return_value = mock_instance
            else:
                mock_instance = Mock()
                mock_extended.return_value = mock_instance

            with patch(
                "kumihan_formatter.config.config_manager.create_config_instance",
                return_value=mock_instance,
            ):
                result = create_config_manager(config_type, config_path)

                assert isinstance(result, ConfigManager)
                assert result.config_type == config_type

    def test_load_config_function_yaml(self):
        """load_config関数YAMLテスト"""
        yaml_content = "output_dir: test_output\ntemplate_dir: test_templates"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            with (
                patch(
                    "kumihan_formatter.config.config_manager.BaseConfig"
                ) as mock_base_class,
                patch(
                    "kumihan_formatter.config.config_manager.ExtendedConfig"
                ) as mock_ext_class,
            ):
                mock_config = Mock()
                mock_base_class.from_file.return_value = mock_config
                mock_ext_class.from_file.return_value = mock_config

                # BaseConfig使用
                load_config(yaml_path, "base")
                mock_base_class.from_file.assert_called_once_with(yaml_path)

                # ExtendedConfig使用（デフォルト）
                load_config(yaml_path)
                mock_ext_class.from_file.assert_called_once_with(yaml_path)

        finally:
            Path(yaml_path).unlink()

    @pytest.mark.parametrize(
        "error_case,expected_exception",
        [
            ("nonexistent_file", FileNotFoundError),
            ("invalid_config_type", ValueError),
        ],
    )
    def test_load_config_error_handling(
        self, error_case: str, expected_exception: type
    ):
        """load_config エラーハンドリングテスト"""
        if error_case == "nonexistent_file":
            with pytest.raises(expected_exception):
                load_config("/nonexistent/file.yaml")
        elif error_case == "invalid_config_type":
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write("test: data")
                temp_path = f.name

            try:
                with pytest.raises(expected_exception):
                    load_config(temp_path, "invalid_type")
            finally:
                Path(temp_path).unlink()


class TestConfigManagerIntegration:
    """ConfigManager統合テスト"""

    def test_complete_workflow_integration(self):
        """完全ワークフロー統合テスト"""
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            # モック設定
            mock_config = Mock()
            mock_config.get.return_value = "test_value"
            mock_config.validate.return_value = True
            mock_config.get_css_variables.return_value = {"color": "blue"}
            mock_config.to_dict.return_value = {"output_dir": "dist"}
            mock_create.return_value = mock_config

            # 初期化
            manager = ConfigManager(config_type="extended", env_prefix="TEST_")

            # 各種操作
            assert manager.get_config("key") == "test_value"
            assert manager.validate() is True
            assert manager.get_css_variables()["color"] == "blue"
            assert manager.to_dict()["output_dir"] == "dist"

            # 設定更新
            manager.set_config("new_key", "new_value")
            mock_config.set.assert_called_with("new_key", "new_value")

    def test_environment_integration(self):
        """環境変数統合テスト"""
        with (
            patch.dict(
                os.environ, {"TEST_OUTPUT_DIR": "env_output", "TEST_THEME": "dark"}
            ),
            patch(
                "kumihan_formatter.config.config_manager.create_config_instance"
            ) as mock_create,
            patch(
                "kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"
            ) as mock_env_class,
        ):
            mock_config = Mock()
            mock_create.return_value = mock_config

            mock_env_handler = Mock()
            mock_env_class.return_value = mock_env_handler

            ConfigManager(env_prefix="TEST_")

            # 環境変数ハンドラが正しく呼ばれることを確認
            mock_env_class.assert_called_once_with("TEST_")
            mock_env_handler.load_from_env.assert_called_once_with(mock_config)

    def test_boundary_cases(self):
        """境界値ケーステスト"""
        # 空文字列パラメータ
        with patch(
            "kumihan_formatter.config.config_manager.create_config_instance"
        ) as mock_create:
            mock_config = Mock()
            mock_create.return_value = mock_config

            manager = ConfigManager(config_type="", config_path="", env_prefix="")

            assert manager.config_type == ""
            assert manager.env_prefix == ""
            mock_create.assert_called_once_with("", "")
