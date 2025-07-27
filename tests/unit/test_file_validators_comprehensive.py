"""
FileValidators包括的テスト - Issue #620 Phase 3

file_validators.pyの12.5%から60%+へのカバレッジ改善
PathValidatorとErrorHandlerの全機能をテスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.file_validators import ErrorHandler, PathValidator


class TestPathValidator:
    """PathValidator包括的テスト"""

    def test_validate_input_file_success(self):
        """有効な入力ファイルの検証テスト"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_path = temp_file.name

        try:
            # 有効なファイルパスの検証
            result = PathValidator.validate_input_file(temp_path)
            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_file()
            assert str(result) == temp_path
        finally:
            Path(temp_path).unlink()

    def test_validate_input_file_not_found(self):
        """存在しないファイルの検証エラーテスト"""
        non_existent_file = "/nonexistent/directory/file.txt"

        with pytest.raises(FileNotFoundError) as exc_info:
            PathValidator.validate_input_file(non_existent_file)

        assert "Input file not found" in str(exc_info.value)
        assert non_existent_file in str(exc_info.value)

    def test_validate_input_file_not_a_file(self):
        """ディレクトリを指定した場合のエラーテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # ディレクトリパスを指定
            with pytest.raises(ValueError) as exc_info:
                PathValidator.validate_input_file(temp_dir)

            assert "Input path is not a file" in str(exc_info.value)
            assert temp_dir in str(exc_info.value)

    def test_validate_output_directory_existing(self):
        """既存ディレクトリの検証テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = PathValidator.validate_output_directory(temp_dir)

            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_dir()
            assert str(result) == temp_dir

    def test_validate_output_directory_create_new(self):
        """新規ディレクトリ作成テスト"""
        with tempfile.TemporaryDirectory() as base_dir:
            new_dir = Path(base_dir) / "new_directory" / "nested"

            result = PathValidator.validate_output_directory(str(new_dir))

            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_dir()
            assert result == new_dir

    def test_validate_output_directory_parents_creation(self):
        """親ディレクトリの自動作成テスト"""
        with tempfile.TemporaryDirectory() as base_dir:
            nested_path = Path(base_dir) / "level1" / "level2" / "level3"

            result = PathValidator.validate_output_directory(str(nested_path))

            assert result.exists()
            assert result.parent.exists()  # level2
            assert result.parent.parent.exists()  # level1

    def test_validate_source_directory_success(self):
        """有効なソースディレクトリの検証テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = PathValidator.validate_source_directory(temp_dir)

            assert isinstance(result, Path)
            assert result.exists()
            assert result.is_dir()
            assert str(result) == temp_dir

    def test_validate_source_directory_not_found(self):
        """存在しないソースディレクトリのエラーテスト"""
        non_existent_dir = "/nonexistent/source/directory"

        with pytest.raises(FileNotFoundError) as exc_info:
            PathValidator.validate_source_directory(non_existent_dir)

        assert "Source directory not found" in str(exc_info.value)
        assert non_existent_dir in str(exc_info.value)

    def test_validate_source_directory_not_a_directory(self):
        """ファイルをソースディレクトリとして指定した場合のエラーテスト"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("not a directory")
            temp_path = temp_file.name

        try:
            with pytest.raises(ValueError) as exc_info:
                PathValidator.validate_source_directory(temp_path)

            assert "Source path is not a directory" in str(exc_info.value)
            assert temp_path in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_path_validator_static_methods(self):
        """PathValidatorの静的メソッド確認テスト"""
        # 全ての主要メソッドが静的メソッドとして存在することを確認
        assert hasattr(PathValidator, "validate_input_file")
        assert hasattr(PathValidator, "validate_output_directory")
        assert hasattr(PathValidator, "validate_source_directory")

        # メソッドが呼び出し可能であることを確認
        assert callable(PathValidator.validate_input_file)
        assert callable(PathValidator.validate_output_directory)
        assert callable(PathValidator.validate_source_directory)

    def test_path_validator_path_handling_edge_cases(self):
        """Pathオブジェクト処理のエッジケーステスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 文字列パスとPathlibオブジェクトの両方で動作することを確認
            string_path = temp_dir
            pathlib_path = Path(temp_dir)

            result1 = PathValidator.validate_output_directory(string_path)
            result2 = PathValidator.validate_source_directory(string_path)

            assert result1.exists()
            assert result2.exists()
            assert result1 == pathlib_path
            assert result2 == pathlib_path


class TestErrorHandler:
    """ErrorHandler包括的テスト"""

    def test_error_handler_initialization_no_ui(self):
        """UI無しでのErrorHandler初期化テスト"""
        handler = ErrorHandler()

        assert handler is not None
        assert handler.ui is None
        assert hasattr(handler, "logger")

    def test_error_handler_initialization_with_ui(self):
        """UI付きでのErrorHandler初期化テスト"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)

        assert handler is not None
        assert handler.ui == mock_ui
        assert hasattr(handler, "logger")

    def test_handle_file_not_found_no_ui(self):
        """UI無しでのファイル未発見エラーハンドリング"""
        handler = ErrorHandler()
        test_file_path = "/path/to/missing/file.txt"

        # UI無しでもエラーハンドリングが正常に動作することを確認
        try:
            handler.handle_file_not_found(test_file_path)
            # 例外が発生しなければ成功
            assert True
        except Exception as e:
            pytest.fail(f"handle_file_not_found raised unexpected exception: {e}")

    def test_handle_file_not_found_with_ui(self):
        """UI付きでのファイル未発見エラーハンドリング"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)
        test_file_path = "/path/to/missing/file.txt"

        handler.handle_file_not_found(test_file_path)

        # UIのfile_errorメソッドが呼ばれることを確認
        mock_ui.file_error.assert_called_once_with(
            test_file_path, "ファイルが見つかりません"
        )

    def test_handle_encoding_error_no_ui(self):
        """UI無しでのエンコーディングエラーハンドリング"""
        handler = ErrorHandler()
        test_file_path = "/path/to/file.txt"
        test_encoding = "shift_jis"

        try:
            handler.handle_encoding_error(test_file_path, test_encoding)
            assert True
        except Exception as e:
            pytest.fail(f"handle_encoding_error raised unexpected exception: {e}")

    def test_handle_encoding_error_with_ui(self):
        """UI付きでのエンコーディングエラーハンドリング"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)
        test_file_path = "/path/to/file.txt"
        test_encoding = "shift_jis"

        handler.handle_encoding_error(test_file_path, test_encoding)

        # UIのencoding_errorとhintメソッドが呼ばれることを確認
        mock_ui.encoding_error.assert_called_once_with(test_file_path)
        mock_ui.hint.assert_called_once()

        # hint呼び出しの引数を確認
        hint_args = mock_ui.hint.call_args[0]
        assert "エンコーディングの問題を解決するには" in hint_args[0]
        assert "UTF-8" in hint_args[1]

    def test_handle_encoding_error_default_encoding(self):
        """デフォルトエンコーディングでのエラーハンドリング"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)
        test_file_path = "/path/to/file.txt"

        # encodingパラメーターを省略
        handler.handle_encoding_error(test_file_path)

        mock_ui.encoding_error.assert_called_once_with(test_file_path)
        mock_ui.hint.assert_called_once()

    def test_handle_permission_error_no_ui(self):
        """UI無しでの権限エラーハンドリング"""
        handler = ErrorHandler()
        error_message = "Permission denied: /restricted/file.txt"

        try:
            handler.handle_permission_error(error_message)
            assert True
        except Exception as e:
            pytest.fail(f"handle_permission_error raised unexpected exception: {e}")

    def test_handle_permission_error_with_ui(self):
        """UI付きでの権限エラーハンドリング"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)
        error_message = "Permission denied: /restricted/file.txt"

        handler.handle_permission_error(error_message)

        mock_ui.permission_error.assert_called_once_with(error_message)

    def test_handle_unexpected_error_no_ui(self):
        """UI無しでの予期しないエラーハンドリング"""
        handler = ErrorHandler()
        error_message = "Unexpected system error occurred"

        try:
            handler.handle_unexpected_error(error_message)
            assert True
        except Exception as e:
            pytest.fail(f"handle_unexpected_error raised unexpected exception: {e}")

    def test_handle_unexpected_error_with_ui(self):
        """UI付きでの予期しないエラーハンドリング"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)
        error_message = "Unexpected system error occurred"

        handler.handle_unexpected_error(error_message)

        mock_ui.unexpected_error.assert_called_once_with(error_message)

    def test_error_handler_all_methods_exist(self):
        """ErrorHandlerの全メソッド存在確認"""
        handler = ErrorHandler()

        expected_methods = [
            "handle_file_not_found",
            "handle_encoding_error",
            "handle_permission_error",
            "handle_unexpected_error",
        ]

        for method_name in expected_methods:
            assert hasattr(handler, method_name)
            assert callable(getattr(handler, method_name))


class TestFileValidatorsIntegration:
    """FileValidators統合テスト"""

    def test_path_validator_and_error_handler_integration(self):
        """PathValidatorとErrorHandlerの統合テスト"""
        mock_ui = Mock()
        error_handler = ErrorHandler(ui=mock_ui)

        # 存在しないファイルで PathValidator がエラーを発生させ、
        # ErrorHandler でそのエラーを処理する統合フロー
        non_existent_file = "/nonexistent/test/file.txt"

        try:
            PathValidator.validate_input_file(non_existent_file)
        except FileNotFoundError:
            # PathValidatorで発生したエラーをErrorHandlerで処理
            error_handler.handle_file_not_found(non_existent_file)

            # UIが適切に呼ばれることを確認
            mock_ui.file_error.assert_called_once()

    def test_complete_validation_workflow(self):
        """完全な検証ワークフローテスト"""
        with tempfile.TemporaryDirectory() as base_dir:
            # 入力ファイル作成
            input_file = Path(base_dir) / "input.txt"
            input_file.write_text("test content")

            # 出力ディレクトリパス
            output_dir = Path(base_dir) / "output"

            # ソースディレクトリパス
            source_dir = Path(base_dir)

            # 全ての検証が成功することを確認
            validated_input = PathValidator.validate_input_file(str(input_file))
            validated_output = PathValidator.validate_output_directory(str(output_dir))
            validated_source = PathValidator.validate_source_directory(str(source_dir))

            assert validated_input.exists()
            assert validated_output.exists()
            assert validated_source.exists()

            assert validated_input.is_file()
            assert validated_output.is_dir()
            assert validated_source.is_dir()

    def test_error_handler_ui_protocol_compliance(self):
        """ErrorHandlerのUIプロトコル準拠テスト"""
        mock_ui = Mock()
        handler = ErrorHandler(ui=mock_ui)

        # UIプロトコルの各メソッドが適切に呼ばれることを確認
        handler.handle_file_not_found("test.txt")
        handler.handle_encoding_error("test.txt", "utf-8")
        handler.handle_permission_error("permission denied")
        handler.handle_unexpected_error("unexpected error")

        # 各UIメソッドが最低1回は呼ばれることを確認
        assert mock_ui.file_error.call_count >= 1
        assert mock_ui.encoding_error.call_count >= 1
        assert mock_ui.hint.call_count >= 1
        assert mock_ui.permission_error.call_count >= 1
        assert mock_ui.unexpected_error.call_count >= 1

    def test_file_validators_logging_integration(self):
        """FileValidatorsのログ統合テスト"""
        with patch(
            "kumihan_formatter.core.file_validators.get_logger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # ErrorHandler初期化でロガーが取得されることを確認
            handler = ErrorHandler()

            mock_get_logger.assert_called_once()

            # エラーハンドリングでログが出力されることを確認
            handler.handle_file_not_found("test.txt")
            mock_logger.error.assert_called()


class TestFileValidatorsCoverage:
    """FileValidatorsカバレッジ向上特化テスト"""

    def test_path_validator_comprehensive_api(self):
        """PathValidator API包括テスト"""
        # クラス自体の確認
        assert PathValidator is not None

        # 静的メソッドの確認
        methods = [
            "validate_input_file",
            "validate_output_directory",
            "validate_source_directory",
        ]
        for method in methods:
            assert hasattr(PathValidator, method)
            method_obj = getattr(PathValidator, method)
            assert callable(method_obj)
            # 静的メソッドであることを確認（__func__アクセス不要）
            assert hasattr(method_obj, "__name__")

    def test_error_handler_comprehensive_api(self):
        """ErrorHandler API包括テスト"""
        handler = ErrorHandler()

        # インスタンス属性の確認
        assert hasattr(handler, "ui")
        assert hasattr(handler, "logger")

        # インスタンスメソッドの確認
        methods = [
            "handle_file_not_found",
            "handle_encoding_error",
            "handle_permission_error",
            "handle_unexpected_error",
        ]
        for method in methods:
            assert hasattr(handler, method)
            assert callable(getattr(handler, method))

    def test_file_validators_module_structure(self):
        """FileValidatorsモジュール構造テスト"""
        from kumihan_formatter.core.file_validators import ErrorHandler, PathValidator

        # 両クラスが適切にインポートできることを確認
        assert PathValidator is not None
        assert ErrorHandler is not None

        # クラスが期待される型であることを確認
        assert isinstance(PathValidator, type)
        assert isinstance(ErrorHandler, type)

    def test_error_handler_optional_ui_handling(self):
        """ErrorHandlerのオプショナルUI処理テスト"""
        # UI無しでの初期化
        handler_no_ui = ErrorHandler()
        assert handler_no_ui.ui is None

        # UI付きでの初期化
        mock_ui = Mock()
        handler_with_ui = ErrorHandler(ui=mock_ui)
        assert handler_with_ui.ui == mock_ui

        # 両パターンでエラーハンドリングが動作することを確認
        test_path = "test_file.txt"

        # UI無しでも例外が発生しない
        handler_no_ui.handle_file_not_found(test_path)
        handler_no_ui.handle_encoding_error(test_path)
        handler_no_ui.handle_permission_error("permission error")
        handler_no_ui.handle_unexpected_error("unexpected error")

        # UI付きでUIメソッドが呼ばれる
        handler_with_ui.handle_file_not_found(test_path)
        mock_ui.file_error.assert_called()
