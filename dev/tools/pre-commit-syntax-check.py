#!/usr/bin/env python3
"""
Pre-commit hook: サンプルファイル・テンプレートファイルの記法チェック

使用方法:
    git add で追加されたテキストファイルに対して自動的に記法検証を実行
    エラーがある場合はコミットを中断し、修正を促す
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Set


def get_staged_txt_files() -> List[Path]:
    """ステージングされた.txtファイルのリストを取得"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True,
            text=True,
            check=True
        )
        
        staged_files = []
        for file_path in result.stdout.strip().split('\n'):
            if file_path and file_path.endswith('.txt'):
                path = Path(file_path)
                if path.exists():
                    staged_files.append(path)
        
        return staged_files
    except subprocess.CalledProcessError:
        return []


def is_sample_or_template_file(file_path: Path) -> bool:
    """サンプル・テンプレートファイルかどうか判定"""
    path_str = str(file_path)
    
    # チェック対象パスのパターン
    check_patterns = [
        '記法ツール/サンプルファイル/',
        'examples/',
        'template',  # ファイル名にtemplateが含まれる
        'sample',    # ファイル名にsampleが含まれる
    ]
    
    return any(pattern in path_str for pattern in check_patterns)


def run_syntax_check(files: List[Path]) -> bool:
    """記法チェックを実行"""
    if not files:
        return True
    
    print("🔍 Pre-commit: Kumihan記法チェックを実行中...")
    
    try:
        # syntax_fixerで検証実行
        result = subprocess.run(
            ['python', 'dev/tools/syntax_fixer.py'] + [str(f) for f in files],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 記法チェック: 全てのファイルが正常です")
            return True
        else:
            print("❌ 記法エラーが検出されました:")
            print(result.stdout)
            if result.stderr:
                print("エラー詳細:")
                print(result.stderr)
            print("\n💡 修正方法:")
            print("  1. 記法修正ツールで自動修正:")
            print(f"     python dev/tools/syntax_fixer.py {' '.join(str(f) for f in files)} --fix")
            print("  2. または記法修正.commandを使用")
            print("  3. 修正後に再度 git add & git commit")
            return False
            
    except Exception as e:
        print(f"❌ 記法チェック実行エラー: {e}")
        return False


def main() -> int:
    """メイン処理"""
    # ステージングされたファイルを取得
    staged_files = get_staged_txt_files()
    
    if not staged_files:
        # .txtファイルの変更がない場合はスキップ
        return 0
    
    # サンプル・テンプレートファイルのみをフィルタ
    target_files = [f for f in staged_files if is_sample_or_template_file(f)]
    
    if not target_files:
        # チェック対象ファイルがない場合はスキップ
        return 0
    
    print(f"📝 Pre-commit check: {len(target_files)} ファイルをチェック中...")
    for file_path in target_files:
        print(f"  - {file_path}")
    
    # 記法チェック実行
    if run_syntax_check(target_files):
        return 0  # 成功: コミット続行
    else:
        return 1  # 失敗: コミット中断


if __name__ == "__main__":
    sys.exit(main())