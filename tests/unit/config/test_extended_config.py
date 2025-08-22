"""ExtendedConfig 効率化テスト - Issue #1115

ExtendedConfig（224行）の重要機能をパラメータ化により20テストに集約。
初期化、マーカー管理、テーマ管理、バリデーション機能を効率的にテスト。
"""

from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from kumihan_formatter.config.extended_config import ExtendedConfig


class TestExtendedConfigCore:
    """ExtendedConfig コア機能テスト"""

    @pytest.mark.parametrize(
        "config_data,expected_theme,expected_markers,expected_themes",
        [
            # デフォルト初期化
            (None, "default", 11, 3),
            ({}, "default", 11, 3),
            # カスタム設定
            (
                {
                    "theme": "dark",
                    "markers": {"カスタム": {"tag": "span"}},
                    "themes": {"custom": {"name": "カスタム", "css": {"color": "red"}}},
                },
                "dark",
                12,
                4,
            ),
            # 不正設定（無視される）
            ({"markers": "invalid", "themes": "invalid"}, "default", 11, 3),
        ],
    )
    def test_initialization_patterns(
        self,
        config_data: Optional[Dict[str, Any]],
        expected_theme: str,
        expected_markers: int,
        expected_themes: int,
    ):
        """初期化パターンテスト"""
        config = ExtendedConfig(config_data)

        assert config.get_current_theme() == expected_theme
        assert len(config.get_markers()) == expected_markers
        assert len(config.get_themes()) == expected_themes

        # BaseConfig継承確認
        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get")
        assert hasattr(config, "set")

    @pytest.mark.parametrize(
        "marker_name,marker_config,expected_result",
        [
            # 新規マーカー追加
            ("新規", {"tag": "div", "class": "new"}, True),
            # 既存マーカー上書き
            ("太字", {"tag": "b", "class": "bold"}, True),
            # 空設定
            ("空", {}, True),
        ],
    )
    def test_marker_addition(
        self, marker_name: str, marker_config: Dict[str, Any], expected_result: bool
    ):
        """マーカー追加テスト"""
        config = ExtendedConfig()
        original_count = len(config.get_markers())

        config.add_marker(marker_name, marker_config)

        markers = config.get_markers()
        assert marker_name in markers
        assert markers[marker_name] == marker_config

        # カウント確認（新規追加か上書きか）
        expected_count = (
            original_count + 1 if marker_name not in ["太字"] else original_count
        )
        assert len(markers) == expected_count

    @pytest.mark.parametrize(
        "marker_to_remove,expected_success,expected_count",
        [
            # 既存マーカー削除
            ("太字", True, 10),
            # 存在しないマーカー削除
            ("存在しない", False, 11),
        ],
    )
    def test_marker_removal(
        self, marker_to_remove: str, expected_success: bool, expected_count: int
    ):
        """マーカー削除テスト"""
        config = ExtendedConfig()

        result = config.remove_marker(marker_to_remove)

        assert result == expected_success
        assert len(config.get_markers()) == expected_count
        assert marker_to_remove not in config.get_markers() or not expected_success

    def test_marker_default_verification(self):
        """デフォルトマーカー定義確認"""
        config = ExtendedConfig()
        markers = config.get_markers()

        # 重要デフォルトマーカーの確認
        expected_markers = {
            "太字": {"tag": "strong"},
            "見出し1": {"tag": "h1"},
            "折りたたみ": {"summary": "詳細を表示"},
        }

        for name, expected in expected_markers.items():
            assert name in markers
            for key, value in expected.items():
                assert markers[name][key] == value


