"""base_config.py の包括的テスト

Issue #929 Phase 3A: Base Configuration Module テスト
40-50テストケースでbase_config.pyの70%カバレッジ達成
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config.base_config import BaseConfig


class TestBaseConfigInitialization:
    """BaseConfig初期化のテスト"""

    def test_正常系_空設定での初期化(self):
        """空config_dataでの初期化テスト"""
        # Given
        config_data = None

        # When
        config = BaseConfig(config_data)

        # Then
        assert config._config == {}
        assert config._css_vars == BaseConfig.DEFAULT_CSS

    def test_正常系_辞書設定での初期化(self):
        """辞書config_dataでの初期化テスト"""
        # Given
        config_data = {"output_dir": "output", "template_dir": "templates"}

        # When
        config = BaseConfig(config_data)

        # Then
        assert config._config == config_data
        assert config._css_vars == BaseConfig.DEFAULT_CSS

    def test_正常系_CSS設定を含む初期化(self):
        """CSS設定を含むconfig_dataでの初期化テスト"""
        # Given
        custom_css = {"max_width": "1000px", "background_color": "#ffffff"}
        config_data = {"css": custom_css, "output_dir": "output"}

        # When
        config = BaseConfig(config_data)

        # Then
        assert config._config == config_data
        expected_css = BaseConfig.DEFAULT_CSS.copy()
        expected_css.update(custom_css)
        assert config._css_vars == expected_css

    def test_正常系_空辞書での初期化(self):
        """空辞書config_dataでの初期化テスト"""
        # Given
        config_data = {}

        # When
        config = BaseConfig(config_data)

        # Then
        assert config._config == {}
        assert config._css_vars == BaseConfig.DEFAULT_CSS

    def test_正常系_CSS設定が不正型の場合(self):
        """CSS設定が不正な型の場合の初期化テスト"""
        # Given
        config_data = {"css": "invalid_css", "output_dir": "output"}

        # When
        config = BaseConfig(config_data)

        # Then
        assert config._config == config_data
        assert config._css_vars == BaseConfig.DEFAULT_CSS


class TestBaseConfigCSS:
    """CSS変数管理のテスト"""

    def test_正常系_デフォルトCSS変数取得(self):
        """get_css_variables()のデフォルト値確認テスト"""
        # Given
        config = BaseConfig()

        # When
        css_vars = config.get_css_variables()

        # Then
        assert css_vars == BaseConfig.DEFAULT_CSS
        # コピーが返されることを確認
        css_vars["max_width"] = "modified"
        assert config._css_vars["max_width"] != "modified"

    def test_正常系_CSS設定更新後の変数反映(self):
        """CSS設定更新後の変数反映テスト"""
        # Given
        config = BaseConfig()
        custom_css = {"max_width": "1200px", "text_color": "#000"}

        # When
        config.set("css", custom_css)
        css_vars = config.get_css_variables()

        # Then
        expected = BaseConfig.DEFAULT_CSS.copy()
        expected.update(custom_css)
        assert css_vars == expected

    def test_正常系_DEFAULT_CSS定数の確認(self):
        """DEFAULT_CSS定数の確認テスト"""
        # Given-When
        default_css = BaseConfig.DEFAULT_CSS

        # Then
        expected_keys = [
            "max_width",
            "background_color",
            "container_background",
            "text_color",
            "line_height",
            "font_family",
        ]
        for key in expected_keys:
            assert key in default_css
        assert isinstance(default_css["max_width"], str)
        assert isinstance(default_css["background_color"], str)
        assert isinstance(default_css["font_family"], str)

    def test_正常系_CSS変数の独立性(self):
        """CSS変数の独立性確認テスト"""
        # Given
        config1 = BaseConfig({"css": {"max_width": "800px"}})
        config2 = BaseConfig({"css": {"max_width": "1000px"}})

        # When
        css1 = config1.get_css_variables()
        css2 = config2.get_css_variables()

        # Then
        assert css1["max_width"] == "800px"
        assert css2["max_width"] == "1000px"


class TestBaseConfigValues:
    """設定値操作のテスト"""

    def test_正常系_get_存在するキー(self):
        """get()の正常系（存在するキー）テスト"""
        # Given
        config_data = {"output_dir": "output", "template_dir": "templates"}
        config = BaseConfig(config_data)

        # When
        output_dir = config.get("output_dir")

        # Then
        assert output_dir == "output"

    def test_正常系_get_デフォルト値(self):
        """get()のデフォルト値テスト"""
        # Given
        config = BaseConfig()

        # When
        value = config.get("non_existent", "default_value")

        # Then
        assert value == "default_value"

    def test_正常系_get_存在しないキー(self):
        """get()で存在しないキーテスト"""
        # Given
        config = BaseConfig()

        # When
        value = config.get("non_existent")

        # Then
        assert value is None

    def test_正常系_set_値設定(self):
        """set()での値設定テスト"""
        # Given
        config = BaseConfig()

        # When
        config.set("new_key", "new_value")

        # Then
        assert config.get("new_key") == "new_value"

    def test_正常系_set_CSS自動更新(self):
        """set()でのCSS自動更新テスト"""
        # Given
        config = BaseConfig()
        custom_css = {"max_width": "900px", "new_property": "new_value"}

        # When
        config.set("css", custom_css)

        # Then
        css_vars = config.get_css_variables()
        assert css_vars["max_width"] == "900px"
        assert css_vars["new_property"] == "new_value"

    def test_正常系_to_dict_辞書変換(self):
        """to_dict()での辞書変換テスト"""
        # Given
        config_data = {"key1": "value1", "key2": {"nested": "value"}}
        config = BaseConfig(config_data)

        # When
        result = config.to_dict()

        # Then
        assert result == config_data
        # コピーが返されることを確認
        result["key3"] = "value3"
        assert "key3" not in config._config

    def test_正常系_set_CSS非辞書型(self):
        """set()でCSS非辞書型の値設定テスト"""
        # Given
        config = BaseConfig()

        # When
        config.set("css", "invalid_css_value")

        # Then
        # CSS変数は更新されない
        assert config.get_css_variables() == BaseConfig.DEFAULT_CSS


class TestBaseConfigTheme:
    """テーマ管理のテスト"""

    def test_正常系_get_theme_name_デフォルト値(self):
        """get_theme_name()のデフォルト値テスト"""
        # Given
        config = BaseConfig()

        # When
        theme_name = config.get_theme_name()

        # Then
        assert theme_name == "デフォルト"

    def test_正常系_get_theme_name_カスタムテーマ(self):
        """カスタムテーマ名の取得テスト"""
        # Given
        config_data = {"theme_name": "カスタムテーマ"}
        config = BaseConfig(config_data)

        # When
        theme_name = config.get_theme_name()

        # Then
        assert theme_name == "カスタムテーマ"

    def test_正常系_get_theme_name_型変換(self):
        """get_theme_name()の型変換テスト"""
        # Given
        config_data = {"theme_name": 123}
        config = BaseConfig(config_data)

        # When
        theme_name = config.get_theme_name()

        # Then
        assert theme_name == "123"
        assert isinstance(theme_name, str)


class TestBaseConfigValidation:
    """設定検証のテスト"""

    def test_正常系_validate_有効な設定(self):
        """validate()の正常系（有効な設定）テスト"""
        # Given
        valid_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "html": {"title": "Test"},
            "css": {"color": "blue"},
        }
        config = BaseConfig(valid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is True

    def test_異常系_validate_必須項目欠落_output_dir(self):
        """必須項目欠落（output_dir）テスト"""
        # Given
        invalid_config = {"template_dir": "templates"}
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_異常系_validate_必須項目欠落_template_dir(self):
        """必須項目欠落（template_dir）テスト"""
        # Given
        invalid_config = {"output_dir": "output"}
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_異常系_validate_型不整合_output_dir(self):
        """型不整合（output_dir）テスト"""
        # Given
        invalid_config = {"output_dir": 123, "template_dir": "templates"}
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_異常系_validate_型不整合_template_dir(self):
        """型不整合（template_dir）テスト"""
        # Given
        invalid_config = {"output_dir": "output", "template_dir": 123}
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_異常系_validate_html設定の型不整合(self):
        """html設定の検証テスト"""
        # Given
        invalid_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "html": "invalid_html_config",
        }
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_異常系_validate_css設定の型不整合(self):
        """css設定の検証テスト"""
        # Given
        invalid_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "css": ["invalid", "css", "config"],
        }
        config = BaseConfig(invalid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is False

    def test_正常系_validate_html設定が辞書型(self):
        """正常なhtml設定の検証テスト"""
        # Given
        valid_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "html": {"title": "Test Title", "lang": "ja"},
        }
        config = BaseConfig(valid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is True

    def test_正常系_validate_css設定が辞書型(self):
        """正常なcss設定の検証テスト"""
        # Given
        valid_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "css": {"color": "red", "font-size": "14px"},
        }
        config = BaseConfig(valid_config)

        # When
        is_valid = config.validate()

        # Then
        assert is_valid is True

    def test_異常系_validate_例外発生時(self):
        """例外処理のテスト"""
        # Given
        config = BaseConfig()

        # When
        with patch.object(config, "_config", side_effect=Exception("Test exception")):
            is_valid = config.validate()

        # Then
        assert is_valid is False


class TestBaseConfigFileOperations:
    """ファイル操作のテスト"""

    def test_正常系_from_file_YAML読み込み(self):
        """from_file()でYAMLファイル読み込みテスト"""
        # Given
        yaml_content = """
