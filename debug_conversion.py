#!/usr/bin/env python3
"""Debug markdown conversion logic"""

import sys
sys.path.insert(0, '.')

from kumihan_formatter.markdown_converter import MarkdownConverter

def debug_detection():
    converter = MarkdownConverter(None)
    with open('docs/QUICKSTART.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # デバッグ情報を出力
    lines = content.split('\n')
    kumihan_pair_count = 0
    in_code_block = False
    in_kumihan_block = False

    print('=== KUMIHAN DETECTION DEBUG ===')
    for i, line in enumerate(lines[:50]):  # 最初の50行のみ
        stripped_line = line.strip()
        
        # コードブロックの開始・終了
        if stripped_line.startswith('```'):
            in_code_block = not in_code_block
            print(f'Line {i+1}: CodeBlock toggle -> {in_code_block}, line: "{stripped_line}"')
            continue
        
        if in_code_block:
            print(f'Line {i+1}: SKIP (in code block): "{stripped_line[:30]}..."')
            continue
        
        # Kumihan記法ブロックの開始
        if stripped_line.startswith(';;;') and any(pattern in stripped_line for pattern in ['見出し', '太字', '枠線', 'ハイライト', 'コードブロック']):
            if not in_kumihan_block:
                in_kumihan_block = True
                print(f'Line {i+1}: Kumihan block START: "{stripped_line}"')
            continue
        
        # Kumihan記法ブロックの終了
        if stripped_line == ';;;':
            if in_kumihan_block:
                in_kumihan_block = False
                kumihan_pair_count += 1
                print(f'Line {i+1}: Kumihan block END, pair count: {kumihan_pair_count}')
            continue

    print(f'Total kumihan pairs: {kumihan_pair_count}')
    
    # Markdown見出しカウント
    markdown_heading_count = 0
    temp_in_code_block = False
    for line in lines:
        if line.strip().startswith('```'):
            temp_in_code_block = not temp_in_code_block
            continue
        if not temp_in_code_block and line.startswith('### '):
            markdown_heading_count += 1
            print(f'Found markdown heading: "{line.strip()}"')
    
    print(f'Markdown headings: {markdown_heading_count}')
    
    # 判定結果
    if kumihan_pair_count >= 3:
        if markdown_heading_count > 0:
            print('DECISION: Call _convert_mixed_format()')
        else:
            print('DECISION: Return content as-is (pure Kumihan)')
    else:
        print('DECISION: Full conversion from Markdown')
    
    # convert_markdown_to_kumihan の実際の動作をテスト
    print('\n=== TESTING convert_markdown_to_kumihan ===')
    
    # 一時的にデバッグメッセージを追加
    import sys
    from unittest.mock import patch
    
    original_convert_mixed = converter._convert_mixed_format
    
    def debug_convert_mixed(content):
        print('DEBUG: _convert_mixed_format was called!')
        
        # デバッグ用のローカル実装
        lines = content.split('\n')
        converted_lines = []
        in_code_block = False
        in_kumihan_block = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # コードブロックの処理
            if stripped_line.startswith('```'):
                if not in_code_block:
                    # コードブロック開始
                    in_code_block = True
                    print(f'DEBUG: Code block START at line {i+1}')
                    converted_lines.append(';;;コードブロック')
                    continue
                else:
                    # コードブロック終了
                    in_code_block = False
                    print(f'DEBUG: Code block END at line {i+1}')
                    converted_lines.append(';;;')
                    continue
            
            if in_code_block:
                # コードブロック内はそのまま保持
                print(f'DEBUG: Code block content: {line[:30]}...')
                converted_lines.append(line)
                continue
            
            # その他の処理
            converted_lines.append(line)
        
        return '\n'.join(converted_lines)
    
    with patch.object(converter, '_convert_mixed_format', debug_convert_mixed):
        result = converter.convert_markdown_to_kumihan(content)
    
    # 結果を確認（コードブロック部分）
    result_lines = result.split('\n')
    for i, line in enumerate(result_lines[200:230]):  # コードブロック周辺を拡大
        print(f'Output {i+201}: {line}')

if __name__ == '__main__':
    debug_detection()