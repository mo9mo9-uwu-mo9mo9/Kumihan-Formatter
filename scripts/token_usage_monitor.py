#!/usr/bin/env python3
"""Token使用量の監視・可視化システム."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


class TokenUsageMonitor:
    """Token使用量の監視・警告."""

    # Token使用量闾値
    WARNING_THRESHOLD = 1500
    ERROR_THRESHOLD = 2000

    def __init__(self) -> None:
        """初期化."""
        self.logger = get_logger(__name__)
        self.usage_log = Path(".token_usage.json")
        self.enable_logging = os.environ.get("KUMIHAN_DEV_LOG", "").lower() == "true"
        self.json_logging = os.environ.get("KUMIHAN_DEV_LOG_JSON", "").lower() == "true"

    def estimate_token_usage(self, files: List[str]) -> int:
        """Token使用量の推定.

        Args:
            files: 変更ファイルリスト

        Returns:
            推定Token数
        """
        total_tokens = 0

        for file_path in files:
            if not Path(file_path).exists():
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 簡易的なToken推定（約4文字 = 1 token）
                tokens = len(content) // 4
                total_tokens += tokens

        return total_tokens

    def analyze_pr_diff(self) -> Dict[str, int]:
        """PR差分のToken使用量分析.

        Returns:
            分析結果
        """
        try:
            # PR差分の取得
            result = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = result.stdout.strip().split("\n")

            # Pythonファイルのみ対象
            py_files = [f for f in changed_files if f.endswith(".py")]

            token_usage = self.estimate_token_usage(py_files)

            return {
                "total_tokens": token_usage,
                "file_count": len(py_files),
                "status": self._get_status(token_usage),
                "timestamp": datetime.now().isoformat(),
            }

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git差分取得失敗: {e}")
            return {"error": str(e)}

    def _get_status(self, tokens: int) -> str:
        """Token数に基づくステータス判定.

        Args:
            tokens: Token数

        Returns:
            ステータス
        """
        if tokens >= self.ERROR_THRESHOLD:
            return "error"
        elif tokens >= self.WARNING_THRESHOLD:
            return "warning"
        return "ok"

    def report_usage(self, analysis: Dict[str, int]) -> None:
        """使用量レポート.

        Args:
            analysis: 分析結果
        """
        if not self.enable_logging:
            return

        if self.json_logging:
            # JSON形式で出力
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            # ヒューマンリーダブル形式
            if "error" in analysis:
                print(f"\n❌ Token使用量分析エラー: {analysis['error']}")
                return

            tokens = analysis["total_tokens"]
            status = analysis["status"]

            print("\n" + "=" * 60)
            print("📊 Token使用量レポート")
            print("=" * 60)
            print(f"\u5408計Token数: {tokens:,}")
            print(f"\u5909更ファイル数: {analysis['file_count']}")

            if status == "error":
                print(
                    f"\n❌ エラー: Token使用量が上限({self.ERROR_THRESHOLD:,})を超えました"
                )
                print("💡 ファイル分割を検討してください")
            elif status == "warning":
                print(
                    f"\n⚠️  警告: Token使用量が警告闾値({self.WARNING_THRESHOLD:,})に近づいています"
                )
            else:
                print("\n✅ Token使用量は適切な範囲内です")

            print("=" * 60)

    def save_history(
        self, analysis: Dict[str, Union[int, str, Dict[str, int]]]
    ) -> None:
        """履歴保存.

        Args:
            analysis: 分析結果
        """
        history = []
        if self.usage_log.exists():
            with open(self.usage_log, "r") as f:
                history = json.load(f)

        history.append(analysis)

        # 最新30件保持
        if len(history) > 30:
            history = history[-30:]

        with open(self.usage_log, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def main() -> None:
    """メインエントリーポイント."""
    monitor = TokenUsageMonitor()
    analysis = monitor.analyze_pr_diff()
    monitor.report_usage(analysis)

    if "total_tokens" in analysis:
        monitor.save_history(analysis)

        # CI/CD用の終了コード
        if analysis["status"] == "error":
            exit(1)


if __name__ == "__main__":
    main()
