"""
file_operations.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - file_operations.py分割
"""

from pathlib import Path
from unittest.mock import Mock

import pytest


class TestFileOperationsCore:
    """ファイル操作コアのテスト"""

    def test_file_operations_core_import(self):
        """RED: ファイル操作コアモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

    def test_file_operations_core_initialization(self):
        """RED: ファイル操作コア初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            mock_ui = Mock()
            ops = FileOperationsCore(mock_ui)

    def test_copy_images_method(self):
        """RED: 画像コピーメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            mock_ui = Mock()
            ops = FileOperationsCore(mock_ui)
            ops.copy_images(Path("input"), Path("output"), [])

    def test_create_sample_images_method(self):
        """RED: サンプル画像作成メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            FileOperationsCore.create_sample_images(Path("images"), {})

    def test_copy_directory_with_exclusions_method(self):
        """RED: 除外パターン付きディレクトリコピーメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            result = FileOperationsCore.copy_directory_with_exclusions(
                Path("src"), Path("dst"), ["*.tmp"]
            )

    def test_find_preview_file_method(self):
        """RED: プレビューファイル検索メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            result = FileOperationsCore.find_preview_file(Path("."))

    def test_ensure_directory_method(self):
        """RED: ディレクトリ作成メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            FileOperationsCore.ensure_directory(Path("test"))

    def test_check_large_file_warning_method(self):
        """RED: 大規模ファイル警告メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_core import FileOperationsCore

            mock_ui = Mock()
            ops = FileOperationsCore(mock_ui)
            result = ops.check_large_file_warning(Path("test.txt"))


class TestFilePathUtilities:
    """ファイルパスユーティリティのテスト"""

    def test_file_path_utilities_import(self):
        """RED: ファイルパスユーティリティモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_path_utilities import FilePathUtilities

    def test_load_distignore_patterns_method(self):
        """RED: distignoreパターン読み込みメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_path_utilities import FilePathUtilities

            patterns = FilePathUtilities.load_distignore_patterns()

    def test_should_exclude_method(self):
        """RED: 除外判定メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_path_utilities import FilePathUtilities

            result = FilePathUtilities.should_exclude(
                Path("test.tmp"), ["*.tmp"], Path(".")
            )

    def test_get_file_size_info_method(self):
        """RED: ファイルサイズ情報取得メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_path_utilities import FilePathUtilities

            info = FilePathUtilities.get_file_size_info(Path("test.txt"))

    def test_estimate_processing_time_method(self):
        """RED: 処理時間推定メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_path_utilities import FilePathUtilities

            time_estimate = FilePathUtilities.estimate_processing_time(10.0)


class TestFileIOHandler:
    """ファイルI/Oハンドラーのテスト"""

    def test_file_io_handler_import(self):
        """RED: ファイルI/Oハンドラーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_io_handler import FileIOHandler

    def test_write_text_file_method(self):
        """RED: テキストファイル書き込みメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_io_handler import FileIOHandler

            FileIOHandler.write_text_file(Path("test.txt"), "content")

    def test_read_text_file_method(self):
        """RED: テキストファイル読み込みメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_io_handler import FileIOHandler

            content = FileIOHandler.read_text_file(Path("test.txt"))


class TestFileOperationsFactory:
    """ファイル操作ファクトリーのテスト"""

    def test_file_operations_factory_import(self):
        """RED: ファイル操作ファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_factory import (
                create_file_operations,
            )

    def test_create_file_operations_function(self):
        """RED: ファイル操作作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_factory import (
                create_file_operations,
            )

            mock_ui = Mock()
            ops = create_file_operations(mock_ui)

    def test_create_file_io_handler_function(self):
        """RED: ファイルI/Oハンドラー作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_factory import (
                create_file_io_handler,
            )

            handler = create_file_io_handler()

    def test_create_file_path_utilities_function(self):
        """RED: ファイルパスユーティリティ作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.file_operations_factory import (
                create_file_path_utilities,
            )

            utils = create_file_path_utilities()


class TestOriginalFileOperations:
    """元のfile_operationsモジュールとの互換性テスト"""

    def test_original_file_operations_still_works(self):
        """元のfile_operationsが正常動作することを確認"""
        from kumihan_formatter.core.file_operations import FileOperations

        # 基本クラスが存在することを確認
        assert FileOperations is not None

    def test_file_operations_initialization(self):
        """元のFileOperations初期化テスト"""
        from unittest.mock import Mock

        from kumihan_formatter.core.file_operations import FileOperations

        mock_ui = Mock()
        ops = FileOperations(mock_ui)

        # 基本メソッドが存在することを確認
        assert hasattr(ops, "copy_images")
        assert hasattr(ops, "check_large_file_warning")

    def test_static_methods_exist(self):
        """静的メソッドが存在することを確認"""
        from kumihan_formatter.core.file_operations import FileOperations

        # 静的メソッドが存在することを確認
        assert hasattr(FileOperations, "load_distignore_patterns")
        assert hasattr(FileOperations, "should_exclude")
        assert hasattr(FileOperations, "create_sample_images")
        assert hasattr(FileOperations, "copy_directory_with_exclusions")
        assert hasattr(FileOperations, "find_preview_file")
        assert hasattr(FileOperations, "ensure_directory")
        assert hasattr(FileOperations, "write_text_file")
        assert hasattr(FileOperations, "read_text_file")
        assert hasattr(FileOperations, "get_file_size_info")
        assert hasattr(FileOperations, "estimate_processing_time")

    def test_basic_functionality(self):
        """基本機能のテスト"""
        from pathlib import Path

        from kumihan_formatter.core.file_operations import FileOperations

        # get_file_size_info メソッドの基本動作
        info = FileOperations.get_file_size_info(Path("nonexistent.txt"))
        assert info["size_bytes"] == 0
        assert info["size_mb"] == 0.0
        assert info["is_large"] is False

    def test_exclusion_functionality(self):
        """除外機能のテスト"""
        from pathlib import Path

        from kumihan_formatter.core.file_operations import FileOperations

        # should_exclude メソッドの基本動作
        result = FileOperations.should_exclude(Path("test.tmp"), ["*.tmp"], Path("."))
        assert isinstance(result, bool)

    def test_processing_time_estimation(self):
        """処理時間推定のテスト"""
        from kumihan_formatter.core.file_operations import FileOperations

        # estimate_processing_time メソッドの基本動作
        time_str = FileOperations.estimate_processing_time(0.5)
        assert isinstance(time_str, str)
        assert "秒" in time_str

    def test_distignore_patterns_loading(self):
        """distignoreパターン読み込みのテスト"""
        from kumihan_formatter.core.file_operations import FileOperations

        # load_distignore_patterns メソッドの基本動作
        patterns = FileOperations.load_distignore_patterns()
        assert isinstance(patterns, list)
