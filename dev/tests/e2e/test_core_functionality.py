"""
コア機能の堅牢なE2Eテスト

環境依存性を最小限に抑えた基本機能テスト
"""

import pytest
import subprocess
import sys
from pathlib import Path
import tempfile
import os


class TestCoreFunctionality:
    """コア機能の環境非依存テスト"""
    
    def test_basic_cli_conversion(self):
        """最小限のCLI変換テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # シンプルなテストファイルを作成
            input_file = temp_path / "test_input.txt"
            input_content = """;;;見出し1
テストファイル
;;;

これは基本的なテストです。

;;;太字
重要な内容
;;;
"""
            input_file.write_text(input_content, encoding='utf-8')
            
            # 出力ディレクトリ
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            # CLI実行
            cmd = [
                sys.executable, "-m", "kumihan_formatter.cli",
                str(input_file),
                "-o", str(output_dir),
                "--no-preview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 基本的な成功確認
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            
            # 出力ファイルの存在確認
            expected_output = output_dir / "test_input.html"
            assert expected_output.exists(), "HTML output file not created"
            
            # HTMLの基本構造確認
            html_content = expected_output.read_text(encoding='utf-8')
            
            # 必須要素の確認（環境非依存）
            assert "<!DOCTYPE html>" in html_content, "Missing DOCTYPE"
            assert "<html" in html_content, "Missing html element"
            assert "</html>" in html_content, "Missing closing html tag"
            assert "<head>" in html_content, "Missing head element"
            assert "<body>" in html_content, "Missing body element"
            
            # コンテンツの基本確認
            assert "テストファイル" in html_content, "Japanese content not preserved"
            assert "重要な内容" in html_content, "Content not converted"
    
    def test_empty_file_handling(self):
        """空ファイルの適切な処理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 空ファイルを作成
            input_file = temp_path / "empty_test.txt"
            input_file.write_text("", encoding='utf-8')
            
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            # CLI実行
            cmd = [
                sys.executable, "-m", "kumihan_formatter.cli",
                str(input_file),
                "-o", str(output_dir),
                "--no-preview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 空ファイルでも正常に処理されることを確認
            assert result.returncode == 0, f"Empty file handling failed: {result.stderr}"
            
            # HTMLファイルが生成されることを確認
            expected_output = output_dir / "empty_test.html"
            assert expected_output.exists(), "HTML not generated for empty file"
            
            html_content = expected_output.read_text(encoding='utf-8')
            assert "<!DOCTYPE html>" in html_content, "Invalid HTML for empty file"
    
    def test_japanese_characters_preservation(self):
        """日本語文字の正しい保持"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 様々な日本語文字を含むファイル
            input_file = temp_path / "japanese_test.txt"
            input_content = """;;;見出し1
日本語文字テスト
;;;

ひらがな: あいうえお
カタカナ: アイウエオ
漢字: 日本語変換
記号: ①②③
"""
            input_file.write_text(input_content, encoding='utf-8')
            
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            cmd = [
                sys.executable, "-m", "kumihan_formatter.cli",
                str(input_file),
                "-o", str(output_dir),
                "--no-preview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            assert result.returncode == 0, f"Japanese text processing failed: {result.stderr}"
            
            expected_output = output_dir / "japanese_test.html"
            assert expected_output.exists(), "HTML not generated for Japanese content"
            
            html_content = expected_output.read_text(encoding='utf-8')
            
            # 日本語文字が正しく保持されていることを確認
            assert "あいうえお" in html_content, "Hiragana not preserved"
            assert "アイウエオ" in html_content, "Katakana not preserved"
            assert "日本語変換" in html_content, "Kanji not preserved"
            assert "①②③" in html_content, "Japanese symbols not preserved"
    
    def test_basic_kumihan_syntax(self):
        """基本的なKumihan記法の動作確認"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            input_file = temp_path / "syntax_test.txt"
            input_content = """;;;見出し1
メイン見出し
;;;

通常の段落です。

;;;太字
太字のテスト
;;;

;;;枠線
枠線のテスト
;;;
"""
            input_file.write_text(input_content, encoding='utf-8')
            
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            cmd = [
                sys.executable, "-m", "kumihan_formatter.cli",
                str(input_file),
                "-o", str(output_dir),
                "--no-preview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            assert result.returncode == 0, f"Syntax processing failed: {result.stderr}"
            
            expected_output = output_dir / "syntax_test.html"
            html_content = expected_output.read_text(encoding='utf-8')
            
            # 基本的な変換が行われていることを確認（厳密ではなく存在確認のみ）
            assert "メイン見出し" in html_content, "Heading content missing"
            assert "太字のテスト" in html_content, "Bold content missing"
            assert "枠線のテスト" in html_content, "Box content missing"
            assert "通常の段落です" in html_content, "Paragraph content missing"
    
    def test_file_not_found_error(self):
        """存在しないファイルのエラーハンドリング"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 存在しないファイルを指定
            nonexistent_file = temp_path / "does_not_exist.txt"
            output_dir = temp_path / "output"
            output_dir.mkdir()
            
            cmd = [
                sys.executable, "-m", "kumihan_formatter.cli",
                str(nonexistent_file),
                "-o", str(output_dir),
                "--no-preview"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # エラーで終了することを確認
            assert result.returncode != 0, "Should fail for nonexistent file"
            assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower(), \
                "Should provide clear error message"