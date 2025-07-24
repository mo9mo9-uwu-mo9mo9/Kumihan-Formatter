#!/usr/bin/env python3
"""緊急回避機能付きpre-commit強制実行システム."""

import os
import subprocess
import sys
from pathlib import Path

from kumihan_formatter.core.utilities.logger import get_logger


class PreCommitEnforcer:
    """緊急回避機能付きpre-commit強制実行."""

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)
        self.emergency_mode = (
            os.environ.get("KUMIHAN_EMERGENCY_SKIP", "").lower() == "true"
        )

    def run_pre_commit(self) -> int:
        """pre-commit実行.

        Returns:
            終了コード
        """
        if self.emergency_mode:
            self.logger.warning("🚨 緊急回避モードが有効です")
            self._track_emergency_bypass()
            return 0

        # 通常のpre-commit実行
        self.logger.info("pre-commitフック実行中...")
        result = subprocess.run(["pre-commit", "run", "--all-files"])

        if result.returncode != 0:
            self.logger.error("🚫 pre-commitチェック失敗")
            self._show_bypass_instructions()

        return result.returncode

    def _track_emergency_bypass(self) -> None:
        """緊急回避の追跡."""
        try:
            subprocess.run(
                [
                    sys.executable,
                    "scripts/emergency_bypass_tracker.py",
                    "pre-commit緊急回避",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.error("緊急回避Issue作成失敗")

    def _show_bypass_instructions(self) -> None:
        """緊急回避手順の表示."""
        print("\n" + "=" * 60)
        print("🚨 pre-commitチェック失敗")
        print("=" * 60)
        print("\n緊急回避が必要な場合:")
        print("  KUMIHAN_EMERGENCY_SKIP=true git commit -m 'メッセージ'")
        print("\n⚠️  緊急回避を使用すると:")
        print("  - 自動でGitHub Issueが作成されます")
        print("  - 7日以内に解消が必要です")
        print("  - 未解決の場合、新機能開発がブロックされます")
        print("=" * 60)


def main() -> None:
    """メインエントリーポイント."""
    enforcer = PreCommitEnforcer()
    sys.exit(enforcer.run_pre_commit())


if __name__ == "__main__":
    main()
