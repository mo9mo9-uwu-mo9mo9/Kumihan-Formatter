"""
pytest configuration and fixtures for Kumihan-Formatter

TDD体制支援のための共通フィクスチャとヘルパー関数
"""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """一時ディレクトリフィクスチャ"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_text():
    """サンプルテキストフィクスチャ"""
    return """# テストドキュメント

これはテスト用のサンプルドキュメントです。

;;;highlight;;; 重要な情報 ;;;

((脚注の例))

｜日本語《にほんご》のルビ

## セクション

- リスト項目1
- リスト項目2
"""


@pytest.fixture
def sample_config():
    """サンプル設定フィクスチャ"""
    return {
        "template": "default",
        "output_format": "html",
        "encoding": "utf-8",
        "include_toc": True,
        "debug": False,
    }


@pytest.fixture
def mock_renderer():
    """モックレンダラーフィクスチャ"""
    renderer = Mock()
    renderer.render.return_value = "<html>test</html>"
    renderer.render_nodes.return_value = "<div>test nodes</div>"
    return renderer


@pytest.fixture
def mock_parser():
    """モックパーサーフィクスチャ"""
    parser = Mock()
    parser.parse.return_value = [Mock()]
    return parser


@pytest.fixture
def sample_file(temp_dir, sample_text):
    """サンプルファイルフィクスチャ"""
    test_file = temp_dir / "test.txt"
    test_file.write_text(sample_text, encoding="utf-8")
    return test_file


@pytest.fixture
def mock_file_operations():
    """モックファイル操作フィクスチャ"""
    mock_ops = Mock()
    mock_ops.read_file.return_value = "test content"
    mock_ops.write_file.return_value = True
    mock_ops.exists.return_value = True
    return mock_ops


@pytest.fixture(autouse=True)
def reset_environment():
    """環境をリセットするフィクスチャ（全テストで自動実行）"""
    # テスト前の処理
    import gc

    gc.collect()

    yield

    # テスト後の処理
    gc.collect()


class TDDHelper:
    """TDD開発支援ヘルパークラス"""

    @staticmethod
    def assert_red_phase(test_func, expected_error=None):
        """Red Phase - テストが失敗することを確認"""
        with pytest.raises((AssertionError, Exception)):
            test_func()

    @staticmethod
    def assert_green_phase(test_func):
        """Green Phase - テストが成功することを確認"""
        try:
            test_func()
        except Exception as e:
            pytest.fail(f"Green phase failed: {e}")

    @staticmethod
    def create_minimal_implementation():
        """最小実装のテンプレート"""
        return Mock()

    @staticmethod
    def verify_refactor_safety(before_func, after_func, test_input):
        """リファクタリング安全性の確認"""
        before_result = before_func(test_input)
        after_result = after_func(test_input)
        assert before_result == after_result, "Refactoring changed behavior"


@pytest.fixture
def tdd_helper():
    """TDDヘルパーフィクスチャ"""
    return TDDHelper()


# カスタムマーカーの定義
def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line(
        "markers", "tdd_red: Red phase tests (should fail initially)"
    )
    config.addinivalue_line(
        "markers", "tdd_green: Green phase tests (should pass after implementation)"
    )
    config.addinivalue_line(
        "markers", "tdd_refactor: Refactor phase tests (verify behavior preservation)"
    )


# テスト実行時の設定
def pytest_collection_modifyitems(config, items):
    """テスト収集後の処理"""
    # 遅いテストにマーカーを自動追加
    for item in items:
        if "performance" in item.nodeid or "slow" in item.name:
            item.add_marker(pytest.mark.slow)

        # ファイルI/Oテストにマーカーを追加
        if "file" in item.name.lower() or "io" in item.name.lower():
            item.add_marker(pytest.mark.file_io)


# セッション設定
def pytest_sessionstart(session):
    """テストセッション開始時の処理"""
    print("\n🧪 TDD Test Session Started")
    print("Follow the Red-Green-Refactor cycle!")


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時の処理"""
    if exitstatus == 0:
        print("\n✅ All tests passed! Ready for next TDD cycle.")
    else:
        print(f"\n❌ Some tests failed (exit status: {exitstatus})")
        print("Review failures and continue TDD cycle.")


# パフォーマンス測定フィクスチャ
@pytest.fixture
def performance_monitor():
    """パフォーマンス測定フィクスチャ"""
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_faster_than(self, max_seconds):
            assert self.duration is not None, "Monitor not started/stopped"
            assert (
                self.duration < max_seconds
            ), f"Too slow: {self.duration}s > {max_seconds}s"

    return PerformanceMonitor()


# デバッグヘルパー
@pytest.fixture
def debug_helper():
    """デバッグ支援フィクスチャ"""

    class DebugHelper:
        def __init__(self):
            self.debug_data = {}

        def capture(self, key, value):
            """デバッグデータをキャプチャ"""
            self.debug_data[key] = value

        def print_captured(self):
            """キャプチャしたデータを出力"""
            for key, value in self.debug_data.items():
                print(f"DEBUG {key}: {value}")

        def assert_captured(self, key, expected_value):
            """キャプチャしたデータをアサート"""
            assert key in self.debug_data, f"No data captured for {key}"
            assert self.debug_data[key] == expected_value

    return DebugHelper()


# pytest.skip最適化ヘルパー関数
def _has_module(module_name: str) -> bool:
    """モジュールが利用可能かチェック（CI/CD最適化用）"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _has_method(obj, method_name: str) -> bool:
    """オブジェクトがメソッドを持つかチェック（CI/CD最適化用）"""
    return hasattr(obj, method_name) and callable(getattr(obj, method_name))


def _has_dependency(module_name: str, class_name: str = None) -> bool:
    """依存関係が利用可能かチェック（CI/CD最適化用）"""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            return hasattr(module, class_name)
        return True
    except ImportError:
        return False


def _has_file_operations() -> bool:
    """FileOperationsモジュールが利用可能かチェック"""
    return _has_module("kumihan_formatter.core.file_operations")


def _has_gui_modules() -> bool:
    """GUIモジュールが利用可能かチェック（Tkinter依存）"""
    try:
        import tkinter

        return _has_module("kumihan_formatter.gui_models")
    except ImportError:
        return False


# グローバルに利用可能にするため pytest namespace に追加
import pytest

pytest._has_module = _has_module
pytest._has_method = _has_method
pytest._has_dependency = _has_dependency
pytest._has_file_operations = _has_file_operations
pytest._has_gui_modules = _has_gui_modules
