#!/usr/bin/env python3
"""
Kumihan-Formatter Pre-commit ツールキット - 統合版

このツールは以下の機能を統合しています:
- pre_commit_check.py: 事前チェック（Git、構文等）
- pre-commit-doc-check.py: ドキュメント整合性チェック
- pre-commit-syntax-check.py: Kumihan記法チェック

使用方法:
    # 基本事前チェック
    python dev/tools/pre_commit_toolkit.py
    
    # 構文チェックのみ
    python dev/tools/pre_commit_toolkit.py --syntax-only
    
    # ドキュメントチェックのみ
    python dev/tools/pre_commit_toolkit.py --docs-only
    
    # 完全チェック（推奨）
    python dev/tools/pre_commit_toolkit.py --full-check
    
    # Git hooksとして使用
    python dev/tools/pre_commit_toolkit.py --git-hook
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class Color:
    """コンソール色定義"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass
class CheckResult:
    """チェック結果"""
    name: str
    passed: bool
    message: str
    details: List[str] = None
    severity: str = "error"  # "error", "warning", "info"
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class GitChecker:
    """Git関連チェック"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def check_sync_status(self) -> CheckResult:
        """mainブランチとの同期状況チェック"""
        try:
            # 現在のブランチ取得
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_root, capture_output=True, text=True
            )
            current_branch = result.stdout.strip()
            
            if current_branch == 'main':
                return CheckResult(
                    "ブランチ同期", True, 
                    "mainブランチで作業中です", 
                    severity="info"
                )
            
            # mainとの差分チェック
            result = subprocess.run(
                ['git', 'rev-list', '--count', f'origin/main..{current_branch}'],
                cwd=self.repo_root, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                ahead_count = int(result.stdout.strip())
                if ahead_count > 0:
                    return CheckResult(
                        "ブランチ同期", True,
                        f"mainより{ahead_count}コミット先行中"
                    )
                else:
                    return CheckResult(
                        "ブランチ同期", True,
                        "mainブランチと同期済み"
                    )
            else:
                return CheckResult(
                    "ブランチ同期", False,
                    "同期状況の確認に失敗",
                    [result.stderr.strip()]
                )
                
        except Exception as e:
            return CheckResult(
                "ブランチ同期", False,
                "Git同期チェックでエラー",
                [str(e)]
            )
    
    def check_uncommitted_changes(self) -> CheckResult:
        """未コミット変更チェック"""
        try:
            # ステージされた変更
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.repo_root, capture_output=True, text=True
            )
            
            # 未ステージの変更
            unstaged_result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.repo_root, capture_output=True, text=True
            )
            
            # 未追跡ファイル
            untracked_result = subprocess.run(
                ['git', 'ls-files', '--others', '--exclude-standard'],
                cwd=self.repo_root, capture_output=True, text=True
            )
            
            staged_files = staged_result.stdout.strip().split('\n') if staged_result.stdout.strip() else []
            unstaged_files = unstaged_result.stdout.strip().split('\n') if unstaged_result.stdout.strip() else []
            untracked_files = untracked_result.stdout.strip().split('\n') if untracked_result.stdout.strip() else []
            
            details = []
            if staged_files:
                details.append(f"ステージ済み: {len(staged_files)}ファイル")
            if unstaged_files:
                details.append(f"未ステージ: {len(unstaged_files)}ファイル")
            if untracked_files:
                details.append(f"未追跡: {len(untracked_files)}ファイル")
            
            if not any([staged_files, unstaged_files, untracked_files]):
                return CheckResult(
                    "作業ディレクトリ", True,
                    "クリーンな状態です"
                )
            else:
                return CheckResult(
                    "作業ディレクトリ", False,
                    "未コミットの変更があります",
                    details,
                    "warning"
                )
                
        except Exception as e:
            return CheckResult(
                "作業ディレクトリ", False,
                "作業ディレクトリチェックでエラー",
                [str(e)]
            )


class SyntaxChecker:
    """構文チェック"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def check_python_syntax(self) -> CheckResult:
        """Python構文チェック"""
        errors = []
        
        # Python ファイルを検索
        python_files = list(self.repo_root.glob("**/*.py"))
        
        # 除外パターン
        exclude_patterns = [
            "__pycache__", ".egg-info", "dist/", "build/",
            ".venv", ".tox"
        ]
        
        source_files = [
            f for f in python_files 
            if not any(pattern in str(f) for pattern in exclude_patterns)
        ]
        
        for py_file in source_files[:10]:  # 最初の10ファイルのみチェック（高速化）
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(py_file)],
                    capture_output=True, text=True
                )
                
                if result.returncode != 0:
                    errors.append(f"{py_file.name}: {result.stderr.strip()}")
                    
            except Exception as e:
                errors.append(f"{py_file.name}: 構文チェックエラー - {e}")
        
        if not errors:
            return CheckResult(
                "Python構文", True,
                f"{len(source_files)}ファイルの構文チェック完了"
            )
        else:
            return CheckResult(
                "Python構文", False,
                f"{len(errors)}ファイルに構文エラー",
                errors[:5]  # 最初の5件のみ表示
            )
    
    def check_kumihan_syntax(self) -> CheckResult:
        """Kumihan記法チェック"""
        try:
            # syntax_toolkit.pyが存在するかチェック
            syntax_tool = self.repo_root / "dev" / "tools" / "syntax_toolkit.py"
            if not syntax_tool.exists():
                return CheckResult(
                    "Kumihan記法", False,
                    "syntax_toolkit.pyが見つかりません",
                    severity="warning"
                )
            
            # サンプルファイルをチェック
            sample_files = list(self.repo_root.glob("examples/*.txt"))
            
            if not sample_files:
                return CheckResult(
                    "Kumihan記法", True,
                    "チェック対象ファイルなし",
                    severity="info"
                )
            
            # 最大3ファイルまでチェック
            files_to_check = sample_files[:3]
            
            errors = []
            for txt_file in files_to_check:
                result = subprocess.run([
                    sys.executable, str(syntax_tool), str(txt_file)
                ], cwd=self.repo_root, capture_output=True, text=True)
                
                if result.returncode != 0:
                    errors.append(f"{txt_file.name}: 記法エラー")
            
            if not errors:
                return CheckResult(
                    "Kumihan記法", True,
                    f"{len(files_to_check)}ファイルの記法チェック完了"
                )
            else:
                return CheckResult(
                    "Kumihan記法", False,
                    f"{len(errors)}ファイルに記法エラー",
                    errors
                )
                
        except Exception as e:
            return CheckResult(
                "Kumihan記法", False,
                "記法チェックでエラー",
                [str(e)],
                "warning"
            )


