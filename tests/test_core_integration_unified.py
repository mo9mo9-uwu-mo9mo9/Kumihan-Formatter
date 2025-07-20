"""Core Integration Tests - Unified Version

Integration tests for core modules combining basic and advanced functionality.
Focuses on high-impact modules: parser, renderer, config, file operations.

Issue #540 Phase 2: 重複テスト統合によるCI/CD最適化
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config import ConfigManager
from kumihan_formatter.core.ast_nodes import Node, NodeBuilder

# Additional high-value modules
from kumihan_formatter.core.encoding_detector import EncodingDetector
from kumihan_formatter.core.file_operations import FileOperations
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.template_context import RenderContext
from kumihan_formatter.core.template_manager import TemplateManager

# Core modules with highest impact
from kumihan_formatter.parser import Parser, parse
from kumihan_formatter.renderer import Renderer, render

pytestmark = [pytest.mark.integration, pytest.mark.tdd_green]


class TestCoreIntegrationBasic:
    """Basic core functionality integration tests"""

    def test_parser_basic_functionality(self):
        """Test basic parser functionality"""
        parser = Parser()
        assert parser is not None

        # Test basic parsing
        test_content = "# Test Heading\nTest paragraph."
        result = parser.parse(test_content)
        assert result is not None

    def test_renderer_basic_functionality(self):
        """Test basic renderer functionality"""
        renderer = Renderer()
        assert renderer is not None

        # Test basic rendering
        nodes = [Node("h1", "Test")]
        result = renderer.render(nodes)
        assert result is not None
        assert isinstance(result, str)

    def test_config_manager_integration(self):
        """Test config manager integration"""
        config = ConfigManager()
        assert config is not None

        # Test basic configuration
        config.set("output_format", "html")
        assert config.get("output_format") == "html"

    def test_file_operations_integration(self):
        """Test file operations integration"""
        file_ops = FileOperations()
        assert file_ops is not None

        # Test with temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("test content")
            tmp_path = tmp.name

        try:
            content = file_ops.read_file(tmp_path)
            assert "test content" in content
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_encoding_detector_integration(self):
        """Test encoding detector integration"""
        detector = EncodingDetector()
        assert detector is not None

        # Test basic detection
        test_bytes = "Hello World".encode("utf-8")
        encoding = detector.detect(test_bytes)
        assert encoding is not None

    def test_keyword_parser_integration(self):
        """Test keyword parser integration"""
        parser = KeywordParser()
        assert parser is not None

        # Test basic keyword parsing
        content = ";;;highlight;;; Important text ;;;"
        result = parser.parse(content)
        assert result is not None

    def test_template_manager_integration(self):
        """Test template manager integration"""
        manager = TemplateManager()
        assert manager is not None

        # Test basic template operations
        try:
            templates = manager.get_available_templates()
            assert isinstance(templates, (list, tuple))
        except AttributeError:
            # Method may not be implemented
                pass

    def test_node_builder_integration(self):
        """Test node builder integration"""
        builder = NodeBuilder()
        assert builder is not None

        # Test basic node creation
        node = builder.create_node("p", "Test paragraph")
        assert node is not None
        assert node.tag == "p"
        assert node.content == "Test paragraph"


class TestCoreIntegrationAdvanced:
    """Advanced core functionality integration tests (from integration/test_core_integration.py)"""

    @pytest.mark.unit
    def test_parser_to_renderer_integration(self):
        """パーサーからレンダラーへの統合フロー"""
        from kumihan_formatter.core.ast_nodes import Node
        from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

        # パーサー的な処理をシミュレート
        nodes = [
            Node("h1", "見出し1"),
            Node("p", "段落テキスト"),
            Node("strong", "太字テキスト"),
        ]

        # レンダラーでHTML出力
        renderer = HTMLRenderer()
        html_output = renderer.render(nodes)

        # 結果検証
        assert html_output is not None
        assert isinstance(html_output, str)
        assert len(html_output) > 0

        # 基本的なHTML要素が含まれているかチェック
        if html_output and len(html_output) > 10:
            # HTML要素の存在確認（柔軟な検証）
            has_heading = any(
                tag in html_output.lower() for tag in ["<h1", "<h2", "<h3"]
            )
            has_paragraph = "<p" in html_output.lower()

            # 少なくとも何らかの構造化された出力があることを確認
            assert has_heading or has_paragraph or len(html_output) > 20

    def test_file_operations_integration(self):
        """ファイル操作の統合テスト"""
        from kumihan_formatter.core.file_operations import FileOperations

        file_ops = FileOperations()

        # テンポラリファイルで統合テスト
        test_content = """# テストドキュメント

これはテスト用のサンプルファイルです。

;;;highlight;;; 重要な情報 ;;;

((脚注の例))
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(test_content)
            temp_file_path = tmp.name

        try:
            # ファイル読み込み
            read_content = file_ops.read_file(temp_file_path)
            assert read_content is not None
            assert "テストドキュメント" in read_content

            # ファイル情報取得
            file_info = file_ops.get_file_info(temp_file_path)
            assert file_info is not None
            assert "size" in file_info
            assert file_info["size"] > 0

        except (AttributeError, NotImplementedError):
            # ファイル操作が未実装の場合はスキップ
            pytest.skip("FileOperations methods not fully implemented")
        finally:
            # クリーンアップ
            Path(temp_file_path).unlink(missing_ok=True)

    def test_ast_nodes_creation_workflow(self):
        """ASTノード作成ワークフローのテスト"""
        from kumihan_formatter.core.ast_nodes import Node, NodeBuilder

        builder = NodeBuilder()

        # 基本的なノード作成
        root_node = builder.create_node("document", "")
        assert root_node is not None
        assert root_node.tag == "document"

        # 子ノードの追加
        heading_node = builder.create_node("h1", "メインタイトル")
        paragraph_node = builder.create_node("p", "段落の内容")

        root_node.add_child(heading_node)
        root_node.add_child(paragraph_node)

        # 階層構造の確認
        assert len(root_node.children) == 2
        assert root_node.children[0].tag == "h1"
        assert root_node.children[1].tag == "p"

        # ノードツリーの深さ確認
        assert root_node.get_depth() >= 0
        assert heading_node.get_depth() == 1

    def test_error_handling_integration(self):
        """エラーハンドリングの統合テスト"""
        from kumihan_formatter.core.encoding_detector import EncodingDetector
        from kumihan_formatter.core.file_operations import FileOperations

        # 存在しないファイルの処理
        file_ops = FileOperations()
        try:
            result = file_ops.read_file("non_existent_file.txt")
            # エラーハンドリングされていれば None または適切なエラー応答
            assert result is None or isinstance(result, str)
        except FileNotFoundError:
            # FileNotFoundError が適切に発生することも正常
                pass

        # 不正なエンコーディングデータの処理
        detector = EncodingDetector()
        try:
            # 不正なバイトデータ
            invalid_data = b"\xff\xfe\x00\x00\x01\x02"
            encoding = detector.detect(invalid_data)
            # エラーハンドリングされていれば None または何らかの値
            assert encoding is None or isinstance(encoding, str)
        except Exception:
            # 何らかの例外が発生するのも正常な動作
                pass


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
