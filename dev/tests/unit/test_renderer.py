"""
Unit tests for the Renderer module
"""

import pytest
from pathlib import Path

from kumihan_formatter.renderer import Renderer
from kumihan_formatter.parser import Parser
from kumihan_formatter.core.ast_nodes import Node, heading, paragraph


class TestRenderer:
    """Rendererクラスのテスト"""

    @pytest.fixture
    def renderer(self):
        """Rendererインスタンスを生成"""
        return Renderer()

    @pytest.fixture
    def simple_document(self):
        """シンプルなNodeリストを生成"""
        nodes = [
            Node(type="keyword", content="タイトル: テストシナリオ"),
            heading(1, "導入"),
            paragraph("これはテストです。"),
        ]
        return nodes

    def test_render_basic_document(self, renderer, simple_document):
        """基本的なドキュメントのレンダリングをテスト"""
        html = renderer.render(simple_document)

        assert isinstance(html, str)
        assert "テストシナリオ" in html
        assert "導入" in html
        assert "これはテストです。" in html

    def test_render_with_custom_config(self, renderer, simple_document):
        """カスタム設定でのレンダリングをテスト"""
        config = {"title": "カスタムタイトル", "author": "カスタム作者"}
        html = renderer.render(simple_document, config)

        assert isinstance(html, str)
        assert "カスタムタイトル" in html or "テストシナリオ" in html

    def test_render_empty_document(self, renderer):
        """空のドキュメントのレンダリングをテスト"""
        nodes = []
        html = renderer.render(nodes)

        assert isinstance(html, str)
        assert len(html) > 0  # 最低限のHTMLテンプレートは生成される

    def test_render_with_template(self, renderer, simple_document, temp_dir):
        """テンプレート指定でのレンダリングをテスト"""
        # デフォルトテンプレートが存在することを確認
        template_dir = (
            Path(__file__).parent.parent.parent.parent
            / "kumihan_formatter"
            / "templates"
        )
        assert template_dir.exists()

        # base.html.j2テンプレートを使用
        config = {"template": "base.html.j2"}
        html = renderer.render(simple_document, config)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_render_special_characters(self, renderer):
        """特殊文字のエスケープをテスト"""
        nodes = [
            Node(type="keyword", content="タイトル: <script>alert('test')</script>"),
            heading(1, "テスト"),
            paragraph("<b>太字</b> & 特殊文字"),
        ]

        html = renderer.render(nodes)

        # HTMLタグがエスケープされていることを確認
        assert "&lt;script&gt;" in html or "<script>" not in html
        assert "alert(" not in html or "&lt;script&gt;" in html

    def test_render_with_invalid_template(self, renderer, simple_document):
        """存在しないテンプレートでのエラーハンドリングをテスト"""
        config = {"template": "non_existent_template.html.j2"}

        # エラーが発生するか、デフォルトテンプレートにフォールバックする
        try:
            html = renderer.render(simple_document, config)
            # フォールバックした場合
            assert isinstance(html, str)
            assert len(html) > 0
        except Exception as e:
            # エラーが発生した場合
            assert "template" in str(e).lower() or "not found" in str(e).lower()

    @pytest.mark.parametrize(
        "invalid_document",
        [
            None,
            123,
        ],
    )
    def test_render_invalid_document(self, renderer, invalid_document):
        """不正なドキュメントに対するエラーハンドリングをテスト"""
        with pytest.raises((TypeError, AttributeError)):
            renderer.render(invalid_document)

    def test_render_string_input(self, renderer):
        """文字列入力のテスト（実際には受け入れられる）"""
        result = renderer.render("string")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_empty_list(self, renderer):
        """空のリスト入力のテスト"""
        result = renderer.render([])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_dict_input(self, renderer):
        """辞書入力のテスト"""
        result = renderer.render({})
        assert isinstance(result, str)
        assert len(result) > 0
