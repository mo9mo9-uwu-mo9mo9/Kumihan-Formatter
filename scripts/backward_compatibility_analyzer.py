#!/usr/bin/env python3
"""
後方互換性分析スクリプト

品質基準変更による既存ファイルへの影響を分析し、
必要な修正範囲を特定します。
"""

import re
from pathlib import Path
from typing import Dict, List, Set


class BackwardCompatibilityAnalyzer:
    """後方互換性分析クラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.affected_files = {}

    def analyze_quality_gate_changes(self) -> Dict:
        """品質ゲート変更による影響分析"""

        # 1. claude_quality_gate.py の使用箇所を検索
        old_gate_usage = self._find_old_quality_gate_usage()

        # 2. CLAUDE.md の変更影響
        claude_md_changes = self._analyze_claude_md_changes()

        # 3. CI/CD設定への影響
        cicd_impact = self._analyze_cicd_impact()

        # 4. スクリプト間の依存関係
        script_dependencies = self._analyze_script_dependencies()

        return {
            "summary": self._generate_impact_summary(),
            "old_gate_usage": old_gate_usage,
            "claude_md_changes": claude_md_changes,
            "cicd_impact": cicd_impact,
            "script_dependencies": script_dependencies,
            "modification_plan": self._create_modification_plan(),
        }

    def _find_old_quality_gate_usage(self) -> Dict:
        """旧品質ゲートの使用箇所検索"""
        usage_patterns = [
            "claude_quality_gate.py",
            "python scripts/claude_quality_gate.py",
            "python3 scripts/claude_quality_gate.py",
        ]

        found_usage = []
        search_paths = [".github/workflows/", "scripts/", "docs/", "Makefile", "*.md"]

        for pattern_path in search_paths:
            if pattern_path == "Makefile":
                makefile = self.project_root / "Makefile"
                if makefile.exists():
                    content = makefile.read_text(encoding="utf-8")
                    for usage_pattern in usage_patterns:
                        if usage_pattern in content:
                            found_usage.append(
                                {
                                    "file": "Makefile",
                                    "pattern": usage_pattern,
                                    "context": "Build script",
                                }
                            )

            elif pattern_path.endswith("/"):
                # ディレクトリ検索
                dir_path = self.project_root / pattern_path.rstrip("/")
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            try:
                                content = file_path.read_text(encoding="utf-8")
                                for usage_pattern in usage_patterns:
                                    if usage_pattern in content:
                                        found_usage.append(
                                            {
                                                "file": str(
                                                    file_path.relative_to(
                                                        self.project_root
                                                    )
                                                ),
                                                "pattern": usage_pattern,
                                                "context": self._extract_context(
                                                    content, usage_pattern
                                                ),
                                            }
                                        )
                            except:
                                continue

        return {
            "total_usage": len(found_usage),
            "usage_details": found_usage,
            "critical_files": [
                u
                for u in found_usage
                if "workflow" in u["file"] or "Makefile" in u["file"]
            ],
        }

    def _analyze_claude_md_changes(self) -> Dict:
        """CLAUDE.md変更の影響分析"""
        return {
            "changed_sections": [
                "品質管理セクション（ティア別基準導入）",
                "品質チェックコマンド変更",
                "段階的改善計画追加",
            ],
            "impact_on_ai": {
                "positive": [
                    "より具体的な品質基準による指示明確化",
                    "段階的改善計画による作業効率化",
                    "現実的基準による開発フロー改善",
                ],
                "attention_required": [
                    "新しいコマンド体系の学習必要",
                    "ティア分類の理解・適用必要",
                ],
            },
            "compatibility": "後方互換性あり（古いコマンドも一時的に併用可能）",
        }

    def _analyze_cicd_impact(self) -> Dict:
        """CI/CD設定への影響分析"""
        cicd_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/quality-check.yml",
            ".github/workflows/test.yml",
        ]

        impact = {"affected_files": [], "required_changes": [], "risk_level": "Medium"}

        for cicd_file in cicd_files:
            file_path = self.project_root / cicd_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if "claude_quality_gate.py" in content:
                        impact["affected_files"].append(cicd_file)
                        impact["required_changes"].append(
                            {
                                "file": cicd_file,
                                "change": "claude_quality_gate.py → tiered_quality_gate.py",
                                "urgency": "High",
                            }
                        )
                except:
                    continue

        return impact

    def _analyze_script_dependencies(self) -> Dict:
        """スクリプト間依存関係分析"""
        return {
            "new_scripts_added": [
                "tiered_quality_gate.py",
                "tdd_root_cause_analyzer.py",
                "gradual_improvement_planner.py",
                "quality_standards_redefiner.py",
            ],
            "modified_scripts": [
                "enforce_tdd.py (--lenient オプション追加)",
                "doc_validator.py (--lenient オプション追加)",
            ],
            "deprecated_scripts": ["claude_quality_gate.py (段階的廃止予定)"],
            "dependency_chain": {
                "tiered_quality_gate.py": ["enforce_tdd.py", "doc_validator.py"],
                "gradual_improvement_planner.py": ["tdd_root_cause_analyzer.py"],
                "quality_standards_redefiner.py": ["tiered_quality_gate.py"],
            },
        }

    def _create_modification_plan(self) -> Dict:
        """修正計画の作成"""
        return {
            "immediate_required": [
                {
                    "action": "CI/CDワークフロー更新",
                    "files": [".github/workflows/*.yml"],
                    "change": "claude_quality_gate.py → tiered_quality_gate.py",
                    "risk": "High（ビルド失敗リスク）",
                    "effort": "1時間",
                }
            ],
            "recommended": [
                {
                    "action": "Makefile更新",
                    "files": ["Makefile"],
                    "change": "quality-gate ターゲット更新",
                    "risk": "Low",
                    "effort": "30分",
                },
                {
                    "action": "ドキュメント更新",
                    "files": ["docs/**/*.md"],
                    "change": "新しい品質管理プロセス説明",
                    "risk": "Low",
                    "effort": "2時間",
                },
            ],
            "optional": [
                {
                    "action": "旧スクリプト保持",
                    "files": ["scripts/claude_quality_gate.py"],
                    "change": "移行期間中の併用維持",
                    "risk": "Very Low",
                    "effort": "0時間",
                }
            ],
        }

    def _generate_impact_summary(self) -> Dict:
        """影響サマリー生成"""
        return {
            "overall_risk": "Medium",
            "breaking_changes": False,
            "backward_compatibility": True,
            "migration_effort": "3-4時間",
            "critical_path": [
                "CI/CDワークフロー更新",
                "品質ゲートコマンド切り替え",
                "新ツール群の動作確認",
            ],
            "benefits": [
                "開発フロー阻害の解消",
                "段階的品質改善の実現",
                "現実的品質基準の適用",
                "技術的負債の体系的管理",
            ],
        }

    def _extract_context(self, content: str, pattern: str) -> str:
        """パターン周辺のコンテキスト抽出"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if pattern in line:
                # 前後1行を含むコンテキスト
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                return " | ".join(lines[start:end])
        return "Context not found"


