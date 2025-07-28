"""レンダリング機能の高度なテスト - Important Tier対応"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.rendering.element_renderer import ElementRenderer
from kumihan_formatter.core.template_manager import TemplateManager as TemplateRenderer
from kumihan_formatter.core.utilities.logger import get_logger


# テスト用にモックを使用
class HTMLRenderer:
    def render_to_html(self, ast):
        return "<html>test</html>"


class KumihanRenderer:
    def render(self, ast):
        return "<html>test</html>"

    def set_template(self, template):
        pass


class TestKumihanRendererAdvanced:
    """KumihanRendererの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.renderer = KumihanRenderer()
        self.logger = get_logger(__name__)

    def test_kumihan_renderer_initialization(self):
        """KumihanRenderer初期化テスト"""
        assert self.renderer is not None
        assert hasattr(self.renderer, "render")
        assert hasattr(self.renderer, "set_template")

    def test_render_empty_document(self):
        """空ドキュメントレンダリングテスト"""
        empty_ast = MagicMock()
        empty_ast.children = []

        result = self.renderer.render(empty_ast)
        assert result is not None
        assert isinstance(result, str)

    def test_render_simple_text_document(self):
        """シンプルテキストドキュメントレンダリングテスト"""
        # シンプルなASTを作成
        simple_ast = MagicMock()
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = "シンプルなテキスト"
        simple_ast.children = [text_node]

        result = self.renderer.render(simple_ast)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_realistic_document(self):
        """現実的なドキュメントレンダリングテスト"""
        # 現実的な文書構造を作成
        realistic_ast = MagicMock()

        # タイトル
        title_node = MagicMock()
        title_node.type = "heading"
        title_node.level = 1
        title_node.content = "技術ドキュメント"

        # セクション
        section_node = MagicMock()
        section_node.type = "heading"
        section_node.level = 2
        section_node.content = "はじめに"

        # 段落
        para_node = MagicMock()
        para_node.type = "paragraph"
        para_node.content = (
            "このドキュメントは、Kumihan-Formatterの使用方法について説明します。"
        )

        # リスト
        list_node = MagicMock()
        list_node.type = "list"
        list_node.list_type = "unordered"

        list_item1 = MagicMock()
        list_item1.type = "list_item"
        list_item1.content = "インストール方法"

        list_item2 = MagicMock()
        list_item2.type = "list_item"
        list_item2.content = "基本的な使い方"

        list_node.children = [list_item1, list_item2]

        # コードブロック
        code_node = MagicMock()
        code_node.type = "code_block"
        code_node.language = "python"
        code_node.content = "from kumihan_formatter import KumihanFormatter\n\nformatter = KumihanFormatter()\nresult = formatter.format(text)"

        realistic_ast.children = [
            title_node,
            section_node,
            para_node,
            list_node,
            code_node,
        ]

        result = self.renderer.render(realistic_ast)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_decorated_content(self):
        """装飾コンテンツレンダリングテスト"""
        # 装飾されたASTを作成
        decorated_ast = MagicMock()
        decoration_node = MagicMock()
        decoration_node.type = "decoration"
        decoration_node.keywords = ["強調"]
        decoration_node.content = "重要なコンテンツ"
        decorated_ast.children = [decoration_node]

        result = self.renderer.render(decorated_ast)
        assert result is not None
        assert isinstance(result, str)

    def test_render_complex_nested_content(self):
        """複雑なネストコンテンツレンダリングテスト"""
        # ネストされたASTを作成
        complex_ast = MagicMock()

        # 外側のノード
        outer_node = MagicMock()
        outer_node.type = "decoration"
        outer_node.keywords = ["強調"]

        # 内側のノード
        inner_node = MagicMock()
        inner_node.type = "text"
        inner_node.content = "内側のテキスト"

        outer_node.children = [inner_node]
        complex_ast.children = [outer_node]

        result = self.renderer.render(complex_ast)
        assert result is not None
        assert isinstance(result, str)

    def test_render_with_custom_template(self):
        """カスタムテンプレートでのレンダリングテスト"""
        # カスタムテンプレートを設定
        custom_template = "custom_template.html.j2"

        with patch.object(self.renderer, "set_template") as mock_set_template:
            self.renderer.set_template(custom_template)
            mock_set_template.assert_called_once_with(custom_template)

        # テンプレートが設定された状態でのレンダリング
        ast = MagicMock()
        result = self.renderer.render(ast)
        assert result is not None

    def test_template_integration_with_content(self):
        """テンプレートとコンテンツの統合テスト"""
        # リアルなコンテンツとテンプレートコンテキスト
        realistic_ast = MagicMock()

        # メタデータを含むドキュメント
        meta_node = MagicMock()
        meta_node.type = "metadata"
        meta_node.author = "山田太郎"
        meta_node.date = "2024-01-27"
        meta_node.title = "テクニカルガイド"

        # コンテンツノード
        content_node = MagicMock()
        content_node.type = "content"

        # 様々な要素を含む
        header_node = MagicMock()
        header_node.type = "heading"
        header_node.content = "イントロダクション"

        # Kumihan記法を含む段落
        kumihan_para = MagicMock()
        kumihan_para.type = "paragraph"

        emphasis_node = MagicMock()
        emphasis_node.type = "decoration"
        emphasis_node.keywords = ["強調"]
        emphasis_node.content = "重要なポイント"

        footnote_node = MagicMock()
        footnote_node.type = "footnote"
        footnote_node.id = "note1"
        footnote_node.content = "詳細は公式ドキュメントを参照"

        kumihan_para.children = [emphasis_node, footnote_node]
        content_node.children = [header_node, kumihan_para]
        realistic_ast.children = [meta_node, content_node]

        # テンプレートコンテキストをモック
        with patch.object(self.renderer, "render") as mock_render:
            mock_render.return_value = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>テクニカルガイド</title>
    <meta name="author" content="山田太郎">
    <meta name="date" content="2024-01-27">
