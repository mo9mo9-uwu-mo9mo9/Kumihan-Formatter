"""
エラー型定義

統一エラーレポート機能の基本データ型
Issue #319対応 - error_reporting.py から分離
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ErrorSeverity(Enum):
    """エラーの重要度"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """エラーのカテゴリ"""

    SYNTAX = "syntax"  # 記法エラー
    STRUCTURE = "structure"  # 構造エラー
    KEYWORD = "keyword"  # キーワードエラー
    ATTRIBUTE = "attribute"  # 属性エラー
    FILE = "file"  # ファイルエラー
    COMPATIBILITY = "compatibility"  # 互換性エラー


@dataclass
class ErrorLocation:
    """エラー位置情報"""

    line: int
    column: int | None = None
    context_start: int | None = None
    context_end: int | None = None

    def __str__(self) -> str:
        if self.column is not None:
            return f"行{self.line}:{self.column}"
        return f"行{self.line}"


@dataclass
class FixSuggestion:
    """修正提案"""

    description: str  # 修正内容の説明
    original_text: str | None = None  # 元のテキスト
    suggested_text: str | None = None  # 提案テキスト
    action_type: str = "replace"  # "replace", "insert", "delete"
    confidence: float = 1.0  # 提案の信頼度 (0.0-1.0)

    def __str__(self) -> str:
        if self.original_text and self.suggested_text:
            return f"{self.description}\n  変更前: {self.original_text}\n  変更後: {self.suggested_text}"
        return self.description


@dataclass
class DetailedError:
    """詳細エラー情報"""

    # 基本情報
    error_id: str  # 一意なエラーID
    severity: ErrorSeverity  # 重要度
    category: ErrorCategory  # カテゴリ
    title: str  # エラータイトル
    message: str  # 詳細メッセージ

    # 位置情報
    file_path: Path | None = None  # ファイルパス
    location: ErrorLocation | None = None  # エラー位置

    # コンテキスト
    context_lines: list[str] = field(default_factory=list)  # 周辺行
    highlighted_line: str | None = None  # ハイライトされた問題行

    # 修正支援
    fix_suggestions: list[FixSuggestion] = field(default_factory=list)
    help_url: str | None = None  # ヘルプURL
    learn_more: str | None = None  # 学習リンク

    # メタデータ
    timestamp: datetime = field(default_factory=datetime.now)
    additional_info: dict[str, Any] = field(default_factory=dict)
