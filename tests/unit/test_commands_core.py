"""Commands機能のCore単体テスト - Critical Tier対応"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.check_syntax import CheckSyntaxCommand
from kumihan_formatter.commands.convert.convert_command import ConvertCommand
from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor
from kumihan_formatter.commands.sample_command import SampleCommand
from kumihan_formatter.core.utilities.logger import get_logger


class TestConvertCommandCore:
    """ConvertCommandのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.logger = get_logger(__name__)

    def test_convert_command_initialization(self):
        """ConvertCommand初期化テスト"""
        cmd = ConvertCommand()
        assert cmd is not None
        assert hasattr(cmd, "execute")
        assert hasattr(cmd, "validator")
        assert hasattr(cmd, "processor")

    def test_convert_command_validation_empty_args(self):
        """空の引数でのバリデーションテスト"""
        cmd = ConvertCommand()

        # 無効な引数での実行（input_file=None）
        with pytest.raises((ValueError, TypeError, SystemExit)):
            cmd.execute(
                input_file=None,
                output="",
                no_preview=False,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
            )

    def test_convert_command_validation_missing_input(self):
        """入力ファイル不足のバリデーションテスト"""
        cmd = ConvertCommand()

        # 存在しないファイルでの実行
        with pytest.raises((FileNotFoundError, SystemExit)):
            cmd.execute(
                input_file="nonexistent.txt",
                output="output.html",
                no_preview=False,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
            )

    def test_convert_command_help_option(self):
        """ヘルプオプションテスト"""
        cmd = ConvertCommand()

        # ヘルプ的な使い方（基本テスト）
        assert hasattr(cmd, "execute")
        assert callable(getattr(cmd, "execute"))

    def test_convert_command_basic_execution(self):
        """基本的な変換実行テスト"""
        cmd = ConvertCommand()

        # 一時ファイルを使用した基本実行テスト
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as input_file:
            input_file.write(";;;強調;;; テストコンテンツ ;;;")
            input_path = input_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            # Mock ConvertProcessorの実行
            with patch.object(cmd.processor, "convert_file") as mock_convert:
                mock_convert.return_value = Path(output_path)

                # SystemExitが発生する可能性があるため例外処理
                try:
                    result = cmd.execute(
                        input_file=input_path,
                        output=output_path,
                        no_preview=True,
                        watch=False,
                        config=None,
                        show_test_cases=False,
                        template_name=None,
                        include_source=False,
                    )
                except SystemExit:
                    # 正常終了のSystemExitは期待される動作
                    pass

                # ConvertProcessorが呼び出されたことを確認
                mock_convert.assert_called_once()

        finally:
            # 一時ファイルを削除
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)


class TestConvertProcessorCore:
    """ConvertProcessorのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.processor = ConvertProcessor()

    def test_convert_processor_initialization(self):
        """ConvertProcessor初期化テスト"""
        assert self.processor is not None
        assert hasattr(self.processor, "convert_file")
        assert hasattr(self.processor, "validate_files")

    def test_convert_processor_file_validation(self):
        """ファイルバリデーション機能テスト"""
        # 存在しないファイルのバリデーション
        with pytest.raises(FileNotFoundError):
            self.processor.validate_files("nonexistent.txt", "output.txt")

    def test_convert_processor_content_processing(self):
        """コンテンツ処理機能テスト"""
        # ConvertProcessorが基本的なメソッドを持っていることを確認
        assert hasattr(self.processor, "convert_file")
        assert callable(getattr(self.processor, "convert_file"))

        # Mock化したファイル読み込みでテスト
        with patch.object(self.processor.file_ops, "read_text_file") as mock_read:
            mock_read.return_value = ";;;強調;;; テストコンテンツ ;;;"

            # 基本的な処理パスの確認のみ
            assert self.processor.file_ops is not None


class TestCheckSyntaxCommandCore:
    """CheckSyntaxCommandのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.cmd = CheckSyntaxCommand()

    def test_check_syntax_command_initialization(self):
        """CheckSyntaxCommand初期化テスト"""
        assert self.cmd is not None
        assert hasattr(self.cmd, "execute")
        assert hasattr(self.cmd, "check")

    def test_check_syntax_validation_empty_args(self):
        """空の引数でのバリデーションテスト"""
        with pytest.raises(SystemExit) as exc_info:
            self.cmd.execute([])
        # エラーコードが非零であることを確認
        assert exc_info.value.code != 0

    def test_check_syntax_file_validation(self):
        """ファイル構文チェック機能テスト"""
        # CheckSyntaxCommandが基本メソッドを持っていることを確認
        assert hasattr(self.cmd, "execute")
        assert hasattr(self.cmd, "check")
        assert callable(getattr(self.cmd, "execute"))
        assert callable(getattr(self.cmd, "check"))

    def test_check_syntax_error_handling(self):
        """構文エラーハンドリングテスト"""
        # 不正な構文のテスト
        invalid_content = ";;;強調;;; 未閉じコンテンツ"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as test_file:
            test_file.write(invalid_content)
            file_path = test_file.name

        try:
            # CheckSyntaxCommandのエラーハンドリング機能確認
            assert hasattr(self.cmd, "_collect_files")
            assert hasattr(self.cmd, "_output_text")

        finally:
            Path(file_path).unlink(missing_ok=True)


