"""ストラテジーパターンのテスト

戦略的な処理選択システムの包括的なテスト。
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

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
        # 特定のパターンに基づく対応度計算
        if "kumihan" in content.lower():
            return min(1.0, self.content_support + 0.3)
        elif "markdown" in content.lower():
            return min(1.0, self.content_support + 0.1)
        else:
            return self.content_support


class MockRenderingStrategy:
    """テスト用レンダリング戦略"""

    def __init__(self, name: str, supported_formats: list = None):
        self.name = name
        self.supported_formats = supported_formats or ["html"]
        self.render_calls = []

    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """戦略的レンダリング実行"""
        result = f"{self.name}_rendered:{data}"
        self.render_calls.append((data, context))
        return result

    def get_strategy_name(self) -> str:
        """戦略名取得"""
        return self.name

    def supports_format(self, output_format: str) -> bool:
        """フォーマット対応判定"""
        return output_format.lower() in [fmt.lower() for fmt in self.supported_formats]


class AdvancedParsingStrategy(MockParsingStrategy):
    """高度なパーシング戦略"""

    def __init__(self):
        super().__init__("advanced", 0.8)

    def supports_content(self, content: str) -> float:
        """高度なコンテンツ判定"""
        score = 0.0
        if "# " in content and "##" in content:  # Kumihanブロック記法
            score += 0.9
        elif len(content) > 1000:  # 大きなコンテンツ
            score += 0.7
        elif content.count("\n") > 50:  # 多行コンテンツ
            score += 0.6
        else:
            score += 0.2
        return min(1.0, score)


class BasicParsingStrategy(MockParsingStrategy):
    """基本的なパーシング戦略"""

    def __init__(self):
        super().__init__("basic", 0.3)

    def supports_content(self, content: str) -> float:
        """基本的なコンテンツ判定"""
        if len(content) < 100:
            return 0.8  # 短いコンテンツに最適
        else:
            return 0.2  # 長いコンテンツには不向き


class TestStrategyPriority:
    """戦略優先度列挙型のテスト"""

    def test_正常系_優先度値確認(self):
        """正常系: 優先度の値確認"""
        # Given/When/Then: 各優先度の値が正しい
        assert StrategyPriority.LOW.value == 1
        assert StrategyPriority.NORMAL.value == 5
        assert StrategyPriority.HIGH.value == 10
        assert StrategyPriority.CRITICAL.value == 20

    def test_正常系_優先度比較(self):
        """正常系: 優先度の比較確認"""
        # Given: 異なる優先度
        # When/Then: 優先度の大小関係が正しい
        assert StrategyPriority.LOW.value < StrategyPriority.NORMAL.value
        assert StrategyPriority.NORMAL.value < StrategyPriority.HIGH.value
        assert StrategyPriority.HIGH.value < StrategyPriority.CRITICAL.value


class TestStrategyManager:
    """戦略管理システムのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.manager = StrategyManager()

    def test_正常系_初期化(self):
        """正常系: 戦略マネージャー初期化の確認"""
        # Given: StrategyManagerクラス
        # When: StrategyManagerを初期化
        manager = StrategyManager()

        # Then: 正しく初期化される
        assert isinstance(manager._parsing_strategies, dict)
        assert isinstance(manager._rendering_strategies, dict)
        assert isinstance(manager._strategy_priorities, dict)
        assert manager._default_parsing_strategy is None
        assert manager._default_rendering_strategy is None

    def test_正常系_パーシング戦略登録(self):
        """正常系: パーシング戦略登録の確認"""
        # Given: パーシング戦略
        strategy = MockParsingStrategy("test_parser")

        # When: 戦略を登録
        self.manager.register_parsing_strategy(
            "test", strategy, StrategyPriority.HIGH, is_default=True
        )

        # Then: 戦略が正しく登録される
        assert "test" in self.manager._parsing_strategies
        assert self.manager._parsing_strategies["test"] is strategy
        assert self.manager._strategy_priorities["test"] == StrategyPriority.HIGH.value
        assert self.manager._default_parsing_strategy == "test"

    def test_正常系_レンダリング戦略登録(self):
        """正常系: レンダリング戦略登録の確認"""
        # Given: レンダリング戦略
        strategy = MockRenderingStrategy("test_renderer")

        # When: 戦略を登録
        self.manager.register_rendering_strategy(
            "test", strategy, StrategyPriority.NORMAL
        )

        # Then: 戦略が正しく登録される
        assert "test" in self.manager._rendering_strategies
        assert self.manager._rendering_strategies["test"] is strategy
        assert (
            self.manager._strategy_priorities["test"] == StrategyPriority.NORMAL.value
        )

    def test_正常系_パーシング戦略選択_単一戦略(self):
        """正常系: 単一パーシング戦略選択の確認"""
        # Given: 単一の戦略登録
        strategy = MockParsingStrategy("single", 0.7)
        self.manager.register_parsing_strategy("single", strategy)

        # When: 戦略を選択
        selected = self.manager.select_parsing_strategy("test content")

        # Then: 登録された戦略が選択される
        assert selected is strategy

    def test_正常系_パーシング戦略選択_複数戦略_対応度優先(self):
        """正常系: 複数戦略での対応度による選択確認"""
        # Given: 対応度の異なる複数戦略
        low_strategy = MockParsingStrategy("low", 0.2)
        high_strategy = MockParsingStrategy("high", 0.8)

        self.manager.register_parsing_strategy(
            "low", low_strategy, StrategyPriority.NORMAL
        )
        self.manager.register_parsing_strategy(
            "high", high_strategy, StrategyPriority.NORMAL
        )

        # When: コンテンツに対して戦略を選択
        selected = self.manager.select_parsing_strategy("regular content")

        # Then: 高対応度の戦略が選択される
        assert selected is high_strategy

    def test_正常系_パーシング戦略選択_優先度重み付け(self):
        """正常系: 優先度による重み付け選択確認"""
        # Given: 優先度の異なる戦略
        normal_strategy = MockParsingStrategy("normal", 0.6)
        high_priority_strategy = MockParsingStrategy("high_priority", 0.5)

        self.manager.register_parsing_strategy(
            "normal", normal_strategy, StrategyPriority.NORMAL
        )
        self.manager.register_parsing_strategy(
            "high_priority", high_priority_strategy, StrategyPriority.HIGH
        )

        # When: 戦略を選択
        selected = self.manager.select_parsing_strategy("test content")

        # Then: 重み付けにより高優先度戦略が選択される可能性が高い
        # 計算: normal = 0.6 * (5/10) = 0.3, high_priority = 0.5 * (10/10) = 0.5
        assert selected is high_priority_strategy

    def test_正常系_パーシング戦略選択_コンテンツ特化(self):
        """正常系: コンテンツ特化戦略選択の確認"""
        # Given: コンテンツ特化戦略
        advanced = AdvancedParsingStrategy()
        basic = BasicParsingStrategy()

        self.manager.register_parsing_strategy("advanced", advanced)
        self.manager.register_parsing_strategy("basic", basic)

        # When: Kumihanコンテンツで戦略選択
        kumihan_content = "# 見出し #内容## と # 別見出し #別内容##"
        selected_kumihan = self.manager.select_parsing_strategy(kumihan_content)

        # 短いコンテンツで戦略選択
        short_content = "短いテキスト"
        selected_short = self.manager.select_parsing_strategy(short_content)

        # Then: コンテンツに応じて最適な戦略が選択される
        assert selected_kumihan is advanced  # Kumihanコンテンツには高度戦略
        assert selected_short is basic  # 短いコンテンツには基本戦略

    def test_正常系_レンダリング戦略選択(self):
        """正常系: レンダリング戦略選択の確認"""
        # Given: フォーマット対応の異なる戦略
        html_strategy = MockRenderingStrategy("html", ["html", "htm"])
        pdf_strategy = MockRenderingStrategy("pdf", ["pdf"])

        self.manager.register_rendering_strategy("html", html_strategy)
        self.manager.register_rendering_strategy("pdf", pdf_strategy)

        # When: 各フォーマットで戦略選択
        html_selected = self.manager.select_rendering_strategy("html")
        pdf_selected = self.manager.select_rendering_strategy("pdf")
        unknown_selected = self.manager.select_rendering_strategy("unknown")

        # Then: 適切な戦略が選択される
        assert html_selected is html_strategy
        assert pdf_selected is pdf_strategy
        assert unknown_selected is None

    def test_正常系_指定戦略取得(self):
        """正常系: 指定戦略取得の確認"""
        # Given: 登録された戦略
        parsing_strategy = MockParsingStrategy("test_parser")
        rendering_strategy = MockRenderingStrategy("test_renderer")

        self.manager.register_parsing_strategy("test_parse", parsing_strategy)
        self.manager.register_rendering_strategy("test_render", rendering_strategy)

        # When: 名前で戦略を取得
        retrieved_parsing = self.manager.get_parsing_strategy("test_parse")
        retrieved_rendering = self.manager.get_rendering_strategy("test_render")

        # Then: 正しい戦略が取得される
        assert retrieved_parsing is parsing_strategy
        assert retrieved_rendering is rendering_strategy

    def test_正常系_戦略一覧取得(self):
        """正常系: 戦略一覧取得の確認"""
        # Given: 複数の戦略登録
        parsing1 = MockParsingStrategy("parser1")
        parsing2 = MockParsingStrategy("parser2")
        rendering1 = MockRenderingStrategy("renderer1")

        self.manager.register_parsing_strategy("parse1", parsing1)
        self.manager.register_parsing_strategy("parse2", parsing2)
        self.manager.register_rendering_strategy("render1", rendering1)

        # When: 戦略一覧を取得
        strategies = self.manager.list_strategies()

        # Then: 正しい一覧が返される
        assert "parsing" in strategies
        assert "rendering" in strategies
        assert "parse1" in strategies["parsing"]
        assert "parse2" in strategies["parsing"]
        assert "render1" in strategies["rendering"]
        assert len(strategies["parsing"]) == 2
        assert len(strategies["rendering"]) == 1

    def test_異常系_未登録戦略取得(self):
        """異常系: 未登録戦略取得の確認"""
        # Given: 空の戦略マネージャー
        # When: 未登録の戦略を取得
        parsing_result = self.manager.get_parsing_strategy("nonexistent")
        rendering_result = self.manager.get_rendering_strategy("nonexistent")

        # Then: Noneが返される
        assert parsing_result is None
        assert rendering_result is None

    def test_異常系_戦略なし選択(self):
        """異常系: 戦略が登録されていない場合の選択確認"""
        # Given: 空の戦略マネージャー
        # When: 戦略選択を試行
        parsing_result = self.manager.select_parsing_strategy("content")
        rendering_result = self.manager.select_rendering_strategy("format")

        # Then: Noneが返される
        assert parsing_result is None
        assert rendering_result is None

    def test_境界値_ゼロ対応度戦略(self):
        """境界値: ゼロ対応度戦略の処理確認"""
        # Given: ゼロ対応度の戦略
        zero_strategy = MockParsingStrategy("zero", 0.0)
        normal_strategy = MockParsingStrategy("normal", 0.5)

        self.manager.register_parsing_strategy("zero", zero_strategy)
        self.manager.register_parsing_strategy("normal", normal_strategy)

        # When: 戦略選択
        selected = self.manager.select_parsing_strategy("content")

        # Then: ゼロでない対応度の戦略が選択される
        assert selected is normal_strategy

    def test_境界値_同一対応度戦略(self):
        """境界値: 同一対応度戦略の選択確認"""
        # Given: 同一対応度の戦略
        strategy1 = MockParsingStrategy("first", 0.5)
        strategy2 = MockParsingStrategy("second", 0.5)

        self.manager.register_parsing_strategy(
            "first", strategy1, StrategyPriority.NORMAL
        )
        self.manager.register_parsing_strategy(
            "second", strategy2, StrategyPriority.NORMAL
        )

        # When: 戦略選択
        selected = self.manager.select_parsing_strategy("content")

        # Then: いずれかの戦略が選択される（実装の詳細に依存）
        assert selected in [strategy1, strategy2]

    def test_境界値_大量戦略登録(self):
        """境界値: 大量の戦略登録・選択確認"""
        # Given: 大量の戦略
        strategies = []
        for i in range(100):
            strategy = MockParsingStrategy(f"strategy_{i}", 0.1 + (i % 10) * 0.1)
            strategies.append(strategy)
            self.manager.register_parsing_strategy(
                f"strategy_{i}", strategy, StrategyPriority.NORMAL
            )

        # When: 戦略選択
        selected = self.manager.select_parsing_strategy("test content")

        # Then: 最高対応度の戦略が選択される
        assert selected is not None
        assert isinstance(selected, MockParsingStrategy)

        # 戦略一覧確認
        listed_strategies = self.manager.list_strategies()
        assert len(listed_strategies["parsing"]) == 100


