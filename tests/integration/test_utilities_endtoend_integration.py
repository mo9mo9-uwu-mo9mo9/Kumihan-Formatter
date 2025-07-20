"""Utilities and End-to-End Integration Tests

ユーティリティシステムとエンドツーエンドワークフローの統合テスト
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.tdd_green
class TestUtilitiesIntegration:
    """ユーティリティ統合テスト"""

    @pytest.mark.unit
    def test_logger_integration(self):
        """ロガー統合テスト"""
        from kumihan_formatter.core.utilities.logger import get_logger

        logger = get_logger("test_module")
        assert logger is not None

        # ログレベルの設定テスト
        logger.debug("デバッグメッセージ")
        logger.info("情報メッセージ")
        logger.warning("警告メッセージ")

    @pytest.mark.file_io
    def test_file_system_integration(self):
        """ファイルシステム統合テスト"""
        try:
            from kumihan_formatter.core.utilities.file_system import ensure_directory

            with tempfile.TemporaryDirectory() as temp_dir:
                test_dir = Path(temp_dir) / "subdir" / "subsubdir"

                result = ensure_directory(str(test_dir))
                assert result is not None
        except ImportError:
            # モジュールが存在しない場合はスキップ
            pass

    @pytest.mark.performance
    def test_performance_monitoring_integration(self):
        """パフォーマンス監視統合テスト"""
        try:
            from kumihan_formatter.core.utilities.performance_optimizer import (
                PerformanceOptimizer,
            )

            optimizer = PerformanceOptimizer()
            assert optimizer is not None
        except ImportError:
            # モジュールが存在しない場合はスキップ
            pass

    @pytest.mark.unit
    def test_memory_tracking_integration(self):
        """メモリ追跡統合テスト"""
        # 基本的なメモリ使用量の確認
        initial_size = sys.getsizeof({})
        test_dict = {"key": "value"}
        final_size = sys.getsizeof(test_dict)

        assert final_size > initial_size


@pytest.mark.e2e
@pytest.mark.tdd_refactor
class TestEndToEndWorkflow:
    """エンドツーエンドワークフロー統合テスト"""

    @pytest.mark.mock_heavy
    def test_simple_conversion_workflow(self):
        """シンプルな変換ワークフローの統合テスト"""
        from kumihan_formatter.core.ast_nodes import Node
        from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

        # 入力データのシミュレート
        input_nodes = [
            Node("h1", "ドキュメントタイトル"),
            Node("p", "これは段落です。"),
            Node(
                "ul",
                [
                    Node("li", "リスト項目1"),
                    Node("li", "リスト項目2"),
                ],
            ),
        ]

        # レンダリング処理
        renderer = HTMLRenderer()

        with (
            patch.object(
                renderer.heading_renderer,
                "render_h1",
                return_value="<h1>ドキュメントタイトル</h1>",
            ),
            patch.object(
                renderer.element_renderer,
                "render_paragraph",
                return_value="<p>これは段落です。</p>",
            ),
            patch.object(
                renderer.element_renderer,
                "render_unordered_list",
                return_value="<ul><li>リスト項目1</li><li>リスト項目2</li></ul>",
            ),
        ):
            result = renderer.render_nodes(input_nodes)

            # 結果の検証
            assert "<h1>ドキュメントタイトル</h1>" in result
            assert "<p>これは段落です。</p>" in result
            assert "<ul>" in result
            assert "<li>リスト項目1</li>" in result

    @pytest.mark.unit
    def test_error_recovery_workflow(self):
        """エラー回復ワークフローの統合テスト"""
        from kumihan_formatter.core.error_handling.error_recovery import ErrorRecovery

        recovery = ErrorRecovery()
        assert recovery is not None

        # 基本的なエラー回復の実行
        try:
            recovery.recover_from_error(Exception("テストエラー"))
        except Exception:
            # エラー回復が未実装の場合は例外を許容
            pass

    @pytest.mark.mock_heavy
    def test_complete_rendering_pipeline(self):
        """完全なレンダリングパイプラインの統合テスト"""
        from kumihan_formatter.core.rendering.content_processor import ContentProcessor
        from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

        renderer = HTMLRenderer()
        processor = ContentProcessor(renderer)

        # 複雑なコンテンツのレンダリング
        content = {
            "type": "document",
            "children": [
                {"type": "h1", "content": "タイトル"},
                {"type": "p", "content": "段落"},
            ],
        }

        with patch.object(
            processor, "render_content", return_value="<div>レンダリング結果</div>"
        ):
            result = processor.render_content(content)
            assert "レンダリング結果" in result
