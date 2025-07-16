"""Test configuration for Kumihan-Formatter

テスト実行時の共通設定とフィクスチャの定義
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_dir():
    """一時ディレクトリのフィクスチャ"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_text_file(temp_dir):
    """サンプルテキストファイルのフィクスチャ"""
    content = """;;;bold;;; テスト内容 ;;;
;;;italic;;; イタリック ;;;
通常のテキスト
;;;underline;;; 下線テキスト ;;;"""

    file_path = temp_dir / "sample.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def mock_logger():
    """モックロガーのフィクスチャ"""
    with patch("kumihan_formatter.core.utilities.logger.get_logger") as mock:
        mock_logger_instance = mock.return_value
        mock_logger_instance.info = lambda *args, **kwargs: None
        mock_logger_instance.error = lambda *args, **kwargs: None
        mock_logger_instance.warning = lambda *args, **kwargs: None
        mock_logger_instance.debug = lambda *args, **kwargs: None
        yield mock_logger_instance


@pytest.fixture
def test_config():
    """テスト用設定のフィクスチャ"""
    return {
        "log_level": "DEBUG",
        "output_format": "html",
        "encoding": "utf-8",
        "enable_performance_logging": False,
        "enable_dev_logging": True,
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """テスト環境の自動セットアップ"""
    # テスト実行時は開発ログを無効化
    os.environ["KUMIHAN_DEV_LOG"] = "false"
    os.environ["KUMIHAN_LOG_LEVEL"] = "WARNING"

    yield

    # テスト後のクリーンアップ
    if "KUMIHAN_DEV_LOG" in os.environ:
        del os.environ["KUMIHAN_DEV_LOG"]
    if "KUMIHAN_LOG_LEVEL" in os.environ:
        del os.environ["KUMIHAN_LOG_LEVEL"]


@pytest.fixture
def error_handler():
    """エラーハンドラーのフィクスチャ"""
    from kumihan_formatter.core.error_handling.unified_handler import (
        UnifiedErrorHandler,
    )

    return UnifiedErrorHandler(enable_logging=False)


@pytest.fixture
def performance_logger():
    """パフォーマンスロガーのフィクスチャ"""
    from kumihan_formatter.core.utilities.performance_logger import (
        get_log_performance_optimizer,
    )

    return get_log_performance_optimizer("test_performance")


# テストマーカーの定義
def pytest_configure(config):
    """テストマーカーの設定"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# テスト実行時の出力制御
def pytest_runtest_setup(item):
    """テスト実行前の設定"""
    # テスト実行時は警告を抑制
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
