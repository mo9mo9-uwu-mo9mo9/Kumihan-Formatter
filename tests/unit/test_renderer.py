"""レンダラー機能の包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（レンダラー系 40% → 80%以上）
"""

from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.renderer import Renderer, render


class TestRendererInitialization(TestCase):
    """レンダラーの初期化テスト"""

    def test_renderer_init_default(self) -> None:
        """デフォルト設定でのレンダラー初期化テスト"""
        with patch("kumihan_formatter.renderer.HTMLRenderer") as mock_html:
            with patch("kumihan_formatter.renderer.TemplateManager") as mock_template:
                with patch("kumihan_formatter.renderer.TOCGenerator") as mock_toc:
                    renderer = Renderer()

                    mock_html.assert_called_once()
                    mock_template.assert_called_once_with(None)
                    mock_toc.assert_called_once()

    def test_renderer_init_with_template_dir(self) -> None:
        """テンプレートディレクトリ指定での初期化テスト"""
        template_dir = Path("/test/templates")

        with patch("kumihan_formatter.renderer.HTMLRenderer") as mock_html:
            with patch("kumihan_formatter.renderer.TemplateManager") as mock_template:
                with patch("kumihan_formatter.renderer.TOCGenerator") as mock_toc:
                    renderer = Renderer(template_dir)

                    mock_template.assert_called_once_with(template_dir)

    def test_renderer_logger_initialization(self) -> None:
        """ログ機能の初期化テスト"""
        with patch("kumihan_formatter.renderer.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            renderer = Renderer()

            mock_get_logger.assert_called_once_with("kumihan_formatter.renderer")
            self.assertEqual(renderer.logger, mock_logger)


class TestRendererBasicRendering(TestCase):
    """レンダラーの基本レンダリング機能テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_empty_ast(self) -> None:
        """空ASTのレンダリングテスト"""
        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
                with patch.object(
                    self.renderer.template_manager, "select_template_name"
                ) as mock_select:
                    with patch.object(
                        self.renderer.template_manager, "render_template"
                    ) as mock_template:
                        mock_render.return_value = ""
                        mock_toc.return_value = {"html": "", "has_toc": False}
                        mock_select.return_value = "base.html"
                        mock_template.return_value = "<html></html>"

                        result = self.renderer.render([])

                        self.assertEqual(result, "<html></html>")
                        mock_render.assert_called_once_with([])

    def test_render_single_node(self) -> None:
        """単一ノードのレンダリングテスト"""
        node = Node("paragraph", {"content": "テストテキスト"})

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
                with patch.object(
                    self.renderer.template_manager, "select_template_name"
                ) as mock_select:
                    with patch.object(
                        self.renderer.template_manager, "render_template"
                    ) as mock_template:
                        mock_render.return_value = "<p>テストテキスト</p>"
                        mock_toc.return_value = {"html": "", "has_toc": False}
                        mock_select.return_value = "base.html"
                        mock_template.return_value = (
                            "<html><body><p>テストテキスト</p></body></html>"
                        )

                        result = self.renderer.render([node])

                        self.assertIn("テストテキスト", result)
                        mock_render.assert_called_once_with([node])

    def test_render_with_title(self) -> None:
        """タイトル付きレンダリングテスト"""
        node = Node("paragraph", {"content": "テスト"})
        title = "テストページ"

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
                with patch.object(
                    self.renderer.template_manager, "select_template_name"
                ) as mock_select:
                    with patch.object(
                        self.renderer.template_manager, "render_template"
                    ) as mock_template:
                        mock_render.return_value = "<p>テスト</p>"
                        mock_toc.return_value = {"html": "", "has_toc": False}
                        mock_select.return_value = "base.html"

                        self.renderer.render([node], title=title)

                        # render_templateの呼び出し引数を確認
                        args, kwargs = mock_template.call_args
                        context = (
                            args[1] if len(args) > 1 else kwargs.get("context", {})
                        )
                        self.assertEqual(context.get("title"), title)

    def test_render_with_custom_template(self) -> None:
        """カスタムテンプレートでのレンダリングテスト"""
        node = Node("paragraph", {"content": "テスト"})
        template_name = "custom.html"

        with patch.object(
            self.renderer.template_manager, "select_template_name"
        ) as mock_select:
            with patch.object(
                self.renderer.template_manager, "render_template"
            ) as mock_template:
                mock_select.return_value = template_name
                mock_template.return_value = "<html></html>"

                self.renderer.render([node], template=template_name)

                mock_select.assert_called_once()
                args, kwargs = mock_select.call_args
                self.assertEqual(kwargs.get("template"), template_name)


class TestRendererTOCHandling(TestCase):
    """レンダラーの目次処理テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_with_toc_marker(self) -> None:
        """TOCマーカー付きレンダリングテスト"""
        toc_node = Node("toc", {})
        paragraph_node = Node("paragraph", {"content": "テスト"})
        ast = [toc_node, paragraph_node]

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
                with patch.object(
                    self.renderer.template_manager, "select_template_name"
                ) as mock_select:
                    with patch.object(
                        self.renderer.template_manager, "render_template"
                    ) as mock_template:
                        mock_render.return_value = "<p>テスト</p>"
                        mock_toc.return_value = {
                            "html": "<ul><li>項目</li></ul>",
                            "has_toc": True,
                        }
                        mock_select.return_value = "base.html"

                        self.renderer.render(ast)

                        # TOCマーカーが除外されて段落のみがレンダリングされることを確認
                        mock_render.assert_called_once_with([paragraph_node])

    def test_render_toc_generation(self) -> None:
        """TOC生成のテスト"""
        heading_node = Node("heading", {"content": "見出し", "level": 1})

        with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
            mock_toc.return_value = {
                "html": "<ul><li>見出し</li></ul>",
                "has_toc": True,
            }

            with patch.object(
                self.renderer.template_manager, "render_template"
            ) as mock_template:
                mock_template.return_value = "<html></html>"

                self.renderer.render([heading_node])

                mock_toc.assert_called_once_with([heading_node])

    def test_get_toc_data(self) -> None:
        """TOCデータ取得のテスト"""
        heading_node = Node("heading", {"content": "見出し", "level": 1})
        expected_toc = {"html": "<ul><li>見出し</li></ul>", "has_toc": True}

        with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
            mock_toc.return_value = expected_toc

            result = self.renderer.get_toc_data([heading_node])

            self.assertEqual(result, expected_toc)
            mock_toc.assert_called_once_with([heading_node])


class TestRendererSourceToggle(TestCase):
    """レンダラーのソース表示機能テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_with_source_toggle(self) -> None:
        """ソース表示機能付きレンダリングテスト"""
        node = Node("paragraph", {"content": "テスト"})
        source_text = "元のテキスト"
        source_filename = "test.txt"

        with patch.object(
            self.renderer.template_manager, "render_template"
        ) as mock_template:
            mock_template.return_value = "<html></html>"

            self.renderer.render(
                [node], source_text=source_text, source_filename=source_filename
            )

            # render_templateの呼び出し引数を確認
            args, kwargs = mock_template.call_args
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            self.assertIn("source_text", context)
            self.assertIn("source_filename", context)

    def test_render_without_source_toggle(self) -> None:
        """ソース表示機能なしのレンダリングテスト"""
        node = Node("paragraph", {"content": "テスト"})

        with patch.object(
            self.renderer.template_manager, "render_template"
        ) as mock_template:
            mock_template.return_value = "<html></html>"

            self.renderer.render([node])

            # ソース関連の情報が含まれないことを確認
            args, kwargs = mock_template.call_args
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            self.assertNotIn("source_text", context)
            self.assertNotIn("source_filename", context)


class TestRendererNavigationHandling(TestCase):
    """レンダラーのナビゲーション処理テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_with_navigation(self) -> None:
        """ナビゲーション付きレンダリングテスト"""
        node = Node("paragraph", {"content": "テスト"})
        navigation_html = "<nav><a href='/'>ホーム</a></nav>"

        with patch.object(
            self.renderer.template_manager, "render_template"
        ) as mock_template:
            mock_template.return_value = "<html></html>"

            self.renderer.render([node], navigation_html=navigation_html)

            # ナビゲーションが含まれることを確認
            args, kwargs = mock_template.call_args
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            self.assertIn("navigation_html", context)


class TestRendererAlternativeMethods(TestCase):
    """レンダラーの代替メソッドテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_nodes_only(self) -> None:
        """ノードのみレンダリングテスト"""
        nodes = [
            Node("paragraph", {"content": "テスト1"}),
            Node("paragraph", {"content": "テスト2"}),
        ]

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            mock_render.return_value = "<p>テスト1</p><p>テスト2</p>"

            result = self.renderer.render_nodes_only(nodes)

            self.assertEqual(result, "<p>テスト1</p><p>テスト2</p>")
            mock_render.assert_called_once_with(nodes)

    def test_render_with_custom_context(self) -> None:
        """カスタムコンテキストでのレンダリングテスト"""
        nodes = [Node("paragraph", {"content": "テスト"})]
        template_name = "custom.html"
        custom_context = {"custom_var": "カスタム値"}

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(self.renderer.toc_generator, "generate_toc") as mock_toc:
                with patch.object(
                    self.renderer.template_manager, "render_template"
                ) as mock_template:
                    mock_render.return_value = "<p>テスト</p>"
                    mock_toc.return_value = {"html": "", "has_toc": False}
                    mock_template.return_value = "<html></html>"

                    result = self.renderer.render_with_custom_context(
                        nodes, template_name, custom_context
                    )

                    # カスタムコンテキストが含まれることを確認
                    args, kwargs = mock_template.call_args
                    context = args[1] if len(args) > 1 else kwargs.get("context", {})
                    self.assertEqual(context.get("custom_var"), "カスタム値")

    def test_get_headings(self) -> None:
        """見出し取得のテスト"""
        nodes = [Node("heading", {"content": "見出し1", "level": 1})]
        expected_headings = [{"content": "見出し1", "level": 1}]

        with patch.object(
            self.renderer.html_renderer, "collect_headings"
        ) as mock_collect:
            mock_collect.return_value = expected_headings

            result = self.renderer.get_headings(nodes)

            self.assertEqual(result, expected_headings)
            mock_collect.assert_called_once_with(nodes)


class TestRendererTemplateManagement(TestCase):
    """レンダラーのテンプレート管理テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_validate_template(self) -> None:
        """テンプレート検証のテスト"""
        template_name = "test.html"
        expected_result = (True, None)

        with patch.object(
            self.renderer.template_manager, "validate_template"
        ) as mock_validate:
            mock_validate.return_value = expected_result

            result = self.renderer.validate_template(template_name)

            self.assertEqual(result, expected_result)
            mock_validate.assert_called_once_with(template_name)

    def test_get_available_templates(self) -> None:
        """利用可能テンプレート取得のテスト"""
        expected_templates = ["base.html", "article.html", "book.html"]

        with patch.object(
            self.renderer.template_manager, "get_available_templates"
        ) as mock_get:
            mock_get.return_value = expected_templates

            result = self.renderer.get_available_templates()

            self.assertEqual(result, expected_templates)
            mock_get.assert_called_once()

    def test_clear_caches(self) -> None:
        """キャッシュクリアのテスト"""
        with patch.object(
            self.renderer.template_manager, "clear_cache"
        ) as mock_clear_template:
            with patch.object(
                self.renderer.html_renderer, "reset_counters"
            ) as mock_reset_html:
                self.renderer.clear_caches()

                mock_clear_template.assert_called_once()
                mock_reset_html.assert_called_once()


class TestRendererPerformance(TestCase):
    """レンダラーのパフォーマンステスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_performance_logging(self) -> None:
        """レンダリングパフォーマンスログのテスト"""
        node = Node("paragraph", {"content": "テスト"})

        with patch("kumihan_formatter.renderer.log_performance") as mock_log_perf:
            with patch.object(
                self.renderer.template_manager, "render_template"
            ) as mock_template:
                mock_template.return_value = "<html><p>テスト</p></html>"

                result = self.renderer.render([node])

                # パフォーマンスログが呼ばれることを確認
                mock_log_perf.assert_called_once()
                args, kwargs = mock_log_perf.call_args
                self.assertEqual(args[0], "render")
                self.assertIsInstance(args[1], float)  # duration
                self.assertEqual(args[2], len(result))  # result length


class TestRenderFunction(TestCase):
    """render関数のテスト"""

    def test_render_function_basic(self) -> None:
        """render関数の基本動作テスト"""
        ast = [Node("paragraph", {"content": "テスト"})]

        with patch("kumihan_formatter.renderer.Renderer") as mock_renderer_class:
            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html><p>テスト</p></html>"
            mock_renderer_class.return_value = mock_renderer

            result = render(ast)

            mock_renderer_class.assert_called_once()
            mock_renderer.render.assert_called_once_with(
                ast=ast,
                config=None,
                template=None,
                title=None,
                source_text=None,
                source_filename=None,
                navigation_html=None,
            )
            self.assertEqual(result, "<html><p>テスト</p></html>")

    def test_render_function_with_all_params(self) -> None:
        """全パラメータ付きrender関数のテスト"""
        ast = [Node("paragraph", {"content": "テスト"})]
        config = {"test": "config"}
        template = "custom.html"
        title = "テストタイトル"
        source_text = "元テキスト"
        source_filename = "test.txt"
        navigation_html = "<nav></nav>"

        with patch("kumihan_formatter.renderer.Renderer") as mock_renderer_class:
            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html></html>"
            mock_renderer_class.return_value = mock_renderer

            result = render(
                ast=ast,
                config=config,
                template=template,
                title=title,
                source_text=source_text,
                source_filename=source_filename,
                navigation_html=navigation_html,
            )

            mock_renderer.render.assert_called_once_with(
                ast=ast,
                config=config,
                template=template,
                title=title,
                source_text=source_text,
                source_filename=source_filename,
                navigation_html=navigation_html,
            )

    def test_render_function_compatibility(self) -> None:
        """render関数の互換性テスト"""
        # 実際のRendererクラスを使用して互換性を確認
        ast = [Node("paragraph", {"content": "テスト"})]

        with patch.object(Renderer, "render") as mock_render:
            mock_render.return_value = "<html></html>"

            result = render(ast)

            self.assertEqual(result, "<html></html>")
            mock_render.assert_called_once()


class TestRendererEdgeCases(TestCase):
    """レンダラーのエッジケーステスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.renderer = Renderer()

    def test_render_large_ast(self) -> None:
        """大きなASTのレンダリングテスト"""
        # 大量のノードを作成
        large_ast = [Node("paragraph", {"content": f"段落{i}"}) for i in range(100)]

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(
                self.renderer.template_manager, "render_template"
            ) as mock_template:
                mock_render.return_value = "<p>内容</p>" * 100
                mock_template.return_value = "<html></html>"

                result = self.renderer.render(large_ast)

                # エラーなく処理されることを確認
                self.assertEqual(result, "<html></html>")
                mock_render.assert_called_once_with(large_ast)

    def test_render_with_none_values(self) -> None:
        """None値でのレンダリングテスト"""
        ast = [Node("paragraph", {"content": "テスト"})]

        with patch.object(
            self.renderer.template_manager, "render_template"
        ) as mock_template:
            mock_template.return_value = "<html></html>"

            # None値を明示的に渡してエラーが発生しないことを確認
            result = self.renderer.render(
                ast=ast,
                config=None,
                template=None,
                title=None,
                source_text=None,
                source_filename=None,
                navigation_html=None,
            )

            self.assertEqual(result, "<html></html>")

    def test_render_mixed_node_types(self) -> None:
        """混合ノードタイプのレンダリングテスト"""
        mixed_ast = [
            Node("paragraph", {"content": "段落"}),
            Node("heading", {"content": "見出し", "level": 1}),
            Node("toc", {}),  # TOCマーカー
            Node("list", {"items": ["項目1", "項目2"]}),
        ]

        with patch.object(self.renderer.html_renderer, "render_nodes") as mock_render:
            with patch.object(
                self.renderer.template_manager, "render_template"
            ) as mock_template:
                # TOCマーカーが除外された配列がrender_nodesに渡されることを確認
                mock_render.return_value = "<html>内容</html>"
                mock_template.return_value = "<html></html>"

                self.renderer.render(mixed_ast)

                # render_nodesに渡される引数を確認
                args, kwargs = mock_render.call_args
                filtered_ast = args[0]

                # TOCマーカーが除外されることを確認
                toc_nodes = [node for node in filtered_ast if node.type == "toc"]
                self.assertEqual(len(toc_nodes), 0)
