#!/usr/bin/env python3
"""GitHub認証の事前検証システム."""

import json
import subprocess
import sys
from typing import Dict, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class GitHubAuthValidator:
    """GitHub CLI認証の検証."""

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)

    def validate_github_auth(self) -> Dict[str, str]:
        """GitHub認証状態の検証.

        Returns:
            認証情報

        Raises:
            RuntimeError: 認証に失敗した場合
        """
        self.logger.info("GitHub認証状態を検証中...")

        # 1. GitHub CLIの存在確認
        if not self._check_gh_cli_installed():
            raise RuntimeError(
                "❌ GitHub CLI (gh) がインストールされていません\n"
                "インストール方法: https://cli.github.com/manual/installation"
            )

        # 2. 認証状態の確認
        auth_info = self._check_auth_status()
        if not auth_info["authenticated"]:
            raise RuntimeError(
                "❌ GitHub CLIにログインしていません\n" "認証方法: gh auth login"
            )

        # 3. 必要な権限の確認
        self._validate_permissions(auth_info)

        self.logger.info("✅ GitHub認証が正常に確認されました")
        return auth_info

    def _check_gh_cli_installed(self) -> bool:
        """GitHub CLIのインストール確認.

        Returns:
            インストール済みかどうか
        """
        try:
            result = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, check=True
            )
            version = result.stdout.strip().split("\n")[0]
            self.logger.info(f"GitHub CLI検出: {version}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_auth_status(self) -> Dict[str, str]:
        """認証状態の詳細確認.

        Returns:
            認証情報辞書
        """
        try:
            # gh auth status --show-token を使用して詳細取得
            result = subprocess.run(
                ["gh", "auth", "status", "--hostname", "github.com"],
                capture_output=True,
                text=True,
                check=True,
            )

            # 出力を解析
            output = result.stderr  # gh auth statusはstderrに出力
            lines = output.strip().split("\n")

            auth_info = {
                "authenticated": "Logged in to github.com" in output,
                "user": self._extract_username(lines),
                "hostname": "github.com",
                "scopes": self._extract_scopes(lines),
            }

            return auth_info

        except subprocess.CalledProcessError as e:
            self.logger.error(f"認証状態確認エラー: {e}")
            return {
                "authenticated": False,
                "user": "unknown",
                "hostname": "github.com",
                "scopes": [],
                "error": str(e),
            }

    def _extract_username(self, status_lines: list[str]) -> str:
        """ステータス出力からユーザー名を抽出.

        Args:
            status_lines: gh auth statusの出力行

        Returns:
            ユーザー名
        """
        for line in status_lines:
            if "account" in line.lower() or "user" in line.lower():
                # "✓ Logged in to github.com account username (keyring)"
                parts = line.split()
                for i, part in enumerate(parts):
                    if "account" in part and i + 1 < len(parts):
                        return parts[i + 1]
        return "unknown"

    def _extract_scopes(self, status_lines: list[str]) -> list[str]:
        """ステータス出力からスコープを抽出.

        Args:
            status_lines: gh auth statusの出力行

        Returns:
            スコープリスト
        """
        scopes = []
        for line in status_lines:
            if "scopes:" in line.lower():
                # "- Token scopes: admin:public_key, gist, read:org, repo"
                scope_part = line.split("scopes:", 1)[-1].strip()
                scopes = [s.strip() for s in scope_part.split(",")]
                break
        return scopes

    def _validate_permissions(self, auth_info: Dict[str, str]) -> None:
        """必要な権限の確認.

        Args:
            auth_info: 認証情報

        Raises:
            RuntimeError: 権限が不足している場合
        """
        required_scopes = ["repo", "write:repo_hook"]
        user_scopes = auth_info.get("scopes", [])

        # repoスコープがあれば基本的にIssue作成は可能
        has_repo_access = any(
            scope in ["repo", "public_repo"] or "repo" in scope for scope in user_scopes
        )

        if not has_repo_access:
            raise RuntimeError(
                "❌ GitHub CLIの権限が不足しています\n"
                f"現在のスコープ: {', '.join(user_scopes)}\n"
                "必要な権限: repo (Issue作成のため)\n"
                "再認証: gh auth refresh -s repo"
            )

        # リポジトリへのアクセステスト
        try:
            subprocess.run(
                ["gh", "repo", "view", "--json", "name"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "❌ 現在のリポジトリへのアクセス権限がありません\n"
                "リポジトリの権限を確認してください"
            )


def main() -> None:
    """メインエントリーポイント."""
    validator = GitHubAuthValidator()

    try:
        auth_info = validator.validate_github_auth()

        print("🔐 GitHub認証情報:")
        print(f"  ✅ ユーザー: {auth_info['user']}")
        print(f"  ✅ ホスト: {auth_info['hostname']}")
        print(f"  ✅ スコープ: {', '.join(auth_info['scopes'])}")
        print("\n🎉 GitHub認証が正常に確認されました！")

    except RuntimeError as e:
        print(f"❌ GitHub認証エラー:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
