"""
高度なエラー回復システム
Issue #694 改善対応 - 詳細なエラー分類と回復戦略
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .logger import get_logger


class ErrorType(Enum):
    """エラー種別分類"""

    SYNTAX_ERROR = "syntax_error"
    ENCODING_ERROR = "encoding_error"
    BLOCK_STRUCTURE_ERROR = "block_structure_error"
    LIST_FORMAT_ERROR = "list_format_error"
    MARKER_MISMATCH_ERROR = "marker_mismatch_error"
    CONTENT_PARSING_ERROR = "content_parsing_error"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryErrorSeverity(Enum):
    """エラー復旧システム専用重要度"""

    CRITICAL = "critical"  # 処理停止が必要
    HIGH = "high"  # 重要なデータ損失の可能性
    MEDIUM = "medium"  # 部分的な問題
    LOW = "low"  # 軽微な問題
    INFO = "info"  # 情報レベル


@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""

    error_type: ErrorType
    severity: RecoveryErrorSeverity
    line_number: int
    column_number: int = 0
    content_snippet: str = ""
    original_exception: Optional[Exception] = None
    recovery_suggestion: str = ""
    additional_info: Dict[str, Any] | None = None  # Optional型に修正

    def __post_init__(self) -> None:
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class RecoveryResult:
    """エラー回復結果"""

    success: bool
    recovered_content: Optional[Any] = None
    skip_to_line: int = 0
    recovery_message: str = ""
    warnings: List[str] | None = None  # Optional型に修正

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


class ErrorRecoveryStrategy(ABC):
    """エラー回復戦略の基底クラス"""

    @abstractmethod
    def can_handle(self, error_context: ErrorContext) -> bool:
        """このストラテジーで処理可能かを判定"""
        pass

    @abstractmethod
    def recover(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """エラー回復を実行"""
        pass


class SyntaxErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """構文エラー回復戦略"""

    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.SYNTAX_ERROR

    def recover(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """構文エラーから回復"""
        line_num = error_context.line_number

        if line_num >= len(content_lines):
            return RecoveryResult(False, recovery_message="Line number out of range")

        # 基本的な構文エラー回復を試行
        try:
            line = content_lines[line_num]
            # 簡単な修復を試行
            fixed_line = line.strip()
            if fixed_line:
                return RecoveryResult(
                    success=True,
                    recovered_content=fixed_line,
                    recovery_message=f"Fixed line: '{line.strip()}' -> '{fixed_line}'",
                )
        except Exception:
            pass

        return RecoveryResult(False, recovery_message="Could not recover syntax error")

    def _fix_incomplete_markers(self, line: str) -> str:
        """不完全なマーカーを修正"""
        # # キーワード # パターンの修正
        pattern1 = r"^(\s*)#\s*([^#]+?)(?:\s*#)?$"
        match1 = re.match(pattern1, line)
        if match1:
            indent, keyword = match1.groups()
            if not line.rstrip().endswith("#"):
                return f"{indent}# {keyword.strip()} #"

        # 修正不可の場合は元の行を返す
        return line

    def _find_next_valid_line(self, lines: List[str], start: int) -> int:
        """次の有効な行を検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith("#"):
                return i

        # 有効な行が見つからない場合
        return len(lines)


class BlockStructureErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """ブロック構造エラー回復戦略"""

    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.BLOCK_STRUCTURE_ERROR

    def recover(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """ブロック構造エラーから回復"""
        line_num = error_context.line_number

        # ブロック終了マーカーを探す
        end_marker_line = self._find_block_end_marker(content_lines, line_num)

        if end_marker_line > line_num:
            return RecoveryResult(
                success=True,
                skip_to_line=end_marker_line + 1,
                recovery_message=(
                    f"Recovered from block structure error by skipping to line "
                    f"{end_marker_line + 1}"
                ),
                warnings=[
                    f"Block content from lines {line_num + 1}-{end_marker_line} may be incomplete"
                ],
            )

        # 終了マーカーが見つからない場合は自動挿入
        return RecoveryResult(
            success=True,
            recovered_content="##",
            skip_to_line=line_num + 1,
            recovery_message="Inserted missing block end marker",
            warnings=["Block end marker was automatically inserted"],
        )

    def _find_block_end_marker(self, lines: List[str], start: int) -> int:
        """ブロック終了マーカーを検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line == "##":
                return i

        # 終了マーカーが見つからない場合
        return -1


class ListFormatErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """リスト形式エラー回復戦略"""

    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.LIST_FORMAT_ERROR

    def recover(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """リスト形式エラーから回復"""
        line_num = error_context.line_number

        if line_num >= len(content_lines):
            return RecoveryResult(False)

        # 基本的なリスト形式修復
        try:
            line = content_lines[line_num]
            fixed_line = line.strip()
            if fixed_line:
                return RecoveryResult(
                    success=True,
                    recovered_content=fixed_line,
                    recovery_message=(
                        f"Fixed list format: '{line.strip()}' -> '{fixed_line.strip()}'"
                    ),
                    warnings=["List format was automatically corrected"],
                )
        except Exception:
            pass

        return RecoveryResult(False)

    def _fix_list_format(self, line: str) -> str:
        """リスト形式を修正"""
        stripped = line.strip()

        # 順序なしリストの修正
        if re.match(r"^[-*+]\s*$", stripped):  # 空のリスト項目
            return line.replace(stripped, f"{stripped[0]} (空の項目)")

        # 修正不可の場合は元の行を返す
        return line

    def _find_list_end(self, lines: List[str], start: int) -> int:
        """リストの終了位置を検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if not line:  # 空行
                return i + 1

        # リストの終了が見つからない場合
        return len(lines)


class AdvancedErrorRecoverySystem:
    """
    高度なエラー回復システム

    機能:
    - エラー種別の自動分類
    - 適切な回復戦略の選択
    - 回復履歴の記録
    - パフォーマンス監視
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.strategies: List[ErrorRecoveryStrategy] = []
        self.recovery_history: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, ErrorType] = {}

        # デフォルト戦略の登録
        self._register_default_strategies()
        self._initialize_error_patterns()

        self.logger.info("Advanced error recovery system initialized")

    def _register_default_strategies(self) -> None:
        """デフォルトの回復戦略を登録"""
        self.strategies.extend(
            [
                SyntaxErrorRecoveryStrategy(),
                BlockStructureErrorRecoveryStrategy(),
                ListFormatErrorRecoveryStrategy(),
            ]
        )

    def _initialize_error_patterns(self) -> None:
        """エラーパターンを初期化"""
        self.error_patterns.update(
            {
                r"invalid syntax": ErrorType.SYNTAX_ERROR,
                r"codec.*decode": ErrorType.ENCODING_ERROR,
                r"list index out of range": ErrorType.CONTENT_PARSING_ERROR,
                r"marker.*mismatch": ErrorType.MARKER_MISMATCH_ERROR,
                r"memory": ErrorType.MEMORY_ERROR,
                r"timeout": ErrorType.TIMEOUT_ERROR,
            }
        )

    def classify_error(
        self, exception: Exception, context_info: Dict[str, Any] | None = None
    ) -> ErrorContext:
        """エラーを分類してコンテキストを作成"""
        if context_info is None:
            context_info = {}

        error_message = str(exception)
        error_type = ErrorType.UNKNOWN_ERROR
        severity = RecoveryErrorSeverity.MEDIUM

        # エラーパターンマッチング
        for pattern, err_type in self.error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                error_type = err_type
                break

        # 重要度の決定
        if error_type in [ErrorType.MEMORY_ERROR, ErrorType.TIMEOUT_ERROR]:
            severity = RecoveryErrorSeverity.CRITICAL
        elif error_type in [ErrorType.ENCODING_ERROR, ErrorType.BLOCK_STRUCTURE_ERROR]:
            severity = RecoveryErrorSeverity.HIGH
        elif error_type in [ErrorType.SYNTAX_ERROR, ErrorType.LIST_FORMAT_ERROR]:
            severity = RecoveryErrorSeverity.MEDIUM

        return ErrorContext(
            error_type=error_type,
            severity=severity,
            line_number=context_info.get("line_number", 0),
            column_number=context_info.get("column_number", 0),
            content_snippet=context_info.get("content_snippet", ""),
            original_exception=exception,
            additional_info=context_info,
        )

    def recover_from_error(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """エラーから回復を試行"""
        self.logger.info(
            f"Attempting recovery for {error_context.error_type.value} error "
            f"at line {error_context.line_number + 1}"
        )

        # 適切な戦略を選択
        for strategy in self.strategies:
            if strategy.can_handle(error_context):
                try:
                    result = strategy.recover(error_context, content_lines)

                    # 回復履歴を記録
                    self._record_recovery(error_context, result)

                    if result.success:
                        self.logger.info(
                            f"Recovery successful: {result.recovery_message}"
                        )
                        return result
                except Exception as e:
                    self.logger.warning(f"Recovery strategy failed: {e}")
                    continue

        # すべての戦略が失敗した場合
        return RecoveryResult(
            success=False,
            recovery_message="All recovery strategies failed",
            warnings=["No suitable recovery strategy found"],
        )

    def _record_recovery(
        self, error_context: ErrorContext, result: RecoveryResult
    ) -> None:
        """回復履歴を記録"""
        record = {
            "timestamp": __import__("time").time(),
            "error_type": error_context.error_type.value,
            "severity": error_context.severity.value,
            "line_number": error_context.line_number,
            "recovery_success": result.success,
            "recovery_message": result.recovery_message,
            "warnings_count": len(result.warnings) if result.warnings else 0,
        }

        self.recovery_history.append(record)

        # 履歴サイズ制限
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-500:]

    def _fallback_recovery(
        self, error_context: ErrorContext, content_lines: List[str]
    ) -> RecoveryResult:
        """フォールバック回復処理"""
        line_num = error_context.line_number

        if error_context.severity == RecoveryErrorSeverity.CRITICAL:
            return RecoveryResult(
                success=False,
                recovery_message=f"Critical error at line {line_num + 1}: processing terminated",
            )

        # 次の安全な行まで進む
        safe_line = self._find_next_safe_line(content_lines, line_num)

        return RecoveryResult(
            success=True,
            skip_to_line=safe_line,
            recovery_message=f"Fallback recovery: skipped to line {safe_line + 1}",
            warnings=[
                f"Content at line {line_num + 1} was skipped due to unrecoverable error"
            ],
        )

    def _find_next_safe_line(self, lines: List[str], start: int) -> int:
        """次の安全な行を検索"""
        for i in range(start + 1, min(start + 10, len(lines))):  # 最大10行先まで
            line = lines[i].strip()

            # 空行は安全
            if not line:
                return i

        # 安全な行が見つからない場合は最後の行
        return len(lines)

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """回復統計を取得"""
        if not self.recovery_history:
            return {"total_recoveries": 0}

        return {
            "total_recoveries": len(self.recovery_history),
            "recovery_success_rate": self._calculate_success_rate(),
            "most_common_errors": self._get_common_errors(),
            "recovery_methods_used": self._get_recovery_methods_stats(),
        }

    def _calculate_success_rate(self) -> float:
        """
        回復成功率を計算

        Returns:
            float: 成功率 (0.0-1.0)
        """
        if not self.recovery_history:
            return 0.0

        successful_recoveries = sum(
            1 for entry in self.recovery_history if entry.get("success", False)
        )

        return successful_recoveries / len(self.recovery_history)

    def _get_common_errors(self) -> List[Tuple[str, int]]:
        """
        よく発生するエラーを取得

        Returns:
            List[Tuple[str, int]]: エラータイプと発生回数のリスト
        """
        from collections import Counter

        error_types = []
        for entry in self.recovery_history:
            if "error_type" in entry:
                error_types.append(entry["error_type"])

        return Counter(error_types).most_common(5)

    def _get_recovery_methods_stats(self) -> Dict[str, int]:
        """
        使用された回復手法の統計を取得

        Returns:
            Dict[str, int]: 回復手法と使用回数
        """
        from collections import defaultdict

        method_stats: Dict[str, int] = defaultdict(int)
        for entry in self.recovery_history:
            if "recovery_method" in entry:
                method_stats[entry["recovery_method"]] += 1

        return dict(method_stats)

    def attempt_recovery(self, error_context: "ErrorContext") -> "RecoveryResult":
        """
        エラー回復を試行

        Args:
            error_context: エラーコンテキスト

        Returns:
            RecoveryResult: 回復結果
        """
        self.logger.info(f"Attempting recovery for error: {error_context.error_type}")

        for strategy in self.strategies:
            if strategy.can_handle(error_context):
                try:
                    result = strategy.recover(error_context, [])
                    if result and result.success:
                        # 回復成功を記録
                        self.recovery_history.append(
                            {
                                "timestamp": self._get_timestamp(),
                                "error_type": error_context.error_type.value,
                                "recovery_method": strategy.__class__.__name__,
                                "success": True,
                            }
                        )
                        self.logger.info(
                            f"Recovery successful using {strategy.__class__.__name__}"
                        )
                        return result
                except Exception as e:
                    self.logger.warning(
                        f"Recovery strategy {strategy.__class__.__name__} failed: {e}"
                    )
                    continue

        # 回復失敗を記録
        self.recovery_history.append(
            {
                "timestamp": self._get_timestamp(),
                "error_type": error_context.error_type.value,
                "success": False,
            }
        )

        # デフォルトの失敗結果を返す
        return RecoveryResult(success=False)

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        import datetime

        return datetime.datetime.now().isoformat()

    def register_custom_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """カスタム回復戦略を登録"""
        self.strategies.append(strategy)
        self.logger.info(
            f"Custom recovery strategy registered: {strategy.__class__.__name__}"
        )

    def add_error_pattern(self, pattern: str, error_type: ErrorType) -> None:
        """エラーパターンを追加"""
        self.error_patterns[pattern] = error_type
        self.logger.debug(f"Error pattern added: {pattern} -> {error_type.value}")


# エラー回復デコレータ
def with_error_recovery(
    recovery_system: AdvancedErrorRecoverySystem,
) -> Callable[..., Any]:
    """エラー回復機能付きデコレータ"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context_info = {
                    "function_name": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                error_context = recovery_system.classify_error(e, context_info)

                if error_context.severity == RecoveryErrorSeverity.CRITICAL:
                    raise  # クリティカルエラーは再発生

                # 回復戦略を実行
                recovery_result = recovery_system.attempt_recovery(error_context)

                if recovery_result.success:
                    return recovery_result.recovered_content
                else:
                    raise  # 回復失敗時は再発生

        return wrapper

    return decorator
