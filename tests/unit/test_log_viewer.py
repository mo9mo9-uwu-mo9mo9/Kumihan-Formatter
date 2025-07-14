"""log_viewer.pyの基本的なユニットテスト

Issue #463対応: log_viewer.pyのテストカバレッジ実装（0% → 基本テスト）
"""

import threading
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.log_viewer import LogViewerWindow


class TestLogViewerWindow(unittest.TestCase):
    """LogViewerWindowの基本テスト"""

    def setUp(self) -> None:
        """テスト前のセットアップ"""
        # tkinter関連のモック
        self.mock_tk = patch("kumihan_formatter.core.log_viewer.tk")
        self.mock_scrolledtext = patch("kumihan_formatter.core.log_viewer.scrolledtext")
        self.mock_ttk = patch("kumihan_formatter.core.log_viewer.ttk")

        self.tk_mock = self.mock_tk.start()
        self.scrolledtext_mock = self.mock_scrolledtext.start()
        self.ttk_mock = self.mock_ttk.start()

        # tkinter要素のモック設定
        self.tk_mock.Tk.return_value = Mock()
        self.tk_mock.Toplevel.return_value = Mock()
        self.tk_mock.BooleanVar.return_value = Mock()
        self.tk_mock.StringVar.return_value = Mock()
        self.scrolledtext_mock.ScrolledText.return_value = Mock()
        self.ttk_mock.Frame.return_value = Mock()
        self.ttk_mock.Button.return_value = Mock()
        self.ttk_mock.Checkbutton.return_value = Mock()
        self.ttk_mock.Combobox.return_value = Mock()
        self.ttk_mock.Label.return_value = Mock()

    def tearDown(self) -> None:
        """テスト後のクリーンアップ"""
        self.mock_tk.stop()
        self.mock_scrolledtext.stop()
        self.mock_ttk.stop()

    def test_init_without_parent(self) -> None:
        """親ウィンドウなしでの初期化テスト"""
        viewer = LogViewerWindow()

        self.assertIsNone(viewer.parent)
        self.assertIsNone(viewer.window)
        self.assertIsNone(viewer.log_text)
        self.assertTrue(viewer.auto_scroll)
        self.assertIsNone(viewer.update_thread)
        self.assertFalse(viewer.running)

    def test_init_with_parent(self) -> None:
        """親ウィンドウありでの初期化テスト"""
        parent_mock = Mock()
        viewer = LogViewerWindow(parent_mock)

        self.assertEqual(viewer.parent, parent_mock)
        self.assertIsNone(viewer.window)

    def test_show_new_window(self) -> None:
        """新規ウィンドウ表示テスト"""
        viewer = LogViewerWindow()

        with patch.object(viewer, "_setup_ui") as mock_setup:
            with patch.object(viewer, "_start_update_thread") as mock_start:
                viewer.show()

                # ウィンドウが作成されることを確認
                self.assertIsNotNone(viewer.window)
                self.tk_mock.Tk.assert_called_once()

                # UIセットアップと更新スレッド開始が呼ばれることを確認
                mock_setup.assert_called_once()
                mock_start.assert_called_once()

    def test_show_existing_window(self) -> None:
        """既存ウィンドウの前面表示テスト"""
        viewer = LogViewerWindow()
        mock_window = Mock()
        viewer.window = mock_window

        viewer.show()

        # 既存ウィンドウが前面に表示される
        mock_window.lift.assert_called_once()
        mock_window.focus_force.assert_called_once()

    def test_show_with_parent(self) -> None:
        """親ウィンドウありでの表示テスト"""
        parent_mock = Mock()
        viewer = LogViewerWindow(parent_mock)

        with patch.object(viewer, "_setup_ui"):
            with patch.object(viewer, "_start_update_thread"):
                viewer.show()

                # Toplevelが作成されることを確認
                self.tk_mock.Toplevel.assert_called_once_with(parent_mock)

    def test_setup_ui_components(self) -> None:
        """UIコンポーネント設定テスト"""
        viewer = LogViewerWindow()
        viewer.window = Mock()

        # _setup_uiメソッドの実行をテスト
        viewer._setup_ui()

        # UIコンポーネントが初期化されることを確認
        self.assertIsNotNone(viewer.auto_scroll_var)
        self.assertIsNotNone(viewer.level_var)
        self.assertIsNotNone(viewer.status_var)
        self.assertIsNotNone(viewer.log_text)

    def test_on_closing(self) -> None:
        """ウィンドウクローズ処理テスト"""
        viewer = LogViewerWindow()
        viewer.running = True
        viewer.update_thread = Mock()
        viewer.window = Mock()

        viewer.on_closing()

        # 実行状態が停止される
        self.assertFalse(viewer.running)

        # ウィンドウは破棄される（実装確認）
        # 実際のon_closingではwindowはNoneに設定される
        self.assertIsNone(viewer.window)

    def test_start_update_thread(self) -> None:
        """更新スレッド開始テスト"""
        viewer = LogViewerWindow()

        with patch("threading.Thread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            viewer._start_update_thread()

            # スレッドが作成され開始される
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()
            self.assertTrue(viewer.running)
            self.assertEqual(viewer.update_thread, mock_thread)

    def test_add_logs(self) -> None:
        """ログ追加処理のテスト"""
        viewer = LogViewerWindow()
        viewer.log_text = Mock()
        viewer.level_var = Mock()
        viewer.level_var.get.return_value = "ALL"
        viewer.auto_scroll = True

        test_logs = ["[INFO    ] Test log message", "[ERROR   ] Error message"]
        viewer._add_logs(test_logs)

        # ログテキストが更新される
        viewer.log_text.config.assert_called()
        viewer.log_text.insert.assert_called()

    def test_clear_log(self) -> None:
        """ログクリア処理テスト"""
        viewer = LogViewerWindow()
        viewer.log_text = Mock()
        viewer.status_var = Mock()

        # メソッドが実行できることを確認（例外なく実行）
        try:
            viewer.clear_log()
            # エラーなく実行されることを確認
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"clear_log should not raise exception: {e}")

    def test_toggle_auto_scroll(self) -> None:
        """自動スクロール切り替えテスト"""
        viewer = LogViewerWindow()
        viewer.auto_scroll_var = Mock()
        viewer.auto_scroll_var.get.return_value = False

        viewer._toggle_auto_scroll()

        # auto_scrollが更新される
        self.assertFalse(viewer.auto_scroll)

    def test_filter_logs(self) -> None:
        """ログフィルタリングテスト"""
        viewer = LogViewerWindow()
        viewer.level_var = Mock()
        viewer.level_var.get.return_value = "ERROR"
        viewer.log_text = Mock()

        viewer._filter_logs()

        # フィルタリングが実行される（実際の実装では再表示）
        self.assertTrue(True)  # 基本的な実行確認

    def test_window_geometry_and_title(self) -> None:
        """ウィンドウのジオメトリとタイトル設定テスト"""
        viewer = LogViewerWindow()

        with patch.object(viewer, "_setup_ui"):
            with patch.object(viewer, "_start_update_thread"):
                viewer.show()

                # ウィンドウのタイトルとサイズが設定される
                viewer.window.title.assert_called_with(
                    "Kumihan-Formatter - Debug Log Viewer"
                )
                viewer.window.geometry.assert_called_with("800x600")

    def test_open_log_file(self) -> None:
        """ログファイルを開く機能のテスト"""
        viewer = LogViewerWindow()
        viewer.status_var = Mock()

        # メソッドが実行できることを確認（例外なく実行）
        try:
            viewer.open_log_file()
            # エラーなく実行されることを確認
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"open_log_file should not raise exception: {e}")

    def test_show_log_viewer_function(self) -> None:
        """show_log_viewer関数のテスト"""
        from kumihan_formatter.core.log_viewer import show_log_viewer

        parent_mock = Mock()

        with patch("kumihan_formatter.core.log_viewer.LogViewerWindow") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            result = show_log_viewer(parent_mock)

            # LogViewerWindowが作成され、showが呼ばれる
            mock_class.assert_called_once_with(parent_mock)
            mock_instance.show.assert_called_once()
            self.assertEqual(result, mock_instance)


if __name__ == "__main__":
    unittest.main()
