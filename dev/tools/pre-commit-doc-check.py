#!/usr/bin/env python3
"""
Git pre-commit hook用のドキュメント整合性チェック

コミット前に変更されたドキュメントの整合性をチェックし、
問題があれば警告またはコミットを停止します。
"""

import subprocess
import sys
from pathlib import Path
from doc_consistency_checker import DocumentConsistencyChecker

def get_staged_files():
    """ステージングされたファイル一覧を取得"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def is_documentation_file(file_path: str) -> bool:
    """ドキュメントファイルかどうかを判定"""
    doc_extensions = ['.md', '.txt', '.rst']
    doc_dirs = ['docs/', 'examples/']
    
    # 拡張子チェック
    if any(file_path.endswith(ext) for ext in doc_extensions):
        return True
    
    # ドキュメントディレクトリチェック
    if any(file_path.startswith(doc_dir) for doc_dir in doc_dirs):
        return True
    
    # 設定ファイルチェック
    config_files = ['pyproject.toml', 'kumihan_formatter/__init__.py']
    if file_path in config_files:
        return True
    
    return False

def main():
    """pre-commit hook のメイン処理"""
    project_root = Path(__file__).parent.parent.parent
    
    # ステージングされたファイルを取得
    staged_files = get_staged_files()
    
    # ドキュメント関連ファイルが変更されているかチェック
    doc_files_changed = any(is_documentation_file(f) for f in staged_files)
    
    if not doc_files_changed:
        # ドキュメント関連の変更がなければスキップ
        sys.exit(0)
    
    print("📋 ドキュメント関連ファイルが変更されています。整合性をチェックします...")
    
    # 整合性チェックを実行
    checker = DocumentConsistencyChecker(project_root)
    issues = checker.run_all_checks()
    
    if not issues:
        print("✅ ドキュメント整合性チェック: 問題なし")
        sys.exit(0)
    
    # 問題が見つかった場合
    high_issues = [i for i in issues if i.severity == 'high']
    medium_issues = [i for i in issues if i.severity == 'medium']
    low_issues = [i for i in issues if i.severity == 'low']
    
    print(f"⚠️  ドキュメント整合性チェックで {len(issues)} 件の問題が発見されました。")
    print()
    
    # 高重要度の問題がある場合はコミットを停止
    if high_issues:
        print("🔴 重大な問題が発見されました。コミットを中止します。")
        print()
        for issue in high_issues:
            print(f"📁 {issue.file_path}:{issue.line_number}")
            print(f"   問題: {issue.description}")
            if issue.suggestion:
                print(f"   提案: {issue.suggestion}")
            print()
        
        print("💡 修正後に再度コミットしてください。")
        print("   詳細なレポートを確認: python dev/tools/doc_consistency_checker.py")
        sys.exit(1)
    
    # 中・低重要度の問題は警告として表示
    if medium_issues or low_issues:
        print("🟡 以下の問題が発見されましたが、コミットは継続します。")
        print()
        
        for issue in medium_issues + low_issues:
            severity_icon = "🟡" if issue.severity == "medium" else "🟢"
            print(f"{severity_icon} {issue.file_path}:{issue.line_number}")
            print(f"   問題: {issue.description}")
            if issue.suggestion:
                print(f"   提案: {issue.suggestion}")
            print()
        
        print("💡 時間があるときに修正することをお勧めします。")
        print("   詳細なレポートを確認: python dev/tools/doc_consistency_checker.py")
    
    sys.exit(0)

if __name__ == '__main__':
    main()