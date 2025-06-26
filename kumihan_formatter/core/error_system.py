"""
ユーザーフレンドリーエラーシステム

技術的なエラーメッセージを分かりやすい日本語メッセージに変換し、
具体的な解決方法を提示するエラーハンドリングシステム
"""

import difflib
import platform
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime


class ErrorLevel(Enum):
    """エラーレベル定義"""
    INFO = "info"           # 青色表示（情報）
    WARNING = "warning"     # 黄色表示（警告）
    ERROR = "error"         # 赤色表示（エラー）
    CRITICAL = "critical"   # 赤背景表示（致命的）


class ErrorCategory(Enum):
    """エラーカテゴリ定義"""
    FILE_SYSTEM = "file_system"        # ファイル関連
    ENCODING = "encoding"              # エンコーディング関連
    SYNTAX = "syntax"                  # 記法関連
    PERMISSION = "permission"          # 権限関連
    SYSTEM = "system"                  # システム関連
    NETWORK = "network"                # ネットワーク関連
    UNKNOWN = "unknown"                # 不明


@dataclass
class ErrorSolution:
    """エラー解決方法"""
    quick_fix: str                     # 即座にできる解決方法
    detailed_steps: List[str]          # 詳細な手順
    external_links: List[str] = None   # 参考リンク
    alternative_approaches: List[str] = None  # 代替手段


@dataclass
class UserFriendlyError:
    """ユーザーフレンドリーエラー情報"""
    error_code: str                    # エラーコード（E001など）
    level: ErrorLevel                  # エラーレベル
    category: ErrorCategory            # エラーカテゴリ
    user_message: str                  # ユーザー向けメッセージ
    solution: ErrorSolution            # 解決方法
    technical_details: Optional[str] = None  # 技術的詳細
    context: Optional[Dict[str, Any]] = None  # エラーコンテキスト
    
    def format_message(self, include_technical: bool = False) -> str:
        """フォーマット済みメッセージを取得"""
        message_parts = [
            f"[{self.error_code}] {self.user_message}"
        ]
        
        if include_technical and self.technical_details:
            message_parts.append(f"\n技術的詳細: {self.technical_details}")
        
        return "\n".join(message_parts)


class SmartSuggestions:
    """スマート提案システム"""
    
    # 有効なKumihan記法キーワード
    VALID_KEYWORDS = [
        "太字", "イタリック", "見出し1", "見出し2", "見出し3", "見出し4", "見出し5",
        "枠線", "ハイライト", "折りたたみ", "ネタバレ", "目次", "画像"
    ]
    
    # よくある間違いパターン
    COMMON_MISTAKES = {
        "太文字": "太字",
        "ボールド": "太字", 
        "bold": "太字",
        "強調": "太字",
        "見だし": "見出し1",
        "ヘッダー": "見出し1",
        "タイトル": "見出し1",
        "斜体": "イタリック",
        "italic": "イタリック",
        "線": "枠線",
        "ボックス": "枠線",
        "囲み": "枠線",
        "マーカー": "ハイライト",
        "highlight": "ハイライト",
        "蛍光ペン": "ハイライト",
        "コラプス": "折りたたみ",
        "アコーディオン": "折りたたみ",
        "隠す": "折りたたみ",
        "スポイラー": "ネタバレ",
        "spoiler": "ネタバレ",
        "隠し": "ネタバレ",
        "もくじ": "目次",
        "インデックス": "目次",
        "index": "目次",
        "pic": "画像",
        "img": "画像",
        "写真": "画像",
        "イメージ": "画像"
    }
    
    @classmethod
    def suggest_keyword(cls, invalid_keyword: str) -> List[str]:
        """無効なキーワードに対する提案を生成"""
        suggestions = []
        
        # 直接的な間違いパターンをチェック
        if invalid_keyword in cls.COMMON_MISTAKES:
            suggestions.append(cls.COMMON_MISTAKES[invalid_keyword])
        
        # 類似文字列検索
        close_matches = difflib.get_close_matches(
            invalid_keyword, 
            cls.VALID_KEYWORDS, 
            n=3, 
            cutoff=0.6
        )
        suggestions.extend(close_matches)
        
        # 重複除去して返す
        return list(dict.fromkeys(suggestions))
    
    @classmethod
    def suggest_file_encoding(cls, file_path: Path) -> List[str]:
        """ファイルエンコーディングエラーの提案"""
        suggestions = []
        
        if platform.system() == "Windows":
            suggestions.extend([
                "メモ帳で開いて「ファイル > 名前を付けて保存」で文字コードを「UTF-8」に変更",
                "サクラエディタで文字コード変換機能を使用",
                "VSCodeで「文字エンコーディングの変更」を選択"
            ])
        elif platform.system() == "Darwin":  # macOS
            suggestions.extend([
                "テキストエディットで「フォーマット > プレーンテキストにする」後、UTF-8で保存",
                "VSCodeで「文字エンコーディングの変更」を選択",
                "CotEditorで文字エンコーディングを変更"
            ])
        else:  # Linux
            suggestions.extend([
                "nkfコマンドでエンコーディング変換: nkf -w --overwrite ファイル名",
                "VSCodeで「文字エンコーディングの変更」を選択",
                "geditで「ファイル > 名前を付けて保存」で文字エンコーディングを指定"
            ])
        
        return suggestions


