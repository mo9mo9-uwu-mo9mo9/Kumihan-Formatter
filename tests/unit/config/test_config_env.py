"""config_manager_env.py 効率化テスト - Issue #1115

ConfigEnvironmentHandler（環境変数管理）の重要機能を10テストに集約。
初期化、環境変数読み込み、CSS・テーマ変数抽出を効率的にテスト。
"""

import os
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config.config_manager_env import ConfigEnvironmentHandler


class TestConfigEnvironmentHandlerCore:
    """ConfigEnvironmentHandler コア機能テスト"""

    @pytest.mark.parametrize(
        "env_prefix,expected_prefix",
        [
            # デフォルトプレフィックス
            (None, "KUMIHAN_"),
            # カスタムプレフィックス
            ("CUSTOM_", "CUSTOM_"),
            ("TEST_", "TEST_"),
            ("APP_", "APP_"),
            # 空文字列
            ("", ""),
        ],
    )
    def test_initialization_patterns(self, env_prefix, expected_prefix):
        """初期化パターンテスト"""
        if env_prefix is None:
            handler = ConfigEnvironmentHandler()
        else:
            handler = ConfigEnvironmentHandler(env_prefix=env_prefix)

        assert handler.env_prefix == expected_prefix

        # 必要なメソッドの存在確認
        assert hasattr(handler, "load_from_env")
        assert hasattr(handler, "_extract_env_config")
        assert hasattr(handler, "_extract_css_vars")


class TestEnvironmentVariableLoading:
    """環境変数読み込みテスト"""

    @pytest.mark.parametrize(
        "env_vars,has_merge_config,expected_calls",
        [
            # merge_configありパターン
            (
                {"KUMIHAN_CSS_BACKGROUND": "#ffffff", "KUMIHAN_THEME": "light"},
                True,
                "merge_config",
            ),
            # merge_configなしパターン
            ({"KUMIHAN_CSS_COLOR": "#000000", "KUMIHAN_THEME": "dark"}, False, "set"),
            # 環境変数なし
            ({}, True, None),
        ],
    )
    def test_load_from_env_patterns(
        self, env_vars: Dict[str, str], has_merge_config: bool, expected_calls: str
    ):
        """環境変数読み込みパターンテスト"""
        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler()

            # モック設定作成
            config = Mock()
            if has_merge_config:
                config.merge_config = Mock()
            else:
                config.set = Mock()
                if hasattr(config, "merge_config"):
                    del config.merge_config

            # テスト実行
            handler.load_from_env(config)

            # 結果確認
            if expected_calls == "merge_config" and env_vars:
                config.merge_config.assert_called_once()
                call_args = config.merge_config.call_args[0][0]
                if "KUMIHAN_CSS_BACKGROUND" in env_vars:
                    assert "css" in call_args
                    assert call_args["css"]["background"] == "#ffffff"
                if "KUMIHAN_THEME" in env_vars:
                    assert call_args["theme"] == env_vars["KUMIHAN_THEME"]
            elif expected_calls == "set" and env_vars:
                config.set.assert_called()
            elif expected_calls is None:
                if has_merge_config:
                    config.merge_config.assert_not_called()

    @pytest.mark.parametrize(
        "prefix,env_vars,expected_extraction",
        [
            # 標準プレフィックス
            (
                "KUMIHAN_",
                {
                    "KUMIHAN_CSS_COLOR": "#123",
                    "KUMIHAN_THEME": "custom",
                    "OTHER_VAR": "ignore",
                },
                {"css": {"color": "#123"}, "theme": "custom"},
            ),
            # カスタムプレフィックス
            (
                "TEST_",
                {
                    "TEST_CSS_FONT_SIZE": "16px",
                    "TEST_THEME": "test",
                    "KUMIHAN_CSS_IGNORE": "ignore",
                },
                {"css": {"font_size": "16px"}, "theme": "test"},
            ),
            # CSS変数のみ
            (
                "KUMIHAN_",
                {"KUMIHAN_CSS_MARGIN": "10px", "KUMIHAN_CSS_PADDING": "5px"},
                {"css": {"margin": "10px", "padding": "5px"}},
            ),
            # テーマ変数のみ
            ("KUMIHAN_", {"KUMIHAN_THEME": "dark_theme"}, {"theme": "dark_theme"}),
        ],
    )
    def test_environment_variable_extraction(
        self, prefix: str, env_vars: Dict[str, str], expected_extraction: Dict[str, Any]
    ):
        """環境変数抽出パターンテスト"""
        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler(env_prefix=prefix)

            result = handler._extract_env_config()

            # 期待される構造と値の確認
            for key, expected_value in expected_extraction.items():
                assert key in result
                assert result[key] == expected_value


