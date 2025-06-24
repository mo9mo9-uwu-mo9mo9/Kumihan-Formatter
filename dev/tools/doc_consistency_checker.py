#!/usr/bin/env python3
"""
ドキュメント整合性チェックツール

ファイル更新時にドキュメント間の整合性をチェックし、
古くなった可能性のある箇所を検出します。
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ConsistencyIssue:
    """整合性問題を表すデータクラス"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    suggestion: str = ""

class DocumentConsistencyChecker:
    """ドキュメント整合性チェッカー"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[ConsistencyIssue] = []
        
        # バージョン情報の抽出
        self.current_version = self._extract_version()
        
        # チェックルール定義
        self.version_files = [
            'pyproject.toml',
            'kumihan_formatter/__init__.py',
            'README.md',
            'CHANGELOG.md'
        ]
        
        # ドキュメント間の参照関係
        self.doc_references = {
            'README.md': ['docs/user/', 'examples/', 'CHANGELOG.md'],
            'CLAUDE.md': ['SPEC.md', 'CONTRIBUTING.md'],
            'CONTRIBUTING.md': ['SPEC.md', 'STYLE_GUIDE.md'],
            'docs/': ['examples/', 'SPEC.md']
        }
        
        # 機能参照のキーワード（更新が必要な可能性が高い）
        self.feature_keywords = [
            '目次機能', '目次マーカー', ';;;目次;;;',
            'ソーストグル', '--with-source-toggle',
            'D&D', 'ドラッグ&ドロップ',
            'バッチファイル', '.bat', '.command',
            'HTML出力', 'PDF出力', 'EPUB出力',
            'ZIP配布版', 'zip-dist', 'Markdown変換', 'ナビゲーション',
            'convert_markdown_to_html', 'markdown_converter',
            'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8',
            'v0.1.0', 'v0.2.0', 'v0.3.0', 'v0.4.0', 'v1.0.0'
        ]

    def _extract_version(self) -> str:
        """pyproject.tomlからバージョンを抽出"""
        try:
            pyproject_path = self.project_root / 'pyproject.toml'
            content = pyproject_path.read_text(encoding='utf-8')
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            return match.group(1) if match else "unknown"
        except Exception:
            return "unknown"

    def check_version_consistency(self) -> None:
        """バージョン情報の整合性をチェック"""
        version_occurrences = {}
        
        for file_path in self.version_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
                
            try:
                content = full_path.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                for i, line in enumerate(lines, 1):
                    # バージョン番号らしきパターンを検索
                    version_patterns = [
                        r'version\s*=\s*"([^"]+)"',  # pyproject.toml
                        r'__version__\s*=\s*"([^"]+)"',  # __init__.py
                        r'version-([0-9]+\.[0-9]+\.[0-9]+)',  # README badge
                        r'\[([0-9]+\.[0-9]+\.[0-9]+)\]'  # CHANGELOG
                    ]
                    
                    for pattern in version_patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            version = match.group(1)
                            # bumpversionの設定変数を除外
                            if version in ['{current_version}', '{new_version}']:
                                continue
                            if file_path not in version_occurrences:
                                version_occurrences[file_path] = []
                            version_occurrences[file_path].append((i, version))
            except Exception as e:
                self.issues.append(ConsistencyIssue(
                    file_path=file_path,
                    line_number=0,
                    issue_type="file_read_error",
                    description=f"ファイル読み込みエラー: {e}",
                    severity="medium"
                ))
        
        # バージョンの不整合をチェック
        all_versions = set()
        for file_path, versions in version_occurrences.items():
            for line_num, version in versions:
                all_versions.add(version)
                # CHANGELOG.mdは履歴なので古いバージョンがあっても問題なし
                if file_path == 'CHANGELOG.md':
                    continue
                
                # 現在のバージョンファイルでバージョンが違う場合のみエラー
                if version != self.current_version:
                    self.issues.append(ConsistencyIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="version_mismatch",
                        description=f"バージョン不整合: {version} (期待値: {self.current_version})",
                        severity="high",
                        suggestion=f"バージョンを {self.current_version} に更新"
                    ))

    def check_feature_references(self) -> None:
        """機能参照の整合性をチェック"""
        # 実装済み機能の確認
        implemented_features = self._get_implemented_features()
        
        # ドキュメント内の機能参照をチェック
        doc_files = list(self.project_root.glob('*.md')) + \
                   list(self.project_root.glob('docs/**/*.md'))
        
        for doc_file in doc_files:
            if not doc_file.exists():
                continue
                
            try:
                content = doc_file.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                for i, line in enumerate(lines, 1):
                    for keyword in self.feature_keywords:
                        if keyword in line:
                            # 機能の実装状況と記述の整合性をチェック
                            self._check_feature_consistency(
                                str(doc_file.relative_to(self.project_root)),
                                i, line, keyword, implemented_features
                            )
            except Exception as e:
                self.issues.append(ConsistencyIssue(
                    file_path=str(doc_file.relative_to(self.project_root)),
                    line_number=0,
                    issue_type="file_read_error",
                    description=f"ファイル読み込みエラー: {e}",
                    severity="medium"
                ))

    def _get_implemented_features(self) -> Dict[str, bool]:
        """実装済み機能の一覧を取得"""
        features = {}
        
        # CLI オプションのチェック
        cli_file = self.project_root / 'kumihan_formatter' / 'cli.py'
        if cli_file.exists():
            content = cli_file.read_text(encoding='utf-8')
            features['with_source_toggle'] = '--with-source-toggle' in content
            features['output_option'] = '--output' in content
        
        # テンプレートのチェック
        template_dir = self.project_root / 'kumihan_formatter' / 'templates'
        if template_dir.exists():
            templates = list(template_dir.glob('*.j2'))
            features['base_template'] = any('base.html.j2' in str(t) for t in templates)
            features['source_toggle_template'] = any('source-toggle' in str(t) for t in templates)
        
        # バッチファイルのチェック
        features['windows_batch'] = (self.project_root / 'WINDOWS').exists()
        features['macos_command'] = (self.project_root / 'MAC').exists()
        
        # 目次機能のチェック（パーサーでの実装確認）
        parser_file = self.project_root / 'kumihan_formatter' / 'parser.py'
        if parser_file.exists():
            content = parser_file.read_text(encoding='utf-8')
            features['toc_feature'] = '目次' in content or 'toc' in content.lower()
        
        return features

    def _check_feature_consistency(self, file_path: str, line_num: int, 
                                 line: str, keyword: str, 
                                 implemented_features: Dict[str, bool]) -> None:
        """特定の機能参照の整合性をチェック"""
        
        # ソーストグル機能の状況チェック
        if 'ソーストグル' in keyword or '--with-source-toggle' in keyword:
            if implemented_features.get('with_source_toggle', False):
                # 実装済みなのに「未実装」「計画中」などの記述があるかチェック
                if any(word in line for word in ['未実装', '計画中', 'TODO', 'バックログ']):
                    self.issues.append(ConsistencyIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="outdated_status",
                        description=f"実装済み機能が未実装として記載: {keyword}",
                        severity="medium",
                        suggestion="実装済みステータスに更新"
                    ))
        
        # マイルストーンの状況チェック
        milestone_pattern = r'M([1-8])'
        if re.search(milestone_pattern, keyword):
            milestone_num = re.search(milestone_pattern, keyword).group(1)
            current_milestone = self._get_current_milestone()
            
            if int(milestone_num) <= current_milestone:
                if any(word in line for word in ['計画中', '予定', 'バックログ']):
                    self.issues.append(ConsistencyIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="outdated_milestone_status",
                        description=f"完了済みマイルストーンが未完了として記載: M{milestone_num}",
                        severity="high",
                        suggestion=f"M{milestone_num}を完了済みステータスに更新"
                    ))

    def _get_current_milestone(self) -> int:
        """現在のマイルストーン番号を推定"""
        # バージョンからマイルストーンを推定
        version_parts = self.current_version.split('.')
        if len(version_parts) >= 2:
            minor_version = int(version_parts[1])
            # v0.3.0 = M5完了 の想定
            return min(5 + minor_version - 3, 8)
        return 1

    def check_broken_links(self) -> None:
        """壊れたリンクやファイル参照をチェック"""
        doc_files = list(self.project_root.glob('*.md')) + \
                   list(self.project_root.glob('docs/**/*.md'))
        
        for doc_file in doc_files:
            if not doc_file.exists():
                continue
                
            try:
                content = doc_file.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                for i, line in enumerate(lines, 1):
                    # Markdownリンクの検出
                    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                    matches = re.finditer(link_pattern, line)
                    
                    for match in matches:
                        link_text = match.group(1)
                        link_path = match.group(2)
                        
                        # 外部リンクはスキップ
                        if link_path.startswith(('http://', 'https://', 'mailto:')):
                            continue
                        
                        # 相対パスのファイル存在チェック
                        if not link_path.startswith('#'):  # アンカーリンクではない
                            target_path = (doc_file.parent / link_path).resolve()
                            if not target_path.exists():
                                self.issues.append(ConsistencyIssue(
                                    file_path=str(doc_file.relative_to(self.project_root)),
                                    line_number=i,
                                    issue_type="broken_link",
                                    description=f"壊れたリンク: {link_path}",
                                    severity="medium",
                                    suggestion=f"リンク先ファイルの確認: {target_path}"
                                ))
            except Exception as e:
                self.issues.append(ConsistencyIssue(
                    file_path=str(doc_file.relative_to(self.project_root)),
                    line_number=0,
                    issue_type="file_read_error",
                    description=f"ファイル読み込みエラー: {e}",
                    severity="medium"
                ))

    def run_all_checks(self) -> List[ConsistencyIssue]:
        """全てのチェックを実行"""
        self.issues.clear()
        
        print("🔍 ドキュメント整合性チェックを開始...")
        
        print("  📋 バージョン整合性チェック...")
        self.check_version_consistency()
        
        print("  🎯 機能参照整合性チェック...")
        self.check_feature_references()
        
        print("  🔗 リンク整合性チェック...")
        self.check_broken_links()
        
        return self.issues

    def generate_report(self, output_format: str = 'text') -> str:
        """チェック結果のレポートを生成"""
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
        report.append("📋 ドキュメント整合性チェック結果")
        report.append("="*60)
        report.append(f"チェック日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"プロジェクトバージョン: {self.current_version}")
        report.append(f"発見された問題: {len(self.issues)}件")
        report.append("")
        
        if not self.issues:
            report.append("✅ 問題は発見されませんでした。")
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
                report.append(f"📁 {issue.file_path}:{issue.line_number}")
                report.append(f"   問題: {issue.description}")
                if issue.suggestion:
                    report.append(f"   提案: {issue.suggestion}")
                report.append("")
        
        return "\n".join(report)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ドキュメント整合性チェックツール')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='出力形式 (default: text)')
    parser.add_argument('--output', '-o', help='出力ファイル')
    parser.add_argument('--project-root', default='.',
                       help='プロジェクトルート (default: .)')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    checker = DocumentConsistencyChecker(project_root)
    
    issues = checker.run_all_checks()
    report = checker.generate_report(args.format)
    
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
        print("\n✅ 問題は発見されませんでした。")
        sys.exit(0)

if __name__ == '__main__':
    main()