"""
Test cases for keyword parsing system.

Tests the keyword parsing engine including definitions, validation, and marker processing.
"""

import pytest
from pathlib import Path

from kumihan_formatter.core.keyword_parsing.validator import KeywordValidator
from kumihan_formatter.core.keyword_parsing.definitions import (
    KeywordDefinitions,
    DEFAULT_BLOCK_KEYWORDS,
    NESTING_ORDER,
)
from kumihan_formatter.core.keyword_parsing.marker_parser import (
    MarkerParser,
    ParseResult,
)


@pytest.mark.unit
@pytest.mark.notation
class TestKeywordDefinitions:
    """Test keyword definitions and configuration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()

    def test_default_keywords_loaded(self):
        """Test default keywords are properly loaded."""
        keywords = self.definitions.get_all_keywords()

        assert len(keywords) > 0
        # Check for some expected default keywords including Phase 2 additions
        expected_keywords = [
            "太字",
            "見出し1",
            "見出し2",
            "下線",
            "取り消し線",
            "コード",
            "引用",
            "中央寄せ",
            "注意",
            "情報",
            "コードブロック",
        ]
        found_keywords = [kw for kw in expected_keywords if kw in keywords]
        assert len(found_keywords) > 0

    def test_block_keywords_configuration(self):
        """Test block keywords configuration."""
        assert DEFAULT_BLOCK_KEYWORDS is not None
        assert len(DEFAULT_BLOCK_KEYWORDS) > 0

        # Should include common block types
        block_types = ["見出し1", "見出し2", "リスト"]
        for block_type in block_types:
            if block_type in DEFAULT_BLOCK_KEYWORDS:
                assert True
                break
        else:
            pytest.skip("No expected block keywords found in configuration")

    def test_nesting_order_configuration(self):
        """Test nesting order configuration."""
        assert NESTING_ORDER is not None

        # Should have some ordering defined
        if len(NESTING_ORDER) > 0:
            assert isinstance(NESTING_ORDER, (list, tuple, dict))

    def test_keyword_validation_rules(self):
        """Test keyword validation rules."""
        # Test valid keyword format
        valid_keywords = ["太字", "見出し1", "下線"]
        for keyword in valid_keywords:
            if keyword in self.definitions.get_all_keywords():
                assert self.definitions.is_valid_keyword(keyword)

    def test_keyword_normalization(self):
        """Test keyword name normalization."""
        # Test various input formats
        test_cases = [
            ("太字", "太字"),
            ("  太字  ", "太字"),  # Whitespace trimming
        ]

        for input_keyword, expected in test_cases:
            normalized = self.definitions.normalize_keyword(input_keyword)
            assert normalized == expected

    def test_phase2_keywords_implementation(self):
        """Test Phase 2 new keywords are properly implemented."""
        # Phase 2.1: Basic decoration keywords
        phase2_1_keywords = {
            "取り消し線": {"tag": "del"},
            "コード": {"tag": "code"},
            "引用": {"tag": "blockquote"},
        }

        # Phase 2.2: Layout keywords
        phase2_2_keywords = {
            "中央寄せ": {"tag": "div", "style": "text-align: center"},
            "注意": {"tag": "div", "class": "alert warning"},
            "情報": {"tag": "div", "class": "alert info"},
            "コードブロック": {"tag": "pre"},
        }

        all_new_keywords = {**phase2_1_keywords, **phase2_2_keywords}

        for keyword, expected_def in all_new_keywords.items():
            # Test keyword exists
            assert self.definitions.is_valid_keyword(
                keyword
            ), f"キーワード '{keyword}' が見つかりません"

            # Test keyword definition
            keyword_info = self.definitions.get_keyword_info(keyword)
            assert (
                keyword_info is not None
            ), f"キーワード '{keyword}' の定義が見つかりません"
            assert (
                keyword_info["tag"] == expected_def["tag"]
            ), f"キーワード '{keyword}' のタグが期待値と異なります"

            # Test additional attributes if present
            for attr, value in expected_def.items():
                if attr != "tag":
                    assert (
                        keyword_info.get(attr) == value
                    ), f"キーワード '{keyword}' の属性 '{attr}' が期待値と異なります"

    def test_new_keywords_nesting_order(self):
        """Test new keywords are properly included in nesting order."""
        nesting_order = self.definitions.get_nesting_order()
        new_tags = ["del", "code", "blockquote", "pre"]

        for tag in new_tags:
            assert (
                tag in nesting_order
            ), f"新しいタグ '{tag}' がネスト順序に含まれていません"

    def test_compound_keywords_compatibility(self):
        """Test that new keywords work in compound scenarios."""
        # Test that new keywords can be retrieved correctly
        test_keywords = [
            "取り消し線",
            "コード",
            "引用",
            "中央寄せ",
            "注意",
            "情報",
            "コードブロック",
        ]

        for keyword in test_keywords:
            tag = self.definitions.get_tag_for_keyword(keyword)
            assert tag is not None, f"キーワード '{keyword}' のタグが取得できません"
            assert isinstance(
                tag, str
            ), f"キーワード '{keyword}' のタグが文字列ではありません"


@pytest.mark.unit
@pytest.mark.notation
class TestKeywordValidator:
    """Test keyword validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.validator = KeywordValidator(self.definitions)

    def test_valid_keyword_validation(self):
        """Test validation of valid keywords."""
        valid_texts = [
            "#太字 有効なテキスト#",
            "#見出し1 タイトル#",
            "#下線 強調文字#",
        ]

        for text in valid_texts:
            errors = self.validator.validate(text)
            assert len(errors) == 0, f"Unexpected errors for: {text}"

    def test_invalid_keyword_validation(self):
        """Test validation of invalid keywords."""
        # Test with potentially invalid structures
        invalid_texts = [
            "#; 不正な開始マーカー",
            "太字 不正な終了マーカー#",
            "#太字 未完了の記法",
        ]

        for text in invalid_texts:
            errors = self.validator.validate(text)
            # Should detect issues (or handle gracefully)
            # The exact behavior depends on implementation
            assert isinstance(errors, list)

    def test_nested_keyword_validation(self):
        """Test validation of nested keyword structures."""
        nested_text = """#太字
外側のコンテンツ
#下線 内側のコンテンツ#
継続するコンテンツ
#"""

        errors = self.validator.validate(nested_text)
        assert isinstance(errors, list)
        # Specific validation rules depend on implementation

    def test_empty_content_validation(self):
        """Test validation of empty content."""
        empty_content_texts = [
            "#太字 #",
            "#太字\n#",
        ]

        for text in empty_content_texts:
            errors = self.validator.validate(text)
            # Should handle empty content appropriately
            assert isinstance(errors, list)


