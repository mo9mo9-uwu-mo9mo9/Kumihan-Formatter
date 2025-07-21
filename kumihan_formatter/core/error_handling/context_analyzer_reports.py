"""
エラーコンテキスト分析レポート機能 - context_analyzer.pyから分割

詳細レポート生成とエクスポート機能
Issue #401対応 - 300行制限遵守
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .context_models import FileContext, OperationContext, SystemContext


class ContextAnalyzerReports:
    """エラーコンテキスト分析のレポート機能"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def generate_detailed_report(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
    ) -> dict[str, Any]:
        """詳細レポートを生成

        Args:
            error: 発生したエラー
            context_stack: コンテキストスタック
            system_context: システムコンテキスト
            file_contexts: ファイルコンテキスト辞書

        Returns:
            詳細レポート辞書
        """
        self.logger.info("詳細レポート生成開始")

        # 基本情報
        report = {
            "report_type": "detailed_error_analysis",
            "error_analysis": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": (
                    str(error.__traceback__) if error.__traceback__ else None
                ),
            },
            "context_analysis": self._analyze_context_stack(context_stack),
            "system_analysis": self._analyze_system_context(system_context),
            "file_analysis": (
                self._analyze_file_contexts(file_contexts) if file_contexts else None
            ),
            "recommendations": self._generate_recommendations(
                error, context_stack, system_context
            ),
        }

        self.logger.info("詳細レポート生成完了")
        return report

    def export_context_as_json(
        self,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
        output_path: Path | None = None,
    ) -> str:
        """コンテキストをJSONでエクスポート

        Args:
            context_stack: コンテキストスタック
            system_context: システムコンテキスト
            file_contexts: ファイルコンテキスト辞書
            output_path: 出力パス（指定されない場合は文字列で返す）

        Returns:
            JSON文字列またはファイルパス
        """
        self.logger.info("コンテキストJSONエクスポート開始")

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "context_stack": [
                {
                    "operation_type": ctx.operation_name,
                    "file_path": ctx.file_path,
                    "line_number": ctx.line_number,
                    "column_number": ctx.column_number,
                    "timestamp": ctx.started_at.isoformat() if ctx.started_at else None,
                    "metadata": ctx.metadata,
                }
                for ctx in context_stack
            ],
            "system_context": {
                "platform": system_context.platform,
                "python_version": system_context.python_version,
                "working_directory": system_context.working_directory,
                "memory_usage": system_context.memory_usage,
                "cpu_usage": system_context.cpu_usage,
                "disk_space": system_context.disk_space,
            },
            "file_contexts": (
                {
                    path: {
                        "size": ctx.file_size,
                        "encoding": ctx.encoding,
                        "last_modified": (
                            ctx.last_modified.isoformat() if ctx.last_modified else None
                        ),
                        "is_readable": ctx.is_readable,
                        "is_writable": ctx.is_writable,
                    }
                    for path, ctx in file_contexts.items()
                }
                if file_contexts
                else None
            ),
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

        if output_path:
            output_path.write_text(json_str, encoding="utf-8")
            self.logger.info(f"コンテキストJSONエクスポート完了: {output_path}")
            return str(output_path)
        else:
            self.logger.info("コンテキストJSONエクスポート完了（文字列）")
            return json_str

    def _analyze_context_stack(
        self, context_stack: list[OperationContext]
    ) -> dict[str, Any]:
        """コンテキストスタックを分析"""
        if not context_stack:
            return {"available": False, "message": "No context stack available"}

        analysis = {
            "available": True,
            "stack_depth": len(context_stack),
            "operation_types": [ctx.operation_name for ctx in context_stack],
            "file_paths": [ctx.file_path for ctx in context_stack if ctx.file_path],
            "timeline": [
                {
                    "operation": ctx.operation_name,
                    "timestamp": ctx.started_at.isoformat() if ctx.started_at else None,
                }
                for ctx in context_stack
            ],
        }

        # 操作パターンの分析
        operation_counts: dict[str, int] = {}
        for ctx in context_stack:
            operation_counts[ctx.operation_name] = (
                operation_counts.get(ctx.operation_name, 0) + 1
            )

        analysis["operation_distribution"] = operation_counts
        analysis["dominant_operation"] = max(
            operation_counts.items(), key=lambda x: x[1]
        )[0]

        return analysis

    def _analyze_system_context(self, system_context: SystemContext) -> dict[str, Any]:
        """システムコンテキストを分析"""
        analysis = {
            "platform_info": {
                "platform": system_context.platform,
                "python_version": system_context.python_version,
            },
            "resource_info": {
                "memory_usage": system_context.memory_usage,
                "cpu_usage": system_context.cpu_usage,
            },
            "environment_info": {
                "working_directory": system_context.working_directory,
            },
        }

        # リソース状況の評価
        if system_context.memory_usage:
            if system_context.memory_usage > 1024 * 1024 * 1024:  # 1GB以上
                analysis["resource_warnings"] = ["High memory usage"]
            else:
                analysis["resource_warnings"] = []

        return analysis

    def _analyze_file_contexts(
        self, file_contexts: dict[str, FileContext]
    ) -> dict[str, Any]:
        """ファイルコンテキストを分析"""
        if not file_contexts:
            return {"available": False}

        analysis = {
            "available": True,
            "file_count": len(file_contexts),
            "total_size": sum(ctx.file_size or 0 for ctx in file_contexts.values()),
            "encodings": list(
                set(ctx.encoding for ctx in file_contexts.values() if ctx.encoding)
            ),
        }

        # サイズ別分析
        large_files = [
            path
            for path, ctx in file_contexts.items()
            if (ctx.file_size or 0) > 1024 * 1024
        ]  # 1MB以上
        if large_files:
            analysis["large_files"] = large_files

        return analysis

    def _generate_recommendations(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
    ) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        error_type = type(error).__name__

        # エラータイプ別の推奨事項
        if error_type in ["FileNotFoundError", "PermissionError"]:
            recommendations.extend(
                [
                    "ファイルパスと存在を確認してください",
                    "ファイルのアクセス権限を確認してください",
                    "相対パスではなく絶対パスの使用を検討してください",
                ]
            )

        elif error_type in ["UnicodeDecodeError", "UnicodeEncodeError"]:
            recommendations.extend(
                [
                    "ファイルのエンコーディングを確認してください",
                    "UTF-8でファイルを保存し直してください",
                    "BOMの有無を確認してください",
                ]
            )

        elif error_type in ["ValueError", "TypeError"]:
            recommendations.extend(
                [
                    "入力データの形式と型を確認してください",
                    "データの妥当性を検証してください",
                    "APIドキュメントを確認してください",
                ]
            )

        # コンテキストベースの推奨事項
        if context_stack:
            current_context = context_stack[0]

            if current_context.operation_name == "file_parsing":
                recommendations.append(
                    "構文エラーの可能性があります。記法を確認してください"
                )

            elif current_context.operation_name == "rendering":
                recommendations.append("レンダリング設定を確認してください")

        # システムリソースベースの推奨事項
        if (
            system_context.memory_usage
            and system_context.memory_usage > 1024 * 1024 * 1024
        ):
            recommendations.append(
                "メモリ不足の可能性があります。システムリソースを確認してください"
            )

        return recommendations
