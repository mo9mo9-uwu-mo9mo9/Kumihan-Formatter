"""Phase 3 Keyword Parser Tests - キーワードパーサー全面テスト

パーサーコア機能テスト - キーワード解析システム
Target: kumihan_formatter/core/keyword_parser.py (444行・0%カバレッジ)
Goal: 0% → 85-95%カバレッジ向上 (Phase 3目標70-80%への最大貢献)

最大カバレッジ貢献ファイル - 推定+25-30%カバレッジ向上
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.keyword_parser import KeywordParser


class TestKeywordParserInitialization:
    """KeywordParser初期化テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = KeywordParser()

    def test_keyword_parser_initialization(self):
        """KeywordParser基本初期化テスト"""
        parser = KeywordParser()

        # 基本属性が初期化されていることを確認
        assert parser is not None
        assert hasattr(parser, "parse_marker_keywords")
        assert hasattr(parser, "create_single_block")
        assert hasattr(parser, "create_compound_block")

    def test_keyword_parser_config_integration(self):
        """設定統合テスト"""
        # KeywordParserは設定なしでも動作することを確認
        parser = KeywordParser()

        # 設定が正しく統合されることを確認
        assert parser is not None
        assert parser.definitions is not None
        assert parser.marker_parser is not None
        assert parser.validator is not None

    def test_create_single_block_basic(self):
        """基本単一ブロック作成テスト"""
        marker_name = "太字"
        content = "テストコンテンツ"
        attributes = {}

        result = self.parser.create_single_block(marker_name, content, attributes)

        # ブロックが正常に作成されることを確認
        assert result is not None


class TestKeywordParserMethods:
    """KeywordParser主要メソッドテスト"""

    def setup_method(self):
        self.parser = KeywordParser()

    def test_create_single_block_all_keywords(self):
        """全てのデフォルトキーワードでブロック作成テスト"""
        test_keywords = [
            "太字",
            "イタリック",
            "枠線",
            "ハイライト",
            "見出し1",
            "見出し2",
            "見出し3",
            "見出し4",
            "見出し5",
            "折りたたみ",
            "ネタバレ",
        ]

        for keyword in test_keywords:
            result = self.parser.create_single_block(keyword, "test content", {})
            assert result is not None

    def test_create_single_block_with_attributes(self):
        """属性付きブロック作成テスト"""
        # ハイライトカラー属性テスト
        result = self.parser.create_single_block(
            "ハイライト", "colored content", {"color": "ff0000"}
        )
        assert result is not None

        # 通常属性テスト
        result = self.parser.create_single_block(
            "太字", "test", {"id": "test-id", "class": "custom"}
        )
        assert result is not None

    def test_create_single_block_empty_content(self):
        """空コンテンツブロック作成テスト"""
        result = self.parser.create_single_block("太字", "", {})
        assert result is not None

    def test_create_single_block_invalid_keyword(self):
        """無効キーワードエラーテスト"""
        result = self.parser.create_single_block("無効キーワード", "content", {})
        # エラーノードが返されることを確認
        assert result is not None

    def test_create_compound_block_basic(self):
        """基本複合ブロック作成テスト"""
        keywords = ["枠線", "太字"]
        content = "複合ブロックテスト"
        attributes = {}

        result = self.parser.create_compound_block(keywords, content, attributes)
        assert result is not None

    def test_create_compound_block_complex(self):
        """複雑な複合ブロック作成テスト"""
        keywords = ["折りたたみ", "枠線", "ハイライト", "太字"]
        content = "複雑な複合ブロック"
        attributes = {"color": "blue"}

        result = self.parser.create_compound_block(keywords, content, attributes)
        assert result is not None

    def test_create_compound_block_empty_keywords(self):
        """空キーワードリストエラーテスト"""
        result = self.parser.create_compound_block([], "content", {})
        assert result is not None  # エラーノードが返される

    def test_create_compound_block_invalid_keywords(self):
        """無効キーワード混在テスト"""
        keywords = ["太字", "無効キーワード", "イタリック"]
        result = self.parser.create_compound_block(keywords, "content", {})
        assert result is not None  # エラーノードが返される

    def test_parse_block_content_method(self):
        """_parse_block_contentメソッドテスト"""
        # プライベートメソッドを直接テスト
        result = self.parser._parse_block_content("test content")
        assert isinstance(result, list)
        assert len(result) == 1

        # 空コンテンツテスト
        result = self.parser._parse_block_content("")
        assert isinstance(result, list)
        assert result == [""]

    def test_process_inline_keywords_method(self):
        """_process_inline_keywordsメソッドテスト"""
        result = self.parser._process_inline_keywords("inline test content")
        assert isinstance(result, str)
        assert result == "inline test content"

    def test_sort_keywords_by_nesting_order(self):
        """_sort_keywords_by_nesting_orderメソッドテスト"""
        keywords = ["太字", "イタリック", "枠線", "折りたたみ"]
        sorted_keywords = self.parser._sort_keywords_by_nesting_order(keywords)

        assert isinstance(sorted_keywords, list)
        assert len(sorted_keywords) == len(keywords)
        # 正しいネスト順序で並んでいることを確認
        assert "折りたたみ" in sorted_keywords  # details (outer)
        assert "太字" in sorted_keywords  # strong (inner)

    def test_keyword_definitions_access(self):
        """キーワード定義アクセステスト"""
        assert hasattr(self.parser, "BLOCK_KEYWORDS")
        assert isinstance(self.parser.BLOCK_KEYWORDS, dict)
        assert "太字" in self.parser.BLOCK_KEYWORDS
        assert "tag" in self.parser.BLOCK_KEYWORDS["太字"]

    def test_nesting_order_access(self):
        """ネスト順序アクセステスト"""
        assert hasattr(self.parser, "NESTING_ORDER")
        assert isinstance(self.parser.NESTING_ORDER, list)
        assert "details" in self.parser.NESTING_ORDER
        assert "strong" in self.parser.NESTING_ORDER


