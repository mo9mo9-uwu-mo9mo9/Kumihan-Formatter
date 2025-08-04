#!/usr/bin/env python3
"""
11_complex_nested_5k.txt用の追加修正スクリプト
残りのエラーパターンを修正
"""

import re
import sys
from pathlib import Path

def fix_remaining_patterns(content: str) -> str:
    """残りのエラーパターンを修正"""

    # パターン1: "##," のようなカンマ付き終了マーカー
    content = re.sub(r'##,', '##', content)

    # パターン2: "## ダメージ: 数値" パターン
    content = re.sub(
        r'^(\s*)##\s+ダメージ:\s*(\d+-\d+)\s*$',
        r'\1ダメージ: \2',
        content,
        flags=re.MULTILINE
    )

    # パターン3: "##: 説明" パターン
    content = re.sub(
        r'^(\s*)##:\s*(.+)$',
        r'\1\2',
        content,
        flags=re.MULTILINE
    )

    # パターン4: "テキスト ##: 説明" パターン
    content = re.sub(
        r'^(\s*.*?)\s*##:\s*(.+)$',
        r'\1: \2',
        content,
        flags=re.MULTILINE
    )

    # パターン5: "## の" パターン（文中の不要な##）
    content = re.sub(
        r'\s*##\s*の',
        ' の',
        content
    )

    # パターン6: 行末の "##" で終わるが、ブロック終了でない場合
    # 文脈を考慮して修正
    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        # 単独の ## または ##: のパターンを検出
        if line.strip() == '##:' or (line.strip().endswith('##:') and ' ' in line):
            # ##: を削除
            fixed_line = line.replace('##:', ':').strip()
            fixed_lines.append(fixed_line)
        # item.condition ## のようなパターン
        elif re.search(r'\w+\.\w+\s*##', line):
            fixed_line = re.sub(r'\s*##\s*', ' ', line)
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # パターン7: 複数の ## が連続している場合
    content = re.sub(r'##\s*##', '##', content)

    # パターン8: "威力増強 ##" のような行末の不要な ##
    content = re.sub(
        r'^(\s*[^#\n]+)\s*##\s*$',
        r'\1',
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
    fixed_content = fix_remaining_patterns(original_content)

    # 書き込み
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✅ Fixed additional patterns: {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
