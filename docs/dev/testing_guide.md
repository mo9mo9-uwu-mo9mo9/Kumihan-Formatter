# テストガイド

> Kumihan-Formatter テスト作成・実行の完全ガイド

## 概要

本ドキュメントでは、Kumihan-Formatterプロジェクトにおけるテストの作成方法、実行方法、およびベストプラクティスを説明します。

## テスト構造

### ディレクトリ構成

```
tests/
├── conftest.py           # 共通フィクスチャ・設定
├── unit/                 # ユニットテスト
│   ├── test_parser_*.py
│   └── test_renderer_*.py
├── integration/          # 統合テスト
│   ├── test_parse_render.py
│   └── test_cli_commands.py
├── e2e/                  # エンドツーエンドテスト
│   └── test_full_workflow.py
└── fixtures/             # テストデータ
    ├── input_samples/
    └── expected_outputs/
```

### テストの種類

#### 1. ユニットテスト
- **対象**: 個別のクラス・関数
- **特徴**: 高速、独立性、特定機能の詳細検証
- **実行時間**: < 1秒/テスト

#### 2. 統合テスト
- **対象**: 複数コンポーネントの連携
- **特徴**: パーサー + レンダラーの組み合わせテスト
- **実行時間**: 1-5秒/テスト

#### 3. E2Eテスト
- **対象**: 全体フローの動作確認
- **特徴**: CLIコマンドから最終出力まで
- **実行時間**: 5-30秒/テスト

## テスト実行

### 基本コマンド

```bash
# 全テスト実行
make test

# または
pytest

# 高速ユニットテストのみ
make test-unit

# 特定ファイルのテスト
pytest tests/unit/test_parser_config.py

# 特定テスト関数
pytest tests/unit/test_parser_config.py::test_parser_basic_functionality

# 詳細出力
pytest -v

# カバレッジ付き実行
pytest --cov=kumihan_formatter --cov-report=html:tmp/htmlcov
```

### マーカーを使った実行

```bash
# ユニットテストのみ
pytest -m unit

# 統合テストのみ  
pytest -m integration

# 重いテストを除外
pytest -m "not slow"

# 並列テスト実行（高速化）
pytest -n auto
```

## テスト作成

### 基本テンプレート

```python
"""
テストモジュールのテンプレート
"""
import pytest
from pathlib import Path

from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer


class TestFeatureName:
    """機能名のテストクラス"""
    
    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.parser = Parser()
        self.renderer = Renderer()
    
    def test_basic_functionality(self):
        """基本機能のテスト"""
        # Given: テストデータ準備
        input_text = "# 見出し1 #\\nテストタイトル\\n##"
        
        # When: 実行
        nodes = self.parser.parse(input_text)
        html = self.renderer.render(nodes)
        
        # Then: 検証
        assert len(nodes) > 0
        assert "<h1>" in html
        assert "テストタイトル" in html
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # Given: 不正な入力
        invalid_input = "# 未完了ブロック"
        
        # When: エラーが期待される処理
        with pytest.raises(Exception):
            self.parser.parse(invalid_input)
    
    @pytest.mark.slow
    def test_large_input(self):
        """大容量データのテスト"""
        # 時間のかかるテストにはマーカーを付与
        large_input = "# 見出し #\\nコンテンツ\\n##\\n" * 10000
        nodes = self.parser.parse(large_input)
        assert len(nodes) == 10000


@pytest.mark.unit
class TestSpecificComponent:
    """特定コンポーネントのテスト"""
    
    def test_component_specific_feature(self):
        """コンポーネント固有機能のテスト"""
        pass
```

### フィクスチャの活用

