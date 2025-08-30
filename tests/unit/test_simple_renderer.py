"""
SimpleHTMLRenderer テスト
"""

import pytest
from kumihan_formatter.core.rendering.main_renderer import MainRenderer


class TestSimpleHTMLRenderer:
    """SimpleHTMLRenderer テストクラス"""

    def setup_method(self):
        self.renderer = MainRenderer()

    def test_render_success_result(self):
        """正常な解析結果のレンダリングテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "kumihan_block",
                    "content": "重要な情報",
                    "attributes": {"decoration": "重要"},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)

        assert "<!DOCTYPE html>" in html
        assert '<html lang="ja">' in html
        assert "重要な情報" in html
        assert "kumihan-block" in html
        assert "important" in html

    def test_render_heading(self):
        """見出しのレンダリングテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "heading_2",
                    "content": "見出し2",
                    "attributes": {"level": "2"},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert '<h2 class="heading-2">見出し2</h2>' in html

    def test_render_paragraph(self):
        """段落のレンダリングテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "paragraph",
                    "content": "段落のテキスト",
                    "attributes": {},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert '<p class="paragraph">段落のテキスト</p>' in html

    def test_render_list_items(self):
        """リストアイテムのレンダリングテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "list_item",
                    "content": "リスト項目",
                    "attributes": {"list_type": "unordered"},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert '<ul class="list-unordered"><li>リスト項目</li></ul>' in html

    def test_render_kumihan_block_decorations(self):
        """Kumihanブロックの装飾テスト"""
        decorations = [
            ("重要", "important"),
            ("注意", "warning"),
            ("情報", "info"),
            ("その他", "default"),
        ]

        for decoration, expected_class in decorations:
            parsed_data = {
                "status": "success",
                "elements": [
                    {
                        "type": "kumihan_block",
                        "content": f"{decoration}な内容",
                        "attributes": {"decoration": decoration},
                        "children": [],
                    }
                ],
            }

            html = self.renderer.render_simple_parsed_data(parsed_data)
            assert f"kumihan-block {expected_class}" in html

    def test_html_escaping(self):
        """HTMLエスケープのテスト"""
        test_text = "<script>alert('xss')</script>"
        escaped = self.renderer._escape_html(test_text)

        assert "&lt;script&gt;" in escaped
        assert "alert(&#39;xss&#39;)" in escaped
        assert "<script>" not in escaped

    def test_render_error_result(self):
        """エラー結果のレンダリングテスト"""
        parsed_data = {"status": "error", "error": "テストエラー"}

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert "エラーが発生しました" in html
        assert "テストエラー" in html
        assert "error" in html  # CSSクラス

    def test_render_empty_result(self):
        """空の結果のレンダリングテスト"""
        parsed_data = {"status": "success", "elements": []}

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert "空の文書" in html

    def test_render_unknown_element(self):
        """不明な要素タイプのレンダリングテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "unknown_type",
                    "content": "不明な要素",
                    "attributes": {},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)
        # 不明な要素は段落として処理される
        assert '<p class="paragraph">不明な要素</p>' in html

    def test_css_styles_included(self):
        """CSSスタイルが含まれているテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "paragraph",
                    "content": "テスト",
                    "attributes": {},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)
        assert "<style>" in html
        assert ".kumihan-block" in html
        assert "font-family" in html

    def test_document_structure(self):
        """HTML文書構造のテスト"""
        parsed_data = {
            "status": "success",
            "elements": [
                {
                    "type": "paragraph",
                    "content": "テスト",
                    "attributes": {},
                    "children": [],
                }
            ],
        }

        html = self.renderer.render_simple_parsed_data(parsed_data)

        # 基本的なHTML文書構造
        assert "<!DOCTYPE html>" in html
        assert '<html lang="ja">' in html
        assert "<head>" in html
        assert '<meta charset="UTF-8">' in html
        assert "<title>Kumihan-Formatter 出力</title>" in html
        assert "<body>" in html
        assert '<div class="container">' in html
        assert '<header class="header">' in html
        assert '<main class="content">' in html
        assert '<footer class="footer">' in html

    def test_render_exception_handling(self):
        """レンダリング例外処理のテスト"""
        import unittest.mock as mock

        # 正常なparsedResult構造
        parsed_result = {
            "status": "success",
            "elements": [
                {
                    "type": "paragraph",
                    "content": "テスト",
                    "attributes": {},
                    "children": [],
                }
            ],
        }

        # _render_simple_elementsでエラーを発生させる
        with mock.patch.object(
            self.renderer, "_render_simple_elements", side_effect=Exception("Rendering error")
        ):
            result = self.renderer.render_simple_parsed_data(parsed_result)

        # エラーページが返されることを確認（実際の日本語エラーメッセージを使用）
        assert "エラーが発生しました" in result
        assert "Rendering error" in result
        assert "<!DOCTYPE html>" in result
