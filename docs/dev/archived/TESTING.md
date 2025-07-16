# Kumihan-Formatter テストガイド

## テスト実行方法

```bash
# 仮想環境のアクティベート
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# すべてのテストを実行（pyproject.tomlの設定を使用）
pytest

# 特定のテストファイルを実行
pytest tests/integration/test_basic_integration.py

# 特定のテストケースを実行
pytest tests/integration/test_basic_integration.py::TestBasicIntegration::test_basic_text_conversion

# マーカーを使用したテスト実行
pytest -m unit      # ユニットテストのみ
pytest -m integration # 統合テストのみ
pytest -m e2e       # E2Eテストのみ
```

## テストファイル構成

```
tests/
├── unit/               # ユニットテスト
├── integration/        # 統合テスト
│   ├── test_basic_integration.py
│   ├── test_cli_integration.py
│   ├── test_file_io_integration.py
│   ├── test_simple_integration.py
│   └── test_template_integration.py
├── e2e/               # E2Eテスト
│   ├── test_error_handling.py
│   ├── test_option_combinations.py
│   ├── test_real_scenarios.py
│   └── test_simple_e2e.py
└── windows_permission_helper.py  # Windows権限テスト用ヘルパー
```

## テストケースの書き方

### パーサーのテスト例
```python
def test_combined_markers():
    parser = Parser()
    text = ";;;太字+イタリック\n内容\n;;;"
    result = parser.parse(text)

    assert len(result) == 1
    node = result[0]
    assert node.type == "strong"
    assert len(node.children) == 1
    assert node.children[0].type == "em"
```

### レンダラーのテスト例
```python
def test_render_heading():
    renderer = Renderer()
    nodes = [Node(type="h1", content="見出し")]
    html = renderer.render(nodes)

    assert "<h1>見出し</h1>" in html
```

## テストデータ生成

```bash
# テストパターンファイルの生成
python -m kumihan_formatter --generate-test
```

## CI/CDでのテスト

GitHub Actionsで自動実行されます（`.github/workflows/test.yml`）:
- Python 3.9, 3.10, 3.11, 3.12でのテスト
- Windows, macOS, Linuxでのクロスプラットフォームテスト
- Push時：軽量チェック（quick-check）
- PR時：フルテスト（full-test）

## テスト設定

テスト設定は `pyproject.toml` で管理されています：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=kumihan_formatter",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests",
]
```
