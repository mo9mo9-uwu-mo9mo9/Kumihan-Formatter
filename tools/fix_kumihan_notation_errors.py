#!/usr/bin/env python3
"""
Kumihan記法エラー修正統合ツール - Issue #726対応
大規模構文エラーの系統的修正を行う統合スクリプト

使用法:
    python3 tools/fix_kumihan_notation_errors.py --files file1.txt file2.txt
    python3 tools/fix_kumihan_notation_errors.py --pattern "samples/performance/*.txt"
    python3 tools/fix_kumihan_notation_errors.py --all-samples
"""

import argparse
import re
import sys
import glob
from pathlib import Path
from typing import Tuple  # List removed - unused import (F401)

def fix_hexadecimal_color_codes(content: str) -> Tuple[str, int]:
    """16進数カラーコード問題を修正"""
    fixes = 0

    # パターン1: 文中の16進数カラーコード
    patterns = [
        (r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])#([0-9a-fA-F]{6})([、。を])', r'\1色コード\2\3'),
        (r'は\s*#([0-9a-fA-F]{6})', r'は色コード\1'),
        (r'を\s*#([0-9a-fA-F]{6})', r'を色コード\1'),
        (r'で\s*#([0-9a-fA-F]{6})', r'で色コード\1'),
        (r'、\s*#([0-9a-fA-F]{6})', r'、色コード\1'),
        (r'リンクは\s*#([0-9a-fA-F]{6})', r'リンクは色コード\1'),
        (r'(?<!\w)#([0-9a-fA-F]{6})(?!\w)', r'色コード\1'),
    ]

    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes += content.count(re.search(pattern, content).group(0) if re.search(pattern, content) else '')
            content = new_content

    return content, fixes

def fix_invalid_markers(content: str) -> Tuple[str, int]:
    """不正な##マーカーを修正"""
    fixes = 0

    patterns = [
        # 文中の不正な##マーカー
        (r'([ぁ-ん]|[ァ-ヴ]|[一-龯]|[a-zA-Z0-9])\s*##\s*([。、！？])', r'\1\2'),
        (r'データベース\s*##\s*。', 'データベース。'),
        (r'監視\s*##\s*。', '監視。'),
        (r'アプリケーション\s*##\s*。', 'アプリケーション。'),
        (r'システム\s*##\s*。', 'システム。'),
        # WCAG準拠パターン
        (r'WCAG\s*##\s*2\.1\s*AA準拠', 'WCAG 2.1 AA準拠'),
        # 数値パターン
        (r':?\s*##\s*(\d+[万千億]?円)', r': \1'),
        (r':?\s*##\s*(\d+%)', r': \1'),
        # 助詞直前の##
        (r'\s*##\s*([がをにでは])', r'\1'),
    ]

    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes += len(re.findall(pattern, content))
            content = new_content

    return content, fixes

def fix_incomplete_markers(content: str) -> Tuple[str, int]:
    """未完了マーカーをブロック記法に変換"""
    fixes = 0

    patterns = [
        # color属性付き未完了マーカー
        (r'(color=色コード[0-9a-fA-F]{6})\s*#\s*([^#\n]+)', r'\1 #\n\2\n##'),
        (r'(color=色コード[a-zA-Z]+)\s*#\s*([^#\n]+)', r'\1 #\n\2\n##'),
        # 複合装飾の未完了マーカー
        (r'^(\s*)([^#\n]+)\s+(color=[^#\s]+)\s*#\s*([^#\n]+)', r'\1\2 \3 #\n\1\4\n\1##', re.MULTILINE),
        # 単純な未完了マーカー
        (r'^(\s*)([^#\n]+)\s*#\s*(\d+%)$', r'\1\2 #\n\1\3\n\1##', re.MULTILINE),
    ]

    for pattern, replacement, *flags in patterns:
        flag = flags[0] if flags else 0
        new_content = re.sub(pattern, replacement, content, flags=flag)
        if new_content != content:
            fixes += len(re.findall(pattern, content, flags=flag))
            content = new_content

    return content, fixes

