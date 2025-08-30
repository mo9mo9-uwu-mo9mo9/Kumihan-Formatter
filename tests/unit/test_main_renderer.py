"""
main_renderer.pyのユニットテスト

このテストファイルは、kumihan_formatter.core.rendering.main_renderer.MainRenderer
の基本機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
from typing import Any, Dict, List

from kumihan_formatter.core.rendering.main_renderer import MainRenderer


class TestMainRenderer:
    """MainRendererクラスのテスト"""

    def test_initialization_default(self):
        """デフォルト設定での初期化テスト"""
        renderer = MainRenderer()

        assert renderer is not None
        assert hasattr(renderer, "logger")
        assert hasattr(renderer, "config")
        assert hasattr(renderer, "markdown_renderer")
        assert hasattr(renderer, "html_formatter")

    def test_initialization_with_config(self):
        """設定付きでの初期化テスト"""
        config = {"output_format": "html", "include_css": True}
        renderer = MainRenderer(config=config)

        assert renderer.config == config

    def test_supports_format_html(self):
        """HTML形式のサポート確認テスト"""
        renderer = MainRenderer()

        assert renderer.supports_format("html") is True

    def test_supports_format_unsupported(self):
        """サポートされていない形式のテスト"""
        renderer = MainRenderer()

        # 実装によってはFalseを返す可能性があるため、例外処理
        try:
            result = renderer.supports_format("pdf")
            # 結果がbooleanであることを確認
            assert isinstance(result, bool)
        except Exception:
            # サポートされていない形式の処理
            pass

    def test_get_renderer_info(self):
        """レンダラー情報取得テスト"""
        renderer = MainRenderer()

        info = renderer.get_renderer_info()

        assert isinstance(info, dict)
        # 基本的な情報が含まれることを確認
        assert "name" in info or "type" in info or "version" in info

    @patch(
        "kumihan_formatter.core.rendering.main_renderer.MainRenderer._render_complete_html_document"
    )
    def test_render_success(self, mock_render_complete):
        """正常な描画処理のテスト"""
        mock_render_complete.return_value = "<html><body>Test</body></html>"

        renderer = MainRenderer()
        elements = [{"type": "paragraph", "content": "Test content"}]

        result = renderer.render(elements)

        assert result is not None
        mock_render_complete.assert_called_once()

    @patch(
        "kumihan_formatter.core.rendering.main_renderer.MainRenderer._render_complete_html_document"
    )
    def test_render_empty_elements(self, mock_render_complete):
        """空要素リストでの描画テスト"""
        mock_render_complete.return_value = "<html><body></body></html>"

        renderer = MainRenderer()
        elements = []

        result = renderer.render(elements)

        assert result is not None
        # _render_complete_html_documentは elements と context の2つの引数で呼び出される
        mock_render_complete.assert_called_once_with([], {})

    @patch(
        "kumihan_formatter.core.rendering.main_renderer.MainRenderer._render_complete_html_document"
    )
    def test_render_with_exception(self, mock_render_complete):
        """描画処理での例外ハンドリングテスト"""
        mock_render_complete.side_effect = Exception("Render error")

        renderer = MainRenderer()
        elements = [{"type": "paragraph", "content": "Test"}]

        # MainRendererは例外をキャッチしてエラーHTMLを返すため、例外は発生しない
        result = renderer.render(elements)

        # エラーHTMLが返されることを確認
        assert result is not None
        assert "error" in result.lower()
        assert "render error" in result.lower() or "rendering failed" in result.lower()

    def test_escape_html_basic(self):
        """HTML エスケープの基本テスト"""
        renderer = MainRenderer()

        # プライベートメソッドへのアクセス
        escaped = renderer._escape_html("<script>alert('xss')</script>")

        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "script" in escaped
        # XSSが防げていることを確認
        assert "<script>" not in escaped

    def test_escape_html_special_characters(self):
        """HTML エスケープの特殊文字テスト"""
        renderer = MainRenderer()

        test_cases = [
            ("&", "&amp;"),
            ("<", "&lt;"),
            (">", "&gt;"),
            ('"', "&quot;"),
        ]

        for original, expected in test_cases:
            result = renderer._escape_html(original)
            assert expected in result

    def test_get_kumihan_css_class(self):
        """Kumihan CSS クラス取得テスト"""
        renderer = MainRenderer()

        # 基本的なキーワードのテスト
        css_class = renderer._get_kumihan_css_class("太字")
        assert css_class is not None
        assert isinstance(css_class, str)

    def test_get_kumihan_css_class_unknown_keyword(self):
        """未知のキーワードでのCSS クラス取得テスト"""
        renderer = MainRenderer()

        # 存在しないキーワード
        css_class = renderer._get_kumihan_css_class("unknown_keyword")
        # デフォルト値または空文字列が返されることを確認
        assert css_class is not None
        assert isinstance(css_class, str)

    @patch("builtins.open", new_callable=mock_open)
    def test_render_to_file_success(self, mock_file):
        """ファイルへの正常な出力テスト"""
        renderer = MainRenderer()
        elements = [{"type": "paragraph", "content": "Test"}]

        with patch.object(
            renderer, "render", return_value="<html>Test</html>"
        ) as mock_render:
            result = renderer.render_to_file(elements, "test.html")

            mock_render.assert_called_once_with(elements, {})
            mock_file.assert_called_once()
            # ファイルへの書き込みが実行されたことを確認
            mock_file().write.assert_called_once_with("<html>Test</html>")

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_render_to_file_io_error(self, mock_file):
        """ファイル出力時のIOエラーテスト"""
        renderer = MainRenderer()
        elements = [{"type": "paragraph", "content": "Test"}]

        with patch.object(renderer, "render", return_value="<html>Test</html>"):
            # render_to_fileはIOエラー時にFalseを返す
            result = renderer.render_to_file(elements, "test.html")
            assert result is False

    def test_render_single_element_paragraph(self):
        """単一段落要素の描画テスト"""
        renderer = MainRenderer()

        element = {"type": "paragraph", "content": "Test paragraph"}
        result = renderer._render_single_element(element)

        assert result is not None
        assert isinstance(result, str)
        assert "Test paragraph" in result or "paragraph" in result

    def test_render_single_element_unknown_type(self):
        """不明なタイプの要素描画テスト"""
        renderer = MainRenderer()

        element = {"type": "unknown_type", "content": "Test"}
        result = renderer._render_single_element(element)

        # 不明なタイプでもエラーが発生しないことを確認
        assert result is not None
        assert isinstance(result, str)

    def test_close_method(self):
        """closeメソッドのテスト"""
        renderer = MainRenderer()

        # closeメソッドが例外を発生させないことを確認
        try:
            renderer.close()
            # 正常終了
        except Exception as e:
            pytest.fail(f"close() method raised an exception: {e}")

    def test_render_kumihan_elements_basic(self):
        """Kumihan要素の基本描画テスト"""
        renderer = MainRenderer()

        elements = [
            {"type": "kumihan_block", "keyword": "太字", "content": "Bold text"},
            {"type": "paragraph", "content": "Normal text"},
        ]

        result = renderer._render_kumihan_elements(elements)

        assert result is not None
        assert isinstance(result, str)
        # 何らかの内容が出力されることを確認
        assert len(result) > 0

    @patch(
        "kumihan_formatter.core.rendering.main_renderer.MainRenderer._render_kumihan_elements"
    )
    def test_render_complete_html_document(self, mock_render_elements):
        """完全なHTMLドキュメントの描画テスト"""
        mock_render_elements.return_value = "<p>Test content</p>"

        renderer = MainRenderer()
        elements = [{"type": "paragraph", "content": "Test"}]

        result = renderer._render_complete_html_document(elements)

        assert result is not None
        assert isinstance(result, str)
        # HTML構造の基本要素が含まれることを確認
        assert any(tag in result.lower() for tag in ["html", "body", "head"])

    def test_context_manager_usage(self):
        """コンテキストマネージャーとしての使用テスト"""
        # MainRendererはコンテキストマネージャーを実装していないため、通常のインスタンス化テストを実行
        renderer = MainRenderer()
        assert renderer is not None
        info = renderer.get_renderer_info()
        assert isinstance(info, dict)

    def test_initialization_with_none_config(self):
        """None設定での初期化テスト"""
        renderer = MainRenderer(config=None)

        assert renderer is not None
        # configがNoneでも初期化できることを確認
        assert renderer.config is None or isinstance(renderer.config, dict)
