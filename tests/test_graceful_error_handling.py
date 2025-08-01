"""
Issue #700: Graceful Error Handling機能のテスト

Phase 1: 基本的なエラー継続処理とHTML埋め込み機能のテスト
"""

import pytest
from pathlib import Path
from kumihan_formatter.core.common.error_base import GracefulSyntaxError
from kumihan_formatter.parser import Parser
from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer


class TestGracefulSyntaxError:
    """GracefulSyntaxErrorデータクラスのテスト"""
    
    def test_graceful_syntax_error_creation(self):
        """GracefulSyntaxErrorの基本的な作成と属性テスト"""
        error = GracefulSyntaxError(
            line_number=5,
            column=10,
            error_type="block_marker_error",
            severity="error",
            message="未完了のブロックマーカー",
            context="# 太字 内容が未完了",
            suggestion="マーカーの最後に # を追加してください",
            file_path="test.txt"
        )
        
        assert error.line_number == 5
        assert error.column == 10
        assert error.error_type == "block_marker_error"
        assert error.severity == "error"
        assert error.message == "未完了のブロックマーカー"
        assert error.context == "# 太字 内容が未完了"
        assert error.suggestion == "マーカーの最後に # を追加してください"
        assert error.file_path == "test.txt"
    
    def test_html_properties(self):
        """HTML表示用プロパティのテスト"""
        error = GracefulSyntaxError(
            line_number=3,
            column=1,
            error_type="syntax_error",
            severity="warning",
            message="記法の警告",
            context="問題のある行"
        )
        
        assert error.html_class == "kumihan-error-warning"
        assert error.display_title == "記法エラー (行 3)"
        assert "<strong>記法の警告</strong>" in error.html_content
        assert "<code>問題のある行</code>" in error.html_content
    
    def test_to_dict_method(self):
        """辞書変換メソッドのテスト"""
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test_error",
            severity="info",
            message="テストメッセージ",
            context="テストコンテキスト",
            suggestion="テスト提案"
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['line_number'] == 1
        assert error_dict['severity'] == "info"
        assert error_dict['html_class'] == "kumihan-error-info"
        assert 'html_content' in error_dict


class TestParserGracefulErrors:
    """Parserのgraceful error handling機能テスト"""
    
    def test_parser_graceful_mode_initialization(self):
        """graceful errorモードでのParser初期化"""
        parser = Parser(graceful_errors=True)
        
        assert parser.graceful_errors is True
        assert parser.graceful_syntax_errors == []
        assert hasattr(parser, '_record_graceful_error')
        assert hasattr(parser, 'get_graceful_errors')
    
    def test_parser_traditional_mode(self):
        """従来モードでのParser動作"""
        parser = Parser(graceful_errors=False)
        
        assert parser.graceful_errors is False
        
        # 正常な記法のテスト
        text = """
# 太字 # 正常なテキスト #

通常のパラグラフ。
"""
        nodes = parser.parse(text.strip())
        assert len(nodes) > 0
        assert not parser.has_graceful_errors()
    
    def test_graceful_error_recording(self):
        """graceful error記録機能のテスト"""
        parser = Parser(graceful_errors=True)
        
        # エラー記録をテスト
        parser._record_graceful_error(
            line_number=2,
            column=5,
            error_type="test_error",
            severity="error",
            message="テストエラー",
            context="テスト行",
            suggestion="テスト修正提案"
        )
        
        assert parser.has_graceful_errors()
        errors = parser.get_graceful_errors()
        assert len(errors) == 1
        assert errors[0].message == "テストエラー"
    
    def test_graceful_error_summary(self):
        """graceful errorサマリー機能のテスト"""
        parser = Parser(graceful_errors=True)
        
        # 複数のエラーを記録
        parser._record_graceful_error(1, 1, "error1", "error", "エラー1", "context1")
        parser._record_graceful_error(2, 1, "error2", "warning", "警告1", "context2")
        parser._record_graceful_error(3, 1, "error3", "error", "エラー2", "context3")
        
        summary = parser.get_graceful_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['by_severity']['error'] == 2
        assert summary['by_severity']['warning'] == 1
        assert summary['has_critical_errors'] is True


class TestHTMLRendererGracefulErrors:
    """HTMLRendererのgraceful error handling機能テスト"""
    
    def test_html_renderer_error_setup(self):
        """HTMLRendererでのエラー設定テスト"""
        renderer = HTMLRenderer()
        
        # エラーリストを作成
        errors = [
            GracefulSyntaxError(
                line_number=1,
                column=1,
                error_type="test_error",
                severity="error",
                message="テストエラー",
                context="テストコンテキスト"
            )
        ]
        
        renderer.set_graceful_errors(errors, embed_in_html=True)
        
        assert len(renderer.graceful_errors) == 1
        assert renderer.embed_errors_in_html is True
    
    def test_error_summary_html_generation(self):
        """エラーサマリーHTML生成テスト"""
        renderer = HTMLRenderer()
        
        errors = [
            GracefulSyntaxError(
                line_number=1, column=1, error_type="error1", severity="error",
                message="エラーメッセージ1", context="コンテキスト1"
            ),
            GracefulSyntaxError(
                line_number=2, column=1, error_type="warning1", severity="warning", 
                message="警告メッセージ1", context="コンテキスト2"
            )
        ]
        
        renderer.set_graceful_errors(errors, embed_in_html=True)
        summary_html = renderer._render_error_summary()
        
        assert "記法エラーレポート" in summary_html
        assert "エラー: 1件" in summary_html
        assert "警告: 1件" in summary_html
        assert "合計: 2件" in summary_html
        assert "エラーメッセージ1" in summary_html
        assert "警告メッセージ1" in summary_html


