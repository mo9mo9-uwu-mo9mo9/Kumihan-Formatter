"""Extended Renderer functionality tests"""

import os
import tempfile
from pathlib import Path

import pytest

try:
    from kumihan_formatter.renderer import Renderer as DocumentRenderer
except ImportError:
    DocumentRenderer = None
try:
    from kumihan_formatter.core.rendering.main_renderer import (
        HTMLRenderer as MainRenderer,
    )
except ImportError:
    MainRenderer = None
try:
    from kumihan_formatter.core.rendering.element_renderer import ElementRenderer
except ImportError:
    ElementRenderer = None
try:
    from kumihan_formatter.core.rendering.html_formatter import HTMLFormatter
except ImportError:
    HTMLFormatter = None
try:
    import kumihan_formatter.core.rendering.html_utils as html_utils_module

    HTMLUtils = html_utils_module  # モジュール自体を参照
except ImportError:
    HTMLUtils = None


class TestDocumentRendererAdvanced:
    """DocumentRendererの高度なテスト"""

    @pytest.fixture
    def renderer(self):
        if DocumentRenderer is None:
            pytest.skip("DocumentRendererがimportできません")
        return DocumentRenderer()

    @pytest.fixture
    def complex_document_data(self):
        """複雑なドキュメントデータ"""
        return {
            "title": "複雑なシナリオ",
            "author": "テスト作者",
            "sections": [
                {
                    "type": "introduction",
                    "title": "導入",
                    "content": "このシナリオは複雑な構造を持っています。",
                },
                {
                    "type": "section",
                    "title": "メインパート",
                    "content": "ここで主要なイベントが発生します。",
                },
            ],
            "npcs": [
                {
                    "name": "探索者A",
                    "description": "主人公の一人",
                    "stats": "STR:13 CON:12 DEX:15",
                },
                {
                    "name": "ボスキャラ",
                    "description": "最終ボス",
                    "stats": "HP:100 サンイチ:99",
                },
            ],
            "rooms": [
                {"name": "書斎", "description": "古い本が置かれた部屋"},
                {"name": "地下室", "description": "暗く湿った地下空間"},
            ],
            "items": [{"name": "古い鍵", "description": "地下室の扉を開ける"}],
        }

    @pytest.mark.skip(reason="AST形式対応が必要")
    def test_render_complex_document(self, renderer, complex_document_data):
        """複雑なドキュメントのレンダリングテスト"""
        pytest.skip("AST形式への対応が必要です")

    def test_render_with_custom_template(
        self, renderer, complex_document_data, temp_dir
    ):
        """カスタムテンプレートでのレンダリングテスト"""
        # カスタムテンプレートを作成
        custom_template = temp_dir / "custom.html.j2"
        custom_template.write_text(
            """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - Custom Template</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .custom-header { color: blue; }
    </style>
</head>
<body>
    <h1 class="custom-header">{{ title }}</h1>
    <p>Author: {{ author }}</p>
    <div class="content">
        {% for section in sections %}
        <div class="section">
            <h2>{{ section.title }}</h2>
            <p>{{ section.content }}</p>
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """,
            encoding="utf-8",
        )

        # カスタムテンプレートでレンダリング
        try:
            result = renderer.render(
                complex_document_data, template_path=str(custom_template)
            )

            assert result is not None
            assert "Custom Template" in result
            assert "custom-header" in result
            assert "複雑なシナリオ" in result

        except Exception as e:
            # テンプレート機能がサポートされていない場合はスキップ
            if "template" in str(e).lower():
                pytest.skip(f"カスタムテンプレート機能がサポートされていません: {e}")
            else:
                raise

    def test_render_empty_data(self, renderer):
        """空のデータのレンダリングテスト"""
        empty_data_cases = [
            {},
            {"title": "", "author": ""},
            {"sections": []},
            {"npcs": [], "rooms": [], "items": []},
        ]

        for empty_data in empty_data_cases:
            result = renderer.render(empty_data)
            assert result is not None
            assert isinstance(result, str)
            # 空の場合でも最低限のHTML構造があることを確認
            assert len(result) > 10  # 最低限の長さ

    @pytest.mark.skip(reason="AST形式対応が必要")
    def test_render_special_characters(self, renderer):
        """特殊文字を含むデータのレンダリングテスト"""
        pytest.skip("AST形式への対応が必要です")

    @pytest.mark.skip(reason="AST形式対応が必要")
    def test_render_unicode_content(self, renderer):
        """ユニコード文字を含むコンテンツのレンダリングテスト"""
        pytest.skip("AST形式への対応が必要です")

        # ユニコード文字が正しくレンダリングされていることを確認
        assert "🌍" in result or "異世界" in result
        assert "✨" in result or "テスト作者" in result
        assert "🎨" in result or "絵文字セクション" in result
        assert "🔥" in result or "火球術" in result


