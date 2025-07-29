#!/usr/bin/env python3
"""
Critical Tier Tests for SimpleMarkdownConverter - Issue #640
TDD-First開発システムに基づく90%カバレッジ達成のためのテスト

Critical Tier: Core機能・Commands（テストカバレッジ90%必須）
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import pytest

from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter


class TestSimpleMarkdownConverterCritical(unittest.TestCase):
    """SimpleMarkdownConverterのCritical Tierテスト"""

    def setUp(self):
        """テスト前準備"""
        self.converter = SimpleMarkdownConverter()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """テスト後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_components(self):
        """初期化時に必要なコンポーネントが作成されること"""
        converter = SimpleMarkdownConverter()
        self.assertIsNotNone(converter.parser)
        self.assertIsNotNone(converter.processor)
        self.assertIsNotNone(converter.renderer)
        self.assertIsNotNone(converter.patterns)

    def test_convert_file_with_valid_markdown(self):
        """有効なMarkdownファイルの変換が成功すること"""
        # テストファイル作成
        test_file = self.temp_dir / "test.md"
        test_content = "# Test Header\n\nThis is a test."
        test_file.write_text(test_content, encoding="utf-8")

        # 変換実行
        with patch.object(self.converter, 'convert_text') as mock_convert:
            mock_convert.return_value = "<h1>Test Header</h1><p>This is a test.</p>"
            with patch.object(self.converter, '_create_full_html') as mock_create:
                mock_create.return_value = "<html>Test</html>"
                
                result = self.converter.convert_file(test_file)
                
                self.assertEqual(result, "<html>Test</html>")
                mock_convert.assert_called_once_with(test_content)
                mock_create.assert_called_once()

    def test_convert_file_nonexistent_raises_error(self):
        """存在しないファイルの場合FileNotFoundErrorが発生すること"""
        nonexistent_file = self.temp_dir / "nonexistent.md"
        
        with self.assertRaises(FileNotFoundError) as context:
            self.converter.convert_file(nonexistent_file)
        
        self.assertIn("ファイルが見つかりません", str(context.exception))

    def test_convert_file_with_shift_jis_encoding(self):
        """Shift_JISエンコーディングのファイルも読み込めること"""
        test_file = self.temp_dir / "test_sjis.md"
        test_content = "# テストヘッダー\n\nこれはテストです。"
        test_file.write_text(test_content, encoding="shift_jis")

        # convert_textとcreate_full_htmlをモック
        with patch.object(self.converter, 'convert_text') as mock_convert:
            mock_convert.return_value = "<h1>テストヘッダー</h1><p>これはテストです。</p>"
            with patch.object(self.converter, '_create_full_html') as mock_create:
                mock_create.return_value = "<html>Test</html>"
                
                result = self.converter.convert_file(test_file)
                
                self.assertEqual(result, "<html>Test</html>")
                mock_convert.assert_called_once()

    def test_convert_custom_title_parameter(self):
        """カスタムタイトルパラメータが正しく処理されること"""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("# Header\n\nContent", encoding="utf-8")
        custom_title = "Custom Title"

        with patch.object(self.converter, 'convert_text') as mock_convert:
            mock_convert.return_value = "<h1>Header</h1><p>Content</p>"
            with patch.object(self.converter, '_create_full_html') as mock_create:
                mock_create.return_value = "<html>Custom</html>"
                
                result = self.converter.convert_file(test_file, title=custom_title)
                
                # カスタムタイトルが渡されることを確認
                self.assertEqual(result, "<html>Custom</html>")
                mock_create.assert_called_once_with(custom_title, "<h1>Header</h1><p>Content</p>", "test.md")

    def test_convert_empty_file(self):
        """空のファイルの処理が正しく行われること"""
        test_file = self.temp_dir / "empty.md"
        test_file.write_text("", encoding="utf-8")

        with patch.object(self.converter, 'convert_text') as mock_convert:
            mock_convert.return_value = ""
            with patch.object(self.converter, '_create_full_html') as mock_create:
                mock_create.return_value = "<html>Empty</html>"
                
                result = self.converter.convert_file(test_file)
                
                self.assertEqual(result, "<html>Empty</html>")
                mock_convert.assert_called_once_with("")

    def test_convert_file_with_special_characters(self):
        """特殊文字を含むファイルの処理が正しく行われること"""
        test_file = self.temp_dir / "special.md"
        test_content = "# Title & <Special>\n\n**Bold** _italic_ `code`"
        test_file.write_text(test_content, encoding="utf-8")

        with patch.object(self.converter, 'convert_text') as mock_convert:
            mock_convert.return_value = "<h1>Title &amp; &lt;Special&gt;</h1><p><strong>Bold</strong> <em>italic</em> <code>code</code></p>"
            with patch.object(self.converter, '_create_full_html') as mock_create:
                mock_create.return_value = "<html>Special</html>"
                
                result = self.converter.convert_file(test_file)
                
                self.assertEqual(result, "<html>Special</html>")
                mock_convert.assert_called_once_with(test_content)

    def test_patterns_attribute_accessible(self):
        """patternsアトリビュートがアクセス可能であること"""
        converter = SimpleMarkdownConverter()
        self.assertIsNotNone(converter.patterns)
        # パーサーのパターンと同じオブジェクトであることを確認
        self.assertIs(converter.patterns, converter.parser.patterns)


if __name__ == "__main__":
    unittest.main()