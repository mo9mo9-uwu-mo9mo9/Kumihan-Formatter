"""
pytest設定・共通フィクスチャ - 最小限版
"""

import pytest
import tempfile
from pathlib import Path
from kumihan_formatter import KumihanFormatter


@pytest.fixture
def formatter():
    """KumihanFormatterインスタンス"""
    return KumihanFormatter()


@pytest.fixture
def sample_text():
    """テスト用サンプルテキスト"""
    return """# 重要 #これは重要な情報です##

## 見出し2

段落のテキストです。**太字**と*イタリック*を含みます。

- リスト項目1
- リスト項目2

1. 番号付きリスト1
2. 番号付きリスト2

# 注意 #注意点があります##
"""


@pytest.fixture
def temp_file():
    """一時ファイル"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".kumihan", delete=False, encoding="utf-8"
    ) as f:
        f.write("# テスト #一時ファイルテスト##\n\nテスト内容です。")
        temp_path = Path(f.name)

    yield temp_path

    # クリーンアップ
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_dir():
    """一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
