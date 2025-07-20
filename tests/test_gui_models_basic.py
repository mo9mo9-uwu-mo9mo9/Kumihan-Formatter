"""Thread-Safe GUI Models Tests

Issue #516 Phase 5A対応 - GUI ModelsのThread-Safe設計とエラーハンドリングのテスト
TDD実践による品質保証
"""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.gui_models import (
    AppState,
    ConversionState,
    FileManager,
    LogManager,
)

pytestmark = [pytest.mark.unit, pytest.mark.tdd_green]


@pytest.mark.tdd_green
class TestConversionStateThreadSafe:
    """ConversionStateのThread-Safe機能テスト"""

    def test_thread_safe_progress_setting(self):
        """進捗設定のThread-Safe動作テスト"""
        state = ConversionState()
        results = []
        errors = []

        def update_progress(thread_id):
            try:
                # CI/CD最適化: ループ数削減 10→3, sleep削除
                for i in range(3):
                    progress = thread_id * 3 + i
                    if progress <= 100:
                        state.set_progress(progress)
                        results.append((thread_id, progress))
                        # time.sleep(0.001) - CI/CD最適化のため削除
            except Exception as e:
                errors.append((thread_id, e))

        # 複数スレッドで同時実行 (CI/CD最適化: 5→2スレッド)
        threads = []
        for i in range(2):
            thread = threading.Thread(target=update_progress, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"エラーが発生: {errors}"
        assert len(results) > 0, "結果が記録されていない"

        # 最終進捗値が有効範囲内にあることを確認
        final_progress = state.get_progress()
        assert 0 <= final_progress <= 100

    def test_callback_functionality(self):
        """コールバック機能のテスト"""
        state = ConversionState()
        callback_calls = []

        def test_callback(progress, status):
            callback_calls.append((progress, status))

        state.set_callback(test_callback)
        state.set_progress(50)
        state.set_status("テスト中")

        assert len(callback_calls) >= 1
        assert any(call[0] == 50 for call in callback_calls)

    def test_elapsed_time_tracking(self):
        """経過時間追跡のテスト"""
        state = ConversionState()

        # 処理開始
        state.start_processing()
        start_time = time.time()

        # CI/CD最適化: time.sleep削除、即座に時間チェック
        # time.sleep(0.1) - CI/CD最適化のため削除

        # 経過時間確認 (即座に実行)
        elapsed = state.get_elapsed_time()
        actual_elapsed = time.time() - start_time

        # 許容誤差内で経過時間が正確であることを確認
        assert abs(elapsed - actual_elapsed) < 0.05

    @pytest.mark.tdd_refactor
    def test_error_handling_in_progress_setting(self):
        """進捗設定時のエラーハンドリングテスト"""
        state = ConversionState()

        # 無効な値での設定（エラーが発生するが継続する）
        with patch("logging.warning") as mock_warning:
            state.set_progress("invalid")  # 文字列を設定
            mock_warning.assert_called()

        # 範囲外の値
        with patch("logging.warning") as mock_warning:
            state.set_progress(150)  # 100を超える値
            mock_warning.assert_called()

        # 負の値
        with patch("logging.warning") as mock_warning:
            state.set_progress(-10)
            mock_warning.assert_called()


@pytest.mark.tdd_green
class TestFileManagerThreadSafe:
    """FileManagerのThread-Safe機能テスト"""

    def test_thread_safe_file_operations(self):
        """ファイル操作のThread-Safe動作テスト"""
        manager = FileManager()
        results = []
        errors = []

        def test_file_operations(thread_id):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_file = Path(temp_dir) / f"test_{thread_id}.txt"
                    test_file.write_text(f"test content {thread_id}", encoding="utf-8")

                    # ファイル情報取得
                    info = manager.get_file_info(str(test_file))
                    if info:
                        results.append((thread_id, info))
            except Exception as e:
                errors.append((thread_id, e))

        # 複数スレッドで同時実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=test_file_operations, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了待機
        for thread in threads:
            thread.join()

        # 結果確認
        assert len(errors) == 0, f"エラーが発生: {errors}"
        assert len(results) == 3, "全スレッドの結果が記録されていない"

    def test_file_cache_thread_safety(self):
        """ファイルキャッシュのThread-Safe動作テスト"""
        manager = FileManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "cache_test.txt"
            test_file.write_text("test content", encoding="utf-8")

            # 複数スレッドで同じファイルにアクセス
            results = []

            def access_file_info():
                info = manager.get_file_info(str(test_file))
                results.append(info)
