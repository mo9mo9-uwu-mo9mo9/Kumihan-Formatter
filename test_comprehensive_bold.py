#!/usr/bin/env python3
"""Comprehensive test for bold parsing and rendering"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.html_renderer import HTMLRenderer
from kumihan_formatter.parser import Parser
from kumihan_formatter.core.template_manager import TemplateManager, RenderContext

def test_full_parsing_pipeline():
    """Test the full parsing pipeline with bold blocks"""
    
    test_text = """これはテストです。

;;;太字
太字のテキストです。
;;;"""
    
    print("=== Full Pipeline Test ===")
    print(f"Input text:\n{test_text}")
    print()
    
    # Parse with full parser
    parser = Parser()
    try:
        ast = parser.parse(test_text)
        print(f"Parsed {len(ast)} nodes")
        
        for i, node in enumerate(ast):
            print(f"Node {i}: type={node.type}")
            if hasattr(node, 'content'):
                print(f"  Content: {repr(node.content)}")
            if hasattr(node, 'attributes'):
                print(f"  Attributes: {node.attributes}")
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
            
            # Create full HTML document
            template_manager = TemplateManager()
            context = RenderContext(
                title="test",
                body_content=html_content,
                toc_html="",
                has_toc=False,
                has_source_toggle=False
            )
            
            full_html = template_manager.render_template("base.html.j2", context)
            print("✅ Full HTML document generated successfully")
            
            return True
        else:
            print("❌ Bold text not properly wrapped")
            return False
            
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_parsing_pipeline()
    sys.exit(0 if success else 1)