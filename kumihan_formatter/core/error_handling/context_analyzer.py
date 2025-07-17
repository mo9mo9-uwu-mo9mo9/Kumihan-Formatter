"""
エラーコンテキスト分析・診断 - Issue #401対応

エラー分析、原因推定、レポート生成を担当。
コンテキスト情報を基にした高度な診断機能を提供。
"""

import json
import re
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .context_models import FileContext, OperationContext, SystemContext


class ContextAnalyzer:
    """エラーコンテキスト分析・診断クラス

    コンテキスト情報を分析してエラーの原因推定や
    有用な診断情報を生成
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def create_error_summary(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
    ) -> dict[str, Any]:
        """エラーサマリーを作成

        Args:
            error: 発生したエラー
            context_stack: コンテキストスタック
            system_context: システムコンテキスト
            file_contexts: ファイルコンテキスト辞書

        Returns:
            エラーサマリー情報
        """
        current_context = context_stack[-1] if context_stack else None
        file_contexts = file_contexts or {}

        error_summary = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": (
                current_context.started_at.isoformat() if current_context else None
            ),
            "location": self._get_error_location(current_context),
            "operation_chain": self._build_operation_chain(context_stack),
            "system_info": self._extract_system_info(system_context),
            "probable_cause": self.suggest_probable_cause(error, current_context),
            "breadcrumb": self.get_context_breadcrumb(context_stack),
        }

        # ファイル関連の情報を追加
        if current_context and current_context.file_path:
            file_path = current_context.file_path
            if file_path in file_contexts:
                error_summary["file_info"] = file_contexts[file_path].to_dict()

        return error_summary

    def suggest_probable_cause(
        self, error: Exception, context: OperationContext | None
    ) -> str:
        """エラーの推定原因を提案

        Args:
            error: 発生したエラー
            context: 現在のコンテキスト

        Returns:
            推定原因の説明
        """
        error_type = type(error).__name__
        error_message = str(error).lower()

        # エラータイプ別の一般的な原因
        common_causes = {
            "FileNotFoundError": "指定されたファイルが存在しないか、パスが間違っています。",
            "PermissionError": "ファイルやディレクトリへのアクセス権限がありません。",
            "UnicodeDecodeError": "ファイルのエンコーディングが正しく検出できませんでした。",
            "ValueError": "入力値の形式や範囲が期待されるものと異なります。",
            "TypeError": "データ型が期待されるものと異なります。",
            "KeyError": "辞書や設定で指定されたキーが見つかりません。",
            "IndexError": "リストやシーケンスの範囲外にアクセスしています。",
            "ImportError": "必要なモジュールやパッケージがインストールされていません。",
        }

        base_cause = common_causes.get(error_type, f"{error_type}が発生しました。")

        # コンテキスト固有の詳細分析
        context_clues = []

        if context:
            # ファイル関連の操作でのエラー
            if context.file_path and error_type in [
                "FileNotFoundError",
                "PermissionError",
            ]:
                context_clues.append(f"ファイル: {context.file_path}")

            # パーサー関連のエラー
            if context.component.lower() == "parser":
                if "syntax" in error_message:
                    context_clues.append("記法エラーの可能性があります。")
                if context.line_number:
                    context_clues.append(
                        f"行 {context.line_number} 付近を確認してください。"
                    )

            # レンダラー関連のエラー
            if context.component.lower() == "renderer":
                if "template" in error_message:
                    context_clues.append(
                        "テンプレートファイルの問題の可能性があります。"
                    )

            # キャッシュ関連のエラー
            if "cache" in context.operation_name.lower():
                context_clues.append(
                    "キャッシュファイルの破損やディスク容量不足の可能性があります。"
                )

        # 特定のエラーメッセージパターンを分析
        if "no space left" in error_message:
            context_clues.append("ディスク容量が不足しています。")
        elif "permission denied" in error_message:
            context_clues.append(
                "管理者権限で実行するか、ファイル権限を確認してください。"
            )
        elif "encoding" in error_message:
            context_clues.append(
                "ファイルのエンコーディングをUTF-8で保存し直してください。"
            )

        # 結果をまとめる
        if context_clues:
            return f"{base_cause} {' '.join(context_clues)}"
        else:
            return base_cause

    def get_context_breadcrumb(self, context_stack: list[OperationContext]) -> str:
        """コンテキストのパンくずリストを生成

        Args:
            context_stack: コンテキストスタック

        Returns:
            パンくずリスト文字列
        """
        if not context_stack:
            return "No operation context"

        breadcrumb_parts = []
        for context in context_stack:
            part = f"{context.component}.{context.operation_name}"
            if context.file_path:
                file_name = Path(context.file_path).name
                part += f"({file_name})"
            breadcrumb_parts.append(part)

        return " → ".join(breadcrumb_parts)

    def _get_error_location(self, context: OperationContext | None) -> dict[str, Any]:
        """エラー位置情報を取得"""
        if not context:
            return {}

        location = {
            "file_path": context.file_path,
            "line_number": context.line_number,
            "column_number": context.column_number,
        }

        return {k: v for k, v in location.items() if v is not None}

    def _build_operation_chain(
        self, context_stack: list[OperationContext]
    ) -> list[dict[str, Any]]:
        """操作チェーンを構築"""
        return [
            {
                "operation": ctx.operation_name,
                "component": ctx.component,
                "started_at": ctx.started_at.isoformat(),
                "metadata": ctx.metadata,
            }
            for ctx in context_stack
        ]

    def _extract_system_info(self, system_context: SystemContext) -> dict[str, Any]:
        """システム情報を抽出"""
        return {
            "platform": system_context.platform,
            "python_version": system_context.python_version,
            "working_directory": system_context.working_directory,
            "memory_usage_mb": (
                round(system_context.memory_usage / 1024 / 1024, 1)
                if system_context.memory_usage
                else None
            ),
            "cpu_usage": system_context.cpu_usage,
            "disk_space_mb": (
                round(system_context.disk_space / 1024 / 1024, 1)
                if system_context.disk_space
                else None
            ),
        }

    def generate_detailed_report(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
    ) -> str:
        """詳細なエラーレポートを生成

        Args:
            error: 発生したエラー
            context_stack: コンテキストスタック
            system_context: システムコンテキスト
            file_contexts: ファイルコンテキスト辞書

        Returns:
            フォーマットされたエラーレポート
        """
        summary = self.create_error_summary(
            error, context_stack, system_context, file_contexts
        )

        lines = []
        lines.append("=" * 60)
        lines.append("ERROR DIAGNOSTIC REPORT")
        lines.append("=" * 60)

        # エラー基本情報
        lines.append(f"Error Type: {summary['error_type']}")
        lines.append(f"Message: {summary['error_message']}")
        lines.append(f"Timestamp: {summary['timestamp']}")
        lines.append("")

        # 推定原因
        lines.append("Probable Cause:")
        lines.append(f"  {summary['probable_cause']}")
        lines.append("")

        # エラー位置
        if summary["location"]:
            lines.append("Error Location:")
            for key, value in summary["location"].items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # 操作チェーン
        if summary["operation_chain"]:
            lines.append("Operation Chain:")
            for i, op in enumerate(summary["operation_chain"]):
                indent = "  " * (i + 1)
                lines.append(f"{indent}{op['component']}.{op['operation']}")
            lines.append("")

        # コンテキストパンくず
        lines.append(f"Context Breadcrumb: {summary['breadcrumb']}")
        lines.append("")

        # システム情報
        lines.append("System Information:")
        sys_info = summary["system_info"]
        for key, value in sys_info.items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        lines.append("")

        # ファイル情報
        if "file_info" in summary:
            lines.append("File Information:")
            file_info = summary["file_info"]
            for key, value in file_info.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def export_context_as_json(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
        output_file: str | None = None,
    ) -> str:
        """コンテキスト情報をJSONとしてエクスポート

        Args:
            error: 発生したエラー
            context_stack: コンテキストスタック
            system_context: システムコンテキスト
            file_contexts: ファイルコンテキスト辞書
            output_file: 出力ファイルパス

        Returns:
            JSON文字列
        """
        summary = self.create_error_summary(
            error, context_stack, system_context, file_contexts
        )

        json_str = json.dumps(summary, indent=2, ensure_ascii=False, default=str)

        if output_file:
            try:
                Path(output_file).write_text(json_str, encoding="utf-8")
                self.logger.info(
                    f"コンテキスト情報をエクスポートしました: {output_file}"
                )
            except Exception as e:
                self.logger.error(f"エクスポートに失敗しました: {e}")

        return json_str
