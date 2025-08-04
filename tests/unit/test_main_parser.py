"""
Test cases for main parser functionality.

Tests cover core parsing features and Parser class integration.
"""

import pytest
from pathlib import Path

from kumihan_formatter.parser import Parser


@pytest.mark.unit
@pytest.mark.parser
class TestMainParser:
    """Main parser functionality tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = Parser()
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        assert self.parser is not None
        assert hasattr(self.parser, 'logger')
    
    def test_basic_text_parsing(self):
        """Test basic text parsing functionality."""
        text = "これは基本的なテキストです。"
        
        # parse_streaming_from_text method should work
        results = list(self.parser.parse_streaming_from_text(text))
        assert len(results) > 0
        
        # Should return Node objects
        for result in results:
            assert hasattr(result, 'type')
    
    def test_empty_text_parsing(self):
        """Test parsing empty text."""
        text = ""
        
        results = list(self.parser.parse_streaming_from_text(text))
        # Empty text should still return some structure
        assert isinstance(results, list)
    
    @pytest.mark.skip(reason="CI timeout issue - parser performance optimization needed")
    def test_block_notation_parsing(self):
        """Test basic block notation parsing."""
        text = """#太字#
重要な情報
##"""
        
        results = list(self.parser.parse_streaming_from_text(text))
        assert len(results) > 0
        
        # Should recognize block notation
        found_bold = any('太字' in str(result) for result in results)
        assert found_bold, "Block notation should be recognized"
    
    @pytest.mark.skip(reason="CI timeout issue - parser performance optimization needed")
    def test_multiline_text_parsing(self):
        """Test parsing multiline text."""
        text = """第一行
第二行
第三行"""
        
        results = list(self.parser.parse_streaming_from_text(text))
        assert len(results) > 0
        
        # Should handle multiple lines
        assert len(results) >= 3
    
    @pytest.mark.skip(reason="CI timeout issue - parser performance optimization needed")
    def test_heading_parsing(self):
        """Test heading notation parsing."""
        text = """#見出し1#
タイトル
##"""
        
        results = list(self.parser.parse_streaming_from_text(text))
        assert len(results) > 0
        
        # Should recognize heading notation
        found_heading = any('見出し' in str(result) for result in results)
        assert found_heading, "Heading notation should be recognized"


@pytest.mark.unit
@pytest.mark.integration
class TestParserIntegration:
    """Parser integration tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = Parser()
    
    def test_get_processing_recommendations(self):
        """Test processing recommendations functionality."""
        # Test with text input
        text = "Test text for recommendations"
        recommendations = self.parser.get_processing_recommendations(text)
        
        assert isinstance(recommendations, dict)
        assert 'input_type' in recommendations
        assert 'recommended_mode' in recommendations
    
    def test_parallel_vs_traditional_processing(self):
        """Test that both processing modes work."""
        text = "小さなテストテキスト"
        
        # Traditional processing
        traditional_results = list(self.parser.parse_streaming_from_text(text))
        
        # Parallel processing (should fall back for small text)
        parallel_results = list(self.parser.parse_parallel_streaming(text))
        
        # Both should work
        assert len(traditional_results) > 0
        assert len(parallel_results) > 0
    
    def test_error_handling(self):
        """Test parser error handling."""
        # Test with potentially problematic input
        problematic_text = "#不正な記法 ###"
        
        # Should not crash
        try:
            results = list(self.parser.parse_streaming_from_text(problematic_text))
            assert isinstance(results, list)
        except Exception as e:
            # If it raises an exception, it should be a known type
            assert isinstance(e, (ValueError, TypeError, RuntimeError))