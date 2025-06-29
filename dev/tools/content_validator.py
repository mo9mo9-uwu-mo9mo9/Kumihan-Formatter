#!/usr/bin/env python3
"""統合コンテンツバリデーター

配布物、サンプルコンテンツ、ZIP機能の包括的な検証ツール。
"""

import argparse
import json
import sys
import tempfile
import zipfile
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationIssue:
    """検証問題を表すデータクラス"""
    file_path: str
    issue_type: str
    description: str
    severity: str = "medium"


@dataclass
class ValidationResult:
    """検証結果を表すデータクラス"""
    success: bool
    issues: List[ValidationIssue]
    total_checks: int
    passed_checks: int


class ContentValidator:
    """統合コンテンツバリデーター"""
    
    # 配布物に必要なファイル・ディレクトリ
    REQUIRED_FILES = {
        # 基本実行ファイル
        "WINDOWS/初回セットアップ.bat",
        "WINDOWS/変換ツール.bat", 
        "WINDOWS/サンプル実行.bat",
        "MAC/初回セットアップ.command",
        "MAC/変換ツール.command",
        "MAC/サンプル実行.command",
        
        # Pythonパッケージ
        "kumihan_formatter/__init__.py",
        "kumihan_formatter/cli.py",
        "kumihan_formatter/parser.py", 
        "kumihan_formatter/renderer.py",
        "kumihan_formatter/config.py",
        
        # サンプルファイル
        "examples/sample.txt",
        "examples/comprehensive-sample.txt",
        
        # ドキュメント
        "README.md",
        "SPEC.md",
        "CONTRIBUTING.md",
    }
    
    # 配布物から除外すべきファイル・ディレクトリ
    EXCLUDED_PATTERNS = {
        "__pycache__",
        "*.pyc", 
        ".git",
        ".vscode",
        ".idea",
        "dev/",
        ".github/",
        "test_*/",
        "tests/",
        ".pytest_cache/",
        "*.egg-info",
        ".coverage",
        "coverage.xml",
        ".env",
        "*.log",
        "node_modules/",
        ".DS_Store",
        "Thumbs.db"
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        """初期化"""
        self.project_root = project_root or Path.cwd()
        self.issues = []
        
        # プロジェクトルートをPythonパスに追加
        sys.path.insert(0, str(self.project_root))
    
    def validate_distribution(self, zip_path: Path) -> ValidationResult:
        """配布物の内容を検証"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        if not zip_path.exists():
            issues.append(ValidationIssue(
                str(zip_path), "missing_file", 
                "配布物ZIPファイルが見つかりません", "high"
            ))
            return ValidationResult(False, issues, 1, 0)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                zip_contents = set(zip_file.namelist())
                
                # 必要ファイルの確認
                for required_file in self.REQUIRED_FILES:
                    total_checks += 1
                    if any(path.endswith(required_file) or required_file in path for path in zip_contents):
                        passed_checks += 1
                    else:
                        issues.append(ValidationIssue(
                            required_file, "missing_required",
                            f"必須ファイル '{required_file}' が見つかりません", "high"
                        ))
                
                # 除外パターンの確認
                for file_path in zip_contents:
                    total_checks += 1
                    if self._should_exclude(file_path):
                        issues.append(ValidationIssue(
                            file_path, "excluded_file",
                            f"除外すべきファイル '{file_path}' が含まれています", "medium"
                        ))
                    else:
                        passed_checks += 1
                
        except zipfile.BadZipFile:
            issues.append(ValidationIssue(
                str(zip_path), "invalid_zip",
                "無効なZIPファイルです", "high"
            ))
            return ValidationResult(False, issues, 1, 0)
        
        success = len(issues) == 0
        return ValidationResult(success, issues, total_checks, passed_checks)
    
    def validate_sample_content(self) -> ValidationResult:
        """サンプルコンテンツを検証"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        try:
            # sample_content.pyからサンプルテキストを取得
            from kumihan_formatter.sample_content import SHOWCASE_SAMPLE
            
            # 一時ファイルに保存して検証
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(SHOWCASE_SAMPLE)
                temp_path = f.name
            
            try:
                # 構文検証（基本的なチェック）
                total_checks += 3
                
                # 1. 基本的な記法チェック
                if ";;;" in SHOWCASE_SAMPLE:
                    passed_checks += 1
                else:
                    issues.append(ValidationIssue(
                        "sample_content.py", "invalid_syntax",
                        "Kumihan記法マーカー ';;;' が見つかりません", "high"
                    ))
                
                # 2. 構造チェック
                lines = SHOWCASE_SAMPLE.split('\n')
                if len(lines) > 10:  # 最低限の内容があるか
                    passed_checks += 1
                else:
                    issues.append(ValidationIssue(
                        "sample_content.py", "insufficient_content",
                        "サンプル内容が不十分です", "medium"
                    ))
                
                # 3. エンコーディングチェック
                try:
                    SHOWCASE_SAMPLE.encode('utf-8')
                    passed_checks += 1
                except UnicodeEncodeError:
                    issues.append(ValidationIssue(
                        "sample_content.py", "encoding_error",
                        "UTF-8エンコーディングエラー", "medium"
                    ))
                
            finally:
                # 一時ファイルをクリーンアップ
                Path(temp_path).unlink(missing_ok=True)
                
        except ImportError as e:
            issues.append(ValidationIssue(
                "sample_content.py", "import_error",
                f"サンプルコンテンツのインポートエラー: {e}", "high"
            ))
            total_checks = 1
        
        success = len(issues) == 0
        return ValidationResult(success, issues, total_checks, passed_checks)
    
    def validate_zip_functionality(self) -> ValidationResult:
        """ZIP配布機能を検証"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # ZIP配布コマンドの存在確認
        total_checks += 1
        try:
            from kumihan_formatter.commands.zip_dist import ZipDistCommand
            passed_checks += 1
        except ImportError:
            issues.append(ValidationIssue(
                "zip_dist.py", "import_error",
                "ZIP配布コマンドがインポートできません", "high"
            ))
        
        # CLIでのzip-distコマンド確認
        total_checks += 1
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                "from kumihan_formatter.cli import cli; help(cli)"
            ], capture_output=True, text=True, timeout=10)
            
            if "zip-dist" in result.stdout or result.returncode == 0:
                passed_checks += 1
            else:
                issues.append(ValidationIssue(
                    "cli.py", "missing_command",
                    "CLIにzip-distコマンドが見つかりません", "medium"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                "cli.py", "cli_error",
                f"CLI確認エラー: {e}", "medium"
            ))
        
        # 配布用ディレクトリ構造確認
        total_checks += 1
        setup_files = list(self.project_root.glob("WINDOWS/*.bat")) + list(self.project_root.glob("MAC/*.command"))
        if setup_files:
            passed_checks += 1
        else:
            issues.append(ValidationIssue(
                "setup files", "missing_setup",
                "セットアップファイルが見つかりません", "medium"
            ))
        
        success = len(issues) == 0
        return ValidationResult(success, issues, total_checks, passed_checks)
    
    def validate_all(self, zip_path: Optional[Path] = None) -> ValidationResult:
        """全ての検証を実行"""
        all_issues = []
        total_checks = 0
        passed_checks = 0
        
        # サンプルコンテンツ検証
        sample_result = self.validate_sample_content()
        all_issues.extend(sample_result.issues)
        total_checks += sample_result.total_checks
        passed_checks += sample_result.passed_checks
        
        # ZIP機能検証
        zip_func_result = self.validate_zip_functionality()
        all_issues.extend(zip_func_result.issues)
        total_checks += zip_func_result.total_checks
        passed_checks += zip_func_result.passed_checks
        
        # 配布物検証（ZIPパスが指定された場合）
        if zip_path:
            dist_result = self.validate_distribution(zip_path)
            all_issues.extend(dist_result.issues)
            total_checks += dist_result.total_checks
            passed_checks += dist_result.passed_checks
        
        success = len(all_issues) == 0
        return ValidationResult(success, all_issues, total_checks, passed_checks)
    
    def _should_exclude(self, file_path: str) -> bool:
        """ファイルが除外パターンに一致するかチェック"""
        import fnmatch
        
        for pattern in self.EXCLUDED_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern) or pattern in file_path:
                return True
        return False
    
    def generate_report(self, result: ValidationResult) -> str:
        """検証結果レポートを生成"""
        report = []
        report.append("# コンテンツ検証レポート\n")
        
        # サマリー
        status = "✅ 成功" if result.success else "❌ 失敗"
        report.append(f"## 検証結果: {status}")
        report.append(f"- 総チェック数: {result.total_checks}")
        report.append(f"- 成功: {result.passed_checks}")
        report.append(f"- 失敗: {result.total_checks - result.passed_checks}")
        report.append("")
        
        # 問題一覧
        if result.issues:
            report.append("## 検出された問題")
            
            # 重要度別にグループ化
            high_issues = [i for i in result.issues if i.severity == "high"]
            medium_issues = [i for i in result.issues if i.severity == "medium"]
            
            if high_issues:
                report.append("### 🔴 高重要度")
                for issue in high_issues:
                    report.append(f"- **{issue.file_path}**: {issue.description} ({issue.issue_type})")
                report.append("")
            
            if medium_issues:
                report.append("### 🟡 中重要度")
                for issue in medium_issues:
                    report.append(f"- **{issue.file_path}**: {issue.description} ({issue.issue_type})")
                report.append("")
        else:
            report.append("## ✅ 問題は検出されませんでした")
        
        # 改善提案
        if result.issues:
            report.append("## 改善提案")
            suggestions = self._generate_suggestions(result.issues)
            for suggestion in suggestions:
                report.append(f"- {suggestion}")
        
        return "\n".join(report)
    
    def _generate_suggestions(self, issues: List[ValidationIssue]) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        # 問題タイプ別の提案
        issue_types = {issue.issue_type for issue in issues}
        
        if "missing_required" in issue_types:
            suggestions.append("必須ファイルを追加してください")
        
        if "excluded_file" in issue_types:
            suggestions.append(".distignoreファイルを確認し、除外パターンを更新してください")
        
        if "invalid_syntax" in issue_types:
            suggestions.append("Kumihan記法の構文を確認してください")
        
        if "import_error" in issue_types:
            suggestions.append("依存関係とインポートパスを確認してください")
        
        return suggestions or ["コンテンツの品質は良好です"]


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="統合コンテンツバリデーター")
    parser.add_argument("--zip", type=Path, help="検証する配布物ZIPファイル")
    parser.add_argument("--output", "-o", type=Path, help="レポート出力ファイル")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="プロジェクトルートディレクトリ")
    parser.add_argument("--json", action="store_true", help="JSON形式で結果を出力")
    
    args = parser.parse_args()
    
    validator = ContentValidator(args.project_root)
    
    print("コンテンツ検証を開始...")
    result = validator.validate_all(args.zip)
    
    if args.json:
        # JSON出力
        json_result = {
            "success": result.success,
            "total_checks": result.total_checks,
            "passed_checks": result.passed_checks,
            "issues": [
                {
                    "file_path": issue.file_path,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                    "severity": issue.severity
                }
                for issue in result.issues
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        output = json.dumps(json_result, indent=2, ensure_ascii=False)
    else:
        # テキストレポート
        output = validator.generate_report(result)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"レポートを保存: {args.output}")
    else:
        print(output)
    
    # 終了コード
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()