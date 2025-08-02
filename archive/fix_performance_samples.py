#!/usr/bin/env python3
"""
Performance サンプルファイルのv3.0.0記法変換スクリプト
Issue #726対応: 単一行記法 → ブロック記法の一括変換
"""

import re
import sys
from pathlib import Path

def convert_inline_to_block_notation(content: str) -> str:
    """単一行記法をブロック記法に変換"""
    
    # 全角マーカーを半角に統一
    content = content.replace('＃', '#')
    
    # パターン1: # キーワード # 内容 → # キーワード #\n内容\n##
    content = re.sub(
        r'^(.*)# ([^#]+) # ([^#\n].*)$',
        r'\1# \2 #\n\3\n##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン2: # キーワード color=色 # 内容 → # キーワード color=色 #\n内容\n##
    content = re.sub(
        r'^(.*)# ([^#]+) color=([^#\s]+) # ([^#\n].*)$',
        r'\1# \2 color=\3 #\n\4\n##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン3: リスト項目内の単一行記法 - # キーワード # 内容
    content = re.sub(
        r'^(\s*-\s*)#([^#]+)# ([^#\n].*)$',
        r'\1#\2#\n\3\n##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン4: 単独の # キーワード # 行 → # キーワード #\n\n##
    content = re.sub(
        r'^(\s*)# ([^#\n]+) #\s*$',
        r'\1# \2 #\n\n##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン5: 行頭の #キーワード# 内容 → #キーワード#\n内容\n##
    content = re.sub(
        r'^#([^#]+)# ([^#\n].*)$',
        r'#\1#\n\2\n##',
        content,
        flags=re.MULTILINE
    )
    
    return content

def main():
    """メイン処理"""
    if len(sys.argv) != 2:
        print("Usage: python fix_performance_samples.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    print(f"Processing: {file_path}")
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # 変換実行
    converted_content = convert_inline_to_block_notation(original_content)
    
    # 変更があった場合のみ書き込み
    if converted_content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            print(f"✅ Conversion completed: {file_path}")
        except Exception as e:
            print(f"Error writing file: {e}")
            sys.exit(1)
    else:
        print(f"ℹ️ No changes needed: {file_path}")

if __name__ == "__main__":
    main()