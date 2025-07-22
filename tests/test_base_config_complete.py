"""base_config.py の未カバー部分完全テスト

Phase 1 最終目標18%達成のための重要テスト
未カバー部分: from_file, validate, set with CSS, error cases
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from kumihan_formatter.config.base_config import BaseConfig


class TestBaseConfigAdvanced:
    """BaseConfig の未カバー部分テスト"""

    def test_set_css_config_update(self):
        """set()でCSS設定時の自動更新テスト"""
        config = BaseConfig()

        new_css = {
            "background_color": "#333",
            "text_color": "#fff",
            "font_size": "16px",
        }

        # CSS設定をセット
        config.set("css", new_css)

        # CSS変数が更新されることを確認
        css_vars = config.get_css_variables()
        assert css_vars["background_color"] == "#333"
        assert css_vars["text_color"] == "#fff"
        assert css_vars["font_size"] == "16px"
        assert "max_width" in css_vars  # デフォルト値は保持

    def test_validate_invalid_config_type(self):
        """validate() - 設定が辞書でない場合のテスト"""
        config = BaseConfig()
        config._config = "invalid_type"  # 辞書以外を設定

        result = config.validate()
        assert result is False

    def test_validate_invalid_css_type(self):
        """validate() - CSS設定が辞書でない場合のテスト"""
        config = BaseConfig()
        config.set("css", "invalid_css_type")  # 辞書以外を設定

        result = config.validate()
        assert result is False

    def test_validate_valid_config(self):
        """validate() - 有効な設定の場合のテスト"""
        config_data = {
            "theme_name": "test_theme",
            "css": {"color": "red", "font_size": "14px"},
            "other_setting": "value",
        }
        config = BaseConfig(config_data)

        result = config.validate()
        assert result is True


class TestFromFileMethod:
    """from_file()メソッドの完全テスト"""

    def test_from_file_json_success(self):
        """JSON設定ファイル読み込み成功テスト"""
        config_data = {"theme_name": "test_theme", "css": {"background_color": "#000"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = BaseConfig.from_file(temp_path)
            assert isinstance(config, BaseConfig)
            assert config.get("theme_name") == "test_theme"
            assert config.get("css")["background_color"] == "#000"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_yaml_success(self):
        """YAML設定ファイル読み込み成功テスト"""
        config_data = {"theme_name": "yaml_theme", "css": {"color": "blue"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = BaseConfig.from_file(temp_path)
            assert isinstance(config, BaseConfig)
            assert config.get("theme_name") == "yaml_theme"
            assert config.get("css")["color"] == "blue"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_yml_extension(self):
        """.yml拡張子でのYAML読み込みテスト"""
        config_data = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = BaseConfig.from_file(temp_path)
            assert config.get("test") == "value"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_not_found(self):
        """ファイルが見つからない場合のテスト"""
        with pytest.raises(FileNotFoundError, match="設定ファイルが見つかりません"):
            BaseConfig.from_file("nonexistent_file.json")

    def test_from_file_unsupported_extension(self):
        """未対応の拡張子の場合のテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="未対応の設定ファイル形式"):
                BaseConfig.from_file(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_invalid_json(self):
        """不正なJSON形式の場合のテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="設定ファイル解析エラー"):
                BaseConfig.from_file(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_invalid_yaml(self):
        """不正なYAML形式の場合のテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="設定ファイル解析エラー"):
                BaseConfig.from_file(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_file_non_dict_content(self):
        """辞書以外のコンテンツの場合のテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump("not a dict", f)
            temp_path = f.name

        try:
            with pytest.raises(
                ValueError, match="設定ファイルの形式が正しくありません"
            ):
                BaseConfig.from_file(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestBaseConfigEdgeCases:
    """BaseConfig のエッジケーステスト"""

    def test_get_theme_name_with_non_string(self):
        """テーマ名が文字列でない場合のテスト"""
        config = BaseConfig({"theme_name": 123})
        theme_name = config.get_theme_name()
        assert theme_name == "123"  # str()で変換される

    def test_css_variables_with_initial_css(self):
        """初期化時にCSS設定がある場合のテスト"""
        config_data = {
            "css": {
                "custom_color": "#123456",
                "max_width": "1200px",  # デフォルト値を上書き
            }
        }

        config = BaseConfig(config_data)
        css_vars = config.get_css_variables()

        assert css_vars["custom_color"] == "#123456"
        assert css_vars["max_width"] == "1200px"
        assert "background_color" in css_vars  # その他のデフォルト値は保持

    def test_set_non_css_config(self):
        """CSS以外の設定値をsetした場合のテスト"""
        config = BaseConfig()
        config.set("theme", "dark")
        config.set("font_family", "Arial")

        assert config.get("theme") == "dark"
        assert config.get("font_family") == "Arial"

    def test_to_dict_independence(self):
        """to_dict()で返される辞書の独立性テスト"""
        config = BaseConfig({"test": "original"})

        config_dict = config.to_dict()
        config_dict["test"] = "modified"

        # 元の設定は変更されない
        assert config.get("test") == "original"

    def test_css_variables_independence(self):
        """get_css_variables()で返される辞書の独立性テスト"""
        config = BaseConfig()

        css_vars = config.get_css_variables()
        css_vars["max_width"] = "modified"

        # 元のCSS変数は変更されない
        original_css_vars = config.get_css_variables()
        assert original_css_vars["max_width"] == "800px"