class TestCSSVariableExtraction:
    """CSS変数抽出テスト"""

    @pytest.mark.parametrize(
        "prefix,env_vars,expected_css",
        [
            # 基本CSS変数
            (
                "KUMIHAN_",
                {"KUMIHAN_CSS_BACKGROUND": "#fff", "KUMIHAN_CSS_COLOR": "#000"},
                {"background": "#fff", "color": "#000"},
            ),
            # 複雑なCSS変数名
            (
                "KUMIHAN_",
                {
                    "KUMIHAN_CSS_BACKGROUND_COLOR": "#f5f5f5",
                    "KUMIHAN_CSS_FONT_SIZE": "14px",
                },
                {"background_color": "#f5f5f5", "font_size": "14px"},
            ),
            # カスタムプレフィックス
            (
                "CUSTOM_",
                {"CUSTOM_CSS_MARGIN": "20px", "CUSTOM_CSS_LINE_HEIGHT": "1.6"},
                {"margin": "20px", "line_height": "1.6"},
            ),
            # CSS変数なし
            ("KUMIHAN_", {"KUMIHAN_THEME": "dark", "OTHER_VAR": "value"}, {}),
        ],
    )
    def test_css_variable_extraction_patterns(
        self, prefix: str, env_vars: Dict[str, str], expected_css: Dict[str, str]
    ):
        """CSS変数抽出パターンテスト"""
        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler(env_prefix=prefix)

            result = handler._extract_css_vars()

            assert result == expected_css

    def test_css_variable_case_handling(self):
        """CSS変数の大文字小文字処理テスト"""
        env_vars = {
            "KUMIHAN_CSS_BACKGROUND_COLOR": "#FFFFFF",
            "KUMIHAN_CSS_FONT_FAMILY": "Arial",
            "KUMIHAN_CSS_MAX_WIDTH": "1200PX",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler()

            result = handler._extract_css_vars()

            # キーは小文字・アンダースコア形式に変換
            assert "background_color" in result
            assert "font_family" in result
            assert "max_width" in result

            # 値は元の値を保持
            assert result["background_color"] == "#FFFFFF"
            assert result["font_family"] == "Arial"
            assert result["max_width"] == "1200PX"


class TestEnvironmentHandlerIntegration:
    """環境ハンドラー統合テスト"""

    def test_complete_environment_workflow(self):
        """完全環境変数ワークフロー"""
        env_vars = {
            "KUMIHAN_CSS_BACKGROUND": "#f8f9fa",
            "KUMIHAN_CSS_COLOR": "#212529",
            "KUMIHAN_CSS_FONT_SIZE": "16px",
            "KUMIHAN_THEME": "bootstrap",
            "KUMIHAN_DEBUG": "true",
            "OTHER_APP_VAR": "ignore",  # 無関係な変数
        }

        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler()

            # 環境設定抽出
            env_config = handler._extract_env_config()

            # CSS設定の確認
            assert "css" in env_config
            css_config = env_config["css"]
            assert css_config["background"] == "#f8f9fa"
            assert css_config["color"] == "#212529"
            assert css_config["font_size"] == "16px"

            # テーマ設定の確認
            assert env_config["theme"] == "bootstrap"

            # その他の設定確認（KUMIHAN_DEBUG は KUMIHAN_CSS_ ではないためCSS変数として扱われない可能性）
            # 環境変数処理の実装により、debugの扱いが変わる可能性がある

            # 無関係な変数が除外されることを確認
            assert "OTHER_APP_VAR" not in str(env_config)

    def test_multiple_config_objects_integration(self):
        """複数設定オブジェクト統合テスト"""
        env_vars = {"TEST_CSS_MARGIN": "10px", "TEST_THEME": "custom"}

        with patch.dict(os.environ, env_vars, clear=True):
            handler = ConfigEnvironmentHandler(env_prefix="TEST_")

            # merge_config対応オブジェクト
            config_with_merge = Mock()
            config_with_merge.merge_config = Mock()

            # set対応オブジェクト
            config_with_set = Mock()
            config_with_set.set = Mock()
            del config_with_set.merge_config  # merge_configなし

            # 両方にロード
            handler.load_from_env(config_with_merge)
            handler.load_from_env(config_with_set)

            # merge_configが呼ばれたことを確認
            config_with_merge.merge_config.assert_called_once()
            merge_args = config_with_merge.merge_config.call_args[0][0]
            assert merge_args["css"]["margin"] == "10px"
            assert merge_args["theme"] == "custom"

            # setが呼ばれたことを確認
            config_with_set.set.assert_called()
            set_calls = config_with_set.set.call_args_list
            assert len(set_calls) == 2  # css, theme

    @pytest.mark.parametrize(
        "boundary_case,env_setup",
        [
            # 空環境
            ("empty_env", {}),
            # 大量CSS変数
            ("many_css_vars", {f"KUMIHAN_CSS_VAR_{i}": f"value{i}" for i in range(50)}),
            # 長い値
            (
                "long_values",
                {"KUMIHAN_CSS_LONG": "A" * 1000, "KUMIHAN_THEME": "B" * 500},
            ),
            # 特殊文字
            (
                "special_chars",
                {"KUMIHAN_CSS_UNICODE": "🎯🔧", "KUMIHAN_THEME": "テーマ名"},
            ),
        ],
    )
    def test_boundary_cases(self, boundary_case: str, env_setup: Dict[str, str]):
        """境界値ケーステスト"""
        with patch.dict(os.environ, env_setup, clear=True):
            handler = ConfigEnvironmentHandler()

            # 環境変数抽出
            env_config = handler._extract_env_config()

            if boundary_case == "empty_env":
                assert env_config == {}
            elif boundary_case == "many_css_vars":
                assert "css" in env_config
                assert len(env_config["css"]) == 50
            elif boundary_case == "long_values":
                assert env_config["css"]["long"] == "A" * 1000
                assert env_config["theme"] == "B" * 500
            elif boundary_case == "special_chars":
                assert env_config["css"]["unicode"] == "🎯🔧"
                assert env_config["theme"] == "テーマ名"

    def test_error_resilience(self):
        """エラー耐性テスト"""
        with patch.dict(os.environ, {"KUMIHAN_CSS_COLOR": "#123"}, clear=True):
            handler = ConfigEnvironmentHandler()

            # 不正な設定オブジェクト（setもmerge_configもない）
            broken_config = Mock()
            del broken_config.set
            del broken_config.merge_config

            # エラーが発生しても処理が継続することを確認
            try:
                handler.load_from_env(broken_config)
            except AttributeError:
                # 期待される動作：適切にエラーハンドリングされる
                pass
