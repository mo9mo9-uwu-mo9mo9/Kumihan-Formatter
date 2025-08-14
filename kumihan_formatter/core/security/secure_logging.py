"""
セキュリティ強化: セキュアログ出力
機密情報の漏洩を防ぐログ処理
"""

import logging
import re


class SecureLogFormatter(logging.Formatter):
    """機密情報をマスクするログフォーマッター"""

    # マスクするパターン
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'password="***"'),
        (r'api_key["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'api_key="***"'),
        (r'secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'secret="***"'),
        (r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'token="***"'),
        (r"Authorization:\s*Bearer\s+([^\s]+)", r"Authorization: Bearer ***"),
        (
            r"([0-9]{4})-?([0-9]{4})-?([0-9]{4})-?([0-9]{4})",
            r"****-****-****-****",
        ),  # カード番号
    ]

    def format(self, record: logging.LogRecord) -> str:
        """ログメッセージの機密情報をマスク"""
        # 基本フォーマット適用
        formatted = super().format(record)

        # 機密情報のマスク処理
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)

        return formatted


class SecureLogFilter(logging.Filter):
    """機密情報を含むログレコードをフィルタリング"""

    SENSITIVE_KEYWORDS = [
        "password",
        "secret",
        "key",
        "token",
        "credential",
        "authorization",
        "bearer",
        "api_key",
        "private_key",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """ログレコードの検査"""
        message = str(record.getMessage()).lower()

        # 機密キーワードを含む場合は詳細レベルを下げる
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in message:
                if record.levelno < logging.WARNING:
                    return False  # INFO/DEBUG レベルの機密情報は出力しない

        return True


def setup_secure_logging() -> logging.Logger:
    """セキュアなロガーの設定"""
    logger = logging.getLogger("kumihan_formatter_secure")

    # ハンドラーが既に設定されている場合はスキップ
    if logger.handlers:
        return logger

    # セキュアフォーマッター
    formatter = SecureLogFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SecureLogFilter())

    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

    return logger
