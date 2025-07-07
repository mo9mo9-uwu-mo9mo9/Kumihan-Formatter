"""pydantic設定モデルのテスト

Issue #390対応 - 型安全性向上のためのテストケース
"""

import pytest
from pydantic import ValidationError

from kumihan_formatter.models.config import FormatterConfig, SimpleFormatterConfig


class TestFormatterConfig:
    """FormatterConfigのテストクラス"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されているかテスト"""
        config = FormatterConfig()

        assert config.input_encoding == "utf-8"
        assert config.output_encoding == "utf-8"
        assert config.template_dir is None
        assert config.template_name is None
        assert config.strict_mode is False
        assert config.include_source is False
        assert config.syntax_check is True
        assert config.no_preview is False
        assert config.watch_mode is False
        assert "max_width" in config.css_variables
        assert config.css_variables["max_width"] == "800px"

    def test_field_validation(self) -> None:
        """フィールドの検証が正しく機能するかテスト"""
        # 正常なケース
        config = FormatterConfig(
            input_encoding="shift_jis",
            output_encoding="utf-8",
            template_name="custom",
            strict_mode=True,
        )

        assert config.input_encoding == "shift_jis"
        assert config.template_name == "custom"
        assert config.strict_mode is True

    def test_whitespace_stripping(self) -> None:
        """文字列の前後空白が自動削除されるかテスト"""
        config = FormatterConfig(input_encoding="  utf-8  ", template_name="  custom  ")

        assert config.input_encoding == "utf-8"
        assert config.template_name == "custom"

    def test_forbidden_extra_fields(self) -> None:
        """未定義フィールドが禁止されているかテスト"""
        with pytest.raises(ValidationError) as exc_info:
            FormatterConfig(unknown_field="value")  # type: ignore

        assert "unknown_field" in str(exc_info.value)
        assert "extra" in str(exc_info.value)

    def test_assignment_validation(self) -> None:
        """代入時の検証が有効かテスト"""
        config = FormatterConfig()

        # 正常な代入
        config.input_encoding = "shift_jis"
        assert config.input_encoding == "shift_jis"

        # 不正な代入をテスト (型不一致)
        with pytest.raises(ValidationError):
            config.strict_mode = "invalid"  # type: ignore

    def test_css_variables_customization(self) -> None:
        """CSS変数のカスタマイズが正しく機能するかテスト"""
        custom_css = {
            "max_width": "1000px",
            "background_color": "#ffffff",
            "custom_var": "custom_value",
        }

        config = FormatterConfig(css_variables=custom_css)

        assert config.css_variables["max_width"] == "1000px"
        assert config.css_variables["background_color"] == "#ffffff"
        assert config.css_variables["custom_var"] == "custom_value"


class TestSimpleFormatterConfig:
    """SimpleFormatterConfigのテストクラス"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されているかテスト"""
        config = SimpleFormatterConfig()

        assert config.template_name == "default"
        assert config.include_source is False
        assert "max_width" in config.css_variables
        assert config.css_variables["max_width"] == "800px"

    def test_get_theme_name(self) -> None:
        """テーマ名の取得が正しく機能するかテスト"""
        config = SimpleFormatterConfig()

        assert config.get_theme_name() == "デフォルト"

    def test_field_validation(self) -> None:
        """フィールドの検証が正しく機能するかテスト"""
        config = SimpleFormatterConfig(template_name="custom", include_source=True)

        assert config.template_name == "custom"
        assert config.include_source is True

    def test_forbidden_extra_fields(self) -> None:
        """未定義フィールドが禁止されているかテスト"""
        with pytest.raises(ValidationError) as exc_info:
            SimpleFormatterConfig(unknown_field="value")  # type: ignore

        assert "unknown_field" in str(exc_info.value)
        assert "extra" in str(exc_info.value)

    def test_css_variables_default(self) -> None:
        """CSS変数のデフォルト値が正しく設定されているかテスト"""
        config = SimpleFormatterConfig()

        expected_keys = {
            "max_width",
            "background_color",
            "container_background",
            "text_color",
            "line_height",
            "font_family",
        }

        assert set(config.css_variables.keys()) == expected_keys
        assert config.css_variables["font_family"].startswith("Hiragino")


class TestConfigCompatibility:
    """既存システムとの互換性テスト"""

    def test_simple_config_compatibility(self) -> None:
        """simple_config.pyとの互換性テスト"""
        from kumihan_formatter.simple_config import SimpleConfig

        # 既存のSimpleConfigの動作を確認
        old_config = SimpleConfig()

        # 新しいSimpleFormatterConfigの動作を確認
        new_config = SimpleFormatterConfig()

        # 同じキーが存在することを確認
        assert old_config.get_theme_name() == new_config.get_theme_name()

        # CSS変数の主要キーが一致することを確認
        old_css = old_config.get_css_variables()
        new_css = new_config.css_variables

        common_keys = {"max_width", "background_color", "text_color", "line_height"}
        for key in common_keys:
            assert key in old_css
            assert key in new_css

    def test_config_serialization(self) -> None:
        """設定のシリアル化/デシリアル化テスト"""
        config = FormatterConfig(
            input_encoding="shift_jis",
            template_name="custom",
            strict_mode=True,
            css_variables={"custom_key": "custom_value"},
        )

        # 辞書形式でシリアル化
        config_dict = config.model_dump()

        # 辞書から復元
        restored_config = FormatterConfig(**config_dict)

        assert restored_config.input_encoding == "shift_jis"
        assert restored_config.template_name == "custom"
        assert restored_config.strict_mode is True
        assert restored_config.css_variables["custom_key"] == "custom_value"
