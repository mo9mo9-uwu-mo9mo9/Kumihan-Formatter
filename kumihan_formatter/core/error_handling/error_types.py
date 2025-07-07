"""
エラー型定義
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ErrorLevel(Enum):
    """エラーレベル定義"""

    INFO = "info"  # 青色表示（情報）
    WARNING = "warning"  # 黄色表示（警告）
    ERROR = "error"  # 赤色表示（エラー）
    CRITICAL = "critical"  # 赤背景表示（致命的）


class ErrorCategory(Enum):
    """エラーカテゴリ定義"""

    FILE_SYSTEM = "file_system"  # ファイル関連
    ENCODING = "encoding"  # エンコーディング関連
    SYNTAX = "syntax"  # 記法関連
    PERMISSION = "permission"  # 権限関連
    SYSTEM = "system"  # システム関連
    NETWORK = "network"  # ネットワーク関連
    RENDERING = "rendering"  # レンダリング関連
    UNKNOWN = "unknown"  # 不明


@dataclass
class ErrorSolution:
    """エラー解決方法"""

    quick_fix: str  # 即座にできる解決方法
    detailed_steps: list[str]  # 詳細な手順
    external_links: list[str] | None = None  # 参考リンク
    alternative_approaches: list[str] | None = None  # 代替手段


@dataclass
class UserFriendlyError:
    """ユーザーフレンドリーエラー情報"""

    error_code: str  # エラーコード（E001など）
    level: ErrorLevel  # エラーレベル
    category: ErrorCategory  # エラーカテゴリ
    user_message: str  # ユーザー向けメッセージ
    solution: ErrorSolution  # 解決方法
    technical_details: str | None = None  # 技術的詳細
    context: dict[str, Any] | None = None  # エラーコンテキスト

    def format_message(self, include_technical: bool = False) -> str:
        """フォーマット済みメッセージを取得"""
        message_parts = [f"[{self.error_code}] {self.user_message}"]

        if include_technical and self.technical_details:
            message_parts.append(f"\n技術的詳細: {self.technical_details}")

        return "\n".join(message_parts)
