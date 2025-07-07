"""基本的な統合テスト"""

import subprocess
import sys


def test_cli_help() -> None:
    """CLIヘルプの基本テスト"""
    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",  # Windows環境対応のためエンコーディングを明示的に指定
    )
    assert result.returncode == 0
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    output = stdout + stderr
    assert "Usage:" in output or "使い方:" in output


def test_cli_sample_command() -> None:
    """CLIサンプルコマンドの基本テスト"""
    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "generate-sample", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",  # Windows環境対応のためエンコーディングを明示的に指定
    )
    assert result.returncode == 0
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    output = stdout + stderr
    assert "Usage:" in output or "使い方:" in output