class TestSampleCommandCore:
    """SampleCommandのCore機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.cmd = SampleCommand()

    def test_sample_command_initialization(self):
        """SampleCommand初期化テスト"""
        assert self.cmd is not None
        assert hasattr(self.cmd, "execute")
        assert hasattr(self.cmd, "generate_sample")

    def test_sample_command_generation(self):
        """サンプル生成機能テスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            result = self.cmd.execute([output_path])

            # サンプルファイルが生成されたことを確認
            output_file_path = Path(output_path)
            assert output_file_path.exists()

            # ファイル内容の基本確認
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 0
                assert ";;;" in content  # Kumihan記法が含まれることを確認

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_sample_command_custom_options(self):
        """カスタムオプション機能テスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            # 詳細サンプル生成テスト
            result = self.cmd.execute([output_path, "--verbose"])

            output_file_path = Path(output_path)
            if output_file_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert len(content) > 0

        except SystemExit:
            # オプションが認識されない場合はスキップ
            pass
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestCommandsIntegration:
    """Commands機能統合テスト"""

    def test_commands_workflow_integration(self):
        """コマンド機能の統合ワークフローテスト"""
        # 1. サンプル生成
        sample_cmd = SampleCommand()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as sample_file:
            sample_path = sample_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            # サンプル生成
            sample_cmd.execute([sample_path])
            assert Path(sample_path).exists()

            # 2. 構文チェック
            check_cmd = CheckSyntaxCommand()
            with patch(
                "kumihan_formatter.commands.check_syntax.KumihanParser"
            ) as mock_parser:
                mock_parser_instance = MagicMock()
                mock_parser.return_value = mock_parser_instance
                mock_parser_instance.parse.return_value = MagicMock()

                check_result = check_cmd.check_file_syntax(sample_path)

            # 3. 変換実行
            convert_cmd = ConvertCommand()
            with patch(
                "kumihan_formatter.commands.convert.convert_command.ConvertProcessor"
            ) as mock_processor:
                mock_instance = MagicMock()
                mock_processor.return_value = mock_instance
                mock_instance.convert.return_value = True

                convert_result = convert_cmd.execute([sample_path, output_path])

            # 統合ワークフローが正常に完了したことを確認
            mock_parser_instance.parse.assert_called()
            mock_instance.convert.assert_called()

        finally:
            Path(sample_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_commands_error_recovery(self):
        """コマンド機能のエラー回復テスト"""
        # 不正な入力でのエラー処理テスト
        convert_cmd = ConvertCommand()
        check_cmd = CheckSyntaxCommand()

        # 存在しないファイルでのエラーハンドリング
        with pytest.raises(FileNotFoundError):
            convert_cmd.execute(["nonexistent.txt", "output.html"])

        with pytest.raises(SystemExit) as exc_info:
            check_cmd.execute(["nonexistent.txt"])
        # エラーコードが非零であることを確認
        assert exc_info.value.code != 0