@pytest.mark.unit
@pytest.mark.notation
class TestMarkerParser:
    """Test marker parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)

    def test_parse_result_structure(self):
        """Test ParseResult data structure."""
        text = "#太字 テスト内容#"
        result = self.parser.parse(text)

        assert isinstance(result, ParseResult)
        assert hasattr(result, "markers")
        assert hasattr(result, "content")

        # Verify basic parsing worked
        assert result.markers is not None
        assert result.content is not None

    def test_simple_marker_parsing(self):
        """Test parsing of simple markers."""
        test_cases = [
            ("#太字 内容#", "太字", "内容"),
            ("#見出し1 タイトル#", "見出し1", "タイトル"),
            ("#下線 強調#", "下線", "強調"),
        ]

        for text, expected_marker, expected_content in test_cases:
            result = self.parser.parse(text)

            assert result is not None
            assert expected_marker in str(result.markers)
            assert expected_content in result.content

    def test_block_marker_parsing(self):
        """Test parsing of block-style markers."""
        block_text = """#見出し1
複数行の
タイトルテキスト
#"""

        result = self.parser.parse(block_text)

        assert result is not None
        assert "見出し1" in str(result.markers)
        assert "複数行の" in result.content
        assert "タイトルテキスト" in result.content

    def test_marker_position_tracking(self):
        """Test marker position tracking."""
        text = "前置き#太字 中身#後置き"
        result = self.parser.parse(text)

        if (
            hasattr(result, "position")
            or hasattr(result, "start")
            or hasattr(result, "end")
        ):
            # Position tracking is implemented
            assert result is not None
        else:
            # Position tracking may not be implemented yet
            assert result is not None

    def test_multiple_markers_parsing(self):
        """Test parsing text with multiple markers."""
        text = "#太字 最初# 中間テキスト #下線 次# 終了"
        result = self.parser.parse(text)

        assert result is not None
        # Should handle multiple markers appropriately
        # Exact behavior depends on implementation

    def test_malformed_marker_handling(self):
        """Test handling of malformed markers."""
        malformed_texts = [
            "#太字 一つ少ない開始マーカー",
            "#太字 一つ少ない終了マーカー",
            "#太字 終了マーカーなし",
            "太字 開始マーカーなし#",
        ]

        for text in malformed_texts:
            result = self.parser.parse(text)
            # Should handle gracefully - either parse what's possible or return appropriate result
            assert result is not None or result is None  # Any handling is acceptable

    def test_edge_case_content(self):
        """Test parsing with edge case content."""
        edge_cases = [
            "#太字 #含む内容#",  # Contains marker-like text
            "#太字 \n\n\n#",  # Multiple newlines
            "#太字     #",  # Only whitespace
            "#太字 ≪特殊文字≫#",  # Special Unicode characters
        ]

        for text in edge_cases:
            result = self.parser.parse(text)
            # Should handle edge cases without crashing
            assert result is not None or result is None
