#!/usr/bin/env python3
"""
New comprehensive test suite for Kumihan-Formatter core functionality
This test suite can run independently without external dependencies like Jinja2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.block_parser import BlockParser
from kumihan_formatter.core.list_parser import ListParser
from kumihan_formatter.core.html_renderer import HTMLRenderer
from kumihan_formatter.core.toc_generator import TOCGenerator
from kumihan_formatter.core.ast_nodes import Node, NodeBuilder

def test_keyword_parser():
    """Test KeywordParser functionality"""
    print("=== Keyword Parser Tests ===")
    
    parser = KeywordParser()
    
    # Test 1: Single keyword parsing
    keywords, attributes, errors = parser.parse_marker_keywords("太字")
    assert keywords == ["太字"], f"Expected ['太字'], got {keywords}"
    assert not errors, f"Unexpected errors: {errors}"
    print("✅ Single keyword parsing")
    
    # Test 2: Compound keyword parsing
    keywords, attributes, errors = parser.parse_marker_keywords("太字+イタリック")
    assert "太字" in keywords and "イタリック" in keywords, f"Expected both keywords, got {keywords}"
    assert not errors, f"Unexpected errors: {errors}"
    print("✅ Compound keyword parsing")
    
    # Test 3: Color attribute parsing
    keywords, attributes, errors = parser.parse_marker_keywords("ハイライト color=#ff0000")
    assert "ハイライト" in keywords, f"Expected ハイライト, got {keywords}"
    assert attributes.get("color") == "#ff0000", f"Expected color #ff0000, got {attributes.get('color')}"
    print("✅ Color attribute parsing")
    
    # Test 4: Single block creation
    node = parser.create_single_block("太字", "テスト内容", {})
    assert node.type == "strong", f"Expected strong, got {node.type}"
    assert node.content == ["テスト内容"], f"Expected ['テスト内容'], got {node.content}"
    print("✅ Single block creation")
    
    # Test 5: Compound block creation
    node = parser.create_compound_block(["太字", "イタリック"], "複合内容", {})
    assert node.type == "strong", f"Expected strong as outer type, got {node.type}"
    assert isinstance(node.content[0], Node), "Expected nested node"
    assert node.content[0].type == "em", f"Expected em as inner type, got {node.content[0].type}"
    print("✅ Compound block creation")
    
    return True

def test_block_parser():
    """Test BlockParser functionality"""
    print("\n=== Block Parser Tests ===")
    
    keyword_parser = KeywordParser()
    parser = BlockParser(keyword_parser)
    
    # Test 1: Opening marker detection
    assert parser.is_opening_marker(";;;太字"), "Should detect ;;;太字 as opening marker"
    assert not parser.is_opening_marker(";;;"), "Should not detect ;;; as opening marker"
    assert not parser.is_opening_marker(";;;太字;;;"), "Should not detect ;;;太字;;; as opening marker"
    print("✅ Opening marker detection")
    
    # Test 2: Closing marker detection
    assert parser.is_closing_marker(";;;"), "Should detect ;;; as closing marker"
    assert not parser.is_closing_marker(";;;太字"), "Should not detect ;;;太字 as closing marker"
    print("✅ Closing marker detection")
    
    # Test 3: Block parsing
    lines = [";;;太字", "内容テキスト", ";;;"]
    node, next_index = parser.parse_block_marker(lines, 0)
    assert node.type == "strong", f"Expected strong, got {node.type}"
    assert next_index == 3, f"Expected next_index 3, got {next_index}"
    print("✅ Block parsing")
    
    # Test 4: Paragraph parsing
    lines = ["これは段落です", "続きの行"]
    node, next_index = parser.parse_paragraph(lines, 0)
    assert node.type == "p", f"Expected p, got {node.type}"
    assert "これは段落です" in node.content, f"Content missing: {node.content}"
    print("✅ Paragraph parsing")
    
    return True

def test_html_renderer():
    """Test HTMLRenderer functionality"""
    print("\n=== HTML Renderer Tests ===")
    
    renderer = HTMLRenderer()
    
    # Test 1: Simple node rendering
    node = Node("p", "テスト段落")
    html = renderer.render_node(node)
    assert "<p>テスト段落</p>" == html, f"Expected <p>テスト段落</p>, got {html}"
    print("✅ Simple node rendering")
    
    # Test 2: Strong node rendering
    node = Node("strong", ["太字テキスト"])
    html = renderer.render_node(node)
    assert "<strong>太字テキスト</strong>" == html, f"Expected <strong>太字テキスト</strong>, got {html}"
    print("✅ Strong node rendering")
    
    # Test 3: Nested node rendering
    inner_node = Node("em", ["イタリック"])
    outer_node = Node("strong", [inner_node])
    html = renderer.render_node(outer_node)
    expected = "<strong><em>イタリック</em></strong>"
    assert expected == html, f"Expected {expected}, got {html}"
    print("✅ Nested node rendering")
    
    # Test 4: Node with attributes
    node = Node("div", "内容", {"class": "box"})
    html = renderer.render_node(node)
    assert 'class="box"' in html and "<div" in html and "</div>" in html, f"Attributes not rendered correctly: {html}"
    print("✅ Node with attributes")
    
    return True

def test_toc_generator():
    """Test TOCGenerator functionality"""
    print("\n=== TOC Generator Tests ===")
    
    generator = TOCGenerator()
    
    # Test 1: Empty nodes
    toc_data = generator.generate_toc([])
    assert not toc_data['has_toc'], "Empty nodes should not have TOC"
    assert toc_data['heading_count'] == 0, f"Expected 0 headings, got {toc_data['heading_count']}"
    print("✅ Empty nodes handling")
    
    # Test 2: Nodes with headings
    h1_node = Node("h1", "第1章", {"id": "heading-1"})
    h2_node = Node("h2", "第1節", {"id": "heading-2"})
    nodes = [h1_node, Node("p", "段落"), h2_node]
    
    toc_data = generator.generate_toc(nodes)
    assert toc_data['has_toc'], "Should have TOC with headings"
    assert toc_data['heading_count'] == 2, f"Expected 2 headings, got {toc_data['heading_count']}"
    print("✅ TOC generation with headings")
    
    # Test 3: Deep recursion protection
    # Create a deeply nested structure
    deep_node = Node("div", "内容")
    current = deep_node
    for i in range(10):
        new_node = Node("div", [current])
        current = new_node
    
    # This should not cause RecursionError
    toc_data = generator.generate_toc([current])
    assert toc_data['heading_count'] == 0, "Deep nesting should not crash"
    print("✅ Deep recursion protection")
    
    return True

def test_integration():
    """Test integration of all components"""
    print("\n=== Integration Tests ===")
    
    # Full pipeline test
    keyword_parser = KeywordParser()
    block_parser = BlockParser(keyword_parser)
    html_renderer = HTMLRenderer()
    
    # Parse a complex document
    lines = [
        ";;;見出し1",
        "第1章",
        ";;;",
        "",
        "これは段落です。",
        "",
        ";;;太字+イタリック",
        "複合スタイル",
        ";;;",
        "",
        "- リスト項目1",
        "- リスト項目2"
    ]
    
    ast = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        if block_parser.is_opening_marker(line):
            node, next_index = block_parser.parse_block_marker(lines, i)
            if node:
                ast.append(node)
            i = next_index
        elif line.startswith("- "):
            # Simple list handling for test
            ast.append(Node("p", line))
            i += 1
        else:
            node, next_index = block_parser.parse_paragraph(lines, i)
            if node:
                ast.append(node)
            i = next_index if next_index > i else i + 1
    
    # Render all nodes
    html_parts = []
    for node in ast:
        html = html_renderer.render_node(node)
        html_parts.append(html)
    
    full_html = '\n'.join(html_parts)
    
    # Debug: Print actual HTML
    print(f"\nGenerated HTML:\n{full_html}")
    print(f"\nParsed nodes: {len(ast)}")
    for i, node in enumerate(ast):
        print(f"  Node {i}: {node.type} - {repr(node.content)}")
    
    # Verify expected elements
    assert "<h1" in full_html, f"Should contain h1 heading. Got: {full_html}"
    assert "<strong>" in full_html, "Should contain strong element"
    assert "<em>" in full_html, "Should contain em element"
    assert "<p>" in full_html, "Should contain paragraph"
    
    print("✅ Full pipeline integration")
    print(f"Generated HTML ({len(full_html)} chars):")
    print(full_html[:200] + "..." if len(full_html) > 200 else full_html)
    
    return True

def main():
    """Run all tests"""
    print("🧪 Running Kumihan-Formatter Core Functionality Tests")
    print("=" * 60)
    
    tests = [
        test_keyword_parser,
        test_block_parser,
        test_html_renderer,
        test_toc_generator,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)