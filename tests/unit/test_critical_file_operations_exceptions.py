#!/usr/bin/env python3
"""
Critical Tier Tests for FileOperations Exception Handling - Issue #640 CRIT-003
TDD-First開発システムによる例外処理強化テスト

Critical Tier: Core機能・Commands（テストカバレッジ90%必須）
目的: ファイル操作における例外処理の堅牢性を確保
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest
import shutil
import errno

from kumihan_formatter.core.file_operations import FileOperations
from kumihan_formatter.core.file_operations_core import FileOperationsCore
from kumihan_formatter.core.file_io_handler import FileIOHandler


class TestFileOperationsCriticalExceptions(unittest.TestCase):
    """FileOperations例外処理のCritical Tierテスト"""

    def setUp(self):
        """テスト前準備"""
        self.file_ops = FileOperations()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """テスト後処理"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

    def test_copy_images_source_directory_not_exists(self):
        """ソース画像ディレクトリが存在しない場合の例外処理"""
        # テスト用のAST（画像ノード含む）
        mock_ast = [
            Mock(type="image", content="test_image.png"),
            Mock(type="text", content="some text")
        ]
        
        nonexistent_input = self.temp_dir / "nonexistent_file.txt"
        output_path = self.temp_dir / "output"
        output_path.mkdir(exist_ok=True)
        
        # 画像ディレクトリが存在しない状況でのテスト
        # 例外を投げずに適切に処理されることを確認
        try:
            self.file_ops.copy_images(nonexistent_input, output_path, mock_ast)
            # 例外が発生しないことを確認（適切な処理）
        except Exception as e:
            self.fail(f"copy_images should handle missing source directory gracefully, but raised: {e}")

    def test_copy_images_permission_denied_source(self):
        """ソースディレクトリの読み取り権限エラー処理"""
        input_file = self.temp_dir / "input.txt"
        input_file.write_text("test", encoding="utf-8")
        
        images_dir = input_file.parent / "images"
        images_dir.mkdir(exist_ok=True)
        
        test_image = images_dir / "test.png"
        test_image.write_text("fake image", encoding="utf-8")
        
        mock_ast = [Mock(type="image", content="test.png")]
        output_path = self.temp_dir / "output"
        output_path.mkdir(exist_ok=True)
        
        # ファイル読み取り権限を削除（Unix系のみ）
        if os.name != 'nt':  # Windows以外
            try:
                os.chmod(test_image, 0o000)
                self.file_ops.copy_images(input_file, output_path, mock_ast)
                # 適切に処理されることを確認
            finally:
                # 権限を復元してクリーンアップ
                os.chmod(test_image, 0o644)

    def test_copy_images_destination_write_error(self):
        """出力先への書き込み権限エラー処理"""
        input_file = self.temp_dir / "input.txt"
        input_file.write_text("test", encoding="utf-8")
        
        images_dir = input_file.parent / "images"
        images_dir.mkdir(exist_ok=True)
        test_image = images_dir / "test.png"
        test_image.write_text("fake image", encoding="utf-8")
        
        mock_ast = [Mock(type="image", content="test.png")]
        
        # 読み取り専用の出力ディレクトリ作成
        readonly_output = self.temp_dir / "readonly_output"
        readonly_output.mkdir(exist_ok=True)
        
        if os.name != 'nt':  # Windows以外
            try:
                os.chmod(readonly_output, 0o444)  # 読み取り専用
                
                # PermissionError が発生することを期待
                with self.assertRaises(PermissionError):
                    self.file_ops.copy_images(input_file, readonly_output, mock_ast)
                    
            finally:
                os.chmod(readonly_output, 0o755)  # 権限復元

    def test_file_io_handler_read_file_not_found(self):
        """存在しないファイルの読み取り例外処理"""
        nonexistent_file = self.temp_dir / "nonexistent.txt"
        
        with self.assertRaises(FileNotFoundError):
            FileIOHandler.read_text_file(nonexistent_file)

    def test_file_io_handler_read_permission_denied(self):
        """ファイル読み取り権限エラー処理"""
        test_file = self.temp_dir / "no_read_permission.txt"
        test_file.write_text("secret content", encoding="utf-8")
        
        if os.name != 'nt':  # Windows以外
            try:
                os.chmod(test_file, 0o000)  # アクセス権限なし
                
                with self.assertRaises(PermissionError):
                    FileIOHandler.read_text_file(test_file)
            finally:
                os.chmod(test_file, 0o644)  # 権限復元

    def test_file_io_handler_write_permission_denied(self):
        """ファイル書き込み権限エラー処理"""
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir(exist_ok=True)
        
        if os.name != 'nt':  # Windows以外
            try:
                os.chmod(readonly_dir, 0o444)  # 読み取り専用
                readonly_file = readonly_dir / "cannot_write.txt"
                
                with self.assertRaises(PermissionError):
                    FileIOHandler.write_text_file(readonly_file, "test content")
            finally:
                os.chmod(readonly_dir, 0o755)  # 権限復元

    def test_file_io_handler_disk_full_simulation(self):
        """ディスク容量不足のシミュレーション"""
        test_file = self.temp_dir / "test_disk_full.txt"
        
        # OSErrorをモック化してディスク容量不足をシミュレート
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = OSError(errno.ENOSPC, "No space left on device")
            
            with self.assertRaises(OSError) as context:
                FileIOHandler.write_text_file(test_file, "test content")
            
            # エラーコードがディスク容量不足であることを確認
            self.assertEqual(context.exception.errno, errno.ENOSPC)

    def test_file_operations_unicode_encoding_error(self):
        """Unicode エンコーディングエラー処理テスト"""
        test_file = self.temp_dir / "unicode_test.txt"
        
        # 不正なUTF-8シーケンスを書き込み
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xfe')  # 不正なUTF-8
        
        # UnicodeDecodeError が適切に処理されることを確認
        try:
            content = FileIOHandler.read_text_file(test_file)
            # 何らかのフォールバック処理が行われることを期待
        except UnicodeDecodeError:
            # UnicodeDecodeErrorが発生する場合もある（実装によって異なる）
            pass
        except Exception as e:
            # その他の適切な例外処理
            self.assertIsInstance(e, (UnicodeDecodeError, UnicodeError))

    def test_large_file_handling(self):
        """大容量ファイル処理の例外処理テスト"""
        large_file = self.temp_dir / "large_file.txt"
        
        # メモリ制限をシミュレート
        with patch('builtins.open') as mock_open_func:
            mock_open_func.side_effect = MemoryError("Cannot allocate memory")
            
            with self.assertRaises(MemoryError):
                FileIOHandler.read_text_file(large_file)

    def test_concurrent_file_access_error(self):
        """同時ファイルアクセスエラー処理"""
        test_file = self.temp_dir / "concurrent_access.txt"
        test_file.write_text("initial content", encoding="utf-8")
        
        # ファイルがロックされている状況をシミュレート
        with patch('builtins.open') as mock_open_func:
            mock_open_func.side_effect = OSError(errno.EACCES, "Permission denied")
            
            with self.assertRaises(OSError) as context:
                FileIOHandler.read_text_file(test_file)
            
            self.assertEqual(context.exception.errno, errno.EACCES)

    def test_network_drive_access_error(self):
        """ネットワークドライブアクセスエラー処理"""
        network_file = Path("//nonexistent/share/file.txt")
        
        # ネットワークエラーをシミュレート
        with self.assertRaises((FileNotFoundError, OSError)):
            FileIOHandler.read_text_file(network_file)


if __name__ == "__main__":
    unittest.main()