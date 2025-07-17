"""
console_ui.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - console_ui.py分割
"""

from unittest.mock import Mock

import pytest


class TestConsoleMessaging:
    """コンソールメッセージ機能のテスト"""

    def test_console_messaging_import(self):
        """RED: メッセージ機能モジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

    def test_console_messaging_initialization(self):
        """RED: メッセージ機能初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

            mock_console = Mock()
            messaging = ConsoleMessaging(mock_console)

    def test_success_messages(self):
        """RED: 成功メッセージ系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

            mock_console = Mock()
            messaging = ConsoleMessaging(mock_console)
            messaging.success("test message")
            messaging.conversion_complete("test.html")

    def test_error_messages(self):
        """RED: エラーメッセージ系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

            mock_console = Mock()
            messaging = ConsoleMessaging(mock_console)
            messaging.error("test error")
            messaging.file_error("test.txt")
            messaging.encoding_error("test.txt")

    def test_warning_messages(self):
        """RED: 警告メッセージ系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

            mock_console = Mock()
            messaging = ConsoleMessaging(mock_console)
            messaging.warning("test warning")
            messaging.validation_warning(5)

    def test_info_messages(self):
        """RED: 情報メッセージ系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_messaging import ConsoleMessaging

            mock_console = Mock()
            messaging = ConsoleMessaging(mock_console)
            messaging.info("test info")
            messaging.hint("test hint")


class TestConsoleOperations:
    """コンソール操作機能のテスト"""

    def test_console_operations_import(self):
        """RED: 操作機能モジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_operations import ConsoleOperations

    def test_console_operations_initialization(self):
        """RED: 操作機能初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_operations import ConsoleOperations

            mock_console = Mock()
            operations = ConsoleOperations(mock_console)

    def test_file_operations(self):
        """RED: ファイル操作系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_operations import ConsoleOperations

            mock_console = Mock()
            operations = ConsoleOperations(mock_console)
            operations.file_copied(5)
            operations.files_missing(["test1.png", "test2.jpg"])

    def test_watch_operations(self):
        """RED: 監視操作系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_operations import ConsoleOperations

            mock_console = Mock()
            operations = ConsoleOperations(mock_console)
            operations.watch_start("test.txt")
            operations.watch_file_changed("test.txt")
            operations.watch_stopped()

    def test_test_operations(self):
        """RED: テスト操作系テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_operations import ConsoleOperations

            mock_console = Mock()
            operations = ConsoleOperations(mock_console)
            operations.test_file_generation()
            operations.test_conversion_start()


class TestConsoleInteraction:
    """コンソール相互作用機能のテスト"""

    def test_console_interaction_import(self):
        """RED: 相互作用機能モジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_interaction import ConsoleInteraction

    def test_console_interaction_initialization(self):
        """RED: 相互作用機能初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_interaction import ConsoleInteraction

            mock_console = Mock()
            interaction = ConsoleInteraction(mock_console)

    def test_user_input(self):
        """RED: ユーザー入力テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_interaction import ConsoleInteraction

            mock_console = Mock()
            interaction = ConsoleInteraction(mock_console)
            result = interaction.input("test prompt")

    def test_confirmation_methods(self):
        """RED: 確認メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_interaction import ConsoleInteraction

            mock_console = Mock()
            interaction = ConsoleInteraction(mock_console)
            result = interaction.confirm_source_toggle()

    def test_progress_creation(self):
        """RED: プログレス作成テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_interaction import ConsoleInteraction

            mock_console = Mock()
            interaction = ConsoleInteraction(mock_console)
            progress = interaction.create_progress()


class TestConsoleFactory:
    """コンソールファクトリーのテスト"""

    def test_console_factory_import(self):
        """RED: ファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_factory import get_console_ui_components

    def test_get_console_ui_components(self):
        """RED: コンソールUIコンポーネント取得テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_factory import get_console_ui_components

            components = get_console_ui_components()

    def test_console_factory_initialization(self):
        """RED: ファクトリー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.ui.console_factory import ConsoleUIFactory

            factory = ConsoleUIFactory()


class TestOriginalConsoleUI:
    """元のconsole_uiモジュールとの互換性テスト"""

    def test_original_console_ui_still_works(self):
        """元のconsole_uiが正常動作することを確認"""
        from kumihan_formatter.ui.console_ui import ConsoleUI, get_console_ui

        # 基本クラスが存在することを確認
        assert ConsoleUI is not None

        # ファクトリー関数が存在することを確認
        assert callable(get_console_ui)

    def test_console_ui_initialization(self):
        """元のConsoleUI初期化テスト"""
        from kumihan_formatter.ui.console_ui import ConsoleUI

        console_ui = ConsoleUI()
        assert console_ui is not None
        assert hasattr(console_ui, "console")

    def test_get_console_ui_function(self):
        """元のget_console_ui関数テスト"""
        from kumihan_formatter.ui.console_ui import get_console_ui

        console_ui = get_console_ui()
        assert console_ui is not None

        # シングルトンパターンの確認
        console_ui2 = get_console_ui()
        assert console_ui is console_ui2

    def test_message_methods_exist(self):
        """メッセージメソッドが存在することを確認"""
        from kumihan_formatter.ui.console_ui import get_console_ui

        console_ui = get_console_ui()

        # 成功メッセージ系
        assert hasattr(console_ui, "success")
        assert hasattr(console_ui, "conversion_complete")

        # エラーメッセージ系
        assert hasattr(console_ui, "error")
        assert hasattr(console_ui, "file_error")
        assert hasattr(console_ui, "encoding_error")

        # 警告メッセージ系
        assert hasattr(console_ui, "warning")
        assert hasattr(console_ui, "validation_warning")

        # 情報メッセージ系
        assert hasattr(console_ui, "info")
        assert hasattr(console_ui, "hint")

    def test_operation_methods_exist(self):
        """操作メソッドが存在することを確認"""
        from kumihan_formatter.ui.console_ui import get_console_ui

        console_ui = get_console_ui()

        # ファイル操作系
        assert hasattr(console_ui, "file_copied")
        assert hasattr(console_ui, "files_missing")

        # 監視操作系
        assert hasattr(console_ui, "watch_start")
        assert hasattr(console_ui, "watch_file_changed")
        assert hasattr(console_ui, "watch_stopped")

        # テスト操作系
        assert hasattr(console_ui, "test_file_generation")
        assert hasattr(console_ui, "test_conversion_start")

    def test_interaction_methods_exist(self):
        """相互作用メソッドが存在することを確認"""
        from kumihan_formatter.ui.console_ui import get_console_ui

        console_ui = get_console_ui()

        # ユーザー入力
        assert hasattr(console_ui, "input")
        assert hasattr(console_ui, "confirm_source_toggle")

        # プログレス
        assert hasattr(console_ui, "create_progress")
