"""
セキュリティ強化: セキュアエラーハンドリング
詳細なエラー情報の漏洩を防ぐ
"""

import traceback
from typing import Any, Dict


class SecureErrorHandler:
    """セキュアなエラーハンドリングクラス"""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.error_count = 0

    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """エラーの安全な処理"""
        self.error_count += 1

        # 基本的なエラー情報
        error_info = {
            "error_type": type(error).__name__,
            "context": context,
            "error_id": f"ERR_{self.error_count:06d}",
        }

        # デバッグモードの場合のみ詳細情報を含める
        if self.debug_mode:
            error_info.update(
                {"error_message": str(error), "traceback": traceback.format_exc()}
            )
        else:
            # 本番環境では汎用メッセージ
            error_info["user_message"] = self._get_safe_error_message(error)

        return error_info

    def _get_safe_error_message(self, error: Exception) -> str:
        """ユーザー向けの安全なエラーメッセージ"""
        error_type = type(error).__name__

        safe_messages = {
            "FileNotFoundError": "指定されたファイルが見つかりませんでした",
            "PermissionError": "ファイルまたはディレクトリへのアクセス権限がありません",
            "ValueError": "無効な値が指定されました",
            "TypeError": "不正なデータ型です",
            "KeyError": "指定されたキーが見つかりませんでした",
            "ConnectionError": "ネットワーク接続エラーが発生しました",
            "TimeoutError": "処理がタイムアウトしました",
        }

        return safe_messages.get(error_type, "処理中にエラーが発生しました")

    def create_error_response(
        self, error: Exception, context: str = ""
    ) -> Dict[str, Any]:
        """外部API向けエラーレスポンス生成"""
        error_info = self.handle_error(error, context)

        return {
            "success": False,
            "error": {
                "code": error_info["error_id"],
                "message": error_info.get("user_message", "An error occurred"),
                "type": error_info["error_type"],
            },
            "debug_info": error_info if self.debug_mode else None,
        }


# グローバルエラーハンドラー
_global_error_handler = SecureErrorHandler(debug_mode=False)


def set_debug_mode(enabled: bool) -> None:
    """デバッグモードの設定"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = SecureErrorHandler()
    _global_error_handler.debug_mode = enabled


def handle_error_safely(error: Exception, context: str = "") -> Dict[str, Any]:
    """グローバルエラーハンドラーを使用した安全なエラー処理"""
    return _global_error_handler.handle_error(error, context)


def create_api_error_response(error: Exception, context: str = "") -> Dict[str, Any]:
    """API向けエラーレスポンスの生成"""
    return _global_error_handler.create_error_response(error, context)
