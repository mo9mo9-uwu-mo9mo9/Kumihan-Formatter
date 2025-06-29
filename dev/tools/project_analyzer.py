#!/usr/bin/env python3
"""統合プロジェクト分析ツール

記法複雑度分析とテストカバレッジ分析を統合したツール。
プロジェクトの品質指標を包括的に測定・報告する。
"""

import re
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SyntaxComplexityResult:
    """記法複雑度分析結果"""
    complex_markers: int
    color_attributes: int
    max_indent_depth: int
    total_lines: int
    complexity_score: float


@dataclass
class CoverageResult:
    """カバレッジ結果を格納するデータクラス"""
    total_coverage: float
    module_coverage: Dict[str, float]
    missing_lines: Dict[str, List[int]]
    uncovered_functions: List[str]
    branch_coverage: Optional[float] = None


@dataclass
class ProjectAnalysisResult:
    """プロジェクト全体の分析結果"""
    syntax_complexity: Dict[str, SyntaxComplexityResult]
    coverage_result: Optional[CoverageResult]
    quality_score: float


class ProjectAnalyzer:
    """統合プロジェクト分析クラス"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初期化"""
        self.project_root = project_root or Path.cwd()
        self.syntax_patterns = {
            'complex_markers': re.compile(r';;;[^;]*\+[^;]*;;;'),
            'color_attrs': re.compile(r'color=#[a-fA-F0-9]{3,6}'),
            'list_items': re.compile(r'^\s*[-・]\s+', re.MULTILINE)
        }
    
    def analyze_syntax_complexity(self, file_path: Path) -> SyntaxComplexityResult:
        """ファイルの記法複雑度を分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            return SyntaxComplexityResult(0, 0, 0, 0, 0.0)
        
        # 複合マーカーの使用頻度
        complex_markers = len(self.syntax_patterns['complex_markers'].findall(content))
        
        # color属性の使用頻度  
        color_attrs = len(self.syntax_patterns['color_attrs'].findall(content))
        
        # ネストしたリストの深度
        lines = content.splitlines()
        max_indent = 0
        for line in lines:
            if line.strip().startswith(('-', '・')):
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        indent_depth = max_indent // 2 if max_indent > 0 else 0
        total_lines = len(lines)
        
        # 複雑度スコア計算（0-100）
        complexity_score = min(100, (
            complex_markers * 5 +
            color_attrs * 2 +
            indent_depth * 10
        ) / max(1, total_lines / 10))
        
        return SyntaxComplexityResult(
            complex_markers=complex_markers,
            color_attributes=color_attrs,
            max_indent_depth=indent_depth,
            total_lines=total_lines,
            complexity_score=complexity_score
        )
    
    def analyze_test_coverage(self) -> Optional[CoverageResult]:
        """テストカバレッジを分析"""
        try:
            # pytest-covを実行してカバレッジを取得
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json:coverage.json",
                "--cov-report=term-missing",
                "-q"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"カバレッジテスト実行エラー: {result.stderr}")
                return None
            
            # JSON結果を読み込み
            coverage_file = self.project_root / "coverage.json"
            if not coverage_file.exists():
                print("カバレッジ結果ファイルが見つかりません")
                return None
            
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            # 結果を解析
            total_coverage = coverage_data['totals']['percent_covered']
            module_coverage = {}
            missing_lines = {}
            uncovered_functions = []
            
            for filename, data in coverage_data['files'].items():
                module_name = Path(filename).stem
                module_coverage[module_name] = data['summary']['percent_covered']
                
                if data['missing_lines']:
                    missing_lines[module_name] = data['missing_lines']
                
                # 未カバーの関数を特定（簡易版）
                if data['summary']['percent_covered'] < 80:
                    uncovered_functions.append(module_name)
            
            # クリーンアップ
            if coverage_file.exists():
                coverage_file.unlink()
            
            return CoverageResult(
                total_coverage=total_coverage,
                module_coverage=module_coverage,
                missing_lines=missing_lines,
                uncovered_functions=uncovered_functions
            )
            
        except subprocess.TimeoutExpired:
            print("カバレッジテストがタイムアウトしました")
            return None
        except Exception as e:
            print(f"カバレッジ分析エラー: {e}")
            return None
    
    def analyze_project(self, include_coverage: bool = True) -> ProjectAnalysisResult:
        """プロジェクト全体を分析"""
        # Kumihan記法ファイルを検索
        kumihan_files = list(self.project_root.glob("**/*.txt"))
        kumihan_files.extend(self.project_root.glob("examples/**/*.md"))
        
        # 記法複雑度分析
        syntax_results = {}
        for file_path in kumihan_files:
            if file_path.stat().st_size > 0:  # 空ファイルをスキップ
                relative_path = str(file_path.relative_to(self.project_root))
                syntax_results[relative_path] = self.analyze_syntax_complexity(file_path)
        
        # カバレッジ分析（オプション）
        coverage_result = None
        if include_coverage:
            coverage_result = self.analyze_test_coverage()
        
        # 全体品質スコア計算
        quality_score = self._calculate_quality_score(syntax_results, coverage_result)
        
        return ProjectAnalysisResult(
            syntax_complexity=syntax_results,
            coverage_result=coverage_result,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(self, 
                                syntax_results: Dict[str, SyntaxComplexityResult],
                                coverage_result: Optional[CoverageResult]) -> float:
        """品質スコアを計算（0-100）"""
        scores = []
        
        # 記法複雑度スコア（低い方が良い）
        if syntax_results:
            avg_complexity = sum(r.complexity_score for r in syntax_results.values()) / len(syntax_results)
            syntax_score = max(0, 100 - avg_complexity)
            scores.append(syntax_score)
        
        # カバレッジスコア
        if coverage_result:
            scores.append(coverage_result.total_coverage)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def generate_report(self, result: ProjectAnalysisResult) -> str:
        """分析結果レポートを生成"""
        report = []
        report.append("# プロジェクト分析レポート\n")
        
        # 全体品質スコア
        report.append(f"## 品質スコア: {result.quality_score:.1f}/100\n")
        
        # 記法複雑度セクション
        if result.syntax_complexity:
            report.append("## 記法複雑度分析")
            report.append("| ファイル | 複合マーカー | 色属性 | 最大ネスト | 複雑度 |")
            report.append("|----------|-------------|--------|------------|--------|")
            
            for file_path, complexity in result.syntax_complexity.items():
                report.append(
                    f"| {file_path} | {complexity.complex_markers} | "
                    f"{complexity.color_attributes} | {complexity.max_indent_depth} | "
                    f"{complexity.complexity_score:.1f} |"
                )
            report.append("")
        
        # カバレッジセクション
        if result.coverage_result:
            cov = result.coverage_result
            report.append(f"## テストカバレッジ: {cov.total_coverage:.1f}%")
            
            if cov.uncovered_functions:
                report.append("### カバレッジ不足モジュール（<80%）:")
                for func in cov.uncovered_functions[:5]:  # 最大5つまで表示
                    coverage = cov.module_coverage.get(func, 0)
                    report.append(f"- {func}: {coverage:.1f}%")
                report.append("")
        
        # 改善提案
        report.append("## 改善提案")
        suggestions = self._generate_suggestions(result)
        for suggestion in suggestions:
            report.append(f"- {suggestion}")
        
        return "\n".join(report)
    
    def _generate_suggestions(self, result: ProjectAnalysisResult) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        # 記法複雑度に基づく提案
        high_complexity_files = [
            (path, complexity) for path, complexity in result.syntax_complexity.items()
            if complexity.complexity_score > 50
        ]
        
        if high_complexity_files:
            suggestions.append(f"記法が複雑なファイル{len(high_complexity_files)}個の簡素化を検討")
        
        # カバレッジに基づく提案
        if result.coverage_result:
            if result.coverage_result.total_coverage < 80:
                suggestions.append("テストカバレッジの向上（目標: 80%以上）")
            if len(result.coverage_result.uncovered_functions) > 5:
                suggestions.append("未テストモジュールのテスト追加を優先")
        
        # 品質スコアに基づく提案
        if result.quality_score < 70:
            suggestions.append("コード品質の全体的な改善が必要")
        elif result.quality_score > 90:
            suggestions.append("良好な品質を維持中 - 現在の開発プラクティスを継続")
        
        return suggestions or ["プロジェクト品質は良好です"]


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="統合プロジェクト分析ツール")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="カバレッジ分析をスキップ")
    parser.add_argument("--output", "-o", type=Path,
                       help="レポート出力ファイル")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="プロジェクトルートディレクトリ")
    
    args = parser.parse_args()
    
    analyzer = ProjectAnalyzer(args.project_root)
    
    print("プロジェクト分析を開始...")
    result = analyzer.analyze_project(include_coverage=not args.no_coverage)
    
    print("レポートを生成中...")
    report = analyzer.generate_report(result)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"レポートを保存: {args.output}")
    else:
        print(report)
    
    print(f"\n品質スコア: {result.quality_score:.1f}/100")


if __name__ == "__main__":
    main()