"""
エラー回復戦略 - Issue #401対応

エラー発生時の自動回復機能を提供し、
可能な限り処理を継続できるようにするシステム。
"""

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utilities.logger import get_logger
from .context_manager import ErrorContextManager
from .error_types import ErrorCategory, UserFriendlyError


class RecoveryStrategy(ABC):
    """回復戦略の基底クラス"""

    def __init__(self, name: str, priority: int = 5):
        """回復戦略を初期化

        Args:
            name: 戦略名
            priority: 優先度（1-10、小さいほど高優先度）
        """
        self.name = name
        self.priority = priority
        self.logger = get_logger(__name__)

    @abstractmethod
    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """このエラーを処理できるかチェック

        Args:
            error: 対象のエラー
            context: エラーコンテキスト

        Returns:
            bool: 処理可能な場合True
        """
        pass

    @abstractmethod
    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """回復を試行

        Args:
            error: 対象のエラー
            context: エラーコンテキスト

        Returns:
            Tuple[bool, Optional[str]]: (成功フラグ, メッセージ)
        """
        pass


class FileEncodingRecoveryStrategy(RecoveryStrategy):
    """ファイルエンコーディングエラーの回復戦略"""

    def __init__(self):
        super().__init__("FileEncodingRecovery", priority=2)
        self.encoding_candidates = [
            "utf-8",
            "shift_jis",
            "cp932",
            "euc-jp",
            "iso-2022-jp",
        ]

    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """エンコーディングエラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.ENCODING
            or "encoding" in error.error_code.lower()
            or "文字化け" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """エンコーディング自動検出・変換による回復"""
        file_path = context.get("file_path")
        if not file_path or not Path(file_path).exists():
            return False, "対象ファイルが見つかりません"

        self.logger.info(f"Attempting encoding recovery for: {file_path}")

        try:
            # 各エンコーディングで読み取りを試行
            for encoding in self.encoding_candidates:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()

                    # UTF-8で一時ファイルを作成
                    temp_file = Path(file_path).with_suffix(".utf8.tmp")
                    with open(temp_file, "w", encoding="utf-8") as f:
                        f.write(content)

                    # 元ファイルをバックアップ
                    backup_file = Path(file_path).with_suffix(".backup")
                    shutil.copy2(file_path, backup_file)

                    # UTF-8版で置き換え
                    shutil.move(str(temp_file), file_path)

                    self.logger.info(
                        f"Successfully converted {file_path} from {encoding} to UTF-8"
                    )
                    return (
                        True,
                        f"ファイルを{encoding}からUTF-8に自動変換しました（バックアップ: {backup_file.name}）",
                    )

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.warning(f"Failed to convert with {encoding}: {e}")
                    continue

            return False, "サポートされているエンコーディングでの読み取りに失敗しました"

        except Exception as e:
            self.logger.error(f"Encoding recovery failed: {e}")
            return False, f"エンコーディング回復に失敗: {str(e)}"


class FilePermissionRecoveryStrategy(RecoveryStrategy):
    """ファイル権限エラーの回復戦略"""

    def __init__(self):
        super().__init__("FilePermissionRecovery", priority=3)

    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """権限エラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.PERMISSION
            or "permission" in error.error_code.lower()
            or "権限" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """一時ファイルでの処理継続による回復"""
        file_path = context.get("file_path")
        if not file_path:
            return False, "対象ファイルが指定されていません"

        self.logger.info(f"Attempting permission recovery for: {file_path}")

        try:
            original_path = Path(file_path)

            # 一時ディレクトリに読み取り可能なコピーを作成
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / original_path.name

                try:
                    # ファイルコピーを試行
                    shutil.copy2(original_path, temp_file)

                    # 一時ファイルの権限を設定
                    temp_file.chmod(0o644)

                    # コンテキストを更新（後続処理で一時ファイルを使用）
                    context["original_file_path"] = file_path
                    context["file_path"] = str(temp_file)
                    context["temp_file_recovery"] = True

                    self.logger.info(f"Created temporary accessible copy: {temp_file}")
                    return True, f"一時ファイルでの処理を継続します: {temp_file.name}"

                except Exception as copy_error:
                    self.logger.warning(
                        f"Failed to create temporary copy: {copy_error}"
                    )

                    # 読み取り専用でもコンテンツが取得できるか試行
                    try:
                        content = original_path.read_text()
                        temp_file.write_text(content)

                        context["original_file_path"] = file_path
                        context["file_path"] = str(temp_file)
                        context["temp_file_recovery"] = True

                        return (
                            True,
                            f"読み取り専用モードで一時ファイルを作成しました: {temp_file.name}",
                        )

                    except Exception as read_error:
                        self.logger.error(f"Failed to read file content: {read_error}")
                        return False, "ファイルの読み取りに失敗しました"

        except Exception as e:
            self.logger.error(f"Permission recovery failed: {e}")
            return False, f"権限回復に失敗: {str(e)}"


