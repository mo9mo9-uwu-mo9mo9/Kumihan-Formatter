"""
大容量ファイル処理用プログレス管理システム
Issue #694対応 - ETA算出・キャンセル機能付きプログレス追跡
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Event
from typing import Any, Callable, Dict, List, Optional

from .logger import get_logger


@dataclass
class ProgressState:
    """プログレス状態を管理するデータクラス"""

    current: int = 0
    total: int = 0
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    estimated_total_time: float = 0.0
    processing_rate: float = 0.0  # items per second
    stage: str = "準備中"
    substage: str = ""
    errors_count: int = 0
    warnings_count: int = 0
    memory_mb: float = 0.0  # 現在のメモリ使用量（MB）
    @property
    def progress_percent(self) -> float:
        """進捗率を取得（0-100）"""
        if self.total == 0:
            return 100.0
        return min(100.0, (self.current / self.total) * 100)
    @property
    def elapsed_time(self) -> float:
        """経過時間（秒）"""
        return time.time() - self.start_time

    @property
    def eta_seconds(self) -> int:
        """推定残り時間（秒）"""
        if self.processing_rate <= 0 or self.current >= self.total:
            return 0

        remaining_items = self.total - self.current
        return int(remaining_items / self.processing_rate)

    @property
    def eta_formatted(self) -> str:
        """フォーマット済み推定残り時間"""
        eta = self.eta_seconds
        if eta <= 0:
            return "完了間近"
        elif eta < 60:
            return f"{eta}秒"
        elif eta < 3600:
            minutes = eta // 60
            seconds = eta % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}時間{minutes}分"


class ProgressManager:
    """
    大容量ファイル処理用の高度なプログレス管理システム

    機能:
    - リアルタイムETA算出
    - 処理速度監視
    - キャンセル機能
    - ステージ別プログレス追跡
    - エラー・警告カウント
    """

    UPDATE_INTERVAL = 0.1  # プログレス更新間隔（秒）- Issue #695要件準拠
    RATE_CALCULATION_WINDOW = 10  # 処理速度計算用のサンプル数

    def __init__(self, task_name: str = "処理中"):
        self.logger = get_logger(__name__)
        self.task_name = task_name
        self.state = ProgressState()
        self.cancelled = Event()

        # コールバック関数
        self.progress_callback: Optional[Callable[[ProgressState], None]] = None
        self.cancellation_callback: Optional[Callable[[], None]] = None

        # 処理速度計算用
        self._progress_history: list[tuple[float, int]] = (
            []
        )  # (timestamp, current_value)

        self.logger.debug(f"ProgressManager initialized for task: {task_name}")

    def start(self, total_items: int, stage: str = "開始"):
        """プログレス追跡を開始"""
        self.state = ProgressState(
            total=total_items,
            stage=stage,
            start_time=time.time(),
            last_update_time=time.time(),
        )
        self.cancelled.clear()
        self._progress_history.clear()

        self.logger.info(
            f"Progress tracking started: {total_items} items, stage: {stage}"
        )
        self._notify_progress()

    def update(self, current: int, substage: str = "") -> bool:
        """
        プログレスを更新
        
        Args:
            current: 現在の進捗値
            substage: サブステージ名
            
