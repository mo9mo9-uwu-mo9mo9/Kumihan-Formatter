"""ストラテジーシステム統合テスト

Strategy パターンとその具体実装の効率化されたテストスイート。
Issue #1114対応: 55テスト → 20テストに最適化
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.patterns.strategies import (
    HTMLRenderingStrategy,
    KumihanParsingStrategy,
)
from kumihan_formatter.core.patterns.strategy import (
    ParsingStrategy,
    RenderingStrategy,
    StrategyManager,
    StrategyPriority,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用戦略実装
class MockParsingStrategy:
    """テスト用パーシング戦略"""

    def __init__(self, name: str, content_support: float = 0.5):
        self.name = name
        self.content_support = content_support
        self.parse_calls = []

    def parse(self, content: str, context: Dict[str, Any]) -> Any:
        """戦略的パース実行"""
        result = f"{self.name}_parsed:{content}"
        self.parse_calls.append((content, context))
        return result

    def get_strategy_name(self) -> str:
        """戦略名取得"""
        return self.name

    def supports_content(self, content: str) -> float:
        """コンテンツ対応度（0.0-1.0）"""
        if "kumihan" in content.lower():
            return min(1.0, self.content_support + 0.3)
        elif "markdown" in content.lower():
            return min(1.0, self.content_support + 0.1)
        else:
            return self.content_support


class MockRenderingStrategy:
    """テスト用レンダリング戦略"""

    def __init__(self, name: str, output_support: float = 0.5):
        self.name = name
        self.output_support = output_support
        self.render_calls = []

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """戦略的レンダー実行"""
        result = f"{self.name}_rendered:{data}"
        self.render_calls.append((data, context))
        return result

    def get_strategy_name(self) -> str:
        """戦略名取得"""
        return self.name

    def supports_output_format(self, format_type: str) -> float:
        """出力フォーマット対応度（0.0-1.0）"""
        if format_type.lower() == "html":
            return min(1.0, self.output_support + 0.3)
        elif format_type.lower() == "markdown":
            return min(1.0, self.output_support + 0.1)
        else:
            return self.output_support


class TestStrategyCore:
    """Strategy パターンコア機能テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.manager = StrategyManager()

    def test_基本_strategy_manager_初期化(self):
        """StrategyManager基本初期化"""
        manager = StrategyManager()

        assert hasattr(manager, "parsing_strategies")
        assert hasattr(manager, "rendering_strategies")
        assert len(manager.parsing_strategies) == 0
        assert len(manager.rendering_strategies) == 0

    def test_基本_parsing_strategy_登録(self):
        """パーシング戦略の登録"""
        strategy = MockParsingStrategy("test_parser")
        self.manager.register_parsing_strategy(strategy)

        assert len(self.manager.parsing_strategies) == 1
        assert self.manager.parsing_strategies[0] == strategy

    def test_基本_rendering_strategy_登録(self):
        """レンダリング戦略の登録"""
        strategy = MockRenderingStrategy("test_renderer")
        self.manager.register_rendering_strategy(strategy)

        assert len(self.manager.rendering_strategies) == 1
        assert self.manager.rendering_strategies[0] == strategy

    def test_基本_最適parsing_strategy_選択(self):
        """最適なパーシング戦略の選択"""
        strategy1 = MockParsingStrategy("parser1", 0.3)
        strategy2 = MockParsingStrategy("parser2", 0.8)

        self.manager.register_parsing_strategy(strategy1)
        self.manager.register_parsing_strategy(strategy2)

        # より高い対応度の戦略が選択される
        best_strategy = self.manager.get_best_parsing_strategy("test content")
        assert best_strategy == strategy2

    def test_基本_最適rendering_strategy_選択(self):
        """最適なレンダリング戦略の選択"""
        strategy1 = MockRenderingStrategy("renderer1", 0.3)
        strategy2 = MockRenderingStrategy("renderer2", 0.8)

        self.manager.register_rendering_strategy(strategy1)
        self.manager.register_rendering_strategy(strategy2)

        # より高い対応度の戦略が選択される
        best_strategy = self.manager.get_best_rendering_strategy("html")
        assert best_strategy == strategy2

    def test_基本_strategy_実行(self):
        """戦略実行とコンテキスト渡し"""
        strategy = MockParsingStrategy("test_parser")
        self.manager.register_parsing_strategy(strategy)

        content = "test content"
        context = {"format": "test"}

        result = self.manager.parse_content(content, context)

        assert result == "test_parser_parsed:test content"
        assert len(strategy.parse_calls) == 1
        assert strategy.parse_calls[0] == (content, context)

    def test_エラー_strategy_見つからない(self):
        """適用可能な戦略が見つからない場合"""
        # 対応度が低い戦略のみ登録
        strategy = MockParsingStrategy("low_support", 0.0)
        self.manager.register_parsing_strategy(strategy)

        with pytest.raises(ValueError, match="No suitable.*strategy"):
            self.manager.parse_content("unsupported content")

    def test_エラー_重複strategy_登録(self):
        """同名戦略の重複登録エラー"""
        strategy1 = MockParsingStrategy("duplicate")
        strategy2 = MockParsingStrategy("duplicate")

        self.manager.register_parsing_strategy(strategy1)

        with pytest.raises(ValueError, match="Strategy.*already registered"):
            self.manager.register_parsing_strategy(strategy2)