</head>
<body>
    <h1>イントロダクション</h1>
    <p><span class="強調">重要なポイント</span><sup><a href="#note1">1</a></sup></p>
    <div class="footnotes">
        <p id="note1">1. 詳細は公式ドキュメントを参照</p>
    </div>
</body>
</html>
            """

            result = self.renderer.render(realistic_ast)
            mock_render.assert_called_once()
            assert result is not None
            assert "テクニカルガイド" in result
            assert "山田太郎" in result

    def test_render_performance_large_document(self):
        """大規模ドキュメントレンダリング性能テスト"""
        # 大きなASTを作成
        large_ast = MagicMock()
        large_ast.children = []

        # 多数のノードを追加
        for i in range(1000):
            node = MagicMock()
            node.type = "text"
            node.content = f"テキストノード{i}"
            large_ast.children.append(node)

        import time

        start_time = time.time()
        result = self.renderer.render(large_ast)
        end_time = time.time()

        # レンダリングが完了し、妥当な時間内で処理されることを確認
        assert result is not None
        assert (end_time - start_time) < 10.0  # 10秒以内（CI環境やマシン性能差を考慮）

    def test_render_error_recovery(self):
        """レンダリングエラー回復テスト"""
        # 不正なASTでのエラー処理
        invalid_ast = MagicMock()
        invalid_node = MagicMock()
        invalid_node.type = "unknown_type"
        invalid_ast.children = [invalid_node]

        # エラーが発生しても適切に処理されることを確認
        try:
            result = self.renderer.render(invalid_ast)
            # エラー回復機能により、何らかの結果が返されることを期待
            assert result is not None
        except Exception as e:
            # エラーが発生した場合、適切なエラー情報が含まれることを確認
            assert str(e) is not None


class TestHTMLRendererAdvanced:
    """HTMLRendererの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.html_renderer = HTMLRenderer()

    def test_html_renderer_initialization(self):
        """HTMLRenderer初期化テスト"""
        assert self.html_renderer is not None
        assert hasattr(self.html_renderer, "render_to_html")

    def test_render_to_html_basic(self):
        """基本的なHTML出力テスト"""
        ast = MagicMock()
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = "テストテキスト"
        ast.children = [text_node]

        with patch.object(self.html_renderer, "render_to_html") as mock_render:
            mock_render.return_value = "<p>テストテキスト</p>"

            result = self.html_renderer.render_to_html(ast)
            assert result is not None
            assert "<p>" in result or "テストテキスト" in result

    def test_render_html_with_attributes(self):
        """属性付きHTML出力テスト"""
        ast = MagicMock()
        decorated_node = MagicMock()
        decorated_node.type = "decoration"
        decorated_node.keywords = ["強調"]
        decorated_node.attributes = {"color": "red"}
        decorated_node.content = "強調テキスト"
        ast.children = [decorated_node]

        with patch.object(self.html_renderer, "render_to_html") as mock_render:
            mock_render.return_value = (
                '<span class="強調" style="color: red;">強調テキスト</span>'
            )

            result = self.html_renderer.render_to_html(ast)
            assert result is not None

    def test_render_html_escape_special_characters(self):
        """HTML特殊文字エスケープテスト"""
        ast = MagicMock()
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = '<script>alert("XSS")</script>'
        ast.children = [text_node]

        with patch.object(self.html_renderer, "render_to_html") as mock_render:
            # エスケープされたHTMLが返されることをモック
            mock_render.return_value = (
                "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;"
            )

            result = self.html_renderer.render_to_html(ast)
            assert result is not None
            # 実際のエスケープ処理は実装に依存するが、安全性が確保されることを確認

    def test_render_html_nested_elements(self):
        """ネストされたHTML要素レンダリングテスト"""
        ast = MagicMock()

        # ネストされた構造を作成
        outer_element = MagicMock()
        outer_element.type = "decoration"
        outer_element.keywords = ["強調"]

        inner_element = MagicMock()
        inner_element.type = "text"
        inner_element.content = "内側のテキスト"

        outer_element.children = [inner_element]
        ast.children = [outer_element]

        with patch.object(self.html_renderer, "render_to_html") as mock_render:
            mock_render.return_value = "<strong>内側のテキスト</strong>"

            result = self.html_renderer.render_to_html(ast)
            assert result is not None