def fix_decoration_examples(content: str) -> Tuple[str, int]:
    """装飾例文パターンを修正"""
    fixes = 0

    patterns = [
        # ##色コードXXXXXX色を使用した装飾の例として...
        (r'##色コード([0-9a-fA-F]{6})色を使用した([^#\n]+)', r'色コード\1色を使用した\2'),
    ]

    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes += len(re.findall(pattern, content))
            content = new_content

    return content, fixes

def fix_misc_patterns(content: str) -> Tuple[str, int]:
    """その他の修正パターン"""
    fixes = 0

    # 全角マーカーを半角に統一
    if '＃' in content:
        content = content.replace('＃', '#')
        fixes += content.count('＃')

    patterns = [
        # 単独の#行を除去
        (r'^\s*#\s*$', '', re.MULTILINE),
        # 空の##行を除去
        (r'^\s*##\s*$', '', re.MULTILINE),
        # 連続する空行を統一
        (r'\n\n+', '\n\n'),
    ]

    for pattern, replacement, *flags in patterns:
        flag = flags[0] if flags else 0
        new_content = re.sub(pattern, replacement, content, flags=flag)
        if new_content != content:
            fixes += len(re.findall(pattern, content, flags=flag))
            content = new_content

    # ファイル末尾の空行整理
    content = content.rstrip() + '\n'

    return content, fixes

def fix_file(file_path: Path, dry_run: bool = False) -> Tuple[int, bool]:
    """単一ファイルの修正を実行"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return 0, False

    content = original_content
    total_fixes = 0

    # 各修正パターンを適用
    fix_functions = [
        ("16進数カラーコード", fix_hexadecimal_color_codes),
        ("不正##マーカー", fix_invalid_markers),
        ("未完了マーカー", fix_incomplete_markers),
        ("装飾例文", fix_decoration_examples),
        ("その他パターン", fix_misc_patterns),
    ]

    print(f"📝 Processing: {file_path}")

    for name, func in fix_functions:
        content, fixes = func(content)
        if fixes > 0:
            print(f"   ✅ {name}: {fixes}個修正")
            total_fixes += fixes

    if dry_run:
        print(f"   📊 Total fixes: {total_fixes} (DRY RUN)")
        return total_fixes, True

    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 Saved with {total_fixes} fixes")
            return total_fixes, True
        except Exception as e:
            print(f"   ❌ Error writing: {e}")
            return 0, False
    else:
        print(f"   ℹ️  No changes needed")
        return 0, True

def main():
    parser = argparse.ArgumentParser(description='Kumihan記法エラー修正統合ツール')
    parser.add_argument('--files', nargs='+', help='修正対象ファイル')
    parser.add_argument('--pattern', help='修正対象ファイルのglobパターン')
    parser.add_argument('--all-samples', action='store_true', help='全サンプルファイルを対象')
    parser.add_argument('--dry-run', action='store_true', help='実際の修正を行わず、結果のみ表示')

    args = parser.parse_args()

    # 対象ファイルの決定
    target_files = []

    if args.files:
        target_files.extend([Path(f) for f in args.files])

    if args.pattern:
        target_files.extend([Path(f) for f in glob.glob(args.pattern)])

    if args.all_samples:
        target_files.extend([Path(f) for f in glob.glob('samples/**/*.txt', recursive=True)])

    if not target_files:
        print("❌ 修正対象ファイルが指定されていません")
        parser.print_help()
        sys.exit(1)

    # 重複除去
    target_files = list(set(target_files))
    target_files.sort()

    print(f"🎯 修正対象: {len(target_files)}ファイル")
    if args.dry_run:
        print("🔍 DRY RUN モード: 実際の修正は行いません")

    total_fixes = 0
    success_count = 0

    for file_path in target_files:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue

        fixes, success = fix_file(file_path, args.dry_run)
        total_fixes += fixes
        if success:
            success_count += 1

    print(f"\n📊 修正完了:")
    print(f"   ✅ 成功: {success_count}/{len(target_files)}ファイル")
    print(f"   🔧 総修正数: {total_fixes}個")

    if not args.dry_run and success_count > 0:
        print(f"\n💡 構文チェック推奨:")
        print(f"   python3 -m kumihan_formatter check-syntax {' '.join(str(f) for f in target_files[:3])}...")

if __name__ == "__main__":
    main()
