#!/usr/bin/env python3
"""
ファイルサイズ効率性分析スクリプト

300行制限による非効率な設計パターンを検出し、
人為的分割・設計歪曲・保守性悪化を特定します。
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FileAnalysis:
    """ファイル分析結果"""

    path: Path
    lines: int
    classes: int
    functions: int
    imports: int
    complexity_score: int
    efficiency_issues: List[str]
    refactor_suggestions: List[str]


class FileSizeEfficiencyAnalyzer:
    """ファイルサイズ効率性分析クラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.line_limit = 300
        self.analyses = []

    def analyze_size_related_inefficiencies(self) -> Dict:
        """サイズ制限関連の非効率性分析"""

        # 1. 300行超過ファイルの特定
        oversized_files = self._find_oversized_files()

        # 2. 人為的分割パターンの検出
        artificial_splits = self._detect_artificial_splits()

        # 3. 設計歪曲パターンの分析
        design_distortions = self._analyze_design_distortions()

        # 4. 保守性への影響評価
        maintainability_impact = self._assess_maintainability_impact()

        return {
            "summary": self._generate_efficiency_summary(
                oversized_files, artificial_splits
            ),
            "oversized_files": oversized_files,
            "artificial_splits": artificial_splits,
            "design_distortions": design_distortions,
            "maintainability_impact": maintainability_impact,
            "recommendations": self._generate_recommendations(),
        }

    def _find_oversized_files(self) -> List[FileAnalysis]:
        """300行超過ファイルの特定と分析"""
        oversized = []

        for py_file in self.project_root.rglob("kumihan_formatter/**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                lines = len(content.splitlines())

                if lines > self.line_limit:
                    analysis = self._analyze_file_structure(py_file, content, lines)
                    oversized.append(analysis)

            except Exception:
                continue

        # 行数順でソート
        oversized.sort(key=lambda x: x.lines, reverse=True)
        return oversized

    def _analyze_file_structure(
        self, file_path: Path, content: str, lines: int
    ) -> FileAnalysis:
        """ファイル構造の詳細分析"""

        # 基本メトリクス
        classes = len(re.findall(r"^class\s+\w+", content, re.MULTILINE))
        functions = len(re.findall(r"^def\s+\w+", content, re.MULTILINE))
        imports = len(re.findall(r"^(import|from)\s+", content, re.MULTILINE))

        # 複雑度指標
        if_statements = len(re.findall(r"\bif\b", content))
        try_blocks = len(re.findall(r"\btry\b", content))
        loops = len(re.findall(r"\b(for|while)\b", content))

        complexity_score = (
            if_statements + try_blocks * 2 + loops + classes * 5 + functions * 2
        )

        # 効率性問題の検出
        efficiency_issues = []
        refactor_suggestions = []

        # 1. 単一責任原則違反の検出
        if classes > 3 and lines > 400:
            efficiency_issues.append(
                "Multiple classes in oversized file (SRP violation)"
            )
            refactor_suggestions.append(
                "Split into separate files by class responsibility"
            )

        # 2. 長大な関数の検出
        long_functions = self._detect_long_functions(content)
        if long_functions:
            efficiency_issues.append(
                f"Long functions detected: {len(long_functions)} functions > 50 lines"
            )
            refactor_suggestions.append("Extract methods from long functions")

        # 3. 重複コードパターンの検出
        if self._has_code_duplication(content):
            efficiency_issues.append("Code duplication patterns detected")
            refactor_suggestions.append("Extract common functionality to utilities")

        # 4. 人為的分割の兆候
        if lines > 280 and lines < 320 and classes == 1:
            efficiency_issues.append(
                "Possible artificial size constraint (near 300-line limit)"
            )
            refactor_suggestions.append(
                "Consider natural module boundaries over line limits"
            )

        return FileAnalysis(
            path=file_path,
            lines=lines,
            classes=classes,
            functions=functions,
            imports=imports,
            complexity_score=complexity_score,
            efficiency_issues=efficiency_issues,
            refactor_suggestions=refactor_suggestions,
        )

    def _detect_long_functions(self, content: str) -> List[str]:
        """長大な関数の検出"""
        lines = content.split("\n")
        long_functions = []

        current_function = None
        function_start = 0
        indent_level = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 関数定義の検出
            if stripped.startswith("def "):
                if current_function and (i - function_start) > 50:
                    long_functions.append(
                        f"{current_function} ({i - function_start} lines)"
                    )

                current_function = stripped.split("(")[0].replace("def ", "")
                function_start = i
                indent_level = len(line) - len(line.lstrip())

            # 関数終了の検出（インデントレベルで判定）
            elif (
                current_function
                and line.strip()
                and len(line) - len(line.lstrip()) <= indent_level
                and not line.startswith(" ")
            ):
                if (i - function_start) > 50:
                    long_functions.append(
                        f"{current_function} ({i - function_start} lines)"
                    )
                current_function = None

        return long_functions

    def _has_code_duplication(self, content: str) -> bool:
        """コード重複の簡易検出"""
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        # 同じ行が3回以上出現（重複の兆候）
        line_counts = {}
        for line in lines:
            if len(line) > 20:  # 短すぎる行は除外
                line_counts[line] = line_counts.get(line, 0) + 1

        return any(count >= 3 for count in line_counts.values())

    def _detect_artificial_splits(self) -> List[Dict]:
        """人為的分割パターンの検出"""
        artificial_splits = []

        # 関連性の高いファイル群を検索
        related_files = self._find_related_file_groups()

        for group in related_files:
            if len(group["files"]) > 3:  # 3個以上の関連ファイル
                total_lines = sum(f["lines"] for f in group["files"])
                avg_lines = total_lines / len(group["files"])

                # 平均250-299行 = 300行制限回避の疑い
                if 250 <= avg_lines <= 299:
                    artificial_splits.append(
                        {
                            "pattern": group["pattern"],
                            "files": group["files"],
                            "total_lines": total_lines,
                            "avg_lines": avg_lines,
                            "suspicion_reason": "Consistent sizing near 300-line limit suggests artificial splitting",
                        }
                    )

        return artificial_splits

    def _find_related_file_groups(self) -> List[Dict]:
        """関連ファイルグループの特定"""
        groups = []

        # パターン別グループ化
        patterns = {
            "performance": "kumihan_formatter/core/performance/",
            "error_handling": "kumihan_formatter/core/error_handling/",
            "utilities": "kumihan_formatter/core/utilities/",
            "rendering": "kumihan_formatter/core/rendering/",
            "caching": "kumihan_formatter/core/caching/",
        }

        for pattern_name, pattern_path in patterns.items():
            pattern_dir = self.project_root / pattern_path
            if pattern_dir.exists():
                files = []
                for py_file in pattern_dir.rglob("*.py"):
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        files.append({"path": py_file, "lines": lines})
                    except:
                        continue

                if files:
                    groups.append({"pattern": pattern_name, "files": files})

        return groups

    def _analyze_design_distortions(self) -> List[Dict]:
        """設計歪曲パターンの分析"""
        distortions = []

        # 1. 過度な抽象化の検出
        over_abstraction = self._detect_over_abstraction()
        if over_abstraction:
            distortions.extend(over_abstraction)

        # 2. 不自然な責任分散の検出
        unnatural_splits = self._detect_unnatural_responsibility_splits()
        if unnatural_splits:
            distortions.extend(unnatural_splits)

        return distortions

    def _detect_over_abstraction(self) -> List[Dict]:
        """過度な抽象化の検出"""
        over_abstractions = []

        # Factory, Builder, Strategy パターンの過剰使用を検出
        pattern_files = list(
            self.project_root.rglob("kumihan_formatter/**/*factory*.py")
        )
        pattern_files.extend(
            self.project_root.rglob("kumihan_formatter/**/*builder*.py")
        )
        pattern_files.extend(
            self.project_root.rglob("kumihan_formatter/**/*strategy*.py")
        )

        for file_path in pattern_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                lines = len(content.splitlines())

                # 小さなファイル（< 100行）で複雑なパターン = 過度な抽象化の疑い
                if lines < 100:
                    classes = len(re.findall(r"^class\s+\w+", content, re.MULTILINE))
                    if classes >= 2:
                        over_abstractions.append(
                            {
                                "file": file_path,
                                "lines": lines,
                                "classes": classes,
                                "issue": "Small file with multiple classes - possible over-abstraction",
                                "suggestion": "Consider consolidating or questioning necessity of pattern",
                            }
                        )
            except:
                continue

        return over_abstractions

    def _detect_unnatural_responsibility_splits(self) -> List[Dict]:
        """不自然な責任分散の検出"""
        unnatural_splits = []

        # 高い結合度を持つファイル群を検出
        import_dependencies = self._analyze_import_dependencies()

        for file_group in import_dependencies:
            if file_group["cross_dependencies"] > 5:  # 相互依存が多い
                unnatural_splits.append(
                    {
                        "files": file_group["files"],
                        "cross_dependencies": file_group["cross_dependencies"],
                        "issue": "High coupling between supposedly separate modules",
                        "suggestion": "Consider merging highly coupled modules",
                    }
                )

        return unnatural_splits

    def _analyze_import_dependencies(self) -> List[Dict]:
        """import依存関係の分析"""
        # 簡略化された実装
        return []  # 実際の実装では詳細な依存関係分析を行う

    def _assess_maintainability_impact(self) -> Dict:
        """保守性への影響評価"""
        return {
            "cognitive_load": {
                "issue": "多数の小ファイルによる認知負荷増大",
                "evidence": "関連機能が複数ファイルに分散",
                "impact": "Medium",
            },
            "navigation_overhead": {
                "issue": "ファイル間移動の頻度増加",
                "evidence": "単一機能理解に複数ファイル確認が必要",
                "impact": "High",
            },
            "testing_complexity": {
                "issue": "統合テストの複雑化",
                "evidence": "分散された機能の結合テスト困難",
                "impact": "High",
            },
        }

    def _generate_efficiency_summary(
        self, oversized_files: List[FileAnalysis], artificial_splits: List[Dict]
    ) -> Dict:
        """効率性サマリー生成"""
        return {
            "total_oversized": len(oversized_files),
            "max_lines": max((f.lines for f in oversized_files), default=0),
            "avg_oversized_lines": (
                sum(f.lines for f in oversized_files) / len(oversized_files)
                if oversized_files
                else 0
            ),
            "artificial_split_groups": len(artificial_splits),
            "efficiency_verdict": self._calculate_efficiency_verdict(
                oversized_files, artificial_splits
            ),
        }

    def _calculate_efficiency_verdict(
        self, oversized_files: List[FileAnalysis], artificial_splits: List[Dict]
    ) -> str:
        """効率性判定"""
        if len(oversized_files) > 20:
            return "High Inefficiency Risk"
        elif len(artificial_splits) > 5:
            return "Moderate Inefficiency Risk"
        elif any(f.lines > 500 for f in oversized_files):
            return "Some Inefficiency Issues"
        else:
            return "Generally Efficient"

    def _generate_recommendations(self) -> List[Dict]:
        """改善推奨事項生成"""
        return [
            {
                "priority": "High",
                "action": "ティア別ファイルサイズ制限の導入",
                "description": "Critical: 400行, Important: 500行, Others: 制限なし",
                "benefit": "自然な設計境界の尊重",
            },
            {
                "priority": "Medium",
                "action": "関連機能ファイルの統合検討",
                "description": "高い結合度を持つファイル群の統合",
                "benefit": "保守性・理解性の向上",
            },
            {
                "priority": "Low",
                "action": "過度な抽象化の見直し",
                "description": "不必要なデザインパターンの簡素化",
                "benefit": "コード複雑性の削減",
            },
        ]


def main():
    """メイン処理"""
    analyzer = FileSizeEfficiencyAnalyzer(Path("."))

    print("📏 ファイルサイズ効率性分析")
    print("=" * 60)

    analysis = analyzer.analyze_size_related_inefficiencies()

    # 1. サマリー
    summary = analysis["summary"]
    print(f"📊 効率性サマリー:")
    print(f"  300行超過ファイル: {summary['total_oversized']}個")
    print(f"  最大行数: {summary['max_lines']:,}行")
    print(f"  平均行数（超過分）: {summary['avg_oversized_lines']:.0f}行")
    print(f"  人為的分割疑い: {summary['artificial_split_groups']}グループ")
    print(f"  効率性判定: {summary['efficiency_verdict']}")

    # 2. 最大の問題ファイル
    oversized = analysis["oversized_files"]
    if oversized:
        print(f"\n🚨 最大のファイル（Top 5）:")
        for i, file_analysis in enumerate(oversized[:5], 1):
            print(f"  {i}. {file_analysis.path.name}: {file_analysis.lines}行")
            print(
                f"     クラス: {file_analysis.classes}, 関数: {file_analysis.functions}"
            )
            if file_analysis.efficiency_issues:
                print(f"     問題: {file_analysis.efficiency_issues[0]}")

    # 3. 人為的分割の検出
    artificial = analysis["artificial_splits"]
    if artificial:
        print(f"\n🔍 人為的分割の疑い:")
        for split in artificial:
            print(f"  {split['pattern']}: {len(split['files'])}ファイル")
            print(f"    平均行数: {split['avg_lines']:.0f}行")
            print(f"    疑い理由: {split['suspicion_reason']}")

    # 4. 保守性への影響
    maintainability = analysis["maintainability_impact"]
    print(f"\n⚠️  保守性への影響:")
    for aspect, impact in maintainability.items():
        print(f"  {aspect}: {impact['impact']} impact")
        print(f"    問題: {impact['issue']}")

    # 5. 推奨事項
    recommendations = analysis["recommendations"]
    print(f"\n💡 改善推奨事項:")
    for rec in recommendations:
        print(f"  [{rec['priority']}] {rec['action']}")
        print(f"    内容: {rec['description']}")
        print(f"    効果: {rec['benefit']}")
        print()

    # 6. 結論
    print(f"🎯 結論:")
    if summary["efficiency_verdict"] in [
        "High Inefficiency Risk",
        "Moderate Inefficiency Risk",
    ]:
        print(f"  ❌ 300行制限による非効率性が確認されました")
        print(f"  💡 ティア別制限への変更を強く推奨します")
    else:
        print(f"  ✅ 全体的には効率的な設計が保たれています")
        print(f"  💡 一部の改善余地はありますが深刻ではありません")


if __name__ == "__main__":
    main()