output_dir: output
template_dir: templates
theme_name: テストテーマ
css:
  max_width: 900px
  color: red
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            yaml_file_path = f.name

        try:
            # When
            config = BaseConfig.from_file(yaml_file_path)

            # Then
            assert config.get("output_dir") == "output"
            assert config.get("template_dir") == "templates"
            assert config.get("theme_name") == "テストテーマ"
            assert config.get_css_variables()["max_width"] == "900px"
            assert config.get_css_variables()["color"] == "red"
        finally:
            Path(yaml_file_path).unlink()

    def test_正常系_from_file_JSON読み込み(self):
        """from_file()でJSONファイル読み込みテスト"""
        # Given
        json_data = {
            "output_dir": "json_output",
            "template_dir": "json_templates",
            "css": {"background_color": "#000000"},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(json_data, f, ensure_ascii=False)
            json_file_path = f.name

        try:
            # When
            config = BaseConfig.from_file(json_file_path)

            # Then
            assert config.get("output_dir") == "json_output"
            assert config.get("template_dir") == "json_templates"
            assert config.get_css_variables()["background_color"] == "#000000"
        finally:
            Path(json_file_path).unlink()

    def test_異常系_from_file_ファイル存在しない(self):
        """ファイルが存在しない場合のエラーテスト"""
        # Given
        non_existent_file = "/path/to/non_existent_file.yaml"

        # When & Then
        with pytest.raises(FileNotFoundError) as exc_info:
            BaseConfig.from_file(non_existent_file)

        assert "設定ファイルが見つかりません" in str(exc_info.value)

    def test_異常系_from_file_不正YAML形式(self):
        """不正な形式のYAMLファイルテスト"""
        # Given
        invalid_yaml = "invalid: yaml: content: ["
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(invalid_yaml)
            invalid_yaml_path = f.name

        try:
            # When & Then
            with pytest.raises(ValueError) as exc_info:
                BaseConfig.from_file(invalid_yaml_path)

            assert "設定ファイルの読み込みに失敗しました" in str(exc_info.value)
        finally:
            Path(invalid_yaml_path).unlink()

    def test_異常系_from_file_不正JSON形式(self):
        """不正な形式のJSONファイルテスト"""
        # Given
        invalid_json = '{"invalid": json content'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(invalid_json)
            invalid_json_path = f.name

        try:
            # When & Then
            with pytest.raises(ValueError) as exc_info:
                BaseConfig.from_file(invalid_json_path)

            assert "設定ファイルの読み込みに失敗しました" in str(exc_info.value)
        finally:
            Path(invalid_json_path).unlink()

    def test_異常系_from_file_未対応拡張子(self):
        """未対応拡張子のファイルテスト"""
        # Given
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("some content")
            txt_file_path = f.name

        try:
            # When & Then
            with pytest.raises(ValueError) as exc_info:
                BaseConfig.from_file(txt_file_path)

            assert "未対応の設定ファイル形式" in str(exc_info.value)
        finally:
            Path(txt_file_path).unlink()

    def test_異常系_from_file_空ファイル(self):
        """空ファイルの処理テスト"""
        # Given
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            empty_file_path = f.name

        try:
            # When & Then
            # 空ファイルはValueErrorを発生させる
            with pytest.raises(ValueError) as exc_info:
                BaseConfig.from_file(empty_file_path)

            assert "設定ファイルの形式が正しくありません" in str(exc_info.value)
        finally:
            Path(empty_file_path).unlink()

    def test_異常系_from_file_非辞書データ(self):
        """非辞書データのファイルテスト"""
        # Given
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(["list", "data"], f)
            list_file_path = f.name

        try:
            # When & Then
            with pytest.raises(ValueError) as exc_info:
                BaseConfig.from_file(list_file_path)

            assert "設定ファイルの形式が正しくありません" in str(exc_info.value)
        finally:
            Path(list_file_path).unlink()

    def test_正常系_from_file_yml拡張子(self):
        """YML拡張子での読み込みテスト"""
        # Given
        yaml_content = "output_dir: yml_output\ntemplate_dir: yml_templates"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            yml_file_path = f.name

        try:
            # When
            config = BaseConfig.from_file(yml_file_path)

            # Then
            assert config.get("output_dir") == "yml_output"
            assert config.get("template_dir") == "yml_templates"
        finally:
            Path(yml_file_path).unlink()


class TestBaseConfigBoundaryAndError:
    """境界値・エラーケースのテスト"""

    def test_境界値_大量データでの処理(self):
        """大量データでの処理テスト"""
        # Given
        large_config = {}
        for i in range(1000):
            large_config[f"key_{i}"] = f"value_{i}"

        # When
        config = BaseConfig(large_config)

        # Then
        assert len(config._config) == 1000
        assert config.get("key_500") == "value_500"
        assert config.to_dict() == large_config

    def test_境界値_特殊文字を含む設定(self):
        """特殊文字を含む設定テスト"""
        # Given
        special_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "特殊キー": "日本語値",
            "emoji_key": "🎯📋🔧",
            "symbol_key": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "unicode_key": "\u2603\u26c4\u2744",
        }

        # When
        config = BaseConfig(special_config)

        # Then
        assert config.get("特殊キー") == "日本語値"
        assert config.get("emoji_key") == "🎯📋🔧"
        assert config.get("symbol_key") == "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        assert config.get("unicode_key") == "\u2603\u26c4\u2744"

    def test_境界値_ネストした辞書構造(self):
        """深くネストした辞書構造のテスト"""
        # Given
        nested_config = {
            "output_dir": "output",
            "template_dir": "templates",
            "level1": {"level2": {"level3": {"deep_value": "found"}}},
        }

        # When
        config = BaseConfig(nested_config)

        # Then
        assert config.get("level1")["level2"]["level3"]["deep_value"] == "found"
        assert config.validate() is True

    def test_境界値_空文字列設定(self):
        """空文字列設定のテスト"""
        # Given
        empty_string_config = {"output_dir": "", "template_dir": "", "empty_value": ""}

        # When
        config = BaseConfig(empty_string_config)

        # Then
        assert config.get("output_dir") == ""
        assert config.get("template_dir") == ""
        assert config.get("empty_value") == ""
        # 空文字列は文字列型なので検証は通る
        assert config.validate() is True


