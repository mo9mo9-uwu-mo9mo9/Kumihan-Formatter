"""
プログレス管理システムのテスト (Issue #695対応)

ProgressManagerとProgressContextManagerの動作を検証
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

from kumihan_formatter.core.utilities.progress_manager import (
    ProgressManager,
    ProgressContextManager,
    ProgressState,
)


class TestProgressState:
    """ProgressStateのテスト"""

    def test_progress_percent_calculation(self):
        """進捗率計算のテスト"""
        state = ProgressState(current=25, total=100)
        assert state.progress_percent == 25.0

        # ゼロ除算エラーの回避
        state = ProgressState(current=0, total=0)
        assert state.progress_percent == 100.0

        # 100%を超えない
        state = ProgressState(current=150, total=100)
        assert state.progress_percent == 100.0

    def test_eta_calculation(self):
        """ETA計算のテスト"""
        state = ProgressState(current=25, total=100, processing_rate=10.0)
        assert state.eta_seconds == 7  # (100-25)/10 = 7.5 -> 7

        # 処理速度が0の場合
        state = ProgressState(current=25, total=100, processing_rate=0.0)
        assert state.eta_seconds == 0

        # 完了済みの場合
        state = ProgressState(current=100, total=100, processing_rate=10.0)
        assert state.eta_seconds == 0

    def test_eta_formatted(self):
        """フォーマット済みETA文字列のテスト"""
        # 秒
        state = ProgressState(current=25, total=100, processing_rate=5.0)
        assert "秒" in state.eta_formatted

        # 分
        state = ProgressState(current=25, total=100, processing_rate=1.0)
        eta_str = state.eta_formatted
        assert "分" in eta_str or "時間" in eta_str

        # 完了間近
        state = ProgressState(current=100, total=100, processing_rate=10.0)
        assert state.eta_formatted == "完了間近"


class TestProgressManager:
    """ProgressManagerのテスト"""

    def test_initialization(self):
        """初期化のテスト"""
        pm = ProgressManager("テストタスク")
        assert pm.task_name == "テストタスク"
        assert pm.state.current == 0
        assert pm.state.total == 0
        assert not pm.is_cancelled()

    def test_start_and_update(self):
        """開始・更新のテスト"""
        pm = ProgressManager("テストタスク")
        pm.start(100, "開始ステージ")

        assert pm.state.total == 100
        assert pm.state.stage == "開始ステージ"

        # 更新テスト
        result = pm.update(25, "進行中")
        assert result is True
        assert pm.state.current == 25
        assert pm.state.substage == "進行中"

    def test_cancellation(self):
        """キャンセル機能のテスト"""
        pm = ProgressManager("テストタスク")
        pm.start(100)

        # キャンセル前
        assert not pm.is_cancelled()
        assert pm.update(25) is True

        # キャンセル実行
        pm.cancel("テストキャンセル")
        assert pm.is_cancelled()
        assert pm.update(50) is False  # キャンセル後は更新失敗

    def test_error_warning_tracking(self):
        """エラー・警告追跡のテスト"""
        pm = ProgressManager("テストタスク")
        pm.start(100)

        # エラー追加
        pm.add_error("テストエラー1")
        pm.add_error("テストエラー2")
        assert pm.state.errors_count == 2

        # 警告追加
        pm.add_warning("テスト警告1")
        assert pm.state.warnings_count == 1

    def test_progress_callback(self):
        """プログレスコールバックのテスト"""
        pm = ProgressManager("テストタスク")
        callback_calls = []

        def test_callback(state: ProgressState):
            callback_calls.append(state.current)

        pm.set_progress_callback(test_callback)
        pm.start(100)

        # 初期コールバック
        assert len(callback_calls) >= 1
        
        # UPDATE_INTERVAL を短縮して確実に更新されるようにする
        pm.UPDATE_INTERVAL = 0.0  # 即座に更新
        pm.update(50)
        
        # コールバックが呼ばれているかチェック（値は更新頻度に依存）
        assert len(callback_calls) >= 2

    def test_processing_rate_calculation(self):
        """処理速度計算のテスト"""
        pm = ProgressManager("テストタスク")
        pm.start(100)

        # 時間をおいて更新
        pm.update(10)
        time.sleep(0.1)
        pm.update(20)

        # 処理速度が計算されている
        assert pm.state.processing_rate >= 0

    def test_summary_generation(self):
        """サマリー生成のテスト"""
        pm = ProgressManager("テストタスク")
        pm.start(100, "テストステージ")
        pm.update(50, "進行中")
        pm.add_error("テストエラー")
        pm.add_warning("テスト警告")

        summary = pm.get_summary()

        assert summary["task_name"] == "テストタスク"
        assert summary["current"] == 50
        assert summary["total"] == 100
        assert summary["progress_percent"] == 50.0
        assert summary["stage"] == "テストステージ"
        assert summary["substage"] == "進行中"
        assert summary["errors_count"] == 1
        assert summary["warnings_count"] == 1
        assert "elapsed_time" in summary
        assert "eta_seconds" in summary


class TestProgressContextManager:
    """ProgressContextManagerのテスト"""

    def test_context_manager_basic(self):
        """基本的なコンテキストマネージャー機能のテスト"""
        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
        ) as progress:
            assert progress.task_name == "テストタスク"
            assert progress.total_items == 100
            assert not progress.is_cancelled()

            # 更新テスト
            result = progress.update(25, "テストステージ")
            assert result is True

    def test_verbosity_levels(self):
        """詳細度レベルのテスト"""
        # サイレントモード
        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
        ) as progress:
            assert progress.verbosity == ProgressContextManager.VerbosityLevel.SILENT
            assert progress.rich_progress is None

        # 詳細モード（Richが利用できない環境での安全なテスト）
        with patch(
            "kumihan_formatter.core.utilities.progress_manager.ProgressContextManager._setup_rich_progress"
        ):
            with ProgressContextManager(
                "テストタスク",
                total_items=100,
                verbosity=ProgressContextManager.VerbosityLevel.DETAILED,
            ) as progress:
                assert (
                    progress.verbosity == ProgressContextManager.VerbosityLevel.DETAILED
                )

    def test_cancellation_handling(self):
        """キャンセル処理のテスト"""
        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
            enable_cancellation=True,
        ) as progress:
            assert not progress.is_cancelled()

            # キャンセル要求
            progress.request_cancellation("テストキャンセル")
            assert progress.is_cancelled()

            # キャンセル後の更新は失敗
            result = progress.update(50)
            assert result is False

    def test_error_warning_tracking_in_context(self):
        """コンテキストマネージャーでのエラー・警告追跡"""
        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
        ) as progress:
            progress.add_error("テストエラー")
            progress.add_warning("テスト警告")

            stats = progress.get_stats()
            assert stats["errors_count"] == 1
            assert stats["warnings_count"] == 1

    def test_cleanup_callbacks(self):
        """クリーンアップコールバックのテスト"""
        cleanup_called = False

        def cleanup_callback():
            nonlocal cleanup_called
            cleanup_called = True

        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
        ) as progress:
            progress.add_cleanup_callback(cleanup_callback)

        # コンテキスト終了時にクリーンアップが呼ばれる
        assert cleanup_called

    def test_exception_handling(self):
        """例外処理のテスト"""
        try:
            with ProgressContextManager(
                "テストタスク",
                total_items=100,
                verbosity=ProgressContextManager.VerbosityLevel.SILENT,
            ) as progress:
                progress.update(25)
                raise ValueError("テスト例外")
        except ValueError:
            pass  # 例外は正常に伝播

        # プログレスマネージャーは適切に終了処理されている
        # （実際の検証は統合テストで行う）

    def test_stats_collection(self):
        """統計情報収集のテスト"""
        with ProgressContextManager(
            "テストタスク",
            total_items=100,
            verbosity=ProgressContextManager.VerbosityLevel.SILENT,
        ) as progress:
            progress.update(25, "ステージ1")
            progress.update(50, "ステージ2")
            progress.add_error("エラー1")

            stats = progress.get_stats()

            assert stats["task_name"] == "テストタスク"
            assert stats["verbosity"] == "SILENT"
            assert stats["stages_completed"] >= 1  # ステージ変更が記録される
            assert stats["errors_count"] == 1
            assert "elapsed_time" in stats


if __name__ == "__main__":
    pytest.main([__file__])
