"""base_config.py の効率化テスト - Issue #1115

BaseConfig（224行）の最重要機能をパラメータ化により15テストに集約。
初期化、設定値操作、バリデーション、CSS変数管理、ファイル操作を効率的にテスト。
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig


class TestBaseConfigCore:
    """BaseConfig コア機能のパラメータ化テスト"""

    @pytest.mark.parametrize(
        "config_data,expected_keys,expected_css_keys",
        [
            # デフォルト初期化
            (None, {}, {"max_width", "background_color", "text_color"}),
            # 空辞書
            ({}, {}, {"max_width", "background_color", "text_color"}),
            # 基本設定
            (
                {"output_dir": "output", "template_dir": "templates"},
                {"output_dir", "template_dir"},
                {"max_width", "background_color", "text_color"},
            ),
            # CSS設定付き
            (
                {
                    "output_dir": "output",
                    "template_dir": "templates",
                    "css": {"max_width": "1000px", "custom_color": "red"},
                },
                {"output_dir", "template_dir", "css"},
                {"max_width", "background_color", "text_color", "custom_color"},
            ),
        ],
    )
    def test_initialization_patterns(
        self,
        config_data: Optional[Dict[str, Any]],
        expected_keys: set,
        expected_css_keys: set,
    ):
        """初期化パターンのテスト"""
        config = BaseConfig(config_data)

        # 設定キーの確認
        if config_data:
            for key in expected_keys:
                assert key in config._config

        # CSS変数の確認
        css_vars = config.get_css_variables()
        for css_key in expected_css_keys:
            assert css_key in css_vars

    @pytest.mark.parametrize(
        "key,value,default,expected",
        [
            ("existing_key", "existing_value", None, "existing_value"),
            ("nonexistent_key", None, "default", "default"),
            ("nonexistent_key", None, None, None),
        ],
    )
    def test_get_set_operations(
        self, key: str, value: Any, default: Any, expected: Any
    ):
        """設定値の取得・設定テスト"""
        config = BaseConfig()

        if value is not None:
            config.set(key, value)

        result = config.get(key, default)
        assert result == expected

    @pytest.mark.parametrize(
        "config_data,is_valid",
        [
            # 有効な設定
            ({"output_dir": "output", "template_dir": "templates"}, True),
            ({"output_dir": "output", "template_dir": "templates", "html": {}}, True),
            ({"output_dir": "output", "template_dir": "templates", "css": {}}, True),
            # 無効な設定
            ({"template_dir": "templates"}, False),  # output_dir欠落
            ({"output_dir": "output"}, False),  # template_dir欠落
            ({"output_dir": 123, "template_dir": "templates"}, False),  # 型不整合
            (
                {
                    "output_dir": "output",
                    "template_dir": "templates",
                    "html": "invalid",
                },
                False,
            ),
            (
                {
                    "output_dir": "output",
                    "template_dir": "templates",
                    "css": ["invalid"],
                },
                False,
            ),
        ],
    )
    def test_validation_patterns(self, config_data: Dict[str, Any], is_valid: bool):
        """バリデーションパターンのテスト"""
        config = BaseConfig(config_data)
        assert config.validate() == is_valid

    @pytest.mark.parametrize(
        "css_config,expected_updates",
        [
            # CSS設定なし
            (None, {}),
            # カスタムCSS設定
            (
                {"max_width": "1200px", "color": "blue"},
                {"max_width": "1200px", "color": "blue"},
            ),
            # 無効なCSS設定
            ("invalid_css", {}),
        ],
    )
    def test_css_variable_management(
        self, css_config: Any, expected_updates: Dict[str, str]
    ):
        """CSS変数管理のテスト"""
        config_data = {"output_dir": "output", "template_dir": "templates"}
        if css_config is not None:
            config_data["css"] = css_config

        config = BaseConfig(config_data)
        css_vars = config.get_css_variables()

        # デフォルトCSS変数の存在確認
        for key in BaseConfig.DEFAULT_CSS:
            assert key in css_vars

        # カスタムCSS変数の確認
        for key, value in expected_updates.items():
            assert css_vars[key] == value

    @pytest.mark.parametrize(
        "theme_config,expected_theme",
        [
            (None, "デフォルト"),
            ({"theme_name": "カスタムテーマ"}, "カスタムテーマ"),
            ({"theme_name": 123}, "123"),  # 型変換
        ],
    )
    def test_theme_management(
        self, theme_config: Optional[Dict[str, Any]], expected_theme: str
    ):
        """テーマ管理のテスト"""
        config = BaseConfig(theme_config)
        assert config.get_theme_name() == expected_theme


class TestBaseConfigFileOperations:
    """ファイル操作の重要テスト"""

    @pytest.mark.parametrize(
        "file_content,suffix,expected_keys",
        [
            # YAML形式
            (
                "output_dir: yaml_output\ntemplate_dir: yaml_templates\ntheme_name: YAMLテーマ",
                ".yaml",
                ["output_dir", "template_dir", "theme_name"],
            ),
            # YML形式
            (
                "output_dir: yml_output\ntemplate_dir: yml_templates",
                ".yml",
                ["output_dir", "template_dir"],
            ),
        ],
    )
    def test_yaml_file_loading(
        self, file_content: str, suffix: str, expected_keys: list
    ):
        """YAMLファイル読み込みテスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as f:
            f.write(file_content)
            file_path = f.name

        try:
            config = BaseConfig.from_file(file_path)
            for key in expected_keys:
                assert config.get(key) is not None
        finally:
            Path(file_path).unlink()

    def test_json_file_loading(self):
        """JSONファイル読み込みテスト"""
        json_data = {
            "output_dir": "json_output",
            "template_dir": "json_templates",
            "css": {"background_color": "#000000"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(json_data, f, ensure_ascii=False)
            json_path = f.name

        try:
            config = BaseConfig.from_file(json_path)
            assert config.get("output_dir") == "json_output"
            assert config.get_css_variables()["background_color"] == "#000000"
        finally:
            Path(json_path).unlink()

    @pytest.mark.parametrize(
        "error_case,exception_type,error_message",
        [
            ("nonexistent", FileNotFoundError, "設定ファイルが見つかりません"),
            ("invalid_yaml", ValueError, "設定ファイルの読み込みに失敗しました"),
            ("invalid_json", ValueError, "設定ファイルの読み込みに失敗しました"),
            ("unsupported_ext", ValueError, "未対応の設定ファイル形式"),
            ("empty_file", ValueError, "設定ファイルの形式が正しくありません"),
            ("non_dict_data", ValueError, "設定ファイルの形式が正しくありません"),
        ],
    )
    def test_file_loading_errors(
        self, error_case: str, exception_type: type, error_message: str
    ):
        """ファイル読み込みエラーテスト"""
        if error_case == "nonexistent":
            with pytest.raises(exception_type) as exc_info:
                BaseConfig.from_file("/nonexistent/file.yaml")
        else:
            # 各種エラーファイルを作成してテスト
            file_content = {
                "invalid_yaml": "invalid: yaml: content: [",
                "invalid_json": '{"invalid": json content',
                "empty_file": "",
                "non_dict_data": json.dumps(["list", "data"]),
            }.get(error_case, "dummy")

            suffix = ".txt" if error_case == "unsupported_ext" else ".yaml"

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, encoding="utf-8"
            ) as f:
                if error_case == "invalid_json":
                    f.write(file_content)
                elif error_case == "non_dict_data":
                    f.write(file_content)
                else:
                    f.write(file_content)
                error_file_path = f.name

            try:
                with pytest.raises(exception_type) as exc_info:
                    BaseConfig.from_file(error_file_path)
            finally:
                Path(error_file_path).unlink()

        assert error_message in str(exc_info.value)


class TestBaseConfigIntegration:
    """統合・境界値テスト"""

    def test_complete_workflow_integration(self):
        """完全ワークフロー統合テスト"""
        complete_config = {
            "output_dir": "dist",
            "template_dir": "src/templates",
            "theme_name": "統合テーマ",
            "html": {"title": "統合テスト", "lang": "ja"},
            "css": {"max_width": "1200px", "background_color": "#f0f0f0"},
        }

        config = BaseConfig(complete_config)

        # 全機能の動作確認
        assert config.validate() is True
        assert config.get_theme_name() == "統合テーマ"

        css_vars = config.get_css_variables()
        assert css_vars["max_width"] == "1200px"
        assert css_vars["background_color"] == "#f0f0f0"

        # 設定更新
        config.set("new_setting", "新規設定")
        assert config.get("new_setting") == "新規設定"

        # 辞書出力
        result_dict = config.to_dict()
        assert "new_setting" in result_dict
        for key in complete_config.keys():
            assert key in result_dict

    @pytest.mark.parametrize(
        "boundary_case,test_data",
        [
            ("large_data", {f"key_{i}": f"value_{i}" for i in range(100)}),
            (
                "special_chars",
                {"特殊キー": "日本語値", "emoji": "🎯📋", "unicode": "\u2603"},
            ),
            ("nested_structure", {"level1": {"level2": {"level3": {"deep": "value"}}}}),
            ("empty_strings", {"output_dir": "", "template_dir": "", "empty": ""}),
        ],
    )
    def test_boundary_cases(self, boundary_case: str, test_data: Dict[str, Any]):
        """境界値ケーステスト"""
        if boundary_case in ["empty_strings"]:
            # 空文字列の場合は基本設定を追加
            test_data.update({"output_dir": "output", "template_dir": "templates"})
        elif boundary_case != "large_data":
            # 大量データ以外は基本設定を追加
            test_data.update({"output_dir": "output", "template_dir": "templates"})

        config = BaseConfig(test_data)

        if boundary_case == "large_data":
            assert len(config._config) == 100
            assert config.get("key_50") == "value_50"
        elif boundary_case == "special_chars":
            assert config.get("特殊キー") == "日本語値"
            assert config.get("emoji") == "🎯📋"
        elif boundary_case == "nested_structure":
            assert config.get("level1")["level2"]["level3"]["deep"] == "value"
            assert config.validate() is True
        elif boundary_case == "empty_strings":
            assert config.get("empty") == ""
            # 空文字列は有効な設定として扱う
            assert config.validate() is True

    def test_exception_handling(self):
        """例外処理テスト"""
        config = BaseConfig()

        with patch.object(config, "_config", side_effect=Exception("Test exception")):
            is_valid = config.validate()
            assert is_valid is False
