"""Error analysis functionality for structured logging

Single Responsibility Principle適用: エラー分析機能の分離
Issue #476 Phase5対応 - structured_logger.py分割
"""

from __future__ import annotations

import re
import traceback
from typing import Any, Optional

from .structured_logger_base import StructuredLogger


class ErrorAnalyzer:
    """Analyzes errors and provides contextual suggestions

    Helps developers understand errors better by:
    - Categorizing error types
    - Providing fix suggestions
    - Adding useful context
    """

    ERROR_PATTERNS: dict[str, dict[str, Any]] = {
        # ファイル関連エラー
        r"FileNotFoundError|No such file or directory": {
            "category": "file_error",
            "suggestions": [
                "ファイルパスが正しいか確認してください",
                "ファイルが存在することを確認してください",
                "相対パスではなく絶対パスを使用することを検討してください",
            ],
        },
        r"PermissionError|Permission denied": {
            "category": "permission_error",
            "suggestions": [
                "ファイルの読み取り/書き込み権限を確認してください",
                "プログラムを管理者権限で実行する必要があるかもしれません",
                "ファイルが他のプロセスで使用されていないか確認してください",
            ],
        },
        # エンコーディングエラー
        r"UnicodeDecodeError|UnicodeEncodeError": {
            "category": "encoding_error",
            "suggestions": [
                "ファイルのエンコーディングを確認してください（UTF-8推奨）",
                "encoding='utf-8'を明示的に指定してください",
                "errors='replace'またはerrors='ignore'の使用を検討してください",
            ],
        },
        # 構文エラー
        r"SyntaxError|IndentationError": {
            "category": "syntax_error",
            "suggestions": [
                "インデントが正しいか確認してください（スペース4つ推奨）",
                "括弧やクォートが正しく閉じられているか確認してください",
                "Pythonのバージョンに対応した構文を使用しているか確認してください",
            ],
        },
        # インポートエラー
        r"ImportError|ModuleNotFoundError": {
            "category": "import_error",
            "suggestions": [
                "必要なパッケージがインストールされているか確認してください",
                "仮想環境が正しくアクティベートされているか確認してください",
                "PYTHONPATHが正しく設定されているか確認してください",
            ],
        },
        # メモリエラー
        r"MemoryError|out of memory": {
            "category": "memory_error",
            "suggestions": [
                "処理するデータサイズを削減してください",
                "バッチ処理やストリーミング処理を検討してください",
                "不要なオブジェクトを削除してメモリを解放してください",
            ],
        },
    }

    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def analyze_error(
        self, error: Exception, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Analyze an error and return structured information

        Args:
            error: The exception to analyze
            context: Additional context about the error

        Returns:
            Dict containing error analysis results
        """
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()

        # カテゴリーと提案を取得
        category = self._categorize_error(error_message)
        suggestions: list[str] = []

        for pattern, info in self.ERROR_PATTERNS.items():
            if re.search(pattern, f"{error_type}: {error_message}", re.IGNORECASE):
                category = info["category"]
                suggestions.extend(info["suggestions"])
                break

        if not suggestions:
            suggestions = self._generate_generic_suggestions(error_type)

        analysis_result: dict[str, Any] = {
            "error_type": error_type,
            "error_message": error_message,
            "category": category,
            "suggestions": suggestions,
            "traceback": error_traceback.split("\n"),
            "timestamp": self.logger._get_timestamp(),
        }

        if context:
            analysis_result["context"] = context

        # トレースバックから問題の行を抽出
        tb_lines = error_traceback.split("\n")
        for i, line in enumerate(tb_lines):
            if "File" in line and i + 1 < len(tb_lines):
                file_info = line.strip()
                code_line = tb_lines[i + 1].strip() if tb_lines[i + 1].strip() else None
                if code_line:
                    analysis_result["error_location"] = {
                        "file": file_info,
                        "code": code_line,
                    }
                break

        return analysis_result

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        error_lower = error_message.lower()
        if any(word in error_lower for word in ["file", "path", "directory"]):
            return "file_error"
        elif any(word in error_lower for word in ["permission", "access", "denied"]):
            return "permission_error"
        elif any(word in error_lower for word in ["encode", "decode", "unicode"]):
            return "encoding_error"
        elif any(word in error_lower for word in ["memory", "heap", "stack"]):
            return "memory_error"
        return "general_error"

    def _generate_generic_suggestions(self, error_type: str) -> list[str]:
        """Generate generic suggestions based on error type"""
        suggestions = [
            f"{error_type}の詳細をドキュメントで確認してください",
            "エラーメッセージの内容を詳しく読んで原因を特定してください",
            "同様のエラーについてStack Overflowで検索してみてください",
        ]

        if "Error" in error_type:
            suggestions.append(
                "try-except文でエラーハンドリングを追加することを検討してください"
            )

        return suggestions

    def log_error_with_analysis(
        self,
        error: Exception,
        message: str = "エラーが発生しました",
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log error with automatic analysis

        Args:
            error: The exception to log
            message: Custom error message
            context: Additional context
            **kwargs: Additional logging parameters
        """
        analysis = self.analyze_error(error, context)

        # 構造化されたコンテキストでログ出力
        log_context = {"error_analysis": analysis}
        if context:
            log_context.update(context)

        self.logger.error(
            f"{message}: {analysis['error_type']} - {analysis['error_message']}",
            **log_context,
            **kwargs,
        )

    def log_warning_with_suggestion(
        self,
        message: str,
        suggestions: list[str],
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log warning with suggestions

        Args:
            message: Warning message
            suggestions: List of suggestions
            context: Additional context
            **kwargs: Additional logging parameters
        """
        log_context = {"suggestions": suggestions}
        if context:
            log_context.update(context)

        self.logger.warning(message, **log_context, **kwargs)
