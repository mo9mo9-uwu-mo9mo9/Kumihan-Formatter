#!/usr/bin/env python3
"""
開発用一時ファイル・ディレクトリのクリーンアップツール

使用方法:
    python dev/tools/cleanup.py [--dry-run]

オプション:
    --dry-run: 実際には削除せず、削除対象を表示するのみ
"""

import os
import shutil
import sys
from pathlib import Path
import argparse


# 削除対象のパターン
CLEANUP_PATTERNS = {
    'directories': [
        '*-output',
        'test_*',
        'dist_test*',
        'dist_syntax_*',
        'test-block-*',
        'expanded_test*',
        'final-test',
        'debug_output',
        'analysis-output',
        'test-output',
    ],
    'files': [
        '*.pyc',
        '__pycache__',
        '.pytest_cache',
        '*.tmp',
        '*.temp',
    ]
}

# 除外パターン（削除しない）
EXCLUDE_PATTERNS = [
    'test_*.py',  # テストコードは削除しない
    'dev/test_data/*',  # テストデータは削除しない
    '.git/*',
    '.claude/*',
    'venv/*',
    '.venv/*',
]


def is_excluded(path: Path) -> bool:
    """指定されたパスが除外パターンに一致するかチェック"""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith('/*'):
            # ディレクトリ配下のファイルをチェック
            dir_pattern = pattern[:-2]
            if path_str.startswith(dir_pattern):
                return True
        elif pattern.endswith('.py') and path.name.startswith('test_') and path.suffix == '.py':
            # test_*.py ファイルは除外
            return True
    return False


def find_cleanup_targets(root_dir: Path, dry_run: bool = True) -> list[Path]:
    """削除対象のファイル・ディレクトリを検索"""
    targets = []
    
    # ルートディレクトリのファイル・ディレクトリをチェック
    for item in root_dir.iterdir():
        if is_excluded(item):
            continue
            
        # ディレクトリパターンをチェック
        if item.is_dir():
            for pattern in CLEANUP_PATTERNS['directories']:
                if item.match(pattern):
                    targets.append(item)
                    if dry_run:
                        print(f"[DIR]  {item}")
                    break
        
        # ファイルパターンをチェック
        elif item.is_file():
            for pattern in CLEANUP_PATTERNS['files']:
                if item.match(pattern):
                    targets.append(item)
                    if dry_run:
                        print(f"[FILE] {item}")
                    break
    
    return targets


def cleanup(targets: list[Path], dry_run: bool = True) -> None:
    """指定されたターゲットを削除"""
    if dry_run:
        print(f"\n{len(targets)} 個のアイテムが削除対象です。")
        print("実際に削除するには --no-dry-run オプションを付けて実行してください。")
        return
    
    deleted_count = 0
    error_count = 0
    
    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
                print(f"削除: [DIR]  {target}")
            else:
                target.unlink()
                print(f"削除: [FILE] {target}")
            deleted_count += 1
        except Exception as e:
            print(f"エラー: {target} - {e}")
            error_count += 1
    
    print(f"\n完了: {deleted_count} 個のアイテムを削除しました。")
    if error_count > 0:
        print(f"エラー: {error_count} 個のアイテムの削除に失敗しました。")


def main():
    parser = argparse.ArgumentParser(description='開発用一時ファイルのクリーンアップ')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='削除対象を表示するのみ（デフォルト）')
    parser.add_argument('--no-dry-run', action='store_false', dest='dry_run',
                        help='実際に削除を実行')
    
    args = parser.parse_args()
    
    # プロジェクトルートを検出
    current_dir = Path.cwd()
    if current_dir.name == 'tools' and current_dir.parent.name == 'dev':
        root_dir = current_dir.parent.parent
    elif current_dir.name == 'dev':
        root_dir = current_dir.parent
    else:
        root_dir = current_dir
    
    print(f"プロジェクトルート: {root_dir}")
    print("削除対象を検索中...\n")
    
    targets = find_cleanup_targets(root_dir, args.dry_run)
    
    if targets:
        cleanup(targets, args.dry_run)
    else:
        print("削除対象のファイル・ディレクトリは見つかりませんでした。")


if __name__ == '__main__':
    main()