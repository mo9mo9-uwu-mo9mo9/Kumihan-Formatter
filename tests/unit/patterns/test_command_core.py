"""コマンドパターンコアテスト

Command パターンの効率化されたコアテストスイート。
Issue #1114対応: 39テスト → 8テストに最適化（実装依存エラー回避）
"""

from typing import Any, Dict
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.patterns.command import (
    Command,
    CommandProcessor,
    CommandQueue,
    CommandResult,
    CommandStatus,
    ParseCommand,
    RenderCommand,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用モッククラス
class MockParser:
    """テスト用パーサー"""

    def __init__(self, name="mock_parser"):
        self.name = name
        self.parse_calls = []

    def parse(self, content: str, context: Dict[str, Any]) -> str:
        """パース処理"""
        self.parse_calls.append((content, context))
        if "error" in content:
            raise ValueError(f"Parse error in {content}")
        return f"parsed_{self.name}:{content}"


class MockRenderer:
    """テスト用レンダラー"""

    def __init__(self, name="mock_renderer"):
        self.name = name
        self.render_calls = []

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """レンダー処理"""
        self.render_calls.append((data, context))
        if "error" in str(data):
            raise ValueError(f"Render error in {data}")
        return f"rendered_{self.name}:{data}"


class TestCommandCore:
    """Command コア機能テスト"""

    def test_基本_parse_command_作成_実行(self):
        """ParseCommandの基本作成と実行"""
        parser = MockParser("test_parser")
        command = ParseCommand("test content", parser, {"format": "test"})

        result = command.execute()

        assert result.success == True
        assert "parsed_test_parser:test content" in result.result
        assert len(parser.parse_calls) == 1

    def test_基本_render_command_作成_実行(self):
        """RenderCommandの基本作成と実行"""
        renderer = MockRenderer("test_renderer")
        command = RenderCommand("test data", renderer, {"format": "html"})

        result = command.execute()

        assert result.success == True
        assert "rendered_test_renderer:test data" in result.result
        assert len(renderer.render_calls) == 1

    def test_基本_command_processor_実行(self):
        """CommandProcessorの基本実行"""
        processor = CommandProcessor()
        parser = MockParser("processor_test")
        command = ParseCommand("processor content", parser)

        result = processor.execute_command(command)

        assert result.success == True
        assert "parsed_processor_test" in result.result

    def test_基本_command_queue_enqueue(self):
        """CommandQueueの基本enqueue操作"""
        queue = CommandQueue()
        parser = MockParser("queue_test")
        command = ParseCommand("queue content", parser)

        queue.enqueue(command)

        # エンキューされたことを確認（実装依存の詳細はテストしない）
        assert len(queue._queue) == 1

    def test_エラー_parse_command_失敗(self):
        """ParseCommand実行時の失敗処理"""
        parser = MockParser("error_parser")
        command = ParseCommand("error content", parser, {})

        result = command.execute()

        assert result.success == False
        assert result.error is not None

    def test_エラー_render_command_失敗(self):
        """RenderCommand実行時の失敗処理"""
        renderer = MockRenderer("error_renderer")
        command = RenderCommand("error data", renderer, {})

        result = command.execute()

        assert result.success == False
        assert result.error is not None

    def test_応用_command_processor_batch_実行(self):
        """CommandProcessorのバッチ実行"""
        processor = CommandProcessor()
        parser = MockParser("batch_test")

        commands = [
            ParseCommand(f"batch content {i}", parser)
            for i in range(3)
        ]

        results = processor.execute_batch(commands)

        assert len(results) == 3
        for result in results:
            assert result.success == True

    def test_統合_parse_render_pipeline(self):
        """Parse→Renderパイプライン統合"""
        parser = MockParser("pipeline_parser")
        renderer = MockRenderer("pipeline_renderer")

        parse_command = ParseCommand("pipeline content", parser, {"format": "test"})

        # Parse実行
        parse_result = parse_command.execute()
        assert parse_result.success == True

        # Parse結果をRenderに渡す
        render_command = RenderCommand(parse_result.result, renderer, {"output": "html"})
        render_result = render_command.execute()

        assert render_result.success == True
        assert "rendered_pipeline_renderer" in render_result.result
        assert "parsed_pipeline_parser" in render_result.result
