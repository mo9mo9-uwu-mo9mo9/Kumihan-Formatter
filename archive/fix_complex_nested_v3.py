#!/usr/bin/env python3
"""
11_complex_nested_5k.txt用の最終修正スクリプト
残り219個の特定エラーパターンを修正
"""

import re
import sys
from pathlib import Path

def fix_final_patterns(content: str) -> str:
    """最終的なエラーパターンを修正"""

    # パターン1: "## と" のような文中の ##
    content = re.sub(r'\s*##\s+と\s*', ' と ', content)

    # パターン2: "## ✓" のような記号付き
    content = re.sub(r'\s*##\s*✓\s*', ' ✓ ', content)

    # パターン3: "## レベルです。" のような文章内の ##
    content = re.sub(r'\s*##\s+レベルです\s*', ' レベルです', content)

    # パターン4: "##が成功の鍵" のような助詞直前の ##
    content = re.sub(r'\s*##が', 'が', content)
    content = re.sub(r'\s*##を', 'を', content)
    content = re.sub(r'\s*##で', 'で', content)
    content = re.sub(r'\s*##に', 'に', content)
    content = re.sub(r'\s*##の', 'の', content)

    # パターン5: "創意工夫 ##を重視" のような単語間の ##
    content = re.sub(r'(\w+)\s*##\s*([をがでにの])', r'\1\2', content)

    # パターン6: "##。" のような句読点前の ##
    content = re.sub(r'\s*##\s*。', '。', content)
    content = re.sub(r'\s*##\s*、', '、', content)

    # パターン7: "## を設定すること。" のような文中の ##
    content = re.sub(r'\s*##\s+を設定すること', ' を設定すること', content)

    # パターン8: "とても緊張していた ##。" のような動詞後の ##
    content = re.sub(r'(\w+た)\s*##\s*。', r'\1。', content)

    # パターン9: "## + " のような記号パターン
    content = re.sub(r'\s*##\s*\+\s*', ' + ', content)

    # パターン10: "##;" のようなセミコロン付き
    content = re.sub(r'\s*##\s*;', ';', content)

    # パターン11: "'nested_code' ##;" のような文字列後の ##
    content = re.sub(r"('[^']*')\s*##\s*;", r'\1;', content)

    # パターン12: "## → " のような矢印パターン
    content = re.sub(r'\s*##\s*→\s*', ' → ', content)

    # パターン13: "## 回" のような回数表現
    content = re.sub(r'\s*##\s+回\s*', ' 回', content)

    # パターン14: "## することがあります。" のような長い文章
    content = re.sub(r'\s*##\s+することがあります', ' することがあります', content)

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
    fixed_content = fix_final_patterns(original_content)

    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed final patterns: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