class SyntaxErrorRecoveryStrategy(RecoveryStrategy):
    """構文エラーの回復戦略"""

    def __init__(self):
        super().__init__("SyntaxErrorRecovery", priority=4)
        # よくある修正パターン
        self.correction_patterns = {
            ";;;太字": ";;;太字;;;",
            ";;;見出し": ";;;見出し1;;;",
            ";;太字;;": ";;;太字;;;",
            ";;;;太字;;;;": ";;;太字;;;",
        }

    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """構文エラーを処理できるかチェック"""
        return (
            error.category == ErrorCategory.SYNTAX
            or "syntax" in error.error_code.lower()
            or "記法" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """構文エラーの自動修正による回復"""
        file_path = context.get("file_path")
        line_number = context.get("line_number")

        if not file_path or not line_number:
            return False, "エラー位置の特定に失敗しました"

        self.logger.info(f"Attempting syntax recovery for: {file_path}:{line_number}")

        try:
            path = Path(file_path)
            lines = path.read_text(encoding="utf-8").splitlines()

            if line_number > len(lines):
                return False, "行番号が範囲外です"

            error_line = lines[line_number - 1]
            original_line = error_line

            # 修正パターンを適用
            corrected = False
            for pattern, replacement in self.correction_patterns.items():
                if pattern in error_line:
                    error_line = error_line.replace(pattern, replacement)
                    corrected = True
                    break

            if not corrected:
                # 一般的な修正を試行
                error_line = self._apply_general_corrections(error_line)
                corrected = error_line != original_line

            if corrected:
                # バックアップを作成
                backup_path = path.with_suffix(".backup")
                if not backup_path.exists():
                    shutil.copy2(path, backup_path)

                # 修正版を保存
                lines[line_number - 1] = error_line
                path.write_text("\n".join(lines), encoding="utf-8")

                self.logger.info(
                    f"Applied syntax correction: '{original_line}' → '{error_line}'"
                )
                return (
                    True,
                    f"構文エラーを自動修正しました: {line_number}行目（バックアップ: {backup_path.name}）",
                )

            return False, "自動修正パターンが見つかりませんでした"

        except Exception as e:
            self.logger.error(f"Syntax recovery failed: {e}")
            return False, f"構文回復に失敗: {str(e)}"

    def _apply_general_corrections(self, line: str) -> str:
        """一般的な構文修正を適用"""
        corrected = line

        # マーカーの修正
        if ";;" in corrected and not corrected.count(";;;") >= 2:
            # ;;;の数を修正
            corrected = corrected.replace(";;", ";;;")

        # 開始マーカーのみの場合、終了マーカーを追加
        if corrected.count(";;;") == 1 and corrected.endswith(";;;"):
            # 単語の終端を探して終了マーカーを追加
            words = corrected.split()
            if len(words) >= 2:
                corrected = corrected + ";;;"

        return corrected


class FileNotFoundRecoveryStrategy(RecoveryStrategy):
    """ファイル未発見エラーの回復戦略"""

    def __init__(self):
        super().__init__("FileNotFoundRecovery", priority=3)

    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """ファイル未発見エラーを処理できるかチェック"""
        return error.category == ErrorCategory.FILE_SYSTEM and (
            "not found" in error.error_code.lower()
            or "見つかりません" in error.user_message
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """類似ファイル名の検索による回復"""
        file_path = context.get("file_path")
        if not file_path:
            return False, "対象ファイルパスが指定されていません"

        self.logger.info(f"Attempting file recovery for: {file_path}")

        try:
            path = Path(file_path)
            parent_dir = path.parent
            target_name = path.name

            if not parent_dir.exists():
                return False, "親ディレクトリが存在しません"

            # 類似ファイルを検索
            similar_files = self._find_similar_files(parent_dir, target_name)

            if similar_files:
                best_match = similar_files[0]

                # コンテキストを更新
                context["original_file_path"] = file_path
                context["file_path"] = str(best_match)
                context["file_recovery"] = True

                self.logger.info(f"Found similar file: {best_match}")
                return True, f"類似ファイルで処理を継続します: {best_match.name}"

            return False, "類似ファイルが見つかりませんでした"

        except Exception as e:
            self.logger.error(f"File recovery failed: {e}")
            return False, f"ファイル回復に失敗: {str(e)}"

    def _find_similar_files(self, directory: Path, target_name: str) -> List[Path]:
        """類似ファイル名を検索"""
        import difflib

        similar_files = []
        target_stem = Path(target_name).stem.lower()
        target_suffix = Path(target_name).suffix.lower()

        for file_path in directory.iterdir():
            if file_path.is_file():
                file_stem = file_path.stem.lower()
                file_suffix = file_path.suffix.lower()

                # 拡張子が同じまたは.txt
                if file_suffix == target_suffix or file_suffix == ".txt":
                    # ファイル名の類似度を計算
                    similarity = difflib.SequenceMatcher(
                        None, target_stem, file_stem
                    ).ratio()
                    if similarity > 0.6:  # 60%以上の類似度
                        similar_files.append((similarity, file_path))

        # 類似度でソート
        similar_files.sort(key=lambda x: x[0], reverse=True)
        return [file_path for _, file_path in similar_files[:3]]


class MemoryErrorRecoveryStrategy(RecoveryStrategy):
    """メモリ不足エラーの回復戦略"""

    def __init__(self):
        super().__init__("MemoryErrorRecovery", priority=1)

    def can_handle(self, error: UserFriendlyError, context: Dict[str, Any]) -> bool:
        """メモリエラーを処理できるかチェック"""
        return (
            "memory" in error.error_code.lower()
            or "メモリ" in error.user_message
            or isinstance(context.get("original_exception"), MemoryError)
        )

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """メモリ使用量の削減による回復"""
        self.logger.info("Attempting memory recovery")

        try:
            # ガベージコレクションを実行
            import gc

            collected = gc.collect()

            # ファイル分割処理の提案
            file_path = context.get("file_path")
            if file_path:
                path = Path(file_path)
                if path.exists():
                    file_size = path.stat().st_size
                    if file_size > 10 * 1024 * 1024:  # 10MB以上
                        context["suggest_file_split"] = True
                        return (
                            True,
                            f"メモリを解放しました（{collected}オブジェクト）。大きなファイルの分割処理を推奨します。",
                        )

            if collected > 0:
                return True, f"メモリを解放しました（{collected}オブジェクト）"

            return False, "メモリ回復効果がありませんでした"

        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")
            return False, f"メモリ回復に失敗: {str(e)}"


class RecoveryManager:
    """
    エラー回復管理システム

    設計ドキュメント:
    - Issue #401: エラーハンドリングの強化と統合
    - 複数の回復戦略を統合管理
    - 優先度ベースの回復試行

    機能:
    - 回復戦略の登録・管理
    - エラータイプ別の自動回復
    - 回復履歴の記録
    - 回復成功率の分析
    """

    def __init__(self, enable_logging: bool = True):
        """回復管理システムを初期化

        Args:
            enable_logging: ログ出力を有効にするか
        """
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

        # 回復戦略のリスト
        self.strategies: List[RecoveryStrategy] = []

        # 回復履歴
        self.recovery_history: List[Dict[str, Any]] = []

        # デフォルト戦略を登録
        self._register_default_strategies()

        if self.logger:
            self.logger.info("RecoveryManager initialized")

    def _register_default_strategies(self) -> None:
        """デフォルトの回復戦略を登録"""
        self.register_strategy(MemoryErrorRecoveryStrategy())
        self.register_strategy(FileEncodingRecoveryStrategy())
        self.register_strategy(FilePermissionRecoveryStrategy())
        self.register_strategy(FileNotFoundRecoveryStrategy())
        self.register_strategy(SyntaxErrorRecoveryStrategy())

    def register_strategy(self, strategy: RecoveryStrategy) -> None:
        """回復戦略を登録

        Args:
            strategy: 登録する回復戦略
        """
        self.strategies.append(strategy)
        # 優先度でソート（小さいほど高優先度）
        self.strategies.sort(key=lambda s: s.priority)

        if self.logger:
            self.logger.debug(f"Registered recovery strategy: {strategy.name}")

    def attempt_recovery(
        self, error: UserFriendlyError, context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """エラーからの回復を試行

        Args:
            error: 回復対象のエラー
            context: エラーコンテキスト

        Returns:
            Tuple[bool, List[str]]: (回復成功フラグ, 実行された回復操作のメッセージリスト)
        """
        recovery_messages = []

        if self.logger:
            self.logger.info(f"Attempting recovery for error: {error.error_code}")

        for strategy in self.strategies:
            if strategy.can_handle(error, context):
                try:
                    success, message = strategy.attempt_recovery(error, context)

                    # 回復履歴に記録
                    self.recovery_history.append(
                        {
                            "strategy": strategy.name,
                            "error_code": error.error_code,
                            "success": success,
                            "message": message,
                            "timestamp": str(context.get("timestamp", "unknown")),
                        }
                    )

                    if success:
                        if message:
                            recovery_messages.append(f"[{strategy.name}] {message}")

                        if self.logger:
                            self.logger.info(
                                f"Recovery successful with strategy: {strategy.name}"
                            )

                        return True, recovery_messages

                    elif message:
                        recovery_messages.append(f"[{strategy.name}] 失敗: {message}")

                except Exception as e:
                    error_msg = f"戦略実行エラー: {str(e)}"
                    recovery_messages.append(f"[{strategy.name}] {error_msg}")

                    if self.logger:
                        self.logger.error(
                            f"Recovery strategy {strategy.name} failed: {e}"
                        )

        if self.logger:
            self.logger.warning(
                f"All recovery strategies failed for error: {error.error_code}"
            )

        return False, recovery_messages

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """回復統計情報を取得

        Returns:
            Dict[str, Any]: 回復統計情報
        """
        if not self.recovery_history:
            return {"total_attempts": 0}

        total_attempts = len(self.recovery_history)
        successful_attempts = sum(
            1 for entry in self.recovery_history if entry["success"]
        )

        # 戦略別統計
        strategy_stats = {}
        for entry in self.recovery_history:
            strategy = entry["strategy"]
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"attempts": 0, "successes": 0}

            strategy_stats[strategy]["attempts"] += 1
            if entry["success"]:
                strategy_stats[strategy]["successes"] += 1

        # 成功率を計算
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = (
                stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0
            )

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "overall_success_rate": successful_attempts / total_attempts,
            "strategy_statistics": strategy_stats,
            "recent_recoveries": self.recovery_history[-10:],  # 最新10件
        }

    def clear_history(self) -> None:
        """回復履歴をクリア"""
        self.recovery_history.clear()

        if self.logger:
            self.logger.info("Recovery history cleared")


# グローバルインスタンス
_global_recovery_manager: Optional[RecoveryManager] = None


def get_global_recovery_manager() -> RecoveryManager:
    """グローバル回復管理システムを取得（遅延初期化）"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager()
    return _global_recovery_manager


def set_global_recovery_manager(manager: RecoveryManager) -> None:
    """グローバル回復管理システムを設定"""
    global _global_recovery_manager
    _global_recovery_manager = manager