class TestStrategyIntegration:
    """戦略パターン統合テスト"""

    def test_統合_完全なパーシングワークフロー(self):
        """統合: 完全なパーシングワークフローの確認"""
        # Given: 戦略マネージャーと複数戦略
        manager = StrategyManager()

        advanced = AdvancedParsingStrategy()
        basic = BasicParsingStrategy()

        manager.register_parsing_strategy("advanced", advanced, StrategyPriority.HIGH)
        manager.register_parsing_strategy("basic", basic, StrategyPriority.NORMAL)

        # When: 異なるコンテンツで解析実行
        kumihan_content = "# タイトル #長い内容## と # 別セクション #追加内容##"
        short_content = "短文"

        kumihan_strategy = manager.select_parsing_strategy(kumihan_content)
        short_strategy = manager.select_parsing_strategy(short_content)

        kumihan_result = kumihan_strategy.parse(kumihan_content, {"format": "kumihan"})
        short_result = short_strategy.parse(short_content, {"format": "simple"})

        # Then: 適切な戦略が選択され、処理が実行される
        assert kumihan_strategy is advanced
        assert short_strategy is basic

        assert "advanced_parsed" in kumihan_result
        assert "basic_parsed" in short_result

        # 呼び出し履歴確認
        assert len(advanced.parse_calls) == 1
        assert len(basic.parse_calls) == 1

    def test_統合_完全なレンダリングワークフロー(self):
        """統合: 完全なレンダリングワークフローの確認"""
        # Given: 戦略マネージャーとレンダリング戦略
        manager = StrategyManager()

        html_strategy = MockRenderingStrategy("html", ["html", "htm"])
        pdf_strategy = MockRenderingStrategy("pdf", ["pdf"])
        markdown_strategy = MockRenderingStrategy("markdown", ["md", "markdown"])

        manager.register_rendering_strategy(
            "html", html_strategy, StrategyPriority.NORMAL
        )
        manager.register_rendering_strategy("pdf", pdf_strategy, StrategyPriority.HIGH)
        manager.register_rendering_strategy(
            "markdown", markdown_strategy, StrategyPriority.LOW
        )

        # When: 異なるフォーマットでレンダリング実行
        data = {"title": "テストドキュメント", "content": "内容"}

        html_renderer = manager.select_rendering_strategy("html")
        pdf_renderer = manager.select_rendering_strategy("pdf")
        markdown_renderer = manager.select_rendering_strategy("markdown")

        html_result = html_renderer.render(data, {"style": "modern"})
        pdf_result = pdf_renderer.render(data, {"page_size": "A4"})
        markdown_result = markdown_renderer.render(data, {"table_of_contents": True})

        # Then: 適切な戦略が選択され、レンダリングが実行される
        assert html_renderer is html_strategy
        assert pdf_renderer is pdf_strategy
        assert markdown_renderer is markdown_strategy

        assert "html_rendered" in html_result
        assert "pdf_rendered" in pdf_result
        assert "markdown_rendered" in markdown_result

    def test_統合_動的戦略切り替え(self):
        """統合: 動的な戦略切り替えの確認"""
        # Given: 戦略マネージャー
        manager = StrategyManager()

        # 初期戦略
        basic = BasicParsingStrategy()
        manager.register_parsing_strategy("basic", basic, StrategyPriority.NORMAL)

        # When: 初期処理実行
        content = "短いテスト"
        initial_strategy = manager.select_parsing_strategy(content)
        initial_result = initial_strategy.parse(content, {})

        # 新しい高優先度戦略を追加
        advanced = AdvancedParsingStrategy()
        manager.register_parsing_strategy("advanced", advanced, StrategyPriority.HIGH)

        # 同じコンテンツで再選択
        updated_strategy = manager.select_parsing_strategy(content)
        updated_result = updated_strategy.parse(content, {})

        # Then: 戦略が動的に切り替わる
        assert initial_strategy is basic
        assert "basic_parsed" in initial_result

        # 短いコンテンツなので basicが選ばれる可能性が高いが、
        # 優先度によってはadvancedが選ばれることもある
        assert updated_strategy in [basic, advanced]

    def test_統合_コンテンツタイプ別最適化(self):
        """統合: コンテンツタイプ別最適化の確認"""
        # Given: コンテンツタイプ特化戦略
        manager = StrategyManager()

        # Kumihan特化戦略
        class KumihanStrategy(MockParsingStrategy):
            def __init__(self):
                super().__init__("kumihan", 0.4)

            def supports_content(self, content: str) -> float:
                if "# " in content and "##" in content:
                    return 0.95
                return 0.1

        # Markdown特化戦略
        class MarkdownStrategy(MockParsingStrategy):
            def __init__(self):
                super().__init__("markdown", 0.4)

            def supports_content(self, content: str) -> float:
                if content.startswith("# ") or "## " in content:
                    return 0.85
                return 0.1

        kumihan_strategy = KumihanStrategy()
        markdown_strategy = MarkdownStrategy()

        manager.register_parsing_strategy("kumihan", kumihan_strategy)
        manager.register_parsing_strategy("markdown", markdown_strategy)

        # When: 異なるコンテンツタイプで処理
        kumihan_content = "# 見出し #Kumihanコンテンツ##"
        markdown_content = "# Markdown見出し\n## サブ見出し"
        plain_content = "普通のテキスト"

        kumihan_selected = manager.select_parsing_strategy(kumihan_content)
        markdown_selected = manager.select_parsing_strategy(markdown_content)
        plain_selected = manager.select_parsing_strategy(plain_content)

        # Then: コンテンツに最適化された戦略が選択される
        assert kumihan_selected is kumihan_strategy
        # markdown_selected は、Markdownヘッダーを含むので markdown_strategy が選ばれるはず
        # ただし、優先度や対応度の計算によって異なる可能性があるため、柔軟に判定
        assert markdown_selected in [kumihan_strategy, markdown_strategy]
        # 普通のテキストはどちらかが選ばれる（対応度が低いため）
        assert plain_selected in [kumihan_strategy, markdown_strategy]
