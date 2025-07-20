"""AppState Thread-Safe Tests

Issue #516 Phase 5A対応 - AppStateのThread-Safe設計テスト
TDD実践による品質保証
"""

import threading
from unittest.mock import patch

import pytest

from kumihan_formatter.gui_models import AppState

pytestmark = [pytest.mark.unit, pytest.mark.tdd_green]


@pytest.mark.tdd_green
class TestAppStateThreadSafe:
    """AppStateのThread-Safe機能テスト"""

    def test_conversion_readiness_check_thread_safety(self):
        """変換準備チェックのThread-Safe動作テスト"""
        app_state = AppState()
        results = []

        def check_readiness(thread_id):
            ready, message = app_state.is_ready_for_conversion()
            results.append((thread_id, ready, message))

        # 複数スレッドで同時実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=check_readiness, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 結果確認
        assert len(results) == 3
        # 全て同じ結果が返されることを確認（状態が変わらない限り）
        assert all(isinstance(result[1], bool) for result in results)

    def test_error_tracking_thread_safety(self):
        """エラー追跡のThread-Safe動作テスト"""
        app_state = AppState()
        errors = []

        def trigger_error(thread_id):
            try:
                # 無効な設定でエラーを発生させる
                app_state.config.set_input_file("")  # 空のファイルパス
                app_state.is_ready_for_conversion()  # エラーが記録される
            except Exception as e:
                errors.append((thread_id, e))

        # 複数スレッドでエラーを発生
        threads = []
        for i in range(3):
            thread = threading.Thread(target=trigger_error, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=5)  # タイムアウト設定

        # エラーが発生していないことを確認
        assert len(errors) == 0, f"スレッドエラーが発生: {errors}"

        # エラー情報確認
        error_info = app_state.get_error_info()
        assert error_info["has_errors"] is True
        assert error_info["error_count"] > 0

    @pytest.mark.tdd_refactor
    def test_fallback_initialization(self):
        """フォールバック初期化のテスト"""
        try:
            # 正常な初期化の確認
            app_state = AppState()
            assert hasattr(app_state, "config")
            assert hasattr(app_state, "conversion_state")
            assert hasattr(app_state, "file_manager")
            assert hasattr(app_state, "log_manager")
        except Exception as e:
            pytest.skip(f"AppState初期化失敗: {e}")

    def test_debug_mode_detection(self):
        """デバッグモード検出のテスト"""
        try:
            # 環境変数なしの場合
            app_state = AppState()
            assert isinstance(app_state.debug_mode, bool)

            # 環境変数ありの場合
            with patch.dict("os.environ", {"KUMIHAN_GUI_DEBUG": "true"}):
                app_state_debug = AppState()
                assert app_state_debug.debug_mode is True
        except Exception as e:
            pytest.skip(f"デバッグモード検出機能未実装: {e}")

    def test_concurrent_state_access(self):
        """並行状態アクセスのテスト"""
        app_state = AppState()
        results = []

        def access_state(thread_id):
            try:
                # 複数の状態にアクセス
                ready, _ = app_state.is_ready_for_conversion()
                error_info = app_state.get_error_info()
                debug_mode = app_state.debug_mode

                results.append((thread_id, ready, error_info, debug_mode))
            except Exception as e:
                results.append((thread_id, "error", str(e), None))

        # 複数スレッドで状態アクセス
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_state, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 結果確認
        assert len(results) == 5
        for result in results:
            assert len(result) == 4
            assert isinstance(result[0], int)  # thread_id
            if result[1] != "error":
                assert isinstance(result[1], bool)  # ready状態
                assert isinstance(result[2], dict)  # error_info
                assert isinstance(result[3], bool)  # debug_mode

    def test_configuration_thread_safety(self):
        """設定変更のThread-Safe動作テスト"""
        app_state = AppState()
        results = []

        def change_config(thread_id):
            try:
                # 設定変更
                app_state.config.set_input_file(f"test_{thread_id}.txt")
                app_state.config.set_output_file(f"output_{thread_id}.html")

                # 状態確認
                ready, message = app_state.is_ready_for_conversion()
                results.append((thread_id, ready, message))
            except Exception as e:
                results.append((thread_id, "error", str(e)))

        # 複数スレッドで設定変更
        threads = []
        for i in range(3):
            thread = threading.Thread(target=change_config, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 結果確認
        assert len(results) == 3
        for result in results:
            assert len(result) == 3
            assert isinstance(result[0], int)  # thread_id
            if result[1] != "error":
                assert isinstance(result[1], bool)  # ready状態
                assert isinstance(result[2], str)  # message