class DocumentChecker:
    """ドキュメント整合性チェック"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def check_required_files(self) -> CheckResult:
        """必須ファイルチェック"""
        required_files = [
            "README.md",
            "CLAUDE.md", 
            "SPEC.md",
            "CONTRIBUTING.md",
            "pyproject.toml"
        ]
        
        missing_files = []
        for file_name in required_files:
            if not (self.repo_root / file_name).exists():
                missing_files.append(file_name)
        
        if not missing_files:
            return CheckResult(
                "必須ファイル", True,
                "必須ファイルが揃っています"
            )
        else:
            return CheckResult(
                "必須ファイル", False,
                f"{len(missing_files)}個の必須ファイルが不足",
                missing_files
            )
    
    def check_doc_consistency(self) -> CheckResult:
        """ドキュメント整合性チェック"""
        inconsistencies = []
        
        try:
            # README.mdとSPEC.mdの整合性チェック（簡易版）
            readme_path = self.repo_root / "README.md"
            spec_path = self.repo_root / "SPEC.md"
            
            if readme_path.exists() and spec_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                with open(spec_path, 'r', encoding='utf-8') as f:
                    spec_content = f.read()
                
                # 基本的な整合性チェック
                if "Kumihan-Formatter" not in readme_content:
                    inconsistencies.append("README.md: プロジェクト名が見つかりません")
                
                if ";;;見出し" not in spec_content:
                    inconsistencies.append("SPEC.md: 基本記法の説明が不足している可能性")
            
            # pyproject.tomlのバージョン情報チェック
            pyproject_path = self.repo_root / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    pyproject_content = f.read()
                
                # バージョン情報の存在チェック
                if 'version =' not in pyproject_content:
                    inconsistencies.append("pyproject.toml: バージョン情報が見つかりません")
            
        except Exception as e:
            inconsistencies.append(f"整合性チェックエラー: {e}")
        
        if not inconsistencies:
            return CheckResult(
                "ドキュメント整合性", True,
                "ドキュメントの整合性は良好です"
            )
        else:
            return CheckResult(
                "ドキュメント整合性", False,
                f"{len(inconsistencies)}個の整合性問題",
                inconsistencies,
                "warning"
            )


class PreCommitToolkit:
    """Pre-commit ツールキット統合クラス"""
    
    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or self._find_repo_root()
        self.git_checker = GitChecker(self.repo_root)
        self.syntax_checker = SyntaxChecker(self.repo_root)
        self.doc_checker = DocumentChecker(self.repo_root)
    
    def _find_repo_root(self) -> Path:
        """リポジトリルート検索"""
        current = Path(__file__).parent
        while current.parent != current:
            if (current / ".git").exists():
                return current
            current = current.parent
        
        # .gitが見つからない場合は、pyproject.tomlで判断
        current = Path(__file__).parent
        while current.parent != current:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        
        return Path(__file__).parent.parent.parent
    
    def run_basic_checks(self) -> List[CheckResult]:
        """基本チェック実行"""
        checks = [
            self.git_checker.check_sync_status,
            self.git_checker.check_uncommitted_changes,
            self.syntax_checker.check_python_syntax,
            self.doc_checker.check_required_files
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(CheckResult(
                    "チェック実行", False,
                    f"チェック実行エラー: {e}",
                    severity="error"
                ))
        
        return results
    
    def run_syntax_checks(self) -> List[CheckResult]:
        """構文チェック実行"""
        return [
            self.syntax_checker.check_python_syntax(),
            self.syntax_checker.check_kumihan_syntax()
        ]
    
    def run_doc_checks(self) -> List[CheckResult]:
        """ドキュメントチェック実行"""
        return [
            self.doc_checker.check_required_files(),
            self.doc_checker.check_doc_consistency()
        ]
    
    def run_full_checks(self) -> List[CheckResult]:
        """完全チェック実行"""
        all_results = []
        
        # 各カテゴリのチェックを実行
        all_results.extend(self.run_basic_checks())
        all_results.extend(self.run_syntax_checks())
        all_results.extend(self.run_doc_checks())
        
        return all_results
    
    def generate_report(self, results: List[CheckResult]) -> str:
        """チェック結果レポート生成"""
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 50)
        report_lines.append("🔍 Pre-commit チェック結果")
        report_lines.append("=" * 50)
        report_lines.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 結果サマリー
        passed_count = sum(1 for r in results if r.passed)
        error_count = sum(1 for r in results if not r.passed and r.severity == "error")
        warning_count = sum(1 for r in results if not r.passed and r.severity == "warning")
        
        report_lines.append("📊 チェック結果サマリー")
        report_lines.append("-" * 30)
        report_lines.append(f"✅ 合格: {passed_count}")
        report_lines.append(f"❌ エラー: {error_count}")
        report_lines.append(f"⚠️  警告: {warning_count}")
        report_lines.append(f"📝 総計: {len(results)}")
        report_lines.append("")
        
        # 詳細結果
        report_lines.append("📋 詳細結果")
        report_lines.append("-" * 30)
        
        for result in results:
            if result.passed:
                icon = "✅"
            elif result.severity == "error":
                icon = "❌"
            elif result.severity == "warning":
                icon = "⚠️"
            else:
                icon = "ℹ️"
            
            report_lines.append(f"{icon} {result.name}: {result.message}")
            
            if result.details:
                for detail in result.details:
                    report_lines.append(f"    • {detail}")
        
        report_lines.append("")
        
        # 推奨事項
        if error_count > 0:
            report_lines.append("🚨 修正が必要な問題があります")
            report_lines.append("コミット前に必ずエラーを修正してください")
        elif warning_count > 0:
            report_lines.append("⚠️  警告があります")
            report_lines.append("可能であれば修正を検討してください")
        else:
            report_lines.append("🎉 すべてのチェックが合格しました！")
            report_lines.append("コミット・プッシュが可能です")
        
        return "\n".join(report_lines)
    
    def should_block_commit(self, results: List[CheckResult]) -> bool:
        """コミットをブロックすべきかの判定"""
        # エラーレベルの問題がある場合はブロック
        error_count = sum(1 for r in results if not r.passed and r.severity == "error")
        return error_count > 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter Pre-commit ツールキット",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--syntax-only', action='store_true', help='構文チェックのみ')
    parser.add_argument('--docs-only', action='store_true', help='ドキュメントチェックのみ')
    parser.add_argument('--full-check', action='store_true', help='完全チェック')
    parser.add_argument('--git-hook', action='store_true', help='Git hookとして実行')
    parser.add_argument('--report-file', help='レポートファイル出力先')
    
    args = parser.parse_args()
    
    toolkit = PreCommitToolkit()
    
    # チェック実行
    if args.syntax_only:
        results = toolkit.run_syntax_checks()
    elif args.docs_only:
        results = toolkit.run_doc_checks()
    elif args.full_check:
        results = toolkit.run_full_checks()
    else:
        # デフォルトは基本チェック
        results = toolkit.run_basic_checks()
    
    # レポート生成
    report = toolkit.generate_report(results)
    
    # 出力
    if args.report_file:
        with open(args.report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 レポートを {args.report_file} に出力しました")
    else:
        print(report)
    
    # Git hookモードの場合、エラーがあればブロック
    if args.git_hook:
        if toolkit.should_block_commit(results):
            print(f"\n{Color.RED}❌ エラーがあるためコミットをブロックしました{Color.END}")
            return 1
        else:
            print(f"\n{Color.GREEN}✅ チェック完了、コミット可能です{Color.END}")
            return 0
    
    # 通常モードでもエラーがあれば終了コード1
    error_count = sum(1 for r in results if not r.passed and r.severity == "error")
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())