#!/usr/bin/env python3
"""
12_heavy_decoration_7k.txt用の最終修正スクリプト
残り173個の全パターンを完全修正
"""

import re
import sys
from pathlib import Path

def fix_all_remaining_patterns(content: str) -> str:
    """残り全てのパターンを完全修正"""
    
    # パターン1: すべての16進数カラーコード（#XXXXXX）をテキスト形式に変換
    # 行内の16進数カラーコードを完全に削除または変換
    content = re.sub(r'#([0-9a-fA-F]{6})', r'色コード\1', content)
    
    # パターン2: スペース付きの16進数カラーコード
    content = re.sub(r'#\s+([0-9a-fA-F]{6})', r'色コード\1', content)
    
    # パターン3: 文中の "## 数値%" パターン
    content = re.sub(r'\s*##\s+(\d+%)', r' \1', content)
    
    # パターン4: "## 金額" パターン
    content = re.sub(r'\s*##\s+(\d+万円)', r' \1', content)
    
    # パターン5: "## AA準拠" のような文中の ##
    content = re.sub(r'\s*##\s+AA準拠', ' AA準拠', content)
    content = re.sub(r'\s*##\s+2\.1\s+AA準拠', ' 2.1 AA準拠', content)
    
    # パターン6: 行頭の無効な ## を削除
    content = re.sub(r'^\s*##\s+(?![#\n])', '', content, flags=re.MULTILINE)
    
    # パターン7: 文中の "# 色名色" パターン
    content = re.sub(r'#\s*([0-9a-fA-F]{6})色', r'色コード\1色', content)
    
    # パターン8: セグメント関連の16進数
    content = re.sub(r'として、#([0-9a-fA-F]{6})セグメント', r'として、色コード\1セグメント', content)
    content = re.sub(r'として、#([0-9a-fA-F]{6})マーケティング', r'として、色コード\1マーケティング', content)
    
    # パターン9: チャネル関連の16進数
    content = re.sub(r'と、#([0-9a-fA-F]{6})チャネル', r'と、色コード\1チャネル', content)
    
    # パターン10: 残存する空白付きマーカー
    content = re.sub(r'##\s\s+', '## ', content)
    
    # パターン11: 数値直前の ##
    content = re.sub(r'##\s*(\d+)', r'\1', content)
    
    # パターン12: リンクやボタンの色指定における16進数
    # すでに変換済みのものも含めて統一
    
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
    fixed_content = fix_all_remaining_patterns(original_content)
    
    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed all remaining patterns: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()