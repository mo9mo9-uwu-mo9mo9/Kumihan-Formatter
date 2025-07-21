"""
エラーレポートフォーマット機能

エラーレポートの表示・フォーマットの責任を担当
Issue #540対応 - error_report.py から分離
"""

from datetime import datetime
from pathlib import Path

from .error_formatter import ErrorFormatter
from .error_types import DetailedError


class ErrorReportFormatter:
    """エラーレポートフォーマット機能"""

    def to_console_output(
        self,
        errors: list[DetailedError],
        warnings: list[DetailedError],
        info: list[DetailedError],
        source_file: Path | None,
        generation_time: datetime,
        show_info: bool = False,
    ) -> str:
        """コンソール表示用の文字列を生成"""
        lines = []

        # ヘッダーを追加
        lines.extend(self._create_header(source_file))

        # サマリーを追加
        lines.extend(self._create_summary(errors, warnings, info, generation_time))

        # エラー・警告・情報を表示
        lines.extend(self._create_error_sections(errors, warnings, info, show_info))

        # フッターを追加
        lines.extend(self._create_footer(errors, warnings))

        return "\n".join(lines)

    def _create_header(self, source_file: Path | None) -> list[str]:
        """ヘッダー部分を作成"""
        if source_file:
            return [
                "╭─────────────────────────────────────────╮",
                f"│  📄 {source_file.name} の記法チェック結果        │",
                "╰─────────────────────────────────────────╯",
            ]
        else:
            return [
                "╭─────────────────────────────────────────╮",
                "│  📋 記法チェック結果                      │",
                "╰─────────────────────────────────────────╯",
            ]

    def _create_summary(
        self,
        errors: list[DetailedError],
        warnings: list[DetailedError],
        info: list[DetailedError],
        generation_time: datetime,
    ) -> list[str]:
        """サマリー部分を作成"""
        error_count = len(errors)
        warning_count = len(warnings)
        lines = []

        if error_count == 0 and warning_count == 0:
            lines.extend(
                [
                    "",
                    "🎉 素晴らしい！記法エラーは見つかりませんでした！",
                    "✨ あなたのファイルはKumihan記法に完全に準拠しています。",
                ]
            )
        else:
            summary = self._get_summary_text(errors, warnings, info)
            lines.extend(["", f"📊 チェック結果: {summary}"])

        lines.append(
            f"⏰ チェック実行時刻: {generation_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return lines

    def _create_error_sections(
        self,
        errors: list[DetailedError],
        warnings: list[DetailedError],
        info: list[DetailedError],
        show_info: bool,
    ) -> list[str]:
        """エラー・警告・情報セクションを作成"""
        lines = []

        # エラー表示
        if errors:
            lines.extend(self._create_error_section(errors))

        # 警告表示
        if warnings:
            lines.extend(self._create_warning_section(warnings))

        # 情報表示
        if show_info and info:
            lines.extend(self._create_info_section(info))

        return lines

    def _create_error_section(self, errors: list[DetailedError]) -> list[str]:
        """エラーセクションを作成"""
        lines = ["", "=" * 50, "🚨 修正が必要な問題", "=" * 50]
        for i, error in enumerate(errors, 1):
            lines.append(f"\n【問題 {i}】")
            lines.append(ErrorFormatter.format_error(error))
        return lines

    def _create_warning_section(self, warnings: list[DetailedError]) -> list[str]:
        """警告セクションを作成"""
        lines = ["", "=" * 50, "⚠️  改善推奨事項", "=" * 50]
        for i, warning in enumerate(warnings, 1):
            lines.append(f"\n【改善案 {i}】")
            lines.append(ErrorFormatter.format_error(warning))
        return lines

    def _create_info_section(self, info: list[DetailedError]) -> list[str]:
        """情報セクションを作成"""
        lines = ["", "=" * 50, "ℹ️  参考情報", "=" * 50]
        for i, info_item in enumerate(info, 1):
            lines.append(f"\n【情報 {i}】")
            lines.append(ErrorFormatter.format_error(info_item))
        return lines

    def _create_footer(
        self, errors: list[DetailedError], warnings: list[DetailedError]
    ) -> list[str]:
        """フッター部分を作成"""
        error_count = len(errors)
        warning_count = len(warnings)

        if error_count > 0:
            return [
                "",
                "🔧 次のステップ:",
                "   1. 上記の修正提案を参考にファイルを修正してください",
                "   2. 修正後、再度チェックを実行してください",
                "   3. 困った場合は SPEC.md を参照してください",
            ]
        elif warning_count > 0:
            return [
                "",
                "✅ 次のステップ:",
                "   • 警告事項は修正推奨ですが、必須ではありません",
                "   • より良い記法のために修正をご検討ください",
            ]
        return []

    def _get_summary_text(
        self,
        errors: list[DetailedError],
        warnings: list[DetailedError],
        info: list[DetailedError],
    ) -> str:
        """サマリーテキストを取得"""
        error_count = len(errors)
        warning_count = len(warnings)
        info_count = len(info)

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