class TestIntegrationGracefulErrors:
    """graceful error handling統合テスト"""
    
    def test_end_to_end_graceful_handling(self):
        """エンドツーエンドのgraceful handling テスト"""
        # この部分は実際のCLI統合テストとして実装
        # 現在は基本的な動作確認のみ
        parser = Parser(graceful_errors=True)
        renderer = HTMLRenderer()
        
        # 正常なコンテンツでテスト
        text = """
# 見出し1 # テストタイトル

正常なパラグラフ。
"""
        
        nodes = parser.parse(text.strip())
        errors = parser.get_graceful_errors()
        
        renderer.set_graceful_errors(errors, embed_in_html=True)
        html = renderer.render_nodes_with_errors(nodes)
        
        assert isinstance(html, str)
        assert len(html) > 0


@pytest.fixture
def sample_error_text():
    """テスト用のエラーを含むテキスト"""
    return """
# 見出し1 # 正常な見出し

# 太字 未完了のマーカー

正常なパラグラフ。

# 不明なキーワード # 存在しないキーワード #
"""


class TestGracefulErrorsWithSampleText:
    """サンプルテキストを使用したgraceful error handlingテスト"""
    
    def test_parser_with_error_text(self, sample_error_text):
        """エラーを含むテキストでのParser動作テスト"""
        parser = Parser(graceful_errors=True)
        
        # パース実行（graceful modeでエラーがあっても継続）
        nodes = parser.parse(sample_error_text.strip())
        
        # 結果検証
        assert len(nodes) > 0  # 一部のノードは正常に生成される
        assert parser.has_graceful_errors()  # エラーが記録されている
        
        errors = parser.get_graceful_errors()
        assert len(errors) > 0
        
        # エラーサマリー確認
        summary = parser.get_graceful_error_summary()
        assert summary['total_errors'] > 0


class TestSecurityGracefulErrors:
    """graceful error handlingのセキュリティテスト"""
    
    def test_xss_prevention_in_error_message(self):
        """エラーメッセージ内のXSS攻撃防止テスト"""
        malicious_message = "<script>alert('XSS')</script>"
        malicious_context = "<img src=x onerror=alert('XSS')>"
        malicious_suggestion = "<iframe src='javascript:alert(1)'></iframe>"
        
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="xss_test",
            severity="error",
            message=malicious_message,
            context=malicious_context,
            suggestion=malicious_suggestion
        )
        
        html_content = error.html_content
        
        # スクリプトタグがエスケープされていることを確認
        assert "<script>" not in html_content
        assert "&lt;script&gt;" in html_content
        assert "<img " not in html_content
        assert "&lt;img " in html_content
        assert "<iframe" not in html_content
        assert "&lt;iframe" in html_content
    
    def test_html_renderer_xss_prevention(self):
        """HTMLレンダラーでのXSS攻撃防止テスト"""
        renderer = HTMLRenderer()
        
        malicious_errors = [
            GracefulSyntaxError(
                line_number=1,
                column=1,
                error_type="xss_test",
                severity="error",
                message="<script>alert('XSS in title')</script>",
                context="<img src=x onerror=alert('context')>",
                suggestion="<iframe src='javascript:alert(1)'></iframe>"
            )
        ]
        
        renderer.set_graceful_errors(malicious_errors, embed_in_html=True)
        summary_html = renderer._render_error_summary()
        
        # 悪意のあるスクリプトがエスケープされていることを確認
        assert "<script>" not in summary_html
        assert "<img " not in summary_html or "&lt;img " in summary_html
        assert "<iframe" not in summary_html
        assert "javascript:" not in summary_html
    
    def test_error_marker_xss_prevention(self):
        """エラーマーカーでのXSS攻撃防止テスト"""
        renderer = HTMLRenderer()
        
        malicious_errors = [
            GracefulSyntaxError(
                line_number=1,
                column=1,
                error_type="xss_test",
                severity="warning",
                message="<svg onload=alert('XSS')>",
                context="normal context",
                suggestion="<marquee onstart=alert('XSS')>suggestion</marquee>"
            )
        ]
        
        renderer.set_graceful_errors(malicious_errors, embed_in_html=True)
        
        test_html = "<p>テストコンテンツ</p>"
        result_html = renderer._embed_error_markers(test_html)
        
        # SVGタグとmarqueeタグがエスケープされていることを確認
        assert "<svg " not in result_html
        assert "&lt;svg " in result_html
        assert "<marquee" not in result_html
        assert "&lt;marquee" in result_html


class TestLargeFileGracefulErrors:
    """大容量ファイルでのgraceful error handlingテスト"""
    
    def test_memory_efficiency_with_many_errors(self):
        """大量エラー発生時のメモリ効率テスト"""
        parser = Parser(graceful_errors=True)
        
        # 大量のエラーを生成
        for i in range(1000):
            parser._record_graceful_error(
                line_number=i+1,
                column=1,
                error_type=f"test_error_{i}",
                severity="warning" if i % 2 == 0 else "error",
                message=f"テストエラー {i}",
                context=f"コンテキスト {i}",
                suggestion=f"提案 {i}"
            )
        
        # メモリ使用量の確認（基本的な動作確認）
        errors = parser.get_graceful_errors()
        assert len(errors) == 1000
        
        # サマリー生成が正常に動作することを確認
        summary = parser.get_graceful_error_summary()
        assert summary['total_errors'] == 1000
        assert summary['by_severity']['error'] == 500
        assert summary['by_severity']['warning'] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])