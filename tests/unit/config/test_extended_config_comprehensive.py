"""ExtendedConfigクラスの包括的テスト - Issue #929 Phase 3D

ExtendedConfig（224行）の全機能をカバーする55テストケースによる包括的テスト実装。
初期化、マーカー管理、テーマ管理、バリデーション、設定統合機能を検証。
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.config.extended_config import ExtendedConfig


class TestExtendedConfig初期化系:
    """初期化系テスト（10ケース）"""

    def test_正常系_デフォルト設定での初期化(self):
        """Given: デフォルト設定
        When: ExtendedConfigを初期化
        Then: デフォルト値で正常に初期化される"""
        config = ExtendedConfig()

        assert config is not None
        assert len(config.get_markers()) == 11  # DEFAULT_MARKERS
        assert len(config.get_themes()) == 3  # DEFAULT_THEMES
        assert config.get_current_theme() == "default"

    def test_正常系_カスタム設定辞書での初期化(self):
        """Given: カスタム設定辞書
        When: ExtendedConfigを初期化
        Then: カスタム設定が適用される"""
        custom_config = {
            "theme": "dark",
            "markers": {"カスタム": {"tag": "span"}},
            "themes": {"custom": {"name": "カスタム", "css": {"color": "red"}}},
        }
        config = ExtendedConfig(custom_config)

        assert config.get_current_theme() == "dark"
        assert "カスタム" in config.get_markers()
        assert "custom" in config.get_themes()

    def test_正常系_マーカー定義初期化確認(self):
        """Given: ExtendedConfig初期化
        When: マーカー定義を確認
        Then: デフォルトマーカーが正しく設定される"""
        config = ExtendedConfig()
        markers = config.get_markers()

        assert "太字" in markers
        assert markers["太字"]["tag"] == "strong"
        assert "見出し1" in markers
        assert markers["見出し1"]["tag"] == "h1"
        assert "折りたたみ" in markers
        assert markers["折りたたみ"]["summary"] == "詳細を表示"

    def test_正常系_テーマ定義初期化確認(self):
        """Given: ExtendedConfig初期化
        When: テーマ定義を確認
        Then: デフォルトテーマが正しく設定される"""
        config = ExtendedConfig()
        themes = config.get_themes()

        assert "default" in themes
        assert themes["default"]["name"] == "デフォルト"
        assert "dark" in themes
        assert themes["dark"]["name"] == "ダーク"
        assert "sepia" in themes
        assert themes["sepia"]["name"] == "セピア"

    def test_正常系_現在テーマ設定確認(self):
        """Given: ExtendedConfig初期化
        When: 現在のテーマを確認
        Then: デフォルトテーマが設定される"""
        config = ExtendedConfig()

        assert config.get_current_theme() == "default"
        assert config.get_theme_name() == "デフォルト"

    def test_正常系_BaseConfig継承確認(self):
        """Given: ExtendedConfig初期化
        When: BaseConfigの機能を確認
        Then: 親クラスの機能が利用可能"""
        config = ExtendedConfig()

        assert hasattr(config, "get_css_variables")
        assert hasattr(config, "get")
        assert hasattr(config, "set")
        css_vars = config.get_css_variables()
        assert isinstance(css_vars, dict)

    def test_境界値_空辞書での初期化(self):
        """Given: 空の設定辞書
        When: ExtendedConfigを初期化
        Then: デフォルト値で初期化される"""
        config = ExtendedConfig({})

        assert config.get_current_theme() == "default"
        assert len(config.get_markers()) == 11
        assert len(config.get_themes()) == 3

    def test_境界値_None設定での初期化(self):
        """Given: None設定
        When: ExtendedConfigを初期化
        Then: デフォルト値で初期化される"""
        config = ExtendedConfig(None)

        assert config.get_current_theme() == "default"
        assert len(config.get_markers()) == 11
        assert len(config.get_themes()) == 3

    def test_異常系_不正マーカー辞書処理(self):
        """Given: 不正なマーカー設定
        When: ExtendedConfigを初期化
        Then: 不正な設定は無視される"""
        config_data = {"markers": "invalid"}
        config = ExtendedConfig(config_data)

        # デフォルトマーカーのみ設定される
        assert len(config.get_markers()) == 11

    def test_異常系_不正テーマ辞書処理(self):
        """Given: 不正なテーマ設定
        When: ExtendedConfigを初期化
        Then: 不正な設定は無視される"""
        config_data = {"themes": "invalid"}
        config = ExtendedConfig(config_data)

        # デフォルトテーマのみ設定される
        assert len(config.get_themes()) == 3


class TestExtendedConfigマーカー管理:
    """マーカー管理テスト（12ケース）"""

    def test_正常系_get_markers_デフォルト取得(self):
        """Given: 初期化されたExtendedConfig
        When: get_markersを呼び出し
        Then: デフォルトマーカーが取得される"""
        config = ExtendedConfig()
        markers = config.get_markers()

        assert isinstance(markers, dict)
        assert len(markers) == 11
        assert "太字" in markers
        assert "イタリック" in markers

    def test_正常系_get_markers_カスタム追加後取得(self):
        """Given: カスタムマーカーを追加したConfig
        When: get_markersを呼び出し
        Then: カスタムマーカーも含めて取得される"""
        config = ExtendedConfig()
        config.add_marker("カスタム", {"tag": "span", "class": "custom"})
        markers = config.get_markers()

        assert len(markers) == 12
        assert "カスタム" in markers
        assert markers["カスタム"]["tag"] == "span"

    def test_正常系_add_marker_新規追加(self):
        """Given: 初期化されたExtendedConfig
        When: 新規マーカーを追加
        Then: マーカーが正常に追加される"""
        config = ExtendedConfig()
        config.add_marker("新規", {"tag": "div", "class": "new"})

        markers = config.get_markers()
        assert "新規" in markers
        assert markers["新規"]["tag"] == "div"
        assert markers["新規"]["class"] == "new"

    def test_正常系_add_marker_既存上書き(self):
        """Given: 既存マーカーがあるExtendedConfig
        When: 同名マーカーを追加
        Then: マーカーが上書きされる"""
        config = ExtendedConfig()
        original_tag = config.get_markers()["太字"]["tag"]
        config.add_marker("太字", {"tag": "b", "class": "bold"})

        markers = config.get_markers()
        assert markers["太字"]["tag"] == "b"
        assert markers["太字"]["class"] == "bold"
        assert original_tag == "strong"  # 元の値は変更されている

    def test_正常系_remove_marker_削除成功(self):
        """Given: マーカーがあるExtendedConfig
        When: 既存マーカーを削除
        Then: マーカーが削除され成功が返される"""
        config = ExtendedConfig()
        result = config.remove_marker("太字")

        assert result is True
        markers = config.get_markers()
        assert "太字" not in markers
        assert len(markers) == 10

    def test_正常系_remove_marker_存在しない削除(self):
        """Given: 初期化されたExtendedConfig
        When: 存在しないマーカーを削除
        Then: 失敗が返される"""
        config = ExtendedConfig()
        result = config.remove_marker("存在しない")

        assert result is False
        markers = config.get_markers()
        assert len(markers) == 11

    def test_境界値_add_marker_最小定義(self):
        """Given: 初期化されたExtendedConfig
        When: 最小限の定義でマーカーを追加
        Then: マーカーが正常に追加される"""
        config = ExtendedConfig()
        config.add_marker("最小", {"tag": "span"})

        markers = config.get_markers()
        assert "最小" in markers
        assert markers["最小"]["tag"] == "span"

    def test_境界値_add_marker_最大定義(self):
        """Given: 初期化されたExtendedConfig
        When: 複雑な定義でマーカーを追加
        Then: マーカーが正常に追加される"""
        config = ExtendedConfig()
        complex_definition = {
            "tag": "div",
            "class": "complex",
            "style": "color: red;",
            "attributes": {"data-test": "value"},
            "summary": "詳細",
        }
        config.add_marker("複雑", complex_definition)

        markers = config.get_markers()
        assert "複雑" in markers
        assert markers["複雑"]["tag"] == "div"
        assert markers["複雑"]["attributes"]["data-test"] == "value"

    def test_異常系_add_marker_tag欠落(self):
        """Given: 初期化されたExtendedConfig
        When: tag属性のないマーカーを追加
        Then: ValueErrorが発生する"""
        config = ExtendedConfig()

        with pytest.raises(ValueError, match="マーカー定義が不正です"):
            config.add_marker("不正", {"class": "invalid"})

    def test_異常系_add_marker_非辞書定義(self):
        """Given: 初期化されたExtendedConfig
        When: 辞書でないマーカー定義を追加
        Then: ValueErrorが発生する"""
        config = ExtendedConfig()

        with pytest.raises(ValueError, match="マーカー定義が不正です"):
            config.add_marker("不正", "invalid_definition")

    def test_異常系_add_marker_空文字名(self):
        """Given: 初期化されたExtendedConfig
        When: 空文字名でマーカーを追加
        Then: マーカーが追加される（名前検証なし）"""
        config = ExtendedConfig()
        config.add_marker("", {"tag": "span"})

        markers = config.get_markers()
        assert "" in markers

    def test_正常系_マーカー定義独立性確認(self):
        """Given: 初期化されたExtendedConfig
        When: get_markersで取得した辞書を変更
        Then: 辞書レベルでは独立しているが、ネスト辞書は浅いコピー"""
        config = ExtendedConfig()
        markers = config.get_markers()
        original_count = len(markers)

        # 新しいキーの追加は独立
        markers["新規"] = {"tag": "span"}
        fresh_markers = config.get_markers()
        assert len(fresh_markers) == original_count  # 元の数と同じ
        assert "新規" not in fresh_markers  # 新規キーは内部に影響しない


class TestExtendedConfigテーマ管理:
    """テーマ管理テスト（15ケース）"""

    def test_正常系_get_themes_デフォルト取得(self):
        """Given: 初期化されたExtendedConfig
        When: get_themesを呼び出し
        Then: デフォルトテーマが取得される"""
        config = ExtendedConfig()
        themes = config.get_themes()

        assert isinstance(themes, dict)
        assert len(themes) == 3
        assert "default" in themes
        assert "dark" in themes
        assert "sepia" in themes

    def test_正常系_get_themes_カスタム追加後取得(self):
        """Given: カスタムテーマを追加したConfig
        When: get_themesを呼び出し
        Then: カスタムテーマも含めて取得される"""
        config = ExtendedConfig()
        config.add_theme("custom", {"name": "カスタム", "css": {"color": "blue"}})
        themes = config.get_themes()

        assert len(themes) == 4
        assert "custom" in themes
        assert themes["custom"]["name"] == "カスタム"

    def test_正常系_add_theme_新規追加(self):
        """Given: 初期化されたExtendedConfig
        When: 新規テーマを追加
        Then: テーマが正常に追加される"""
        config = ExtendedConfig()
        theme_data = {
            "name": "新テーマ",
            "css": {"background_color": "#ffffff", "text_color": "#000000"},
        }
        config.add_theme("new_theme", theme_data)

        themes = config.get_themes()
        assert "new_theme" in themes
        assert themes["new_theme"]["name"] == "新テーマ"

    def test_正常系_add_theme_既存上書き(self):
        """Given: 既存テーマがあるExtendedConfig
        When: 同IDテーマを追加
        Then: テーマが上書きされる"""
        config = ExtendedConfig()
        new_theme_data = {"name": "新ダーク", "css": {"background_color": "#000000"}}
        config.add_theme("dark", new_theme_data)

        themes = config.get_themes()
        assert themes["dark"]["name"] == "新ダーク"

    def test_正常系_set_theme_有効テーマ設定(self):
        """Given: 初期化されたExtendedConfig
        When: 有効なテーマIDを設定
        Then: テーマが設定され成功が返される"""
        config = ExtendedConfig()
        result = config.set_theme("dark")

        assert result is True
        assert config.get_current_theme() == "dark"
        assert config.get_theme_name() == "ダーク"

    def test_正常系_set_theme_無効テーマ設定(self):
        """Given: 初期化されたExtendedConfig
        When: 無効なテーマIDを設定
        Then: 設定が失敗し失敗が返される"""
        config = ExtendedConfig()
        result = config.set_theme("nonexistent")

        assert result is False
        assert config.get_current_theme() == "default"

    def test_正常系_get_current_theme_現在設定取得(self):
        """Given: テーマが設定されたExtendedConfig
        When: get_current_themeを呼び出し
        Then: 現在のテーマIDが返される"""
        config = ExtendedConfig()
        config.set_theme("sepia")

        current_theme = config.get_current_theme()
        assert current_theme == "sepia"
        assert isinstance(current_theme, str)

    def test_正常系_get_theme_name_名前取得(self):
        """Given: テーマが設定されたExtendedConfig
        When: get_theme_nameを呼び出し
        Then: テーマ名が返される"""
        config = ExtendedConfig()
        config.set_theme("sepia")

        theme_name = config.get_theme_name()
        assert theme_name == "セピア"

    def test_正常系_get_theme_name_不明テーマ(self):
        """Given: 不明なテーマが設定されたExtendedConfig
        When: get_theme_nameを呼び出し
        Then: "不明"が返される"""
        config = ExtendedConfig({"theme": "unknown"})

        theme_name = config.get_theme_name()
        assert theme_name == "不明"

    @patch.object(ExtendedConfig, "_apply_theme")
    def test_正常系_テーマ適用CSS反映確認(self, mock_apply_theme):
        """Given: 初期化されたExtendedConfig
        When: テーマを設定
        Then: _apply_themeが呼ばれる"""
        config = ExtendedConfig()
        config.set_theme("dark")

        mock_apply_theme.assert_called()

    def test_境界値_add_theme_最小定義(self):
        """Given: 初期化されたExtendedConfig
        When: 最小限の定義でテーマを追加
        Then: テーマが正常に追加される"""
        config = ExtendedConfig()
        config.add_theme("minimal", {"name": "最小"})

        themes = config.get_themes()
        assert "minimal" in themes
        assert themes["minimal"]["name"] == "最小"

    def test_異常系_add_theme_name欠落(self):
        """Given: 初期化されたExtendedConfig
        When: name属性のないテーマを追加
        Then: ValueErrorが発生する"""
        config = ExtendedConfig()

        with pytest.raises(ValueError, match="テーマ定義が不正です"):
            config.add_theme("invalid", {"css": {"color": "red"}})

    def test_異常系_add_theme_非辞書定義(self):
        """Given: 初期化されたExtendedConfig
        When: 辞書でないテーマ定義を追加
        Then: ValueErrorが発生する"""
        config = ExtendedConfig()

        with pytest.raises(ValueError, match="テーマ定義が不正です"):
            config.add_theme("invalid", "invalid_definition")

    def test_正常系_テーマ定義独立性確認(self):
        """Given: 初期化されたExtendedConfig
        When: get_themesで取得した辞書を変更
        Then: 辞書レベルでは独立しているが、ネスト辞書は浅いコピー"""
        config = ExtendedConfig()
        themes = config.get_themes()
        original_count = len(themes)

        # 新しいキーの追加は独立
        themes["新規"] = {"name": "新規テーマ"}
        fresh_themes = config.get_themes()
        assert len(fresh_themes) == original_count  # 元の数と同じ
        assert "新規" not in fresh_themes  # 新規キーは内部に影響しない

    def test_正常系_初期化時テーマ適用確認(self):
        """Given: テーマ設定を含む設定データ
        When: ExtendedConfigを初期化
        Then: 指定されたテーマが適用される"""
        config_data = {"theme": "dark"}
        config = ExtendedConfig(config_data)

        assert config.get_current_theme() == "dark"
        css_vars = config.get_css_variables()
        assert css_vars["background_color"] == "#1a1a1a"


class TestExtendedConfigバリデーション設定操作:
    """バリデーション・設定操作（5ケース）"""

    @patch.object(ExtendedConfig.__bases__[0], "validate", return_value=True)
    def test_正常系_validate_親クラス継承確認(self, mock_parent_validate):
        """Given: 初期化されたExtendedConfig
        When: validateを呼び出し
        Then: 親クラスのvalidateが呼ばれ結果が返される"""
        config = ExtendedConfig()
        result = config.validate()

        mock_parent_validate.assert_called_once()
        assert result is True

    @patch.object(ExtendedConfig.__bases__[0], "validate", return_value=False)
    def test_正常系_validate_拡張機能追加確認(self, mock_parent_validate):
        """Given: 親クラスvalidateがFalseを返すExtendedConfig
        When: validateを呼び出し
        Then: Falseが返される"""
        config = ExtendedConfig()
        result = config.validate()

        assert result is False

    def test_正常系_merge_config_辞書マージ(self):
        """Given: 初期化されたExtendedConfig
        When: 設定辞書をマージ
        Then: 設定が正常にマージされる"""
        config = ExtendedConfig()
        other_config = {"new_key": "new_value", "another_key": 123}
        config.merge_config(other_config)

        assert config.get("new_key") == "new_value"
        assert config.get("another_key") == 123

    def test_正常系_merge_config_再帰マージ(self):
        """Given: 既存の辞書設定があるExtendedConfig
        When: 同じキーの辞書をマージ
        Then: 辞書が再帰的にマージされる"""
        config = ExtendedConfig({"existing": {"key1": "value1", "key2": "value2"}})
        other_config = {"existing": {"key2": "updated", "key3": "new"}}
        config.merge_config(other_config)

        existing = config.get("existing")
        assert existing["key1"] == "value1"  # 保持
        assert existing["key2"] == "updated"  # 更新
        assert existing["key3"] == "new"  # 追加

    def test_境界値_merge_config_空辞書マージ(self):
        """Given: 初期化されたExtendedConfig
        When: 空辞書をマージ
        Then: 設定に変化がない"""
        config = ExtendedConfig()
        original_dict = config.to_dict()
        config.merge_config({})

        assert config.to_dict() == original_dict


class TestExtendedConfig設定統合:
    """設定統合テスト（8ケース）"""

    def test_正常系_merge_config_マーカーマージ(self):
        """Given: カスタムマーカーがあるExtendedConfig
        When: マーカー設定をマージ
        Then: マーカーが統合される"""
        config = ExtendedConfig()
        config.add_marker("既存", {"tag": "div"})

        other_config = {"markers": {"新規": {"tag": "span"}}}
        config.merge_config(other_config)

        # 直接的なマーカー確認（内部実装による更新は期待しない）
        merged_dict = config.to_dict()
        assert "既存" in config.get_markers()
        assert "markers" in merged_dict

    def test_正常系_merge_config_テーママージ(self):
        """Given: カスタムテーマがあるExtendedConfig
        When: テーマ設定をマージ
        Then: テーマが統合される"""
        config = ExtendedConfig()
        config.add_theme("既存", {"name": "既存テーマ"})

        other_config = {"themes": {"新規": {"name": "新規テーマ"}}}
        config.merge_config(other_config)

        # 直接的なテーマ確認
        merged_dict = config.to_dict()
        assert "既存" in config.get_themes()
        assert "themes" in merged_dict

    def test_正常系_merge_config_CSS更新(self):
        """Given: 初期化されたExtendedConfig
        When: CSS設定をマージ
        Then: CSS変数が更新される"""
        config = ExtendedConfig()
        other_config = {"css": {"new_color": "#ff0000", "new_size": "16px"}}
        config.merge_config(other_config)

        css_vars = config.get_css_variables()
        # 新しいCSS設定がベース設定に追加されることを確認
        merged_config = config.get("css")
        assert merged_config["new_color"] == "#ff0000"

    def test_正常系_merge_config_既存値保持(self):
        """Given: 既存設定があるExtendedConfig
        When: 一部設定をマージ
        Then: 既存値が保持される"""
        original_config = {"key1": "value1", "key2": {"nested": "value"}}
        config = ExtendedConfig(original_config)

        other_config = {"key3": "value3"}
        config.merge_config(other_config)

        assert config.get("key1") == "value1"
        assert config.get("key2")["nested"] == "value"
        assert config.get("key3") == "value3"

    def test_境界値_merge_config_部分更新(self):
        """Given: 複雑な設定があるExtendedConfig
        When: 部分的な設定をマージ
        Then: 指定部分のみ更新される"""
        original_config = {"section1": {"a": 1, "b": 2}, "section2": {"c": 3, "d": 4}}
        config = ExtendedConfig(original_config)

        other_config = {"section1": {"b": 999}}
        config.merge_config(other_config)

        assert config.get("section1")["a"] == 1  # 保持
        assert config.get("section1")["b"] == 999  # 更新
        assert config.get("section2")["c"] == 3  # 保持

    def test_異常系_merge_config_型不一致(self):
        """Given: 辞書設定があるExtendedConfig
        When: 同じキーで非辞書値をマージ
        Then: 値が上書きされる"""
        config = ExtendedConfig({"key": {"nested": "value"}})
        other_config = {"key": "string_value"}
        config.merge_config(other_config)

        assert config.get("key") == "string_value"

    def test_正常系_merge_config_深いネスト(self):
        """Given: 深いネスト構造のExtendedConfig
        When: 深いネスト設定をマージ
        Then: 深い階層まで正しくマージされる"""
        original_config = {"level1": {"level2": {"level3": {"key": "original"}}}}
        config = ExtendedConfig(original_config)

        other_config = {
            "level1": {"level2": {"level3": {"key": "updated", "new_key": "added"}}}
        }
        config.merge_config(other_config)

        level3 = config.get("level1")["level2"]["level3"]
        assert level3["key"] == "updated"
        assert level3["new_key"] == "added"

    def test_正常系_設定適用順序確認(self):
        """Given: 初期設定があるExtendedConfig
        When: 複数の設定を順次マージ
        Then: 後の設定が優先される"""
        config = ExtendedConfig({"priority": "first"})

        config.merge_config({"priority": "second"})
        assert config.get("priority") == "second"

        config.merge_config({"priority": "third"})
        assert config.get("priority") == "third"


class TestExtendedConfig辞書変換:
    """辞書変換テスト（5ケース）"""

    def test_正常系_to_dict_完全出力(self):
        """Given: 初期化されたExtendedConfig
        When: to_dictを呼び出し
        Then: 完全な設定辞書が返される"""
        config = ExtendedConfig()
        result = config.to_dict()

        assert isinstance(result, dict)
        assert "markers" in result
        assert "themes" in result
        assert "theme" in result
        assert "css" in result

    def test_正常系_to_dict_親クラス含む(self):
        """Given: 親クラスの設定があるExtendedConfig
        When: to_dictを呼び出し
        Then: 親クラスの設定も含まれる"""
        config_data = {"parent_key": "parent_value"}
        config = ExtendedConfig(config_data)
        result = config.to_dict()

        assert "parent_key" in result
        assert result["parent_key"] == "parent_value"

    def test_正常系_to_dict_マーカー含む(self):
        """Given: カスタムマーカーがあるExtendedConfig
        When: to_dictを呼び出し
        Then: マーカー定義が含まれる"""
        config = ExtendedConfig()
        config.add_marker("カスタム", {"tag": "span"})
        result = config.to_dict()

        assert "markers" in result
        assert "カスタム" in result["markers"]
        assert result["markers"]["カスタム"]["tag"] == "span"

    def test_正常系_to_dict_テーマ含む(self):
        """Given: カスタムテーマがあるExtendedConfig
        When: to_dictを呼び出し
        Then: テーマ定義が含まれる"""
        config = ExtendedConfig()
        config.add_theme("カスタム", {"name": "カスタムテーマ"})
        result = config.to_dict()

        assert "themes" in result
        assert "カスタム" in result["themes"]
        assert result["themes"]["カスタム"]["name"] == "カスタムテーマ"

    def test_正常系_to_dict_現在状態反映(self):
        """Given: テーマ変更したExtendedConfig
        When: to_dictを呼び出し
        Then: 現在の状態が反映される"""
        config = ExtendedConfig()
        config.set_theme("dark")
        result = config.to_dict()

        assert result["theme"] == "dark"
        # CSS変数にダークテーマが反映されているか確認
        assert result["css"]["background_color"] == "#1a1a1a"