class TestBaseConfigIntegration:
    """統合テスト"""

    def test_統合_完全な設定ワークフロー(self):
        """完全な設定ワークフローの統合テスト"""
        # Given
        complete_config = {
            "output_dir": "dist",
            "template_dir": "src/templates",
            "theme_name": "完全テーマ",
            "html": {"title": "統合テスト", "lang": "ja", "charset": "UTF-8"},
            "css": {
                "max_width": "1200px",
                "background_color": "#f0f0f0",
                "font_family": "ヒラギノ角ゴ ProN",
            },
        }

        # When
        config = BaseConfig(complete_config)

        # Then - 全機能の動作確認
        assert config.validate() is True
        assert config.get_theme_name() == "完全テーマ"

        css_vars = config.get_css_variables()
        assert css_vars["max_width"] == "1200px"
        assert css_vars["background_color"] == "#f0f0f0"
        assert css_vars["font_family"] == "ヒラギノ角ゴ ProN"

        # 設定の追加更新
        config.set("new_setting", "新しい設定")
        assert config.get("new_setting") == "新しい設定"

        # 辞書出力
        result_dict = config.to_dict()
        assert result_dict["new_setting"] == "新しい設定"
        # 新しい設定が追加されていることを確認
        assert "new_setting" in result_dict
        for key in complete_config.keys():
            assert key in result_dict

    def test_統合_ファイルから読み込みして検証(self):
        """ファイルから読み込みして検証する統合テスト"""
        # Given
        yaml_content = """
output_dir: integration_output
template_dir: integration_templates
theme_name: 統合テストテーマ
html:
  title: ファイル読み込みテスト
  description: 統合テスト用の設定
css:
  max_width: 1000px
  text_color: "#333333"
  line_height: "1.6"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            integration_file_path = f.name

        try:
            # When
            config = BaseConfig.from_file(integration_file_path)

            # Then
            assert config.validate() is True
            assert config.get_theme_name() == "統合テストテーマ"
            assert config.get("html")["title"] == "ファイル読み込みテスト"

            css_vars = config.get_css_variables()
            assert css_vars["max_width"] == "1000px"
            assert css_vars["text_color"] == "#333333"
            assert css_vars["line_height"] == "1.6"

        finally:
            Path(integration_file_path).unlink()