class ErrorCatalog:
    """エラーカタログ - 定義済みエラーパターン"""
    
    @staticmethod
    def create_file_not_found_error(file_path: str) -> UserFriendlyError:
        """ファイル未発見エラー"""
        return UserFriendlyError(
            error_code="E001",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📁 ファイル '{file_path}' が見つかりません",
            solution=ErrorSolution(
                quick_fix="ファイル名とパスを確認してください",
                detailed_steps=[
                    "1. ファイル名のスペルミスがないか確認",
                    "2. ファイルが正しい場所に保存されているか確認",
                    "3. 拡張子が .txt になっているか確認",
                    "4. ファイルが他のアプリケーションで開かれていないか確認"
                ],
                alternative_approaches=[
                    "ファイルをKumihan-Formatterのフォルダにコピーして再実行",
                    "フルパス（絶対パス）で指定して実行"
                ]
            ),
            context={"file_path": file_path}
        )
    
    @staticmethod
    def create_encoding_error(file_path: str) -> UserFriendlyError:
        """エンコーディングエラー"""
        suggestions = SmartSuggestions.suggest_file_encoding(Path(file_path))
        
        return UserFriendlyError(
            error_code="E002",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.ENCODING,
            user_message=f"📝 文字化けを検出しました（ファイル: {Path(file_path).name}）",
            solution=ErrorSolution(
                quick_fix="テキストファイルをUTF-8形式で保存し直してください",
                detailed_steps=suggestions[:3] if suggestions else [
                    "テキストエディタでファイルを開く",
                    "文字エンコーディングをUTF-8に変更して保存",
                    "再度変換を実行"
                ],
                external_links=[
                    "UTF-8とは: https://ja.wikipedia.org/wiki/UTF-8"
                ]
            ),
            context={"file_path": file_path}
        )
    
    @staticmethod
    def create_syntax_error(line_num: int, invalid_content: str, file_path: str = None) -> UserFriendlyError:
        """記法エラー"""
        suggestions = SmartSuggestions.suggest_keyword(invalid_content.strip(';'))
        
        suggestion_text = ""
        if suggestions:
            suggestion_text = f"もしかして: {', '.join(suggestions[:3])}"
        
        return UserFriendlyError(
            error_code="E003",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.SYNTAX,
            user_message=f"✏️ {line_num}行目: 記法エラーを検出しました",
            solution=ErrorSolution(
                quick_fix=suggestion_text if suggestion_text else "Kumihan記法ガイドを確認してください",
                detailed_steps=[
                    "1. マーカーは ;;; で開始し、;;; で終了する必要があります",
                    "2. マーカーは行頭に記述してください",
                    "3. 有効なキーワードを使用してください",
                    "4. 複合記法の場合は + で連結してください"
                ],
                external_links=[
                    "記法ガイド: SPEC.md を参照"
                ]
            ),
            context={
                "line_number": line_num,
                "invalid_content": invalid_content,
                "file_path": file_path,
                "suggestions": suggestions
            }
        )
    
    @staticmethod
    def create_permission_error(file_path: str, operation: str = "アクセス") -> UserFriendlyError:
        """権限エラー"""
        return UserFriendlyError(
            error_code="E004",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.PERMISSION,
            user_message=f"🔒 ファイルに{operation}できません（権限エラー）",
            solution=ErrorSolution(
                quick_fix="ファイルが他のアプリケーションで開かれていないか確認してください",
                detailed_steps=[
                    "1. ファイルを開いているアプリケーションをすべて閉じる",
                    "2. ファイルの読み取り専用属性を確認・解除",
                    "3. 管理者権限で実行を試す",
                    "4. ファイルを別の場所にコピーして実行"
                ],
                alternative_approaches=[
                    "ファイルをデスクトップにコピーして変換",
                    "別名でファイルを保存して再実行"
                ]
            ),
            context={"file_path": file_path, "operation": operation}
        )
    
    @staticmethod
    def create_empty_file_error(file_path: str) -> UserFriendlyError:
        """空ファイルエラー"""
        return UserFriendlyError(
            error_code="E005",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📄 ファイルが空です（ファイル: {Path(file_path).name}）",
            solution=ErrorSolution(
                quick_fix="ファイルに変換したい内容を記述してください",
                detailed_steps=[
                    "1. テキストエディタでファイルを開く",
                    "2. 変換したい内容をKumihan記法で記述",
                    "3. UTF-8形式で保存",
                    "4. 再度変換を実行"
                ],
                external_links=[
                    "Kumihan記法の基本: SPEC.md を参照",
                    "サンプルファイル: examples/ フォルダを参照"
                ]
            ),
            context={"file_path": file_path}
        )
    
    @staticmethod
    def create_unknown_error(original_error: str, context: Dict[str, Any] = None) -> UserFriendlyError:
        """不明なエラー"""
        return UserFriendlyError(
            error_code="E999",
            level=ErrorLevel.CRITICAL,
            category=ErrorCategory.UNKNOWN,
            user_message="🚨 予期しないエラーが発生しました",
            solution=ErrorSolution(
                quick_fix="GitHubのIssueで詳細を報告してください",
                detailed_steps=[
                    "1. エラーメッセージの全文をコピー",
                    "2. 使用していたファイルと操作手順を記録",
                    "3. GitHubのIssueページで新しいIssueを作成",
                    "4. エラー詳細と再現手順を記載して投稿"
                ],
                external_links=[
                    "Issue報告: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues"
                ]
            ),
            technical_details=original_error,
            context=context or {}
        )


