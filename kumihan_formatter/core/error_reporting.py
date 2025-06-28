"""
統一エラーレポート機能

Issue #240対応: エラーの詳細レポート・修正提案・複数エラー一括表示
"""

import json
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

    description: str  # 修正内容の説明
    original_text: Optional[str] = None  # 元のテキスト
    suggested_text: Optional[str] = None  # 提案テキスト
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
    file_path: Optional[Path] = None  # ファイルパス
    location: Optional[ErrorLocation] = None  # エラー位置

    # コンテキスト
    context_lines: List[str] = field(default_factory=list)  # 周辺行
    highlighted_line: Optional[str] = None  # ハイライトされた問題行

    # 修正支援
    fix_suggestions: List[FixSuggestion] = field(default_factory=list)
    help_url: Optional[str] = None  # ヘルプURL
    learn_more: Optional[str] = None  # 学習リンク

    # メタデータ
    timestamp: datetime = field(default_factory=datetime.now)
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """人間が読みやすい形式でエラーを表示"""
        # 絵文字とユーザーフレンドリーなメッセージ
        severity_icons = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨",
        }

        # メインメッセージ
        icon = severity_icons.get(self.severity, "❓")
        lines = [f"{icon} {self.title}", f"   {self.message}"]

        # ファイル位置情報（分かりやすく）
        if self.file_path and self.location:
            lines.append(f"   📍 ファイル: {self.file_path.name} ({self.location})")

        # 問題箇所の表示（視覚的に強調）
        if self.highlighted_line:
            lines.extend(
                [
                    "",
                    "   🔍 問題箇所:",
                    f"   ┌─ {self.location if self.location else '不明'}",
                    f"   │ {self.highlighted_line.strip()}",
                    "   └─",
                ]
            )

        # コンテキスト行の表示
        if self.context_lines:
            lines.extend(["", "   📝 周辺コード:"])
            for i, context_line in enumerate(self.context_lines):
                prefix = "   → " if i == len(self.context_lines) // 2 else "     "
                lines.append(f"{prefix}{context_line.rstrip()}")

        # 修正提案（アクション指向）
        if self.fix_suggestions:
            lines.extend(["", "   💡 修正方法:"])
            for i, suggestion in enumerate(self.fix_suggestions, 1):
                confidence_emoji = (
                    "🎯" if suggestion.confidence >= 0.9 else "💭" if suggestion.confidence >= 0.7 else "🤔"
                )
                lines.append(f"   {confidence_emoji} {i}. {suggestion}")

        # ヘルプリンク
        if self.help_url:
            lines.extend(["", f"   📚 詳細: {self.help_url}"])

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

        # 美しいヘッダー
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

        # サマリー情報（分かりやすく）
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        info_count = len(self.info)

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

        lines.append(f"⏰ チェック実行時刻: {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # エラー表示（重要度順）
        if self.errors:
            lines.extend(["", "=" * 50, "🚨 修正が必要な問題", "=" * 50])
            for i, error in enumerate(self.errors, 1):
                lines.append(f"\n【問題 {i}】")
                lines.append(str(error))

        # 警告表示
        if self.warnings:
            lines.extend(["", "=" * 50, "⚠️  改善推奨事項", "=" * 50])
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"\n【改善案 {i}】")
                lines.append(str(warning))

        # 情報表示（オプション）
        if show_info and self.info:
            lines.extend(["", "=" * 50, "ℹ️  参考情報", "=" * 50])
            for i, info in enumerate(self.info, 1):
                lines.append(f"\n【情報 {i}】")
                lines.append(str(info))

        # フッター（次のアクション提案）
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
        lines.append(f"🕒 実行時刻: {self.generation_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
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
        lines.append("Kumihan記法の詳細: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md")
        lines.append("問題報告: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues")
        lines.append("=" * 60)

        # ファイルに書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _format_error_for_file(self, error: DetailedError) -> str:
        """ファイル出力用にエラーをフォーマット"""
        lines = []

        # 基本情報
        lines.append(f"タイトル: {error.title}")
        lines.append(f"メッセージ: {error.message}")
        lines.append(f"重要度: {error.severity.value}")
        lines.append(f"カテゴリ: {error.category.value}")

        # 位置情報
        if error.location:
            lines.append(f"位置: {error.location}")

        # 問題箇所
        if error.highlighted_line:
            lines.append(f"問題行: {error.highlighted_line.strip()}")

        # コンテキスト行
        if error.context_lines:
            lines.append("周辺コード:")
            for context_line in error.context_lines:
                lines.append(f"  {context_line}")

        # 修正提案
        if error.fix_suggestions:
            lines.append("修正提案:")
            for i, suggestion in enumerate(error.fix_suggestions, 1):
                confidence_text = (
                    "高" if suggestion.confidence >= 0.9 else "中" if suggestion.confidence >= 0.7 else "低"
                )
                lines.append(f"  {i}. {suggestion.description} (信頼度: {confidence_text})")
                if suggestion.original_text and suggestion.suggested_text:
                    lines.append(f"     変更前: {suggestion.original_text}")
                    lines.append(f"     変更後: {suggestion.suggested_text}")

        # ヘルプURL
        if error.help_url:
            lines.append(f"詳細情報: {error.help_url}")

        return "\n".join(lines)

    def _error_to_dict(self, error: DetailedError) -> Dict[str, Any]:
        """DetailedErrorを辞書形式に変換"""
        return {
            "error_id": error.error_id,
            "severity": error.severity.value,
            "category": error.category.value,
            "title": error.title,
            "message": error.message,
            "file_path": str(error.file_path) if error.file_path else None,
            "location": (
                {
                    "line": error.location.line,
                    "column": error.location.column,
                    "context_start": error.location.context_start,
                    "context_end": error.location.context_end,
                }
                if error.location
                else None
            ),
            "context_lines": error.context_lines,
            "highlighted_line": error.highlighted_line,
            "fix_suggestions": [
                {
                    "description": suggestion.description,
                    "original_text": suggestion.original_text,
                    "suggested_text": suggestion.suggested_text,
                    "action_type": suggestion.action_type,
                    "confidence": suggestion.confidence,
                }
                for suggestion in error.fix_suggestions
            ],
            "help_url": error.help_url,
            "learn_more": error.learn_more,
            "timestamp": error.timestamp.isoformat(),
            "additional_info": error.additional_info,
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
        suggestions: Optional[List[FixSuggestion]] = None,
        context_lines_count: int = 3,
    ) -> DetailedError:
        """記法エラーを作成（コンテキスト行を自動取得）"""
        # コンテキスト行を自動取得
        context_lines = ErrorReportBuilder._get_context_lines(file_path, line_number, context_lines_count)

        return DetailedError(
            error_id=f"syntax_{line_number}_{hash(problem_text) % 10000}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title=title,
            message=message,
            file_path=file_path,
            location=ErrorLocation(line=line_number),
            highlighted_line=problem_text,
            context_lines=context_lines,
            fix_suggestions=suggestions or [],
            help_url="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md",
        )

    @staticmethod
    def create_keyword_error(
        invalid_keyword: str, file_path: Path, line_number: int, valid_keywords: List[str]
    ) -> DetailedError:
        """キーワードエラーを作成"""
        suggestions = []

        # 類似キーワードの提案
        similar_keywords = ErrorReportBuilder._find_similar_keywords(invalid_keyword, valid_keywords)
        if similar_keywords:
            for keyword in similar_keywords[:3]:  # 上位3つまで
                suggestions.append(
                    FixSuggestion(
                        description=f"'{keyword}' を使用する",
                        original_text=invalid_keyword,
                        suggested_text=keyword,
                        confidence=0.8,
                    )
                )

        # 正しい記法の説明
        suggestions.append(
            FixSuggestion(description="使用可能なキーワード一覧を確認する", action_type="reference", confidence=0.9)
        )

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
            additional_info={"invalid_keyword": invalid_keyword, "valid_keywords": valid_keywords},
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

    @staticmethod
    def _get_context_lines(file_path: Path, line_number: int, context_count: int = 3) -> List[str]:
        """指定した行の周辺コンテキストを取得"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            # 行番号は1ベース、配列は0ベース
            target_line_index = line_number - 1
            start_index = max(0, target_line_index - context_count)
            end_index = min(len(all_lines), target_line_index + context_count + 1)

            context_lines = []
            for i in range(start_index, end_index):
                line_content = all_lines[i].rstrip()
                if i == target_line_index:
                    # 問題行を明確にマーク
                    context_lines.append(f"{i + 1:3d} →│ {line_content}")
                else:
                    context_lines.append(f"{i + 1:3d}  │ {line_content}")

            return context_lines

        except (FileNotFoundError, UnicodeDecodeError, IndexError):
            return [f"{line_number:3d} →│ （コンテキストを取得できませんでした）"]

    @staticmethod
    def create_enhanced_syntax_error(
        title: str,
        message: str,
        file_path: Path,
        line_number: int,
        problem_text: str,
        error_type: str,
        suggestions: Optional[List[FixSuggestion]] = None,
    ) -> DetailedError:
        """改良版記法エラー作成（より詳細なエラー分析）"""

        # エラータイプに基づいてカテゴリ決定
        category_map = {
            "keyword": ErrorCategory.KEYWORD,
            "marker": ErrorCategory.SYNTAX,
            "block": ErrorCategory.STRUCTURE,
            "attribute": ErrorCategory.ATTRIBUTE,
            "file": ErrorCategory.FILE,
        }
        category = category_map.get(error_type.lower(), ErrorCategory.SYNTAX)

        # エラータイプ別の具体的な修正提案を生成
        auto_suggestions = ErrorReportBuilder._generate_smart_suggestions(error_type, problem_text)

        # 手動提案と自動提案をマージ
        all_suggestions = (suggestions or []) + auto_suggestions

        # コンテキスト行を取得
        context_lines = ErrorReportBuilder._get_context_lines(file_path, line_number)

        return DetailedError(
            error_id=f"enhanced_{error_type}_{line_number}_{hash(problem_text) % 10000}",
            severity=ErrorSeverity.ERROR,
            category=category,
            title=title,
            message=message,
            file_path=file_path,
            location=ErrorLocation(line=line_number),
            highlighted_line=problem_text,
            context_lines=context_lines,
            fix_suggestions=all_suggestions,
            help_url="https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/blob/main/SPEC.md",
            additional_info={"error_type": error_type},
        )

    @staticmethod
    def _generate_smart_suggestions(error_type: str, problem_text: str) -> List[FixSuggestion]:
        """エラータイプ別のスマート修正提案を生成"""
        suggestions = []

        if error_type == "unclosed_block":
            suggestions.append(
                FixSuggestion(
                    description="ブロックの最後に ;;; を追加する",
                    original_text="（ブロック内容）",
                    suggested_text="（ブロック内容）\n;;;",
                    action_type="insert",
                    confidence=0.95,
                )
            )

        elif error_type == "empty_block":
            suggestions.extend(
                [
                    FixSuggestion(
                        description="ブロック内にコンテンツを追加する",
                        original_text=problem_text,
                        suggested_text="何らかの内容",
                        action_type="replace",
                        confidence=0.8,
                    ),
                    FixSuggestion(
                        description="空のブロックを削除する",
                        original_text=problem_text,
                        suggested_text="",
                        action_type="delete",
                        confidence=0.9,
                    ),
                ]
            )

        elif error_type == "invalid_keyword":
            # 一般的なスペルミスの修正提案
            common_fixes = {"見だし": "見出し", "ハイライド": "ハイライト", "太時": "太字", "イタリク": "イタリック"}

            for wrong, correct in common_fixes.items():
                if wrong in problem_text:
                    suggestions.append(
                        FixSuggestion(
                            description=f"'{wrong}' を '{correct}' に修正する",
                            original_text=problem_text.replace(wrong, f"[{wrong}]"),
                            suggested_text=problem_text.replace(wrong, correct),
                            action_type="replace",
                            confidence=0.9,
                        )
                    )

        elif error_type == "color_attribute_error":
            suggestions.append(
                FixSuggestion(
                    description="color属性は最後に配置してください",
                    original_text=problem_text,
                    suggested_text=";;;ハイライト color=#ff0000;;;",
                    action_type="replace",
                    confidence=0.85,
                )
            )

        return suggestions
