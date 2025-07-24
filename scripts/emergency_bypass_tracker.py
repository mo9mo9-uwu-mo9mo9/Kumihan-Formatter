#!/usr/bin/env python3
"""緊急回避時の自動Issue作成システム."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class EmergencyBypassTracker:
    """緊急回避の自動追跡・Issue作成."""

    # 悪用防止設定
    MAX_BYPASSES_PER_DAY = 3  # 24時間内の最大回避回数
    MIN_REASON_LENGTH = 10  # 理由の最小文字数
    FORBIDDEN_REASONS = [
        "急いでいる",
        "時間がない",
        "後で直す",
        "一時的",
        "temp",
        "temporary",
        "later",
        "fix later",
    ]

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)
        self.bypass_log = Path(".emergency_bypass.json")

    def track_emergency_bypass(self, reason: Optional[str] = None) -> None:
        """緊急回避の追跡とIssue作成.

        Args:
            reason: 緊急回避の理由

        Raises:
            ValueError: 悪用防止チェックに失敗した場合
        """
        self.logger.warning("緊急回避が検出されました")

        # 悪用防止チェック
        self._validate_bypass_request(reason)

        # 回避情報を記録
        bypass_info = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason or "緊急対応",
            "commit": self._get_current_commit(),
            "branch": self._get_current_branch(),
            "user": self._get_current_user(),
        }

        # ログ記録
        self._save_bypass_log(bypass_info)

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

    def _get_current_user(self) -> str:
        """現在のユーザー名取得."""
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _validate_bypass_request(self, reason: Optional[str]) -> None:
        """緊急回避リクエストの妃当性検証.

        Args:
            reason: 緊急回避の理由

        Raises:
            ValueError: 検証に失敗した場合
        """
        # 1. 理由の必須化
        if not reason or reason.strip() == "":
            raise ValueError(
                "🚫 緊急回避には理由の入力が必須です\n"
                "使用方法: python scripts/emergency_bypass_tracker.py '具体的な理由'"
            )

        reason_clean = reason.strip().lower()

        # 2. 理由の最小文字数チェック
        if len(reason_clean) < self.MIN_REASON_LENGTH:
            raise ValueError(
                f"🚫 理由が短すぎます (最小{self.MIN_REASON_LENGTH}文字)\n"
                f"現在: {len(reason_clean)}文字 - '{reason}'"
            )

        # 3. 禁止された理由のチェック
        for forbidden in self.FORBIDDEN_REASONS:
            if forbidden in reason_clean:
                raise ValueError(
                    f"🚫 不適切な理由です: '{forbidden}'\n"
                    "具体的で技術的な理由を記載してください"
                )

        # 4. 頻度制限チェック
        recent_bypasses = self._get_recent_bypasses()
        if len(recent_bypasses) >= self.MAX_BYPASSES_PER_DAY:
            last_bypass = recent_bypasses[-1]
            raise ValueError(
                f"🚫 24時間内の緊急回避上限を超えました\n"
                f"上限: {self.MAX_BYPASSES_PER_DAY}回/日\n"
                f"最終回避: {last_bypass['timestamp']} - {last_bypass['reason']}"
            )

    def _get_recent_bypasses(self) -> List[Dict[str, str]]:
        """直近24時間の緊急回避履歴取得.

        Returns:
            直近24時間の回避リスト
        """
        if not self.bypass_log.exists():
            return []

        try:
            with open(self.bypass_log, "r", encoding="utf-8") as f:
                all_bypasses = json.load(f)

            # 24時間以内のレコードをフィルタリング
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_bypasses = []

            for bypass in all_bypasses:
                bypass_time = datetime.fromisoformat(bypass["timestamp"])
                if bypass_time > cutoff_time:
                    recent_bypasses.append(bypass)

            return recent_bypasses

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"回避ログ読み込みエラー: {e}")
            return []

    def _save_bypass_log(self, bypass_info: Dict[str, str]) -> None:
        """緊急回避ログ保存.

        Args:
            bypass_info: 回避情報
        """
        try:
            # 既存ログ読み込み
            all_bypasses = []
            if self.bypass_log.exists():
                with open(self.bypass_log, "r", encoding="utf-8") as f:
                    all_bypasses = json.load(f)

            # 新しいレコード追加
            all_bypasses.append(bypass_info)

            # 最新100件保持
            if len(all_bypasses) > 100:
                all_bypasses = all_bypasses[-100:]

            # ファイル保存
            with open(self.bypass_log, "w", encoding="utf-8") as f:
                json.dump(all_bypasses, f, ensure_ascii=False, indent=2)

            self.logger.info(f"回避ログ保存完了: {self.bypass_log}")

        except Exception as e:
            self.logger.error(f"回避ログ保存失敗: {e}")

    def _create_github_issue(self, bypass_info: dict) -> None:
        """GitHub Issue作成."""
        issue_title = f"🚨 緊急回避の技術的負債解消: {bypass_info['commit']}"
        deadline = datetime.now() + timedelta(days=7)

        # 緊急度評価
        recent_count = len(self._get_recent_bypasses())
        urgency_level = "HIGH" if recent_count >= 2 else "MEDIUM"

        issue_body = f"""
