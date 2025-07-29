#!/usr/bin/env python3
"""
Critical Tier Tests for CheckSyntaxCommand - Issue #640
TDD-First開発システムに基づく90%カバレッジ達成のためのテスト

Critical Tier: Core機能・Commands（テストカバレッジ90%必須）
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import pytest

from kumihan_formatter.commands.check_syntax import CheckSyntaxCommand
from kumihan_formatter.core.syntax import ErrorSeverity


class TestCheckSyntaxCommandCritical(unittest.TestCase):
    """CheckSyntaxCommandのCritical Tierテスト"""

    def setUp(self):
        """テスト前準備"""
        self.command = CheckSyntaxCommand()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """テスト後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_method_alias(self):
        """checkメソッドがexecuteメソッドのエイリアスとして動作すること"""
        test_files = ["test.txt"]
        
        with patch.object(self.command, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = self.command.check(test_files, recursive=True)
            
            self.assertEqual(result, {"status": "success"})
            mock_execute.assert_called_once_with(test_files, recursive=True)

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_single_file_success(self, mock_console, mock_check_files):
        """単一ファイルのチェックが成功すること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("test content", encoding="utf-8")
        
        # Mock設定
        mock_check_files.return_value = {"errors": []}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file])
        
        self.assertEqual(result["success"], True)
        self.assertEqual(result["error_count"], 0)
        mock_check_files.assert_called_once()
        mock_ui.success.assert_called()

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_with_errors(self, mock_console, mock_check_files):
        """エラーがある場合の処理が正しく行われること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("error content", encoding="utf-8")
        
        # Mock設定
        mock_errors = [
            {
                "file": test_file,
                "line": 1,
                "column": 1,
                "severity": ErrorSeverity.ERROR,
                "message": "Test error",
                "suggestion": "Fix this"
            }
        ]
        mock_check_files.return_value = {"errors": mock_errors}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file])
        
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_count"], 1)
        mock_ui.error.assert_called()

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_recursive_directory(self, mock_console, mock_check_files):
        """ディレクトリの再帰的チェックが正しく動作すること"""
        # サブディレクトリとファイルを作成
        sub_dir = self.temp_dir / "subdir"
        sub_dir.mkdir()
        (self.temp_dir / "test1.txt").write_text("content1", encoding="utf-8")
        (sub_dir / "test2.txt").write_text("content2", encoding="utf-8")
        
        mock_check_files.return_value = {"errors": []}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([str(self.temp_dir)], recursive=True)
        
        self.assertEqual(result["success"], True)
        # check_filesが呼ばれたことを確認
        mock_check_files.assert_called_once()
        args = mock_check_files.call_args[0][0]
        # 再帰的にファイルが収集されていることを確認
        self.assertGreaterEqual(len(args), 2)

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_json_format_output(self, mock_console, mock_check_files):
        """JSON形式の出力が正しく行われること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("test content", encoding="utf-8")
        
        mock_check_files.return_value = {"errors": []}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file], format_output="json")
        
        self.assertEqual(result["success"], True)

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_no_suggestions(self, mock_console, mock_check_files):
        """提案を表示しない設定が正しく動作すること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("error content", encoding="utf-8")
        
        mock_errors = [
            {
                "file": test_file,
                "line": 1,
                "column": 1,
                "severity": ErrorSeverity.ERROR,
                "message": "Test error",
                "suggestion": "Fix this"
            }
        ]
        mock_check_files.return_value = {"errors": mock_errors}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file], show_suggestions=False)
        
        self.assertEqual(result["success"], False)

    def test_execute_empty_file_list(self):
        """空のファイルリストが渡された場合の処理"""
        with patch('kumihan_formatter.commands.check_syntax.get_console_ui') as mock_console:
            with patch('sys.exit') as mock_exit:
                mock_ui = MagicMock()
                mock_console.return_value = mock_ui
                
                self.command.execute([])
                
                mock_exit.assert_called_once_with(1)
                mock_ui.error.assert_called_with("チェックするファイルが見つかりません")

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_exception_handling(self, mock_console, mock_check_files):
        """例外が発生した場合の処理が正しく行われること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("test content", encoding="utf-8")
        
        # check_filesで例外を発生させる
        mock_check_files.side_effect = Exception("Test exception")
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file])
        
        self.assertEqual(result["success"], False)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test exception")
        mock_ui.error.assert_called_with("構文チェック中にエラーが発生しました: Test exception")

    @patch('kumihan_formatter.commands.check_syntax.check_files')
    @patch('kumihan_formatter.commands.check_syntax.get_console_ui')
    def test_execute_with_warnings(self, mock_console, mock_check_files):
        """警告レベルのエラーが正しく処理されること"""
        test_file = str(self.temp_dir / "test.txt")
        Path(test_file).write_text("warning content", encoding="utf-8")
        
        mock_errors = [
            {
                "file": test_file,
                "line": 1,
                "column": 1,
                "severity": ErrorSeverity.WARNING,
                "message": "Test warning",
                "suggestion": None
            }
        ]
        mock_check_files.return_value = {"errors": mock_errors}
        mock_ui = MagicMock()
        mock_console.return_value = mock_ui
        
        result = self.command.execute([test_file])
        
        # 警告の場合もエラーとして扱われることを確認
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error_count"], 1)


if __name__ == "__main__":
    unittest.main()