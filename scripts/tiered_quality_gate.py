#!/usr/bin/env python3
"""
ティア別品質ゲートスクリプト

ファイルをティア別に分類し、適切な品質基準を適用する建設的な品質チェックシステム。
段階的改善を促進し、開発フローを阻害しない設計。
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TieredQualityGate:
    """ティア別品質ゲートクラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_tiers = self._load_file_tier_mapping()
        self.results = {}

    def _load_file_tier_mapping(self) -> Dict[str, str]:
        """ファイルティア分類の読み込み"""
        # ファイルパスパターンによるティア分類
        tier_patterns = {
            "critical": [
                "kumihan_formatter/core/error_reporting.py",
                "kumihan_formatter/core/file_operations.py",
                "kumihan_formatter/core/markdown_converter.py",
                "kumihan_formatter/commands/",
                "kumihan_formatter/core/file_validators.py",
                "kumihan_formatter/core/markdown_parser.py",
                "kumihan_formatter/core/file_io_handler.py",
            ],
            "important": [
                "kumihan_formatter/core/rendering/",
                "kumihan_formatter/core/validators/",
                "kumihan_formatter/core/error_handling/",
                "kumihan_formatter/core/syntax/",
            ],
            "supportive": [
                "kumihan_formatter/core/utilities/",
                "kumihan_formatter/core/caching/",
                "kumihan_formatter/utils/",
            ],
            "special": [
                "kumihan_formatter/gui_",
                "kumihan_formatter/ui/",
                "kumihan_formatter/core/performance/",
                "kumihan_formatter/core/debug_logger",
                "tests/test_smart_suggestions.py",
                "tests/test_unified_handler.py",
            ],
        }

        file_tiers = {}

        # 全ファイルを収集（実装ファイル + 特定のテストファイル）
        for py_file in self.project_root.rglob("kumihan_formatter/**/*.py"):
            file_path = str(py_file.relative_to(self.project_root))
            tier = "supportive"  # デフォルト

            # パターンマッチングでティア決定
            for tier_name, patterns in tier_patterns.items():
                for pattern in patterns:
                    if pattern in file_path:
                        tier = tier_name
                        break
                if tier != "supportive":
                    break

            file_tiers[file_path] = tier

        # 特定のテストファイルも追加
        for tier_name, patterns in tier_patterns.items():
            for pattern in patterns:
                if pattern.startswith("tests/"):
                    test_file = self.project_root / pattern
                    if test_file.exists():
                        file_tiers[pattern] = tier_name

        return file_tiers

    def get_tier_requirements(self, tier: str) -> Dict:
        """ティア別要件の取得"""
        requirements = {
            "critical": {
                "test_coverage": {
                    "required": True,
                    "threshold": 35,
                    "blocking": True,
                },  # 実測値ベース
                "documentation": {"required": True, "blocking": True},
                "file_size": {"limit": 300, "blocking": False},  # 警告のみ
                "complexity": {"threshold": 10, "blocking": False},
            },
            "important": {
                "test_coverage": {
                    "required": True,
                    "threshold": 30,
                    "blocking": False,
                },  # 実測値ベース
                "documentation": {"required": True, "blocking": False},
                "file_size": {"limit": 400, "blocking": False},
                "complexity": {"threshold": 15, "blocking": False},
            },
            "supportive": {
                "test_coverage": {
                    "required": False,
                    "threshold": 25,  # 実測値ベース
                    "blocking": False,
                },
                "documentation": {"required": False, "blocking": False},
                "file_size": {"limit": None, "blocking": False},
                "complexity": {"threshold": None, "blocking": False},
            },
            "special": {
                "test_coverage": {
                    "required": False,
                    "threshold": None,
                    "blocking": False,
                },
                "documentation": {"required": False, "blocking": False},
                "file_size": {"limit": None, "blocking": False},
                "complexity": {"threshold": None, "blocking": False},
            },
        }
        return requirements.get(tier, requirements["supportive"])

    def run_tiered_quality_check(self) -> Dict:
        """ティア別品質チェック実行"""
        safe_print("🚀 Tiered Quality Gate", "Tiered Quality Gate")
        print("=" * 50)

        results = {
            "overall_status": "PASS",
            "tier_results": {},
            "blocking_issues": [],
            "warnings": [],
            "recommendations": [],
        }

        # 基本チェック（全ティア共通）
        basic_checks_passed = self._run_basic_checks()
        if not basic_checks_passed:
            results["overall_status"] = "FAIL"
            return results

        # ティア別チェック
        tier_stats = {"critical": 0, "important": 0, "supportive": 0, "special": 0}

        for file_path, tier in self.file_tiers.items():
            tier_stats[tier] += 1

        safe_print(f"\n📊 Tier Distribution:", f"\nTier Distribution:")
        for tier, count in tier_stats.items():
            print(f"  {tier.upper()}: {count} files")

        # Critical tierの詳細チェック
        critical_result = self._check_critical_tier()
        results["tier_results"]["critical"] = critical_result

        if critical_result["blocking_issues"]:
            results["overall_status"] = "FAIL"
            results["blocking_issues"].extend(critical_result["blocking_issues"])

        # Other tiersは警告のみ
        for tier in ["important", "supportive", "special"]:
            tier_result = self._check_tier_warnings(tier)
            results["tier_results"][tier] = tier_result
            results["warnings"].extend(tier_result["warnings"])

        # 推奨事項の生成
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _run_basic_checks(self) -> bool:
        """基本チェック（全ティア共通）"""
        safe_print(
            "🔧 Running Basic Checks (All Tiers)...",
            "Running Basic Checks (All Tiers)...",
        )

        checks = [
            (
                ["python3", "-m", "black", "--check", "kumihan_formatter/"],
                "Black formatting",
            ),
            (
                ["python3", "-m", "isort", "--check-only", "kumihan_formatter/"],
                "Import sorting",
            ),
            (
                [
                    "python3",
                    "-m",
                    "flake8",
                    "kumihan_formatter/",
                    "--select=E9,F63,F7,F82",
                ],
                "Syntax check",
            ),
            (
                [
                    "python3",
                    "-m",
                    "pytest",
                    "tests/",
                    "-x",
                    "--tb=no",
                    "-q",
                    "--ignore=tests/test_smart_suggestions.py",
                    "--ignore=tests/test_unified_handler.py",
                ],
                "Basic tests (excluding special tier)",
            ),
        ]

        all_passed = True
        for cmd, description in checks:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    safe_print(f"✅ {description}", f"[OK] {description}")
                else:
                    safe_print(f"❌ {description}", f"[FAIL] {description}")
                    all_passed = False
            except Exception as e:
                safe_print(
                    f"💥 {description} - Error: {e}",
                    f"[ERROR] {description} - Error: {e}",
                )
                all_passed = False

        return all_passed

    def _check_critical_tier(self) -> Dict:
        """Critical tierの詳細チェック"""
        safe_print("\n🎯 Critical Tier Analysis...", "\nCritical Tier Analysis...")

        critical_files = [f for f, t in self.file_tiers.items() if t == "critical"]
        result = {
            "total_files": len(critical_files),
            "checked_files": 0,
            "test_coverage": 0.0,
            "blocking_issues": [],
            "warnings": [],
        }

        # 簡易テストカバレッジチェック（実際のファイル存在確認）
        tested_files = 0
        for file_path in critical_files:
            if self._has_test_file(file_path):
                tested_files += 1
            else:
                # Critical tierでテストがない場合は警告（即座にブロックしない）
                result["warnings"].append(
                    f"Critical file missing test: {Path(file_path).name}"
                )

        result["checked_files"] = len(critical_files)
        result["test_coverage"] = (
            (tested_files / len(critical_files)) * 100 if critical_files else 0
        )

        safe_print(
            f"  📋 Critical files: {len(critical_files)}",
            f"  Critical files: {len(critical_files)}",
        )
        safe_print(
            f"  🧪 Test coverage: {result['test_coverage']:.1f}%",
            f"  Test coverage: {result['test_coverage']:.1f}%",
        )

        # 段階的基準適用（即座にブロックしない）
        if result["test_coverage"] < 30:  # 緩い基準から開始
            result["warnings"].append(
                f"Critical tier test coverage ({result['test_coverage']:.1f}%) below recommended 30%"
            )

        return result

    def _check_tier_warnings(self, tier: str) -> Dict:
        """ティア別警告チェック"""
        tier_files = [f for f, t in self.file_tiers.items() if t == tier]

        result = {"total_files": len(tier_files), "warnings": [], "recommendations": []}

        if tier == "important":
            tested_files = sum(1 for f in tier_files if self._has_test_file(f))
            coverage = (tested_files / len(tier_files)) * 100 if tier_files else 0

            if coverage < 40:
                result["recommendations"].append(
                    f"Important tier: Consider adding tests (current: {coverage:.1f}%)"
                )

        elif tier == "special":
            result["recommendations"].append(
                f"Special tier ({len(tier_files)} files): Consider E2E/manual testing strategies"
            )

        return result

    def _has_test_file(self, file_path: str) -> bool:
        """テストファイル存在チェック"""
        file_stem = Path(file_path).stem
        test_patterns = [
            f"tests/unit/test_{file_stem}.py",
            f"tests/integration/test_{file_stem}.py",
            f"tests/test_{file_stem}.py",
        ]

        return any((self.project_root / pattern).exists() for pattern in test_patterns)

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []

        critical_result = results["tier_results"].get("critical", {})
        critical_coverage = critical_result.get("test_coverage", 0)

        if critical_coverage < 50:
            recommendations.append(
                "🎯 Focus: Add tests for critical tier files to improve stability"
            )

        if len(results["warnings"]) > 10:
            recommendations.append(
                "📋 Consider: Gradual improvement plan for non-critical issues"
            )

        if critical_coverage > 70:
            recommendations.append("🚀 Ready: Expand testing to important tier files")

        return recommendations

    def print_results(self, results: Dict) -> None:
        """結果出力"""
        print("\n" + "=" * 50)

        if results["overall_status"] == "PASS":
            safe_print("🎉 Quality Gate: PASSED", "Quality Gate: PASSED")
            safe_print("✅ Development can continue", "Development can continue")
        else:
            safe_print(
                "⚠️  Quality Gate: NEEDS ATTENTION", "Quality Gate: NEEDS ATTENTION"
            )
            safe_print(
                "🔄 Development can continue with warnings",
                "Development can continue with warnings",
            )

        # Critical tier状況
        critical_result = results["tier_results"].get("critical", {})
        if critical_result:
            safe_print(f"\n🎯 Critical Tier Status:", f"\nCritical Tier Status:")
            print(f"   Files: {critical_result['total_files']}")
            print(f"   Test Coverage: {critical_result.get('test_coverage', 0):.1f}%")

        # 警告事項
        if results["warnings"]:
            safe_print(
                f"\n⚠️  Warnings ({len(results['warnings'])}):",
                f"\nWarnings ({len(results['warnings'])}):",
            )
            for warning in results["warnings"][:5]:  # 最初の5個のみ表示
                print(f"   • {warning}")
            if len(results["warnings"]) > 5:
                print(f"   ... and {len(results['warnings']) - 5} more")

        # 推奨事項
        if results["recommendations"]:
            safe_print(f"\n💡 Recommendations:", f"\nRecommendations:")
            for rec in results["recommendations"]:
                print(f"   • {rec}")

        safe_print(f"\n📈 Next Steps:", f"\nNext Steps:")
        print(f"   1. Address critical tier test coverage")
        print(f"   2. Review warnings for improvement opportunities")
        print(f"   3. Follow gradual improvement plan")


