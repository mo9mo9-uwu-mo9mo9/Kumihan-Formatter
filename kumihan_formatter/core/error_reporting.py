"""
統一エラーレポート機能

Issue #240対応: エラーの詳細レポート・修正提案・複数エラー一括表示
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
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
    
    def __str__(self) -> str:
        """人間が読みやすい形式でエラーを表示"""
        lines = [
            f"[{self.severity.value.upper()}] {self.title}",
            f"  {self.message}"
        ]
        
        if self.file_path and self.location:
            lines.append(f"  場所: {self.file_path.name} {self.location}")
        
        if self.highlighted_line:
            lines.extend([
                "  問題行:",
                f"    {self.highlighted_line}"
            ])
        
        if self.fix_suggestions:
            lines.append("  修正提案:")
            for i, suggestion in enumerate(self.fix_suggestions, 1):
                lines.append(f"    {i}. {suggestion}")
        
        return "\n".join(lines)


class ErrorReport:
    """エラーレポート統合クラス"""
    
    def __init__(self, source_file: Optional[Path] = None):
        self.source_file = source_file
        self.errors: List[DetailedError] = []
        self.warnings: List[DetailedError] = []
        self.info: List[DetailedError] = []
        self.generation_time = datetime.now()
    
    def add_error(self, error: DetailedError) -> None:
        """エラーを追加"""
        if error.severity == ErrorSeverity.ERROR or error.severity == ErrorSeverity.CRITICAL:
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
            lines.append(f"=== {self.source_file.name} のエラーレポート ===")
        else:
            lines.append("=== エラーレポート ===")
        
        lines.append(f"実行時刻: {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"結果: {self.get_summary()}")
        lines.append("")
        
        # エラー表示
        if self.errors:
            lines.append("🚫 エラー:")
            for error in self.errors:
                lines.append(str(error))
                lines.append("")
        
        # 警告表示
        if self.warnings:
            lines.append("⚠️  警告:")
            for warning in self.warnings:
                lines.append(str(warning))
                lines.append("")
        
        # 情報表示（オプション）
        if show_info and self.info:
            lines.append("ℹ️  情報:")
            for info in self.info:
                lines.append(str(info))
                lines.append("")
        
        return "\n".join(lines)
    
    def to_file_report(self, output_path: Path) -> None:
        """詳細レポートをファイルに出力"""
        report_data = {
            "metadata": {
                "source_file": str(self.source_file) if self.source_file else None,
                "generation_time": self.generation_time.isoformat(),
                "summary": self.get_summary(),
                "counts": {
                    "errors": len(self.errors),
                    "warnings": len(self.warnings),
                    "info": len(self.info)
                }
            },
            "errors": [self._error_to_dict(error) for error in self.errors],
            "warnings": [self._error_to_dict(error) for error in self.warnings],
            "info": [self._error_to_dict(error) for error in self.info]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    def _error_to_dict(self, error: DetailedError) -> Dict[str, Any]:
        """DetailedErrorを辞書形式に変換"""
        return {
            "error_id": error.error_id,
            "severity": error.severity.value,
            "category": error.category.value,
            "title": error.title,
            "message": error.message,
            "file_path": str(error.file_path) if error.file_path else None,
            "location": {
                "line": error.location.line,
                "column": error.location.column,
                "context_start": error.location.context_start,
                "context_end": error.location.context_end
            } if error.location else None,
            "context_lines": error.context_lines,
            "highlighted_line": error.highlighted_line,
            "fix_suggestions": [
                {
                    "description": suggestion.description,
                    "original_text": suggestion.original_text,
                    "suggested_text": suggestion.suggested_text,
                    "action_type": suggestion.action_type,
                    "confidence": suggestion.confidence
                }
                for suggestion in error.fix_suggestions
            ],
            "help_url": error.help_url,
            "learn_more": error.learn_more,
            "timestamp": error.timestamp.isoformat(),
            "additional_info": error.additional_info
        }


class ErrorReportBuilder:
    """エラーレポート作成ヘルパー"""
    
    @staticmethod
    def create_syntax_error(
        title: str,
        message: str,
        file_path: Path,
        line_number: int,
        problem_text: str,
        suggestions: Optional[List[FixSuggestion]] = None
    ) -> DetailedError:
        """記法エラーを作成"""
        return DetailedError(
            error_id=f"syntax_{line_number}_{hash(problem_text) % 10000}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title=title,
            message=message,
            file_path=file_path,
            location=ErrorLocation(line=line_number),
            highlighted_line=problem_text,
            fix_suggestions=suggestions or [],
            help_url="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md"
        )
    
    @staticmethod
    def create_keyword_error(
        invalid_keyword: str,
        file_path: Path,
        line_number: int,
        valid_keywords: List[str]
    ) -> DetailedError:
        """キーワードエラーを作成"""
        suggestions = []
        
        # 類似キーワードの提案
        similar_keywords = ErrorReportBuilder._find_similar_keywords(invalid_keyword, valid_keywords)
        if similar_keywords:
            for keyword in similar_keywords[:3]:  # 上位3つまで
                suggestions.append(FixSuggestion(
                    description=f"'{keyword}' を使用する",
                    original_text=invalid_keyword,
                    suggested_text=keyword,
                    confidence=0.8
                ))
        
        # 正しい記法の説明
        suggestions.append(FixSuggestion(
            description="使用可能なキーワード一覧を確認する",
            action_type="reference",
            confidence=0.9
        ))
        
        return DetailedError(
            error_id=f"keyword_{line_number}_{hash(invalid_keyword) % 10000}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.KEYWORD,
            title=f"不明なキーワード: {invalid_keyword}",
            message=f"'{invalid_keyword}' は有効なKumihan記法キーワードではありません",
            file_path=file_path,
            location=ErrorLocation(line=line_number),
            fix_suggestions=suggestions,
            help_url="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md",
            additional_info={"invalid_keyword": invalid_keyword, "valid_keywords": valid_keywords}
        )
    
    @staticmethod
    def _find_similar_keywords(target: str, candidates: List[str]) -> List[str]:
        """類似キーワードを検索（シンプルな編集距離ベース）"""
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # 編集距離で類似度を計算
        similarities = []
        for candidate in candidates:
            distance = levenshtein_distance(target.lower(), candidate.lower())
            if distance <= 2:  # 編集距離2以下を類似とみなす
                similarities.append((candidate, distance))
        
        # 編集距離でソート
        similarities.sort(key=lambda x: x[1])
        return [candidate for candidate, _ in similarities]