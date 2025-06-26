#!/usr/bin/env python3
"""Test parsing pipeline without template dependencies"""

import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.list_parser import ListParser
from kumihan_formatter.core.rendering import HTMLRenderer

def test_parsing_pipeline():
    """Test the parsing pipeline with bold blocks"""
    
    test_lines = [
        "これはテストです。",
        "",
        ";;;太字",
        "太字のテキストです。",
        ";;;"
    ]
    
    print("=== Parsing Pipeline Test ===")
    print("Input lines:")
    for i, line in enumerate(test_lines):
        print(f"  {i}: '{line}'")
    print()
    
    # Initialize parsers
    keyword_parser = KeywordParser()
    list_parser = ListParser(keyword_parser)
    block_parser = BlockParser(keyword_parser)
    
    # Parse document
    ast = []
    i = 0
    
    while i < len(test_lines):
        line = test_lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Parse block markers
        print(f"  Checking line {i}: '{line}' - is_opening_marker: {block_parser.is_opening_marker(line)}")
        if block_parser.is_opening_marker(line):
            node, next_index = block_parser.parse_block_marker(test_lines, i)
            if node:
                ast.append(node)
                print(f"  Parsed block: type={node.type}, content={repr(node.content)}")
            else:
                print(f"  Block parsing failed")
            i = next_index
        
        # Parse list items
        elif line.startswith('- ') or re.match(r'^\d+\.\s', line):
            # This would be list parsing
            i += 1
        
        # Parse paragraphs
        else:
            node, next_index = block_parser.parse_paragraph(test_lines, i)
            if node:
                ast.append(node)
                print(f"Parsed paragraph: type={node.type}, content={repr(node.content)}")
            i = next_index if next_index > i else i + 1  # Prevent infinite loop
    
    print(f"\nParsed {len(ast)} nodes total")
    print()
    
    # Render HTML
    html_renderer = HTMLRenderer()
    html_content = html_renderer.render_nodes(ast)
    
    print("=== Generated HTML Content ===")
    print(html_content)
    print()
    
    # Check for strong tags
    if "<strong>" in html_content and "太字のテキストです。" in html_content:
        print("✅ Bold text correctly wrapped in strong tags")
        return True
    else:
        print("❌ Bold text not properly wrapped")
        return False

if __name__ == "__main__":
    success = test_parsing_pipeline()
    sys.exit(0 if success else 1)