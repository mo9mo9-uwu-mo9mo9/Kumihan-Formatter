"""
pytest configuration and shared fixtures for Kumihan-Formatter tests
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# プロジェクトルートをPYTHONPATHに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを作成するfixture"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_text() -> str:
    """テスト用のサンプルテキスト"""
    return """■タイトル: テストシナリオ
■作者: テスト作者

●導入
これはテスト用のシナリオです。

▼NPC1: テストNPC
テスト用のNPC説明文です。

◆部屋1: テスト部屋
テスト用の部屋説明文です。
"""


@pytest.fixture
def sample_config() -> dict:
    """テスト用の設定"""
    return {
        "title": "テスト設定",
        "author": "テスト作者",
        "output_dir": "test_output",
        "template": "base.html.j2",
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """テスト後のクリーンアップ"""
    yield
    # テスト実行後にtest_outputディレクトリを削除
    test_output = PROJECT_ROOT / "test_output"
    if test_output.exists():
        import shutil

        shutil.rmtree(test_output)


@pytest.fixture
def mock_cli_runner():
    """CLIテスト用のrunner"""
    from click.testing import CliRunner

    return CliRunner()


# パフォーマンステスト用のデコレータ
def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
