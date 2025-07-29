#!/usr/bin/env python3
"""
Quality Gate Checker - Issue #640 Phase 1
品質ゲートシステム

目的: ティア別品質基準の自動チェック
- Critical Tier: 95%カバレッジ必須
- Important Tier: 85%カバレッジ推奨
- Supportive Tier: 70%カバレッジ基準
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class TierLevel(Enum):
    """ティアレベル定義"""

    CRITICAL = "critical"
    IMPORTANT = "important"
    SUPPORTIVE = "supportive"
    SPECIAL = "special"


@dataclass
class QualityGateResult:
    """品質ゲート結果"""

    module_name: str
    tier: TierLevel
    coverage_percentage: float
    required_coverage: float
    complexity_score: float
    max_complexity: float
    test_count: int
    required_tests: List[str]
    passed: bool
    violations: List[str]


class QualityGateChecker:
    """品質ゲートチェッカー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.quality_gates_config = self._load_quality_gates()

    def _load_quality_gates(self) -> Dict:
        """品質ゲート設定の読み込み"""
        config_path = self.project_root / "scripts" / "quality_gates.json"

        if not config_path.exists():
            logger.warning("品質ゲート設定が見つかりません。デフォルト設定を使用")
            return self._get_default_quality_gates()

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_default_quality_gates(self) -> Dict:
        """デフォルト品質ゲート設定"""
        return {
            "critical_tier": {
                "modules": [
                    "kumihan_formatter.core.parser",
                    "kumihan_formatter.core.renderer",
                    "kumihan_formatter.commands",
                ],
                "min_coverage": 95.0,
                "required_tests": ["unit", "integration"],
                "max_complexity": 10,
            },
            "important_tier": {
                "modules": [
                    "kumihan_formatter.core.validation",
                    "kumihan_formatter.core.file_operations",
                ],
                "min_coverage": 85.0,
                "required_tests": ["unit"],
                "max_complexity": 15,
            },
            "supportive_tier": {
                "modules": [
                    "kumihan_formatter.core.utilities",
                    "kumihan_formatter.core.caching",
                ],
                "min_coverage": 70.0,
                "required_tests": ["integration"],
                "max_complexity": 20,
            },
            "special_tier": {
                "modules": [
                    "kumihan_formatter.gui",
                    "kumihan_formatter.playground",
                ],
                "min_coverage": 50.0,  # E2E/手動テストでカバー
                "required_tests": ["e2e"],
                "max_complexity": 25,
            },
        }

    def check_all_gates(self) -> List[QualityGateResult]:
        """全品質ゲートのチェック"""
        logger.info("🔍 品質ゲートチェックを開始...")

        all_results = []

        for tier_name, config in self.quality_gates_config.items():
            tier = TierLevel(tier_name.replace("_tier", ""))

            for module_name in config["modules"]:
                result = self._check_module_quality(module_name, tier, config)
                all_results.append(result)

                if result.passed:
                    logger.info(f"✅ {module_name} ({tier.value}): 品質ゲート通過")
                else:
                    logger.error(f"❌ {module_name} ({tier.value}): 品質ゲート違反")
                    for violation in result.violations:
                        logger.error(f"   - {violation}")

        return all_results

    def _check_module_quality(
        self, module_name: str, tier: TierLevel, config: Dict
    ) -> QualityGateResult:
        """個別モジュールの品質チェック"""

        # カバレッジ取得
        coverage_percentage = self._get_module_coverage(module_name)

        # 複雑度取得
        complexity_score = self._get_module_complexity(module_name)

        # テスト数取得
        test_count = self._get_module_test_count(module_name)

        # 違反チェック
        violations = []
        required_coverage = config["min_coverage"]
        max_complexity = config["max_complexity"]
        required_tests = config["required_tests"]

        if coverage_percentage < required_coverage:
            violations.append(
                f"カバレッジ不足: {coverage_percentage:.1f}% < {required_coverage}%"
            )

        if complexity_score > max_complexity:
            violations.append(f"複雑度超過: {complexity_score:.1f} > {max_complexity}")

        if test_count == 0:
            violations.append("テストが存在しません")

        passed = len(violations) == 0

        return QualityGateResult(
            module_name=module_name,
            tier=tier,
            coverage_percentage=coverage_percentage,
            required_coverage=required_coverage,
            complexity_score=complexity_score,
            max_complexity=max_complexity,
            test_count=test_count,
            required_tests=required_tests,
            passed=passed,
            violations=violations,
        )

    def _get_module_coverage(self, module_name: str) -> float:
        """モジュール別カバレッジ取得"""
        try:
            # カバレッジレポート生成
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                f"--cov={module_name}",
                "--cov-report=json:temp_coverage.json",
                "--collect-only",
                "-q",
            ]

            subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

            coverage_file = self.project_root / "temp_coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                    return data["totals"]["percent_covered"]

        except Exception as e:
            logger.warning(f"カバレッジ取得失敗 {module_name}: {e}")

        return 0.0

    def _get_module_complexity(self, module_name: str) -> float:
        """モジュール複雑度取得"""
        try:
            # radon使用して複雑度計算
            module_path = module_name.replace(".", "/") + ".py"
            full_path = self.project_root / module_path

            if not full_path.exists():
                # パッケージの場合は__init__.pyまたはディレクトリ内の平均
                package_path = self.project_root / module_name.replace(".", "/")
                if package_path.is_dir():
                    return self._calculate_package_complexity(package_path)

            cmd = ["radon", "cc", str(full_path), "-s", "-a"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 平均複雑度を抽出
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Average complexity:" in line:
                        return float(line.split()[-1])

        except Exception as e:
            logger.warning(f"複雑度取得失敗 {module_name}: {e}")

        return 0.0

    def _calculate_package_complexity(self, package_path: Path) -> float:
        """パッケージ全体の平均複雑度計算"""
        complexities = []

        for py_file in package_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue

            try:
                cmd = ["radon", "cc", str(py_file), "-s", "-a"]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if "Average complexity:" in line:
                            complexities.append(float(line.split()[-1]))
                            break
            except:
                continue

        return sum(complexities) / len(complexities) if complexities else 0.0

    def _get_module_test_count(self, module_name: str) -> int:
        """モジュールのテスト数取得"""
        try:
            # テストファイル検索
            test_pattern = f"**/test_{module_name.split('.')[-1]}*.py"
            test_files = list(self.project_root.glob(test_pattern))

            if not test_files:
                # より広範囲な検索
                test_pattern = f"**/test_*{module_name.split('.')[-1]}*.py"
                test_files = list(self.project_root.glob(test_pattern))

            total_tests = 0
            for test_file in test_files:
                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(test_file),
                    "--collect-only",
                    "-q",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    # テスト数をカウント
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if " tests collected" in line:
                            total_tests += int(line.split()[0])
                            break

            return total_tests

        except Exception as e:
            logger.warning(f"テスト数取得失敗 {module_name}: {e}")
            return 0

    def generate_quality_report(self, results: List[QualityGateResult]) -> str:
        """品質レポート生成"""
        report = []
        report.append("=" * 60)
        report.append("品質ゲートレポート - Issue #640 Phase 1")
        report.append("=" * 60)
        report.append("")

        # ティア別サマリー
        tier_summary = {}
        for result in results:
            tier_name = result.tier.value
            if tier_name not in tier_summary:
                tier_summary[tier_name] = {"total": 0, "passed": 0}
            tier_summary[tier_name]["total"] += 1
            if result.passed:
                tier_summary[tier_name]["passed"] += 1

        report.append("📊 ティア別サマリー:")
        for tier, summary in tier_summary.items():
            passed_rate = summary["passed"] / summary["total"] * 100
            status = "✅" if passed_rate == 100 else "⚠️" if passed_rate >= 80 else "❌"
            report.append(
                f"  {status} {tier.title()} Tier: {summary['passed']}/{summary['total']} ({passed_rate:.1f}%)"
            )

        report.append("")
        report.append("🔍 詳細結果:")

        for result in results:
            status = "✅" if result.passed else "❌"
            report.append(f"{status} {result.module_name} ({result.tier.value})")
            report.append(
                f"    カバレッジ: {result.coverage_percentage:.1f}% (要求: {result.required_coverage}%)"
            )
            report.append(
                f"    複雑度: {result.complexity_score:.1f} (上限: {result.max_complexity})"
            )
            report.append(f"    テスト数: {result.test_count}")

            if result.violations:
                report.append("    違反項目:")
                for violation in result.violations:
                    report.append(f"      - {violation}")
            report.append("")

        # 改善提案
        failed_results = [r for r in results if not r.passed]
        if failed_results:
            report.append("💡 改善提案:")

            critical_failures = [
                r for r in failed_results if r.tier == TierLevel.CRITICAL
            ]
            if critical_failures:
                report.append("  🚨 Critical Tier緊急対応:")
                for result in critical_failures:
                    report.append(f"    - {result.module_name}: 即座にテスト追加が必要")

            report.append("  📈 推奨アクション:")
            report.append("    1. 失敗モジュールへの単体テスト追加")
            report.append("    2. 複雑度の高い関数のリファクタリング")
            report.append("    3. テストカバレッジの段階的向上")

        return "\n".join(report)


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent

    checker = QualityGateChecker(project_root)

    logger.info("🚀 品質ゲートチェック開始 - Issue #640 Phase 1")

    # 全品質ゲートチェック
    results = checker.check_all_gates()

    # レポート生成
    report = checker.generate_quality_report(results)

    # レポート出力
    report_path = project_root / "quality_gate_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # コンソール出力
    print(report)

    # 全体結果判定
    failed_count = len([r for r in results if not r.passed])
    total_count = len(results)

    if failed_count == 0:
        logger.info("🎯 全品質ゲート通過!")
        sys.exit(0)
    else:
        logger.error(f"❌ 品質ゲート違反: {failed_count}/{total_count}")
        sys.exit(1)


if __name__ == "__main__":
    main()
