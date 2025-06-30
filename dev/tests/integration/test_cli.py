"""
Integration tests for CLI functionality
"""
import pytest
from pathlib import Path
from click.testing import CliRunner

from kumihan_formatter.cli import main


class TestCLI:
    """CLIコマンドの統合テスト"""

    @pytest.fixture
    def runner(self):
        """CLIテスト用のrunner"""
        return CliRunner()

    @pytest.fixture
    def sample_file(self, temp_dir):
        """テスト用のサンプルファイル"""
        file_path = temp_dir / "test.txt"
        file_path.write_text("""■タイトル: テストシナリオ
■作者: テスト作者

●導入
これはテストシナリオです。
""", encoding="utf-8")
        return file_path

    def test_cli_help(self, runner):
        """ヘルプコマンドのテスト"""
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "Kumihan-Formatter" in result.output
        assert "Commands:" in result.output

    def test_convert_command_help(self, runner):
        """convertコマンドのヘルプテスト"""
        result = runner.invoke(main, ["convert", "--help"])
        
        assert result.exit_code == 0
        assert "convert" in result.output

    @pytest.mark.integration
    def test_convert_basic_file(self, runner, sample_file, temp_dir):
        """基本的なファイル変換のテスト"""
        output_dir = temp_dir / "output"
        
        result = runner.invoke(main, [
            "convert",
            str(sample_file),
            "--output-dir", str(output_dir)
        ])
        
        # 実行結果の確認
        assert result.exit_code == 0
        
        # 出力ファイルの確認
        expected_output = output_dir / "test" / "test.html"
        assert expected_output.exists()
        
        # HTMLの内容確認
        html_content = expected_output.read_text(encoding="utf-8")
        assert "テストシナリオ" in html_content
        assert "テスト作者" in html_content

    def test_convert_nonexistent_file(self, runner):
        """存在しないファイルの変換テスト"""
        result = runner.invoke(main, ["convert", "nonexistent.txt"])
        
        assert result.exit_code != 0
        assert "Error" in result.output or "エラー" in result.output

    def test_check_syntax_command_help(self, runner):
        """check-syntaxコマンドのヘルプテスト"""
        result = runner.invoke(main, ["check-syntax", "--help"])
        
        assert result.exit_code == 0
        assert "check-syntax" in result.output

    @pytest.mark.integration
    def test_check_syntax_valid_file(self, runner, sample_file):
        """正しい記法のファイルのチェックテスト"""
        result = runner.invoke(main, ["check-syntax", str(sample_file)])
        
        # 記法チェックの結果（エラーがなければ成功）
        assert result.exit_code == 0 or "エラー: 0" in result.output

    def test_sample_command(self, runner, temp_dir):
        """sampleコマンドのテスト"""
        result = runner.invoke(main, ["sample", "--output-dir", str(temp_dir)])
        
        assert result.exit_code == 0
        
        # サンプルファイルが生成されたか確認
        sample_files = list(temp_dir.glob("*.txt"))
        assert len(sample_files) > 0

    def test_multiple_file_conversion(self, runner, temp_dir):
        """複数ファイルの変換テスト"""
        # 複数のテストファイルを作成
        file1 = temp_dir / "test1.txt"
        file2 = temp_dir / "test2.txt"
        
        for i, file_path in enumerate([file1, file2], 1):
            file_path.write_text(f"""■タイトル: テストシナリオ{i}
■作者: テスト作者{i}

●導入
これはテストシナリオ{i}です。
""", encoding="utf-8")
        
        output_dir = temp_dir / "output"
        
        # 複数ファイルを変換
        result = runner.invoke(main, [
            "convert",
            str(file1),
            str(file2),
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        
        # 両方のファイルが変換されたか確認
        assert (output_dir / "test1" / "test1.html").exists()
        assert (output_dir / "test2" / "test2.html").exists()

    @pytest.mark.slow
    def test_watch_mode(self, runner, sample_file, temp_dir):
        """ウォッチモードのテスト（即座に終了）"""
        import threading
        import time
        
        output_dir = temp_dir / "output"
        
        # ウォッチモードを別スレッドで実行
        def run_watch():
            runner.invoke(main, [
                "convert",
                str(sample_file),
                "--output-dir", str(output_dir),
                "--watch"
            ])
        
        thread = threading.Thread(target=run_watch)
        thread.daemon = True
        thread.start()
        
        # 少し待ってからスレッドを終了
        time.sleep(0.5)
        
        # 出力ファイルが生成されたか確認
        expected_output = output_dir / "test" / "test.html"
        assert expected_output.exists()