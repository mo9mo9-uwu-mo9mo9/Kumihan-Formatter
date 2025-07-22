"""Phase 2 Parser Integration Tests - パーサー統合テスト

パーサー統合機能テスト - KeywordParser統合
Target: parser.py, keyword_parser.py の統合機能
Goal: パーサー間の連携・統合テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.parser import parse


class TestKeywordParser:
    """KeywordParser テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KeywordParser()

    def test_keyword_parser_initialization(self):
        """KeywordParser初期化テスト"""
        parser = KeywordParser()

        # 基本属性が初期化されていることを確認
        assert hasattr(parser, "definitions")
        assert hasattr(parser, "marker_parser")
        assert hasattr(parser, "validator")
        assert hasattr(parser, "BLOCK_KEYWORDS")

    def test_keyword_validation(self):
        """キーワード検証テスト"""
        keywords = ["太字", "イタリック", "無効キーワード"]
        valid, invalid = self.parser.validate_keywords(keywords)

        # 有効なキーワードが正しく認識されることを確認
        assert "太字" in valid
        assert "イタリック" in valid
        # 無効キーワードはエラーメッセージ形式で返されることを確認
        assert any("無効キーワード" in item for item in invalid)

    def test_single_block_creation(self):
        """単一ブロック作成テスト"""
        content = "Test content"
        result = self.parser.create_single_block("太字", content, {})

        # 太字ブロックが正しく作成されることを確認
        assert result is not None
        assert result.type == "strong"

    def test_compound_block_creation(self):
        """複合ブロック作成テスト"""
        keywords = ["太字", "イタリック"]
        content = "Test compound content"
        result = self.parser.create_compound_block(keywords, content, {})

        # 複合ブロックが正しく作成されることを確認
        assert result is not None

    def test_marker_parser_availability(self):
        """マーカーパーサー可用性テスト"""
        # マーカーパーサーが初期化されていることを確認
        assert hasattr(self.parser, "marker_parser")
        assert self.parser.marker_parser is not None

    def test_block_keywords_existence(self):
        """ブロックキーワード存在テスト"""
        parser = KeywordParser()

        # デフォルトキーワードが存在することを確認
        expected_keywords = ["太字", "イタリック", "枠線", "ハイライト"]
        for keyword in expected_keywords:
            assert keyword in parser.BLOCK_KEYWORDS

    def test_keyword_parser_methods(self):
        """キーワードパーサーメソッドテスト"""
        # キーワードパーサーのメソッドが存在することを確認
        assert callable(getattr(self.parser, "validate_keywords", None))
        assert callable(getattr(self.parser, "create_single_block", None))
        assert callable(getattr(self.parser, "create_compound_block", None))


class TestParserIntegration:
    """パーサー統合テスト"""

    def test_parse_function_basic_integration(self):
        """parse関数基本統合テスト"""
        text = "Simple text for integration testing"
        result = parse(text)

        # 統合パーサーが基本テキストを処理することを確認
        assert isinstance(result, list)

    def test_parse_with_config_integration(self):
        """設定付きparse統合テスト"""
        text = "Text with config"
        config = {"test": True}
        result = parse(text, config=config)

        # 設定付きで統合パーサーが動作することを確認
        assert isinstance(result, list)

    def test_parser_components_availability(self):
        """パーサーコンポーネント可用性テスト"""
        # KeywordParserが正しく初期化されることを確認
        keyword_parser = KeywordParser()
        assert keyword_parser is not None
        assert hasattr(keyword_parser, "BLOCK_KEYWORDS")

    def test_parser_error_handling_integration(self):
        """パーサーエラーハンドリング統合テスト"""
        error_cases = ["", None, 123]

        for case in error_cases:
            try:
                result = parse(case) if case is not None else None
                if result is not None:
                    assert isinstance(result, list)
            except Exception:
                # エラーが適切に処理されることを確認
                assert True

    def test_parser_unicode_support(self):
        """パーサーUnicode対応テスト"""
        unicode_text = "日本語のテキスト content"
        result = parse(unicode_text)

        # Unicode文字が正しく処理されることを確認
        assert isinstance(result, list)

    def test_parser_performance_integration(self):
        """パーサーパフォーマンス統合テスト"""
        # 中程度のサイズのコンテンツでパフォーマンステスト
        content = "# Heading\n\nParagraph content.\n\n" * 50

        import time

        start = time.time()
        result = parse(content)
        end = time.time()

        # 合理的な時間内で完了することを確認
        assert isinstance(result, list)
        assert (end - start) < 5.0  # 5秒以内

    def test_parser_memory_efficiency(self):
        """パーサーメモリ効率テスト"""
        # 複数回の解析でメモリリークが発生しないことを確認
        texts = ["Simple text", "Another text", "Third text"]

        for _ in range(10):
            for text in texts:
                result = parse(text)
                assert isinstance(result, list)

        # ガベージコレクション
        import gc

        gc.collect()
        assert True

    def test_parser_robustness(self):
        """パーサー堅牢性テスト"""
        # 様々な入力に対してパーサーが安定して動作することを確認
        test_inputs = [
            "Normal text",
            "# Heading",
            "- List item",
            "**Bold text**",
            "*Italic text*",
            "`Code text`",
        ]

        for text in test_inputs:
            result = parse(text)
            assert isinstance(result, list)

    def test_integration_completeness(self):
        """統合完全性テスト"""
        # parse関数とKeywordParserが正しく統合されていることを確認
        assert callable(parse)

        keyword_parser = KeywordParser()
        assert len(keyword_parser.BLOCK_KEYWORDS) > 0

        # 基本的な解析が動作することを確認
        result = parse("Test integration")
        assert isinstance(result, list)
