"""基本的な統合テスト"""

import subprocess
import sys


def test_cli_help():
    """CLIヘルプの基本テスト"""
    # Windows環境での詳細デバッグ情報を追加
    import platform

    print(f"DEBUG: Platform: {platform.system()}")
    print(f"DEBUG: Python executable: {sys.executable}")

    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",  # エンコーディングを明示的に指定
    )

    print(f"DEBUG: Return code: {result.returncode}")
    print(f"DEBUG: stdout length: {len(result.stdout or '')}")
    print(f"DEBUG: stderr length: {len(result.stderr or '')}")
    print(f"DEBUG: stdout: '{result.stdout}'")
    print(f"DEBUG: stderr: '{result.stderr}'")

    assert (
        result.returncode == 0
    ), f"CLI failed with code {result.returncode}, stderr: {result.stderr}"
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    output = stdout + stderr
    assert (
        "Usage:" in output or "使い方:" in output
    ), f"Help text not found in output: '{output}'"


def test_cli_sample_command():
    """CLIサンプルコマンドの基本テスト"""
    # Windows環境での詳細デバッグ情報を追加
    import platform

    print(f"DEBUG: Platform: {platform.system()}")
    print(f"DEBUG: Python executable: {sys.executable}")

    result = subprocess.run(
        [sys.executable, "-m", "kumihan_formatter", "generate-sample", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",  # エンコーディングを明示的に指定
    )

    print(f"DEBUG: Return code: {result.returncode}")
    print(f"DEBUG: stdout length: {len(result.stdout or '')}")
    print(f"DEBUG: stderr length: {len(result.stderr or '')}")
    print(f"DEBUG: stdout: '{result.stdout}'")
    print(f"DEBUG: stderr: '{result.stderr}'")

    assert (
        result.returncode == 0
    ), f"CLI failed with code {result.returncode}, stderr: {result.stderr}"
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    output = stdout + stderr
    assert (
        "Usage:" in output or "使い方:" in output
    ), f"Help text not found in output: '{output}'"
