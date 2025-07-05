"""Discord Webhook通知モジュール"""
import json
import time
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException


class DiscordNotifier:
    """Discord Webhookへの通知を管理するクラス"""

    def __init__(self, webhook_url: str):
        """
        Args:
            webhook_url: Discord WebhookのURL
        """
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def send_message(
        self,
        content: str,
        embeds: Optional[list] = None,
        username: Optional[str] = "Kumihan Formatter",
        avatar_url: Optional[str] = None,
    ) -> bool:
        """
        Discordにメッセージを送信

        Args:
            content: 送信するメッセージ内容
            embeds: Discord Embed形式のリスト（オプション）
            username: 表示される送信者名（オプション）
            avatar_url: アバター画像のURL（オプション）

        Returns:
            bool: 送信成功時True、失敗時False
        """
        payload: Dict[str, Any] = {"content": content, "username": username}

        if embeds:
            payload["embeds"] = embeds

        if avatar_url:
            payload["avatar_url"] = avatar_url

        return self._send_with_retry(payload)

    def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00FF00,  # デフォルトは緑
        fields: Optional[list] = None,
        footer: Optional[str] = None,
        username: Optional[str] = "Kumihan Formatter",
    ) -> bool:
        """
        Embed形式でメッセージを送信

        Args:
            title: Embedのタイトル
            description: Embedの説明
            color: Embedの色（16進数）
            fields: フィールドのリスト
            footer: フッターテキスト
            username: 表示される送信者名

        Returns:
            bool: 送信成功時True、失敗時False
        """
        embed = {"title": title, "description": description, "color": color}

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = {"text": footer}

        payload = {"username": username, "embeds": [embed]}

        return self._send_with_retry(payload)

    def send_format_complete(
        self,
        file_path: str,
        success: bool,
        message: Optional[str] = None,
        stats: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        フォーマット完了通知を送信

        Args:
            file_path: フォーマットしたファイルパス
            success: 成功/失敗
            message: 追加メッセージ
            stats: 統計情報（処理時間、変更行数など）

        Returns:
            bool: 送信成功時True、失敗時False
        """
        color = 0x00FF00 if success else 0xFF0000  # 成功:緑、失敗:赤
        status = "✅ 成功" if success else "❌ 失敗"

        title = f"フォーマット完了 {status}"
        description = f"ファイル: `{file_path}`"

        if message:
            description += f"\n{message}"

        fields = []
        if stats:
            for key, value in stats.items():
                fields.append({"name": key, "value": str(value), "inline": True})

        return self.send_embed(
            title=title,
            description=description,
            color=color,
            fields=fields if fields else None,
            footer="Kumihan Formatter",
        )

    def _send_with_retry(self, payload: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        リトライ機能付きでWebhookに送信

        Args:
            payload: 送信するペイロード
            max_retries: 最大リトライ回数

        Returns:
            bool: 送信成功時True、失敗時False
        """
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.webhook_url, data=json.dumps(payload), timeout=10
                )

                if response.status_code == 204:
                    return True
                elif response.status_code == 429:  # Rate limit
                    retry_after = response.json().get("retry_after", 1000) / 1000
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Discord Webhook送信エラー: {response.status_code}")
                    print(f"レスポンス: {response.text}")

            except RequestException as e:
                print(f"Discord Webhook送信時の例外: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    continue

        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
