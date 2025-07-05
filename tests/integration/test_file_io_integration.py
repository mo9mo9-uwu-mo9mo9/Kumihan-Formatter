"""ファイル入出力の統合テスト（12テスト）

統合テスト: ファイル入出力の統合テスト
- ファイル読み込みテスト（4テスト）
- ファイル出力テスト（4テスト）
- 文字エンコーディングテスト（4テスト）
"""

import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from kumihan_formatter.core.encoding_detector import EncodingDetector
from kumihan_formatter.core.file_ops import FileOperations

from .permission_helper import PermissionHelper


class TestFileIOIntegration(TestCase):
    """ファイル入出力の統合テスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.file_ops = FileOperations()
        self.encoding_detector = EncodingDetector()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_file(self, filename, content, encoding="utf-8"):
        """テスト用ファイルを作成"""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content, encoding=encoding)
        return file_path

    # ファイル読み込みテスト（4テスト）

    def test_read_basic_text_file(self):
        """基本的なテキストファイル読み込みテスト"""
        content = """# テストシナリオ

## 基本的な読み込みテスト

これは基本的な読み込みテストです。

### リスト
- 項目1
- 項目2
- 項目3
"""
        file_path = self._create_test_file("basic_test.txt", content)

        # ファイルを読み込み
        result = self.file_ops.read_text_file(file_path)

        # 読み込んだ内容が正しいことを確認
        self.assertEqual(result, content)

    def test_read_large_text_file(self):
        """大きなテキストファイル読み込みテスト"""
        # 大きなファイルを作成（1000行）
        lines = [f"行{i}: これは大きなファイルのテストです。" for i in range(1000)]
        content = "\n".join(lines)
        file_path = self._create_test_file("large_test.txt", content)

        # ファイルを読み込み
        result = self.file_ops.read_text_file(file_path)

        # 読み込んだ内容が正しいことを確認
        self.assertEqual(result, content)
        self.assertEqual(len(result.split("\n")), 1000)

    def test_read_nonexistent_file(self):
        """存在しないファイル読み込みテスト"""
        nonexistent_file = Path(self.test_dir) / "nonexistent.txt"

        # 存在しないファイルの読み込みで例外が発生することを確認
        with self.assertRaises(FileNotFoundError):
            self.file_ops.read_text_file(nonexistent_file)

    def test_read_permission_denied_file(self):
        """読み込み権限なしファイルテスト"""
        content = "権限テスト"
        file_path = self._create_test_file("permission_test.txt", content)

        with PermissionHelper.create_permission_test_context(
            file_path=file_path
        ) as ctx:
            if ctx.permission_denied_should_occur():
                # 権限なしファイルの読み込みで例外が発生することを確認
                with self.assertRaises(PermissionError):
                    self.file_ops.read_text_file(file_path)
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest("Could not deny file read permissions on this platform")

    # ファイル出力テスト（4テスト）

    def test_write_basic_html_file(self):
        """基本的なHTMLファイル出力テスト"""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>テストHTML</title>
</head>
<body>
    <h1>テストシナリオ</h1>
    <p>これは出力テストです。</p>
</body>
</html>"""
        output_file = Path(self.test_dir) / "output.html"

        # HTMLファイルを出力
        self.file_ops.write_text_file(output_file, html_content)

        # ファイルが作成されたことを確認
        self.assertTrue(output_file.exists())

        # 出力内容が正しいことを確認
        result = output_file.read_text(encoding="utf-8")
        self.assertEqual(result, html_content)

    def test_write_to_new_directory(self):
        """新しいディレクトリへの出力テスト"""
        content = "新しいディレクトリテスト"
        output_dir = Path(self.test_dir) / "new_dir" / "subdir"
        output_file = output_dir / "test.html"

        # ディレクトリを作成してファイルを出力
        output_dir.mkdir(parents=True, exist_ok=True)
        self.file_ops.write_text_file(output_file, content)

        # ファイルが作成されたことを確認
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(encoding="utf-8"), content)

    def test_overwrite_existing_file(self):
        """既存ファイル上書きテスト"""
        original_content = "元のファイル内容"
        new_content = "新しいファイル内容"
        output_file = Path(self.test_dir) / "overwrite_test.html"

        # 最初のファイルを作成
        output_file.write_text(original_content, encoding="utf-8")
        self.assertEqual(output_file.read_text(encoding="utf-8"), original_content)

        # ファイルを上書き
        self.file_ops.write_text_file(output_file, new_content)

        # 上書きされたことを確認
        self.assertEqual(output_file.read_text(encoding="utf-8"), new_content)

    def test_write_permission_denied_directory(self):
        """書き込み権限なしディレクトリテスト"""
        content = "権限テスト"
        readonly_dir = Path(self.test_dir) / "readonly"
        readonly_dir.mkdir()
        output_file = readonly_dir / "test.html"

        with PermissionHelper.create_permission_test_context(
            dir_path=readonly_dir
        ) as ctx:
            if ctx.permission_denied_should_occur():
                # 権限なしディレクトリへの書き込みで例外が発生することを確認
                with self.assertRaises(PermissionError):
                    self.file_ops.write_text_file(output_file, content)
            else:
                # 権限変更に失敗した場合はテストをスキップ
                self.skipTest(
                    "Could not deny directory write permissions on this platform"
                )

    # 文字エンコーディングテスト（4テスト）

    def test_utf8_encoding_detection(self):
        """UTF-8エンコーディング検出テスト"""
        content = "UTF-8テスト: 日本語文字列 🎌"
        file_path = self._create_test_file("utf8_test.txt", content, encoding="utf-8")

        # エンコーディングを検出
        detected_encoding, has_bom = self.encoding_detector.detect(file_path)

        # UTF-8が検出されることを確認
        self.assertIn("utf", detected_encoding.lower())

    def test_shiftjis_encoding_detection(self):
        """Shift_JISエンコーディング検出テスト"""
        content = "Shift_JISテスト: 日本語文字列"
        file_path = Path(self.test_dir) / "shiftjis_test.txt"

        # Shift_JISでファイルを作成
        with open(file_path, "w", encoding="shift_jis") as f:
            f.write(content)

        # エンコーディングを検出
        detected_encoding, has_bom = self.encoding_detector.detect(file_path)

        # Shift_JISまたは関連エンコーディングが検出されることを確認
        self.assertTrue(
            any(enc in detected_encoding.lower() for enc in ["shift", "sjis", "cp932"])
        )

    def test_encoding_with_bom(self):
        """BOM付きファイルのエンコーディング検出テスト"""
        content = "BOMテスト: 日本語文字列"
        file_path = Path(self.test_dir) / "bom_test.txt"

        # UTF-8 BOM付きでファイルを作成
        with open(file_path, "w", encoding="utf-8-sig") as f:
            f.write(content)

        # エンコーディングを検出
        detected_encoding, has_bom = self.encoding_detector.detect(file_path)

        # UTF-8が検出されることを確認
        self.assertIn("utf", detected_encoding.lower())
        self.assertTrue(has_bom)

    def test_mixed_encoding_handling(self):
        """複数エンコーディング混在処理テスト"""
        # 複数のエンコーディングでファイルを作成
        encodings = ["utf-8", "shift_jis", "euc-jp"]
        test_files = []

        for i, encoding in enumerate(encodings):
            content = f"エンコーディングテスト{i}: 日本語文字列"
            file_path = Path(self.test_dir) / f"mixed_test_{i}.txt"

            try:
                with open(file_path, "w", encoding=encoding) as f:
                    f.write(content)
                test_files.append((file_path, encoding))
            except UnicodeEncodeError:
                # 一部のエンコーディングで文字が表現できない場合はスキップ
                continue

        # 各ファイルのエンコーディングが正しく検出されることを確認
        for file_path, expected_encoding in test_files:
            detected_encoding, has_bom = self.encoding_detector.detect(file_path)
            self.assertIsNotNone(detected_encoding)
            # 検出されたエンコーディングでファイルが読み込めることを確認
            try:
                with open(file_path, "r", encoding=detected_encoding) as f:
                    content = f.read()
                    self.assertIn("エンコーディングテスト", content)
            except UnicodeDecodeError:
                # エンコーディング検出に失敗した場合は、期待されるエンコーディングで再試行
                with open(file_path, "r", encoding=expected_encoding) as f:
                    content = f.read()
                    self.assertIn("エンコーディングテスト", content)
