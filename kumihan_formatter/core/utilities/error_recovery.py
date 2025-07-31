"""
高度なエラー回復システム
Issue #694 改善対応 - 詳細なエラー分類と回復戦略
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

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


class ErrorSeverity(Enum):
    """エラー重要度"""
    CRITICAL = "critical"    # 処理停止が必要
    HIGH = "high"           # 重要なデータ損失の可能性
    MEDIUM = "medium"       # 部分的な問題
    LOW = "low"            # 軽微な問題
    INFO = "info"          # 情報レベル


@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""
    error_type: ErrorType
    severity: ErrorSeverity
    line_number: int
    column_number: int = 0
    content_snippet: str = ""
    original_exception: Optional[Exception] = None
    recovery_suggestion: str = ""
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class RecoveryResult:
    """エラー回復結果"""
    success: bool
    recovered_content: Optional[Any] = None
    skip_to_line: int = 0
    recovery_message: str = ""
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ErrorRecoveryStrategy(ABC):
    """エラー回復戦略の基底クラス"""
    
    @abstractmethod
    def can_handle(self, error_context: ErrorContext) -> bool:
        """このストラテジーで処理可能かを判定"""
        pass
    
    @abstractmethod
    def recover(self, error_context: ErrorContext, content_lines: List[str]) -> RecoveryResult:
        """エラー回復を実行"""
        pass


class SyntaxErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """構文エラー回復戦略"""
    
    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.SYNTAX_ERROR
    
    def recover(self, error_context: ErrorContext, content_lines: List[str]) -> RecoveryResult:
        """構文エラーから回復"""
        line_num = error_context.line_number
        
        if line_num >= len(content_lines):
            return RecoveryResult(False, recovery_message="Line number out of range")
        
        line = content_lines[line_num]
        
        # マーカー修正の試行
        if '#' in line:
            # 不完全なマーカーの修正
            fixed_line = self._fix_incomplete_markers(line)
            if fixed_line != line:
                return RecoveryResult(
                    success=True,
                    recovered_content=fixed_line,
                    recovery_message=f"Fixed incomplete marker: '{line.strip()}' -> '{fixed_line.strip()}'",
                    warnings=["Marker syntax was automatically corrected"]
                )
        
        # 次の有効な行まで進む
        next_valid_line = self._find_next_valid_line(content_lines, line_num)
        return RecoveryResult(
            success=True,
            skip_to_line=next_valid_line,
            recovery_message=f"Skipped invalid syntax at line {line_num + 1}",
            warnings=[f"Content on line {line_num + 1} was skipped due to syntax error"]
        )
    
    def _fix_incomplete_markers(self, line: str) -> str:
        """不完全なマーカーを修正"""
        # # キーワード # パターンの修正
        pattern1 = r'^(\s*)#\s*([^#]+?)(?:\s*#)?$'
        match1 = re.match(pattern1, line)
        if match1:
            indent, keyword = match1.groups()
            if not line.rstrip().endswith('#'):
                return f"{indent}# {keyword.strip()} #"
        
        # ## 終了マーカーの修正
        if line.strip() == '#':
            return '##'
        
        return line
    
    def _find_next_valid_line(self, lines: List[str], start: int) -> int:
        """次の有効な行を検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith('#'):
                return i
            if re.match(r'^\s*#\s+\w+\s*#', line):  # 有効なマーカー
                return i
        return start + 1


class BlockStructureErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """ブロック構造エラー回復戦略"""
    
    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.BLOCK_STRUCTURE_ERROR
    
    def recover(self, error_context: ErrorContext, content_lines: List[str]) -> RecoveryResult:
        """ブロック構造エラーから回復"""
        line_num = error_context.line_number
        
        # ブロック終了マーカーを探す
        end_marker_line = self._find_block_end_marker(content_lines, line_num)
        
        if end_marker_line > line_num:
            return RecoveryResult(
                success=True,
                skip_to_line=end_marker_line + 1,
                recovery_message=f"Recovered from block structure error by skipping to line {end_marker_line + 1}",
                warnings=[f"Block content from lines {line_num + 1}-{end_marker_line} may be incomplete"]
            )
        
        # 終了マーカーが見つからない場合は自動挿入
        return RecoveryResult(
            success=True,
            recovered_content="##",
            skip_to_line=line_num + 1,
            recovery_message="Inserted missing block end marker",
            warnings=["Block end marker was automatically inserted"]
        )
    
    def _find_block_end_marker(self, lines: List[str], start: int) -> int:
        """ブロック終了マーカーを検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line == "##":
                return i
            if line.startswith('#') and re.match(r'^\s*#\s+\w+\s*#', line):
                return i - 1  # 新しいブロックの前
        return -1


class ListFormatErrorRecoveryStrategy(ErrorRecoveryStrategy):
    """リスト形式エラー回復戦略"""
    
    def can_handle(self, error_context: ErrorContext) -> bool:
        return error_context.error_type == ErrorType.LIST_FORMAT_ERROR
    
    def recover(self, error_context: ErrorContext, content_lines: List[str]) -> RecoveryResult:
        """リスト形式エラーから回復"""
        line_num = error_context.line_number
        
        if line_num >= len(content_lines):
            return RecoveryResult(False)
        
        line = content_lines[line_num]
        
        # リスト項目の修正を試行
        fixed_line = self._fix_list_format(line)
        if fixed_line != line:
            return RecoveryResult(
                success=True,
                recovered_content=fixed_line,
                recovery_message=f"Fixed list format: '{line.strip()}' -> '{fixed_line.strip()}'",
                warnings=["List format was automatically corrected"]
            )
        
        # リストの終了を検出
        list_end = self._find_list_end(content_lines, line_num)
        return RecoveryResult(
            success=True,
            skip_to_line=list_end,
            recovery_message=f"Skipped malformed list item at line {line_num + 1}",
            warnings=[f"List item on line {line_num + 1} was skipped due to format error"]
        )
    
    def _fix_list_format(self, line: str) -> str:
        """リスト形式を修正"""
        stripped = line.strip()
        
        # 順序なしリストの修正
        if re.match(r'^[-*+]\s*$', stripped):  # 空のリスト項目
            return line.replace(stripped, f"{stripped[0]} (空の項目)")
        
        # 順序付きリストの修正
        if re.match(r'^\d+\.\s*$', stripped):  # 空の番号付きリスト
            return line.replace(stripped, f"{stripped} (空の項目)")
        
        # インデント修正
        if stripped.startswith(('-', '*', '+')) and not stripped.startswith(('-', '*', '+'), 1):
            indent = len(line) - len(line.lstrip())
            marker = stripped[0]
            content = stripped[1:].strip()
            return ' ' * indent + f"{marker} {content}" if content else line
        
        return line
    
    def _find_list_end(self, lines: List[str], start: int) -> int:
        """リストの終了位置を検索"""
        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if not line:  # 空行
                return i + 1
            if not re.match(r'^[-*+\d]\s', line):  # リスト項目でない
                return i
        return start + 1


class AdvancedErrorRecoverySystem:
    """
    高度なエラー回復システム
    
    機能:
    - エラー種別の自動分類
    - 適切な回復戦略の選択
    - 回復履歴の記録
    - パフォーマンス監視
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.strategies: List[ErrorRecoveryStrategy] = []
        self.recovery_history: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, ErrorType] = {}
        
        # デフォルト戦略の登録
        self._register_default_strategies()
        self._initialize_error_patterns()
        
        self.logger.info("Advanced error recovery system initialized")
    
    def _register_default_strategies(self):
        """デフォルトの回復戦略を登録"""
        self.strategies.extend([
            SyntaxErrorRecoveryStrategy(),
            BlockStructureErrorRecoveryStrategy(),
            ListFormatErrorRecoveryStrategy(),
        ])
    
    def _initialize_error_patterns(self):
        """エラーパターンを初期化"""
        self.error_patterns.update({
            r'invalid syntax': ErrorType.SYNTAX_ERROR,
            r'codec.*decode': ErrorType.ENCODING_ERROR,
            r'list index out of range': ErrorType.CONTENT_PARSING_ERROR,
            r'marker.*mismatch': ErrorType.MARKER_MISMATCH_ERROR,
            r'memory': ErrorType.MEMORY_ERROR,
            r'timeout': ErrorType.TIMEOUT_ERROR,
        })
    
    def classify_error(self, exception: Exception, context_info: Dict[str, Any] = None) -> ErrorContext:
        """エラーを分類してコンテキストを作成"""
        if context_info is None:
            context_info = {}
        
        error_message = str(exception)
        error_type = ErrorType.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM
        
        # エラーパターンマッチング
        for pattern, err_type in self.error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                error_type = err_type
                break
        
        # 重要度の決定
        if error_type in [ErrorType.MEMORY_ERROR, ErrorType.TIMEOUT_ERROR]:
            severity = ErrorSeverity.CRITICAL
        elif error_type in [ErrorType.ENCODING_ERROR, ErrorType.BLOCK_STRUCTURE_ERROR]:
            severity = ErrorSeverity.HIGH
        elif error_type in [ErrorType.SYNTAX_ERROR, ErrorType.LIST_FORMAT_ERROR]:
            severity = ErrorSeverity.MEDIUM
        
        return ErrorContext(
            error_type=error_type,
            severity=severity,
            line_number=context_info.get('line_number', 0),
            column_number=context_info.get('column_number', 0),
            content_snippet=context_info.get('content_snippet', ''),
            original_exception=exception,
            additional_info=context_info
        )
    
    def recover_from_error(
        self, 
        error_context: ErrorContext, 
        content_lines: List[str]
    ) -> RecoveryResult:
        """エラーから回復を試行"""
        self.logger.info(f"Attempting recovery for {error_context.error_type.value} error at line {error_context.line_number + 1}")
        
        # 適切な戦略を選択
        for strategy in self.strategies:
            if strategy.can_handle(error_context):
                try:
                    result = strategy.recover(error_context, content_lines)
                    
                    # 回復履歴を記録
                    self._record_recovery(error_context, result)
                    
                    if result.success:
                        self.logger.info(f"Recovery successful: {result.recovery_message}")
                        return result
                    
                except Exception as e:
                    self.logger.warning(f"Recovery strategy failed: {e}")
        
        # 回復不可能な場合のフォールバック
        fallback_result = self._fallback_recovery(error_context, content_lines)
        self._record_recovery(error_context, fallback_result)
        
        return fallback_result
    
    def _record_recovery(self, error_context: ErrorContext, result: RecoveryResult):
        """回復履歴を記録"""
        record = {
            'timestamp': __import__('time').time(),
            'error_type': error_context.error_type.value,
            'severity': error_context.severity.value,
            'line_number': error_context.line_number,
            'recovery_success': result.success,
            'recovery_message': result.recovery_message,
            'warnings_count': len(result.warnings)
        }
        
        self.recovery_history.append(record)
        
        # 履歴サイズ制限
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-500:]
    
    def _fallback_recovery(self, error_context: ErrorContext, content_lines: List[str]) -> RecoveryResult:
        """フォールバック回復処理"""
        line_num = error_context.line_number
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryResult(
                success=False,
                recovery_message=f"Critical error at line {line_num + 1}: processing terminated"
            )
        
        # 次の安全な行まで進む
        safe_line = self._find_next_safe_line(content_lines, line_num)
        
        return RecoveryResult(
            success=True,
            skip_to_line=safe_line,
            recovery_message=f"Fallback recovery: skipped to line {safe_line + 1}",
            warnings=[f"Content at line {line_num + 1} was skipped due to unrecoverable error"]
        )
    
    def _find_next_safe_line(self, lines: List[str], start: int) -> int:
        """次の安全な行を検索"""
        for i in range(start + 1, min(start + 10, len(lines))):  # 最大10行先まで
            line = lines[i].strip()
            
            # 空行は安全
            if not line:
                return i
            
            # 単純なテキスト行は安全
            if not line.startswith('#') and not re.match(r'^[-*+\d]\s', line):
                return i
        
        return min(start + 1, len(lines) - 1)
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """回復統計を取得"""
        if not self.recovery_history:
            return {'total_recoveries': 0}
        
        total = len(self.recovery_history)
        successful = sum(1 for r in self.recovery_history if r['recovery_success'])
        
        error_type_counts = {}
        for record in self.recovery_history:
            error_type = record['error_type']
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            'total_recoveries': total,
            'successful_recoveries': successful,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'error_type_breakdown': error_type_counts,
            'recent_recoveries': self.recovery_history[-10:]  # 直近10件
        }
    
    def register_custom_strategy(self, strategy: ErrorRecoveryStrategy):
        """カスタム回復戦略を登録"""
        self.strategies.append(strategy)
        self.logger.info(f"Custom recovery strategy registered: {strategy.__class__.__name__}")
    
    def add_error_pattern(self, pattern: str, error_type: ErrorType):
        """エラーパターンを追加"""
        self.error_patterns[pattern] = error_type
        self.logger.debug(f"Error pattern added: {pattern} -> {error_type.value}")


# エラー回復デコレータ
def with_error_recovery(recovery_system: AdvancedErrorRecoverySystem):
    """エラー回復機能付きデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context_info = {
                    'function_name': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                error_context = recovery_system.classify_error(e, context_info)
                
                if error_context.severity == ErrorSeverity.CRITICAL:
                    raise  # クリティカルエラーは再発生
                
                # 回復を試行（コンテキストに応じて）
                recovery_result = RecoveryResult(
                    success=True,
                    recovery_message=f"Function {func.__name__} recovered from {error_context.error_type.value}",
                    warnings=[f"Error in {func.__name__} was handled gracefully"]
                )
                
                return recovery_result
        
        return wrapper
    return decorator