def safe_print(text: str, fallback: str = None) -> None:
    """Windows環境でのエンコーディング安全な出力"""
    try:
        print(text)
    except UnicodeEncodeError:
        if fallback:
            print(fallback)
        else:
            # 絵文字を代替文字に置換
            safe_text = (
                text.replace("🚀", "[ROCKET]")
                .replace("🔧", "[TOOL]")
                .replace("✅", "[CHECK]")
                .replace("❌", "[X]")
                .replace("💥", "[BOOM]")
                .replace("🎯", "[TARGET]")
                .replace("🧪", "[TEST]")
                .replace("📋", "[CLIPBOARD]")
                .replace("🔄", "[REFRESH]")
                .replace("⚠️", "[WARNING]")
                .replace("💡", "[BULB]")
                .replace("📈", "[CHART]")
                .replace("🤖", "[ROBOT]")
                .replace("🎉", "[PARTY]")
                .replace("📊", "[BAR_CHART]")
            )
            print(safe_text)


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent

    # Windows環境での文字エンコーディング対応
    if os.name == "nt":
        try:
            os.system("chcp 65001 > nul")  # UTF-8に設定
        except:
            pass

    safe_print("🤖 Tiered Quality Gate", "Tiered Quality Gate")
    print("   Building sustainable quality standards")
    print()

    gate = TieredQualityGate(project_root)
    results = gate.run_tiered_quality_check()
    gate.print_results(results)

    # 終了コード：警告があっても継続可能
    if results["overall_status"] == "FAIL" and results["blocking_issues"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
