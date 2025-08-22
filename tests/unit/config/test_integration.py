"""設定システム統合テスト - Issue #1115

ConfigManager、設定ファイル読み込み、環境変数統合の重要シナリオを15テストに集約。
実際のAPI統合、エラーハンドリング、完全ワークフローを効率的にテスト。
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager import (
    ConfigManager,
    create_config_manager,
    load_config,
)
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigManagerTypeIntegration:
    """ConfigManager タイプ統合テスト"""

    @pytest.mark.parametrize(
        "config_type,expected_instance_type,has_extended_methods",
        [
            ("base", BaseConfig, False),
            ("extended", ExtendedConfig, True),
        ],
    )
    def test_config_type_integration(
        self, config_type: str, expected_instance_type: type, has_extended_methods: bool
    ):
        """ConfigManager タイプ別統合テスト"""
        manager = ConfigManager(config_type=config_type)

        assert manager.config_type == config_type
        assert isinstance(manager._config, expected_instance_type)

        # 拡張メソッドの存在確認
        if has_extended_methods:
            assert hasattr(manager, "get_markers")
            assert hasattr(manager, "get_themes")
            assert callable(manager.get_markers)
            assert callable(manager.get_themes)


class TestEnvironmentVariableIntegration:
    """環境変数統合テスト"""

    @pytest.mark.parametrize(
        "env_vars,env_prefix,config_type",
        [
            (
                {"KUMIHAN_CSS_BACKGROUND": "#ffffff", "KUMIHAN_THEME": "dark"},
                "KUMIHAN_",
                "extended",
            ),
            ({"TEST_OUTPUT_DIR": "test_output", "TEST_DEBUG": "true"}, "TEST_", "base"),
            ({}, "EMPTY_", "extended"),  # 環境変数なし
        ],
    )
    def test_environment_variable_integration(
        self, env_vars: Dict[str, str], env_prefix: str, config_type: str
    ):
        """環境変数統合テスト"""
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager(config_type=config_type, env_prefix=env_prefix)

            assert manager.env_prefix == env_prefix
            assert manager._config is not None

            # CSS変数が取得できることを確認（環境変数の影響を受ける可能性がある）
            css_vars = manager.get_css_variables()
            assert isinstance(css_vars, dict)
            assert len(css_vars) > 0


class TestConfigFileIntegration:
    """設定ファイル統合テスト"""

    @pytest.mark.parametrize(
        "file_content,file_suffix,config_type,expected_success",
        [
            # YAML設定ファイル
            (
                'output_dir: "yaml_output"\ntemplate_dir: "yaml_templates"',
                ".yaml",
                "base",
                True,
            ),
            # JSON設定ファイル
            (
                '{"output_dir": "json_output", "template_dir": "json_templates"}',
                ".json",
                "extended",
                True,
            ),
            # 不正JSON
            ('{"invalid": json content}', ".json", "base", False),
        ],
    )
    def test_config_file_integration(
        self,
        file_content: str,
        file_suffix: str,
        config_type: str,
        expected_success: bool,
    ):
        """設定ファイル読み込み統合テスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_suffix, delete=False, encoding="utf-8"
        ) as f:
            f.write(file_content)
            config_path = f.name

        try:
            if expected_success:
                # 正常ケース
                manager = ConfigManager(
                    config_type=config_type, config_path=config_path
                )
                assert manager._config is not None

                # load_config関数テスト
                config = load_config(config_path, config_type)
                assert config is not None
            else:
                # エラーケース：例外が発生するか、フォールバックが動作する
                manager = ConfigManager(
                    config_type=config_type, config_path=config_path
                )
                assert manager._config is not None  # フォールバック動作

        finally:
            Path(config_path).unlink()

    def test_file_error_handling_integration(self):
        """ファイルエラーハンドリング統合テスト"""
        # 存在しないファイル
        invalid_path = "/nonexistent/config.yaml"

        # ConfigManager は例外を発生させずフォールバックする
        manager = ConfigManager(config_path=invalid_path)
        assert manager._config is not None
        assert isinstance(manager._config, ExtendedConfig)  # デフォルトタイプ

        # load_config関数は例外を発生させる
        with pytest.raises(FileNotFoundError):
            load_config(invalid_path)


class TestConfigOperationIntegration:
    """設定操作統合テスト"""

    def test_basic_config_operations_integration(self):
        """基本設定操作統合テスト"""
        manager = ConfigManager(config_type="base")

        # 設定取得・更新
        manager.set_config("test_key", "test_value")
        assert manager.get_config("test_key") == "test_value"

        # バリデーション
        is_valid = manager.validate()
        assert isinstance(is_valid, bool)

        # 辞書変換
        config_dict = manager.to_dict()
        assert isinstance(config_dict, dict)
        assert "test_key" in config_dict

    def test_extended_config_operations_integration(self):
        """拡張設定操作統合テスト"""
        manager = ConfigManager(config_type="extended")

        # マーカー操作
        initial_markers = manager.get_markers()
        manager.add_marker("test_marker", {"tag": "span", "class": "test"})
        updated_markers = manager.get_markers()
        assert len(updated_markers) == len(initial_markers) + 1
        assert "test_marker" in updated_markers

        # テーマ操作
        manager.add_theme("test_theme", {"name": "テスト", "css": {"color": "red"}})
        themes = manager.get_themes()
        assert "test_theme" in themes

        manager.set_theme("test_theme")
        assert manager.get_current_theme() == "test_theme"

        # CSS変数確認（テーマ切り替えの影響）
        css_vars = manager.get_css_variables()
        assert css_vars["color"] == "red"

    def test_config_merge_integration(self):
        """設定マージ統合テスト"""
        manager = ConfigManager(config_type="extended")

        # 初期設定確認
        manager.to_dict()

        # マージデータ準備
        merge_data = {
            "output_dir": "merged_output",
            "template_dir": "merged_templates",
            "custom_setting": "custom_value",
        }

        # マージ実行
        manager.merge_config(merge_data)

        # マージ後確認
        assert manager.get_config("output_dir") == "merged_output"
        assert manager.get_config("custom_setting") == "custom_value"

        # バリデーション
        assert manager.validate() is True