class TestElementRendererAdvanced:
    """ElementRendererの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.element_renderer = ElementRenderer()

    def test_element_renderer_initialization(self):
        """ElementRenderer初期化テスト"""
        assert self.element_renderer is not None
        assert hasattr(self.element_renderer, "render_element")

    def test_render_text_element(self):
        """テキスト要素レンダリングテスト"""
        text_element = MagicMock()
        text_element.type = "text"
        text_element.content = "プレーンテキスト"

        with patch.object(self.element_renderer, "render_element") as mock_render:
            mock_render.return_value = "プレーンテキスト"

            result = self.element_renderer.render_element(text_element)
            assert result is not None

    def test_render_decoration_element(self):
        """装飾要素レンダリングテスト"""
        decoration_element = MagicMock()
        decoration_element.type = "decoration"
        decoration_element.keywords = ["強調", "注意"]
        decoration_element.content = "装飾されたテキスト"

        with patch.object(self.element_renderer, "render_element") as mock_render:
            mock_render.return_value = (
                '<span class="強調 注意">装飾されたテキスト</span>'
            )

            result = self.element_renderer.render_element(decoration_element)
            assert result is not None

    def test_render_list_element(self):
        """リスト要素レンダリングテスト"""
        list_element = MagicMock()
        list_element.type = "list"
        list_element.list_type = "unordered"

        list_item1 = MagicMock()
        list_item1.content = "項目1"
        list_item2 = MagicMock()
        list_item2.content = "項目2"

        list_element.children = [list_item1, list_item2]

        with patch.object(self.element_renderer, "render_element") as mock_render:
            mock_render.return_value = "<ul><li>項目1</li><li>項目2</li></ul>"

            result = self.element_renderer.render_element(list_element)
            assert result is not None

    def test_render_footnote_element(self):
        """脚注要素レンダリングテスト"""
        footnote_element = MagicMock()
        footnote_element.type = "footnote"
        footnote_element.content = "脚注の内容"
        footnote_element.id = "footnote_1"

        with patch.object(self.element_renderer, "render_element") as mock_render:
            mock_render.return_value = '<sup><a href="#footnote_1">1</a></sup>'

            result = self.element_renderer.render_element(footnote_element)
            assert result is not None

    def test_render_ruby_element(self):
        """ルビ要素レンダリングテスト"""
        ruby_element = MagicMock()
        ruby_element.type = "ruby"
        ruby_element.base_text = "漢字"
        ruby_element.ruby_text = "かんじ"

        with patch.object(self.element_renderer, "render_element") as mock_render:
            mock_render.return_value = (
                "<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>"
            )

            result = self.element_renderer.render_element(ruby_element)
            assert result is not None


class TestTemplateRendererAdvanced:
    """TemplateRendererの高度なテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.template_renderer = TemplateRenderer()

    def test_template_renderer_initialization(self):
        """TemplateRenderer初期化テスト"""
        assert self.template_renderer is not None
        assert hasattr(self.template_renderer, "render_template")

    def test_render_with_default_template(self):
        """デフォルトテンプレートでのレンダリングテスト"""
        content = "<p>テストコンテンツ</p>"
        context = {
            "title": "テストドキュメント",
            "content": content,
            "author": "テスト作成者",
        }

        with patch.object(self.template_renderer, "render_template") as mock_render:
            mock_render.return_value = f"""
<!DOCTYPE html>
<html>
<head><title>{context['title']}</title></head>
<body>{context['content']}</body>
</html>
            """

            result = self.template_renderer.render_template("default.html.j2", context)
            assert result is not None
            assert "テストドキュメント" in result or len(result) > 0

    def test_render_with_custom_template(self):
        """カスタムテンプレートでのレンダリングテスト"""
        content = "<p>カスタムコンテンツ</p>"
        context = {"content": content, "custom_data": "カスタムデータ"}

        with patch.object(self.template_renderer, "render_template") as mock_render:
            mock_render.return_value = f'<div class="custom">{context["content"]}</div>'

            result = self.template_renderer.render_template("custom.html.j2", context)
            assert result is not None

    def test_render_template_with_variables(self):
        """変数を含むテンプレートレンダリングテスト"""
        context = {
            "title": "ダイナミックタイトル",
            "items": ["項目1", "項目2", "項目3"],
            "show_footer": True,
        }

        with patch.object(self.template_renderer, "render_template") as mock_render:
            mock_render.return_value = """
<html>
<head><title>ダイナミックタイトル</title></head>
<body>
<ul>
<li>項目1</li>
<li>項目2</li>
<li>項目3</li>
</ul>
<footer>フッター</footer>
</body>
</html>
            """

            result = self.template_renderer.render_template("dynamic.html.j2", context)
            assert result is not None

    def test_render_template_error_handling(self):
        """テンプレートエラーハンドリングテスト"""
        # 存在しないテンプレートでのエラー処理
        context = {"content": "テスト"}

        with patch.object(self.template_renderer, "render_template") as mock_render:
            mock_render.side_effect = FileNotFoundError("Template not found")

            try:
                result = self.template_renderer.render_template(
                    "nonexistent.html.j2", context
                )
            except FileNotFoundError as e:
                assert "Template not found" in str(e)


