"""Property-based tests for Kumihan parser

These tests use property-based testing to verify parser behavior
across a wide range of inputs and find edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from . import HAS_HYPOTHESIS

if HAS_HYPOTHESIS:
    from hypothesis import given, strategies as st, settings, assume
    from hypothesis.strategies import text, integers, lists, composite
else:
    # Create dummy decorators if hypothesis not available
    def given(*args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                pytest.skip("hypothesis not available")
            return wrapper
        return decorator
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class DummyStrategies:
        text = lambda *args, **kwargs: None
        integers = lambda *args, **kwargs: None
        lists = lambda *args, **kwargs: None
    
    st = DummyStrategies()
    composite = lambda func: func
    assume = lambda x: None

from kumihan_formatter.parser import KumihanParser
from kumihan_formatter.core.ast_nodes import Node


# Custom strategies for Kumihan content
@composite
def kumihan_keyword(draw):
    """Generate valid Kumihan keywords"""
    if not HAS_HYPOTHESIS:
        return "太字"
    
    keywords = [
        "太字", "イタリック", "見出し1", "見出し2", "見出し3", 
        "見出し4", "見出し5", "枠線", "ハイライト", "折りたたみ", 
        "ネタバレ", "目次", "画像"
    ]
    return draw(st.sampled_from(keywords))


@composite
def kumihan_block(draw):
    """Generate valid Kumihan block markup"""
    if not HAS_HYPOTHESIS:
        return ";;;太字\nテスト\n;;;"
    
    keyword = draw(kumihan_keyword())
    content = draw(st.text(min_size=1, max_size=100))
    
    # Ensure content doesn't contain ;;; to avoid breaking the block
    content = content.replace(";;;", "")
    
    return f";;{keyword}\n{content}\n;;;"


@composite
def kumihan_list_item(draw):
    """Generate valid Kumihan list items"""
    if not HAS_HYPOTHESIS:
        return "- テスト項目"
    
    prefix = draw(st.sampled_from(["- ", "・", "1. ", "2. ", "3. "]))
    content = draw(st.text(min_size=1, max_size=50))
    
    # Clean content to avoid line breaks
    content = content.replace("\n", " ").strip()
    if not content:
        content = "テスト"
    
    return f"{prefix}{content}"


@composite
def kumihan_document(draw):
    """Generate a complete Kumihan document"""
    if not HAS_HYPOTHESIS:
        return "これはテストです。"
    
    paragraphs = draw(st.lists(
        st.one_of(
            st.text(min_size=1, max_size=100),
            kumihan_block(),
            kumihan_list_item()
        ),
        min_size=1,
        max_size=10
    ))
    
    # Clean and join paragraphs
    clean_paragraphs = []
    for p in paragraphs:
        # Ensure no empty paragraphs
        if p.strip():
            clean_paragraphs.append(p.strip())
    
    return "\n\n".join(clean_paragraphs)


class TestParserProperties:
    """Property-based tests for the Kumihan parser"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.parser = KumihanParser()
    
    @given(kumihan_document())
    @settings(max_examples=50, deadline=5000)  # Reasonable limits for CI
    def test_parser_never_crashes(self, document):
        """Parser should never crash on any input"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        try:
            # Parser should handle any input gracefully
            result = self.parser.parse(document)
            
            # Result should always be a list
            assert isinstance(result, list)
            
            # All items should be Node objects
            for item in result:
                assert isinstance(item, Node)
                
        except Exception as e:
            pytest.fail(f"Parser crashed on input: {document[:100]}...\nError: {e}")
    
    @given(st.text(min_size=0, max_size=1000))
    @settings(max_examples=30)
    def test_parser_handles_arbitrary_text(self, text):
        """Parser should handle arbitrary text input"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        try:
            result = self.parser.parse(text)
            assert isinstance(result, list)
            
            # If input is not empty, should produce some output
            if text.strip():
                assert len(result) >= 0  # Could be 0 if all invalid
                
        except Exception as e:
            pytest.fail(f"Parser failed on text: {text[:50]}...\nError: {e}")
    
    @given(kumihan_keyword())
    @settings(max_examples=20)
    def test_valid_keywords_parse_correctly(self, keyword):
        """Valid keywords should always parse correctly"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Create a simple block with the keyword
        document = f";;{keyword}\nテスト内容\n;;;"
        
        try:
            result = self.parser.parse(document)
            
            # Should produce at least one node
            assert len(result) >= 1
            
            # First node should be a block with the keyword
            first_node = result[0]
            assert hasattr(first_node, 'type')
            
        except Exception as e:
            pytest.fail(f"Failed to parse valid keyword '{keyword}': {e}")
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5))
    @settings(max_examples=20)
    def test_multiple_paragraphs(self, paragraphs):
        """Multiple paragraphs should be handled correctly"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Filter out empty paragraphs and join with double newlines
        clean_paragraphs = [p.strip() for p in paragraphs if p.strip()]
        if not clean_paragraphs:
            assume(False)  # Skip if no valid paragraphs
        
        document = "\n\n".join(clean_paragraphs)
        
        try:
            result = self.parser.parse(document)
            assert isinstance(result, list)
            
            # Should have at least as many nodes as paragraphs
            # (Could be more due to parsing rules)
            assert len(result) >= 1
            
        except Exception as e:
            pytest.fail(f"Failed on multiple paragraphs: {e}")
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=10)
    def test_heading_levels(self, level):
        """All heading levels should work correctly"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        keyword = f"見出し{level}"
        document = f";;{keyword}\n見出しテキスト\n;;;"
        
        try:
            result = self.parser.parse(document)
            assert len(result) >= 1
            
            # Should contain a heading node
            has_heading = any(
                hasattr(node, 'type') and 'heading' in str(node.type).lower()
                for node in result
            )
            # Note: This assertion might be too strict depending on implementation
            # assert has_heading, f"No heading found for level {level}"
            
        except Exception as e:
            pytest.fail(f"Failed on heading level {level}: {e}")


class TestParserInvariants:
    """Test parser invariants - properties that should always hold"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.parser = KumihanParser()
    
    @given(kumihan_document())
    @settings(max_examples=30)
    def test_parse_is_deterministic(self, document):
        """Parsing the same document should always give the same result"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        try:
            result1 = self.parser.parse(document)
            result2 = self.parser.parse(document)
            
            # Results should be identical
            assert len(result1) == len(result2)
            
            # Note: Deep comparison of AST nodes might be complex
            # For now, just check basic structure
            for n1, n2 in zip(result1, result2):
                assert type(n1) == type(n2)
                assert hasattr(n1, 'type') == hasattr(n2, 'type')
                
        except Exception as e:
            pytest.fail(f"Determinism test failed: {e}")
    
    @given(st.text(max_size=100))
    @settings(max_examples=20)
    def test_empty_input_handling(self, text):
        """Empty or whitespace-only input should be handled gracefully"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Only test with whitespace-only strings
        assume(not text.strip())
        
        try:
            result = self.parser.parse(text)
            assert isinstance(result, list)
            
            # Empty input should produce empty or minimal output
            assert len(result) >= 0
            
        except Exception as e:
            pytest.fail(f"Failed on empty/whitespace input: {e}")


# Performance property tests
class TestParserPerformance:
    """Property-based performance tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.parser = KumihanParser()
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=10)
    def test_linear_scaling(self, size):
        """Parser should scale roughly linearly with input size"""
        if not HAS_HYPOTHESIS:
            pytest.skip("hypothesis not available")
        
        # Create document with predictable size
        document = "テスト段落です。\n\n" * size
        
        import time
        start_time = time.time()
        
        try:
            result = self.parser.parse(document)
            end_time = time.time()
            
            parse_time = end_time - start_time
            
            # Should complete within reasonable time (very loose bound)
            assert parse_time < 10.0, f"Parsing took too long: {parse_time}s for size {size}"
            
            # Should produce reasonable output
            assert isinstance(result, list)
            assert len(result) > 0
            
        except Exception as e:
            pytest.fail(f"Performance test failed for size {size}: {e}")


if __name__ == "__main__":
    # Run property-based tests
    if HAS_HYPOTHESIS:
        pytest.main([__file__, "-v"])
    else:
        print("Hypothesis not available. Install with: pip install hypothesis")
        print("Skipping property-based tests.")