class TestExtendedConfigThemeManagement:
    """テーマ管理テスト"""

    @pytest.mark.parametrize(
        "theme_name,theme_config,expected_result",
        [
            # 新規テーマ追加
            ("新規", {"name": "新規テーマ", "css": {"color": "blue"}}, True),
            # 既存テーマ上書き
            ("default", {"name": "上書き", "css": {"background": "white"}}, True),
            # CSS省略テーマ
            ("シンプル", {"name": "シンプル"}, True),
        ],
    )
    def test_theme_addition(
        self, theme_name: str, theme_config: Dict[str, Any], expected_result: bool
    ):
        """テーマ追加テスト"""
        config = ExtendedConfig()
        original_count = len(config.get_themes())

        config.add_theme(theme_name, theme_config)

        themes = config.get_themes()
        assert theme_name in themes
        assert themes[theme_name] == theme_config

        # カウント確認（新規追加か上書きか）
        expected_count = (
            original_count + 1 if theme_name not in ["default"] else original_count
        )
        assert len(themes) == expected_count

    @pytest.mark.parametrize(
        "theme_to_remove,expected_success,expected_count",
        [
            # 既存テーマ削除
            ("dark", True, 2),
            # 存在しないテーマ削除
            ("存在しない", False, 3),
        ],
    )
    def test_theme_removal(
        self, theme_to_remove: str, expected_success: bool, expected_count: int
    ):
        """テーマ削除テスト"""
        config = ExtendedConfig()

        result = config.remove_theme(theme_to_remove)

        assert result == expected_success
        assert len(config.get_themes()) == expected_count

    def test_theme_default_verification(self):
        """デフォルトテーマ定義確認"""
        config = ExtendedConfig()
        themes = config.get_themes()

        expected_themes = {
            "default": {"name": "デフォルト"},
            "dark": {"name": "ダーク"},
            "sepia": {"name": "セピア"},
        }

        for name, expected in expected_themes.items():
            assert name in themes
            assert themes[name]["name"] == expected["name"]

    @pytest.mark.parametrize(
        "theme_to_set,expected_theme,expected_name",
        [
            ("dark", "dark", "ダーク"),
            ("sepia", "sepia", "セピア"),
            ("default", "default", "デフォルト"),
            ("存在しない", "default", "デフォルト"),  # 存在しない場合はデフォルト
        ],
    )
    def test_theme_switching(
        self, theme_to_set: str, expected_theme: str, expected_name: str
    ):
        """テーマ切り替えテスト"""
        config = ExtendedConfig()

        config.set_theme(theme_to_set)

        assert config.get_current_theme() == expected_theme
        assert config.get_theme_name() == expected_name


class TestExtendedConfigValidation:
    """バリデーション・設定統合テスト"""

    @pytest.mark.parametrize(
        "config_data,expected_valid",
        [
            # BaseConfig基準の有効設定
            ({"output_dir": "output", "template_dir": "templates"}, True),
            # Extended独自設定込み
            (
                {
                    "output_dir": "output",
                    "template_dir": "templates",
                    "markers": {"custom": {"tag": "span"}},
                    "themes": {"custom": {"name": "カスタム"}},
                },
                True,
            ),
            # 基本設定不足
            ({"markers": {"test": {}}}, False),
            ({"template_dir": "templates"}, False),
        ],
    )
    def test_validation_patterns(
        self, config_data: Dict[str, Any], expected_valid: bool
    ):
        """バリデーションパターンテスト"""
        config = ExtendedConfig(config_data)
        assert config.validate() == expected_valid

    def test_theme_css_integration(self):
        """テーマCSS統合テスト"""
        config = ExtendedConfig()

        # カスタムCSS付きテーマ追加
        config.add_theme(
            "カスタム",
            {"name": "カスタムテーマ", "css": {"background": "red", "color": "white"}},
        )

        config.set_theme("カスタム")

        # CSS変数に反映されることを確認
        css_vars = config.get_css_variables()
        assert css_vars["background"] == "red"
        assert css_vars["color"] == "white"

    def test_marker_css_integration(self):
        """マーカーCSS統合テスト"""
        config = ExtendedConfig()

        # CSS付きマーカー追加
        config.add_marker(
            "スペシャル", {"tag": "div", "class": "special", "style": "color: purple;"}
        )

        markers = config.get_markers()
        assert markers["スペシャル"]["style"] == "color: purple;"

    def test_configuration_persistence(self):
        """設定永続性テスト"""
        config_data = {
            "output_dir": "output",
            "template_dir": "templates",
            "theme": "dark",
            "markers": {"test": {"tag": "test"}},
            "themes": {"test": {"name": "テスト"}},
        }

        config = ExtendedConfig(config_data)

        # 設定追加
        config.add_marker("追加", {"tag": "add"})
        config.add_theme("追加", {"name": "追加テーマ"})
        config.set("custom_setting", "カスタム値")

        # 全設定の永続性確認
        assert config.get_current_theme() == "dark"
        assert "test" in config.get_markers()
        assert "追加" in config.get_markers()
        assert "test" in config.get_themes()
        assert "追加" in config.get_themes()
        assert config.get("custom_setting") == "カスタム値"


