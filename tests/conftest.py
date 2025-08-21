"""
Test configuration and fixtures for Kumihan-Formatter test suite.
"""

import multiprocessing
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import psutil
import pytest

from kumihan_formatter.core.utilities.logger import get_logger

# PYTHONPATH設定 - プロジェクトルートをsys.pathに追加
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# trio利用可能性チェック
try:
    import trio

    trio_available = True
except ImportError:
    trio_available = False


def _get_optimal_worker_count() -> int:
    """
    環境に応じて最適なワーカー数を決定
    Issue #1049: pytest-xdist並列実行設定最適化
    """
    # CI環境の判定
    is_ci = os.getenv("GITHUB_ACTIONS", "").lower() == "true"
    is_ci_generic = os.getenv("CI", "").lower() == "true"

    # CPU数とメモリ情報の取得
    cpu_count = multiprocessing.cpu_count()

    try:
        # メモリ使用量の取得（GB単位）
        memory_gb = psutil.virtual_memory().total / (1024**3)
    except:
        # psutilが利用できない場合のフォールバック
        memory_gb = 8.0

    # テスト規模の推定（大雑把な分類）
    test_markers = os.getenv("PYTEST_CURRENT_TEST", "")

    if is_ci or is_ci_generic:
        # GitHub Actions環境（2コア想定）での最適化
        if "performance" in test_markers or "benchmark" in test_markers:
            return 1  # パフォーマンステストは単一ワーカー
        elif "system" in test_markers:
            return 1  # システムテストは慎重に
        elif "end_to_end" in test_markers:
            return min(2, cpu_count)  # E2Eテストは最大2
        else:
            return 2  # CI環境では固定2並列
    else:
        # ローカル環境での最適化
        if "performance" in test_markers or "benchmark" in test_markers:
            return 1  # ベンチマークは単一実行
        elif "system" in test_markers:
            return 1  # システムテストは単一実行
        elif "end_to_end" in test_markers:
            return min(2, cpu_count)  # E2Eは最大2並列
        elif memory_gb < 4:
            return min(2, cpu_count)  # メモリ不足時は制限
        else:
            # 通常のユニット/統合テスト
            return min(4, cpu_count)  # 最大4並列


def pytest_configure(config):
    """Configure pytest with optimal xdist settings"""
    logger = get_logger(__name__)

    # PYTHONPATH設定 - ワーカープロセスでも確実に適用
    project_root = Path(__file__).parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 環境変数としてもPYTHONPATHを設定（xdistワーカー用）
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if str(project_root) not in current_pythonpath:
        if current_pythonpath:
            os.environ["PYTHONPATH"] = f"{project_root}:{current_pythonpath}"
        else:
            os.environ["PYTHONPATH"] = str(project_root)

    logger.debug(f"PYTHONPATH configured: {os.environ.get('PYTHONPATH', 'Not set')}")

    # anyioバックエンド設定 - trioが利用できない場合はasyncioのみ
    if hasattr(config.option, "anyio_backends"):
        if not trio_available:
            config.option.anyio_backends = ["asyncio"]
        else:
            config.option.anyio_backends = ["asyncio", "trio"]

    # Issue #1004: pytest-benchmarkとxdistの競合回避
    try:
        import pytest_benchmark

        if config.getoption("--numprocesses", default=None) or getattr(
            config.option, "dist", None
        ):
            config.addinivalue_line("addopts", "--benchmark-disable")
            logger.debug("Benchmark disabled for parallel execution")
    except ImportError:
        pass

    # Issue #1049: 動的xdist設定
    # コマンドラインで明示的に指定されている場合はそれを優先
    explicit_workers = config.getoption("--numprocesses", default=None)
    if explicit_workers is None:
        # 環境に応じた最適ワーカー数の決定
        optimal_workers = _get_optimal_worker_count()

        # xdist設定の動的適用
        config.addinivalue_line("addopts", f"-n={optimal_workers}")
        config.addinivalue_line("addopts", "--dist=worksteal")

        logger.info(f"Configured xdist with {optimal_workers} workers")

        # 環境情報のログ出力
        is_ci = os.getenv("GITHUB_ACTIONS", "").lower() == "true"
        cpu_count = multiprocessing.cpu_count()
        try:
            memory_gb = psutil.virtual_memory().total / (1024**3)
            logger.debug(
                f"Environment: CI={is_ci}, CPU={cpu_count}, Memory={memory_gb:.1f}GB, Workers={optimal_workers}"
            )
        except:
            logger.debug(
                f"Environment: CI={is_ci}, CPU={cpu_count}, Workers={optimal_workers}"
            )
    else:
        logger.info(f"Using explicitly specified worker count: {explicit_workers}")

        # 明示的指定でも分散戦略は追加
        if not any("--dist" in str(opt) for opt in config.getini("addopts")):
            config.addinivalue_line("addopts", "--dist=worksteal")


@pytest.fixture
def logger():
    """Provide a logger instance for testing."""
    return get_logger(__name__)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_text_files(temp_dir: Path) -> Dict[str, Path]:
    """Create sample text files for testing."""
    files = {}

    # Basic notation test file
    basic_file = temp_dir / "basic_notation.txt"
    basic_file.write_text(
        """#見出し1
メインタイトル
##

これは基本的なテキストです。

#太字
重要な情報
##

通常のテキストが続きます。""",
        encoding="utf-8",
    )
    files["basic"] = basic_file

    # Complex notation test file
    complex_file = temp_dir / "complex_notation.txt"
    complex_file.write_text(
        """#見出し1
複合記法テスト
##

#太字
重要情報：#下線
強調されたテキスト
##
##

#リスト
- 項目1
- 項目2
- 項目3
#""",
        encoding="utf-8",
    )
    files["complex"] = complex_file

    # Error test file (invalid syntax)
    error_file = temp_dir / "error_syntax.txt"
    error_file.write_text(
        """#見出し1
エラーテスト
# # Missing closing marker

#太字
未完了の記法
# Missing end marker""",
        encoding="utf-8",
    )
    files["error"] = error_file

    return files


@pytest.fixture
def large_text_content() -> str:
    """Generate large text content for performance testing."""
    base_text = """#見出し{num}
セクション{num}のタイトル
##

これはセクション{num}の内容です。
複数行にわたる長いテキストコンテンツを含んでいます。

#太字
重要な情報{num}
##

さらに詳細なテキストが続きます。
"""

    # Generate 1000 sections for performance testing
    content_parts = []
    for i in range(1000):
        content_parts.append(base_text.format(num=i))

    return "\n\n".join(content_parts)


@pytest.fixture
def config_data() -> Dict[str, Any]:
    """Provide test configuration data."""
    return {
        "encoding": "utf-8",
        "output_format": "html",
        "template": "base.html.j2",
        "strict_validation": True,
        "performance_monitoring": False,
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for each test."""
    # Set test-specific environment variables
    os.environ["KUMIHAN_TEST_MODE"] = "true"
    os.environ["KUMIHAN_LOG_LEVEL"] = "DEBUG"

    yield

    # Clean up test environment
    os.environ.pop("KUMIHAN_TEST_MODE", None)
    os.environ.pop("KUMIHAN_LOG_LEVEL", None)


# 新規ファイル作成のため、tests/unit/test_toc_generator.py を作成
