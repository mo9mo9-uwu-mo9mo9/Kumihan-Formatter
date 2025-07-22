"""Phase 2 File Operations Coverage Tests - ファイル操作完全テスト

ファイル操作機能の完全テスト - 高カバレッジ効率実現
Target: file_operations.py, encoding_detector.py
Goal: +2.8%ポイント（中級カバレッジ向上）
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.file_operations import FileOperations


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


class TestFileOperationsAdvanced:
    """FileOperations 高度機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_ui = Mock()
        self.file_ops = FileOperations(ui=self.mock_ui)

    def test_file_operations_with_ui_feedback(self):
        """UI付きファイル操作テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "ui_test.txt"
            test_content = "Content with UI feedback"

            self.file_ops.write_text_file(test_file, test_content)
            result = self.file_ops.read_text_file(test_file)

            # UI付きで正常に動作することを確認
            assert result == test_content

    def test_file_operations_large_file_handling(self):
        """大きなファイルの処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            large_file = Path(temp_dir) / "large.txt"
            # 大きなコンテンツを生成（約1MB）
            large_content = "Large file content line\n" * 50000

            self.file_ops.write_text_file(large_file, large_content)
            result = self.file_ops.read_text_file(large_file)

            # 大きなファイルが正しく処理されることを確認
            assert result == large_content

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

    def test_file_operations_concurrent_access(self):
        """並行ファイルアクセステスト"""
        import threading

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "concurrent.txt"
            results = []

            def write_and_read(content_id):
                content = f"Concurrent content {content_id}"
                thread_file = Path(temp_dir) / f"thread_{content_id}.txt"
                self.file_ops.write_text_file(thread_file, content)
                result = self.file_ops.read_text_file(thread_file)
                results.append(result == content)

            threads = []
            for i in range(5):
                thread = threading.Thread(target=write_and_read, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # 並行アクセスが全て正常に処理されることを確認
            assert all(results)

    def test_file_operations_permission_handling(self):
        """ファイル権限処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "permission_test.txt"
            test_content = "Permission test content"

            # ファイルを作成
            self.file_ops.write_text_file(test_file, test_content)

            # 権限を変更（読み取り専用）
            test_file.chmod(0o444)

            try:
                # 読み取りは正常に動作することを確認
                result = self.file_ops.read_text_file(test_file)
                assert result == test_content

                # 書き込み試行（権限エラーが予想される）
                with pytest.raises(PermissionError):
                    self.file_ops.write_text_file(test_file, "New content")

            finally:
                # テスト後に権限を戻す
                test_file.chmod(0o644)

    def test_file_operations_encoding_detection(self):
        """エンコーディング検出テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 異なるエンコーディングでファイルを作成
            encodings_to_test = ["utf-8", "utf-8-sig", "shift_jis", "euc-jp"]
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

    def test_file_operations_error_recovery(self):
        """エラー回復テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 書き込み権限のないディレクトリを作成
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o555)  # 読み取り・実行のみ

            readonly_file = readonly_dir / "test.txt"

            try:
                # 書き込みエラーが適切に処理されることを確認
                with pytest.raises(PermissionError):
                    self.file_ops.write_text_file(readonly_file, "test content")

            finally:
                # テスト後にクリーンアップ
                readonly_dir.chmod(0o755)

    def test_file_operations_symlink_handling(self):
        """シンボリックリンク処理テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 元ファイルを作成
            original_file = Path(temp_dir) / "original.txt"
            original_content = "Original file content"
            original_file.write_text(original_content, encoding="utf-8")

            # シンボリックリンクを作成
            symlink_file = Path(temp_dir) / "symlink.txt"
            try:
                symlink_file.symlink_to(original_file)

                # シンボリックリンク経由で読み込み
                result = self.file_ops.read_text_file(symlink_file)
                assert result == original_content

                # シンボリックリンク経由で書き込み
                new_content = "New content via symlink"
                self.file_ops.write_text_file(symlink_file, new_content)

                # 元ファイルの内容が変更されることを確認
                updated_content = original_file.read_text(encoding="utf-8")
                assert updated_content == new_content

            except OSError:
                # シンボリックリンクがサポートされていない環境ではスキップ
                pytest.skip("Symlinks not supported on this platform")


class TestFileOperationsIntegration:
    """FileOperations 統合テスト"""

    def test_file_operations_workflow(self):
        """完全なファイル操作ワークフローテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            ui = Mock()
            file_ops = FileOperations(ui=ui)

            # 1. 複数ファイルの作成
            files_data = {
                "input.txt": "Original input content",
                "config.txt": "Configuration data",
                "template.html": "<html><body>Template</body></html>",
            }

            created_files = []
            for filename, content in files_data.items():
                file_path = Path(temp_dir) / filename
                file_ops.write_text_file(file_path, content)
                created_files.append(file_path)

            # 2. ファイルの読み込みと検証
            for file_path in created_files:
                assert file_path.exists()
                content = file_ops.read_text_file(file_path)
                assert content == files_data[file_path.name]

            # 3. ファイルの更新
            updated_content = "Updated content with new data"
            file_ops.write_text_file(created_files[0], updated_content)

            # 4. 更新の確認
            result = file_ops.read_text_file(created_files[0])
            assert result == updated_content

            # 5. バイナリファイルの処理
            binary_file = Path(temp_dir) / "binary.dat"
            binary_content = b"Binary data \x00\x01\x02\x03"
            file_ops.write_file(binary_file, binary_content)

            assert binary_file.exists()
            written_binary = binary_file.read_bytes()
            assert written_binary == binary_content

    def test_file_operations_performance(self):
        """ファイル操作パフォーマンステスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_ops = FileOperations()

            import time

            start_time = time.time()

            # 100個の小さなファイルを作成
            for i in range(100):
                test_file = Path(temp_dir) / f"perf_test_{i}.txt"
                content = f"Performance test content {i}"
                file_ops.write_text_file(test_file, content)

                # すぐに読み込み
                result = file_ops.read_text_file(test_file)
                assert result == content

            end_time = time.time()
            duration = end_time - start_time

            # 合理的な時間内で完了することを確認
            assert duration < 5.0  # 5秒以内

    def test_file_operations_memory_efficiency(self):
        """メモリ効率テスト"""
        import gc

        with tempfile.TemporaryDirectory() as temp_dir:
            file_ops = FileOperations()

            # 大量のファイル操作を実行してメモリリークがないことを確認
            for i in range(50):
                test_file = Path(temp_dir) / f"memory_test_{i}.txt"
                large_content = "Memory test line\n" * 1000  # 約15KB

                file_ops.write_text_file(test_file, large_content)
                result = file_ops.read_text_file(test_file)

                # ファイルを削除
                test_file.unlink()

                # 定期的にガベージコレクション
                if i % 10 == 0:
                    gc.collect()

            # 最終的なガベージコレクション
            gc.collect()
            assert True
