#!/usr/bin/env python3
"""テストカバレッジ分析ツール

現在のテストカバレッジを測定し、不足箇所を特定するツール。
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CoverageResult:
    """カバレッジ結果を格納するデータクラス"""
    total_coverage: float
    module_coverage: Dict[str, float]
    missing_lines: Dict[str, List[int]]
    uncovered_functions: List[str]
    branch_coverage: Optional[float] = None


class CoverageAnalyzer:
    """テストカバレッジ分析クラス"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初期化
        
        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.target_coverage = 80
        self.critical_modules = {
            "parser.py": 95,
            "renderer.py": 95,
            "cli.py": 85,
            "config.py": 90,
        }
    
    def run_coverage(self) -> CoverageResult:
        """
        カバレッジ測定を実行
        
        Returns:
            CoverageResult: 測定結果
        """
        try:
            # カバレッジ付きでテスト実行
            cmd = [
                sys.executable, "-m", "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json",
                "--cov-report=term-missing",
                "dev/tests/"
            ]
            
            print("🧪 カバレッジ測定を実行中...")
            result = subprocess.run(
                cmd, 
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ テスト実行エラー:\n{result.stderr}")
                sys.exit(1)
            
            # JSONレポートを読み込み
            coverage_json = self.project_root / "coverage.json"
            if not coverage_json.exists():
                print("❌ coverage.jsonが見つかりません")
                sys.exit(1)
            
            with open(coverage_json, 'r') as f:
                coverage_data = json.load(f)
            
            return self._parse_coverage_data(coverage_data)
            
        except Exception as e:
            print(f"❌ カバレッジ測定エラー: {e}")
            sys.exit(1)
    
    def _parse_coverage_data(self, data: Dict) -> CoverageResult:
        """
        カバレッジデータを解析
        
        Args:
            data: coverage.jsonの内容
            
        Returns:
            CoverageResult: 解析結果
        """
        total_coverage = data["totals"]["percent_covered"]
        
        module_coverage = {}
        missing_lines = {}
        uncovered_functions = []
        
        for file_path, file_data in data["files"].items():
            if "kumihan_formatter" in file_path:
                # モジュール名を抽出
                module_name = Path(file_path).name
                module_coverage[module_name] = file_data["summary"]["percent_covered"]
                
                # 未カバー行を収集
                if file_data["missing_lines"]:
                    missing_lines[module_name] = file_data["missing_lines"]
        
        return CoverageResult(
            total_coverage=total_coverage,
            module_coverage=module_coverage,
            missing_lines=missing_lines,
            uncovered_functions=uncovered_functions
        )
    
    def analyze_gaps(self, result: CoverageResult) -> Dict[str, List[str]]:
        """
        カバレッジギャップを分析
        
        Args:
            result: カバレッジ結果
            
        Returns:
            Dict[str, List[str]]: 改善提案
        """
        recommendations = {
            "critical": [],
            "important": [],
            "nice_to_have": []
        }
        
        # 重要モジュールのチェック
        for module, target in self.critical_modules.items():
            current = result.module_coverage.get(module, 0)
            if current < target:
                recommendations["critical"].append(
                    f"{module}: {current:.1f}% < {target}% (不足: {target - current:.1f}%)"
                )
        
        # 全体カバレッジのチェック
        if result.total_coverage < self.target_coverage:
            recommendations["important"].append(
                f"全体カバレッジ: {result.total_coverage:.1f}% < {self.target_coverage}% "
                f"(不足: {self.target_coverage - result.total_coverage:.1f}%)"
            )
        
        # 未カバー行の多いモジュール
        for module, lines in result.missing_lines.items():
            if len(lines) > 10:
                recommendations["nice_to_have"].append(
                    f"{module}: {len(lines)}行が未カバー"
                )
        
        return recommendations
    
    def generate_report(self, result: CoverageResult) -> str:
        """
        カバレッジレポートを生成
        
        Args:
            result: カバレッジ結果
            
        Returns:
            str: レポート文字列
        """
        report = []
        report.append("📊 テストカバレッジレポート")
        report.append("=" * 50)
        report.append(f"全体カバレッジ: {result.total_coverage:.2f}%")
        report.append("")
        
        # モジュール別カバレッジ
        report.append("📁 モジュール別カバレッジ:")
        for module, coverage in sorted(result.module_coverage.items()):
            status = "✅" if coverage >= self.critical_modules.get(module, 80) else "❌"
            target = self.critical_modules.get(module, "N/A")
            report.append(f"  {status} {module:<20} {coverage:>6.1f}% (目標: {target}%)")
        
        report.append("")
        
        # 改善提案
        recommendations = self.analyze_gaps(result)
        if any(recommendations.values()):
            report.append("🎯 改善提案:")
            
            if recommendations["critical"]:
                report.append("  🔴 緊急 (重要モジュール):")
                for rec in recommendations["critical"]:
                    report.append(f"    - {rec}")
            
            if recommendations["important"]:
                report.append("  🟡 重要 (全体カバレッジ):")
                for rec in recommendations["important"]:
                    report.append(f"    - {rec}")
            
            if recommendations["nice_to_have"]:
                report.append("  🔵 推奨 (個別改善):")
                for rec in recommendations["nice_to_have"]:
                    report.append(f"    - {rec}")
        else:
            report.append("🎉 すべての目標を達成しています！")
        
        return "\n".join(report)
    
    def find_uncovered_functions(self, result: CoverageResult) -> List[Tuple[str, str]]:
        """
        未カバーの関数を特定
        
        Args:
            result: カバレッジ結果
            
        Returns:
            List[Tuple[str, str]]: (ファイル名, 関数名) のリスト
        """
        uncovered = []
        
        # 各ファイルの未カバー行から関数を推定
        for module, lines in result.missing_lines.items():
            file_path = self.project_root / "kumihan_formatter" / module
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_lines = f.readlines()
                    
                    for line_num in lines:
                        if line_num <= len(file_lines):
                            line = file_lines[line_num - 1].strip()
                            if line.startswith("def ") and ":" in line:
                                func_name = line.split("def ")[1].split("(")[0]
                                uncovered.append((module, func_name))
                except Exception:
                    continue
        
        return uncovered


def main():
    """メイン関数"""
    analyzer = CoverageAnalyzer()
    
    print("🎯 Kumihan-Formatter テストカバレッジ分析")
    print("=" * 50)
    
    # カバレッジ測定
    result = analyzer.run_coverage()
    
    # レポート生成
    report = analyzer.generate_report(result)
    print(report)
    
    # 未カバー関数の特定
    uncovered_functions = analyzer.find_uncovered_functions(result)
    if uncovered_functions:
        print("\n🔍 未カバー関数（推定）:")
        for module, func in uncovered_functions[:10]:  # 最初の10個のみ表示
            print(f"  - {module}:{func}")
        if len(uncovered_functions) > 10:
            print(f"  ... 他 {len(uncovered_functions) - 10}個")
    
    # HTMLレポートの案内
    htmlcov_path = Path("htmlcov/index.html")
    if htmlcov_path.exists():
        print(f"\n📋 詳細レポート: {htmlcov_path.resolve()}")
    
    print("\n🔧 改善コマンド例:")
    print("  pytest --cov=kumihan_formatter --cov-report=html")
    print("  open htmlcov/index.html")


if __name__ == "__main__":
    main()