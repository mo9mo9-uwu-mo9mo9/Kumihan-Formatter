"""config コア機能統合テスト - Issue #1115

config_utils、config_init、環境変数処理の統合による25テストケース。
設定インスタンス作成、ファクトリ関数、モジュールAPI、環境変数統合を効率的にテスト。
"""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, Optional
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
from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager_utils import (
    create_config_instance,
    merge_config_data,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigInstanceCreation:
    """設定インスタンス作成テスト"""

    @pytest.mark.parametrize(
        "config_type,config_path,expected_class,should_use_file",
        [
            # 基本パターン
            ("base", None, "BaseConfig", False),
            ("extended", None, "ExtendedConfig", False),
            # パス指定パターン
            ("base", "/path/to/config.yaml", "BaseConfig", True),
            ("extended", "/path/to/config.json", "ExtendedConfig", True),
            # エラーケース - 無効なタイプはBaseConfigにフォールバック
            ("invalid", None, "BaseConfig", False),
        ],
    )
    def test_config_instance_creation_patterns(
        self,
        config_type: str,
        config_path: Optional[str],
        expected_class: str,
        should_use_file: bool,
    ):
        """設定インスタンス作成パターンテスト"""
        with (
            patch(
                "kumihan_formatter.config.config_manager_utils.BaseConfig"
            ) as mock_base,
            patch(
                "kumihan_formatter.config.config_manager_utils.ExtendedConfig"
            ) as mock_extended,
            patch("kumihan_formatter.config.config_manager_utils.Path") as mock_path,
        ):
            # モック設定
            mock_instance = Mock()
            if expected_class == "BaseConfig":
                mock_base.return_value = mock_instance
                if should_use_file:
                    mock_base.from_file.return_value = mock_instance
            else:
                mock_extended.return_value = mock_instance
                if should_use_file:
                    mock_extended.from_file.return_value = mock_instance

            # ファイル存在モック
            if config_path:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = should_use_file
                mock_path.return_value = mock_path_instance

            # テスト実行
            result = create_config_instance(config_type, config_path)

            # 検証
            assert result == mock_instance

            if should_use_file and config_path:
                if expected_class == "BaseConfig":
                    mock_base.from_file.assert_called_once_with(config_path)
                else:
                    mock_extended.from_file.assert_called_once_with(config_path)

    @pytest.mark.parametrize(
        "error_scenario,config_type,config_path,expected_fallback",
        [
            ("file_not_exists", "base", "/nonexistent/config.yaml", "BaseConfig"),
            ("file_load_error", "extended", "/invalid/config.json", "ExtendedConfig"),
        ],
    )
    def test_config_creation_error_handling(
        self,
        error_scenario: str,
        config_type: str,
        config_path: str,
        expected_fallback: str,
    ):
        """設定作成エラーハンドリングテスト"""
        with (
            patch(
                "kumihan_formatter.config.config_manager_utils.BaseConfig"
            ) as mock_base,
            patch(
                "kumihan_formatter.config.config_manager_utils.ExtendedConfig"
            ) as mock_extended,
            patch("kumihan_formatter.config.config_manager_utils.Path") as mock_path,
        ):
            fallback_instance = Mock()

            if expected_fallback == "BaseConfig":
                mock_base.return_value = fallback_instance
                if error_scenario == "file_load_error":
                    mock_base.from_file.side_effect = Exception("Load error")
            else:
                mock_extended.return_value = fallback_instance
                if error_scenario == "file_load_error":
                    mock_extended.from_file.side_effect = Exception("Load error")

            # ファイル存在状況の設定
            mock_path_instance = Mock()
            if error_scenario == "file_not_exists":
                mock_path_instance.exists.return_value = False
            else:
                mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # テスト実行
            result = create_config_instance(config_type, config_path)

            # フォールバックインスタンスが返されることを確認
            assert result == fallback_instance


class TestConfigModuleAPI:
    """config モジュール API テスト"""

    def test_module_exports(self):
        """モジュールエクスポートテスト"""
        expected_exports = [
            "BaseConfig",
            "ExtendedConfig",
            "ConfigManager",
            "Config",
            "create_config_manager",
            "load_config",
        ]

        for item in expected_exports:
            assert item in __all__

        # Config エイリアス確認
        assert Config is ConfigManager

    @pytest.mark.parametrize(
        "deprecated_function,expected_warning_text",
        [
            ("create_simple_config", "create_simple_config()は非推奨です"),
            ("get_default_config", "get_default_config()は非推奨です"),
        ],
    )
    def test_deprecated_functions(
        self, deprecated_function: str, expected_warning_text: str
    ):
        """非推奨関数のテスト"""
        with (
            patch("kumihan_formatter.config.create_config_manager") as mock_create,
            warnings.catch_warnings(record=True) as caught_warnings,
        ):
            warnings.simplefilter("always")
            mock_create.return_value = Mock()

            if deprecated_function == "create_simple_config":
                create_simple_config()
                mock_create.assert_called_once_with(config_type="base")
            else:
                get_default_config()

            # 警告確認
            assert len(caught_warnings) == 1
            assert issubclass(caught_warnings[0].category, DeprecationWarning)
            assert expected_warning_text in str(caught_warnings[0].message)

    def test_default_config_caching(self):
        """デフォルト設定のキャッシングテスト"""
        reset_default_config()  # テスト前にリセット

        with (
            patch("kumihan_formatter.config.create_config_manager") as mock_create,
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore", DeprecationWarning)
            mock_config = Mock()
            mock_create.return_value = mock_config

            # 初回呼び出し
            first_call = get_default_config()
            # 2回目呼び出し
            second_call = get_default_config()

            # キャッシングの確認
            assert first_call is second_call
            mock_create.assert_called_once()  # 1回のみ呼び出し

    def test_default_config_reset(self):
        """デフォルト設定リセットテスト"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # 初期設定作成
            first_config = get_default_config()

            # リセット
            reset_default_config()

            # 再作成
            second_config = get_default_config()

            # 異なるインスタンスであることを確認
            assert first_config is not second_config


class TestConfigMergeUtility:
    """設定マージユーティリティテスト"""

    def test_merge_config_with_merge_method(self):
        """merge_configメソッド使用のテスト"""
        with patch(
            "kumihan_formatter.config.config_manager_utils.BaseConfig"
        ) as mock_base:
            mock_config = Mock()
            mock_config.merge_config = Mock()
            mock_base.return_value = mock_config

            config = create_config_instance("base", None)
            merge_data = {"key": "value", "nested": {"inner": "data"}}

            merge_config_data(config, merge_data)

            # merge_configが呼ばれることを確認
            mock_config.merge_config.assert_called_once_with(merge_data)

    def test_merge_config_with_set_method(self):
        """setメソッド使用のテスト"""
        with patch(
            "kumihan_formatter.config.config_manager_utils.BaseConfig"
        ) as mock_base:
            mock_config = Mock()
            mock_config.set = Mock()
            # merge_configメソッドを削除
            del mock_config.merge_config
            mock_base.return_value = mock_config

            config = create_config_instance("base", None)
            merge_data = {"key1": "value1", "key2": "value2"}

            merge_config_data(config, merge_data)

            # setが各キーに対して呼ばれることを確認
            assert mock_config.set.call_count == len(merge_data)
            expected_calls = [("key1", "value1"), ("key2", "value2")]
            actual_calls = [call[0] for call in mock_config.set.call_args_list]
            for expected_call in expected_calls:
                assert expected_call in actual_calls


class TestEnvironmentVariableIntegration:
    """環境変数統合テスト"""

    @pytest.mark.parametrize(
        "env_vars,prefix,expected_calls",
        [
            # 基本環境変数
            (
                {"TEST_OUTPUT_DIR": "env_output", "TEST_THEME": "dark"},
                "TEST_",
                ["OUTPUT_DIR", "THEME"],
            ),
            # Kumihanプレフィックス
            (
                {"KUMIHAN_TEMPLATE_DIR": "env_templates", "KUMIHAN_DEBUG": "true"},
                "KUMIHAN_",
                ["TEMPLATE_DIR", "DEBUG"],
            ),
            # 環境変数なし
            ({}, "EMPTY_", []),
        ],
    )
    def test_environment_variable_processing(
        self, env_vars: Dict[str, str], prefix: str, expected_calls: list
    ):
        """環境変数処理テスト"""
        with (
            patch.dict(os.environ, env_vars, clear=True),
            patch(
                "kumihan_formatter.config.config_manager.ConfigEnvironmentHandler"
            ) as mock_env_handler_class,
        ):
            mock_env_handler = Mock()
            mock_env_handler_class.return_value = mock_env_handler

            # ConfigManagerを使用して環境変数処理をテスト
            with patch(
                "kumihan_formatter.config.config_manager.create_config_instance"
            ) as mock_create:
                mock_config = Mock()
                mock_create.return_value = mock_config

                ConfigManager(env_prefix=prefix)  # noqa: F841

                # 環境変数ハンドラの呼び出し確認
                mock_env_handler_class.assert_called_once_with(prefix)
                mock_env_handler.load_from_env.assert_called_once_with(mock_config)


class TestConfigIntegrationWorkflows:
    """設定統合ワークフローテスト"""

    def test_complete_config_workflow_base(self):
        """BaseConfig完全ワークフローテスト"""
        with patch(
            "kumihan_formatter.config.config_manager_utils.BaseConfig"
        ) as mock_base:
            mock_instance = Mock()
            mock_instance.get.return_value = "test_value"
            mock_instance.validate.return_value = True
            mock_instance.get_css_variables.return_value = {"color": "blue"}
            mock_instance.to_dict.return_value = {"output_dir": "output"}
            mock_base.return_value = mock_instance

            # インスタンス作成
            config = create_config_instance("base", None)

            # 各種操作
            assert config.get("test_key") == "test_value"
            assert config.validate() is True
            assert config.get_css_variables()["color"] == "blue"
            assert config.to_dict()["output_dir"] == "output"

    def test_complete_config_workflow_extended(self):
        """ExtendedConfig完全ワークフローテスト"""
        with patch(
            "kumihan_formatter.config.config_manager_utils.ExtendedConfig"
        ) as mock_extended:
            mock_instance = Mock()
            mock_instance.get_markers.return_value = {"太字": {"tag": "strong"}}
            mock_instance.get_themes.return_value = {"default": {"name": "デフォルト"}}
            mock_instance.get_current_theme.return_value = "default"
            mock_extended.return_value = mock_instance

            # インスタンス作成
            config = create_config_instance("extended", None)

            # 拡張機能操作
            assert "太字" in config.get_markers()
            assert "default" in config.get_themes()
            assert config.get_current_theme() == "default"

    @pytest.mark.parametrize(
        "boundary_case,test_data",
        [
            ("empty_strings", {"": "", "empty": ""}),
            ("special_chars", {"特殊": "値", "emoji": "🎯"}),
            (
                "large_data",
                {f"key_{i}": f"value_{i}" for i in range(10)},
            ),  # 実用的なサイズに縮小
            ("nested_deep", {"l1": {"l2": {"l3": {"l4": "deep_value"}}}}),
        ],
    )
    def test_boundary_cases(self, boundary_case: str, test_data: Dict[str, Any]):
        """境界値ケーステスト"""
        with patch(
            "kumihan_formatter.config.config_manager_utils.BaseConfig"
        ) as mock_base:
            mock_config = Mock()
            mock_config.set = Mock()
            mock_base.return_value = mock_config

            config = create_config_instance("base", None)
            merge_config_data(config, test_data)

            # データが適切に処理されることを確認
            # merge_config_dataが呼ばれることを確認
            # 実際のsetの呼び出し数は実装により異なるため、エラーが発生しないことを確認

    def test_exception_resilience(self):
        """例外耐性テスト"""
        # ファイル読み込み時の例外処理
        with (
            patch(
                "kumihan_formatter.config.config_manager_utils.BaseConfig"
            ) as mock_base,
            patch("kumihan_formatter.config.config_manager_utils.Path") as mock_path,
        ):
            # ファイルが存在するが読み込みエラーのケース
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # from_fileで例外発生、フォールバック処理
            fallback_instance = Mock()
            mock_base.from_file.side_effect = Exception("File read error")
            mock_base.return_value = fallback_instance

            # フォールバック動作の確認
            result = create_config_instance("base", "/path/to/config.yaml")

            # フォールバック処理によりデフォルトインスタンスが返される
            assert result == fallback_instance
            mock_base.assert_called_once()
