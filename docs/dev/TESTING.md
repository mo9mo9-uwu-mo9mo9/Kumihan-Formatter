# Kumihan-Formatter テストガイド

## テスト実行方法

```bash
# 仮想環境のアクティベート
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest dev/tests/test_parser.py

# 特定のテストケースを実行
pytest dev/tests/test_parser.py::test_combined_markers

# カバレッジレポート付き
pytest --cov=kumihan_formatter
```

## テストファイル構成

```
dev/tests/
├── test_parser.py      # パーサーのテスト
├── test_renderer.py    # レンダラーのテスト
├── test_config.py      # 設定機能のテスト
├── test_cli.py         # CLIのテスト
├── test_toc.py         # 目次機能のテスト
├── test_image_embedding.py  # 画像埋め込みのテスト
└── test_sample_generation.py # サンプル生成のテスト
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