class TestExtendedConfigBoundaryAndIntegration:
    """境界値・統合テスト"""

    def test_complete_extended_workflow(self):
        """完全ExtendedConfigワークフロー"""
        # 初期化
        config = ExtendedConfig(
            {"output_dir": "dist", "template_dir": "templates", "theme": "dark"}
        )

        # マーカー操作
        config.add_marker("カスタム1", {"tag": "span", "class": "custom1"})
        config.add_marker("カスタム2", {"tag": "div", "class": "custom2"})
        assert len(config.get_markers()) == 13

        # テーマ操作
        config.add_theme(
            "カスタムテーマ", {"name": "カスタム", "css": {"background": "blue"}}
        )
        config.set_theme("カスタムテーマ")
        assert config.get_current_theme() == "カスタムテーマ"

        # 削除操作
        assert config.remove_marker("カスタム1") is True
        assert config.remove_theme("sepia") is True
        assert len(config.get_markers()) == 12
        assert len(config.get_themes()) == 3

        # 最終検証
        assert config.validate() is True
        css_vars = config.get_css_variables()
        assert css_vars["background"] == "blue"

    @pytest.mark.parametrize(
        "boundary_case,config_update",
        [
            ("large_markers", {f"marker_{i}": {"tag": f"tag{i}"} for i in range(50)}),
            ("large_themes", {f"theme_{i}": {"name": f"テーマ{i}"} for i in range(20)}),
            ("special_chars", {"特殊マーカー": {"tag": "特殊"}}),
            ("empty_configs", {"empty": {}}),
        ],
    )
    def test_boundary_cases(self, boundary_case: str, config_update: Dict[str, Any]):
        """境界値ケーステスト"""
        config = ExtendedConfig({"output_dir": "output", "template_dir": "templates"})

        if boundary_case.startswith("large_markers"):
            for name, marker_config in config_update.items():
                config.add_marker(name, marker_config)
            assert len(config.get_markers()) == 11 + 50
        elif boundary_case.startswith("large_themes"):
            for name, theme_config in config_update.items():
                config.add_theme(name, theme_config)
            assert len(config.get_themes()) == 3 + 20
        elif boundary_case == "special_chars":
            config.add_marker("特殊マーカー", {"tag": "特殊"})
            assert "特殊マーカー" in config.get_markers()
        elif boundary_case == "empty_configs":
            config.add_marker("empty", {})
            config.add_theme("empty", {})
            assert "empty" in config.get_markers()
            assert "empty" in config.get_themes()

    def test_exception_handling(self):
        """例外処理テスト"""
        config = ExtendedConfig()

        # バリデーション例外
        with patch.object(config, "_config", side_effect=Exception("Test exception")):
            assert config.validate() is False

        # マーカー操作例外対応
        with patch.object(
            config, "_markers", side_effect=Exception("Marker exception")
        ):
            try:
                config.get_markers()
            except Exception:
                # 例外が発生しても適切に処理される
                pass
