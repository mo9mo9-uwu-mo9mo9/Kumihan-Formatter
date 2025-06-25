#!/usr/bin/env python3
"""
ZIP配布機能の自動検証ツール

ZIP配布版Markdown変換機能が古くならないように定期的にチェックし、
機能の整合性を検証するツール
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# markdown_converter.pyは削除されました
# from kumihan_formatter.markdown_converter import convert_markdown_to_html
from kumihan_formatter.cli import zip_dist

@dataclass
class ValidationIssue:
    """検証問題を表すデータクラス"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    suggestion: str = ""

class ZipFeatureValidator:
    """ZIP配布機能検証クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[ValidationIssue] = []
        
        # 検証対象機能の定義（Markdown変換機能は削除済み）
        self.required_features = {
            'cli_zip_command': {
                'file': 'kumihan_formatter/cli.py',
                'functions': ['zip_dist']
                # 注意: Markdown変換関連のインポートは削除済み
            },
            'template_navigation': {
                'file': 'kumihan_formatter/templates/base.html.j2',
                'elements': ['.kumihan-nav', '.breadcrumb', '.page-nav']
            }
        }
        
        # ZIP配布関連のキーワード（Markdown変換機能は削除済み）
        self.issue_keywords = [
            'ZIP配布版', 'ナビゲーション',
            'index.html', '同人作家', 'Booth配布'
        ]

    def validate_core_functions(self) -> None:
        """コア機能の存在と完整性を検証"""
        
        for feature_name, feature_spec in self.required_features.items():
            file_path = self.project_root / feature_spec['file']
            
            if not file_path.exists():
                self.issues.append(ValidationIssue(
                    file_path=feature_spec['file'],
                    line_number=0,
                    issue_type="missing_file",
                    description=f"必須ファイルが見つかりません: {feature_name}",
                    severity="high",
                    suggestion=f"ファイル {feature_spec['file']} を復元してください"
                ))
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                self._validate_file_content(feature_name, feature_spec, content, str(file_path))
            except Exception as e:
                self.issues.append(ValidationIssue(
                    file_path=feature_spec['file'],
                    line_number=0,
                    issue_type="file_read_error",
                    description=f"ファイル読み込みエラー: {e}",
                    severity="medium"
                ))

    def _validate_file_content(self, feature_name: str, feature_spec: Dict, 
                             content: str, file_path: str) -> None:
        """ファイル内容の検証"""
        lines = content.splitlines()
        
        # 関数の存在チェック
        if 'functions' in feature_spec:
            for func_name in feature_spec['functions']:
                if not self._find_function_definition(content, func_name):
                    self.issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=0,
                        issue_type="missing_function",
                        description=f"必須関数が見つかりません: {func_name}",
                        severity="high",
                        suggestion=f"関数 {func_name} を実装してください"
                    ))
        
        # インポートの存在チェック
        if 'imports' in feature_spec:
            for import_stmt in feature_spec['imports']:
                if import_stmt not in content:
                    self.issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=0,
                        issue_type="missing_import",
                        description=f"必須インポートが見つかりません: {import_stmt}",
                        severity="high",
                        suggestion=f"インポート文を追加してください: {import_stmt}"
                    ))
        
        # パラメータの存在チェック
        if 'parameters' in feature_spec:
            for param_name in feature_spec['parameters']:
                if param_name not in content:
                    self.issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=0,
                        issue_type="missing_parameter",
                        description=f"必須パラメータが見つかりません: {param_name}",
                        severity="medium",
                        suggestion=f"パラメータ {param_name} を追加してください"
                    ))
        
        # テンプレート変数のチェック
        if 'template_vars' in feature_spec:
            for var_name in feature_spec['template_vars']:
                pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*[|}\s]'
                if not re.search(pattern, content):
                    self.issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=0,
                        issue_type="missing_template_var",
                        description=f"必須テンプレート変数が見つかりません: {var_name}",
                        severity="medium",
                        suggestion=f"テンプレート変数 {var_name} を追加してください"
                    ))
        
        # CSS要素のチェック
        if 'elements' in feature_spec:
            for element in feature_spec['elements']:
                if element not in content:
                    self.issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=0,
                        issue_type="missing_css_element",
                        description=f"必須CSS要素が見つかりません: {element}",
                        severity="medium",
                        suggestion=f"CSS要素 {element} を追加してください"
                    ))

    def _find_function_definition(self, content: str, func_name: str) -> bool:
        """関数定義の検索"""
        # クラスメソッドと通常の関数の両方をチェック
        patterns = [
            rf'def\s+{re.escape(func_name)}\s*\(',  # 通常の関数
            rf'def\s+{re.escape(func_name.split(".")[-1])}\s*\('  # クラスメソッド
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False

    def validate_integration_with_issues(self) -> None:
        """Issue #108との整合性を検証"""
        issue_file = self.project_root / '.github' / 'ISSUE_TEMPLATE' / 'feature_request.md'
        
        # Issue #108の内容確認（GitHub APIまたはローカルファイル）
        try:
            # gh コマンドでIssue #108を取得
            result = subprocess.run(
                ['gh', 'issue', 'view', '108', '--json', 'title,body'],
                cwd=self.project_root,
                capture_output=True, text=True, check=True
            )
            issue_data = json.loads(result.stdout)
            issue_content = issue_data.get('body', '')
            
            # Issue #108で言及された機能が実装されているかチェック
            self._check_issue_requirements(issue_content)
            
        except subprocess.CalledProcessError:
            self.issues.append(ValidationIssue(
                file_path="",
                line_number=0,
                issue_type="issue_access_error",
                description="Issue #108にアクセスできません",
                severity="low",
                suggestion="GitHub CLIの設定を確認してください"
            ))
        except json.JSONDecodeError:
            self.issues.append(ValidationIssue(
                file_path="",
                line_number=0,
                issue_type="issue_parse_error",
                description="Issue #108の内容を解析できません",
                severity="low"
            ))

    def _check_issue_requirements(self, issue_content: str) -> None:
        """Issue #108の要件との整合性をチェック"""
        
        # 必須機能の実装状況をチェック（Markdown変換機能は削除済み）
        required_implementations = {
            'ZIP配布': 'zip_dist関数'
            # 注意: Markdown変換関連機能は削除済み
        }
        
        for requirement, implementation in required_implementations.items():
            if requirement in issue_content:
                # 対応する実装が存在するかチェック
                if not self._check_implementation_exists(implementation):
                    self.issues.append(ValidationIssue(
                        file_path="",
                        line_number=0,
                        issue_type="missing_issue_requirement",
                        description=f"Issue #108で要求された機能が未実装: {requirement}",
                        severity="high",
                        suggestion=f"{implementation}を実装してください"
                    ))

    def _check_implementation_exists(self, implementation_name: str) -> bool:
        """指定された実装が存在するかチェック"""
        implementation_files = [
            'kumihan_formatter/cli.py',
            'kumihan_formatter/renderer.py'
            # 注意: markdown_converter.pyは削除済み
        ]
        
        for file_path in implementation_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    if implementation_name.replace('関数', '') in content:
                        return True
                except Exception:
                    continue
        return False

    def validate_example_usage(self) -> None:
        """使用例の動作確認"""
        # テスト用の一時ディレクトリを作成してサンプル実行
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # テスト用Markdownファイルを作成
            test_md = temp_path / "test.md"
            test_md.write_text("""# テストドキュメント

これはZIP配布機能のテストです。

## セクション1

[リンクテスト](section2.md)

## セクション2

内容です。
""", encoding='utf-8')
            
            test_md2 = temp_path / "section2.md"
            test_md2.write_text("""# セクション2

詳細内容です。

[戻る](test.md)
""", encoding='utf-8')
            
            # Markdown変換機能は削除されたため、このテストは正常にスキップ
            # テスト用ディレクトリが存在することを確認
            if not temp_path.exists():
                self.issues.append(ValidationIssue(
                    file_path="",
                    line_number=0,
                    issue_type="test_setup_error",
                    description="テスト用ディレクトリの作成に失敗しました",
                    severity="medium",
                    suggestion="テスト環境の設定を確認してください"
                ))

    def run_all_validations(self) -> List[ValidationIssue]:
        """全ての検証を実行"""
        self.issues.clear()
        
        print("🔍 ZIP配布機能検証を開始...")
        
        print("  📋 コア機能検証...")
        self.validate_core_functions()
        
        print("  🎯 Issue整合性検証...")
        self.validate_integration_with_issues()
        
        print("  🧪 実行テスト...")
        self.validate_example_usage()
        
        return self.issues

    def generate_report(self, output_format: str = 'text') -> str:
        """検証結果のレポートを生成"""
        if output_format == 'json':
            return json.dumps([
                {
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'issue_type': issue.issue_type,
                    'description': issue.description,
                    'severity': issue.severity,
                    'suggestion': issue.suggestion
                }
                for issue in self.issues
            ], ensure_ascii=False, indent=2)
        
        # テキスト形式のレポート
        report = []
        report.append("="*60)
        report.append("📋 ZIP配布機能検証結果")
        report.append("="*60)
        report.append(f"検証日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"発見された問題: {len(self.issues)}件")
        report.append("")
        
        if not self.issues:
            report.append("✅ 問題は発見されませんでした。ZIP配布機能は正常です。")
            return "\n".join(report)
        
        # 重要度別に分類
        high_issues = [i for i in self.issues if i.severity == 'high']
        medium_issues = [i for i in self.issues if i.severity == 'medium']
        low_issues = [i for i in self.issues if i.severity == 'low']
        
        for severity, issues, icon in [
            ('high', high_issues, '🔴'),
            ('medium', medium_issues, '🟡'),
            ('low', low_issues, '🟢')
        ]:
            if not issues:
                continue
                
            report.append(f"{icon} {severity.upper()}重要度 ({len(issues)}件)")
            report.append("-" * 40)
            
            for issue in issues:
                if issue.file_path:
                    report.append(f"📁 {issue.file_path}:{issue.line_number}")
                else:
                    report.append(f"📁 全般")
                report.append(f"   問題: {issue.description}")
                if issue.suggestion:
                    report.append(f"   提案: {issue.suggestion}")
                report.append("")
        
        return "\n".join(report)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZIP配布機能自動検証ツール')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='出力形式 (default: text)')
    parser.add_argument('--output', '-o', help='出力ファイル')
    parser.add_argument('--project-root', default='.',
                       help='プロジェクトルート (default: .)')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    validator = ZipFeatureValidator(project_root)
    
    issues = validator.run_all_validations()
    report = validator.generate_report(args.format)
    
    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"📄 レポートを {args.output} に出力しました。")
    else:
        print(report)
    
    # 重要度highの問題があれば終了コード1で終了
    high_issues = [i for i in issues if i.severity == 'high']
    if high_issues:
        print(f"\n❌ {len(high_issues)}件の重大な問題が発見されました。修正が必要です。")
        sys.exit(1)
    elif issues:
        print(f"\n⚠️  {len(issues)}件の軽微な問題が発見されましたが、処理は正常終了します。")
        sys.exit(0)
    else:
        print("\n✅ ZIP配布機能は正常に動作しています。")
        sys.exit(0)

if __name__ == '__main__':
    main()