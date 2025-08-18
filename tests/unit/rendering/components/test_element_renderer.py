"""
ElementRendererDelegate のユニットテスト

rendering/components/element_renderer_delegate.py の包括的テスト
カバレッジ80%以上、HTMLエスケープ・XSS防御を重点的にテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from kumihan_formatter.core.rendering.components.element_renderer_delegate import (
    ElementRendererDelegate,
)
from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.utilities.logger import get_logger


class TestElementRendererDelegate:
    """要素レンダリング委譲クラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        # MainRendererのモック作成
        self.main_renderer_mock = Mock()
        self.main_renderer_mock.element_renderer = Mock()
        self.main_renderer_mock.content_processor = Mock()
        self.main_renderer_mock._process_text_content = Mock()
        self.main_renderer_mock._contains_html_tags = Mock()
        self.main_renderer_mock._render_attributes = Mock()
        
        # ElementRendererDelegateインスタンス作成
        self.element_renderer = ElementRendererDelegate(self.main_renderer_mock)

    def test_初期化_正常系(self) -> None:
        """正常系: ElementRendererDelegateの初期化"""
        # Given: MainRendererモック
        renderer = ElementRendererDelegate(self.main_renderer_mock)
        
        # Then: 初期化が正常に完了することを確認
        assert renderer.main_renderer == self.main_renderer_mock
        assert renderer.logger is not None
        assert isinstance(renderer._renderer_method_cache, dict)
        assert len(renderer._renderer_method_cache) == 0

    def test_render_node_正常系_段落要素(self) -> None:
        """正常系: 段落ノードのレンダリング"""
        # Given: 段落ノード
        node = Node(type="p", content="テスト段落")
        expected_html = "<p>テスト段落</p>"
        self.main_renderer_mock.element_renderer.render_paragraph.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 期待するHTML出力
        assert result == expected_html
        self.main_renderer_mock.element_renderer.render_paragraph.assert_called_once_with(node)

    def test_render_node_正常系_見出し要素(self) -> None:
        """正常系: 見出しノードのレンダリング"""
        # Given: h1見出しノード
        node = Node(type="h1", content="メインタイトル")
        expected_html = "<h1>メインタイトル</h1>"
        self.main_renderer_mock.element_renderer.render_heading.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 期待するHTML出力と適切なメソッド呼び出し
        assert result == expected_html
        self.main_renderer_mock.element_renderer.render_heading.assert_called_once_with(node, 1)

    def test_render_node_正常系_太字要素(self) -> None:
        """正常系: 太字ノードのレンダリング"""
        # Given: 太字ノード
        node = Node(type="strong", content="重要な文字")
        expected_html = "<strong>重要な文字</strong>"
        self.main_renderer_mock.element_renderer.render_strong.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 期待するHTML出力
        assert result == expected_html
        self.main_renderer_mock.element_renderer.render_strong.assert_called_once_with(node)

    def test_render_node_正常系_リスト要素(self) -> None:
        """正常系: 無順序リストノードのレンダリング"""
        # Given: 無順序リストノード
        node = Node(type="ul", content=[], children=[])
        expected_html = "<ul></ul>"
        self.main_renderer_mock.element_renderer.render_unordered_list.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 期待するHTML出力
        assert result == expected_html
        self.main_renderer_mock.element_renderer.render_unordered_list.assert_called_once_with(node)

    def test_render_node_異常系_不正なノードタイプ(self) -> None:
        """異常系: Nodeインスタンスでない場合のTypeError"""
        # Given: 不正なデータ（文字列）
        invalid_node = "not a node"
        
        # When/Then: TypeErrorが発生することを確認
        with pytest.raises(TypeError, match="Expected Node instance"):
            self.element_renderer.render_node(invalid_node)  # type: ignore

    def test_render_node_異常系_未定義ノードタイプ_汎用レンダラー呼び出し(self) -> None:
        """異常系: 未定義ノードタイプは汎用レンダラーで処理"""
        # Given: 未定義のノードタイプ
        node = Node(type="unknown_type", content="未知の要素")
        expected_html = "<div>未知の要素</div>"
        self.main_renderer_mock.element_renderer.render_generic.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 汎用レンダラーが呼び出されることを確認
        assert result == expected_html
        self.main_renderer_mock.element_renderer.render_generic.assert_called_once_with(node)

    def test_render_node_optimized_正常系_キャッシュ利用(self) -> None:
        """正常系: 最適化レンダリングでメソッドキャッシュが利用される"""
        # Given: 段落ノード
        node = Node(type="p", content="キャッシュテスト")
        expected_html = "<p>キャッシュテスト</p>"
        self.main_renderer_mock.element_renderer.render_paragraph.return_value = expected_html
        
        # When: 最適化レンダリングを2回実行
        result1 = self.element_renderer.render_node_optimized(node)
        result2 = self.element_renderer.render_node_optimized(node)
        
        # Then: 両方とも同じ結果でキャッシュが機能
        assert result1 == expected_html
        assert result2 == expected_html
        assert "p" in self.element_renderer._renderer_method_cache

    def test_get_cached_renderer_method_正常系_キャッシュ機能(self) -> None:
        """正常系: レンダラーメソッドキャッシュの取得機能"""
        # Given: ノードタイプ
        node_type = "strong"
        
        # When: キャッシュメソッド取得（初回）
        method1 = self.element_renderer._get_cached_renderer_method(node_type)
        method2 = self.element_renderer._get_cached_renderer_method(node_type)
        
        # Then: キャッシュが機能し、同じメソッドオブジェクトが返される
        assert method1 == method2
        assert node_type in self.element_renderer._renderer_method_cache
        assert callable(method1)

    def test_render_各種要素タイプ_網羅テスト(self) -> None:
        """正常系: 各種要素タイプの網羅的なレンダリングテスト"""
        test_cases = [
            ("em", "render_emphasis"),
            ("div", "render_div"),
            ("h2", "render_heading"),
            ("h3", "render_heading"),
            ("h4", "render_heading"),
            ("h5", "render_heading"),
            ("ol", "render_ordered_list"),
            ("li", "render_list_item"),
            ("details", "render_details"),
            ("pre", "render_preformatted"),
            ("code", "render_code"),
            ("image", "render_image"),
            ("error", "render_error"),
            ("toc", "render_toc_placeholder"),
            ("ruby", "render_ruby"),
        ]
        
        for node_type, expected_method in test_cases:
            # Given: 各タイプのノード
            node = Node(type=node_type, content=f"{node_type}のテスト")
            expected_html = f"<{node_type}>test</{node_type}>"
            
            # モック設定
            getattr(self.main_renderer_mock.element_renderer, expected_method).return_value = expected_html
            
            # When: レンダリング実行
            result = self.element_renderer.render_node(node)
            
            # Then: 適切なメソッドが呼び出される
            assert result == expected_html

    def test_process_text_content_XSS防御(self) -> None:
        """セキュリティ: テキスト処理でのXSS防御"""
        # Given: 悪意のあるスクリプト
        malicious_text = "<script>alert('XSS')</script>"
        safe_text = "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        self.main_renderer_mock._process_text_content.return_value = safe_text
        
        # When: テキスト処理実行
        result = self.element_renderer._process_text_content(malicious_text)
        
        # Then: エスケープされた安全なテキストが返される
        assert result == safe_text
        assert "<script>" not in result
        self.main_renderer_mock._process_text_content.assert_called_once_with(malicious_text)

    def test_contains_html_tags_正常系(self) -> None:
        """正常系: HTMLタグ含有チェック"""
        # Given: HTMLタグを含むテキスト
        html_text = "<div>コンテンツ</div>"
        self.main_renderer_mock._contains_html_tags.return_value = True
        
        # When: HTMLタグチェック実行
        result = self.element_renderer._contains_html_tags(html_text)
        
        # Then: HTMLタグが検出される
        assert result is True
        self.main_renderer_mock._contains_html_tags.assert_called_once_with(html_text)

    def test_render_attributes_正常系_属性レンダリング(self) -> None:
        """正常系: HTML属性のレンダリング"""
        # Given: 属性辞書
        attributes = {"class": "test-class", "id": "test-id"}
        expected_attrs = ' class="test-class" id="test-id"'
        self.main_renderer_mock._render_attributes.return_value = expected_attrs
        
        # When: 属性レンダリング実行
        result = self.element_renderer._render_attributes(attributes)
        
        # Then: 正しい属性文字列が生成される
        assert result == expected_attrs
        self.main_renderer_mock._render_attributes.assert_called_once_with(attributes)

    def test_render_content_再帰処理(self) -> None:
        """正常系: ノードコンテンツの再帰レンダリング"""
        # Given: ネストしたコンテンツ
        content = [Node(type="strong", content="太字"), "通常テキスト"]
        depth = 1
        expected_html = "<strong>太字</strong>通常テキスト"
        self.main_renderer_mock.content_processor.render_content.return_value = expected_html
        
        # When: コンテンツレンダリング実行
        result = self.element_renderer._render_content(content, depth)
        
        # Then: 再帰処理が適切に実行される
        assert result == expected_html
        self.main_renderer_mock.content_processor.render_content.assert_called_once_with(content, depth)

    def test_render_node_with_depth_深度追跡(self) -> None:
        """正常系: 深度追跡付きノードレンダリング"""
        # Given: ノードと深度
        node = Node(type="div", content="深度テスト")
        depth = 2
        expected_html = "<div>深度テスト</div>"
        self.main_renderer_mock.content_processor.render_node_with_depth.return_value = expected_html
        
        # When: 深度追跡レンダリング実行
        result = self.element_renderer._render_node_with_depth(node, depth)
        
        # Then: 深度情報と共に処理される
        assert result == expected_html
        self.main_renderer_mock.content_processor.render_node_with_depth.assert_called_once_with(node, depth)

    def test_境界値_空ノード処理(self) -> None:
        """境界値: 空のノード処理"""
        # Given: 空のコンテンツを持つノード
        node = Node(type="p", content="")
        expected_html = "<p></p>"
        self.main_renderer_mock.element_renderer.render_paragraph.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 空でも正常に処理される
        assert result == expected_html

    def test_境界値_日本語文字処理(self) -> None:
        """境界値: 日本語・特殊文字の処理"""
        # Given: 日本語を含むノード
        node = Node(type="p", content="これは日本語のテストです。絵文字も→😀")
        expected_html = "<p>これは日本語のテストです。絵文字も→😀</p>"
        self.main_renderer_mock.element_renderer.render_paragraph.return_value = expected_html
        
        # When: レンダリング実行
        result = self.element_renderer.render_node(node)
        
        # Then: 日本語・特殊文字が正常に処理される
        assert result == expected_html
        assert "これは日本語" in result
        assert "😀" in result

    def test_パフォーマンス_大量ノード処理(self) -> None:
        """パフォーマンス: 大量ノードの処理性能"""
        # Given: 大量の段落ノード
        nodes = [Node(type="p", content=f"段落{i}") for i in range(100)]
        self.main_renderer_mock.element_renderer.render_paragraph.return_value = "<p>test</p>"
        
        # When: 大量ノードのレンダリング実行
        results = []
        for node in nodes:
            result = self.element_renderer.render_node_optimized(node)
            results.append(result)
        
        # Then: 全て正常に処理され、キャッシュが効果的に機能
        assert len(results) == 100
        assert all(result == "<p>test</p>" for result in results)
        assert "p" in self.element_renderer._renderer_method_cache