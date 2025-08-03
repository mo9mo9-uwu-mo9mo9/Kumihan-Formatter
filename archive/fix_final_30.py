#!/usr/bin/env python3
"""
残り30個の最終エラー完全解決スクリプト
- ##色コードXXXXXX色を使用した装飾の例として、...
- ブロック開始マーカーなしに # が見つかりました
"""

import re
import sys
from pathlib import Path

def fix_final_30_patterns(content: str) -> str:
    """残り30個のエラーパターンを完全修正"""
    
    # パターン1: 「##色コード000080色を使用した下線装飾の例として、この文章は視覚的なインパクトを与えます。」
    # → 「色コード000080色を使用した下線装飾の例として、この文章は視覚的なインパクトを与えます。」
    content = re.sub(
        r'##色コード([0-9a-fA-F]{6})色を使用した([^#\n]+)',
        r'色コード\1色を使用した\2',
        content
    )
    
    # パターン2: 単独の # 行を除去
    content = re.sub(r'^\s*#\s*$', '', content, flags=re.MULTILINE)
    
    # パターン3: 行頭の ## を除去（既に処理済みのものを含む）
    content = re.sub(r'^\s*##\s*$', '', content, flags=re.MULTILINE)
    
    # パターン4: 複数の空行を1つに統一
    content = re.sub(r'\n\n+', '\n\n', content)
    
    # パターン5: ファイル末尾の余分な空行を削除
    content = content.rstrip() + '\n'
    
    return content

def main():
    """メイン処理"""
    files = [
        "samples/performance/12_heavy_decoration_7k.txt",
        "samples/practical/21_technical_manual.txt"
    ]
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"Processing: {file_path}")
        
        # ファイル読み込み
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            continue
        
        # 修正実行
        fixed_content = fix_final_30_patterns(original_content)
        
        # 書き込み
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed final 30 patterns: {file_path}")
        except Exception as e:
            print(f"Error writing file: {e}")
            continue

if __name__ == "__main__":
    main()