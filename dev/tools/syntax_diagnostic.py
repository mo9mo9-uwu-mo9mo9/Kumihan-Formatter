#!/usr/bin/env python3
"""
Kumihan記法の構文エラー診断・分析ツール

エラーパターンを分析して自動修正の提案を行います。
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class SyntaxDiagnostic:
    """構文エラーの診断・分析クラス"""
    
    def __init__(self):
        self.error_patterns = defaultdict(list)
        self.fix_suggestions = []
    
    def analyze_file(self, file_path: Path) -> Dict:
        """ファイルの構文エラーを分析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        analysis = {
            'file': file_path,
            'total_lines': len(lines),
            'errors': [],
            'patterns': defaultdict(int),
            'suggestions': []
        }
        
        # エラーパターンの検出
        self._detect_missing_closers(lines, analysis)
        self._detect_duplicate_markers(lines, analysis)
        self._detect_color_order_errors(lines, analysis)
        self._detect_standalone_markers(lines, analysis)
        
        return analysis
    
    def _detect_missing_closers(self, lines: List[str], analysis: Dict):
        """閉じマーカー不足の検出"""
        in_block = False
        block_start_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if re.match(r'^;;;(見出し[1-5]|太字|枠線|ハイライト)', stripped):
                if in_block:
                    # 前のブロックが閉じられていない
                    error = {
                        'line': i + 1,
                        'type': 'missing_closer',
                        'message': f'Line {block_start_line}のブロックが閉じられていません',
                        'suggestion': f'Line {i}の前に ;;; を追加'
                    }
                    analysis['errors'].append(error)
                    analysis['patterns']['missing_closer'] += 1
                
                in_block = True
                block_start_line = i + 1
            
            elif stripped == ';;;':
                in_block = False
    
    def _detect_duplicate_markers(self, lines: List[str], analysis: Dict):
        """重複マーカーの検出"""
        for i in range(len(lines) - 1):
            if lines[i].strip() == ';;;' and lines[i + 1].strip() == ';;;':
                error = {
                    'line': i + 2,
                    'type': 'duplicate_marker',
                    'message': '不要な重複マーカー',
                    'suggestion': 'どちらか一方の ;;; を削除'
                }
                analysis['errors'].append(error)
                analysis['patterns']['duplicate_marker'] += 1
    
    def _detect_color_order_errors(self, lines: List[str], analysis: Dict):
        """Color属性順序エラーの検出"""
        pattern = r';;;ハイライト\+太字(\s+color=#[a-fA-F0-9]{6})'
        
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                error = {
                    'line': i + 1,
                    'type': 'color_order',
                    'message': 'color属性は太字キーワードではサポートされていません',
                    'suggestion': ';;;太字+ハイライト color=#xxx の順序に変更'
                }
                analysis['errors'].append(error)
                analysis['patterns']['color_order'] += 1
    
    def _detect_standalone_markers(self, lines: List[str], analysis: Dict):
        """問題のある独立マーカーの検出"""
        for i, line in enumerate(lines):
            if line.strip() == ';;;':
                # 前後の文脈をチェック
                prev_line = lines[i-1].strip() if i > 0 else ''
                next_line = lines[i+1].strip() if i < len(lines) - 1 else ''
                
                # 問題のあるパターンを検出
                if prev_line == ';;;':
                    error = {
                        'line': i + 1,
                        'type': 'unnecessary_marker',
                        'message': '不要な独立マーカー',
                        'suggestion': 'この ;;; を削除'
                    }
                    analysis['errors'].append(error)
                    analysis['patterns']['unnecessary_marker'] += 1
    
    def generate_report(self, analyses: List[Dict]) -> str:
        """分析結果のレポートを生成"""
        total_files = len(analyses)
        total_errors = sum(len(a['errors']) for a in analyses)
        
        # パターン別集計
        pattern_summary = defaultdict(int)
        for analysis in analyses:
            for pattern, count in analysis['patterns'].items():
                pattern_summary[pattern] += count
        
        report = f"""
📊 Kumihan記法 構文エラー診断レポート
=====================================

📁 分析対象: {total_files} ファイル
🚨 総エラー数: {total_errors} 個

📈 エラーパターン別統計:
"""
        
        for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            report += f"  • {pattern}: {count} 個 ({percentage:.1f}%)\n"
        
        report += "\n🔧 自動修正可能性:\n"
        
        auto_fixable = ['missing_closer', 'duplicate_marker', 'color_order', 'unnecessary_marker']
        auto_fixable_count = sum(pattern_summary[p] for p in auto_fixable)
        auto_fix_rate = (auto_fixable_count / total_errors * 100) if total_errors > 0 else 0
        
        report += f"  • 自動修正可能: {auto_fixable_count}/{total_errors} ({auto_fix_rate:.1f}%)\n"
        report += f"  • 推奨ツール: auto_fix_syntax.py\n"
        
        report += "\n📋 ファイル別詳細:\n"
        for analysis in analyses:
            if analysis['errors']:
                report += f"\n📄 {analysis['file'].name}: {len(analysis['errors'])} エラー\n"
                for error in analysis['errors'][:5]:  # 最初の5つのエラーのみ表示
                    report += f"  Line {error['line']}: {error['message']}\n"
                    report += f"    💡 {error['suggestion']}\n"
                
                if len(analysis['errors']) > 5:
                    report += f"  ... and {len(analysis['errors']) - 5} more errors\n"
        
        return report


def main():
    """メイン実行関数"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python syntax_diagnostic.py <file_or_directory>")
        sys.exit(1)
    
    diagnostic = SyntaxDiagnostic()
    analyses = []
    
    path = Path(sys.argv[1])
    
    if path.is_file() and path.suffix == '.txt':
        analyses.append(diagnostic.analyze_file(path))
    elif path.is_dir():
        for txt_file in path.rglob('*.txt'):
            analyses.append(diagnostic.analyze_file(txt_file))
    
    if analyses:
        report = diagnostic.generate_report(analyses)
        print(report)
        
        # レポートをファイルに保存
        report_file = Path('syntax_diagnostic_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📝 詳細レポートを {report_file} に保存しました")
    else:
        print("❌ 分析対象のファイルが見つかりませんでした")


if __name__ == "__main__":
    main()