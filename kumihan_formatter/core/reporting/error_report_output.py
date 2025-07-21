"""
エラーレポート出力機能

エラーレポートの出力・表示の責任を担当
Issue #540対応 - error_report.py から分離
"""

from datetime import datetime
from pathlib import Path

from .error_types import DetailedError


class ErrorReportOutput:
    """エラーレポート出力機能"""

    def to_file_report(
        self,
        errors: list[DetailedError],
        warnings: list[DetailedError],
        info: list[DetailedError],
        source_file: Path | None,
        generation_time: datetime,
        output_path: Path,
    ) -> None:
        """詳細レポートをテキストファイルに出力"""
        lines = []

        # ヘッダー情報
        lines.append("=" * 60)
        lines.append("Kumihan-Formatter エラーレポート")
        lines.append("=" * 60)
        lines.append("")

        # メタデータ
        if source_file:
            lines.append(f"📁 対象ファイル: {source_file}")
        lines.append(
            f"🕒 実行時刻: {generation_time.strftime('%Y年%m月%d日 %H:%M:%S')}"
        )

        # サマリー情報を生成
        summary = self._get_summary_text(errors, warnings, info)
        lines.append(f"📊 結果概要: {summary}")
        lines.append("")

        # 統計情報
        lines.append("📈 統計情報:")
        lines.append(f"   エラー: {len(errors)}個")
        lines.append(f"   警告: {len(warnings)}個")
        lines.append(f"   情報: {len(info)}個")
        lines.append("")

        # エラー詳細
        if errors:
            lines.append("🚫 エラー詳細:")
            lines.append("-" * 40)
            for i, error in enumerate(errors, 1):
                lines.append(f"[エラー {i}]")
                lines.append(self._format_error_for_file(error))
                lines.append("")

        # 警告詳細
        if warnings:
            lines.append("⚠️  警告詳細:")
            lines.append("-" * 40)
            for i, warning in enumerate(warnings, 1):
                lines.append(f"[警告 {i}]")
                lines.append(self._format_error_for_file(warning))
                lines.append("")

        # 情報詳細
        if info:
            lines.append("ℹ️  情報詳細:")
            lines.append("-" * 40)
            for i, info_item in enumerate(info, 1):
                lines.append(f"[情報 {i}]")
                lines.append(self._format_error_for_file(info_item))
                lines.append("")

        # フッター
        lines.append("=" * 60)
        lines.append(
            "Kumihan記法の詳細: "
            "https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md"
        )
        lines.append(
            "問題報告: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues"
        )
        lines.append("=" * 60)

        # ファイルに書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

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