```python
"""
フィクスチャを活用したテスト例
"""
import pytest


@pytest.fixture
def sample_document():
    """サンプル文書フィクスチャ"""
    return """
    # 見出し1 #メインタイトル##
    
    # 太字 #重要な情報##
    
    通常のテキスト段落です。
    
    # リスト #
    - 項目1
    - 項目2
    - 項目3
    ##
    """


@pytest.fixture
def parser_with_config():
    """設定済みパーサーフィクスチャ"""
    from kumihan_formatter.parser import Parser, ParallelProcessingConfig
    
    config = ParallelProcessingConfig(parallel_threshold_lines=100)
    return Parser(parallel_config=config, graceful_errors=True)


class TestWithFixtures:
    """フィクスチャを使用したテストクラス"""
    
    def test_parse_sample_document(self, sample_document, parser_with_config):
        """サンプル文書の解析テスト"""
        nodes = parser_with_config.parse(sample_document)
        
        # 見出し、段落、リストの存在確認
        node_types = [node.type for node in nodes]
        assert "heading" in node_types
        assert "text" in node_types
        assert "list" in node_types
    
    def test_output_to_temp_dir(self, temp_dir, sample_document):
        """一時ディレクトリへの出力テスト"""
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.renderer import Renderer
        
        parser = Parser()
        renderer = Renderer()
        
        nodes = parser.parse(sample_document)
        html = renderer.render(nodes, title="テスト文書")
        
        # tmp/配下への出力（ルール遵守）
        output_file = temp_dir / "test_output.html"
        with output_file.open("w", encoding="utf-8") as f:
            f.write(html)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
```

### パラメータ化テスト

```python
"""
パラメータ化テストの例
"""
import pytest


class TestKumihanSyntax:
    """Kumihan記法のテストクラス"""
    
    @pytest.mark.parametrize("input_text,expected_type", [
        ("# 見出し1 #タイトル##", "heading"),
        ("# 太字 #強調テキスト##", "text"),
        ("# イタリック #斜体テキスト##", "text"),
        ("# 枠線 #囲み内容##", "block"),
    ])
    def test_syntax_parsing(self, input_text, expected_type, parser_instance):
        """各種記法の解析テスト（パラメータ化）"""
        nodes = parser_instance.parse(input_text)
        
        assert len(nodes) > 0
        # 特定の記法に応じた検証を追加
    
    @pytest.mark.parametrize("error_input", [
        "# 未完了ブロック",
        "# 見出し1 #内容",  # 終了タグなし
        "見出し1 #内容##",   # 開始タグなし
    ])
    def test_syntax_errors(self, error_input, parser_instance):
        """構文エラーのテスト"""
        # グレースフルエラーハンドリング使用時
        parser = Parser(graceful_errors=True)
        nodes = parser.parse(error_input)
        
        # エラーが記録されているか確認
        assert parser.has_graceful_errors()
        errors = parser.get_graceful_errors()
        assert len(errors) > 0
```

### モック・パッチの使用

```python
"""
モック・パッチを使用したテスト例
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestExternalDependencies:
    """外部依存関係のテスト"""
    
    def test_file_operations_with_mock(self, temp_dir):
        """ファイル操作のモックテスト"""
        from pathlib import Path
        
        # ファイル読み込みをモック
        mock_content = "# モック #テストコンテンツ##"
        
        with patch('pathlib.Path.open') as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = mock_content
            mock_open.return_value = mock_file
            
            # テスト対象実行
            # ここでファイル読み込みを使用する機能をテスト
            pass
    
    @patch('kumihan_formatter.core.utilities.logger.get_logger')
    def test_logging_behavior(self, mock_logger):
        """ログ出力動作のテスト"""
        from kumihan_formatter.parser import Parser
        
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        parser = Parser()
        parser.parse("# テスト #内容##")
        
        # ログ出力が呼ばれたか確認
        mock_logger_instance.info.assert_called()
```

## テスト品質管理

### カバレッジ目標

```bash
# カバレッジレポート生成
pytest --cov=kumihan_formatter --cov-report=html:tmp/htmlcov

# カバレッジ確認
open tmp/htmlcov/index.html  # macOS
# または
xdg-open tmp/htmlcov/index.html  # Linux
```

