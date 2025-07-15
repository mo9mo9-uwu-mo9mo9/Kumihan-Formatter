"""設定系機能の包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（設定系 58% → 80%以上）
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from kumihan_formatter.simple_config import SimpleConfig, create_simple_config


class TestSimpleConfig(TestCase):
    """SimpleConfigクラスのテスト"""

    def test_simple_config_initialization(self) -> None:
        """SimpleConfig初期化のテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {"color": "blue"}
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            mock_create.assert_called_once_with(config_type="base")
            self.assertEqual(config._manager, mock_manager)
            self.assertEqual(config.css_vars, {"color": "blue"})

    def test_get_css_variables(self) -> None:
        """CSS変数取得のテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            expected_css = {
                "max_width": "800px",
                "background_color": "#f9f9f9",
                "text_color": "#333",
            }
            mock_manager.get_css_variables.return_value = expected_css
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_css_variables()

            self.assertEqual(result, expected_css)
            mock_manager.get_css_variables.assert_called()

    def test_get_theme_name(self) -> None:
        """テーマ名取得のテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_theme_name.return_value = "default"
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_theme_name()

            self.assertEqual(result, "default")
            mock_manager.get_theme_name.assert_called_once()

    def test_default_css_constants(self) -> None:
        """デフォルトCSS定数のテスト"""
        expected_keys = [
            "max_width",
            "background_color",
            "container_background",
            "text_color",
            "line_height",
            "font_family",
        ]

        for key in expected_keys:
            self.assertIn(key, SimpleConfig.DEFAULT_CSS)

        # 具体的な値も確認
        self.assertEqual(SimpleConfig.DEFAULT_CSS["max_width"], "800px")
        self.assertEqual(SimpleConfig.DEFAULT_CSS["text_color"], "#333")
        self.assertEqual(SimpleConfig.DEFAULT_CSS["line_height"], "1.8")

    def test_css_variables_delegation(self) -> None:
        """CSS変数の委譲テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {"test": "value"}
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # 初期化時とget_css_variables呼び出し時の両方で委譲されることを確認
            result = config.get_css_variables()

            self.assertEqual(result, {"test": "value"})
            # get_css_variablesが少なくとも2回呼ばれる（初期化時 + 明示的呼び出し）
            self.assertGreaterEqual(mock_manager.get_css_variables.call_count, 2)


class TestCreateSimpleConfig(TestCase):
    """create_simple_config関数のテスト"""

    def test_create_simple_config_function(self) -> None:
        """create_simple_config関数のテスト"""
        with patch("kumihan_formatter.simple_config.SimpleConfig") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            result = create_simple_config()

            mock_class.assert_called_once()
            self.assertEqual(result, mock_instance)

    def test_create_simple_config_returns_instance(self) -> None:
        """create_simple_config関数が正しいインスタンスを返すテスト"""
        with patch("kumihan_formatter.simple_config.create_config_manager"):
            result = create_simple_config()

            self.assertIsInstance(result, SimpleConfig)

    def test_create_simple_config_integration(self) -> None:
        """create_simple_config統合テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {"integration": "test"}
            mock_manager.get_theme_name.return_value = "integration_theme"
            mock_create.return_value = mock_manager

            config = create_simple_config()

            # 正しく機能することを確認
            self.assertEqual(config.get_css_variables(), {"integration": "test"})
            self.assertEqual(config.get_theme_name(), "integration_theme")


class TestSimpleConfigCompatibility(TestCase):
    """SimpleConfigの互換性テスト"""

    def test_manager_delegation(self) -> None:
        """マネージャーへの委譲テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # マネージャーが正しく設定されることを確認
            self.assertEqual(config._manager, mock_manager)
            mock_create.assert_called_once_with(config_type="base")

    def test_css_vars_initialization(self) -> None:
        """CSS変数の初期化テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            initial_css = {"init": "value"}
            mock_manager.get_css_variables.return_value = initial_css
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # 初期化時にCSS変数が設定されることを確認
            self.assertEqual(config.css_vars, initial_css)

    def test_multiple_get_css_variables_calls(self) -> None:
        """複数回のCSS変数取得テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {"multi": "call"}
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # 複数回呼び出し
            result1 = config.get_css_variables()
            result2 = config.get_css_variables()

            self.assertEqual(result1, {"multi": "call"})
            self.assertEqual(result2, {"multi": "call"})
            # 各呼び出しで委譲されることを確認
            self.assertGreaterEqual(mock_manager.get_css_variables.call_count, 3)

    def test_theme_name_consistency(self) -> None:
        """テーマ名の一貫性テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_theme_name.return_value = "consistent_theme"
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # 複数回呼び出しても一貫した結果が返されることを確認
            theme1 = config.get_theme_name()
            theme2 = config.get_theme_name()

            self.assertEqual(theme1, "consistent_theme")
            self.assertEqual(theme2, "consistent_theme")
            self.assertEqual(mock_manager.get_theme_name.call_count, 2)


