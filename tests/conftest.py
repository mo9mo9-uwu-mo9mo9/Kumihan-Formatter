"""
テスト共通設定・フィクスチャ定義

個人開発最適化のためのpytest設定（シンプル版）
"""

import tempfile
from pathlib import Path
from typing import Generator
import pytest

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
KUMIHAN_ROOT = PROJECT_ROOT / "kumihan_formatter"

# テスト用一時ディレクトリ（tmp/配下強制ルール準拠）
TEST_TMP_DIR = PROJECT_ROOT / "tmp" / "test_artifacts"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境全体の初期化"""
    # tmp/test_artifacts ディレクトリ作成
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # テスト開始時のクリーンアップ
    yield
    
    # テスト終了時の自動クリーンアップ（個人開発効率化）
    import shutil
    if TEST_TMP_DIR.exists():
        shutil.rmtree(TEST_TMP_DIR, ignore_errors=True)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリ提供（tmp/配下強制ルール準拠）"""
    with tempfile.TemporaryDirectory(dir=TEST_TMP_DIR) as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_kumihan_text() -> str:
    """サンプルKumihan記法テキスト"""
    return """# 見出し #これは見出しです##
    
# 太字 #重要な内容##
# イタリック #斜体テキスト##

通常のテキストも含まれます。

# リスト #
- 項目1
- 項目2
##"""


@pytest.fixture
def expected_html_output() -> str:
    """期待されるHTML出力"""
    return """<h1>これは見出しです</h1>
<p><strong>重要な内容</strong></p>
<p><em>斜体テキスト</em></p>
<p>通常のテキストも含まれます。</p>
<ul>
<li>項目1</li>
<li>項目2</li>
</ul>"""


@pytest.fixture
def parser_config() -> dict[str, str]:
    """パーサー設定（デフォルト）"""
    return {
        "output_format": "html",
        "encoding": "utf-8",
    }


@pytest.fixture
def test_file_path(temp_dir: Path) -> Path:
    """テスト用ファイルパス生成"""
    return temp_dir / "test_input.kumihan"


@pytest.fixture
def output_file_path(temp_dir: Path) -> Path:
    """出力ファイルパス生成"""
    return temp_dir / "test_output.html"


