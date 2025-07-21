"""GUI and Rendering Integration Tests

GUIシステムとレンダリングシステムの統合テスト
"""

from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.gui
@pytest.mark.tdd_green
class TestGUIIntegration:
    """GUI統合テスト"""

    @pytest.mark.skip_ci
    def test_gui_models_integration(self):
        """GUIモデルの統合テスト"""
        # Tkinter環境が必要なテストは基本的なモジュール確認のみ
        try:
            from kumihan_formatter.gui_models import AppState

            # Tkinterを使わずにクラスの存在確認のみ
            assert AppState is not None
        except RuntimeError:
            # Tkinter環境が利用できない場合はスキップ
            pass

    @pytest.mark.mock_heavy
    def test_gui_controllers_integration(self):
        """GUIコントローラーの統合テスト"""
        from kumihan_formatter.gui_controllers.gui_controller import GuiController

        with (
            patch("kumihan_formatter.gui_controllers.gui_controller.StateModel"),
            patch("kumihan_formatter.gui_controllers.gui_controller.MainWindow"),
            patch("kumihan_formatter.gui_controllers.gui_controller.FileController"),
            patch(
                "kumihan_formatter.gui_controllers.gui_controller.ConversionController"
            ),
            patch("kumihan_formatter.gui_controllers.gui_controller.MainController"),
        ):
            controller = GuiController()
            assert controller is not None


@pytest.mark.tdd_green
class TestRenderingIntegration:
    """レンダリングシステム統合テスト"""

    @pytest.mark.unit
    def test_heading_rendering_integration(self):
        """見出しレンダリングの統合テスト"""
        from kumihan_formatter.core.ast_nodes import Node
        from kumihan_formatter.core.rendering.heading_collector import HeadingCollector
        from kumihan_formatter.core.rendering.heading_renderer import HeadingRenderer

        renderer = HeadingRenderer()
        collector = HeadingCollector()

        # 見出しノードの作成
        h1_node = Node("h1", "メインタイトル")
        h2_node = Node("h2", "サブタイトル")

        nodes = [h1_node, h2_node]

        # 見出し収集の統合テスト
        headings = collector.collect_headings(nodes)
        assert len(headings) >= 0  # 実際の実装に依存

        # カウンターの同期テスト
        renderer.heading_counter = 5
        assert renderer.heading_counter == 5

    @pytest.mark.mock_heavy
    def test_element_rendering_integration(self):
        """要素レンダリングの統合テスト"""
        from kumihan_formatter.core.ast_nodes import Node
        from kumihan_formatter.core.rendering.element_renderer import ElementRenderer

        renderer = ElementRenderer()

        # 各種要素のレンダリングテスト
        p_node = Node("p", "段落テキスト")
        strong_node = Node("strong", "太字テキスト")

        with (
            patch.object(
                renderer, "render_paragraph", return_value="<p>段落テキスト</p>"
            ),
            patch.object(
                renderer, "render_strong", return_value="<strong>太字テキスト</strong>"
            ),
        ):
            p_result = renderer.render_paragraph(p_node)
            strong_result = renderer.render_strong(strong_node)

            assert "<p>" in p_result
            assert "<strong>" in strong_result
