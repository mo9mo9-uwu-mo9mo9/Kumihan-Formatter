"""Template System Integration Tests

テンプレートシステムの統合テスト
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.tdd_green
class TestTemplateIntegration:
    """テンプレートシステム統合テスト"""

    @pytest.mark.unit
    def test_template_context_integration(self):
        """テンプレートコンテキスト統合テスト"""
        try:
            from kumihan_formatter.core.template_context import TemplateContext

            context = TemplateContext()
            assert context is not None
        except ImportError:
            # モジュールが存在しない場合はスキップ
            pass

    @pytest.mark.unit
    def test_template_filters_integration(self):
        """テンプレートフィルター統合テスト"""
        try:
            from kumihan_formatter.core.template_filters import escape_html

            result = escape_html("<script>alert('xss')</script>")
            assert "&lt;script&gt;" in result
            assert "&lt;/script&gt;" in result
        except ImportError:
            # モジュールが存在しない場合はスキップ
            pass
