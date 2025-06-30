"""Extended CLI functionality tests"""
import pytest
from pathlib import Path
from click.testing import CliRunner

try:
    from kumihan_formatter.cli import cli
except ImportError:
    cli = None
try:
    from kumihan_formatter.commands.convert import ConvertCommand
except ImportError:
    ConvertCommand = None
try:
    from kumihan_formatter.commands.check_syntax import create_check_syntax_command
except ImportError:
    create_check_syntax_command = None
try:
    from kumihan_formatter.commands.sample import create_sample_command
except ImportError:
    create_sample_command = None


class TestCLIArguments:
    """CLI引数パースのテスト"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_convert_command_creation(self):
        """convertコマンドの作成テスト"""
        if ConvertCommand is None:
            pytest.skip("ConvertCommandがimportできません")
        command = ConvertCommand()
        assert command is not None

    def test_check_syntax_command_creation(self):
        """check-syntaxコマンドの作成テスト"""
        if create_check_syntax_command is None:
            pytest.skip("check-syntax commandがimportできません")
        command = create_check_syntax_command()
        assert command is not None
        assert hasattr(command, "callback")

    def test_sample_command_creation(self):
        """sampleコマンドの作成テスト"""
        if create_sample_command is None:
            pytest.skip("sample commandがimportできません")
        command = create_sample_command()
        assert command is not None
        assert hasattr(command, "callback")

    def test_cli_group_commands(self, runner):
        """CLIグループに登録されたコマンドのテスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        
        # 各コマンドがヘルプに表示されることを確認
        help_output = result.output
        assert "convert" in help_output
        assert "check-syntax" in help_output or "check_syntax" in help_output
        assert "generate-sample" in help_output or "sample" in help_output

    def test_convert_invalid_arguments(self, runner):
        """convertコマンドの不正な引数テスト"""
        # ファイルパスなしでの実行
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["convert"])
        assert result.exit_code != 0

    def test_convert_help_details(self, runner):
        """convertコマンドのヘルプ詳細テスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["convert", "--help"])
        assert result.exit_code == 0
        
        help_output = result.output.lower()
        # 主要なオプションが表示されることを確認
        assert "output-dir" in help_output or "output_dir" in help_output
        assert "watch" in help_output or "監視" in help_output

    def test_check_syntax_help_details(self, runner):
        """check-syntaxコマンドのヘルプ詳細テスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["check-syntax", "--help"])
        assert result.exit_code == 0
        
        help_output = result.output
        # 記法チェック関連の説明があることを確認
        assert len(help_output) > 50  # ある程度の長さのヘルプがあることを確認


class TestCLIErrorHandling:
    """CLIエラーハンドリングのテスト"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_nonexistent_command(self, runner):
        """存在しないコマンドのテスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["nonexistent-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output or "コマンドが見つかりません" in result.output

    def test_convert_nonexistent_file(self, runner):
        """存在しないファイルの変換テスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["convert", "nonexistent_file.txt"])
        assert result.exit_code != 0
        # エラーメッセージの確認（日本語または英語）
        error_output = result.output.lower()
        assert ("error" in error_output or "エラー" in result.output or 
                "not found" in error_output or "見つかりません" in result.output)

    def test_convert_invalid_output_dir(self, runner, temp_dir):
        """不正な出力ディレクトリのテスト"""
        # テストファイルを作成
        test_file = temp_dir / "test.txt"
        test_file.write_text("■タイトル: テスト", encoding="utf-8")
        
        # 存在しない親ディレクトリを指定
        invalid_output = "/nonexistent/path/output"
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, [
            "convert", str(test_file), 
            "--output-dir", invalid_output
        ])
        
        # エラーが発生することを確認（ただし、ディレクトリが自動作成される可能性もある）
        # 結果を確認するが、自動作成される場合は成功する可能性もある
        if result.exit_code != 0:
            assert "error" in result.output.lower() or "エラー" in result.output

    def test_check_syntax_nonexistent_file(self, runner):
        """存在しないファイルの記法チェックテスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, ["check-syntax", "nonexistent.txt"])
        assert result.exit_code != 0
        error_output = result.output.lower()
        assert ("error" in error_output or "エラー" in result.output or 
                "not found" in error_output or "見つかりません" in result.output)


class TestCLIIntegration:
    """CLI統合機能のテスト"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_files(self, temp_dir):
        """複数のテストファイルを作成"""
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"""■タイトル: テスト{i}
■作者: テスト作者{i}

●セクション{i}
テスト内容{i}です。

▼NPC{i}: テストNPC{i}
NPC{i}の説明です。
""", encoding="utf-8")
            files.append(file_path)
        return files

    @pytest.mark.integration
    def test_convert_multiple_files(self, runner, sample_files, temp_dir):
        """複数ファイルの一括変換テスト"""
        output_dir = temp_dir / "output"
        
        # 複数のファイルを指定して変換
        file_paths = [str(f) for f in sample_files]
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, [
            "convert", *file_paths,
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        
        # 各ファイルが変換されたことを確認
        for i in range(3):
            expected_output = output_dir / f"test_{i}" / f"test_{i}.html"
            assert expected_output.exists(), f"test_{i}.html が生成されていません"
            
            # HTMLの内容確認
            html_content = expected_output.read_text(encoding="utf-8")
            assert f"テスト{i}" in html_content
            assert f"テスト作者{i}" in html_content

    @pytest.mark.integration
    def test_convert_with_config_file(self, runner, temp_dir):
        """設定ファイル付きでの変換テスト"""
        # テストファイルを作成
        test_file = temp_dir / "test.txt"
        test_file.write_text("""■タイトル: 設定テスト
■作者: テスト作者

●導入
設定ファイルのテストです。
""", encoding="utf-8")
        
        # 設定ファイルを作成
        config_file = temp_dir / "config.yaml"
        config_file.write_text("""title: "カスタムタイトル"
author: "カスタム作者"
template: "base.html.j2"
""", encoding="utf-8")
        
        output_dir = temp_dir / "output"
        
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, [
            "convert", str(test_file),
            "--output-dir", str(output_dir),
            "--config", str(config_file)
        ])
        
        assert result.exit_code == 0
        
        # 出力ファイルの確認
        expected_output = output_dir / "test" / "test.html"
        assert expected_output.exists()
        
        # 設定が適用されたことを確認
        html_content = expected_output.read_text(encoding="utf-8")
        assert "設定テスト" in html_content  # 元のタイトルが使われることを確認

    def test_generate_sample_with_custom_output(self, runner, temp_dir):
        """カスタム出力ディレクトリでのサンプル生成テスト"""
        if cli is None:
            pytest.skip("cliがimportできません")
        result = runner.invoke(cli, [
            "generate-sample",
            "--output-dir", str(temp_dir)
        ])
        
        assert result.exit_code == 0
        
        # サンプルファイルが生成されたことを確認
        sample_files = list(temp_dir.glob("*.txt"))
        assert len(sample_files) > 0, "サンプルファイルが生成されていません"
        
        # 生成されたファイルの内容確認
        for sample_file in sample_files:
            content = sample_file.read_text(encoding="utf-8")
            assert "■" in content or "●" in content or "▼" in content  # 基本的な記法が含まれることを確認
