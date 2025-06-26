#!/usr/bin/env python3
"""Test for recursion issues in AST processing"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.toc_generator import TOCGenerator
from kumihan_formatter.core.html_renderer import HTMLRenderer

def test_circular_reference():
    """Test if there are any circular references in AST nodes"""
    
    print("=== Circular Reference Test ===")
    
    try:
        # Create a complex AST structure
        keyword_parser = KeywordParser()
        block_parser = BlockParser(keyword_parser)
        
        # Test sample with headings and compound blocks
        sample_lines = [
            ";;;見出し1",
            "第1章",
            ";;;",
            "",
            ";;;太字+イタリック", 
            "複合テキスト",
            ";;;",
            "",
            ";;;見出し2",
            "第2章",
            ";;;"
        ]
        
        print(f"Parsing {len(sample_lines)} lines...")
        
        ast = []
        i = 0
        
        while i < len(sample_lines):
            line = sample_lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Parse block markers
            if block_parser.is_opening_marker(line):
                node, next_index = block_parser.parse_block_marker(sample_lines, i)
                if node:
                    ast.append(node)
                    print(f"  Parsed: {node.type}")
                i = next_index
            else:
                i += 1
        
        print(f"Created AST with {len(ast)} nodes")
        
        # Test TOC generation (this is where RecursionError might occur)
        print("Testing TOC generation...")
        toc_generator = TOCGenerator()
        toc_data = toc_generator.generate_toc(ast)
        print(f"TOC generated successfully: {toc_data['heading_count']} headings")
        
        # Test HTML rendering
        print("Testing HTML rendering...")
        html_renderer = HTMLRenderer()
        html = html_renderer.render_nodes(ast)
        print(f"HTML rendered successfully: {len(html)} characters")
        
        print("✅ No circular reference detected")
        return True
        
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

def test_node_structure():
    """Test individual node structure for circular references"""
    
    print("\n=== Node Structure Test ===")
    
    try:
        keyword_parser = KeywordParser()
        
        # Create a compound node
        node = keyword_parser.create_compound_block(
            ["太字", "イタリック"], 
            "テスト内容", 
            {}
        )
        
        print(f"Created node: {node.type}")
        print(f"Node content type: {type(node.content)}")
        
        if isinstance(node.content, list):
            print(f"Content has {len(node.content)} items")
            for i, item in enumerate(node.content):
                print(f"  Item {i}: {type(item)} - {getattr(item, 'type', 'N/A')}")
        
        # Check for self-reference
        def check_circular(node, visited=None):
            if visited is None:
                visited = set()
            
            node_id = id(node)
            if node_id in visited:
                return True  # Circular reference found
            
            visited.add(node_id)
            
            if hasattr(node, 'content') and isinstance(node.content, list):
                for item in node.content:
                    if hasattr(item, 'type'):  # It's a Node
                        if check_circular(item, visited.copy()):
                            return True
            
            return False
        
        has_circular = check_circular(node)
        if has_circular:
            print("❌ Circular reference found in node structure")
            return False
        else:
            print("✅ No circular reference in node structure")
            return True
            
    except Exception as e:
        print(f"❌ Error checking node structure: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_circular_reference()
    success2 = test_node_structure()
    sys.exit(0 if (success1 and success2) else 1)