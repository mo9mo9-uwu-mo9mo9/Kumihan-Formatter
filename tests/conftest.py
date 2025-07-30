"""
Test configuration and fixtures for Kumihan-Formatter test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Generator

from kumihan_formatter.core.utilities.logger import get_logger


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
    basic_file.write_text("""#見出し1
メインタイトル
##

これは基本的なテキストです。

#太字
重要な情報
##

通常のテキストが続きます。""", encoding="utf-8")
    files["basic"] = basic_file
    
    # Complex notation test file
    complex_file = temp_dir / "complex_notation.txt"
    complex_file.write_text("""#見出し1
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
#""", encoding="utf-8")
    files["complex"] = complex_file
    
    # Error test file (invalid syntax)
    error_file = temp_dir / "error_syntax.txt"
    error_file.write_text("""#見出し1
エラーテスト
# # Missing closing marker

#太字
未完了の記法
# Missing end marker""", encoding="utf-8")
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
        "performance_monitoring": False
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