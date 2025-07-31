#!/usr/bin/env python3
"""パーサーのgraceful error機能をデバッグするためのスクリプト"""

from kumihan_formatter.parser import Parser

# テスト用のテキスト
test_text = """# テスト # 正常なコンテンツ

これは正常なテキストです。

# 太字 # これも正常

# 間違った記法
この行は正しい記法です。

# 太字 これは終了マーカーが不完全
正常なテキストが続きます。

# 存在しない記法 # この記法は存在しません

最後の正常なテキストです。"""

def main():
    print("=== Graceful Error Parser Debug ===")
    
    # graceful_errors=True でパーサーを初期化
    parser = Parser(graceful_errors=True)
    
    print(f"Graceful errors enabled: {parser.graceful_errors}")
    print(f"Correction engine available: {hasattr(parser, 'correction_engine')}")
    
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
            if hasattr(error, 'correction_suggestions'):
                print(f"   Suggestions: {error.correction_suggestions}")
    else:
        print("\n--- No Graceful Errors Found ---")
        print("This indicates the graceful error detection is not working.")
    
    # 各ノードの内容を表示
    print("\n--- Generated Nodes ---")
    for i, node in enumerate(nodes, 1):
        print(f"{i}. Type: {node.type}, Content: {str(node)[:50]}...")

if __name__ == "__main__":
    main()