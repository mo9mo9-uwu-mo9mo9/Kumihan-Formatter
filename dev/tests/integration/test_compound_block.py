#!/usr/bin/env python3
"""Test compound block processing"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.rendering import HTMLRenderer

def test_compound_block():
    """Test compound block processing"""
    
    print("=== Compound Block Test ===")
    
    # Test simple compound block
    keyword_parser = KeywordParser()
    
    try:
        # Test compound keywords parsing
        keywords = ["太字", "イタリック"]
        content = "複合スタイルで、より豊かな表現が可能です"
        attributes = {}
        
        print(f"Creating compound block with keywords: {keywords}")
        print(f"Content: {content}")
        
        node = keyword_parser.create_compound_block(keywords, content, attributes)
        print(f"Created node: type={node.type}")
        print(f"Node content: {node.content}")
        
        # Test rendering
        renderer = HTMLRenderer()
        html = renderer.render_node(node)
        print(f"Rendered HTML: {html}")
        
        if "<strong>" in html and "<em>" in html:
            print("✅ Compound block created successfully")
            return True
        else:
            print("❌ Compound block missing expected tags")
            return False
            
    except RecursionError as e:
        print(f"❌ RecursionError detected: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_parsing():
    """Test parsing sample content that causes RecursionError"""
    
    print("\n=== Sample Content Test ===")
    
    sample_text = """;;;太字+イタリック
複合スタイルで、より豊かな表現が可能です
;;;"""
    
    try:
        from kumihan_formatter.core.block_parser import BlockParser
        from kumihan_formatter.core.keyword_parser import KeywordParser
        
        keyword_parser = KeywordParser()
        block_parser = BlockParser(keyword_parser)
        
        lines = sample_text.strip().split('\n')
        print(f"Parsing lines: {lines}")
        
        node, next_index = block_parser.parse_block_marker(lines, 0)
        print(f"Parsed node: type={node.type}")
        
        renderer = HTMLRenderer()
        html = renderer.render_node(node)
        print(f"Rendered HTML: {html}")
        
        return True
        
    except RecursionError as e:
        print(f"❌ RecursionError in sample parsing: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Other error in sample parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_compound_block()
    success2 = test_sample_parsing()
    sys.exit(0 if (success1 and success2) else 1)