**カバレッジ目標:**
- 全体: 80%以上
- 新規コード: 90%以上
- 中核機能（Parser/Renderer): 95%以上

### テスト品質チェックリスト

#### ✅ 必須項目
- [ ] 各テストは独立して実行可能
- [ ] テスト名は実行内容を明確に表現
- [ ] 適切なアサーションを使用
- [ ] エラーケースもテスト
- [ ] tmp/配下への出力遵守

#### ✅ 推奨項目
- [ ] 境界値テストの実施
- [ ] パフォーマンステストの追加
- [ ] 大容量データでのテスト
- [ ] 並列処理のテスト
- [ ] メモリリーク検出

### テストデータ管理

```python
"""
テストデータ管理の例
"""
import json
from pathlib import Path


class TestDataManager:
    """テストデータ管理クラス"""
    
    def __init__(self, test_data_dir: Path):
        self.test_data_dir = test_data_dir
    
    def load_sample_text(self, filename: str) -> str:
        """サンプルテキストの読み込み"""
        file_path = self.test_data_dir / "samples" / filename
        return file_path.read_text(encoding="utf-8")
    
    def load_expected_output(self, filename: str) -> str:
        """期待出力の読み込み"""
        file_path = self.test_data_dir / "expected" / filename
        return file_path.read_text(encoding="utf-8")
    
    def save_test_result(self, result_data: dict, filename: str) -> None:
        """テスト結果をtmp/配下に保存"""
        tmp_dir = Path("tmp/test_results")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = tmp_dir / filename
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)


@pytest.fixture(scope="session")
def test_data_manager():
    """テストデータマネージャーフィクスチャ"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return TestDataManager(fixtures_dir)
```

## パフォーマンステスト

### ベンチマークテスト

```python
"""
パフォーマンステストの例
"""
import time
import pytest
from pathlib import Path


class TestPerformance:
    """パフォーマンステストクラス"""
    
    @pytest.mark.slow
    def test_large_document_performance(self):
        """大容量文書の処理性能テスト"""
        from kumihan_formatter.parser import Parser
        from kumihan_formatter.renderer import Renderer
        
        # 大容量テストデータ生成
        large_text = self._generate_large_document(lines=10000)
        
        parser = Parser()
        renderer = Renderer()
        
        # パース性能測定
        start_time = time.time()
        nodes = parser.parse_optimized(large_text)
        parse_time = time.time() - start_time
        
        # レンダリング性能測定
        start_time = time.time()
        html = renderer.render(nodes)
        render_time = time.time() - start_time
        
        # 性能基準チェック
        assert parse_time < 5.0, f"パース時間が遅すぎます: {parse_time:.2f}秒"
        assert render_time < 3.0, f"レンダリング時間が遅すぎます: {render_time:.2f}秒"
        
        # 結果をtmp/配下に記録
        self._save_performance_result({
            "lines": 10000,
            "parse_time": parse_time,
            "render_time": render_time,
            "total_time": parse_time + render_time,
            "nodes_count": len(nodes),
            "html_size": len(html)
        })
    
    def _generate_large_document(self, lines: int) -> str:
        """大容量文書生成"""
        content = []
        for i in range(lines):
            if i % 100 == 0:
                content.append(f"# 見出し1 #セクション {i//100}##")
            else:
                content.append(f"行 {i}: テストコンテンツ " + "x" * (i % 50))
        return "\\n".join(content)
    
    def _save_performance_result(self, result: dict) -> None:
        """性能テスト結果の保存"""
        import json
        tmp_dir = Path("tmp/performance_results")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = tmp_dir / f"perf_test_{int(time.time())}.json"
        with result_file.open("w") as f:
            json.dump(result, f, indent=2)
```

### メモリテスト

