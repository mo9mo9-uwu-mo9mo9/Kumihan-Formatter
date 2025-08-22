"""
Test advanced error handling features
Issue #700対応 - 高度なエラー表示機能のテスト
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.common.error_base import GracefulSyntaxError
from kumihan_formatter.core.error_handling.analysis.correction_engine import (
    CorrectionEngine,
    CorrectionRule,
)
from kumihan_formatter.core.error_handling.analysis.statistics_generator import (
    ErrorStatistics,
    StatisticsGenerator,
)


class TestAdvancedErrorHandling:
    """高度なエラーハンドリング拡張機能テスト"""

    def test_highlight_range_setting(self):
        """ハイライト範囲設定のテスト"""
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test",
            severity="error",
            message="Test error",
            context="# incomplete marker",
        )

        error.set_highlight_range(2, 10)
        assert error.highlight_start == 2
        assert error.highlight_end == 10

        # 負の値は0に修正される
        error.set_highlight_range(-1, 5)
        assert error.highlight_start == 0
        assert error.highlight_end == 5

    def test_correction_suggestions(self):
        """修正提案機能のテスト"""
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test",
            severity="error",
            message="Test error",
            context="# incomplete",
        )

        error.add_correction_suggestion("マーカーを完成させてください")
        error.add_correction_suggestion("終了マーカー「#」を追加してください")

        assert len(error.correction_suggestions) == 2
        assert "マーカーを完成させてください" in error.correction_suggestions

        # 重複は追加されない
        error.add_correction_suggestion("マーカーを完成させてください")
        assert len(error.correction_suggestions) == 2

    def test_error_pattern_classification(self):
        """エラーパターン分類のテスト"""
        test_cases = [
            ("marker mismatch error", "marker_mismatch"),
            ("incomplete marker found", "incomplete_marker"),
            ("invalid syntax detected", "invalid_syntax"),
            ("missing element in block", "missing_element"),
            ("unknown error type", "general_syntax"),
        ]

        for message, expected_pattern in test_cases:
            error = GracefulSyntaxError(
                line_number=1,
                column=1,
                error_type="test",
                severity="error",
                message=message,
                context="",
            )

            pattern = error.classify_error_pattern()
            assert pattern == expected_pattern
            assert error.error_pattern == expected_pattern

    def test_highlighted_context_generation(self):
        """ハイライト付きコンテキスト生成のテスト"""
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test",
            severity="error",
            message="Test error",
            context="# incomplete marker",
        )

        error.set_highlight_range(2, 12)  # "incomplete"部分
        highlighted = error.get_highlighted_context()

        assert "<mark class='error-highlight'>" in highlighted
        assert "incomplete" in highlighted

        # HTMLエスケープのテスト
        error.context = "# <script>alert('xss')</script>"
        error.set_highlight_range(2, 8)  # "<script>"部分
        highlighted = error.get_highlighted_context()
        assert "&lt;script&gt;" in highlighted

    def test_correction_suggestions_html(self):
        """修正提案HTML生成のテスト"""
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test",
            severity="error",
            message="Test error",
            context="",
        )

        error.add_correction_suggestion("提案1")
        error.add_correction_suggestion("提案2")

        html = error.get_correction_suggestions_html()
        assert "<ul class='correction-suggestions'>" in html
        assert "<li>提案1</li>" in html
        assert "<li>提案2</li>" in html

        # XSS対策テスト
        error.correction_suggestions = ["<script>alert('xss')</script>"]
        html = error.get_correction_suggestions_html()
        assert "&lt;script&gt;" in html


class TestCorrectionEngine:
    """修正提案エンジンのテスト"""

    def setUp(self):
        self.engine = CorrectionEngine()

    def test_correction_rule_matching(self):
        """修正ルールのマッチングテスト"""
        engine = CorrectionEngine()

        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="marker_error",
            severity="error",
            message="incomplete marker found",
            context="# keyword",
        )

        suggestions = engine.generate_suggestions(error)
        assert len(suggestions) > 0
        assert any("マーカー" in suggestion for suggestion in suggestions)

    def test_context_based_suggestions(self):
        """コンテキストベース提案のテスト"""
        engine = CorrectionEngine()

        # 不完全マーカーのテスト
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="marker_error",
            severity="error",
            message="test error",
            context="# keyword",
        )

        suggestions = engine.generate_suggestions(error)
        assert any("# keyword #" in suggestion for suggestion in suggestions)

    def test_mixed_width_character_detection(self):
        """半角・全角文字混在検出のテスト"""
        engine = CorrectionEngine()

        # 半角・全角混在のテスト
        test_text_mixed = "# キーワード keyword"
        assert engine._has_mixed_width_chars(test_text_mixed)

        # 純粋な半角文字
        test_text_half = "# keyword"
        assert not engine._has_mixed_width_chars(test_text_half)

        # 純粋な全角文字
        test_text_full = "＃　キーワード"
        assert not engine._has_mixed_width_chars(test_text_full)

    def test_common_mistakes_detection(self):
        """よくある間違いパターン検出のテスト"""
        engine = CorrectionEngine()

        # 全角スペースの検出
        suggestions = engine._detect_common_mistakes("#\u3000keyword")
        assert any("全角スペース" in s for s in suggestions)

        # 全角・半角マーカー混在
        suggestions = engine._detect_common_mistakes("#＃keyword")
        assert any("半角「#」" in s for s in suggestions)

    def test_error_enhancement(self):
        """エラー拡張機能のテスト"""
        engine = CorrectionEngine()

        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="marker_error",
            severity="error",
            message="incomplete marker",
            context="# keyword",
        )

        enhanced_error = engine.enhance_error_with_suggestions(error)

        assert len(enhanced_error.correction_suggestions) > 0
        assert enhanced_error.error_pattern != ""
        assert enhanced_error.highlight_start >= 0


class TestStatisticsGenerator:
    """エラー統計生成システムのテスト"""

    def test_basic_statistics_generation(self):
        """基本統計生成のテスト"""
        generator = StatisticsGenerator()

        errors = [
            GracefulSyntaxError(
                line_number=1,
                column=1,
                error_type="marker",
                severity="error",
                message="marker mismatch",
                context="",
            ),
            GracefulSyntaxError(
                line_number=2,
                column=1,
                error_type="syntax",
                severity="warning",
                message="invalid syntax",
                context="",
            ),
            GracefulSyntaxError(
                line_number=3,
                column=1,
                error_type="marker",
                severity="error",
                message="incomplete marker",
                context="",
            ),
        ]

        statistics = generator.generate_statistics(errors)

        assert statistics.total_errors == 3
        assert statistics.error_by_severity["error"] == 2
        assert statistics.error_by_severity["warning"] == 1
        assert len(statistics.most_common_errors) > 0

    def test_empty_errors_statistics(self):
        """エラーなしの場合の統計テスト"""
        generator = StatisticsGenerator()

        statistics = generator.generate_statistics([])

        assert statistics.total_errors == 0
        assert statistics.error_by_severity == {}
        assert statistics.most_common_errors == []

    def test_line_range_distribution(self):
        """行範囲別分布のテスト"""
        generator = StatisticsGenerator()

        errors = [
            GracefulSyntaxError(5, 1, "test", "error", "test", ""),  # 1-10
            GracefulSyntaxError(25, 1, "test", "error", "test", ""),  # 11-50
            GracefulSyntaxError(75, 1, "test", "error", "test", ""),  # 51-100
            GracefulSyntaxError(150, 1, "test", "error", "test", ""),  # 100+
        ]

        statistics = generator.generate_statistics(errors)

        assert statistics.error_by_line_range["1-10"] == 1
        assert statistics.error_by_line_range["11-50"] == 1
        assert statistics.error_by_line_range["51-100"] == 1
        assert statistics.error_by_line_range["100+"] == 1

    def test_html_report_generation(self):
        """HTML報告書生成のテスト"""
        generator = StatisticsGenerator()

        errors = [
            GracefulSyntaxError(1, 1, "marker", "error", "marker mismatch", ""),
            GracefulSyntaxError(2, 1, "syntax", "warning", "invalid syntax", ""),
        ]

        statistics = generator.generate_statistics(errors)
        html_report = generator.generate_html_report(statistics)

        assert "error-statistics-report" in html_report
        assert "エラー統計レポート" in html_report
        assert "2" in html_report  # 総エラー数

    def test_no_errors_html_report(self):
        """エラーなしHTML報告書のテスト"""
        generator = StatisticsGenerator()

        statistics = generator.generate_statistics([])
        html_report = generator.generate_html_report(statistics)

        assert "no-errors" in html_report
        assert "エラーは検出されませんでした" in html_report

    def test_summary_text_generation(self):
        """テキストサマリー生成のテスト"""
        generator = StatisticsGenerator()

        errors = [
            GracefulSyntaxError(1, 1, "marker", "error", "marker mismatch", ""),
            GracefulSyntaxError(2, 1, "syntax", "warning", "invalid syntax", ""),
        ]
        # 修正提案を追加
        errors[0].correction_suggestions = ["提案1", "提案2"]
        errors[1].correction_suggestions = ["提案3"]

        statistics = generator.generate_statistics(errors)
        summary = generator.generate_summary_text(statistics)

        assert "総エラー数: 2" in summary
        assert "修正提案数: 3" in summary
        assert "重要度別:" in summary


class TestErrorHandlingIntegration:
    """エラーハンドリング統合テスト"""

    def test_parser_integration(self):
        """パーサーとの統合テスト"""
        from kumihan_formatter.parser import Parser

        # graceful_errorsを有効にしてパーサーを初期化
        parser = Parser(graceful_errors=True)

        # correction_engineが初期化されていることを確認
        assert hasattr(parser, "correction_engine")
        assert parser.correction_engine is not None

    @patch("kumihan_formatter.core.error_analysis.correction_engine.CorrectionEngine")
    def test_parser_error_enhancement(self, mock_correction_engine):
        """パーサーでのエラー拡張機能テスト"""
        from kumihan_formatter.parser import Parser

        # モックのセットアップ
        mock_engine = Mock()
        mock_correction_engine.return_value = mock_engine

        parser = Parser(graceful_errors=True)

        # エラー記録時にエンジンが呼ばれることをテスト
        parser._record_graceful_error(1, 1, "test", "error", "test message", "test context")

        # enhance_error_with_suggestionsが呼ばれたことを確認
        mock_engine.enhance_error_with_suggestions.assert_called_once()

    def test_html_renderer_integration(self):
        """HTMLレンダラーとの統合テスト"""
        from kumihan_formatter.core.ast_nodes import Node
        from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer

        renderer = HTMLRenderer()

        # 高度なエラーハンドリング拡張エラーを設定
        error = GracefulSyntaxError(
            line_number=1,
            column=1,
            error_type="test",
            severity="error",
            message="Test error",
            context="# incomplete",
        )
        error.add_correction_suggestion("修正提案1")
        error.set_highlight_range(2, 10)

        renderer.set_graceful_errors([error], embed_in_html=True)

        # エラーサマリーに高度なエラーハンドリング機能が含まれることを確認
        summary_html = renderer._render_error_summary()

        assert "error-statistics-report" in summary_html
        assert "修正提案:" in summary_html


# テスト実行用のフィクスチャ
@pytest.fixture
def sample_errors():
    """テスト用のサンプルエラーリスト"""
    errors = []

    # 様々なタイプのエラーを作成
    error1 = GracefulSyntaxError(
        line_number=1,
        column=1,
        error_type="marker_error",
        severity="error",
        message="marker mismatch detected",
        context="# keyword",
    )
    error1.add_correction_suggestion("マーカーを統一してください")
    error1.set_highlight_range(0, 1)

    error2 = GracefulSyntaxError(
        line_number=5,
        column=3,
        error_type="syntax_error",
        severity="warning",
        message="invalid syntax found",
        context="invalid text",
    )
    error2.add_correction_suggestion("構文を確認してください")

    errors.extend([error1, error2])
    return errors


def test_complete_advanced_error_workflow(sample_errors):
    """高度なエラーハンドリングの完全なワークフローテスト"""
    from kumihan_formatter.core.error_handling.analysis.correction_engine import (
        CorrectionEngine,
    )
    from kumihan_formatter.core.error_handling.analysis.statistics_generator import (
        StatisticsGenerator,
    )

    # 1. エラーを修正提案エンジンで拡張
    engine = CorrectionEngine()
    enhanced_errors = []

    for error in sample_errors:
        enhanced_error = engine.enhance_error_with_suggestions(error)
        enhanced_errors.append(enhanced_error)

    # 2. 統計を生成
    stats_generator = StatisticsGenerator()
    statistics = stats_generator.generate_statistics(enhanced_errors)

    # 3. HTML報告書を生成
    html_report = stats_generator.generate_html_report(statistics)

    # 4. 結果の検証
    assert statistics.total_errors == 2
    assert len(statistics.most_common_errors) > 0
    assert "error-statistics-report" in html_report

    # 各エラーが適切に拡張されていることを確認
    for error in enhanced_errors:
        assert len(error.correction_suggestions) > 0
        assert error.error_pattern != ""