## 🚨 緊急回避の詳細
- **日時**: {bypass_info['timestamp']}
- **理由**: {bypass_info['reason']}
- **ユーザー**: {bypass_info['user']}
- **コミット**: {bypass_info['commit']}
- **ブランチ**: {bypass_info['branch']}
- **解消期限**: {deadline.strftime('%Y-%m-%d')}
- **緊急度**: {urgency_level} ({recent_count + 1}/3 回 直近24h)

## 📋 必須タスク
- [ ] 品質ゲートの適用
- [ ] pre-commitフックの修正
- [ ] テストカバレッジの確保
- [ ] ドキュメント更新
- [ ] 回避理由の根本解決

## ⚠️  警告
- この課題が**7日以内**に解決されない場合、新機能開発をブロックします
- 24時間内の緊急回避上限: **3回**
- 現在の使用回数: **{recent_count + 1}回**

---
*このIssueは悪用防止機能付き緊急回避システムにより自動作成されました*
"""

        # GitHub認証の事前検証
        self._validate_github_auth()

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
            raise RuntimeError(
                f"❌ GitHub Issue作成に失敗しました: {e}\n"
                "認証状態を確認してください: gh auth status"
            )

    def _validate_github_auth(self) -> None:
        """簡易GitHub認証確認.

        Raises:
            RuntimeError: 認証に失敗した場合
        """
        try:
            # 認証状態確認
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, check=True
            )
            if "Logged in to github.com" not in result.stderr:
                raise RuntimeError("認証されていません")

        except FileNotFoundError:
            raise RuntimeError(
                "❌ GitHub CLI (gh) がインストールされていません\n"
                "インストール: https://cli.github.com/"
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "❌ GitHub CLIにログインしていません\n" "ログイン: gh auth login"
            )


def main() -> None:
    """メインエントリーポイント."""
    if len(sys.argv) < 2:
        print("🚫 エラー: 緊急回避の理由が必要です")
        print("使用方法: python scripts/emergency_bypass_tracker.py '具体的な理由'")
        print("\n例:")
        print(
            "  python scripts/emergency_bypass_tracker.py 'CI/CD障害による緊急リリース対応'"
        )
        print(
            "  python scripts/emergency_bypass_tracker.py '本番サーバーでのセキュリティ修正'"
        )
        sys.exit(1)

    tracker = EmergencyBypassTracker()
    reason = sys.argv[1]

    try:
        tracker.track_emergency_bypass(reason)
        print("✅ 緊急回避Issueが作成されました")
    except ValueError as e:
        print(f"❌ 緊急回避が拒否されました:\n{e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ GitHub操作エラー:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