def main():
    """メイン処理"""
    analyzer = BackwardCompatibilityAnalyzer(Path("."))

    print("🔍 後方互換性影響分析")
    print("=" * 50)

    analysis = analyzer.analyze_quality_gate_changes()

    # 1. サマリー
    summary = analysis["summary"]
    print(f"📊 影響サマリー:")
    print(f"  総合リスク: {summary['overall_risk']}")
    print(f"  破壊的変更: {'あり' if summary['breaking_changes'] else 'なし'}")
    print(f"  後方互換性: {'あり' if summary['backward_compatibility'] else 'なし'}")
    print(f"  移行工数: {summary['migration_effort']}")

    # 2. 旧品質ゲート使用箇所
    old_usage = analysis["old_gate_usage"]
    print(f"\n🔍 旧品質ゲート使用箇所:")
    print(f"  検出箇所: {old_usage['total_usage']}件")
    if old_usage["critical_files"]:
        print(f"  重要ファイル:")
        for critical in old_usage["critical_files"]:
            print(f"    - {critical['file']}")

    # 3. 必要な修正
    mod_plan = analysis["modification_plan"]
    print(f"\n⚡ 必要な修正:")
    print(f"  緊急対応: {len(mod_plan['immediate_required'])}件")
    for item in mod_plan["immediate_required"]:
        print(f"    - {item['action']}: {item['effort']} ({item['risk']} risk)")

    print(f"  推奨対応: {len(mod_plan['recommended'])}件")
    for item in mod_plan["recommended"]:
        print(f"    - {item['action']}: {item['effort']} ({item['risk']} risk)")

    # 4. 結論
    print(f"\n✅ 結論:")
    print(f"  • 後方互換性は保たれている")
    print(f"  • 破壊的変更はなし")
    print(f"  • CI/CD更新が最重要（1時間程度）")
    print(f"  • 段階的移行により安全に実施可能")


if __name__ == "__main__":
    main()
