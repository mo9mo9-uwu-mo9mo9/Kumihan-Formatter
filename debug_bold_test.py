#!/usr/bin/env python3
"""Debug script to test bold keyword processing"""

from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer

def test_bold_processing():
    """Test bold keyword processing step by step"""
    
    # Test input
    test_text = """これはテストです。

;;;太字
太字のテキストです。
;;;"""
    
    print("=== Test Input ===")
    print(test_text)
    print()
    
    # Parse
    parser = Parser()
    ast = parser.parse(test_text)
    
    print("=== Parsed AST ===")
    for i, node in enumerate(ast):
        print(f"Node {i}: type={node.type}, content={repr(node.content)}, attributes={node.attributes}")
        if hasattr(node, 'content') and isinstance(node.content, list):
            for j, child in enumerate(node.content):
                print(f"  Child {j}: {repr(child)}")
    print()
    
    # Render
    renderer = Renderer()
    html = renderer.render(ast, "test_debug")
    
    print("=== Generated HTML ===")
    print(html)
    print()
    
    # Check for strong tags
    if "<strong>" in html:
        print("✅ Strong tags found in HTML")
    else:
        print("❌ Strong tags NOT found in HTML")

if __name__ == "__main__":
    test_bold_processing()