"""基本的な統合テスト"""

import subprocess
import sys


def test_cli_help():
    """CLIヘルプの基本テスト"""
    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout or "使い方:" in result.stdout


def test_cli_sample_command():
    """CLIサンプルコマンドの基本テスト"""
    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "generate-sample", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout or "使い方:" in result.stdout
