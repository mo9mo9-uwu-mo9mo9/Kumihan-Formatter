#!/usr/bin/env python3
"""
12_heavy_decoration_7k.txt用の追加修正スクリプト
残り120個の16進数カラーコード関連エラーを修正
"""

import re
import sys
from pathlib import Path

def fix_remaining_color_patterns(content: str) -> str:
    """残りの16進数カラーコード関連パターンを修正"""
    
    # パターン1: 文中の16進数カラーコード（#で始まる6桁）を通常テキストとして扱う
    # "プライマリカラーは #4169e1 、" のようなパターンで、#がマーカーと誤認される
    # これらを文章として認識されるよう、#を削除または別の表記に変更
    
    # 16進数カラーコードのパターンをテキスト形式に変換
    content = re.sub(r'は\s*#([0-9a-fA-F]{6})\s*、', r'は色コード\1、', content)
    content = re.sub(r'は\s*#([0-9a-fA-F]{6})\s*を', r'は色コード\1を', content)
    content = re.sub(r'は\s*#([0-9a-fA-F]{6})\s*で', r'は色コード\1で', content)
    content = re.sub(r'リンクは\s*#([0-9a-fA-F]{6})\s*で', r'リンクは色コード\1で', content)
    
    # パターン2: 文中の "# f0a030製品" のようなパターン
    content = re.sub(r'、\s*#\s*([0-9a-fA-F]{6})製品', r'、色コード\1製品', content)
    
    # パターン3: "#da70d6色を使用した" のようなパターン
    content = re.sub(r'#([0-9a-fA-F]{6})色', r'色コード\1色', content)
    
    # パターン4: 既に変換済みの #XXXXXX のパターンが残っている場合の処理
    content = re.sub(r'(?<![#\w])\s*#([0-9a-fA-F]{6})(?![#\w])', r'色コード\1', content)
    
    # パターン5: カラーコード後の残存する # を削除
    content = re.sub(r'色コード([0-9a-fA-F]{6})\s*#', r'色コード\1', content)
    
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
    fixed_content = fix_remaining_color_patterns(original_content)
    
    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed color patterns: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()