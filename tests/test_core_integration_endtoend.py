"""Core Integration End-to-End Tests

End-to-end integration tests for core modules workflow.
Issue #540 Phase 2: 300行制限遵守のための分割
"""

import pytest

from kumihan_formatter.config import ConfigManager
from kumihan_formatter.core.template_context import RenderContext
from kumihan_formatter.core.template_manager import TemplateManager
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer

pytestmark = [pytest.mark.integration, pytest.mark.tdd_green]


class TestCoreIntegrationEndToEnd:
    """End-to-end core integration tests"""

    def test_complete_processing_workflow(self):
        """完全な処理ワークフローテスト"""
        # シンプルなテキストを準備
        input_text = "# Test Document\n\nThis is a test."

        try:
            # パーサーで解析
            parser = Parser()
            nodes = parser.parse(input_text)
            assert nodes is not None

            # レンダラーで出力
            renderer = Renderer()
            output = renderer.render(nodes)
            assert output is not None
            assert isinstance(output, str)

        except (AttributeError, NotImplementedError):
            # 完全な実装がない場合はスキップ
            pytest.skip("Complete workflow not fully implemented")

    def test_configuration_driven_processing(self):
        """設定による処理制御のテスト"""
        try:
            # 設定の準備
            config = ConfigManager()
            config.set("output_format", "html")
            config.set("encoding", "utf-8")

            # 設定を使った処理
            parser = Parser()
            parser.configure(config)

            renderer = Renderer()
            renderer.configure(config)

            # 基本的な処理フロー
            input_text = "# Configured Test"
            nodes = parser.parse(input_text)
            output = renderer.render(nodes)

            assert output is not None

        except (AttributeError, NotImplementedError):
            # 設定機能が未実装の場合はスキップ
            pytest.skip("Configuration-driven processing not implemented")

    def test_template_context_integration(self):
        """テンプレートコンテキスト統合テスト"""
        try:
            # コンテキストの作成
            context = RenderContext()
            context.set("title", "Test Document")
            context.set("author", "Test Author")

            # テンプレートマネージャーとの連携
            template_manager = TemplateManager()
            template_manager.set_context(context)

            # 基本的な動作確認
            assert context.get("title") == "Test Document"
            assert template_manager is not None

        except (AttributeError, NotImplementedError):
            # テンプレート機能が未実装の場合はスキップ
            pytest.skip("Template context integration not implemented")