class ErrorHandler:
    """エラーハンドラ - 例外をユーザーフレンドリーエラーに変換"""
    
    def __init__(self, console_ui=None):
        """エラーハンドラを初期化"""
        self.console_ui = console_ui
        self._error_history: List[UserFriendlyError] = []
    
    def handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> UserFriendlyError:
        """例外をユーザーフレンドリーエラーに変換"""
        context = context or {}
        
        # ファイル関連エラー
        if isinstance(exception, FileNotFoundError):
            file_path = context.get('file_path', str(exception))
            return ErrorCatalog.create_file_not_found_error(file_path)
        
        # エンコーディングエラー
        elif isinstance(exception, UnicodeDecodeError):
            file_path = context.get('file_path', '不明なファイル')
            return ErrorCatalog.create_encoding_error(file_path)
        
        # 権限エラー
        elif isinstance(exception, PermissionError):
            file_path = context.get('file_path', str(exception))
            operation = context.get('operation', 'アクセス')
            return ErrorCatalog.create_permission_error(file_path, operation)
        
        # その他の例外
        else:
            return ErrorCatalog.create_unknown_error(
                original_error=str(exception),
                context=context
            )
    
    def display_error(self, error: UserFriendlyError, verbose: bool = False) -> None:
        """エラーを画面に表示"""
        if not self.console_ui:
            print(f"[{error.error_code}] {error.user_message}")
            print(f"解決方法: {error.solution.quick_fix}")
            return
        
        # エラーレベル別の表示スタイル
        level_styles = {
            ErrorLevel.INFO: "blue",
            ErrorLevel.WARNING: "yellow", 
            ErrorLevel.ERROR: "red",
            ErrorLevel.CRITICAL: "red on yellow"
        }
        
        style = level_styles.get(error.level, "red")
        
        # メインメッセージ
        self.console_ui.console.print(f"[{style}][エラー] {error.user_message}[/{style}]")
        
        # 解決方法
        self.console_ui.console.print(f"[green]💡 解決方法: {error.solution.quick_fix}[/green]")
        
        # 詳細な手順（verboseモード）
        if verbose and error.solution.detailed_steps:
            self.console_ui.console.print("\n[cyan]詳細な解決手順:[/cyan]")
            for step in error.solution.detailed_steps:
                self.console_ui.console.print(f"[dim]   {step}[/dim]")
        
        # 代替手段
        if error.solution.alternative_approaches:
            self.console_ui.console.print("\n[yellow]代替手段:[/yellow]")
            for approach in error.solution.alternative_approaches:
                self.console_ui.console.print(f"[dim]   • {approach}[/dim]")
        
        # 技術的詳細（verboseモード）
        if verbose and error.technical_details:
            self.console_ui.console.print(f"\n[dim]技術的詳細: {error.technical_details}[/dim]")
        
        # エラー履歴に追加
        self._error_history.append(error)
    
    def show_error_context(self, file_path: Path, line_number: int, error_line: str) -> None:
        """エラー箇所の前後コンテキストを表示"""
        if not self.console_ui:
            return
        
        try:
            lines = file_path.read_text(encoding='utf-8').splitlines()
            
            self.console_ui.console.print("\n[red]📍 エラー発生箇所:[/red]")
            
            # 前後2行を表示
            start_line = max(0, line_number - 3)
            end_line = min(len(lines), line_number + 2)
            
            for i in range(start_line, end_line):
                line_content = lines[i] if i < len(lines) else ""
                line_num_display = i + 1
                
                if i == line_number - 1:  # エラー行
                    self.console_ui.console.print(f"[red]→ {line_num_display:3d}: {line_content}[/red]")
                else:
                    self.console_ui.console.print(f"[dim]  {line_num_display:3d}: {line_content}[/dim]")
        
        except Exception:
            # ファイル読み込みでエラーが発生した場合はスキップ
            pass
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        if not self._error_history:
            return {}
        
        categories = {}
        levels = {}
        
        for error in self._error_history:
            categories[error.category.value] = categories.get(error.category.value, 0) + 1
            levels[error.level.value] = levels.get(error.level.value, 0) + 1
        
        return {
            "total_errors": len(self._error_history),
            "by_category": categories,
            "by_level": levels,
            "most_recent": self._error_history[-1].error_code if self._error_history else None
        }