class TestSimpleConfigEdgeCases(TestCase):
    """SimpleConfigのエッジケーステスト"""

    def test_empty_css_variables(self) -> None:
        """空のCSS変数テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {}
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_css_variables()

            self.assertEqual(result, {})
            self.assertEqual(config.css_vars, {})

    def test_none_theme_name(self) -> None:
        """Noneテーマ名テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_theme_name.return_value = None
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_theme_name()

            self.assertIsNone(result)

    def test_large_css_variables(self) -> None:
        """大量のCSS変数テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            large_css = {f"var_{i}": f"value_{i}" for i in range(100)}
            mock_manager.get_css_variables.return_value = large_css
            mock_create.return_value = mock_manager

            config = SimpleConfig()
            result = config.get_css_variables()

            self.assertEqual(len(result), 100)
            self.assertEqual(result["var_0"], "value_0")
            self.assertEqual(result["var_99"], "value_99")

    def test_unicode_values(self) -> None:
        """Unicode値テスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            unicode_css = {
                "font_family": "游ゴシック, Yu Gothic",
                "content": "こんにちは世界",
                "emoji": "🎨📝",
            }
            mock_manager.get_css_variables.return_value = unicode_css
            mock_manager.get_theme_name.return_value = "日本語テーマ"
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            css_result = config.get_css_variables()
            theme_result = config.get_theme_name()

            self.assertEqual(css_result["font_family"], "游ゴシック, Yu Gothic")
            self.assertEqual(css_result["content"], "こんにちは世界")
            self.assertEqual(css_result["emoji"], "🎨📝")
            self.assertEqual(theme_result, "日本語テーマ")


class TestSimpleConfigIntegration(TestCase):
    """SimpleConfigの統合テスト"""

    def test_full_workflow(self) -> None:
        """完全なワークフローテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            mock_manager.get_css_variables.return_value = {
                "max_width": "1200px",
                "background_color": "#ffffff",
            }
            mock_manager.get_theme_name.return_value = "modern"
            mock_create.return_value = mock_manager

            # ファクトリ関数を使用してインスタンスを作成
            config = create_simple_config()

            # 各機能をテスト
            css_vars = config.get_css_variables()
            theme_name = config.get_theme_name()

            # 結果を検証
            self.assertEqual(css_vars["max_width"], "1200px")
            self.assertEqual(css_vars["background_color"], "#ffffff")
            self.assertEqual(theme_name, "modern")

            # 統合設定システムとの連携を確認
            mock_create.assert_called_once_with(config_type="base")

    def test_error_handling(self) -> None:
        """エラーハンドリングテスト"""
        with patch(
            "kumihan_formatter.simple_config.create_config_manager"
        ) as mock_create:
            mock_manager = MagicMock()
            # 初期化時は正常に動作させる
            mock_manager.get_css_variables.return_value = {"init": "ok"}
            mock_create.return_value = mock_manager

            config = SimpleConfig()

            # その後エラーを設定
            mock_manager.get_css_variables.side_effect = Exception("CSS取得エラー")
            mock_manager.get_theme_name.side_effect = Exception("テーマ取得エラー")

            # エラーが適切に伝播されることを確認
            with self.assertRaises(Exception) as cm:
                config.get_css_variables()
            self.assertEqual(str(cm.exception), "CSS取得エラー")

            with self.assertRaises(Exception) as cm:
                config.get_theme_name()
            self.assertEqual(str(cm.exception), "テーマ取得エラー")