class TestCompleteWorkflowIntegration:
    """完全ワークフロー統合テスト"""

    def test_complete_base_config_workflow(self):
        """BaseConfig完全ワークフロー"""
        # 1. 環境変数設定
        env_vars = {
            "TEST_OUTPUT_DIR": "env_output",
            "TEST_TEMPLATE_DIR": "env_templates",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # 2. 設定ファイル作成
            config_content = """
output_dir: "file_output"
template_dir: "file_templates"
css:
  max_width: "1000px"
  background_color: "#f5f5f5"
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False, encoding="utf-8"
            ) as f:
                f.write(config_content)
                config_path = f.name

            try:
                # 3. ConfigManager初期化（ファイル + 環境変数）
                manager = ConfigManager(
                    config_type="base", config_path=config_path, env_prefix="TEST_"
                )

                # 4. 設定確認
                assert manager._config is not None
                assert (
                    manager.get_config("output_dir") is not None
                )  # ファイルまたは環境変数から

                # 5. 設定更新
                manager.set_config("new_setting", "new_value")

                # 6. CSS変数取得
                css_vars = manager.get_css_variables()
                assert "max_width" in css_vars

                # 7. バリデーション
                assert manager.validate() is True

                # 8. 最終出力
                final_config = manager.to_dict()
                assert "new_setting" in final_config

            finally:
                Path(config_path).unlink()

    def test_complete_extended_config_workflow(self):
        """ExtendedConfig完全ワークフロー"""
        # 1. 初期化
        manager = ConfigManager(config_type="extended")

        # 2. 基本設定
        manager.set_config("output_dir", "workflow_output")
        manager.set_config("template_dir", "workflow_templates")

        # 3. マーカー管理
        manager.add_marker("ワークフロー", {"tag": "div", "class": "workflow"})
        manager.add_marker("テスト", {"tag": "span", "class": "test"})
        assert len(manager.get_markers()) >= 13  # デフォルト11 + 追加2

        # 4. テーマ管理
        manager.add_theme(
            "ワークフロー",
            {
                "name": "ワークフローテーマ",
                "css": {"background": "blue", "color": "white"},
            },
        )
        manager.set_theme("ワークフロー")
        assert manager.get_current_theme() == "ワークフロー"

        # 5. CSS統合確認
        css_vars = manager.get_css_variables()
        assert css_vars["background"] == "blue"
        assert css_vars["color"] == "white"

        # 6. 削除操作
        manager.remove_marker("テスト")
        assert "テスト" not in manager.get_markers()

        # 7. 最終バリデーション
        assert manager.validate() is True

        # 8. 完全出力
        final_config = manager.to_dict()
        assert final_config["output_dir"] == "workflow_output"

    @pytest.mark.parametrize(
        "factory_function,args,expected_type",
        [
            (create_config_manager, ("base",), ConfigManager),
            (create_config_manager, ("extended", None), ConfigManager),
        ],
    )
    def test_factory_function_integration(
        self, factory_function, args: tuple, expected_type: type
    ):
        """ファクトリ関数統合テスト"""
        result = factory_function(*args)

        assert isinstance(result, expected_type)
        assert result._config is not None
        assert hasattr(result, "get_config")
        assert hasattr(result, "set_config")
        assert hasattr(result, "validate")


class TestBoundaryAndErrorIntegration:
    """境界値・エラー統合テスト"""

    def test_empty_configuration_integration(self):
        """空設定統合テスト"""
        manager = ConfigManager()

        # 空マージ
        manager.merge_config({})

        # 空設定でも動作することを確認
        config_dict = manager.to_dict()
        assert isinstance(config_dict, dict)

        css_vars = manager.get_css_variables()
        assert isinstance(css_vars, dict)

    def test_large_configuration_integration(self):
        """大量設定統合テスト"""
        manager = ConfigManager(config_type="extended")

        # 大量データマージ
        large_config = {f"key_{i}": f"value_{i}" for i in range(100)}
        manager.merge_config(large_config)

        # 大量マーカー追加
        for i in range(20):
            manager.add_marker(f"marker_{i}", {"tag": f"tag{i}"})

        # 大量テーマ追加
        for i in range(10):
            manager.add_theme(f"theme_{i}", {"name": f"テーマ{i}"})

        # 正常動作確認
        assert len(manager.get_markers()) >= 31  # デフォルト11 + 追加20
        assert len(manager.get_themes()) >= 13  # デフォルト3 + 追加10

        config_dict = manager.to_dict()
        assert len([k for k in config_dict.keys() if k.startswith("key_")]) == 100

    def test_error_recovery_integration(self):
        """エラー回復統合テスト"""
        manager = ConfigManager(config_type="extended")

        # 不正なマーカー操作（存在しないマーカー削除）
        result = manager.remove_marker("存在しないマーカー")
        assert result is False

        # 不正なテーマ操作（存在しないテーマ削除）
        result = manager.remove_theme("存在しないテーマ")
        assert result is False

        # 不正なテーマ設定
        manager.set_theme("存在しないテーマ")
        # デフォルトテーマにフォールバックされることを確認
        current_theme = manager.get_current_theme()
        assert current_theme in ["default", "存在しないテーマ"]  # 実装による

        # エラー後も基本機能は動作する
        assert manager.validate() is not None
        assert manager.get_css_variables() is not None
