"""
エラーコンテキスト分析コア機能 - context_analyzer.pyから分割

基本的なエラー分析と診断機能
Issue #401対応 - 300行制限遵守
"""

import json
import re
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .context_models import FileContext, OperationContext, SystemContext


class ContextAnalyzerCore:
    """エラーコンテキスト分析のコア機能"""

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
            エラーサマリー辞書
        """
        self.logger.debug(f"エラーサマリー作成開始: {type(error).__name__}")

        # 基本情報
        summary = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": system_context.timestamp,
            "location": self._get_error_location(context_stack[0] if context_stack else None),
            "operation_chain": self._build_operation_chain(context_stack),
            "system_info": self._extract_system_info(system_context),
        }

        # ファイルコンテキストを追加
        if file_contexts:
            summary["file_contexts"] = {
                path: {
                    "size": ctx.size,
                    "encoding": ctx.encoding,
                    "last_modified": ctx.last_modified.isoformat() if ctx.last_modified else None,
                    "content_type": ctx.content_type,
                }
                for path, ctx in file_contexts.items()
            }

        # 推定原因を追加
        probable_cause = self.suggest_probable_cause(error, context_stack, system_context)
        summary["probable_cause"] = probable_cause

        # コンテキストブレッドクラムを追加
        breadcrumb = self.get_context_breadcrumb(context_stack)
        summary["context_breadcrumb"] = breadcrumb

        self.logger.debug("エラーサマリー作成完了")
        return summary

    def suggest_probable_cause(
        self,
        error: Exception,
        context_stack: list[OperationContext],
        system_context: SystemContext,
    ) -> dict[str, Any]:
        """推定原因を提案

        Args:
            error: 発生したエラー
            context_stack: コンテキストスタック
            system_context: システムコンテキスト

        Returns:
            推定原因辞書
        """
        self.logger.debug("推定原因分析開始")

        error_type = type(error).__name__
        error_msg = str(error)
        
        # 基本的な原因分析
        cause_analysis = {
            "primary_cause": "unknown",
            "confidence": 0.0,
            "suggestions": [],
            "related_contexts": [],
        }

        # エラータイプ別の分析
        if error_type in ["FileNotFoundError", "PermissionError"]:
            cause_analysis["primary_cause"] = "file_system_issue"
            cause_analysis["confidence"] = 0.8
            cause_analysis["suggestions"] = [
                "ファイルパスを確認してください",
                "ファイルの存在とアクセス権限を確認してください",
            ]
            
        elif error_type in ["UnicodeDecodeError", "UnicodeEncodeError"]:
            cause_analysis["primary_cause"] = "encoding_issue"
            cause_analysis["confidence"] = 0.9
            cause_analysis["suggestions"] = [
                "ファイルのエンコーディングを確認してください",
                "UTF-8でファイルを保存し直してください",
            ]
            
        elif error_type in ["ValueError", "TypeError"]:
            cause_analysis["primary_cause"] = "data_format_issue"
            cause_analysis["confidence"] = 0.7
            cause_analysis["suggestions"] = [
                "入力データの形式を確認してください",
                "データの型と値を確認してください",
            ]
            
        elif "syntax" in error_msg.lower():
            cause_analysis["primary_cause"] = "syntax_error"
            cause_analysis["confidence"] = 0.85
            cause_analysis["suggestions"] = [
                "記法の構文を確認してください",
                "対応する終了タグがあるか確認してください",
            ]

        # コンテキストベースの追加分析
        if context_stack:
            current_context = context_stack[0]
            
            # 操作種別による分析
            if current_context.operation_type == "file_parsing":
                cause_analysis["related_contexts"].append("file_parsing")
                if "line" in error_msg.lower():
                    cause_analysis["suggestions"].append("指定された行番号付近を確認してください")
                    
            elif current_context.operation_type == "rendering":
                cause_analysis["related_contexts"].append("rendering")
                cause_analysis["suggestions"].append("レンダリング設定を確認してください")

        self.logger.debug(f"推定原因分析完了: {cause_analysis['primary_cause']}")
        return cause_analysis

    def get_context_breadcrumb(self, context_stack: list[OperationContext]) -> str:
        """コンテキストブレッドクラムを取得

        Args:
            context_stack: コンテキストスタック

        Returns:
            ブレッドクラム文字列
        """
        if not context_stack:
            return "No context available"

        breadcrumb_parts = []
        for i, context in enumerate(reversed(context_stack)):
            level_indicator = "→" if i > 0 else "📍"
            breadcrumb_parts.append(f"{level_indicator} {context.operation_type}")
            
            if context.file_path:
                breadcrumb_parts.append(f"({Path(context.file_path).name})")

        return " ".join(breadcrumb_parts)

    def _get_error_location(self, context: OperationContext | None) -> dict[str, Any]:
        """エラー位置情報を取得"""
        if not context:
            return {"available": False}

        location = {
            "available": True,
            "file_path": context.file_path,
            "line_number": context.line_number,
            "column_number": context.column_number,
            "operation_type": context.operation_type,
        }

        return location

    def _build_operation_chain(
        self, context_stack: list[OperationContext]
    ) -> list[dict[str, Any]]:
        """操作チェーンを構築"""
        if not context_stack:
            return []

        chain = []
        for context in context_stack:
            chain.append({
                "operation_type": context.operation_type,
                "file_path": context.file_path,
                "line_number": context.line_number,
                "timestamp": context.timestamp.isoformat() if context.timestamp else None,
            })

        return chain

    def _extract_system_info(self, system_context: SystemContext) -> dict[str, Any]:
        """システム情報を抽出"""
        return {
            "platform": system_context.platform,
            "python_version": system_context.python_version,
            "working_directory": system_context.working_directory,
            "environment_variables": system_context.environment_variables,
            "available_memory": system_context.available_memory,
            "cpu_count": system_context.cpu_count,
        }