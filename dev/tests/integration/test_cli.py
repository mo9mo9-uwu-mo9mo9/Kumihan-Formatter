"""CLIのテスト"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import cli
from kumihan_formatter.commands.convert import ConvertCommand


def test_convert_file():
    """convert_file関数のテスト"""
    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("これはテストです。\n\n;;;太字\n太字のテキストです。\n;;;")
        temp_input = Path(f.name)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 新しいConvertCommandクラスを使用
            convert_command = ConvertCommand()
            output_file = convert_command._convert_file(temp_input, temp_dir, show_stats=False)
            
            assert output_file.exists()
            assert output_file.suffix == '.html'
            
            # HTMLの内容をチェック
            content = output_file.read_text(encoding='utf-8')
            assert '<p>これはテストです。</p>' in content
            # 正しい太字ブロックの形式（strongタグが内容を直接包含）
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
            result = runner.invoke(cli, [
                'convert',
                temp_input,
                '-o', temp_dir,
                '--no-preview'
            ], input='n\n')  # ソーストグルプロンプトに対して 'n' を入力
            
            assert result.exit_code == 0
            assert "完了" in result.output
    finally:
        Path(temp_input).unlink()


def test_cli_file_not_found():
    """存在しないファイルのテスト"""
    runner = CliRunner()
    
    result = runner.invoke(cli, [
        'convert',
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
            result = runner.invoke(cli, [
                'convert',
                temp_input,
                '-o', temp_dir
            ], input='n\n')  # ソーストグルプロンプトに対して 'n' を入力
            
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
                result = runner.invoke(cli, [
                    'convert',
                    temp_input,
                    '-o', temp_dir,
                    '--no-preview'
                ], input='n\n')  # ソーストグルプロンプトに対して 'n' を入力
                
                assert result.exit_code == 0
                mock_browser.assert_not_called()
    finally:
        Path(temp_input).unlink()


def test_zip_dist_command():
    """zip-dist コマンドのテスト"""
    runner = CliRunner()
    
    # 一時的なソースディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_source_dir:
        with tempfile.TemporaryDirectory() as temp_output_dir:
            # テスト用ファイルを作成
            source_path = Path(temp_source_dir)
            test_file = source_path / "test.txt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("テスト用ファイルです。")
            
            # zip-dist コマンドを実行
            result = runner.invoke(cli, [
                'zip-dist',
                str(source_path),
                '-o', temp_output_dir,
                '--no-zip',
                '--no-preview'
            ])
            
            assert result.exit_code == 0
            assert "配布パッケージの作成が完了しました" in result.output


def test_generate_sample_command():
    """generate-sample コマンドのテスト"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(cli, [
            'generate-sample',
            '--output', temp_dir
        ], input='n\n')  # ソーストグルプロンプトに対して 'n' を入力
        
        assert result.exit_code == 0
        assert "サンプル生成完了" in result.output
        
        # 生成されたファイルの確認
        output_path = Path(temp_dir)
        assert (output_path / "showcase.txt").exists()
        assert (output_path / "showcase.html").exists()
        assert (output_path / "images").exists()