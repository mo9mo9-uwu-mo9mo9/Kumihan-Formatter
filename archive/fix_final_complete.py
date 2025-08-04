#!/usr/bin/env python3
"""
残り516エラー完全解決スクリプト
12_heavy_decoration_7k.txt と 21_technical_manual.txt 用
"""

import re
import sys
from pathlib import Path

def fix_all_final_patterns(content: str) -> str:
    """残り全てのエラーパターンを完全修正"""

    # 全角マーカーを半角に統一
    content = content.replace('＃', '#')

    # パターン1: 全ての16進数カラーコード（#XXXXXX）を安全なテキスト形式に変換
    # 「プライマリカラーは#4169e1、」→「プライマリカラーは色コード4169e1、」
    content = re.sub(r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])#([0-9a-fA-F]{6})([、。を])', r'\1色コード\2\3', content)
    content = re.sub(r'は\s*#([0-9a-fA-F]{6})', r'は色コード\1', content)
    content = re.sub(r'を\s*#([0-9a-fA-F]{6})', r'を色コード\1', content)
    content = re.sub(r'で\s*#([0-9a-fA-F]{6})', r'で色コード\1', content)
    content = re.sub(r'、\s*#([0-9a-fA-F]{6})', r'、色コード\1', content)
    content = re.sub(r'リンクは\s*#([0-9a-fA-F]{6})', r'リンクは色コード\1', content)

    # パターン2: 単語直後の16進数カラーコード
    content = re.sub(r'([ァ-ヴ]+)#([0-9a-fA-F]{6})', r'\1色コード\2', content)
    content = re.sub(r'([一-龯]+)#([0-9a-fA-F]{6})', r'\1色コード\2', content)

    # パターン3: 残存する独立した16進数カラーコード
    content = re.sub(r'(?<!\w)#([0-9a-fA-F]{6})(?!\w)', r'色コード\1', content)

    # パターン4: 文中の「##。」「##、」などの不正マーカー完全除去
    content = re.sub(r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])\s*##\s*([。、！？])', r'\1\2', content)
    content = re.sub(r'データベース\s*##\s*。', 'データベース。', content)
    content = re.sub(r'監視\s*##\s*。', '監視。', content)
    content = re.sub(r'アプリケーション\s*##\s*。', 'アプリケーション。', content)
    content = re.sub(r'システム\s*##\s*。', 'システム。', content)

    # パターン5: 行末の不正な##パターン
    content = re.sub(r'\s*##\s*$', '', content, flags=re.MULTILINE)

    # パターン6: 数値直後の##
    content = re.sub(r'(\d+)\s*##', r'\1', content)

    # パターン7: 助詞直前の##
    content = re.sub(r'\s*##\s*([がをにでは])', r'\1', content)

    # パターン8: 単語間の不正な##
    content = re.sub(r'([一-龯]+)\s*##\s*([一-龯]+)', r'\1\2', content)

    # パターン9: 残存する###等の連続マーカー
    content = re.sub(r'#{3,}', '##', content)

    # パターン10: 空行の無効マーカー除去
    content = re.sub(r'^\s*##\s*$', '', content, flags=re.MULTILINE)

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
        fixed_content = fix_all_final_patterns(original_content)

        # 書き込み
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed: {file_path}")
        except Exception as e:
            print(f"Error writing file: {e}")
            continue

if __name__ == "__main__":
    main()
