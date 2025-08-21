"""Design Patterns Integration Tests"""

import asyncio
import time
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.patterns import (
    ArchitectureManager,
    CachingParserDecorator,
    CommandProcessor,
    DecoratorChain,
    Event,
    EventBus,
    EventType,
    Observer,
    ParseCommand,
    ParsingStrategy,
    RenderCommand,
    RenderingStrategy,
    StrategyManager,
)


class MockKumihanParser:
    """テスト用Kumihanパーサー"""

    def parse(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Kumihan記法パース（簡易実装）"""
        import re

        pattern = r"# (\w+) #([^#]+)##"
        matches = re.findall(pattern, content)

        blocks = []
        for decoration, text in matches:
            blocks.append(
                {
                    "type": "kumihan_block",
                    "decoration": decoration,
                    "content": text.strip(),
                }
            )

        return {"blocks": blocks, "total_blocks": len(blocks), "parser": "mock_kumihan"}


class MockHTMLRenderer:
    """テスト用HTMLレンダラー"""

    def render(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """HTMLレンダリング（簡易実装）"""
        if not isinstance(data, dict) or "blocks" not in data:
            return ""

        html_parts = ["<html><body>"]

        for block in data["blocks"]:
            if block["type"] == "kumihan_block":
                decoration = block["decoration"]
                content = block["content"]

                if decoration == "太字":
                    html_parts.append(f"<strong>{content}</strong>")
                elif decoration == "イタリック":
                    html_parts.append(f"<em>{content}</em>")
                elif decoration == "見出し":
                    html_parts.append(f"<h2>{content}</h2>")
                else:
                    html_parts.append(f"<span class='{decoration}'>{content}</span>")

        html_parts.append("</body></html>")
        return "\n".join(html_parts)


class EventCollector(Observer):
    """テスト用イベントコレクター"""

    def __init__(self):
        self.events = []

    def handle_event(self, event: Event) -> None:
        self.events.append(event)

    def get_supported_events(self) -> List[EventType]:
        return list(EventType)


class TestPatternIntegration:
    """パターン統合テスト"""

    def test_event_driven_parsing_workflow(self):
        """イベント駆動パーシングワークフローテスト"""
        # アーキテクチャマネージャー初期化
        manager = ArchitectureManager()
        event_bus = manager.get_event_bus()

        # イベントコレクター設定
        collector = EventCollector()
        event_bus.subscribe_global(collector)

        # パーサーとコマンドプロセッサー
        parser = MockKumihanParser()
        command_processor = manager.get_command_processor()

        # パーシングコマンド作成・実行
        content = "# 見出し #テストヘッダー## # 太字 #重要なテキスト##"

        # パーシング開始イベント発行
        manager.publish_event(
            EventType.PARSING_STARTED,
            "integration_test",
            {"content_length": len(content)},
        )

        # パーシングコマンド実行
        parse_command = ParseCommand(content, parser, {"format": "kumihan"})
        result = command_processor.execute_command(parse_command)

        # パーシング完了イベント発行
        manager.publish_event(
            EventType.PARSING_COMPLETED,
            "integration_test",
            {
                "duration": result.execution_time,
                "blocks_count": len(result.result.get("blocks", [])),
            },
        )

        # 結果検証
        assert result.success is True
        assert len(result.result["blocks"]) == 2
        assert result.result["blocks"][0]["decoration"] == "見出し"
        assert result.result["blocks"][1]["decoration"] == "太字"

        # イベント発行確認
        assert len(collector.events) == 2
        assert collector.events[0].event_type == EventType.PARSING_STARTED
        assert collector.events[1].event_type == EventType.PARSING_COMPLETED

    def test_strategy_based_rendering_workflow(self):
        """戦略ベースレンダリングワークフローテスト"""
        manager = ArchitectureManager()
        strategy_manager = manager.get_strategy_manager()
        command_processor = manager.get_command_processor()

        # レンダリング戦略設定
        html_renderer = MockHTMLRenderer()

        class HTMLRenderingStrategy:
            def render(self, data, context):
                return html_renderer.render(data, context)

            def get_strategy_name(self):
                return "html_strategy"

            def supports_format(self, output_format):
                return output_format.lower() in ["html", "htm"]

        strategy_manager.register_rendering_strategy(
            "html", HTMLRenderingStrategy(), is_default=True
        )

        # テストデータ準備
        parsed_data = {
            "blocks": [
                {
                    "type": "kumihan_block",
                    "decoration": "見出し",
                    "content": "テストタイトル",
                },
                {
                    "type": "kumihan_block",
                    "decoration": "太字",
                    "content": "重要な内容",
                },
            ]
        }

        # 戦略選択・レンダリング実行
        rendering_strategy = strategy_manager.select_rendering_strategy("html")
        assert rendering_strategy is not None

        render_command = RenderCommand(
            parsed_data, rendering_strategy, {"format": "html"}
        )
        result = command_processor.execute_command(render_command)

        # 結果検証
        assert result.success is True
        html_output = result.result
        assert "<html>" in html_output
        assert "<h2>テストタイトル</h2>" in html_output
        assert "<strong>重要な内容</strong>" in html_output
        assert "</html>" in html_output

    def test_decorated_pipeline_workflow(self):
        """デコレート済みパイプラインワークフローテスト"""
        manager = ArchitectureManager()

        # ベースパーサー
        base_parser = MockKumihanParser()

        # 機能拡張パーサー作成（キャッシュ・ログ機能付き）
        enhanced_parser = manager.create_enhanced_parser(base_parser)

        # 同じコンテンツを複数回パース
        content = "# 見出し #キャッシュテスト##"

        # 初回パース（パフォーマンス測定）
        start_time = time.time()
        result1 = enhanced_parser.parse(content, {})
        first_duration = time.time() - start_time

        # 二回目パース（キャッシュ効果測定）
        start_time = time.time()
        result2 = enhanced_parser.parse(content, {})
        second_duration = time.time() - start_time

        # 結果検証
        assert result1 == result2  # 同じ結果
        assert len(result1["blocks"]) == 1
        assert result1["blocks"][0]["decoration"] == "見出し"

        # キャッシュ効果確認（二回目は高速）
        assert second_duration < first_duration * 0.5  # 50%以上高速化

    def test_complete_processing_pipeline(self):
        """完全処理パイプラインテスト"""
        # 統合システム初期化
        manager = ArchitectureManager()
        event_bus = manager.get_event_bus()
        strategy_manager = manager.get_strategy_manager()
        command_processor = manager.get_command_processor()

        # イベント収集
        collector = EventCollector()
        event_bus.subscribe_global(collector)

        # パーサー戦略設定
        class KumihanParsingStrategy:
            def parse(self, content, context):
                return MockKumihanParser().parse(content, context)

            def get_strategy_name(self):
                return "kumihan"

            def supports_content(self, content):
                return 0.9 if "# " in content and "##" in content else 0.1

        # レンダリング戦略設定
        class HTMLRenderingStrategy:
            def render(self, data, context):
                return MockHTMLRenderer().render(data, context)

            def get_strategy_name(self):
                return "html"

            def supports_format(self, output_format):
                return output_format.lower() == "html"

        strategy_manager.register_parsing_strategy(
            "kumihan", KumihanParsingStrategy(), is_default=True
        )
        strategy_manager.register_rendering_strategy(
            "html", HTMLRenderingStrategy(), is_default=True
        )

        # テストコンテンツ
        content = """
        # 見出し #メインタイトル##
        # 太字 #重要なポイント##
        # イタリック #補足説明##
        """

        # Step 1: パーシング処理
        manager.publish_event(
            EventType.PARSING_STARTED, "pipeline_test", {"content_length": len(content)}
        )

        parsing_strategy = strategy_manager.select_parsing_strategy(content)
        parse_command = ParseCommand(content, parsing_strategy)
        parse_result = command_processor.execute_command(parse_command)

        manager.publish_event(
            EventType.PARSING_COMPLETED,
            "pipeline_test",
            {
                "duration": parse_result.execution_time,
                "blocks_count": len(parse_result.result.get("blocks", [])),
            },
        )

        # Step 2: レンダリング処理
        manager.publish_event(
            EventType.RENDERING_STARTED, "pipeline_test", {"format": "html"}
        )

        rendering_strategy = strategy_manager.select_rendering_strategy("html")
        render_command = RenderCommand(
            parse_result.result, rendering_strategy, {"format": "html"}
        )
        render_result = command_processor.execute_command(render_command)

        manager.publish_event(
            EventType.RENDERING_COMPLETED,
            "pipeline_test",
            {
                "duration": render_result.execution_time,
                "output_size": len(render_result.result),
            },
        )

        # 結果検証
        assert parse_result.success is True
        assert render_result.success is True

        # パース結果確認
        parsed_blocks = parse_result.result["blocks"]
        assert len(parsed_blocks) == 3
        assert parsed_blocks[0]["decoration"] == "見出し"
        assert parsed_blocks[1]["decoration"] == "太字"
        assert parsed_blocks[2]["decoration"] == "イタリック"

        # レンダリング結果確認
        html_output = render_result.result
        assert "<h2>メインタイトル</h2>" in html_output
        assert "<strong>重要なポイント</strong>" in html_output
        assert "<em>補足説明</em>" in html_output

        # イベント処理確認
        assert len(collector.events) == 4
        event_types = [event.event_type for event in collector.events]
        assert EventType.PARSING_STARTED in event_types
        assert EventType.PARSING_COMPLETED in event_types
        assert EventType.RENDERING_STARTED in event_types
        assert EventType.RENDERING_COMPLETED in event_types

        # コマンド履歴確認
        history = command_processor.get_command_history()
        assert len(history) == 2
        assert isinstance(history[0], ParseCommand)
        assert isinstance(history[1], RenderCommand)

    def test_async_event_processing(self):
        """非同期イベント処理テスト"""

        async def async_test():
            manager = ArchitectureManager()
            event_bus = manager.get_event_bus()

            # 非同期オブザーバー
            async_events = []

            class AsyncEventHandler:
                async def handle_event_async(self, event):
                    await asyncio.sleep(0.01)  # 非同期処理シミュレート
                    async_events.append(event)

            handler = AsyncEventHandler()
            event_bus.subscribe_async(EventType.PARSING_STARTED, handler)

            # 非同期イベント発行
            event = Event(EventType.PARSING_STARTED, "async_test")
            await event_bus.publish_async(event)

            # 結果確認
            assert len(async_events) == 1
            assert async_events[0].event_type == EventType.PARSING_STARTED
            assert async_events[0].source == "async_test"

        # 同期テストとして実行
        asyncio.run(async_test())

    def test_error_resilience(self):
        """エラー耐性テスト"""
        manager = ArchitectureManager()
        event_bus = manager.get_event_bus()
        command_processor = manager.get_command_processor()

        # エラーを発生させるオブザーバー
        error_observer = Mock()
        error_observer.handle_event = Mock(side_effect=Exception("Observer error"))

        # 正常なオブザーバー
        normal_observer = Mock()
        normal_observer.handle_event = Mock()

        event_bus.subscribe(EventType.PARSING_ERROR, error_observer)
        event_bus.subscribe(EventType.PARSING_ERROR, normal_observer)

        # エラーイベント発行
        error_event = Event(
            EventType.PARSING_ERROR, "error_test", {"error": "Test error"}
        )

        # エラーが発生してもシステムが停止しないことを確認
        event_bus.publish(error_event)

        # 正常なオブザーバーは動作することを確認
        normal_observer.handle_event.assert_called_once_with(error_event)

        # エラーを発生させるパーサー
        error_parser = Mock()
        error_parser.parse = Mock(side_effect=ValueError("Parse error"))

        parse_command = ParseCommand("content", error_parser)
        result = command_processor.execute_command(parse_command)

        # エラーが適切に処理されることを確認
        assert result.success is False
        assert isinstance(result.error, ValueError)

    def test_performance_benchmarks(self):
        """パフォーマンスベンチマークテスト"""
        manager = ArchitectureManager()

        # 大量のイベント処理
        event_bus = manager.get_event_bus()
        collector = EventCollector()
        event_bus.subscribe_global(collector)

        # イベント大量発行（性能測定）
        start_time = time.time()
        for i in range(1000):
            event = Event(EventType.PARSING_STARTED, f"perf_test_{i}", {"index": i})
            event_bus.publish(event)

        event_processing_time = time.time() - start_time

        # パフォーマンス要件チェック
        assert event_processing_time < 1.0  # 1000イベント処理が1秒以内
        assert len(collector.events) == 1000

        # 単一イベント処理時間（要件: < 0.1ms）
        start_time = time.time()
        single_event = Event(EventType.PARSING_COMPLETED, "single_test")
        event_bus.publish(single_event)
        single_event_time = time.time() - start_time

        assert single_event_time < 0.0001  # 0.1ms以内
