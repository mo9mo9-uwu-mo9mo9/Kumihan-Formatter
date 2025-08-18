"""
ContentProcessorDelegate のユニットテスト

rendering/components/content_processor_delegate.py の包括的テスト
最適化されたレンダリング・エラー処理のテストを重点実装
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from kumihan_formatter.core.rendering.components.content_processor_delegate import (
    ContentProcessorDelegate,
)
from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.utilities.logger import get_logger


class TestContentProcessorDelegate:
    """コンテンツ処理・最適化委譲クラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        # MainRendererのモック作成
        self.main_renderer_mock = Mock()
        self.main_renderer_mock.graceful_errors = []
        self.main_renderer_mock.embed_errors_in_html = False
        self.main_renderer_mock.render_node = Mock()
        self.main_renderer_mock._element_delegate = Mock()
        self.main_renderer_mock._element_delegate.render_node_optimized = Mock()
        
        # ContentProcessorDelegateインスタンス作成
        self.content_processor = ContentProcessorDelegate(self.main_renderer_mock)

    def test_初期化_正常系(self) -> None:
        """正常系: ContentProcessorDelegateの初期化"""
        # Given: MainRendererモック
        processor = ContentProcessorDelegate(self.main_renderer_mock)
        
        # Then: 初期化が正常に完了することを確認
        assert processor.main_renderer == self.main_renderer_mock
        assert processor.logger is not None

    def test_render_nodes_optimized_正常系_エラーなし(self) -> None:
        """正常系: エラーなしの最適化ノードリストレンダリング"""
        # Given: ノードリスト（エラーなし）
        nodes = [
            Node(type="p", content="段落1"),
            Node(type="p", content="段落2"),
            Node(type="h1", content="見出し")
        ]
        self.main_renderer_mock.graceful_errors = []
        self.main_renderer_mock.embed_errors_in_html = False
        self.main_renderer_mock.render_node.side_effect = [
            "<p>段落1</p>",
            "<p>段落2</p>",
            "<h1>見出し</h1>"
        ]
        
        # When: 最適化レンダリング実行
        result = self.content_processor.render_nodes_optimized(nodes)
        
        # Then: 結合されたHTML出力
        expected = "<p>段落1</p>\n<p>段落2</p>\n<h1>見出し</h1>"
        assert result == expected
        assert self.main_renderer_mock.render_node.call_count == 3

    def test_render_nodes_optimized_エラー処理_有効時(self) -> None:
        """正常系: エラー処理有効時は専用メソッド呼び出し"""
        # Given: エラー処理有効な設定
        nodes = [Node(type="p", content="テスト")]
        self.main_renderer_mock.graceful_errors = [Mock()]
        self.main_renderer_mock.embed_errors_in_html = True
        
        # render_nodes_with_errors_optimizedメソッドをモック
        with patch.object(self.content_processor, 'render_nodes_with_errors_optimized') as mock_error_render:
            mock_error_render.return_value = "<div>エラー付きHTML</div>"
            
            # When: 最適化レンダリング実行
            result = self.content_processor.render_nodes_optimized(nodes)
            
            # Then: エラー処理専用メソッドが呼び出される
            assert result == "<div>エラー付きHTML</div>"
            mock_error_render.assert_called_once_with(nodes)

    def test_render_nodes_with_errors_optimized_正常系(self) -> None:
        """正常系: エラー情報埋め込み付きレンダリング"""
        # Given: ノードリストとエラー情報
        nodes = [Node(type="p", content="テスト段落")]
        error_mock = Mock()
        error_mock.severity = "error"
        error_mock.line_number = 1
        error_mock.message = "テストエラー"
        error_mock.suggestion = "修正提案"
        self.main_renderer_mock.graceful_errors = [error_mock]
        self.main_renderer_mock.embed_errors_in_html = True
        self.main_renderer_mock._element_delegate.render_node_optimized.return_value = "<p>テスト段落</p>"
        
        # エラーサマリーとマーカー埋め込みメソッドをモック
        with patch.object(self.content_processor, '_render_error_summary_optimized') as mock_summary, \
             patch.object(self.content_processor, '_embed_error_markers_optimized') as mock_markers:
            mock_summary.return_value = "<div class='error-summary'>エラーサマリー</div>"
            mock_markers.return_value = "<div class='error-summary'>エラーサマリー</div>\n<p>テスト段落</p>"
            
            # When: エラー付きレンダリング実行
            result = self.content_processor.render_nodes_with_errors_optimized(nodes)
            
            # Then: エラー情報が適切に埋め込まれる
            assert "エラーサマリー" in result
            assert "<p>テスト段落</p>" in result
            mock_summary.assert_called_once()
            mock_markers.assert_called_once()

    def test_render_error_summary_optimized_正常系(self) -> None:
        """正常系: 最適化エラーサマリーHTML生成"""
        # Given: エラーリスト
        error1 = Mock()
        error1.severity = "error"
        error2 = Mock()
        error2.severity = "warning"
        self.main_renderer_mock.graceful_errors = [error1, error2]
        
        # _render_single_error_optimizedメソッドをモック
        with patch.object(self.content_processor, '_render_single_error_optimized') as mock_single:
            mock_single.side_effect = [
                '<div class="error-item">エラー1</div>',
                '<div class="error-item">エラー2</div>'
            ]
            
            # When: エラーサマリー生成
            result = self.content_processor._render_error_summary_optimized()
            
            # Then: エラー統計とサマリーが含まれる
            assert "❌ エラー: 1件" in result
            assert "⚠️ 警告: 1件" in result
            assert "📊 合計: 2件" in result
            assert "kumihan-error-summary" in result
            assert "エラー1" in result
            assert "エラー2" in result

    def test_render_error_summary_optimized_エラーなし(self) -> None:
        """境界値: エラーなし時の空文字列返却"""
        # Given: エラーなしの状態
        self.main_renderer_mock.graceful_errors = []
        
        # When: エラーサマリー生成
        result = self.content_processor._render_error_summary_optimized()
        
        # Then: 空文字列が返される
        assert result == ""

    @patch('kumihan_formatter.core.rendering.html_escaping.escape_html')
    def test_render_single_error_optimized_XSS防御(self, mock_escape: Mock) -> None:
        """セキュリティ: 単一エラーレンダリングでのXSS防御"""
        # Given: 悪意のあるスクリプトを含むエラー
        error_mock = Mock()
        error_mock.display_title = "<script>alert('XSS')</script>"
        error_mock.severity = "error"
        error_mock.html_content = "安全なコンテンツ"
        error_mock.line_number = 1
        error_mock.html_class = "test-error"
        
        mock_escape.side_effect = [
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
            "ERROR"
        ]
        
        # When: 単一エラーレンダリング実行
        result = self.content_processor._render_single_error_optimized(error_mock, 1)
        
        # Then: XSSが適切にエスケープされる
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
        assert "安全なコンテンツ" in result
        assert 'class="error-item test-error"' in result
        mock_escape.assert_called()

    def test_embed_error_markers_optimized_正常系(self) -> None:
        """正常系: 最適化エラーマーカー埋め込み"""
        # Given: HTML文字列とエラー情報
        html = "行1\n行2\n行3"
        error_mock = Mock()
        error_mock.line_number = 2
        error_mock.message = "2行目のエラー"
        error_mock.suggestion = "修正してください"
        error_mock.severity = "error"
        self.main_renderer_mock.graceful_errors = [error_mock]
        
        # エラーマーカー作成メソッドをモック
        with patch.object(self.content_processor, '_create_error_marker_optimized') as mock_marker:
            mock_marker.return_value = '<div class="error-marker">エラーマーカー</div>'
            
            # When: エラーマーカー埋め込み実行
            result = self.content_processor._embed_error_markers_optimized(html)
            
            # Then: 指定行にマーカーが埋め込まれる
            lines = result.split('\n')
            assert len(lines) == 4  # 元の3行 + マーカー1行
            assert "エラーマーカー" in result
            mock_marker.assert_called_once_with(error_mock)

    def test_embed_error_markers_optimized_エラーなし(self) -> None:
        """境界値: エラーなし時はHTML未変更"""
        # Given: HTML文字列、エラーなし
        html = "行1\n行2\n行3"
        self.main_renderer_mock.graceful_errors = []
        
        # When: エラーマーカー埋め込み実行
        result = self.content_processor._embed_error_markers_optimized(html)
        
        # Then: 元のHTMLがそのまま返される
        assert result == html

    @patch('kumihan_formatter.core.rendering.html_escaping.escape_html')
    def test_create_error_marker_optimized_XSS防御(self, mock_escape: Mock) -> None:
        """セキュリティ: エラーマーカー作成でのXSS防御"""
        # Given: 悪意のあるスクリプトを含むエラー
        error_mock = Mock()
        error_mock.message = "<script>alert('XSS')</script>"
        error_mock.suggestion = "<img src=x onerror=alert('XSS')>"
        error_mock.severity = "error"
        error_mock.line_number = 1
        error_mock.html_class = "test-error"
        
        # side_effect: message, suggestion の順でエスケープされる
        mock_escape.side_effect = [
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
            "&lt;img src=x onerror=alert('XSS')&gt;"
        ]
        
        # When: エラーマーカー作成実行
        result = self.content_processor._create_error_marker_optimized(error_mock)
        
        # Then: XSSが適切にエスケープされる
        assert "&lt;script&gt;" in result
        assert "&lt;img src=x onerror=alert" in result  # エスケープされた形で含まれる
        assert "<script>" not in result
        assert "❌" in result  # エラーアイコン
        mock_escape.assert_called()

    def test_create_error_marker_optimized_警告タイプ(self) -> None:
        """正常系: 警告タイプエラーマーカーの作成"""
        # Given: 警告エラー
        error_mock = Mock()
        error_mock.message = "警告メッセージ"
        error_mock.suggestion = None
        error_mock.severity = "warning"
        error_mock.line_number = 5
        error_mock.html_class = "warning-class"
        
        with patch('kumihan_formatter.core.rendering.html_escaping.escape_html') as mock_escape:
            mock_escape.return_value = "警告メッセージ"
            
            # When: 警告エラーマーカー作成実行
            result = self.content_processor._create_error_marker_optimized(error_mock)
            
            # Then: 警告アイコンが使用される
            assert "⚠️" in result
            assert "❌" not in result
            assert "警告メッセージ" in result
            assert "error-suggestion" not in result  # 提案なし

    def test_パフォーマンス_大量ノード処理(self) -> None:
        """パフォーマンス: 大量ノードの最適化処理"""
        # Given: 大量ノードリスト
        nodes = [Node(type="p", content=f"段落{i}") for i in range(1000)]
        self.main_renderer_mock.graceful_errors = []
        self.main_renderer_mock.embed_errors_in_html = False
        self.main_renderer_mock.render_node.return_value = "<p>test</p>"
        
        # When: 大量ノード最適化レンダリング実行
        result = self.content_processor.render_nodes_optimized(nodes)
        
        # Then: 効率的に処理され、結果が正しい
        lines = result.split('\n')
        assert len(lines) == 1000
        assert all(line == "<p>test</p>" for line in lines)
        assert self.main_renderer_mock.render_node.call_count == 1000

    def test_境界値_空ノードリスト(self) -> None:
        """境界値: 空ノードリストの処理"""
        # Given: 空のノードリスト
        nodes: List[Node] = []
        self.main_renderer_mock.graceful_errors = []
        self.main_renderer_mock.embed_errors_in_html = False
        
        # When: 空リストレンダリング実行
        result = self.content_processor.render_nodes_optimized(nodes)
        
        # Then: 空文字列が返される
        assert result == ""

    def test_境界値_Noneコンテンツノード(self) -> None:
        """境界値: Noneコンテンツを持つノードの処理"""
        # Given: Noneコンテンツのノード
        nodes = [Node(type="p", content=None)]
        self.main_renderer_mock.graceful_errors = []
        self.main_renderer_mock.embed_errors_in_html = False
        self.main_renderer_mock.render_node.return_value = ""  # 空文字列返却
        
        # When: Noneコンテンツレンダリング実行
        result = self.content_processor.render_nodes_optimized(nodes)
        
        # Then: 適切に処理される
        assert result == ""

    def test_統合_エラー処理フロー全体(self) -> None:
        """統合: エラー処理フロー全体のテスト"""
        # Given: ノードとエラーの完全なセットアップ
        nodes = [
            Node(type="p", content="正常段落"),
            Node(type="h1", content="エラー見出し")
        ]
        
        error1 = Mock()
        error1.severity = "error"
        error1.line_number = 1
        error1.message = "構文エラー"
        error1.suggestion = "修正してください"
        error1.display_title = "構文エラー"
        error1.html_content = "エラー詳細"
        error1.html_class = "syntax-error"
        
        error2 = Mock()
        error2.severity = "warning"
        error2.line_number = 2
        error2.message = "警告"
        error2.suggestion = None
        error2.display_title = "警告"
        error2.html_content = "警告詳細"
        error2.html_class = "warning"
        
        self.main_renderer_mock.graceful_errors = [error1, error2]
        self.main_renderer_mock.embed_errors_in_html = True
        self.main_renderer_mock._element_delegate.render_node_optimized.side_effect = [
            "<p>正常段落</p>",
            "<h1>エラー見出し</h1>"
        ]
        
        # When: 統合エラー処理実行
        with patch('kumihan_formatter.core.rendering.html_escaping.escape_html') as mock_escape:
            mock_escape.side_effect = lambda x: x.replace('<', '&lt;').replace('>', '&gt;')
            result = self.content_processor.render_nodes_with_errors_optimized(nodes)
        
        # Then: エラーサマリーとマーカーが適切に埋め込まれる
        assert "kumihan-error-summary" in result
        assert "❌ エラー: 1件" in result
        assert "⚠️ 警告: 1件" in result
        assert "<p>正常段落</p>" in result
        assert "<h1>エラー見出し</h1>" in result