=======
            last_update_time=time.time(),
        )
        self.cancelled.clear()
        self._progress_history.clear()

        self.logger.info(
            f"Progress tracking started: {total_items} items, stage: {stage}"
        )
        self._notify_progress()

    def update(self, current: int, substage: str = "") -> bool:
        """
        プログレスを更新

        Args:
            current: 現在の進捗値
            substage: サブステージ名

        Returns:
            bool: 継続可能な場合True キャンセル時False
        """
        if self.cancelled.is_set():
            return False

        now = time.time()

        # 状態更新
        self.state.current = min(current, self.state.total)
        self.state.substage = substage

        # 処理速度計算
        self._update_processing_rate(now, current)

        # 定期的なプログレス通知
        if now - self.state.last_update_time >= self.UPDATE_INTERVAL:
            self.state.last_update_time = now
            self._notify_progress()

        return True

    def increment(self, amount: int = 1, substage: str = "") -> bool:
        """プログレスを増分更新"""
        return self.update(self.state.current + amount, substage)

    def set_stage(self, stage: str, substage: str = ""):
        """処理ステージを変更"""
        self.state.stage = stage
        self.state.substage = substage
        self.logger.info(f"Stage changed: {stage} - {substage}")
        self._notify_progress()

    def add_error(self, error_message: str = ""):
        """エラーカウントを増加"""
        self.state.errors_count += 1
        if error_message:
            self.logger.warning(f"Error recorded: {error_message}")
        self._notify_progress()

    def add_warning(self, warning_message: str = ""):
        """警告カウントを増加"""
        self.state.warnings_count += 1
        if warning_message:
            self.logger.info(f"Warning recorded: {warning_message}")
        self._notify_progress()

    def finish(self, final_stage: str = "完了"):
        """プログレス追跡を完了"""
        self.state.current = self.state.total
        self.state.stage = final_stage
        self.state.substage = ""

        elapsed = self.state.elapsed_time
        self.logger.info(
            f"Progress completed: {self.state.total} items in {elapsed:.2f}s, "
            f"{self.state.errors_count} errors, {self.state.warnings_count} warnings"
        )

        self._notify_progress()

    def cancel(self, reason: str = "ユーザー要求"):
        """処理をキャンセル"""
        self.cancelled.set()
        self.state.stage = "キャンセル中"
        self.logger.info(f"Progress cancelled: {reason}")

        if self.cancellation_callback:
            self.cancellation_callback()

        self._notify_progress()

    def is_cancelled(self) -> bool:
        """キャンセル状態を確認"""
        return self.cancelled.is_set()

    def set_progress_callback(self, callback: Callable[[ProgressState], None]):
        """プログレス更新コールバックを設定"""
        self.progress_callback = callback

    def set_cancellation_callback(self, callback: Callable[[], None]):
        """キャンセル時コールバックを設定"""
        self.cancellation_callback = callback

    def get_state(self) -> ProgressState:
        """現在のプログレス状態を取得"""
        return self.state

    def save_progress_log(self, filepath: str):
        """プログレス情報をJSONファイルに保存"""
        import json
        from pathlib import Path

        log_data = {
            "task_name": self.task_name,
            "summary": self.get_summary(),
            "history": [
                {"timestamp": t, "value": v, "elapsed_time": t - self.state.start_time}
                for t, v in self._progress_history
            ],
            "final_stats": {
                "total_time": self.state.elapsed_time,
                "completion_rate": self.state.progress_percent,
                "avg_processing_rate": self.state.processing_rate,
                "errors": self.state.errors_count,
                "warnings": self.state.warnings_count,
                "memory_peak_mb": self.state.memory_mb,
            },
        }

        try:
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Progress log saved to: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save progress log: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """プログレス概要を取得"""
        return {
            "task_name": self.task_name,
            "progress_percent": self.state.progress_percent,
            "current": self.state.current,
            "total": self.state.total,
            "elapsed_time": self.state.elapsed_time,
            "eta_seconds": self.state.eta_seconds,
            "eta_formatted": self.state.eta_formatted,
            "stage": self.state.stage,
            "substage": self.state.substage,
            "processing_rate": self.state.processing_rate,
            "errors_count": self.state.errors_count,
            "warnings_count": self.state.warnings_count,
            "memory_mb": self.state.memory_mb,
            "is_cancelled": self.is_cancelled(),
        }

    def _update_processing_rate(self, timestamp: float, current: int):
        """処理速度を更新"""
        # 履歴に追加
        self._progress_history.append((timestamp, current))

        # 古い履歴を削除（指定されたウィンドウサイズを維持）
        if len(self._progress_history) > self.RATE_CALCULATION_WINDOW:
            self._progress_history.pop(0)

        # 処理速度計算（最初と最後の2点から算出）
        if len(self._progress_history) >= 2:
            first_time, first_value = self._progress_history[0]
            last_time, last_value = self._progress_history[-1]

            time_diff = last_time - first_time
            value_diff = last_value - first_value

            if time_diff > 0:
                self.state.processing_rate = value_diff / time_diff
            else:
                self.state.processing_rate = 0.0

    def _update_memory_stats(self):
        """メモリ使用量を更新"""
        try:
            import psutil

            process = psutil.Process()
            self.state.memory_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            # psutilが利用できない場合は0のまま
            if not hasattr(self, "_psutil_warned"):
                self.logger.warning(
                    "psutil is not installed. Memory statistics will not be available. "
                    "Install with: pip install psutil"
                )
                self._psutil_warned = True
        except Exception as e:
            self.logger.debug(f"Memory stats update error: {e}")

    def _notify_progress(self):
        """プログレス更新を通知"""
        # メモリ統計を更新
        self._update_memory_stats()

        if self.progress_callback:
            try:
                self.progress_callback(self.state)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")


