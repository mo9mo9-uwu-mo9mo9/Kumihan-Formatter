#!/usr/bin/env python3
"""緊急回避時の自動Issue作成システム."""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from kumihan_formatter.core.utilities.logger import get_logger


class EmergencyBypassTracker:
    """緊急回避の自動追跡・Issue作成."""

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)
        self.bypass_log = Path(".emergency_bypass.log")

    def track_emergency_bypass(self, reason: Optional[str] = None) -> None:
        """緊急回避の追跡とIssue作成.

        Args:
            reason: 緊急回避の理由
        """
        self.logger.warning("緊急回避が検出されました")

        # 回避情報を記録
        bypass_info = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason or "緊急対応",
            "commit": self._get_current_commit(),
            "branch": self._get_current_branch(),
        }

        # Issue作成
        self._create_github_issue(bypass_info)

    def _get_current_commit(self) -> str:
        """現在のコミットハッシュ取得."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()[:8]
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_current_branch(self) -> str:
        """現在のブランチ名取得."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _create_github_issue(self, bypass_info: dict) -> None:
        """GitHub Issue作成."""
        issue_title = f"🚨 緊急回避の技術的負債解消: {bypass_info['commit']}"
        deadline = datetime.now() + timedelta(days=7)

        issue_body = f"""
## 緊急回避の詳細
- 日時: {bypass_info['timestamp']}
- 理由: {bypass_info['reason']}
- コミット: {bypass_info['commit']}
- ブランチ: {bypass_info['branch']}
- 解消期限: {deadline.strftime('%Y-%m-%d')}

## 必須タスク
- [ ] 品質ゲートの適用
- [ ] pre-commitフックの修正
- [ ] テストカバレッジの確保
- [ ] ドキュメント更新

**⚠️ この課題が7日以内に解決されない場合、新機能開発をブロックします**

---
*このIssueは緊急回避検出により自動作成されました*
"""

        try:
            # GitHub CLIでIssue作成
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    issue_title,
                    "--body",
                    issue_body,
                    "--label",
                    "緊急,品質改善",
                ],
                check=True,
            )
            self.logger.info("緊急回避Issue作成完了")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Issue作成失敗: {e}")


def main() -> None:
    """メインエントリーポイント."""
    tracker = EmergencyBypassTracker()
    reason = sys.argv[1] if len(sys.argv) > 1 else None
    tracker.track_emergency_bypass(reason)


if __name__ == "__main__":
    main()