# 便利な関数群
def create_syntax_error_from_validation(validation_error, file_path: str = None) -> UserFriendlyError:
    """バリデーションエラーからユーザーフレンドリーエラーを作成"""
    if hasattr(validation_error, 'line_number') and hasattr(validation_error, 'message'):
        return ErrorCatalog.create_syntax_error(
            line_num=validation_error.line_number,
            invalid_content=validation_error.message,
            file_path=file_path
        )
    
    return ErrorCatalog.create_unknown_error(str(validation_error))


def format_file_size_error(file_path: str, size_mb: float, max_size_mb: float = 10) -> UserFriendlyError:
    """ファイルサイズエラーをフォーマット"""
    return UserFriendlyError(
        error_code="E006",
        level=ErrorLevel.WARNING,
        category=ErrorCategory.FILE_SYSTEM,
        user_message=f"📊 ファイルサイズが大きすぎます（{size_mb:.1f}MB > {max_size_mb}MB）",
        solution=ErrorSolution(
            quick_fix="ファイルサイズを小さくするか、分割してください",
            detailed_steps=[
                "1. ファイルを複数の小さなファイルに分割",
                "2. 不要な内容を削除",
                "3. 画像参照がある場合は画像ファイルサイズを縮小",
                "4. 分割したファイルを個別に変換"
            ]
        ),
        context={"file_path": file_path, "size_mb": size_mb, "max_size_mb": max_size_mb}
    )