class ProgressContextManager:
    """
    高度なプログレス管理のためのコンテキストマネージャ

    Issue #695対応: より透明で対話的なファイル処理体験を提供
    - 多段階進捗追跡
    - 詳細レベル制御 (SILENT, MINIMAL, DETAILED, VERBOSE)
    - 高頻度更新 (100ミリ秒間隔)
    - ツールチップ・統計情報
    - 安全なキャンセル機能
    """

    class VerbosityLevel(Enum):
        SILENT = 0  # プログレス表示なし
        MINIMAL = 1  # 基本プログレスのみ
        DETAILED = 2  # 詳細統計付き (デフォルト)
        VERBOSE = 3  # 全情報表示

    def __init__(
        self,
        task_name: str,
        total_items: int,
        verbosity: "VerbosityLevel" = None,
        update_interval: float = 0.1,  # 100ms更新
        show_tooltips: bool = True,
        enable_eta: bool = True,
        enable_cancellation: bool = True,
        progress_style: str = "bar",
        progress_log: str | None = None,
    ):
        if verbosity is None:
            verbosity = self.VerbosityLevel.DETAILED

        self.task_name = task_name
        self.total_items = total_items
        self.verbosity = verbosity
        self.update_interval = update_interval
        self.show_tooltips = show_tooltips
        self.enable_eta = enable_eta
        self.enable_cancellation = enable_cancellation
        self.progress_style = progress_style
        self.progress_log = progress_log

        self.progress_manager: Optional[ProgressManager] = None
        self.rich_progress: Optional[Any] = None  # rich.Progress instance
        self.task_id: Optional[Any] = None
        self.logger = get_logger(__name__)

        # 統計情報
        self.start_time = time.time()
        self.stages_completed = 0
        self.last_tooltip_update = 0.0

        # キャンセル処理
        self._cancellation_requested = Event()
        self._cleanup_callbacks: List[Callable[[], None]] = []

    def __enter__(self) -> "ProgressContextManager":
        """コンテキスト開始"""
        if self.verbosity == self.VerbosityLevel.SILENT:
            # サイレントモード: ProgressManagerのみ使用
            self.progress_manager = ProgressManager(self.task_name)
            self.progress_manager.start(self.total_items)
            return self

        # Rich Progress表示設定
        self._setup_rich_progress()

        # ProgressManager設定
        self.progress_manager = ProgressManager(self.task_name)
        self.progress_manager.UPDATE_INTERVAL = self.update_interval
        self.progress_manager.start(self.total_items)

        # プログレスコールバック設定
        if self.rich_progress and self.task_id is not None:

            def update_callback(state: ProgressState):
                self._update_rich_display(state)

            self.progress_manager.set_progress_callback(update_callback)

        # キャンセル処理設定
        if self.enable_cancellation:
            self.progress_manager.set_cancellation_callback(self._handle_cancellation)

        self.logger.info(
            f"Progress context started: {self.task_name} ({self.total_items} items)"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了"""
        try:
            if self.progress_manager:
                if exc_type is not None:
                    # 例外発生時
                    self.progress_manager.add_error(f"Exception: {exc_type.__name__}")
                    self.progress_manager.cancel("例外により中断")
                else:
                    # 正常終了
                    self.progress_manager.finish("処理完了")

            # Rich Progress終了
            if self.rich_progress:
                if self.task_id is not None:
                    self.rich_progress.update(self.task_id, completed=100)
                self.rich_progress.stop()

            # クリーンアップコールバック実行
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Cleanup callback error: {e}")

            # プログレスログ保存
            if self.progress_log and self.progress_manager:
                try:
                    self.progress_manager.save_progress_log(self.progress_log)
                except Exception as e:
                    self.logger.error(f"Failed to save progress log: {e}")

            # 最終統計出力
            if self.verbosity.value >= self.VerbosityLevel.DETAILED.value:
                self._display_final_stats()

        except Exception as e:
            self.logger.error(f"Error during progress context cleanup: {e}")

    def update(self, current: int, stage: str = "", substage: str = "") -> bool:
        """
        プログレス更新

        Returns:
            bool: 継続可能な場合True キャンセル時False
        """
        if self._cancellation_requested.is_set():
            return False

        if self.progress_manager:
            success = self.progress_manager.update(current, substage)
            if stage and stage != self.progress_manager.state.stage:
                self.progress_manager.set_stage(stage, substage)
                self.stages_completed += 1

            return success

        return True

    def increment(self, amount: int = 1, stage: str = "", substage: str = "") -> bool:
        """プログレス増分更新"""
        if self.progress_manager:
            current = self.progress_manager.state.current + amount
            return self.update(current, stage, substage)
        return True

    def add_error(self, message: str = ""):
        """エラー追加"""
        if self.progress_manager:
            self.progress_manager.add_error(message)

    def add_warning(self, message: str = ""):
        """警告追加"""
        if self.progress_manager:
            self.progress_manager.add_warning(message)

    def request_cancellation(self, reason: str = "ユーザー要求"):
        """キャンセル要求"""
        self._cancellation_requested.set()
        if self.progress_manager:
            self.progress_manager.cancel(reason)

    def is_cancelled(self) -> bool:
        """キャンセル状態確認"""
        return self._cancellation_requested.is_set() or (
            self.progress_manager and self.progress_manager.is_cancelled()
        )

    def add_cleanup_callback(self, callback: Callable[[], None]):
        """クリーンアップコールバック追加"""
        self._cleanup_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """現在の統計情報取得"""
        base_stats = {
            "task_name": self.task_name,
            "verbosity": self.verbosity.name,
            "stages_completed": self.stages_completed,
            "elapsed_time": time.time() - self.start_time,
        }

        if self.progress_manager:
            base_stats.update(self.progress_manager.get_summary())

        return base_stats

    def _setup_rich_progress(self):
        """Rich Progress初期化"""
        try:
            from rich.console import Console
            from rich.progress import (
                BarColumn,
                Progress,
                SpinnerColumn,
                TaskProgressColumn,
                TextColumn,
                TimeElapsedColumn,
                TimeRemainingColumn,
            )

            # プログレススタイルと詳細度に応じてカラム構成を調整
            # スタイル別の基本カラム設定
            if self.progress_style == "spinner":
                columns = [SpinnerColumn(), TextColumn("[bold blue]{task.description}")]
            elif self.progress_style == "percentage":
                columns = [
                    TextColumn("[bold blue]{task.description}"),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ]
            else:  # bar (default)
                columns = [TextColumn("[bold blue]{task.description}")]
                if self.verbosity.value >= self.VerbosityLevel.MINIMAL.value:
                    columns.extend([BarColumn(), TaskProgressColumn()])

            # 詳細レベルに応じた追加カラム
            if self.verbosity.value >= self.VerbosityLevel.DETAILED.value:
                if self.enable_eta and self.progress_style != "percentage":
                    columns.append(TimeRemainingColumn())
                if self.progress_style != "percentage":
                    columns.append(TimeElapsedColumn())

            self.rich_progress = Progress(*columns, console=Console())
            self.rich_progress.start()

            # タスク追加
            description = self.task_name
            if self.verbosity.value >= self.VerbosityLevel.VERBOSE.value:
                description += f" ({self.total_items} items)"

            self.task_id = self.rich_progress.add_task(
                description, total=100  # パーセンテージベース
            )

        except ImportError:
            self.logger.warning(
                "Rich library not available, falling back to basic progress"
            )
            self.rich_progress = None
            self.task_id = None

    def _update_rich_display(self, state: ProgressState):
        """Rich Progress表示更新"""
        if not self.rich_progress or self.task_id is None:
            return

        try:
            # 基本プログレス更新
            self.rich_progress.update(
                self.task_id,
                completed=state.progress_percent,
                description=self._format_description(state),
            )

            # ツールチップ更新（VERBOSEモード時）
            if (
                self.verbosity == self.VerbosityLevel.VERBOSE
                and self.show_tooltips
                and time.time() - self.last_tooltip_update > 1.0
            ):  # 1秒間隔

                self._update_tooltip(state)
                self.last_tooltip_update = time.time()

        except Exception as e:
            self.logger.error(f"Rich display update error: {e}")

    def _format_description(self, state: ProgressState) -> str:
        """プログレス説明文フォーマット"""
        desc = self.task_name

        if self.verbosity.value >= self.VerbosityLevel.DETAILED.value:
            if state.stage:
                desc += f" - {state.stage}"
            if (
                state.substage
                and self.verbosity.value >= self.VerbosityLevel.VERBOSE.value
            ):
                desc += f" ({state.substage})"

        return desc

    def _update_tooltip(self, state: ProgressState):
        """ツールチップ情報更新"""
        if not self.show_tooltips:
            return

        tooltip_info = [
            f"処理速度: {state.processing_rate:.1f} items/sec",
            f"エラー: {state.errors_count}, 警告: {state.warnings_count}",
            f"段階: {self.stages_completed} 完了",
        ]

        # コンソールに追加情報出力（必要に応じて）
        self.logger.debug(" | ".join(tooltip_info))

    def _handle_cancellation(self):
        """キャンセル処理"""
        self.logger.info(f"Cancellation handling for task: {self.task_name}")

        # Rich Progress更新
        if self.rich_progress and self.task_id is not None:
            self.rich_progress.update(
                self.task_id, description=f"{self.task_name} - キャンセル中..."
            )

    def _display_final_stats(self):
        """最終統計表示"""
        if self.verbosity.value < self.VerbosityLevel.DETAILED.value:
            return

        stats = self.get_stats()

        self.logger.info(
            f"Task completed: {stats['task_name']} | "
            f"Progress: {stats.get('progress_percent', 0):.1f}% | "
            f"Time: {stats['elapsed_time']:.2f}s | "
            f"Errors: {stats.get('errors_count', 0)} | "
            f"Warnings: {stats.get('warnings_count', 0)} | "
            f"Stages: {stats['stages_completed']}"
        )