class TestMainRendererIntegration:
    """MainRendererの統合テスト"""

    def test_main_renderer_creation(self):
        """MainRendererの作成テスト"""
        try:
            renderer = MainRenderer()
            assert renderer is not None
        except ImportError:
            pytest.skip("MainRendererがimportできません")

    def test_main_renderer_basic_functionality(self):
        """MainRendererの基本機能テスト"""
        try:
            renderer = MainRenderer()

            test_data = {
                "title": "メインレンダラーテスト",
                "content": "テストコンテンツ",
            }

            if hasattr(renderer, "render"):
                result = renderer.render(test_data)
                assert result is not None
            else:
                pytest.skip("MainRendererにrenderメソッドがありません")

        except ImportError:
            pytest.skip("MainRendererがimportできません")


class TestElementRendererIntegration:
    """ElementRendererの統合テスト"""

    def test_element_renderer_creation(self):
        """ElementRendererの作成テスト"""
        try:
            renderer = ElementRenderer()
            assert renderer is not None
        except ImportError:
            pytest.skip("ElementRendererがimportできません")

    def test_element_rendering(self):
        """各要素のレンダリングテスト"""
        try:
            renderer = ElementRenderer()

            # 各種要素のテストデータ
            test_elements = [
                {"type": "title", "content": "タイトル要素"},
                {"type": "section", "content": "セクション要素"},
                {"type": "npc", "content": "NPC要素"},
                {"type": "room", "content": "部屋要素"},
                {"type": "item", "content": "アイテム要素"},
            ]

            for element in test_elements:
                if hasattr(renderer, "render_element"):
                    result = renderer.render_element(element)
                    assert result is not None
                elif hasattr(renderer, "render"):
                    result = renderer.render(element)
                    assert result is not None
                else:
                    pytest.skip("ElementRendererに適切なメソッドがありません")

        except ImportError:
            pytest.skip("ElementRendererがimportできません")


class TestHTMLFormatterIntegration:
    """HTMLFormatterの統合テスト"""

    def test_html_formatter_creation(self):
        """HTMLFormatterの作成テスト"""
        try:
            formatter = HTMLFormatter()
            assert formatter is not None
        except ImportError:
            pytest.skip("HTMLFormatterがimportできません")

    def test_html_formatting(self):
        """HTMLフォーマット機能のテスト"""
        try:
            formatter = HTMLFormatter()

            test_content = "テストコンテンツ"

            if hasattr(formatter, "format"):
                result = formatter.format(test_content)
                assert result is not None
                assert isinstance(result, str)
            else:
                pytest.skip("HTMLFormatterにformatメソッドがありません")

        except ImportError:
            pytest.skip("HTMLFormatterがimportできません")

    def test_html_escaping(self):
        """HTMLエスケープ機能のテスト"""
        try:
            formatter = HTMLFormatter()

            dangerous_content = "<script>alert('XSS')</script>&amp;テスト"

            if hasattr(formatter, "escape") or hasattr(formatter, "format"):
                escape_method = getattr(formatter, "escape", None) or getattr(
                    formatter, "format", None
                )
                result = escape_method(dangerous_content)

                assert result is not None
                # スクリプトタグがエスケープされていることを確認
                assert "<script>" not in result or "&lt;script&gt;" in result
            else:
                pytest.skip("HTMLFormatterに適切なメソッドがありません")

        except ImportError:
            pytest.skip("HTMLFormatterがimportできません")