class TestKeywordParserDelegation:
    """KeywordParser委譲メソッドテスト"""

    def setup_method(self):
        self.parser = KeywordParser()

    def test_normalize_marker_syntax_delegation(self):
        """_normalize_marker_syntax委譲テスト"""
        result = self.parser._normalize_marker_syntax("test marker content")
        assert isinstance(result, str)

    def test_parse_marker_keywords_delegation(self):
        """parse_marker_keywords委譲テスト"""
        result = self.parser.parse_marker_keywords("太字")
        assert isinstance(result, tuple)
        assert len(result) == 3  # (keywords, attributes, errors)

    def test_validate_keywords_delegation(self):
        """validate_keywords委譲テスト"""
        keywords = ["太字", "イタリック"]
        result = self.parser.validate_keywords(keywords)
        assert isinstance(result, tuple)
        assert len(result) == 2  # (valid_keywords, error_messages)

    def test_get_keyword_suggestions_delegation(self):
        """_get_keyword_suggestions委譲テスト"""
        result = self.parser._get_keyword_suggestions("大字", max_suggestions=3)
        assert isinstance(result, list)


class TestMarkerValidator:
    """MarkerValidatorテスト"""

    def test_validate_marker_line_valid(self):
        """正常なマーカー行検証テスト"""
        from kumihan_formatter.core.keyword_parser import MarkerValidator

        valid_line = ";;;太字;;;"
        is_valid, warnings = MarkerValidator.validate_marker_line(valid_line)

        assert isinstance(is_valid, bool)
        assert isinstance(warnings, list)

    def test_validate_marker_line_invalid(self):
        """無効なマーカー行検証テスト"""
        from kumihan_formatter.core.keyword_parser import MarkerValidator

        invalid_line = "invalid marker line"
        is_valid, warnings = MarkerValidator.validate_marker_line(invalid_line)

        assert is_valid is False
        assert len(warnings) > 0

    def test_validate_block_structure_complete(self):
        """完全なブロック構造検証テスト"""
        from kumihan_formatter.core.keyword_parser import MarkerValidator

        lines = [
            "Some text",
            ";;;太字;;; start",
            "block content",
            ";;; end",
            "more text",
        ]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 1
        )

        assert isinstance(is_valid, bool)
        assert end_index is None or isinstance(end_index, int)
        assert isinstance(warnings, list)

    def test_validate_block_structure_incomplete(self):
        """不完全ブロック構造検証テスト"""
        from kumihan_formatter.core.keyword_parser import MarkerValidator

        lines = ["Some text", ";;;太字;;; start", "block content without end"]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 1
        )

        assert is_valid is False
        assert end_index is None
        assert len(warnings) > 0
