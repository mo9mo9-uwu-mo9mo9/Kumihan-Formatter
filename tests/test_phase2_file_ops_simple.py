"""Phase 2 File Operations Simple Tests - ファイル操作シンプルテスト

ファイル操作基本機能テスト - 実際の実装に合わせた簡易版
Target: file_operations.py の実際の機能
Goal: 動作するテストでカバレッジ向上
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.file_io_handler import FileIOHandler
from kumihan_formatter.core.file_operations import FileOperations


class TestFileOperationsSimple:
    """FileOperations シンプルテスト"""

    def test_file_operations_class_exists(self):
        """FileOperationsクラスの存在確認"""
        assert FileOperations is not None
        assert hasattr(FileOperations, "read_text_file")
        assert hasattr(FileOperations, "write_text_file")

    def test_file_operations_inheritance(self):
        """FileOperations継承確認"""
        file_ops = FileOperations()
        assert file_ops is not None
        assert hasattr(file_ops, "ui")

    def test_file_operations_static_methods(self):
        """静的メソッド確認"""
        # 静的メソッドが存在することを確認
        assert hasattr(FileOperations, "load_distignore_patterns")
        assert hasattr(FileOperations, "should_exclude")
        assert hasattr(FileOperations, "get_file_size_info")

    def test_file_io_handler_read_write(self):
        """FileIOHandler読み書きテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Simple test content"

            # 書き込み
            FileIOHandler.write_text_file(test_file, test_content)
            assert test_file.exists()

            # 読み込み
            result = FileIOHandler.read_text_file(test_file)
            assert result == test_content

    def test_file_operations_delegation(self):
        """FileOperations委譲テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "delegation_test.txt"
            test_content = "Delegation test content"

            # FileOperations経由での書き込み・読み込み
            FileOperations.write_text_file(test_file, test_content)
            result = FileOperations.read_text_file(test_file)

            assert result == test_content

    def test_file_operations_unicode_handling(self):
        """Unicode文字処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "unicode.txt"
            test_content = "Unicode: 日本語 🎌 émojis"

            FileOperations.write_text_file(test_file, test_content)
            result = FileOperations.read_text_file(test_file)

            assert result == test_content

    def test_file_operations_initialization_with_ui(self):
        """UI付き初期化テスト"""
        mock_ui = Mock()
        file_ops = FileOperations(ui=mock_ui)

        assert file_ops.ui == mock_ui

    def test_file_operations_multiple_instances(self):
        """複数インスタンステスト"""
        file_ops1 = FileOperations()
        file_ops2 = FileOperations()

        # 独立したインスタンスであることを確認
        assert file_ops1 is not file_ops2
        assert type(file_ops1) == type(file_ops2)

    def test_file_operations_error_handling(self):
        """エラーハンドリングテスト"""
        # 存在しないファイルの読み込み
        nonexistent = Path("/nonexistent/file.txt")

        with pytest.raises(Exception):  # FileNotFoundError or similar
            FileOperations.read_text_file(nonexistent)

    def test_file_operations_large_content(self):
        """大きなコンテンツ処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "large.txt"
            large_content = "Large content line\n" * 1000

            FileOperations.write_text_file(test_file, large_content)
            result = FileOperations.read_text_file(test_file)

            assert result == large_content

    def test_file_operations_empty_content(self):
        """空コンテンツ処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "empty.txt"
            empty_content = ""

            FileOperations.write_text_file(test_file, empty_content)
            result = FileOperations.read_text_file(test_file)

            assert result == empty_content

    def test_file_operations_special_characters(self):
        """特殊文字処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "special.txt"
            special_content = "Special: !@#$%^&*()[]{}|"

            FileOperations.write_text_file(test_file, special_content)
            result = FileOperations.read_text_file(test_file)

            assert result == special_content

    def test_file_operations_nested_directory(self):
        """ネストディレクトリ作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_file = Path(temp_dir) / "level1" / "level2" / "nested.txt"
            nested_content = "Nested directory content"

            # ディレクトリを手動作成
            nested_file.parent.mkdir(parents=True, exist_ok=True)

            # 書き込み・読み込みテスト
            FileOperations.write_text_file(nested_file, nested_content)
            result = FileOperations.read_text_file(nested_file)

            assert result == nested_content
            assert nested_file.exists()

    def test_file_operations_overwrite(self):
        """ファイル上書きテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "overwrite.txt"

            # 最初の書き込み
            FileOperations.write_text_file(test_file, "First content")
            first_result = FileOperations.read_text_file(test_file)
            assert first_result == "First content"

            # 上書き
            FileOperations.write_text_file(test_file, "Second content")
            second_result = FileOperations.read_text_file(test_file)
            assert second_result == "Second content"
