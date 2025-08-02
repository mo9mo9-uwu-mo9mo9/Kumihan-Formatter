#!/usr/bin/env python3
"""
11_complex_nested_5k.txt専用の高度な修正スクリプト
複雑なネスト構造と不正なマーカーパターンを修正
"""

import re
import sys
from pathlib import Path

def fix_complex_nested_patterns(content: str) -> str:
    """複雑なネストパターンを修正"""
    
    # 全角マーカーを半角に統一
    content = content.replace('＃', '#')
    
    # パターン1: 単独の # を削除（行頭の単独 # のみ）
    content = re.sub(r'^\s*#\s*$', '', content, flags=re.MULTILINE)
    
    # パターン2: ### のような連続マーカーを ## に修正
    content = re.sub(r'#{3,}', '##', content)
    
    # パターン3: 不完全なマーカー修正 "## -" → "##"
    content = re.sub(r'##\s*-\s*', '## ', content)
    
    # パターン4: # キーワード color=色 ### → # キーワード color=色 #\n\n##
    content = re.sub(
        r'^(\s*)#\s*([^#]+?)\s+color=([^#\s]+)\s*###\s*$',
        r'\1# \2 color=\3 #\n\n##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン5: # 引用 color=色 # → # 引用 color=色 #\n（既に正しい形式の場合はスキップ）
    content = re.sub(
        r'^(\s*)#\s*(引用|枠線|折りたたみ)\s+color=([^#\s]+)\s*#\s*$',
        r'\1# \2 color=\3 #',
        content,
        flags=re.MULTILINE
    )
    
    # パターン6: 単一行記法の変換（基本パターン）
    # # キーワード # 内容 → # キーワード #\n内容\n##
    content = re.sub(
        r'^(\s*)#\s*([^#\s]+)\s*#\s*([^#\n]+)$',
        r'\1# \2 #\n\1\3\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン7: color属性付き単一行記法
    content = re.sub(
        r'^(\s*)#\s*([^#\s]+)\s+color=([^#\s]+)\s*#\s*([^#\n]+)$',
        r'\1# \2 color=\3 #\n\1\4\n\1##',
        content,
        flags=re.MULTILINE
    )
    
    # パターン8: リスト項目内の不正なマーカー
    content = re.sub(
        r'^(\s*•\s*)#\s*$',
        r'\1',
        content,
        flags=re.MULTILINE
    )
    
    # パターン9: 不完全な終了マーカーの修正
    # "内容 ##" のパターンで、前に開始マーカーがない場合
    lines = content.split('\n')
    fixed_lines = []
    in_block = False
    
    for i, line in enumerate(lines):
        # ブロック開始を検出
        if re.match(r'^\s*#\s*[^#]+\s*#\s*$', line):
            in_block = True
            fixed_lines.append(line)
        # 正しいブロック終了
        elif re.match(r'^\s*##\s*$', line):
            in_block = False
            fixed_lines.append(line)
        # 不正な終了マーカーを含む行
        elif ' ## ' in line and not in_block:
            # " ## " を " " に置換
            fixed_line = re.sub(r'\s*##\s*', ' ', line)
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # パターン10: 見出し内の余分なマーカー修正
    content = re.sub(
        r'^(#見出し\d#[^#]+)###$',
        r'\1##',
        content,
        flags=re.MULTILINE
    )
    
    return content

def main():
    """メイン処理"""
    file_path = Path("samples/performance/11_complex_nested_5k.txt")
    
    print(f"Processing: {file_path}")
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # 修正実行
    fixed_content = fix_complex_nested_patterns(original_content)
    
    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()