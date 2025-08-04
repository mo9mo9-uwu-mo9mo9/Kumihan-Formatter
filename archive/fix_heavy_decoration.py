#!/usr/bin/env python3
"""
12_heavy_decoration_7k.txt専用の修正スクリプト
11_complex_nested_5k.txtで使用したパターンを適用
"""

import re
import sys
from pathlib import Path

def fix_heavy_decoration_patterns(content: str) -> str:
    """heavy decorationファイル用のパターン修正"""

    # 全角マーカーを半角に統一
    content = content.replace('＃', '#')

    # パターン1: 単独の # を削除（行頭の単独 # のみ）
    content = re.sub(r'^\s*#\s*$', '', content, flags=re.MULTILINE)

    # パターン2: ### のような連続マーカーを ## に修正
    content = re.sub(r'#{3,}', '##', content)

    # パターン3: 不完全なマーカー修正 "## -" → "##"
    content = re.sub(r'##\s*-\s*', '## ', content)

    # パターン4: "プライマリカラーは#4169e1、" のような文中の16進数カラーコード
    # これは正規の色指定ではなく文章内容なので、#を削除しない
    # ただし、エラーメッセージから判断すると、これがマーカーと誤認されている
    # 16進数カラーコードの前後にスペースを追加して分離する
    content = re.sub(r'は#([0-9a-fA-F]{6})、', r'は #\1 、', content)
    content = re.sub(r'は#([0-9a-fA-F]{6})を', r'は #\1 を', content)

    # パターン5: 基本的な単一行記法の変換
    content = re.sub(
        r'^(\s*)#\s*([^#\s]+)\s*#\s*([^#\n]+)$',
        r'\1# \2 #\n\1\3\n\1##',
        content,
        flags=re.MULTILINE
    )

    # パターン6: color属性付き単一行記法
    content = re.sub(
        r'^(\s*)#\s*([^#\s]+)\s+color=([^#\s]+)\s*#\s*([^#\n]+)$',
        r'\1# \2 color=\3 #\n\1\4\n\1##',
        content,
        flags=re.MULTILINE
    )

    # パターン7: 文中の不要な##パターンを修正
    content = re.sub(r'##,', '##', content)
    content = re.sub(r'\s*##\s+と\s*', ' と ', content)
    content = re.sub(r'\s*##\s*✓\s*', ' ✓ ', content)
    content = re.sub(r'\s*##が', 'が', content)
    content = re.sub(r'\s*##を', 'を', content)
    content = re.sub(r'\s*##で', 'で', content)
    content = re.sub(r'\s*##に', 'に', content)
    content = re.sub(r'\s*##の', 'の', content)
    content = re.sub(r'\s*##\s*。', '。', content)
    content = re.sub(r'\s*##\s*、', '、', content)

    return content

def main():
    """メイン処理"""
    file_path = Path("samples/performance/12_heavy_decoration_7k.txt")

    print(f"Processing: {file_path}")

    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # 修正実行
    fixed_content = fix_heavy_decoration_patterns(original_content)

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
