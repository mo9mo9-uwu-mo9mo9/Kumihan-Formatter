"""
エラーレポート機能

エラーの収集・集約・出力の責任を担当
Issue #319対応 - error_reporting.py から分離
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .error_formatter import ErrorFormatter
from .error_types import (
    DetailedError,
    ErrorCategory,
    ErrorLocation,
    ErrorSeverity,
    FixSuggestion,
)


class ErrorReport:
    """エラーレポート統合クラス

    責任: エラーの収集・分類・サマリー生成
    """

    def __init__(self, source_file: Path | None = None):
        self.source_file = source_file
        self.errors: list[DetailedError] = []
        self.warnings: list[DetailedError] = []
        self.info: list[DetailedError] = []
        self.generation_time = datetime.now()

    def add_error(self, error: DetailedError) -> None:
        """エラーを追加"""
        if error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.errors.append(error)
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)

    def has_errors(self) -> bool:
        """エラーが存在するかチェック"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """警告が存在するかチェック"""
        return len(self.warnings) > 0

    def get_total_count(self) -> int:
        """総問題数を取得"""
        return len(self.errors) + len(self.warnings) + len(self.info)

    def get_summary(self) -> str:
        """サマリー情報を取得"""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        info_count = len(self.info)

        parts = []
        if error_count > 0:
            parts.append(f"{error_count}個のエラー")
        if warning_count > 0:
            parts.append(f"{warning_count}個の警告")
        if info_count > 0:
            parts.append(f"{info_count}個の情報")

        if not parts:
            return "問題は見つかりませんでした"

        return "、".join(parts) + "が見つかりました"

    def to_console_output(self, show_info: bool = False) -> str:
        """コンソール表示用の文字列を生成"""
        lines = []

        # ヘッダー
        if self.source_file:
            lines.extend(
                [
                    "╭─────────────────────────────────────────╮",
                    f"│  📄 {self.source_file.name} の記法チェック結果        │",
                    "╰─────────────────────────────────────────╯",
                ]
            )
        else:
            lines.extend(
                [
                    "╭─────────────────────────────────────────╮",
                    "│  📋 記法チェック結果                      │",
                    "╰─────────────────────────────────────────╯",
                ]
            )

        # サマリー情報
        error_count = len(self.errors)
        warning_count = len(self.warnings)

        if error_count == 0 and warning_count == 0:
            lines.extend(
                [
                    "",
                    "🎉 素晴らしい！記法エラーは見つかりませんでした！",
                    "✨ あなたのファイルはKumihan記法に完全に準拠しています。",
                ]
            )
        else:
            lines.append("")
            lines.append(f"📊 チェック結果: {self.get_summary()}")

        lines.append(
            f"⏰ チェック実行時刻: {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # エラー表示
        if self.errors:
            lines.extend(["", "=" * 50, "🚨 修正が必要な問題", "=" * 50])
            for i, error in enumerate(self.errors, 1):
                lines.append(f"\n【問題 {i}】")
                lines.append(ErrorFormatter.format_error(error))

        # 警告表示
        if self.warnings:
            lines.extend(["", "=" * 50, "⚠️  改善推奨事項", "=" * 50])
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"\n【改善案 {i}】")
                lines.append(ErrorFormatter.format_error(warning))

        # 情報表示
        if show_info and self.info:
            lines.extend(["", "=" * 50, "ℹ️  参考情報", "=" * 50])
            for i, info in enumerate(self.info, 1):
                lines.append(f"\n【情報 {i}】")
                lines.append(ErrorFormatter.format_error(info))

        # フッター
        if error_count > 0:
            lines.extend(
                [
                    "",
                    "🔧 次のステップ:",
                    "   1. 上記の修正提案を参考にファイルを修正してください",
                    "   2. 修正後、再度チェックを実行してください",
                    "   3. 困った場合は SPEC.md を参照してください",
                ]
            )
        elif warning_count > 0:
            lines.extend(
                [
                    "",
                    "✅ 次のステップ:",
                    "   • 警告事項は修正推奨ですが、必須ではありません",
                    "   • より良い記法のために修正をご検討ください",
                ]
            )

        return "\n".join(lines)

    def to_file_report(self, output_path: Path) -> None:
        """詳細レポートをテキストファイルに出力"""
        lines = []

        # ヘッダー情報
        lines.append("=" * 60)
        lines.append("Kumihan-Formatter エラーレポート")
        lines.append("=" * 60)
        lines.append("")

        # メタデータ
        if self.source_file:
            lines.append(f"📁 対象ファイル: {self.source_file}")
        lines.append(
            f"🕒 実行時刻: {self.generation_time.strftime('%Y年%m月%d日 %H:%M:%S')}"
        )
        lines.append(f"📊 結果概要: {self.get_summary()}")
        lines.append("")

        # 統計情報
        lines.append("📈 統計情報:")
        lines.append(f"   エラー: {len(self.errors)}個")
        lines.append(f"   警告: {len(self.warnings)}個")
        lines.append(f"   情報: {len(self.info)}個")
        lines.append("")

        # エラー詳細
        if self.errors:
            lines.append("🚫 エラー詳細:")
            lines.append("-" * 40)
            for i, error in enumerate(self.errors, 1):
                lines.append(f"[エラー {i}]")
                lines.append(self._format_error_for_file(error))
                lines.append("")

        # 警告詳細
        if self.warnings:
            lines.append("⚠️  警告詳細:")
            lines.append("-" * 40)
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"[警告 {i}]")
                lines.append(self._format_error_for_file(warning))
                lines.append("")

        # 情報詳細
        if self.info:
            lines.append("ℹ️  情報詳細:")
            lines.append("-" * 40)
            for i, info in enumerate(self.info, 1):
                lines.append(f"[情報 {i}]")
                lines.append(self._format_error_for_file(info))
                lines.append("")

        # フッター
        lines.append("=" * 60)
        lines.append(
            "Kumihan記法の詳細: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md"
        )
        lines.append(
            "問題報告: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues"
        )
        lines.append("=" * 60)

        # ファイルに書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _format_error_for_file(self, error: DetailedError) -> str:
        """ファイル出力用のエラーフォーマット"""
        lines = []
        lines.append(f"  ID: {error.error_id}")
        lines.append(f"  重要度: {error.severity.value}")
        lines.append(f"  カテゴリ: {error.category.value}")
        lines.append(f"  タイトル: {error.title}")
        lines.append(f"  メッセージ: {error.message}")

        if error.location:
            lines.append(f"  位置: {error.location}")

        if error.fix_suggestions:
            lines.append("  修正提案:")
            for suggestion in error.fix_suggestions:
                lines.append(f"    - {suggestion.description}")

        return "\n".join(lines)


class ErrorReportBuilder:
    """エラーレポートビルダー

    責任: エラーレポートの段階的構築
    """

    def __init__(self, source_file: Path | None = None):
        self.report = ErrorReport(source_file)

    def add_syntax_error(
        self, line: int, message: str, suggestion: str | None = None
    ) -> "ErrorReportBuilder":
        """構文エラーを追加"""
        error = DetailedError(
            error_id=f"syntax_{line}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title="構文エラー",
            message=message,
            location=ErrorLocation(line=line),
        )

        if suggestion:
            error.fix_suggestions.append(FixSuggestion(description=suggestion))

        self.report.add_error(error)
        return self

    def add_keyword_error(
        self, line: int, keyword: str, suggestion: str | None = None
    ) -> "ErrorReportBuilder":
        """キーワードエラーを追加"""
        error = DetailedError(
            error_id=f"keyword_{line}_{keyword}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.KEYWORD,
            title="無効なキーワード",
            message=f"無効なキーワードが見つかりました: {keyword}",
            location=ErrorLocation(line=line),
        )

        if suggestion:
            error.fix_suggestions.append(FixSuggestion(description=suggestion))

        self.report.add_error(error)
        return self

    def build(self) -> ErrorReport:
        """エラーレポートを構築"""
        return self.report
