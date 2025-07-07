"""
エラーフォーマッター

エラー表示の責任を担当
Issue #319対応 - error_reporting.py から分離
"""

from typing import List

from .error_types import DetailedError, ErrorSeverity


class ErrorFormatter:
    """エラー表示フォーマッター

    責任: エラー情報の人間読みやすい形式への変換
    """

    # 重要度アイコンマッピング
    SEVERITY_ICONS: dict[ErrorSeverity, str] = {
        ErrorSeverity.INFO: "ℹ️",
        ErrorSeverity.WARNING: "⚠️",
        ErrorSeverity.ERROR: "❌",
        ErrorSeverity.CRITICAL: "🚨",
    }

    @classmethod
    def format_error(cls, error: DetailedError) -> str:
        """エラーを人間が読みやすい形式で表示"""

        # メインメッセージ
        icon = cls.SEVERITY_ICONS.get(error.severity, "❓")
        lines = [f"{icon} {error.title}", f"   {error.message}"]

        # ファイル位置情報
        if error.file_path and error.location:
            lines.append(f"   📍 ファイル: {error.file_path.name} ({error.location})")

        # 問題箇所の表示
        if error.highlighted_line:
            lines.extend(
                [
                    "",
                    "   🔍 問題箇所:",
                    f"   ┌─ {error.location if error.location else '不明'}",
                    f"   │ {error.highlighted_line.strip()}",
                    "   └─",
                ]
            )

        # コンテキスト行の表示
        if error.context_lines:
            lines.extend(["", "   📝 周辺コード:"])
            for i, context_line in enumerate(error.context_lines):
                prefix = "   → " if i == len(error.context_lines) // 2 else "     "
                lines.append(f"{prefix}{context_line.rstrip()}")

        # 修正提案
        if error.fix_suggestions:
            lines.extend(["", "   💡 修正方法:"])
            for i, suggestion in enumerate(error.fix_suggestions, 1):
                confidence_emoji = cls._get_confidence_emoji(suggestion.confidence)
                lines.append(f"   {confidence_emoji} {i}. {suggestion}")

        # ヘルプリンク
        if error.help_url:
            lines.extend(["", f"   📚 詳細: {error.help_url}"])

        return "\n".join(lines)

    @classmethod
    def format_summary(cls, errors: list[DetailedError]) -> str:
        """エラーサマリーを表示"""
        if not errors:
            return "✅ エラーはありません。"

        # 重要度別集計
        by_severity: dict[ErrorSeverity, list[DetailedError]] = {}
        for error in errors:
            severity = error.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)

        lines = ["📊 エラーサマリー", "=" * 30]

        # 重要度別表示
        for severity in [
            ErrorSeverity.CRITICAL,
            ErrorSeverity.ERROR,
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO,
        ]:
            if severity in by_severity:
                count = len(by_severity[severity])
                icon = cls.SEVERITY_ICONS.get(severity, "❓")
                lines.append(f"{icon} {severity.value.upper()}: {count}件")

        return "\n".join(lines)

    @staticmethod
    def _get_confidence_emoji(confidence: float) -> str:
        """信頼度に応じた絵文字を取得"""
        if confidence >= 0.9:
            return "🎯"
        elif confidence >= 0.7:
            return "💭"
        else:
            return "🤔"
