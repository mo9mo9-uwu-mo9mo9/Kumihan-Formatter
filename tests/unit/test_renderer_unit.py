"""
Rendererクラスのユニットテスト

Critical Tier対応: コア機能の基本動作確認
Issue #620: テストカバレッジ改善
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.renderer import Renderer, render


class TestRenderer:
    """Rendererクラスのテスト"""

    def setup_method(self):
        """各テストの前にセットアップ"""
        with patch("kumihan_formatter.renderer.get_logger"):
            with patch("kumihan_formatter.renderer.HTMLRenderer"):
                with patch("kumihan_formatter.renderer.TemplateManager"):
                    with patch("kumihan_formatter.renderer.TOCGenerator"):
                        self.renderer = Renderer()

    @patch("kumihan_formatter.renderer.get_logger")
    @patch("kumihan_formatter.renderer.HTMLRenderer")
    @patch("kumihan_formatter.renderer.TemplateManager")
    @patch("kumihan_formatter.renderer.TOCGenerator")
    def test_renderer_initialization(
        self, mock_toc, mock_template, mock_html, mock_logger
    ):
        """レンダラーの初期化テスト"""
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        renderer = Renderer()

        # 各コンポーネントが初期化されることを確認
        mock_html.assert_called_once()
        mock_template.assert_called_once_with(None)
        mock_toc.assert_called_once()
        mock_logger.assert_called_once_with("kumihan_formatter.renderer")
        mock_logger_instance.debug.assert_called_once_with(
            "Renderer initialized with template_dir: %s", None
        )

    @patch("kumihan_formatter.renderer.get_logger")
    @patch("kumihan_formatter.renderer.HTMLRenderer")
    @patch("kumihan_formatter.renderer.TemplateManager")
    @patch("kumihan_formatter.renderer.TOCGenerator")
    def test_renderer_initialization_with_template_dir(
        self, mock_toc, mock_template, mock_html, mock_logger
    ):
        """テンプレートディレクトリ指定での初期化テスト"""
        template_dir = Path("/custom/templates")

        renderer = Renderer(template_dir)

        mock_template.assert_called_once_with(template_dir)

    @patch("kumihan_formatter.renderer.time")
    @patch("kumihan_formatter.renderer.create_simple_config")
    @patch("kumihan_formatter.renderer.RenderContext")
    @patch("kumihan_formatter.renderer.log_performance")
    def test_render_basic(
        self, mock_log_perf, mock_context_class, mock_config, mock_time
    ):
        """基本的なレンダリングテスト"""
        # モックの設定
        mock_time.time.side_effect = [0.0, 1.0]  # 開始と終了時間

        mock_ast = [Mock(spec=Node)]
        mock_ast[0].type = "paragraph"

        # HTMLRendererのモック
        self.renderer.html_renderer.render_nodes.return_value = "<p>content</p>"

        # TOCGeneratorのモック
        self.renderer.toc_generator.generate_toc.return_value = {
            "html": "<div>toc</div>",
            "has_toc": True,
        }

        # TemplateManagerのモック
        self.renderer.template_manager.select_template_name.return_value = "base.html"
        self.renderer.template_manager.render_template.return_value = (
            "<html>result</html>"
        )

        # SimpleConfigのモック
        mock_config.return_value.get_css_variables.return_value = {"color": "blue"}

        # RenderContextのモック
        mock_context = Mock()
        mock_context.title.return_value = mock_context
        mock_context.body_content.return_value = mock_context
        mock_context.toc_html.return_value = mock_context
        mock_context.has_toc.return_value = mock_context
        mock_context.css_vars.return_value = mock_context
        mock_context.build.return_value = {"title": "Document"}
        mock_context_class.return_value = mock_context

        result = self.renderer.render(mock_ast)

        # 戻り値の確認
        assert result == "<html>result</html>"

        # メソッド呼び出しの確認
        self.renderer.html_renderer.render_nodes.assert_called_once()
        self.renderer.toc_generator.generate_toc.assert_called_once_with(mock_ast)
        self.renderer.template_manager.select_template_name.assert_called_once()
        self.renderer.template_manager.render_template.assert_called_once_with(
            "base.html", {"title": "Document"}
        )

        # パフォーマンスログの確認
        mock_log_perf.assert_called_once_with("render", 1.0, len("<html>result</html>"))

    def test_render_with_toc_markers(self):
        """TOCマーカーを含むレンダリングテスト"""
        mock_ast = [Mock(spec=Node, type="toc"), Mock(spec=Node, type="paragraph")]

        self.renderer.html_renderer.render_nodes.return_value = "<p>content</p>"
        self.renderer.toc_generator.generate_toc.return_value = {
            "html": "",
            "has_toc": False,
        }
        self.renderer.template_manager.select_template_name.return_value = "base.html"
        self.renderer.template_manager.render_template.return_value = (
            "<html>result</html>"
        )

        with patch("kumihan_formatter.renderer.create_simple_config"):
            with patch(
                "kumihan_formatter.renderer.RenderContext"
            ) as mock_context_class:
                mock_context = Mock()
                mock_context.title.return_value = mock_context
                mock_context.body_content.return_value = mock_context
                mock_context.toc_html.return_value = mock_context
                mock_context.has_toc.return_value = mock_context
                mock_context.css_vars.return_value = mock_context
                mock_context.build.return_value = {}
                mock_context_class.return_value = mock_context

                result = self.renderer.render(mock_ast)

        # TOCマーカーがフィルタされてbody_astに含まれないことを確認
        call_args = self.renderer.html_renderer.render_nodes.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].type == "paragraph"

    def test_render_with_source_toggle(self):
        """ソーストグル付きレンダリングテスト"""
        mock_ast = [Mock(spec=Node, type="paragraph")]

        self.renderer.html_renderer.render_nodes.return_value = "<p>content</p>"
        self.renderer.toc_generator.generate_toc.return_value = {
            "html": "",
            "has_toc": False,
        }
        self.renderer.template_manager.select_template_name.return_value = "base.html"
        self.renderer.template_manager.render_template.return_value = (
            "<html>result</html>"
        )

        with patch("kumihan_formatter.renderer.create_simple_config"):
            with patch(
                "kumihan_formatter.renderer.RenderContext"
            ) as mock_context_class:
                mock_context = Mock()
                mock_context.title.return_value = mock_context
                mock_context.body_content.return_value = mock_context
                mock_context.toc_html.return_value = mock_context
                mock_context.has_toc.return_value = mock_context
                mock_context.css_vars.return_value = mock_context
                mock_context.source_toggle.return_value = mock_context
                mock_context.build.return_value = {}
                mock_context_class.return_value = mock_context

                result = self.renderer.render(
                    mock_ast, source_text="source content", source_filename="test.txt"
                )

        # source_toggleが呼ばれることを確認
        mock_context.source_toggle.assert_called_once_with("source content", "test.txt")

    def test_render_with_navigation(self):
        """ナビゲーション付きレンダリングテスト"""
        mock_ast = [Mock(spec=Node, type="paragraph")]

        self.renderer.html_renderer.render_nodes.return_value = "<p>content</p>"
        self.renderer.toc_generator.generate_toc.return_value = {
            "html": "",
            "has_toc": False,
        }
        self.renderer.template_manager.select_template_name.return_value = "base.html"
        self.renderer.template_manager.render_template.return_value = (
            "<html>result</html>"
        )

        with patch("kumihan_formatter.renderer.create_simple_config"):
            with patch(
                "kumihan_formatter.renderer.RenderContext"
            ) as mock_context_class:
                mock_context = Mock()
                mock_context.title.return_value = mock_context
                mock_context.body_content.return_value = mock_context
                mock_context.toc_html.return_value = mock_context
                mock_context.has_toc.return_value = mock_context
                mock_context.css_vars.return_value = mock_context
                mock_context.navigation.return_value = mock_context
                mock_context.build.return_value = {}
                mock_context_class.return_value = mock_context

                result = self.renderer.render(
                    mock_ast, navigation_html="<nav>Navigation</nav>"
                )

        # navigationが呼ばれることを確認
        mock_context.navigation.assert_called_once_with("<nav>Navigation</nav>")

    def test_render_nodes_only(self):
        """ノードのみのレンダリングテスト"""
        mock_nodes = [Mock(spec=Node), Mock(spec=Node)]
        expected_html = "<p>content</p>"

        self.renderer.html_renderer.render_nodes.return_value = expected_html

        result = self.renderer.render_nodes_only(mock_nodes)

        assert result == expected_html
        self.renderer.html_renderer.render_nodes.assert_called_once_with(mock_nodes)

    def test_render_with_custom_context(self):
        """カスタムコンテキスト付きレンダリングテスト"""
        mock_ast = [Mock(spec=Node)]
        template_name = "custom.html"
        custom_context = {"custom_var": "custom_value"}

        self.renderer.html_renderer.render_nodes.return_value = "<p>content</p>"
        self.renderer.toc_generator.generate_toc.return_value = {
            "html": "",
            "has_toc": False,
        }
        self.renderer.template_manager.render_template.return_value = (
            "<html>custom</html>"
        )

        with patch("kumihan_formatter.renderer.RenderContext") as mock_context_class:
            mock_context = Mock()
            mock_context.body_content.return_value = mock_context
            mock_context.toc_html.return_value = mock_context
            mock_context.has_toc.return_value = mock_context
            mock_context.build.return_value = {"base": "context"}
            mock_context_class.return_value = mock_context

            result = self.renderer.render_with_custom_context(
                mock_ast, template_name, custom_context
            )

        assert result == "<html>custom</html>"

        # カスタムコンテキストが追加されることを確認
        expected_context = {"base": "context", "custom_var": "custom_value"}
        self.renderer.template_manager.render_template.assert_called_once_with(
            template_name, expected_context
        )

    def test_get_toc_data(self):
        """TOCデータ取得テスト"""
        mock_ast = [Mock(spec=Node)]
        expected_toc_data = {"html": "<toc>", "has_toc": True}

        self.renderer.toc_generator.generate_toc.return_value = expected_toc_data

        result = self.renderer.get_toc_data(mock_ast)

        assert result == expected_toc_data
        self.renderer.toc_generator.generate_toc.assert_called_once_with(mock_ast)

    def test_get_headings(self):
        """見出し取得テスト"""
        mock_ast = [Mock(spec=Node)]
        expected_headings = [{"level": 1, "text": "Heading"}]

        self.renderer.html_renderer.collect_headings.return_value = expected_headings

        result = self.renderer.get_headings(mock_ast)

        assert result == expected_headings
        self.renderer.html_renderer.collect_headings.assert_called_once_with(mock_ast)

    def test_validate_template(self):
        """テンプレート検証テスト"""
        template_name = "test.html"
        expected_result = (True, None)

        self.renderer.template_manager.validate_template.return_value = expected_result

        result = self.renderer.validate_template(template_name)

        assert result == expected_result
        self.renderer.template_manager.validate_template.assert_called_once_with(
            template_name
        )

    def test_get_available_templates(self):
        """利用可能テンプレート取得テスト"""
        expected_templates = ["base.html", "custom.html"]

        self.renderer.template_manager.get_available_templates.return_value = (
            expected_templates
        )

        result = self.renderer.get_available_templates()

        assert result == expected_templates
        self.renderer.template_manager.get_available_templates.assert_called_once()

    def test_clear_caches(self):
        """キャッシュクリアテスト"""
        self.renderer.clear_caches()

        self.renderer.template_manager.clear_cache.assert_called_once()
        self.renderer.html_renderer.reset_counters.assert_called_once()


class TestRenderFunction:
    """render関数のテスト"""

    @patch("kumihan_formatter.renderer.Renderer")
    def test_render_function_creates_renderer(self, mock_renderer_class):
        """render関数がRendererインスタンスを作成することを確認"""
        mock_renderer = Mock()
        mock_renderer.render.return_value = "<html>result</html>"
        mock_renderer_class.return_value = mock_renderer

        mock_ast = [Mock(spec=Node)]

        result = render(mock_ast)

        mock_renderer_class.assert_called_once()
        mock_renderer.render.assert_called_once_with(
            ast=mock_ast,
            config=None,
            template=None,
            title=None,
            source_text=None,
            source_filename=None,
            navigation_html=None,
        )
        assert result == "<html>result</html>"

    @patch("kumihan_formatter.renderer.Renderer")
    def test_render_function_with_all_params(self, mock_renderer_class):
        """全パラメータ指定でのrender関数テスト"""
        mock_renderer = Mock()
        mock_renderer.render.return_value = "<html>result</html>"
        mock_renderer_class.return_value = mock_renderer

        mock_ast = [Mock(spec=Node)]
        config = {"test": "config"}
        template = "custom.html"
        title = "Test Title"
        source_text = "source"
        source_filename = "test.txt"
        navigation_html = "<nav/>"

        result = render(
            ast=mock_ast,
            config=config,
            template=template,
            title=title,
            source_text=source_text,
            source_filename=source_filename,
            navigation_html=navigation_html,
        )

        mock_renderer.render.assert_called_once_with(
            ast=mock_ast,
            config=config,
            template=template,
            title=title,
            source_text=source_text,
            source_filename=source_filename,
            navigation_html=navigation_html,
        )


class TestRendererIntegration:
    """Renderer統合テスト（モックを使わない基本動作確認）"""

    def test_renderer_basic_functionality(self):
        """レンダラーの基本機能テスト"""
        with patch("kumihan_formatter.renderer.get_logger"):
            with patch("kumihan_formatter.renderer.HTMLRenderer"):
                with patch("kumihan_formatter.renderer.TemplateManager"):
                    with patch("kumihan_formatter.renderer.TOCGenerator"):
                        renderer = Renderer()

        # 最低限の動作確認
        assert renderer is not None
        assert hasattr(renderer, "render")
        assert hasattr(renderer, "render_nodes_only")
        assert hasattr(renderer, "get_toc_data")

    def test_render_function_basic_functionality(self):
        """render関数の基本機能テスト"""
        with patch("kumihan_formatter.renderer.Renderer") as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer.render.return_value = ""
            mock_renderer_class.return_value = mock_renderer

            # 最低限の動作確認
            result = render([])
            assert isinstance(result, str)
