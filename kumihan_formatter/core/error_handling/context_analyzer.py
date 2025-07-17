"""
エラーコンテキスト分析・診断 - Issue #401対応 統合モジュール

エラー分析、原因推定、レポート生成を担当。
コンテキスト情報を基にした高度な診断機能を提供。

分割されたモジュール:
- context_analyzer_core: 基本的なエラー分析と診断機能
- context_analyzer_reports: 詳細レポート生成とエクスポート機能
"""

from pathlib import Path
from typing import Any

from .context_analyzer_core import ContextAnalyzerCore
from .context_analyzer_reports import ContextAnalyzerReports
from .context_models import FileContext, OperationContext, SystemContext


class ContextAnalyzer(ContextAnalyzerCore):
    """エラーコンテキスト分析・診断クラス（統合）

    コンテキスト情報を分析してエラーの原因推定や
    有用な診断情報を生成
    """

    def __init__(self) -> None:
        """コンテキスト分析器を初期化"""
        super().__init__()

        # レポート機能を初期化
        self.reports = ContextAnalyzerReports()

    # レポート機能へのデリゲート
    def generate_detailed_report(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
    ) -> dict[str, Any]:
        """詳細レポートを生成"""
        return self.reports.generate_detailed_report(
            error, context_stack, system_context, file_contexts
        )

    def export_context_as_json(
        self,
        context_stack: list[OperationContext],
        system_context: SystemContext,
        file_contexts: dict[str, FileContext] | None = None,
        output_path: Path | None = None,
    ) -> str:
        """コンテキストをJSONでエクスポート"""
        return self.reports.export_context_as_json(
            context_stack, system_context, file_contexts, output_path
        )


# 後方互換性のため、クラスをエクスポート
__all__ = [
    "ContextAnalyzer",
    "ContextAnalyzerCore",
    "ContextAnalyzerReports",
]
