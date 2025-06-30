"""
エラー型定義

統一エラーレポート機能の基本データ型
Issue #319対応 - error_reporting.py から分離
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime


class ErrorSeverity(Enum):
    """エラーの重要度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """エラーのカテゴリ"""
    SYNTAX = "syntax"           # 記法エラー
    STRUCTURE = "structure"     # 構造エラー
    KEYWORD = "keyword"         # キーワードエラー
    ATTRIBUTE = "attribute"     # 属性エラー
    FILE = "file"              # ファイルエラー
    COMPATIBILITY = "compatibility"  # 互換性エラー


@dataclass
class ErrorLocation:
    """エラー位置情報"""
    line: int
    column: Optional[int] = None
    context_start: Optional[int] = None
    context_end: Optional[int] = None
    
    def __str__(self) -> str:
        if self.column is not None:
            return f"行{self.line}:{self.column}"
        return f"行{self.line}"


@dataclass
class FixSuggestion:
    """修正提案"""
    description: str                    # 修正内容の説明
    original_text: Optional[str] = None # 元のテキスト
    suggested_text: Optional[str] = None # 提案テキスト
    action_type: str = "replace"        # "replace", "insert", "delete"
    confidence: float = 1.0             # 提案の信頼度 (0.0-1.0)
    
    def __str__(self) -> str:
        if self.original_text and self.suggested_text:
            return f"{self.description}\n  変更前: {self.original_text}\n  変更後: {self.suggested_text}"
        return self.description


@dataclass
class DetailedError:
    """詳細エラー情報"""
    # 基本情報
    error_id: str                           # 一意なエラーID
    severity: ErrorSeverity                 # 重要度
    category: ErrorCategory                 # カテゴリ
    title: str                              # エラータイトル
    message: str                            # 詳細メッセージ
    
    # 位置情報
    file_path: Optional[Path] = None        # ファイルパス
    location: Optional[ErrorLocation] = None # エラー位置
    
    # コンテキスト
    context_lines: List[str] = field(default_factory=list)  # 周辺行
    highlighted_line: Optional[str] = None   # ハイライトされた問題行
    
    # 修正支援
    fix_suggestions: List[FixSuggestion] = field(default_factory=list)
    help_url: Optional[str] = None          # ヘルプURL
    learn_more: Optional[str] = None        # 学習リンク
    
    # メタデータ
    timestamp: datetime = field(default_factory=datetime.now)
    additional_info: Dict[str, Any] = field(default_factory=dict)