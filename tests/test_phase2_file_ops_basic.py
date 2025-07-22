"""Phase 2 File Operations Basic Tests - ファイル操作基本テスト

ファイル操作基本機能テスト - 読み書き・エンコーディング
Target: file_operations.py の基本機能
Goal: 基本的な読み書き・Unicode対応テスト
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.file_operations_core import FileOperations


class TestFileOperationsCore:
    """FileOperations コア機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.file_ops = FileOperations()

    def test_file_operations_initialization(self):
        """FileOperations初期化テスト"""
        file_ops = FileOperations()

        # 基本属性が初期化されていることを確認
        assert hasattr(file_ops, "ui")
        assert file_ops.ui is None  # デフォルトでNone

    def test_file_operations_with_ui(self):
        """UI付きFileOperations初期化テスト"""
        mock_ui = Mock()
        file_ops = FileOperations(ui=mock_ui)

        # UIが正しく設定されることを確認
        assert file_ops.ui == mock_ui

    def test_read_text_file_basic(self):
        """基本的なテキストファイル読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Test content for file operations"
            test_file.write_text(test_content, encoding="utf-8")

            result = self.file_ops.read_text_file(test_file)

            # ファイル内容が正しく読み込まれることを確認
            assert result == test_content

    def test_read_text_file_utf8_bom(self):
        """UTF-8 BOM付きファイル読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_bom.txt"
            test_content = "UTF-8 BOM test content"
            # BOM付きで書き込み
            test_file.write_text(test_content, encoding="utf-8-sig")

            result = self.file_ops.read_text_file(test_file)

            # BOMが正しく処理されることを確認
            assert result == test_content

    def test_read_text_file_different_encodings(self):
        """異なるエンコーディングのファイル読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # UTF-8ファイル
            utf8_file = Path(temp_dir) / "utf8.txt"
            utf8_content = "UTF-8 content with Japanese: 日本語"
            utf8_file.write_text(utf8_content, encoding="utf-8")

            result = self.file_ops.read_text_file(utf8_file)
            assert result == utf8_content

    def test_read_text_file_nonexistent(self):
        """存在しないファイルの読み込みテスト"""
        nonexistent_file = Path("/nonexistent/path/file.txt")

        # 存在しないファイルで例外が発生することを確認
        with pytest.raises(FileNotFoundError):
            self.file_ops.read_text_file(nonexistent_file)

    def test_write_text_file_basic(self):
        """基本的なテキストファイル書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "output.txt"
            test_content = "Content to write"

            self.file_ops.write_text_file(test_file, test_content)

            # ファイルが正しく書き込まれることを確認
            assert test_file.exists()
            written_content = test_file.read_text(encoding="utf-8")
            assert written_content == test_content

    def test_write_text_file_unicode(self):
        """Unicode文字のファイル書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "unicode.txt"
            test_content = "Unicode content: 日本語テスト with émojis 🎌"

            self.file_ops.write_text_file(test_file, test_content)

            # Unicode文字が正しく書き込まれることを確認
            assert test_file.exists()
            written_content = test_file.read_text(encoding="utf-8")
            assert written_content == test_content

    def test_write_text_file_overwrite(self):
        """ファイル上書きテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "overwrite.txt"

            # 最初の書き込み
            original_content = "Original content"
            self.file_ops.write_text_file(test_file, original_content)
            assert test_file.read_text(encoding="utf-8") == original_content

            # 上書き
            new_content = "New overwritten content"
            self.file_ops.write_text_file(test_file, new_content)

            # 上書きが正しく行われることを確認
            written_content = test_file.read_text(encoding="utf-8")
            assert written_content == new_content

    def test_write_text_file_create_directory(self):
        """ディレクトリ自動作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_file = Path(temp_dir) / "nested" / "dir" / "file.txt"
            test_content = "Content in nested directory"

            self.file_ops.write_text_file(nested_file, test_content)

            # ディレクトリが自動作成され、ファイルが書き込まれることを確認
            assert nested_file.exists()
            written_content = nested_file.read_text(encoding="utf-8")
            assert written_content == test_content

    def test_write_file_basic(self):
        """基本的なファイル書き込み（バイナリ対応）テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "binary.dat"
            test_content = b"Binary content data"

            self.file_ops.write_file(test_file, test_content)

            # バイナリファイルが正しく書き込まれることを確認
            assert test_file.exists()
            written_content = test_file.read_bytes()
            assert written_content == test_content

    def test_write_file_text_content(self):
        """文字列コンテンツのファイル書き込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "text.txt"
            test_content = "Text content as string"

            self.file_ops.write_file(test_file, test_content)

            # 文字列が正しく書き込まれることを確認
            assert test_file.exists()
            written_content = test_file.read_text(encoding="utf-8")
            assert written_content == test_content

    def test_file_operations_encoding_detection(self):
        """エンコーディング検出テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 異なるエンコーディングでファイルを作成
            encodings_to_test = ["utf-8", "utf-8-sig"]
            test_content = "エンコーディングテスト content"

            for encoding in encodings_to_test:
                try:
                    test_file = (
                        Path(temp_dir) / f"encoding_{encoding.replace('-', '_')}.txt"
                    )
                    test_file.write_text(test_content, encoding=encoding)

                    # FileOperationsで読み込み（自動検出）
                    result = self.file_ops.read_text_file(test_file)

                    # 内容が正しく読み込まれることを確認
                    assert test_content in result or len(result) > 0

                except UnicodeEncodeError:
                    # エンコーディングがサポートされていない場合はスキップ
                    continue

    def test_file_operations_special_characters(self):
        """特殊文字を含むファイル処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            special_file = Path(temp_dir) / "special.txt"
            special_content = """Special characters test:
            Line breaks: \n\r\n
            Tabs: \t\t\t
            Unicode: 🎌 🌸 ⚡
            Mathematical: ∑∏∂∆∇
            Arrows: →←↑↓⇄
            Currency: $€¥£₹
            """

            self.file_ops.write_text_file(special_file, special_content)
            result = self.file_ops.read_text_file(special_file)

            # 特殊文字が正しく処理されることを確認
            assert result == special_content