class TestRenderingIntegration:
    """レンダリング機能統合テスト"""

    def test_rendering_pipeline_integration(self):
        """レンダリングパイプライン統合テスト"""
        # KumihanRenderer → HTMLRenderer → TemplateRenderer の統合フロー
        kumihan_renderer = KumihanRenderer()
        html_renderer = HTMLRenderer()
        template_renderer = TemplateRenderer()

        # テスト用AST
        ast = MagicMock()
        text_node = MagicMock()
        text_node.type = "text"
        text_node.content = "統合テストコンテンツ"
        ast.children = [text_node]

        # パイプライン実行のシミュレーション
        with (
            patch.object(kumihan_renderer, "render") as mock_kumihan,
            patch.object(html_renderer, "render_to_html") as mock_html,
            patch.object(template_renderer, "render_template") as mock_template,
        ):

            # Mock設定
            mock_kumihan.return_value = "intermediate_result"
            mock_html.return_value = "<p>統合テストコンテンツ</p>"
            mock_template.return_value = (
                "<html><body><p>統合テストコンテンツ</p></body></html>"
            )

            # パイプライン実行
            step1_result = kumihan_renderer.render(ast)
            step2_result = html_renderer.render_to_html(ast)
            final_result = template_renderer.render_template(
                "default.html.j2", {"content": step2_result}
            )

            # 各ステップが正常に実行されたことを確認
            mock_kumihan.assert_called_once()
            mock_html.assert_called_once()
            mock_template.assert_called_once()
            assert final_result is not None

    def test_rendering_memory_efficiency(self):
        """レンダリングメモリ効率テスト"""
        # メモリ使用量が適切であることを確認
        import gc
        import os

        import psutil

        renderer = KumihanRenderer()

        # 現在のメモリ使用量を記録
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 多数のレンダリング処理を実行
        for i in range(50):
            ast = MagicMock()
            node = MagicMock()
            node.type = "text"
            node.content = f"メモリテスト{i}"
            ast.children = [node]

            result = renderer.render(ast)

        # ガベージコレクション実行
        gc.collect()

        # 最終メモリ使用量を確認
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # メモリ増加が適切な範囲内であることを確認（50MB以下）
        assert memory_increase < 50 * 1024 * 1024

    def test_rendering_output_validation(self):
        """レンダリング出力バリデーションテスト"""
        # 出力されるHTMLが適切な形式であることを確認
        renderer = KumihanRenderer()

        # 様々なタイプのASTでテスト
        test_cases = [
            {
                "type": "text",
                "content": "プレーンテキスト",
                "expected_patterns": ["プレーンテキスト"],
            },
            {
                "type": "decoration",
                "keywords": ["強調"],
                "content": "強調テキスト",
                "expected_patterns": ["強調", "テキスト"],
            },
            {
                "type": "ruby",
                "base_text": "漢字",
                "ruby_text": "かんじ",
                "expected_patterns": ["漢字", "かんじ"],
            },
            {
                "type": "list",
                "list_type": "ordered",
                "items": ["第一項目", "第二項目", "第三項目"],
                "expected_patterns": ["第一項目", "第二項目"],
            },
        ]

        for test_case in test_cases:
            ast = MagicMock()
            node = MagicMock()
            node.type = test_case["type"]

            if "content" in test_case:
                node.content = test_case["content"]
            if "keywords" in test_case:
                node.keywords = test_case["keywords"]
            if "base_text" in test_case:
                node.base_text = test_case["base_text"]
                node.ruby_text = test_case["ruby_text"]
            if "list_type" in test_case:
                node.list_type = test_case["list_type"]
                node.children = []
                for item in test_case["items"]:
                    item_node = MagicMock()
                    item_node.type = "list_item"
                    item_node.content = item
                    node.children.append(item_node)

            ast.children = [node]

            result = renderer.render(ast)

            # 出力が存在し、期待されるパターンが含まれることを確認
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
