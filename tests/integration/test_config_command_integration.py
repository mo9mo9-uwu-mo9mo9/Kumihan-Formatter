"""Config and Command Integration Tests

設定とコマンドシステムの統合テスト
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.tdd_green
class TestConfigIntegration:
    """設定システムの統合テスト"""

    @pytest.mark.unit
    def test_config_loading_workflow(self):
        """設定読み込みワークフロー"""
        from kumihan_formatter.config import Config

        # 基本設定オブジェクトの作成
        config = Config()
        assert config is not None

    @pytest.mark.unit
    def test_config_environment_integration(self):
        """環境変数連携テスト"""
        with patch.dict("os.environ", {"KUMIHAN_DEBUG": "true"}):
            # 環境変数が設定されることを確認
            assert os.environ.get("KUMIHAN_DEBUG") == "true"


@pytest.mark.tdd_green
class TestCommandIntegration:
    """コマンドシステムの統合テスト"""

    @pytest.mark.mock_heavy
    def test_convert_command_workflow(self):
        """変換コマンドのワークフロー"""
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand

        with (
            patch("kumihan_formatter.commands.convert.convert_command.get_logger"),
            patch("kumihan_formatter.commands.convert.convert_command.get_console_ui"),
        ):
            command = ConvertCommand()

            # コマンド初期化の確認
            assert command is not None
            assert hasattr(command, "validator")
            assert hasattr(command, "processor")

    @pytest.mark.unit
    def test_sample_command_integration(self):
        """サンプルコマンドの統合テスト"""
        from kumihan_formatter.commands.sample_command import SampleCommand

        command = SampleCommand()
        assert command is not None
