#!/usr/bin/env python3
"""パーサーのgraceful error機能を詳細にデバッグするためのスクリプト"""

from kumihan_formatter.parser import Parser

# テスト用のテキスト
test_text = """# 間違った記法
この行は正しい記法です。

# 太字 これは終了マーカーが不完全
正常なテキストが続きます。"""

def main():
    print("=== Detailed Graceful Error Parser Debug ===")
    
    # graceful_errors=True でパーサーを初期化
    parser = Parser(graceful_errors=True)
    
    print(f"Graceful errors enabled: {parser.graceful_errors}")
    print(f"Block parser has parser reference: {hasattr(parser.block_parser, 'parser_ref')}")
    if hasattr(parser.block_parser, 'parser_ref'):
        print(f"Parser reference is set: {parser.block_parser.parser_ref is not None}")
    
    # パース実行
    print("\n--- Starting parse ---")
    nodes = parser.parse(test_text)
    
    print(f"Parse completed. Nodes created: {len(nodes)}")
    print(f"Traditional errors: {len(parser.errors)}")
    print(f"Graceful errors: {len(parser.graceful_syntax_errors)}")
    
    # 従来のエラーを表示
    if parser.errors:
        print("\n--- Traditional Errors ---")
        for i, error in enumerate(parser.errors, 1):
            print(f"{i}. {error}")
    
    # Graceful errorsを表示
    if parser.graceful_syntax_errors:
        print("\n--- Graceful Errors ---")
        for i, error in enumerate(parser.graceful_syntax_errors, 1):
            print(f"{i}. Line {error.line_number}: {error.message}")
            print(f"   Context: {error.context}")
            print(f"   Severity: {error.severity}")
    else:
        print("\n--- No Graceful Errors Found ---")
    
    # 各ノードの内容を表示
    print("\n--- Generated Nodes ---")
    for i, node in enumerate(nodes, 1):
        print(f"{i}. Type: {node.type}, Content: {str(node)[:50]}...")
        if node.type == 'error':
            print(f"   Error content: {node.content}")
            print(f"   Attributes: {node.attributes}")

    # 手動でBlockParserをテスト
    print("\n--- Manual BlockParser Test ---")
    lines = test_text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#'):
            print(f"Line {i}: {line}")
            is_opening = parser.block_parser.is_opening_marker(line)
            print(f"  is_opening_marker: {is_opening}")
            if is_opening:
                try:
                    result = parser.block_parser.parse_block_marker(lines, i)
                    print(f"  parse_block_marker result: {result}")
                except Exception as e:
                    print(f"  parse_block_marker exception: {e}")

if __name__ == "__main__":
    main()