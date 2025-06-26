#!/usr/bin/env python3
"""Simple test for renderer without dependencies"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.html_renderer import HTMLRenderer

def test_bold_rendering():
    """Test bold keyword rendering"""
    
    # Test content
    content = "太字のテキストです。"
    
    # Create parser
    keyword_parser = KeywordParser()
    
    # Create bold block node
    bold_node = keyword_parser.create_single_block("太字", content, {})
    
    print(f"Created node: type={bold_node.type}, content={bold_node.content}")
    
    # Render to HTML
    renderer = HTMLRenderer()
    html = renderer.render_node(bold_node)
    
    print(f"Rendered HTML: {html}")
    
    # Check if strong tags are present
    if "<strong>" in html and "</strong>" in html:
        print("✅ Strong tags found in HTML")
        return True
    else:
        print("❌ Strong tags NOT found in HTML")
        return False

if __name__ == "__main__":
    success = test_bold_rendering()
    sys.exit(0 if success else 1)