"""
FileValidatorsのテスト

Test coverage targets:
- Path validation: 90%
- Error handling: 85%
- UI integration: 75%
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.file_validators import ErrorHandler, PathValidator
from kumihan_formatter.core.utilities.logger import get_logger


class TestPathValidator:
    """PathValidatorクラスのテスト"""

    def test_validate_input_file_success(self):
        """有効な入力ファイルの検証テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            test_file = f.name

        # When
        result = PathValidator.validate_input_file(test_file)

        # Then
        assert result == Path(test_file)
        assert result.exists()
        assert result.is_file()

        # Cleanup
        Path(test_file).unlink()

    def test_validate_input_file_not_exists(self):
        """存在しないファイルの検証エラーテスト"""
        # Given
        non_existent_file = "non_existent_file.txt"

        # When & Then
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            PathValidator.validate_input_file(non_existent_file)

    def test_validate_input_file_is_directory(self):
        """ディレクトリを指定した場合のエラーテスト"""
        # Given
        test_dir = tempfile.mkdtemp()

        # When & Then
        with pytest.raises(ValueError, match="Input path is not a file"):
            PathValidator.validate_input_file(test_dir)

        # Cleanup
        Path(test_dir).rmdir()

    def test_validate_output_directory_existing(self):
        """既存ディレクトリの出力検証テスト"""
        # Given
        test_dir = tempfile.mkdtemp()

        # When
        result = PathValidator.validate_output_directory(test_dir)

        # Then
        assert result == Path(test_dir)
        assert result.exists()
        assert result.is_dir()

        # Cleanup
        result.rmdir()

    def test_validate_output_directory_create_new(self):
        """新規ディレクトリ作成の出力検証テスト"""
        # Given
        base_dir = tempfile.mkdtemp()
        new_dir = Path(base_dir) / "new_output_dir"

        # When
        result = PathValidator.validate_output_directory(str(new_dir))

        # Then
        assert result == new_dir
        assert result.exists()
        assert result.is_dir()

        # Cleanup
        new_dir.rmdir()
        Path(base_dir).rmdir()

    def test_validate_output_directory_nested_creation(self):
        """ネストしたディレクトリ作成の出力検証テスト"""
        # Given
        base_dir = tempfile.mkdtemp()
        nested_dir = Path(base_dir) / "level1" / "level2" / "output"

        # When
        result = PathValidator.validate_output_directory(str(nested_dir))

        # Then
        assert result == nested_dir
        assert result.exists()
        assert result.is_dir()

        # Cleanup
        nested_dir.rmdir()
        nested_dir.parent.rmdir()
        nested_dir.parent.parent.rmdir()
        Path(base_dir).rmdir()

    def test_validate_source_directory_success(self):
        """有効なソースディレクトリの検証テスト"""
        # Given
        test_dir = tempfile.mkdtemp()

        # When
        result = PathValidator.validate_source_directory(test_dir)

        # Then
        assert result == Path(test_dir)
        assert result.exists()
        assert result.is_dir()

        # Cleanup
        result.rmdir()

    def test_validate_source_directory_not_exists(self):
        """存在しないソースディレクトリの検証エラーテスト"""
        # Given
        non_existent_dir = "non_existent_directory"

        # When & Then
        with pytest.raises(FileNotFoundError, match="Source directory not found"):
            PathValidator.validate_source_directory(non_existent_dir)

    def test_validate_source_directory_is_file(self):
        """ファイルを指定した場合のソースディレクトリエラーテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            test_file = f.name

        # When & Then
        with pytest.raises(ValueError, match="Source path is not a directory"):
            PathValidator.validate_source_directory(test_file)

        # Cleanup
        Path(test_file).unlink()


class TestErrorHandler:
    """ErrorHandlerクラスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.mock_ui = Mock()
        self.error_handler = ErrorHandler(ui=self.mock_ui)

    def test_init_without_ui(self):
        """UI無しでの初期化テスト"""
        # Given & When
        handler = ErrorHandler()

        # Then
        assert handler.ui is None
        assert handler.logger is not None

    def test_init_with_ui(self):
        """UI付きでの初期化テスト"""
        # Given
        mock_ui = Mock()

        # When
        handler = ErrorHandler(ui=mock_ui)

        # Then
        assert handler.ui is mock_ui
        assert handler.logger is not None

    def test_handle_file_not_found_with_ui(self):
        """UI付きでのファイル未発見エラー処理テスト"""
        # Given
        file_path = "missing_file.txt"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_file_not_found(file_path)

            # Then
            mock_log.assert_called_once_with(f"File not found: {file_path}")
            self.mock_ui.file_error.assert_called_once_with(
                file_path, "ファイルが見つかりません"
            )

    def test_handle_file_not_found_without_ui(self):
        """UI無しでのファイル未発見エラー処理テスト"""
        # Given
        handler = ErrorHandler(ui=None)
        file_path = "missing_file.txt"

        with patch.object(handler.logger, "error") as mock_log:
            # When
            handler.handle_file_not_found(file_path)

            # Then
            mock_log.assert_called_once_with(f"File not found: {file_path}")

    def test_handle_encoding_error_with_ui(self):
        """UI付きでのエンコーディングエラー処理テスト"""
        # Given
        file_path = "bad_encoding.txt"
        encoding = "utf-8"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_encoding_error(file_path, encoding)

            # Then
            mock_log.assert_called_once_with(
                f"Encoding error in file: {file_path} (tried: {encoding})"
            )
            self.mock_ui.encoding_error.assert_called_once_with(file_path)
            self.mock_ui.hint.assert_called_once()

            # ヒントメッセージの内容確認
            hint_args = self.mock_ui.hint.call_args
            assert "エンコーディングの問題を解決するには:" in hint_args[0][0]
            assert "UTF-8で保存し直してください" in hint_args[0][1]

    def test_handle_encoding_error_default_encoding(self):
        """デフォルトエンコーディングでのエンコーディングエラー処理テスト"""
        # Given
        file_path = "bad_encoding.txt"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_encoding_error(
                file_path
            )  # encodingパラメータ省略

            # Then
            mock_log.assert_called_once_with(
                f"Encoding error in file: {file_path} (tried: utf-8)"
            )

    def test_handle_encoding_error_without_ui(self):
        """UI無しでのエンコーディングエラー処理テスト"""
        # Given
        handler = ErrorHandler(ui=None)
        file_path = "bad_encoding.txt"
        encoding = "shift_jis"

        with patch.object(handler.logger, "error") as mock_log:
            # When
            handler.handle_encoding_error(file_path, encoding)

            # Then
            mock_log.assert_called_once_with(
                f"Encoding error in file: {file_path} (tried: {encoding})"
            )

    def test_handle_permission_error_with_ui(self):
        """UI付きでの権限エラー処理テスト"""
        # Given
        error_message = "Permission denied: cannot write to directory"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_permission_error(error_message)

            # Then
            mock_log.assert_called_once_with(f"Permission error: {error_message}")
            self.mock_ui.permission_error.assert_called_once_with(error_message)

    def test_handle_permission_error_without_ui(self):
        """UI無しでの権限エラー処理テスト"""
        # Given
        handler = ErrorHandler(ui=None)
        error_message = "Permission denied: cannot write to directory"

        with patch.object(handler.logger, "error") as mock_log:
            # When
            handler.handle_permission_error(error_message)

            # Then
            mock_log.assert_called_once_with(f"Permission error: {error_message}")

    def test_handle_unexpected_error_with_ui(self):
        """UI付きでの予期しないエラー処理テスト"""
        # Given
        error_message = "Unexpected runtime error occurred"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_unexpected_error(error_message)

            # Then
            mock_log.assert_called_once_with(f"Unexpected error: {error_message}")
            self.mock_ui.unexpected_error.assert_called_once_with(error_message)

    def test_handle_unexpected_error_without_ui(self):
        """UI無しでの予期しないエラー処理テスト"""
        # Given
        handler = ErrorHandler(ui=None)
        error_message = "Unexpected runtime error occurred"

        with patch.object(handler.logger, "error") as mock_log:
            # When
            handler.handle_unexpected_error(error_message)

            # Then
            mock_log.assert_called_once_with(f"Unexpected error: {error_message}")

    def test_multiple_error_handling_sequence(self):
        """複数のエラーハンドリングシーケンステスト"""
        # Given
        file_path = "test_file.txt"
        encoding_error = "encoding error"
        permission_error = "permission error"
        unexpected_error = "unexpected error"

        with patch.object(self.error_handler.logger, "error") as mock_log:
            # When
            self.error_handler.handle_file_not_found(file_path)
            self.error_handler.handle_encoding_error(file_path)
            self.error_handler.handle_permission_error(permission_error)
            self.error_handler.handle_unexpected_error(unexpected_error)

            # Then
            assert mock_log.call_count == 4
            assert self.mock_ui.file_error.call_count == 1
            assert self.mock_ui.encoding_error.call_count == 1
            assert self.mock_ui.hint.call_count == 1
            assert self.mock_ui.permission_error.call_count == 1
            assert self.mock_ui.unexpected_error.call_count == 1

    def test_logger_debug_on_initialization(self):
        """初期化時のデバッグログ出力テスト"""
        # Given & When
        with patch(
            "kumihan_formatter.core.file_validators.get_logger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            handler = ErrorHandler()

            # Then
            mock_logger.debug.assert_called_once_with("ErrorHandler initialized")

    def test_error_handling_comprehensive_coverage(self):
        """エラーハンドリングの包括的カバレッジテスト"""
        # Given
        test_cases = [
            ("handle_file_not_found", ["test.txt"]),
            ("handle_encoding_error", ["test.txt", "utf-8"]),
            ("handle_permission_error", ["permission denied"]),
            ("handle_unexpected_error", ["runtime error"]),
        ]

        # When & Then
        for method_name, args in test_cases:
            method = getattr(self.error_handler, method_name)

            # UI有りでの呼び出し
            method(*args)

            # UI無しでの呼び出し
            handler_no_ui = ErrorHandler(ui=None)
            method_no_ui = getattr(handler_no_ui, method_name)
            method_no_ui(*args)

        # すべてのケースでエラーが発生しないことを確認
        assert True  # テストが完了すれば成功
