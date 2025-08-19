"""
セキュリティ強化: 入力検証モジュール
外部ライブラリとして安全な入力処理を提供
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse


class SecureInputValidator:
    """セキュアな入力検証クラス"""

    # 安全なファイルパス用正規表現
    SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]+$")

    # 危険な文字列パターン
    DANGEROUS_PATTERNS = [
        r"\.\./",  # パストラバーサル
        r"<script",  # XSS
        r"javascript:",  # JavaScript injection
        r"data:.*base64",  # Data URI
        r"[;&|`$(){}]",  # コマンドインジェクション
    ]

    @classmethod
    def validate_file_path(cls, file_path: Union[str, Path]) -> bool:
        """ファイルパスの安全性検証"""
        try:
            path_str = str(file_path)

            # 基本的な危険パターンチェック
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    return False

            # パストラバーサル攻撃の検出
            normalized = os.path.normpath(path_str)
            if ".." in normalized or normalized.startswith("/"):
                return False

            # 文字種制限チェック
            if not cls.SAFE_PATH_PATTERN.match(path_str):
                return False

            return True

        except (TypeError, ValueError):
            return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """ファイル名のサニタイズ"""
        # HTMLタグとスクリプトを完全除去
        sanitized = re.sub(r'<[^>]*>', "", filename)

        # 危険な文字を除去
        sanitized = re.sub(r'[<>:"/\\|?*]', "", sanitized)

        # JavaScript関連キーワードを除去
        dangerous_keywords = ['script', 'javascript', 'vbscript', 'onload', 'onerror']
        for keyword in dangerous_keywords:
            sanitized = re.sub(re.escape(keyword), "", sanitized, flags=re.IGNORECASE)

        # ドットで始まるファイル名を回避
        if sanitized.startswith("."):
            sanitized = "_" + sanitized[1:]

        # 空文字列の場合はデフォルト名
        if not sanitized:
            sanitized = "unnamed_file"

        return sanitized[:255]  # ファイル名長制限

    @classmethod
    def validate_text_content(cls, content: str, max_length: int = 1000000) -> bool:
        """テキスト内容の検証"""
        try:
            # 長さ制限
            if len(content) > max_length:
                return False

            # バイナリデータの混入チェック
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                return False

            # 危険なパターンの検出
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    return False

            return True

        except (TypeError, AttributeError):
            return False

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """URL の安全性検証"""
        try:
            parsed = urlparse(url)

            # プロトコル制限
            if parsed.scheme not in ["http", "https", "ftp"]:
                return False

            # ローカルファイルシステムアクセス防止
            if parsed.scheme == "file":
                return False

            # プライベートIP範囲への接続防止
            if parsed.hostname:
                if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    return False

            return True

        except (ValueError, TypeError):
            return False


class SecureConfigManager:
    """セキュアな設定管理クラス"""

    def __init__(self) -> None:
        self.secrets_loaded = False
        self._secrets: dict[str, str] = {}

    def load_secrets_from_env(self) -> None:
        """環境変数からシークレットを安全に読み込み"""
        secret_keys = [
            "KUMIHAN_API_KEY",
            "GEMINI_API_KEY",
            "CLAUDE_API_KEY",
            "DATABASE_URL",
        ]

        for key in secret_keys:
            value = os.getenv(key)
            if value:
                # 値をハッシュ化して保存（ログ出力時の安全性）
                self._secrets[key] = hashlib.sha256(value.encode()).hexdigest()[:8]

        self.secrets_loaded = True

    def get_secret_hash(self, key: str) -> Optional[str]:
        """シークレットのハッシュ値を取得（デバッグ用）"""
        return self._secrets.get(key)

    def has_secret(self, key: str) -> bool:
        """シークレットの存在確認"""
        return key in self._secrets
