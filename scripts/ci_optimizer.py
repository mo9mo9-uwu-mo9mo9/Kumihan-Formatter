#!/usr/bin/env python3
"""
CI実行時間最適化スクリプト - Issue #610対応
並列実行とティア別テストによるCI時間短縮
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class CIOptimizer:
    """CI実行時間最適化クラス"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tier_config = {
            "critical": [
                "tests/unit/test_commands_core.py",
                "tests/unit/test_core_parser_advanced.py",
            ],
            "important": [
                "tests/unit/test_rendering_advanced.py",
                "tests/unit/test_validation_advanced.py",
                "tests/unit/test_file_operations_comprehensive.py",
                "tests/unit/test_file_validators_comprehensive.py",
            ],
            "supportive": [
                "tests/unit/",
                "tests/integration/",
            ],
        }

    def get_cpu_count(self) -> int:
        """CPUコア数を取得（CI環境考慮）"""
        try:
            import psutil

            return max(2, min(psutil.cpu_count(logical=False) or 2, 4))
        except ImportError:
            return min(os.cpu_count() or 2, 4)

    def run_tier_tests(
        self, tier: str, parallel: bool = True, platform_aware: bool = True
    ) -> int:
        """ティア別テスト実行（プラットフォーム対応）"""
        if tier not in self.tier_config:
            print(f"❌ 不正なティア: {tier}")
            return 1

        test_paths = self.tier_config[tier]
        cpu_count = self.get_cpu_count() if parallel else 1

        cmd = [
            "python",
            "-m",
            "pytest",
            "-n",
            str(cpu_count) if parallel else "0",
            "--durations=5",
            "--tb=short",
        ]

        # プラットフォーム考慮のマーカー除外
        if platform_aware:
            import platform

            current_platform = platform.system()
            exclusions = []

            if current_platform == "Windows":
                exclusions.extend(["macos_only", "linux_only", "unix_like"])
            elif current_platform == "Darwin":  # macOS
                exclusions.extend(["windows_only", "linux_only"])
            elif current_platform == "Linux":
                exclusions.extend(["windows_only", "macos_only"])

            # CI環境では追加除外
            if os.getenv("CI", "").lower() == "true":
                exclusions.extend(["gui", "skip_ci"])
                if tier != "supportive":  # supportive以外はslowも除外
                    exclusions.append("slow")

            if exclusions:
                marker_expr = " and ".join([f"not {exc}" for exc in exclusions])
                cmd.extend(["-m", marker_expr])

        # ティア別オプション設定
        if tier == "critical":
            cmd.extend(["--maxfail=3", "--timeout=60"])
        elif tier == "important":
            cmd.extend(["--maxfail=5", "--timeout=120"])
        else:
            cmd.extend(["--maxfail=10"])

        # カバレッジ（Supportiveティアのみ）
        if tier == "supportive":
            cmd.extend(
                [
                    "--cov=kumihan_formatter",
                    "--cov-report=xml",
                    "--cov-report=term-missing",
                ]
            )

        cmd.extend(test_paths)

        platform_info = (
            f" (プラットフォーム: {platform.system()})" if platform_aware else ""
        )
        print(f"🚀 {tier.upper()} Tier テスト実行開始{platform_info}...")
        print(f"並列度: {cpu_count}, コマンド: {' '.join(cmd)}")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def optimize_cache(self) -> None:
        """キャッシュ最適化"""
        cache_dirs = [
            ".pytest_cache",
            "__pycache__",
            ".mypy_cache",
        ]

        for cache_dir in cache_dirs:
            cache_path = self.project_root / cache_dir
            if cache_path.exists():
                print(f"🧹 キャッシュクリア: {cache_dir}")

    def estimate_time(self, tier: str) -> str:
        """実行時間見積もり"""
        estimates = {"critical": "2-4分", "important": "5-8分", "supportive": "10-15分"}
        return estimates.get(tier, "不明")


def main():
    parser = argparse.ArgumentParser(description="CI実行時間最適化")
    parser.add_argument(
        "tier",
        choices=["critical", "important", "supportive", "all"],
        help="実行するテストティア",
    )
    parser.add_argument("--no-parallel", action="store_true", help="並列実行を無効化")
    parser.add_argument(
        "--estimate", action="store_true", help="実行時間見積もりのみ表示"
    )

    args = parser.parse_args()
    optimizer = CIOptimizer()

    if args.estimate:
        print(f"📊 {args.tier}ティア推定実行時間: {optimizer.estimate_time(args.tier)}")
        return 0

    if args.tier == "all":
        for tier in ["critical", "important", "supportive"]:
            print(f"\n{'='*50}")
            result = optimizer.run_tier_tests(tier, not args.no_parallel)
            if result != 0:
                print(f"❌ {tier}ティア失敗")
                return result
        print("\n✅ 全ティア成功")
        return 0
    else:
        return optimizer.run_tier_tests(args.tier, not args.no_parallel)


if __name__ == "__main__":
    sys.exit(main())