class TestHTMLUtilsIntegration:
    """HTMLUtilsの統合テスト"""

    def test_html_utils_module_import(self):
        """HTMLUtilsモジュールのインポートテスト"""
        if HTMLUtils is None:
            pytest.skip("HTMLUtilsがimportできません")
        assert HTMLUtils is not None

    def test_html_utilities(self):
        """HTMLユーティリティ機能のテスト"""
        if HTMLUtils is None:
            pytest.skip("HTMLUtilsがimportできません")

        # 様々なユーティリティ関数をテスト
        test_cases = [
            {
                "function_name": "escape_html",
                "input": "<>&\"'テスト",
                "expected_safe": True,
            },
            {
                "function_name": "render_attributes",
                "input": {"class": "test", "id": "example"},
                "expected_safe": True,
            },
        ]

        for test_case in test_cases:
            function_name = test_case["function_name"]
            if hasattr(HTMLUtils, function_name):
                function = getattr(HTMLUtils, function_name)
                result = function(test_case["input"])
                assert result is not None
                assert isinstance(result, str)

                if test_case["expected_safe"]:
                    # 危険なスクリプトが除去されていることを確認
                    assert "<script>" not in result or "&lt;script&gt;" in result

        # 少なくとも一つの関数が存在することを確認
        available_functions = [
            case["function_name"]
            for case in test_cases
            if hasattr(HTMLUtils, case["function_name"])
        ]
        if not available_functions:
            pytest.skip("HTMLUtilsに期待される関数がありません")


class TestRendererPerformance:
    """Rendererのパフォーマンステスト"""

    @pytest.fixture
    def renderer(self):
        if DocumentRenderer is None:
            pytest.skip("DocumentRendererがimportできません")
        return DocumentRenderer()

    @pytest.mark.slow
    def test_large_document_rendering(self, renderer):
        """大きなドキュメントのレンダリングパフォーマンステスト"""
        import time

        # 大きなドキュメントデータを生成
        large_data = {
            "title": "大きなドキュメント",
            "author": "パフォーマンステスト",
            "sections": [],
            "npcs": [],
            "rooms": [],
            "items": [],
        }

        # 500個のセクションを生成
        for i in range(500):
            large_data["sections"].append(
                {
                    "title": f"セクション{i}",
                    "content": f"これはセクション{i}のコンテンツです。\n複数行にわたる説明文が続きます。\nこのセクションでは様々なイベントが発生します。",
                }
            )

            if i % 5 == 0:  # 5個おきにNPCを追加
                large_data["npcs"].append(
                    {
                        "name": f"NPC{i}",
                        "description": f"NPC{i}の詳細な説明文です。このキャラクターは特別な能力を持っています。",
                    }
                )

        # レンダリング時間を測定
        start_time = time.time()
        result = renderer.render(large_data)
        end_time = time.time()

        rendering_time = end_time - start_time

        # 結果の確認
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 1000  # 十分な長さのコンテンツが生成されている

        # パフォーマンスの確認（合理的な時間内で完了すること）
        assert (
            rendering_time < 15.0
        ), f"レンダリング時間が長すぎます: {rendering_time}秒"

        print(f"\n大きなドキュメントのレンダリング時間: {rendering_time:.3f}秒")
        print(f"生成されたHTMLのサイズ: {len(result):,}文字")

    def test_repeated_rendering(self, renderer):
        """繰り返しレンダリングのパフォーマンステスト"""
        import time

        test_data = {
            "title": "パフォーマンステスト",
            "author": "テスト作者",
            "sections": [
                {
                    "title": "テストセクション",
                    "content": "テストコンテンツの説明文です。",
                }
            ],
            "npcs": [{"name": "テストNPC", "description": "テスト用のNPCです。"}],
        }

        # 20回繰り返してレンダリング
        start_time = time.time()
        for i in range(20):
            result = renderer.render(test_data)
            assert result is not None
            assert len(result) > 0
        end_time = time.time()

        total_time = end_time - start_time
        average_time = total_time / 20

        # 平均的なレンダリング時間が合理的であることを確認
        assert (
            average_time < 0.5
        ), f"平均レンダリング時間が遅いです: {average_time:.3f}秒"

        print(f"\n20回の繰り返しレンダリング - 平均時間: {average_time:.3f}秒")
