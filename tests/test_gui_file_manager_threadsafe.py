"""FileManager Thread-Safe Tests

Issue #516 Phase 5A対応 - FileManagerのThread-Safe設計テスト
TDD実践による品質保証
"""

import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from kumihan_formatter.gui_models import FileManager, LogManager

pytestmark = [pytest.mark.unit, pytest.mark.tdd_green]


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

            threads = []
            for _ in range(5):
                thread = threading.Thread(target=access_file_info)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # 全て同じ結果が返されることを確認
            assert len(results) == 5
            assert all(result is not None for result in results)
            # キャッシュにより同じ情報が返されることを確認
            first_result = results[0]
            assert all(result["path"] == first_result["path"] for result in results)

    def test_directory_validation_error_handling(self):
        """ディレクトリ検証のエラーハンドリングテスト"""
        # 無効なパスでのテスト
        with patch("logging.warning") as mock_warning:
            result = FileManager.validate_directory_writable("")
            assert result is False

        with patch("logging.warning") as mock_warning:
            result = FileManager.validate_directory_writable(None)
            assert result is False


@pytest.mark.tdd_green
class TestLogManagerThreadSafe:
    """LogManagerのThread-Safe機能テスト"""

    def test_concurrent_message_adding(self):
        """並行メッセージ追加のテスト"""
        log_manager = LogManager(max_messages=100)
        results = []

        def add_messages(thread_id):
            for i in range(10):
                message = f"Thread {thread_id} Message {i}"
                formatted = log_manager.add_message(message, "info")
                results.append((thread_id, formatted))

        # 複数スレッドで同時実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_messages, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 結果確認
        assert len(results) == 50  # 5スレッド × 10メッセージ
        assert log_manager.get_message_count() == 50

    def test_message_limit_enforcement(self):
        """メッセージ数制限の動作テスト"""
        log_manager = LogManager(max_messages=10)

        # 制限を超えるメッセージを追加
        for i in range(20):
            log_manager.add_message(f"Message {i}", "info")

        # メッセージ数が制限内に収まっていることを確認
        assert log_manager.get_message_count() <= 10

    def test_level_based_message_retrieval(self):
        """レベル別メッセージ取得のテスト"""
        log_manager = LogManager()

        # 異なるレベルのメッセージを追加
        log_manager.add_message("Info message", "info")
        log_manager.add_message("Error message", "error")
        log_manager.add_message("Warning message", "warning")

        # レベル別取得
        error_messages = log_manager.get_messages_by_level("error")
        info_messages = log_manager.get_messages_by_level("info")

        assert len(error_messages) == 1
        assert len(info_messages) == 1
        assert error_messages[0]["message"] == "Error message"