```python
"""
メモリ使用量テストの例
"""
import gc
import psutil
import pytest
from pathlib import Path


class TestMemoryUsage:
    """メモリ使用量テストクラス"""
    
    def test_memory_leak_detection(self):
        """メモリリーク検出テスト"""
        from kumihan_formatter.parser import Parser
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        parser = Parser()
        sample_text = "# 見出し #テスト##\\n" * 1000
        
        # 複数回実行してメモリリークを検出
        for i in range(100):
            nodes = parser.parse(sample_text)
            if i % 10 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # メモリ増加量が許容範囲内か確認（10MB以下）
        assert memory_increase < 10 * 1024 * 1024, (
            f"メモリリークの可能性: {memory_increase / 1024 / 1024:.2f}MB増加"
        )
```

## CI/CD統合

### GitHub Actions設定例

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,test]
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=kumihan_formatter --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### プレコミットフック

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit/ -x
        language: system
        types: [python]
        pass_filenames: false
        
      - id: coverage-check
        name: coverage check
        entry: pytest --cov=kumihan_formatter --cov-fail-under=80
        language: system
        types: [python]
        pass_filenames: false
```

## デバッグ・トラブルシューティング

### よくあるテストエラー

#### 1. ImportError
```bash
# 原因: パッケージが正しくインストールされていない
# 解決方法
pip install -e .
```

#### 2. FileNotFoundError
```python
# 原因: テストファイルの絶対パス指定なし
# 解決例
test_file = Path(__file__).parent / "fixtures" / "sample.txt"
```

#### 3. tmp/ディレクトリ関連エラー
```python
# 原因: tmp/配下への出力ルール違反
# 解決例
from pathlib import Path
tmp_dir = Path("tmp/test_output")
tmp_dir.mkdir(parents=True, exist_ok=True)
```

### デバッグ用ツール

```python
"""
テストデバッグ用ヘルパー
"""
import json
from pathlib import Path


def debug_test_data(data: any, tag: str = "debug") -> None:
    """テストデータのデバッグ出力"""
    tmp_dir = Path("tmp/test_debug")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    debug_file = tmp_dir / f"{tag}_data.json"
    with debug_file.open("w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"デバッグデータ出力: {debug_file}")


def print_test_progress(test_name: str, step: str) -> None:
    """テストの進行状況を表示"""
    print(f"[{test_name}] {step}")
```

## ベストプラクティス

### 1. テスト命名規則
```python
# ✅ 良い例: 何をテストしているかが明確
def test_parser_handles_empty_input_gracefully():
    pass

def test_renderer_generates_valid_html_for_heading_nodes():
    pass

# ❌ 悪い例: 曖昧で内容が不明
def test_parser_1():
    pass

def test_something():
    pass
```

### 2. アサーション選択
```python
# ✅ 具体的なアサーション
assert len(nodes) == 3
assert node.type == "heading"
assert "expected_text" in html_output

# ❌ 曖昧なアサーション  
assert nodes
assert html_output
```

### 3. テストの独立性
```python
# ✅ 各テストが独立
class TestParser:
    def setup_method(self):
        self.parser = Parser()  # 毎回新しいインスタンス
    
    def test_feature_a(self):
        # このテストは他のテストに依存しない
        pass
```

### 4. エラーメッセージ
```python
# ✅ 詳細なエラーメッセージ
assert len(nodes) == expected_count, (
    f"Expected {expected_count} nodes, but got {len(nodes)}. "
    f"Nodes: {[n.type for n in nodes]}"
)

# ❌ 不十分なエラーメッセージ
assert len(nodes) == expected_count
```

## 関連ドキュメント

- [コーディング規約](coding-standards.md) - 開発規約とベストプラクティス
- [アーキテクチャ](architecture.md) - システム設計思想
- [Parser API](../api/parser_api.md) - パーサーAPI仕様
- [Renderer API](../api/renderer_api.md) - レンダラーAPI仕様