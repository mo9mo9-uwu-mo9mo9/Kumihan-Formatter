"""
Test cases for basic Kumihan notation system.

Tests cover inline and block format notation parsing and validation.
"""

import pytest
from pathlib import Path

from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser
from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


@pytest.mark.unit
@pytest.mark.notation
class TestBasicNotation:
    """Basic notation parsing and validation tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.keyword_definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.keyword_definitions)
        self.validator = KumihanSyntaxValidator()
    
    def test_inline_notation_deprecated_error(self):
        """Test that inline notation is properly rejected in v3.0.0."""
        # v3.0.0では単一行記法は完全廃止
        deprecated_texts = [
            "これは#太字 重要な情報# です",
            "#太字 コンテンツ#",
            "#見出し1 タイトル#",
            "#下線 強調テキスト##"
        ]
        
        for text in deprecated_texts:
            # パーサーがこれらを適切に拒否することをテスト
            errors = self.validator.validate_text(text)
            # エラーが発生することを期待（単一行記法廃止）
            assert len(errors) > 0, f"単一行記法 '{text}' はv3.0.0でエラーになるべきです"
    
    def test_block_notation_basic_v3(self):
        """Test basic block notation parsing in v3.0.0."""
        text = """#太字#
重要な情報
##"""
        result = self.parser.parse(text)
        
        assert result is not None
        # v3.0.0ではブロック記法のみサポート
        # パーサーがブロック記法を適切に処理することをテスト
    
    def test_block_notation_basic(self):
        """Test basic block notation parsing."""
        text = """#見出し1
タイトルテキスト
#"""
        result = self.parser.parse(text)
        
        assert result is not None
        assert "見出し1" in result.markers
        assert "タイトルテキスト" in result.content
    
    def test_block_notation_multiline(self):
        """Test block notation with multiple lines."""
        text = """#太字
複数行の
重要な情報が
ここにあります
#"""
        result = self.parser.parse(text)
        
        assert result is not None
        assert "太字" in result.markers
        assert "複数行の" in result.content
        assert "重要な情報が" in result.content
    
    def test_empty_notation_content(self):
        """Test notation with empty content."""
        text = "#太字 #"
        result = self.parser.parse(text)
        
        assert result is not None
        assert "太字" in result.markers
        assert result.content.strip() == ""
        
    def test_notation_with_special_characters(self):
        """Test notation containing special characters."""
        text = "#太字 特殊文字!@#$%^&*()#"
        result = self.parser.parse(text)
        
        assert result is not None
        assert "太字" in result.markers
        assert "特殊文字!@#$%^&*()" in result.content
        
    def test_notation_with_japanese_punctuation(self):
        """Test notation with Japanese punctuation marks."""
        text = "#太字 これは、重要な「情報」です。#"
        result = self.parser.parse(text)
        
        assert result is not None
        assert "太字" in result.markers
        assert "これは、重要な「情報」です。" in result.content
    
    def test_nested_notation_simple(self):
        """Test simple nested notation structures."""
        text = """#太字
外側の内容
#下線 内側の内容#
続きの内容
#"""
        result = self.parser.parse(text)
        
        # Should handle nested structures appropriately
        assert result is not None
        assert len(result.markers) >= 1
    
    def test_syntax_validation_valid_notation(self):
        """Test syntax validation for valid notation."""
        text = "#太字 有効な記法です#"
        errors = self.validator.validate_text(text)
        
        # Should pass validation with no errors
        assert len(errors) == 0
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in notation."""
        text = "#  太字   重要な情報   #"
        result = self.parser.parse(text)
        
        assert result is not None
        assert "太字" in result.markers
        # Content should preserve internal whitespace
        assert "重要な情報" in result.content
    
    def test_keyword_definitions_loading(self):
        """Test keyword definitions are properly loaded."""
        keywords = self.keyword_definitions.get_all_keywords()
        
        # Should have default keywords available
        assert len(keywords) > 0
        assert "太字" in keywords or "見出し1" in keywords
    
    def test_marker_boundary_detection(self):
        """Test proper detection of marker boundaries."""
        text = "前の文章#太字 重要#後の文章"
        result = self.parser.parse(text)
        
        assert result is not None
        # Should properly detect boundaries without including surrounding text
        assert "前の文章" not in result.content
        assert "後の文章" not in result.content


@pytest.mark.unit
@pytest.mark.notation
class TestDecorationNotation:
    """Decoration-specific notation tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.keyword_definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.keyword_definitions)
        self.validator = KumihanSyntaxValidator()
    
    @pytest.mark.parametrize("decoration,content", [
        ("太字", "重要な情報"),
        ("下線", "強調テキスト"),
        ("斜体", "イタリック文字"),
        ("見出し1", "メインタイトル"),
        ("見出し2", "サブタイトル"),
        ("リスト", "項目内容"),
    ])
    def test_specific_decorations(self, decoration, content):
        """Test specific decoration types."""
        text = f"#{decoration} {content}#"
        result = self.parser.parse(text)
        
        assert result is not None
        assert decoration in result.markers
        assert content in result.content
    
    def test_decoration_case_sensitivity(self):
        """Test decoration name case sensitivity."""
        text_lower = "#太字 テスト#"
        text_upper = "#太字 テスト#"  # Same in Japanese
        
        result_lower = self.parser.parse(text_lower)
        result_upper = self.parser.parse(text_upper)
        
        # Both should be parsed successfully
        assert result_lower is not None
        assert result_upper is not None
        
    def test_unknown_decoration(self):
        """Test handling of unknown decoration types."""
        text = "#未知の装飾 テスト内容#"
        
        # Should handle gracefully - either parse or validate appropriately
        result = self.parser.parse(text)
        errors = self.validator.validate_text(text)
        
        # Either parsing should work (flexible) or validation should flag it
        assert result is not None or len(errors) > 0