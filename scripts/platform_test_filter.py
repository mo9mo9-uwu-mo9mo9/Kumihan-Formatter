#!/usr/bin/env python3
"""
プラットフォーム別テストフィルタースクリプト - Issue #610対応
CI環境でのプラットフォーム固有テスト実行制御
"""

import os
import platform
import subprocess
import sys
from typing import List


class PlatformTestFilter:
    """プラットフォーム別テストフィルター"""

    def __init__(self):
        self.current_platform = platform.system()
        self.is_ci = os.getenv("CI", "").lower() == "true"

    def get_platform_exclusions(self) -> List[str]:
        """現在のプラットフォームで除外するマーカー"""
        exclusions = []

        if self.current_platform == "Windows":
            exclusions.extend(["macos_only", "linux_only", "unix_like"])
        elif self.current_platform == "Darwin":  # macOS
            exclusions.extend(["windows_only", "linux_only"])
        elif self.current_platform == "Linux":
            exclusions.extend(["windows_only", "macos_only"])

        # CI環境では追加で除外
        if self.is_ci:
            exclusions.extend(["gui", "slow", "skip_ci"])

        return exclusions

    def get_pytest_args(self, additional_args: List[str] = None) -> List[str]:
        """プラットフォーム考慮のpytestコマンド引数生成"""
        args = ["python", "-m", "pytest"]

        # 並列実行
        args.extend(["-n", "auto"])

        # プラットフォーム除外
        exclusions = self.get_platform_exclusions()
        if exclusions:
            marker_expr = " and ".join([f"not {exc}" for exc in exclusions])
            args.extend(["-m", marker_expr])

        # CI環境での最適化
        if self.is_ci:
            args.extend(["--durations=5", "--maxfail=3", "--timeout=120", "--tb=short"])

        # 追加引数
        if additional_args:
            args.extend(additional_args)

        return args

    def run_filtered_tests(self, test_paths: List[str] = None) -> int:
        """フィルタリングされたテスト実行"""
        args = self.get_pytest_args()

        if test_paths:
            args.extend(test_paths)

        print(f"🧪 プラットフォーム: {self.current_platform}")
        print(f"🔧 除外マーカー: {', '.join(self.get_platform_exclusions())}")
        print(f"🚀 実行コマンド: {' '.join(args)}")

        return subprocess.run(args).returncode


def main():
    import argparse

    parser = argparse.ArgumentParser(description="プラットフォーム別テスト実行")
    parser.add_argument("test_paths", nargs="*", help="テスト対象パス")
    parser.add_argument(
        "--coverage", action="store_true", help="カバレッジ測定を有効化"
    )

    args = parser.parse_args()

    filter_runner = PlatformTestFilter()

    # カバレッジオプション
    additional_args = []
    if args.coverage:
        additional_args.extend(
            ["--cov=kumihan_formatter", "--cov-report=xml", "--cov-report=term-missing"]
        )

    pytest_args = filter_runner.get_pytest_args(additional_args)

    if args.test_paths:
        pytest_args.extend(args.test_paths)

    print(f"実行コマンド: {' '.join(pytest_args)}")
    return subprocess.run(pytest_args).returncode


if __name__ == "__main__":
    sys.exit(main())
