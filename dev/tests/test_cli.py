"""CLIのテスト"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import main, convert_file


def test_convert_file():
    """convert_file関数のテスト"""
    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("これはテストです。\n\n;;;太字\n太字のテキストです。\n;;;")
        temp_input = Path(f.name)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = convert_file(str(temp_input), temp_dir, show_stats=False)
            
            assert output_file.exists()
            assert output_file.suffix == '.html'
            
            # HTMLの内容をチェック
            content = output_file.read_text(encoding='utf-8')
            assert '<p>これはテストです。</p>' in content
            assert '<strong>太字のテキストです。</strong>' in content
    finally:
        temp_input.unlink()


def test_cli_basic():
    """基本的なCLI機能のテスト"""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("# テスト見出し\n\nテスト内容です。")
        temp_input = f.name
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(main, [
                temp_input,
                '-o', temp_dir,
                '--no-preview'
            ])
            
            assert result.exit_code == 0
            assert "完了" in result.output
    finally:
        Path(temp_input).unlink()


def test_cli_file_not_found():
    """存在しないファイルのテスト"""
    runner = CliRunner()
    
    result = runner.invoke(main, [
        'non_existent_file.txt',
        '--no-preview'
    ])
    
    # clickは存在しないファイルの場合exit_code 2を返す
    assert result.exit_code == 2
    assert "does not exist" in result.output or "not exist" in result.output


@patch('webbrowser.open')
def test_cli_preview(mock_browser):
    """ブラウザプレビューのテスト"""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("プレビューテスト")
        temp_input = f.name
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(main, [
                temp_input,
                '-o', temp_dir
            ])
            
            assert result.exit_code == 0
            mock_browser.assert_called_once()
    finally:
        Path(temp_input).unlink()


def test_cli_no_preview():
    """プレビューなしのテスト"""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("ノープレビューテスト")
        temp_input = f.name
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('webbrowser.open') as mock_browser:
                result = runner.invoke(main, [
                    temp_input,
                    '-o', temp_dir,
                    '--no-preview'
                ])
                
                assert result.exit_code == 0
                mock_browser.assert_not_called()
    finally:
        Path(temp_input).unlink()