#!/usr/bin/env python3
"""
残り83個の最終エラー完全解決スクリプト
- 未完了マーカー (## パターン)
- 閉じられていないブロック (#色名色を使用した...)
"""

import re
import sys
from pathlib import Path

def fix_final_83_patterns(content: str) -> str:
    """残り83個のエラーパターンを完全修正"""
    
    # パターン1: 「WCAG ## 2.1 AA準拠」→「WCAG 2.1 AA準拠」
    content = re.sub(r'WCAG\s*##\s*2\.1\s*AA準拠', 'WCAG 2.1 AA準拠', content)
    
    # パターン2: 「売上高: ## 8623万円」→「売上高: 8623万円」
    content = re.sub(r':?\s*##\s*(\d+[万千億]?円)', r': \1', content)
    content = re.sub(r':?\s*##\s*(\d+%)', r': \1', content)
    
    # パターン3: color属性後の中途半端な#を除去または完了
    # 「color=色コード008000 # 下線装飾の活用法」→「color=色コード008000 #
    # 下線装飾の活用法」（改行してブロック化）
    content = re.sub(
        r'(color=色コード[0-9a-fA-F]{6})\s*#\s*([^#\n]+)',
        r'\1 #\n\2\n##',
        content
    )
    
    # パターン4: 既存のcolor属性付きマーカーで中途半端なもの
    content = re.sub(
        r'(color=色コード[a-zA-Z]+)\s*#\s*([^#\n]+)',
        r'\1 #\n\2\n##',
        content
    )
    
    # パターン5: 「イタリック # 85%」→「イタリック #
    # 85%
    # ##」
    content = re.sub(
        r'^(\s*)([^#\n]+)\s*#\s*(\d+%)$',
        r'\1\2 #\n\1\3\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン6: 「中央寄せ color=色コードff0000 # 38%」
    content = re.sub(
        r'^(\s*)([^#\n]+)\s+(color=[^#\s]+)\s*#\s*(\d+%)$',
        r'\1\2 \3 #\n\1\4\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン7: 「#cd5c5c色を使用した注意装飾の例として、この文章は...」
    # → 「色コードcd5c5c色を使用した注意装飾の例として、この文章は...」
    content = re.sub(
        r'#([0-9a-fA-F]{6})色を使用した([^#\n]+)',
        r'色コード\1色を使用した\2',
        content
    )
    
    # パターン8: 複合装飾でcolor属性がある未完了マーカー
    content = re.sub(
        r'^(\s*)([^#\n]+)\s+(color=色コード[0-9a-fA-F]{6})\s*#\s*([^#\n]+)',
        r'\1\2 \3 #\n\1\4\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン9: AA準拠パターンの統一処理
    content = re.sub(
        r'^(\s*)([^#\n]+)\s+(color=[^#\s]+)\s*#\s*AA準拠を([^#\n]+)',
        r'\1\2 \3 #\nAA準拠を\4\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン10: 単独の数値パーセントマーカー修正
    content = re.sub(r'^\s*##\s*(\d+%)\s*$', r'\1', content, flags=re.MULTILINE)
    
    # パターン11: システム設計仕様書パターン
    content = re.sub(
        r'^(\s*)([^#\n]+)\s+(color=[^#\s]+)\s*#\s*(システム設計仕様書[^#\n]*)',
        r'\1\2 \3 #\n\1\4\n\1##',
        content,
        flags=re.MULTILINE
    )
    
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
        fixed_content = fix_final_83_patterns(original_content)
        
        # 書き込み
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed remaining patterns: {file_path}")
        except Exception as e:
            print(f"Error writing file: {e}")
            continue

if __name__ == "__main__":
    main()