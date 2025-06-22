#!/usr/bin/env python3
"""
フォーマット記号移行スクリプト
旧形式（:::）から新形式（;;;）への変換を支援します。
"""

import sys
import argparse
from pathlib import Path
import re
from typing import List, Tuple


def convert_file(file_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    ファイル内のフォーマット記号を変換
    
    Args:
        file_path: 変換対象のファイルパス
        dry_run: True の場合、実際に変更せずに変更内容を表示
        
    Returns:
        (変更箇所数, 変更内容のリスト)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
    except Exception as e:
        print(f"エラー: {file_path} の読み込みに失敗しました: {e}")
        return 0, []
    
    changes = []
    change_count = 0
    
    # ブロック記法の変換（::: → ;;;）
    # ただし、Python文字列内の ::: は変換しない
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        
        # ブロックマーカーの変換
        if re.match(r'^([\s]*):::', line):
            # 行頭の空白を保持しつつ変換
            new_line = re.sub(r'^([\s]*):::', r'\1;;;', line)
            new_lines.append(new_line)
            if new_line != original_line:
                changes.append(f"行 {i+1}: '{original_line.strip()}' → '{new_line.strip()}'")
                change_count += 1
        # キーワード付きリストの変換（- :キーワード: → - ;;;キーワード;;;）
        elif re.match(r'^([\s]*)-\s+:', line):
            # :キーワード: 形式を ;;;キーワード;;; に変換
            new_line = re.sub(r'^([\s]*-\s+):([^:]+):\s*', r'\1;;;\2;;; ', line)
            new_lines.append(new_line)
            if new_line != original_line:
                changes.append(f"行 {i+1}: '{original_line.strip()}' → '{new_line.strip()}'")
                change_count += 1
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if not dry_run and new_content != original_content:
        try:
            # バックアップを作成
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 新しい内容を書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"✅ {file_path} を変換しました（バックアップ: {backup_path}）")
        except Exception as e:
            print(f"エラー: {file_path} の書き込みに失敗しました: {e}")
            return 0, []
    
    return change_count, changes


def main():
    parser = argparse.ArgumentParser(
        description='Kumihan-Formatter フォーマット記号移行ツール\n'
                    '旧形式（:::）から新形式（;;;）への変換を支援します。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'files', 
        nargs='+', 
        type=str,
        help='変換対象のファイル（複数指定可）'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='変更内容を表示するだけで、実際にファイルを変更しない'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細な変更内容を表示'
    )
    
    args = parser.parse_args()
    
    total_changes = 0
    
    for file_pattern in args.files:
        # ワイルドカード展開
        file_paths = list(Path().glob(file_pattern))
        
        if not file_paths:
            print(f"警告: {file_pattern} に一致するファイルが見つかりません")
            continue
            
        for file_path in file_paths:
            if not file_path.is_file():
                continue
                
            print(f"\n📄 処理中: {file_path}")
            
            change_count, changes = convert_file(file_path, args.dry_run)
            total_changes += change_count
            
            if change_count > 0:
                if args.verbose or args.dry_run:
                    print(f"  変更箇所: {change_count} 件")
                    for change in changes:
                        print(f"    {change}")
            else:
                print("  変更なし")
    
    print(f"\n{'[ドライラン] ' if args.dry_run else ''}合計 {total_changes} 箇所を{'変更予定' if args.dry_run else '変更しました'}")
    
    if args.dry_run and total_changes > 0:
        print("\n実際に変換を実行するには、--dry-run オプションを外して再実行してください。")


if __name__ == '__main__':
    main()