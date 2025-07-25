"""
エラー回復戦略のテスト

Important Tier Phase 2-1対応 - Issue #593
エラー回復戦略の体系的テスト実装
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.error_handling.recovery import (
    FileEncodingRecoveryStrategy,
    FileNotFoundRecoveryStrategy,
    FilePermissionRecoveryStrategy,
    MemoryErrorRecoveryStrategy,
    RecoveryManager,
    RecoveryStrategy,
    SyntaxErrorRecoveryStrategy,
)


class TestRecoveryStrategy:
    """基底回復戦略クラスのテスト"""

    def test_abstract_methods(self):
        """抽象メソッドのテスト"""
        # RecoveryStrategyは抽象基底クラスなので直接インスタンス化できない
        with pytest.raises(TypeError):
            RecoveryStrategy()


class TestFileEncodingRecoveryStrategy:
    """ファイルエンコーディング回復戦略のテスト"""

    def test_can_handle_encoding_error(self):
        """エンコーディングエラーを処理できるかのテスト"""
        # Given
        strategy = FileEncodingRecoveryStrategy()
        encoding_error = UnicodeDecodeError(
            "utf-8", b"\x80\x81", 0, 2, "invalid start byte"
        )
        other_error = ValueError("Not an encoding error")

        # When/Then
        assert strategy.can_handle(encoding_error) is True
        assert strategy.can_handle(other_error) is False

    def test_recover_with_encoding_detection(self):
        """エンコーディング検出による回復テスト"""
        # Given
        strategy = FileEncodingRecoveryStrategy()
        error = UnicodeDecodeError("utf-8", b"\x82\xa0", 0, 2, "invalid start byte")
        context = {"file_path": "test.txt", "original_encoding": "utf-8"}

        # Create a test file with Shift-JIS encoding
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
            tmp.write("あいうえお".encode("shift_jis"))
            temp_path = Path(tmp.name)

        try:
            context["file_path"] = str(temp_path)

            # When
            result = strategy.recover(error, context)

            # Then
            assert result["success"] is True
            assert "detected_encoding" in result
            assert result["recovered_data"] == "あいうえお"
        finally:
            temp_path.unlink()

    def test_recover_with_fallback_encodings(self):
        """フォールバックエンコーディングでの回復テスト"""
        # Given
        strategy = FileEncodingRecoveryStrategy()
        error = UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte")
        context = {"file_path": "nonexistent.txt"}

        # When
        result = strategy.recover(error, context)

        # Then
        assert result["success"] is False
        assert "attempted_encodings" in result

    def test_priority(self):
        """優先度のテスト"""
        strategy = FileEncodingRecoveryStrategy()
        assert strategy.priority == 80


class TestFileNotFoundRecoveryStrategy:
    """ファイル未発見回復戦略のテスト"""

    def test_can_handle_file_not_found(self):
        """FileNotFoundErrorを処理できるかのテスト"""
        # Given
        strategy = FileNotFoundRecoveryStrategy()
        file_error = FileNotFoundError("File not found")
        other_error = ValueError("Not a file error")

        # When/Then
        assert strategy.can_handle(file_error) is True
        assert strategy.can_handle(other_error) is False

    def test_recover_create_empty_file(self):
        """空ファイル作成による回復テスト"""
        # Given
        strategy = FileNotFoundRecoveryStrategy()
        error = FileNotFoundError("File not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            context = {"file_path": str(file_path), "operation": "read"}

            # When
            result = strategy.recover(error, context)

            # Then
            assert result["success"] is True
            assert file_path.exists()
            assert result["action"] == "created_empty_file"

    def test_recover_with_alternative_paths(self):
        """代替パスでの回復テスト"""
        # Given
        strategy = FileNotFoundRecoveryStrategy()
        error = FileNotFoundError("File not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create alternative file
            alt_path = Path(tmpdir) / "test.txt.bak"
            alt_path.write_text("Backup content")

            context = {
                "file_path": str(Path(tmpdir) / "test.txt"),
                "alternative_paths": [str(alt_path)],
            }

            # When
            result = strategy.recover(error, context)

            # Then
            assert result["success"] is True
            assert result["alternative_path"] == str(alt_path)
            assert result["recovered_data"] == "Backup content"


class TestFilePermissionRecoveryStrategy:
    """ファイル権限回復戦略のテスト"""

    def test_can_handle_permission_error(self):
        """PermissionErrorを処理できるかのテスト"""
        # Given
        strategy = FilePermissionRecoveryStrategy()
        perm_error = PermissionError("Permission denied")
        other_error = ValueError("Not a permission error")

        # When/Then
        assert strategy.can_handle(perm_error) is True
        assert strategy.can_handle(other_error) is False

    def test_recover_with_temp_location(self):
        """一時ファイルへの書き込みによる回復テスト"""
        # Given
        strategy = FilePermissionRecoveryStrategy()
        error = PermissionError("Permission denied")
        context = {
            "file_path": "/protected/file.txt",
            "operation": "write",
            "data": "Test data",
        }

        # When
        result = strategy.recover(error, context)

        # Then
        assert result["success"] is True
        assert "temp_path" in result
        assert Path(result["temp_path"]).exists()
        assert Path(result["temp_path"]).read_text() == "Test data"

        # Cleanup
        Path(result["temp_path"]).unlink()

    def test_recover_read_only_file(self):
        """読み取り専用ファイルの回復テスト"""
        # Given
        strategy = FilePermissionRecoveryStrategy()
        error = PermissionError("Permission denied")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write("Original content")
            temp_path = Path(tmp.name)

        # Make file read-only
        temp_path.chmod(0o444)

        try:
            context = {"file_path": str(temp_path), "operation": "read"}

            # When
            result = strategy.recover(error, context)

            # Then
            assert result["success"] is True
            assert result["recovered_data"] == "Original content"
        finally:
            # Restore permissions and cleanup
            temp_path.chmod(0o644)
            temp_path.unlink()


class TestSyntaxErrorRecoveryStrategy:
    """構文エラー回復戦略のテスト"""

    def test_can_handle_syntax_errors(self):
        """構文エラーを処理できるかのテスト"""
        # Given
        strategy = SyntaxErrorRecoveryStrategy()
        syntax_error = SyntaxError("Invalid syntax")
        value_error = ValueError("Invalid markdown syntax")
        other_error = FileNotFoundError("Not a syntax error")

        # When/Then
        assert strategy.can_handle(syntax_error) is True
        assert (
            strategy.can_handle(value_error) is True
        )  # Also handles ValueError with "syntax"
        assert strategy.can_handle(other_error) is False

    def test_recover_markdown_syntax(self):
        """Markdown構文エラーの回復テスト"""
        # Given
        strategy = SyntaxErrorRecoveryStrategy()
        error = ValueError("Invalid markdown syntax")
        context = {
            "content": ";;;invalid;;;\nValid content\n;;;invalid",
            "line_number": 1,
        }

        # When
        result = strategy.recover(error, context)

        # Then
        assert result["success"] is True
        assert ";;;invalid;;;" not in result["corrected_content"]
        assert "Valid content" in result["corrected_content"]
        assert len(result["corrections"]) > 0

    def test_recover_with_auto_correction(self):
        """自動修正による回復テスト"""
        # Given
        strategy = SyntaxErrorRecoveryStrategy()
        error = SyntaxError("Unclosed bracket")
        context = {
            "content": "Test [unclosed bracket\nNext line",
            "line_number": 1,
        }

        # When
        result = strategy.recover(error, context)

        # Then
        assert result["success"] is True
        # 修正案が提供される
        assert "corrections" in result or "suggestions" in result


class TestMemoryErrorRecoveryStrategy:
    """メモリエラー回復戦略のテスト"""

    def test_can_handle_memory_error(self):
        """MemoryErrorを処理できるかのテスト"""
        # Given
        strategy = MemoryErrorRecoveryStrategy()
        mem_error = MemoryError("Out of memory")
        other_error = ValueError("Not a memory error")

        # When/Then
        assert strategy.can_handle(mem_error) is True
        assert strategy.can_handle(other_error) is False

    @patch("gc.collect")
    def test_recover_with_gc(self, mock_gc_collect):
        """ガベージコレクションによる回復テスト"""
        # Given
        strategy = MemoryErrorRecoveryStrategy()
        error = MemoryError("Out of memory")
        context = {"operation": "large_file_processing"}

        # When
        result = strategy.recover(error, context)

        # Then
        mock_gc_collect.assert_called()
        assert result["success"] is True
        assert result["action"] == "gc_and_retry"

    def test_recover_with_chunking(self):
        """チャンク処理による回復テスト"""
        # Given
        strategy = MemoryErrorRecoveryStrategy()
        error = MemoryError("Out of memory")
        context = {
            "data_size": 1000000,
            "operation": "data_processing",
        }

        # When
        result = strategy.recover(error, context)

        # Then
        assert "chunk_size" in result
        assert result["chunk_size"] < context["data_size"]


class TestRecoveryManager:
    """回復管理システムのテスト"""

    def test_init_with_defaults(self):
        """デフォルト設定での初期化テスト"""
        # When
        manager = RecoveryManager()

        # Then
        assert manager.enable_logging is True
        assert len(manager.strategies) > 0  # デフォルト戦略が登録されている
        assert len(manager.recovery_history) == 0

    def test_register_strategy(self):
        """戦略登録のテスト"""
        # Given
        manager = RecoveryManager()
        initial_count = len(manager.strategies)
        custom_strategy = FileNotFoundRecoveryStrategy()

        # When
        manager.register_strategy(custom_strategy)

        # Then
        assert len(manager.strategies) == initial_count + 1
        assert custom_strategy in manager.strategies

    def test_attempt_recovery_success(self):
        """回復成功のテスト"""
        # Given
        manager = RecoveryManager()
        error = FileNotFoundError("File not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            context = {"file_path": str(file_path), "operation": "read"}

            # When
            result = manager.attempt_recovery(error, context)

            # Then
            assert result is not None
            assert result["success"] is True
            assert file_path.exists()
            assert len(manager.recovery_history) == 1

    def test_attempt_recovery_no_suitable_strategy(self):
        """適切な戦略がない場合のテスト"""
        # Given
        manager = RecoveryManager()
        manager.strategies = []  # Clear all strategies
        error = ValueError("Unknown error")
        context = {}

        # When
        result = manager.attempt_recovery(error, context)

        # Then
        assert result is None
        assert len(manager.recovery_history) == 0

    def test_attempt_recovery_all_strategies_fail(self):
        """全戦略が失敗する場合のテスト"""
        # Given
        manager = RecoveryManager()
        error = FileNotFoundError("File not found")
        context = {"file_path": "/impossible/path/that/cannot/be/created"}

        # Mock all strategies to fail
        for strategy in manager.strategies:
            if isinstance(strategy, FileNotFoundRecoveryStrategy):
                strategy.recover = Mock(
                    return_value={"success": False, "reason": "Cannot create file"}
                )

        # When
        result = manager.attempt_recovery(error, context)

        # Then
        assert result is None or (
            isinstance(result, dict) and not result.get("success", True)
        )

    def test_get_recovery_stats(self):
        """回復統計取得のテスト"""
        # Given
        manager = RecoveryManager()
        manager.recovery_history = [
            {
                "error_type": "FileNotFoundError",
                "strategy": "FileNotFoundRecoveryStrategy",
                "success": True,
            },
            {
                "error_type": "MemoryError",
                "strategy": "MemoryErrorRecoveryStrategy",
                "success": True,
            },
            {
                "error_type": "PermissionError",
                "strategy": "FilePermissionRecoveryStrategy",
                "success": False,
            },
        ]

        # When
        stats = manager.get_recovery_stats()

        # Then
        assert stats["total_attempts"] == 3
        assert stats["successful_recoveries"] == 2
        assert stats["success_rate"] == 2 / 3
        assert "FileNotFoundError" in stats["by_error_type"]
        assert stats["by_error_type"]["FileNotFoundError"]["attempts"] == 1

    def test_clear_history(self):
        """履歴クリアのテスト"""
        # Given
        manager = RecoveryManager()
        manager.recovery_history = [{"error_type": "TestError", "success": True}]

        # When
        manager.clear_history()

        # Then
        assert len(manager.recovery_history) == 0

    def test_priority_based_recovery(self):
        """優先度ベースの回復テスト"""
        # Given
        manager = RecoveryManager()

        # Create strategies with different priorities
        high_priority_strategy = Mock(spec=RecoveryStrategy)
        high_priority_strategy.priority = 100
        high_priority_strategy.can_handle.return_value = True
        high_priority_strategy.recover.return_value = {
            "success": True,
            "strategy": "high",
        }

        low_priority_strategy = Mock(spec=RecoveryStrategy)
        low_priority_strategy.priority = 10
        low_priority_strategy.can_handle.return_value = True
        low_priority_strategy.recover.return_value = {
            "success": True,
            "strategy": "low",
        }

        # Register in reverse priority order
        manager.strategies = [low_priority_strategy, high_priority_strategy]

        # When
        error = ValueError("Test error")
        result = manager.attempt_recovery(error, {})

        # Then
        # 高優先度の戦略が最初に試される
        high_priority_strategy.recover.assert_called_once()
        low_priority_strategy.recover.assert_not_called()
        assert result["strategy"] == "high"