class TestKumihanParsingStrategy:
    """KumihanParsingStrategy具体実装テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.strategy = KumihanParsingStrategy()
        self.sample_context = {"format": "kumihan", "encoding": "utf-8"}

    def test_基本_kumihan_strategy_初期化(self):
        """Kumihan戦略の基本初期化"""
        strategy = KumihanParsingStrategy()

        assert strategy is not None
        assert hasattr(strategy, "parse")
        assert hasattr(strategy, "get_strategy_name")
        assert hasattr(strategy, "supports_content")

    def test_基本_kumihan_strategy_名前(self):
        """Kumihan戦略名の確認"""
        name = self.strategy.get_strategy_name()

        assert isinstance(name, str)
        assert "kumihan" in name.lower()

    def test_基本_kumihan_content_対応度(self):
        """Kumihanコンテンツ対応度の確認"""
        kumihan_content = "# title #content## kumihan format"
        markdown_content = "# Markdown title\n\nContent"
        plain_content = "Plain text content"

        kumihan_support = self.strategy.supports_content(kumihan_content)
        markdown_support = self.strategy.supports_content(markdown_content)
        plain_support = self.strategy.supports_content(plain_content)

        # Kumihanコンテンツが最も高い対応度
        assert kumihan_support > markdown_support
        assert kumihan_support > plain_support

    def test_基本_kumihan_parsing_実行(self):
        """Kumihanパーシング実行確認"""
        content = "# title #content##"
        result = self.strategy.parse(content, self.sample_context)

        # パース結果が返される（具体的な実装に依存）
        assert result is not None
        assert isinstance(result, (str, dict, list))

    def test_エラー_kumihan_parsing_例外(self):
        """Kumihanパーシング時の例外処理"""
        # 不正なコンテンツでの例外処理確認
        invalid_content = None

        with pytest.raises((ValueError, TypeError)):
            self.strategy.parse(invalid_content, self.sample_context)


class TestHTMLRenderingStrategy:
    """HTMLRenderingStrategy具体実装テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.strategy = HTMLRenderingStrategy()
        self.sample_context = {"output_format": "html", "theme": "default"}

    def test_基本_html_strategy_初期化(self):
        """HTML戦略の基本初期化"""
        strategy = HTMLRenderingStrategy()

        assert strategy is not None
        assert hasattr(strategy, "render")
        assert hasattr(strategy, "get_strategy_name")
        assert hasattr(strategy, "supports_output_format")

    def test_基本_html_strategy_名前(self):
        """HTML戦略名の確認"""
        name = self.strategy.get_strategy_name()

        assert isinstance(name, str)
        assert "html" in name.lower()

    def test_基本_html_format_対応度(self):
        """HTMLフォーマット対応度の確認"""
        html_support = self.strategy.supports_output_format("html")
        xml_support = self.strategy.supports_output_format("xml")
        markdown_support = self.strategy.supports_output_format("markdown")

        # HTMLフォーマットが最も高い対応度
        assert html_support > xml_support
        assert html_support > markdown_support
        assert html_support > 0.8  # 高い対応度

    def test_基本_html_rendering_実行(self):
        """HTMLレンダリング実行確認"""
        data = {"title": "Test", "content": "Test content"}
        result = self.strategy.render(data, self.sample_context)

        # レンダリング結果が返される
        assert result is not None
        assert isinstance(result, str)

    def test_エラー_html_rendering_例外(self):
        """HTMLレンダリング時の例外処理"""
        # 不正なデータでの例外処理確認
        invalid_data = None

        with pytest.raises((ValueError, TypeError)):
            self.strategy.render(invalid_data, self.sample_context)


class TestStrategyIntegration:
    """戦略システム統合テスト"""

    def test_統合_parsing_rendering_連携(self):
        """パーシングとレンダリング戦略の連携"""
        manager = StrategyManager()

        # 戦略登録
        parsing_strategy = KumihanParsingStrategy()
        rendering_strategy = HTMLRenderingStrategy()

        manager.register_parsing_strategy(parsing_strategy)
        manager.register_rendering_strategy(rendering_strategy)

        # パース→レンダーのワークフロー
        content = "# title #content##"
        parse_context = {"format": "kumihan"}
        render_context = {"output_format": "html"}

        parsed_data = manager.parse_content(content, parse_context)
        rendered_result = manager.render_content(parsed_data, render_context)

        # 両方の処理が正常完了
        assert parsed_data is not None
        assert rendered_result is not None
        assert isinstance(rendered_result, str)

    def test_統合_複数strategy_優先順位(self):
        """複数戦略登録時の優先順位確認"""
        manager = StrategyManager()

        # 異なる対応度の戦略を登録
        low_strategy = MockParsingStrategy("low", 0.3)
        high_strategy = MockParsingStrategy("high", 0.9)

        manager.register_parsing_strategy(low_strategy)
        manager.register_parsing_strategy(high_strategy)

        # 高い対応度の戦略が選択・実行される
        content = "test content"
        result = manager.parse_content(content)

        assert result == "high_parsed:test content"
        assert len(high_strategy.parse_calls) == 1
        assert len(low_strategy.parse_calls) == 0

    def test_統合_strategy_動的切り替え(self):
        """コンテンツに応じた戦略動的切り替え"""
        manager = StrategyManager()

        # 異なるコンテンツタイプに特化した戦略
        kumihan_strategy = MockParsingStrategy("kumihan_specialist", 0.5)
        markdown_strategy = MockParsingStrategy("markdown_specialist", 0.5)

        manager.register_parsing_strategy(kumihan_strategy)
        manager.register_parsing_strategy(markdown_strategy)

        # Kumihanコンテンツ処理
        kumihan_content = "# title #kumihan content##"
        result1 = manager.parse_content(kumihan_content)

        # Markdownコンテンツ処理
        markdown_content = "# Markdown Title\n\nmarkdown content"
        result2 = manager.parse_content(markdown_content)

        # コンテンツに応じて適切な戦略が選択される
        assert "kumihan_specialist" in result1
        assert "markdown_specialist" in result2
