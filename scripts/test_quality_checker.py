#!/usr/bin/env python3
"""
テスト品質自動チェッカー

Issue #1120: テスト品質ガイドライン策定
テスト肥大化防止のための自動品質チェック機能

Usage:
    python3 scripts/test_quality_checker.py
    python3 scripts/test_quality_checker.py --category unit
    python3 scripts/test_quality_checker.py --strict
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, NamedTuple
from collections import defaultdict


class TestQualityReport(NamedTuple):
    """テスト品質レポートの構造"""
    total_tests: int
    category_counts: Dict[str, int]
    violations: List[str]
    warnings: List[str]
    recommendations: List[str]


class TestQualityChecker:
    """テスト品質チェック機能"""

    # ガイドライン基準値
    LIMITS = {
        'total_tests': 1500,
        'categories': {
            'unit': 1450,
            'unit/rendering': 130,
            'unit/config': 100,
            'unit/ast_nodes': 100,
            'unit/patterns': 95,
            'unit/parsing': 80,
            'integration': 100,
            'performance': 50,
            'system': 30,
            'end_to_end': 30,
        }
    }

    # 命名規約パターン
    NAMING_PATTERNS = {
        'good': [
            r'test_\w+_\w+_\w+',  # test_function_condition_result
            r'test_\w+_returns_\w+',  # test_function_returns_value
            r'test_\w+_raises_\w+',   # test_function_raises_error
            r'test_\w+_when_\w+',     # test_function_when_condition
        ],
        'bad': [
            r'test_\d+$',           # test_1
            r'test_[a-z]$',         # test_a
            r'test_\w{1,3}$',       # test_fn (too short)
            r'test_\w*正常系\w*',     # Japanese in test name
        ]
    }

    def __init__(self, tests_dir: str = "tests"):
        self.tests_dir = Path(tests_dir)
        self.test_files = list(self.tests_dir.rglob("test_*.py"))

    def count_test_methods(self, file_path: Path) -> List[str]:
        """ファイル内のテストメソッド名リストを取得"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return re.findall(r'def (test_\w+)', content)
        except Exception as e:
            print(f"⚠️ ファイル読み込みエラー: {file_path} - {e}")
            return []

    def categorize_test(self, file_path: Path) -> str:
        """テストファイルのカテゴリを判定"""
        relative_path = file_path.relative_to(self.tests_dir)
        parts = relative_path.parts

        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}" if parts[0] == 'unit' else parts[0]
        return parts[0] if parts else 'unknown'

    def check_test_count_limits(self) -> Tuple[List[str], List[str]]:
        """テスト数の上限チェック"""
        violations = []
        warnings = []

        # カテゴリ別集計
        category_counts = defaultdict(int)
        total_tests = 0

        for test_file in self.test_files:
            test_methods = self.count_test_methods(test_file)
            category = self.categorize_test(test_file)
            category_counts[category] += len(test_methods)
            total_tests += len(test_methods)

        # 総数チェック
        if total_tests > self.LIMITS['total_tests']:
            violations.append(
                f"❌ テスト総数上限超過: {total_tests}/{self.LIMITS['total_tests']}"
            )
        elif total_tests > self.LIMITS['total_tests'] * 0.9:
            warnings.append(
                f"⚠️ テスト総数が上限に接近: {total_tests}/{self.LIMITS['total_tests']} "
                f"({total_tests/self.LIMITS['total_tests']*100:.1f}%)"
            )

        # カテゴリ別チェック
        for category, count in category_counts.items():
            limit = self.LIMITS['categories'].get(category)
            if limit and count > limit:
                violations.append(
                    f"❌ {category} テスト数上限超過: {count}/{limit}"
                )
            elif limit and count > limit * 0.9:
                warnings.append(
                    f"⚠️ {category} テスト数が上限に接近: {count}/{limit} "
                    f"({count/limit*100:.1f}%)"
                )

        return violations, warnings, category_counts, total_tests

    def check_naming_conventions(self) -> Tuple[List[str], List[str]]:
        """命名規約チェック"""
        violations = []
        warnings = []

        for test_file in self.test_files:
            test_methods = self.count_test_methods(test_file)

            for method_name in test_methods:
                # 悪いパターンチェック
                for bad_pattern in self.NAMING_PATTERNS['bad']:
                    if re.match(bad_pattern, method_name):
                        violations.append(
                            f"❌ 命名規約違反: {method_name} in {test_file.relative_to(self.tests_dir)}"
                        )
                        break
                else:
                    # 良いパターンのいずれかにマッチするかチェック
                    good_match = False
                    for good_pattern in self.NAMING_PATTERNS['good']:
                        if re.match(good_pattern, method_name):
                            good_match = True
                            break

                    if not good_match and len(method_name.split('_')) < 4:
                        warnings.append(
                            f"⚠️ 命名推奨改善: {method_name} "
                            f"(推奨: test_機能名_条件_期待結果)"
                        )

        return violations, warnings

    def check_test_density(self) -> List[str]:
        """テスト密度チェック（1ファイルあたりのテスト数）"""
        warnings = []

        for test_file in self.test_files:
            test_methods = self.count_test_methods(test_file)
            test_count = len(test_methods)

            # 1ファイルに過度に多くのテストがある場合
            if test_count > 50:
                warnings.append(
                    f"⚠️ テスト密度過多: {test_file.relative_to(self.tests_dir)} "
                    f"({test_count}個) - 分割を検討"
                )
            # 1ファイルにテストが1個しかない場合
            elif test_count == 1:
                warnings.append(
                    f"⚠️ テスト密度過少: {test_file.relative_to(self.tests_dir)} "
                    f"(1個) - 統合を検討"
                )

        return warnings

    def check_duplicate_patterns(self) -> List[str]:
        """重複テストパターンの検出"""
        warnings = []
        test_patterns = defaultdict(list)

        for test_file in self.test_files:
            test_methods = self.count_test_methods(test_file)
            for method_name in test_methods:
                # テスト名から機能部分を抽出
                pattern = re.sub(r'test_(\w+)_.*', r'\1', method_name)
                test_patterns[pattern].append((method_name, test_file))

        # 同じパターンが多数ある場合
        for pattern, tests in test_patterns.items():
            if len(tests) > 10 and pattern not in ['config', 'parse', 'render']:
                warnings.append(
                    f"⚠️ テストパターン重複の可能性: '{pattern}' "
                    f"({len(tests)}個) - 統合・パラメータ化を検討"
                )

        return warnings

    def generate_quality_report(self, strict: bool = False) -> TestQualityReport:
        """総合品質レポート生成"""
        all_violations = []
        all_warnings = []
        recommendations = []

        # 各種チェック実行
        count_violations, count_warnings, category_counts, total_tests = self.check_test_count_limits()
        naming_violations, naming_warnings = self.check_naming_conventions()
        density_warnings = self.check_test_density()
        duplicate_warnings = self.check_duplicate_patterns()

        all_violations.extend(count_violations)
        all_violations.extend(naming_violations)

        all_warnings.extend(count_warnings)
        all_warnings.extend(naming_warnings)
        all_warnings.extend(density_warnings)
        all_warnings.extend(duplicate_warnings)

        # 推奨事項生成
        if total_tests < self.LIMITS['total_tests'] * 0.7:
            recommendations.append(
                f"💡 テストカバレッジ向上の余地: 現在{total_tests}個、上限{self.LIMITS['total_tests']}個"
            )

        if len(all_warnings) > 10:
            recommendations.append(
                "💡 警告数が多いため、段階的な改善を推奨"
            )

        return TestQualityReport(
            total_tests=total_tests,
            category_counts=dict(category_counts),
            violations=all_violations,
            warnings=all_warnings if not strict else all_warnings[:5],
            recommendations=recommendations
        )

    def print_report(self, report: TestQualityReport, verbose: bool = False):
        """品質レポートの出力"""
        print("📊 テスト品質レポート")
        print("=" * 50)
        print()

        # 総合状況
        print("📈 テスト数サマリー")
        print("-" * 25)
        print(f"総テスト数: {report.total_tests}/{self.LIMITS['total_tests']} "
              f"({report.total_tests/self.LIMITS['total_tests']*100:.1f}%)")

        # カテゴリ別内訳
        print("\n📋 カテゴリ別内訳")
        print("-" * 25)
        for category, count in sorted(report.category_counts.items(),
                                     key=lambda x: x[1], reverse=True):
            limit = self.LIMITS['categories'].get(category, 'N/A')
            if isinstance(limit, int):
                percentage = f"{count/limit*100:.1f}%"
                status = "✅" if count <= limit else "❌"
                print(f"{status} {category}: {count}/{limit} ({percentage})")
            else:
                print(f"📊 {category}: {count}")

        # 品質評価
        print(f"\n🔍 品質評価")
        print("-" * 25)

        if not report.violations and not report.warnings:
            print("✅ 全品質基準をクリア - 優秀な状態です")
        elif not report.violations:
            print("⚠️ 基本品質基準クリア - 一部改善の余地あり")
        else:
            print("❌ 品質基準違反あり - 改善が必要です")

        # 違反事項
        if report.violations:
            print(f"\n🚨 品質基準違反 ({len(report.violations)}件)")
            print("-" * 25)
            for violation in report.violations:
                print(violation)

        # 警告事項
        if report.warnings:
            print(f"\n⚠️ 改善推奨事項 ({len(report.warnings)}件)")
            print("-" * 25)
            for warning in report.warnings:
                print(warning)

        # 推奨事項
        if report.recommendations:
            print(f"\n💡 推奨事項 ({len(report.recommendations)}件)")
            print("-" * 25)
            for recommendation in report.recommendations:
                print(recommendation)

        print()
        print("🎯 詳細ガイドライン: docs/TESTING_GUIDELINES.md")
        print("🔧 継続改善: 月次品質レビューで基準見直し")


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='テスト品質自動チェッカー')
    parser.add_argument('--category', help='特定カテゴリのみチェック')
    parser.add_argument('--strict', action='store_true', help='厳格モード（警告を制限）')
    parser.add_argument('--verbose', action='store_true', help='詳細出力')
    parser.add_argument('--fail-on-violation', action='store_true',
                       help='違反時に非零終了コードを返す')

    args = parser.parse_args()

    # testsディレクトリの存在確認
    if not os.path.exists('tests'):
        print("❌ testsディレクトリが見つかりません")
        return 1

    # チェッカー実行
    checker = TestQualityChecker()
    report = checker.generate_quality_report(strict=args.strict)
    checker.print_report(report, verbose=args.verbose)

    # 終了コード決定
    if args.fail_on_violation and report.violations:
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
