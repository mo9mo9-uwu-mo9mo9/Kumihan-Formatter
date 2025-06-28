#!/usr/bin/env python3
"""
Pre-commit Check Script - 事前チェックスクリプト

自動マージ失敗を防ぐため、PR作成前に必要なチェックを実行します。

使用方法:
    python dev/tools/pre_commit_check.py

チェック項目:
    1. mainブランチとの同期状況
    2. 未コミットの変更
    3. 基本的な構文エラー
    4. 必要なファイルの存在確認
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional

class Color:
    """コンソール色定義"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class PreCommitChecker:
    """事前チェッククラス"""
    
    def __init__(self):
        self.repo_root = self._find_repo_root()
        self.errors = []
        self.warnings = []
        
    def _find_repo_root(self) -> Path:
        """リポジトリルートを検索"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        raise RuntimeError("Gitリポジトリが見つかりません")
    
    def _run_command(self, cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
        """コマンド実行"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.repo_root,
                check=check
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
        except FileNotFoundError:
            return 1, "", f"コマンドが見つかりません: {' '.join(cmd)}"
    
    def check_git_status(self) -> bool:
        """Git状態チェック"""
        print(f"{Color.BLUE}🔍 Git状態をチェック中...{Color.END}")
        
        # 現在のブランチ確認
        code, branch, _ = self._run_command(['git', 'branch', '--show-current'])
        if code != 0:
            self.errors.append("現在のブランチを取得できません")
            return False
        
        if branch == 'main':
            self.errors.append("mainブランチで作業中です。feature/ブランチを作成してください")
            return False
        
        # 未コミットの変更チェック
        code, status, _ = self._run_command(['git', 'status', '--porcelain'])
        if code != 0:
            self.errors.append("Git statusを取得できません")
            return False
        
        if status:
            uncommitted_files = status.split('\n')
            print(f"  {Color.YELLOW}⚠️ 未コミットの変更: {len(uncommitted_files)} ファイル{Color.END}")
            for file_status in uncommitted_files[:5]:  # 最初の5ファイルのみ表示
                print(f"    {file_status}")
            if len(uncommitted_files) > 5:
                print(f"    ... 他 {len(uncommitted_files) - 5} ファイル")
            self.warnings.append("未コミットの変更があります")
        
        print(f"  {Color.GREEN}✅ ブランチ: {branch}{Color.END}")
        return True
    
    def check_branch_sync(self) -> bool:
        """mainブランチとの同期チェック"""
        print(f"{Color.BLUE}🔄 mainブランチとの同期状況をチェック中...{Color.END}")
        
        # remoteを更新
        code, _, stderr = self._run_command(['git', 'fetch', 'origin', 'main'], check=False)
        if code != 0:
            self.warnings.append(f"remote更新に失敗: {stderr}")
        
        # mainとの比較
        code, behind_commits, _ = self._run_command([
            'git', 'rev-list', '--count', 'HEAD..origin/main'
        ], check=False)
        
        if code != 0:
            self.warnings.append("mainブランチとの比較ができません")
            return True
        
        behind_count = int(behind_commits) if behind_commits.isdigit() else 0
        if behind_count > 0:
            self.warnings.append(f"mainブランチより {behind_count} コミット遅れています")
            print(f"  {Color.YELLOW}⚠️ mainより {behind_count} コミット遅れ{Color.END}")
            print(f"  {Color.YELLOW}💡 推奨: git checkout main && git pull origin main && git checkout - && git rebase main{Color.END}")
            return False
        
        print(f"  {Color.GREEN}✅ mainブランチと同期済み{Color.END}")
        return True
    
    def check_syntax_errors(self) -> bool:
        """基本的な構文エラーチェック"""
        print(f"{Color.BLUE}🔍 基本構文チェック中...{Color.END}")
        
        # Python構文チェック
        python_files = list(self.repo_root.rglob('*.py'))
        syntax_errors = []
        
        for py_file in python_files:
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            code, _, stderr = self._run_command([
                sys.executable, '-m', 'py_compile', str(py_file)
            ], check=False)
            
            if code != 0:
                syntax_errors.append(f"{py_file.relative_to(self.repo_root)}: {stderr}")
        
        if syntax_errors:
            self.errors.extend(syntax_errors)
            print(f"  {Color.RED}❌ Python構文エラー: {len(syntax_errors)} ファイル{Color.END}")
            return False
        
        print(f"  {Color.GREEN}✅ Python構文エラーなし{Color.END}")
        return True
    
    def check_required_files(self) -> bool:
        """必要ファイルの存在確認"""
        print(f"{Color.BLUE}📁 必要ファイルをチェック中...{Color.END}")
        
        required_files = [
            'CLAUDE.md',
            'SPEC.md',
            'CONTRIBUTING.md',
            'kumihan_formatter/cli.py',
            'kumihan_formatter/parser.py',
            'kumihan_formatter/renderer.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.repo_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.errors.extend([f"必要ファイルが見つかりません: {f}" for f in missing_files])
            print(f"  {Color.RED}❌ 不足ファイル: {len(missing_files)} 個{Color.END}")
            return False
        
        print(f"  {Color.GREEN}✅ 必要ファイル全て存在{Color.END}")
        return True
    
    def suggest_next_steps(self) -> None:
        """次のステップを提案"""
        print(f"\n{Color.BOLD}📋 次のステップ:{Color.END}")
        
        if self.errors:
            print(f"{Color.RED}🚨 以下のエラーを修正してください:{Color.END}")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print(f"{Color.YELLOW}⚠️ 警告事項:{Color.END}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        if not self.errors:
            print(f"{Color.GREEN}✅ PR作成準備完了！{Color.END}")
            print(f"{Color.BOLD}推奨コマンド:{Color.END}")
            print(f"  git add . && git commit -m \"作業内容\"")
            print(f"  git push -u origin $(git branch --show-current)")
            print(f"  gh pr create --title \"タイトル\" --body \"説明\" && gh pr merge --auto --squash")
    
    def run_all_checks(self) -> bool:
        """全チェック実行"""
        print(f"{Color.BOLD}🔍 Pre-commit Check 開始{Color.END}")
        print(f"リポジトリ: {self.repo_root}")
        print()
        
        checks = [
            self.check_git_status(),
            self.check_branch_sync(),
            self.check_syntax_errors(),
            self.check_required_files()
        ]
        
        success = all(checks)
        
        print(f"\n{Color.BOLD}📊 チェック結果:{Color.END}")
        if success and not self.warnings:
            print(f"{Color.GREEN}✅ 全てのチェックが正常に完了しました{Color.END}")
        elif success:
            print(f"{Color.YELLOW}⚠️ チェック完了（警告あり）{Color.END}")
        else:
            print(f"{Color.RED}❌ エラーが検出されました{Color.END}")
        
        self.suggest_next_steps()
        
        return success and not self.errors

def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        return
    
    try:
        checker = PreCommitChecker()
        success = checker.run_all_checks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"{Color.RED}❌ 予期しないエラー: {e}{Color.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()