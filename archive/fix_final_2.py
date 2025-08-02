#!/usr/bin/env python3
"""
21_technical_manual.txt の残り2個エラー修正
1. #目次 → #目次#
2. "#太字 未完了の記法" → "#太字# 未完了の記法"
"""

import re
import sys
from pathlib import Path

def fix_final_2_patterns(content: str) -> str:
    """残り2個のエラーパターンを修正"""
    
    # パターン1: #目次 → #目次#
    content = re.sub(r'^#目次\s*$', '#目次#', content, flags=re.MULTILINE)
    
    # パターン2: "#太字 未完了の記法" → "#太字# 未完了の記法"
    content = re.sub(r'"#太字\s+未完了の記法"', '"#太字# 未完了の記法"', content)
    
    return content

def main():
    """メイン処理"""
    file_path = Path("samples/practical/21_technical_manual.txt")
    
    print(f"Processing: {file_path}")
    
    # ファイル読み込み
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # 修正実行
    fixed_content = fix_final_2_patterns(original_content)
    
    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed final 2 errors: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()