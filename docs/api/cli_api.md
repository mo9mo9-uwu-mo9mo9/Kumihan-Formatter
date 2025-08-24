# CLI API リファレンス

> Kumihan-Formatter コマンドラインインターフェースの完全ガイド

## 概要

CLI APIは、Kumihan-Formatterをコマンドラインから操作するためのインターフェースを提供します。開発者向けの機能が中心となっています。

## メインコマンド

### kumihan-formatter

メインCLIエントリーポイント。

```bash
kumihan-formatter --version
# 出力: kumihan-formatter, version 3.0.0-dev
```

## サブコマンド

### convert

テキストファイルをHTMLに変換する中核コマンド。

```bash
kumihan-formatter convert [INPUT_FILE] [OPTIONS]
```

#### 基本的な使用方法

```bash
# 基本的な変換
kumihan-formatter convert document.txt

# 出力ディレクトリ指定
kumihan-formatter convert document.txt --output ./output

# 監視モード（ファイル変更を自動検出）
kumihan-formatter convert document.txt --watch

# プレビューをスキップ
kumihan-formatter convert document.txt --no-preview
```

#### オプション一覧

##### 基本オプション

| オプション | 短縮 | 説明 | デフォルト |
|------------|------|------|------------|
| `--output` | `-o` | 出力ディレクトリ | `./dist` |
| `--no-preview` | - | 変換後のブラウザプレビューをスキップ | False |
| `--watch` | `-w` | ファイル変更を監視して自動変換 | False |
| `--config` | `-c` | 設定ファイルのパス | - |
| `--template` | - | 使用するテンプレート名 | 自動選択 |
| `--include-source` | - | ソース表示機能を含める | False |

##### 開発者向けオプション

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `--show-test-cases` | テストケースを表示 | False |
| `--no-syntax-check` | 変換前の構文チェックをスキップ | False |

##### プログレス表示オプション

| オプション | 短縮 | 値 | 説明 | デフォルト |
|------------|------|---|------|------------|
| `--progress-level` | `-p` | `silent`/`minimal`/`detailed`/`verbose` | プログレス表示の詳細レベル | `detailed` |
| `--no-progress-tooltip` | - | - | プログレス表示でツールチップ情報を無効化 | False |
| `--disable-cancellation` | - | - | 処理のキャンセル機能を無効化 | False |
| `--progress-style` | - | `bar`/`spinner`/`percentage` | プログレス表示スタイル | `bar` |
| `--progress-log` | - | ファイルパス | プログレスログの出力先ファイル（JSON形式） | - |

##### エラーハンドリングオプション（Issue #700対応）

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `--continue-on-error` | 記法エラーが発生してもHTML生成を継続 | False |
| `--graceful-errors` | エラー情報をHTMLに埋め込んで表示 | False |
| `--error-level` | エラー処理レベル（`strict`/`normal`/`lenient`/`ignore`） | `normal` |
| `--no-suggestions` | エラー修正提案を非表示 | False |
| `--no-statistics` | エラー統計を非表示 | False |

#### 環境変数サポート

CLIオプションは対応する環境変数でも設定可能：

```bash
# 環境変数での設定例
export KUMIHAN_PROGRESS_LEVEL=verbose
export KUMIHAN_NO_PROGRESS_TOOLTIP=1
export KUMIHAN_DISABLE_CANCELLATION=1
export KUMIHAN_PROGRESS_STYLE=spinner
export KUMIHAN_PROGRESS_LOG=/tmp/kumihan_progress.json
export KUMIHAN_CONTINUE_ON_ERROR=1
export KUMIHAN_GRACEFUL_ERRORS=1
export KUMIHAN_ERROR_LEVEL=lenient

# コマンド実行（環境変数が適用される）
kumihan-formatter convert document.txt
```

#### 使用例

##### 基本的な変換

```bash
# シンプルな変換
kumihan-formatter convert my-document.txt

# カスタム出力先
kumihan-formatter convert my-document.txt -o ./build

# ソース表示機能付き
kumihan-formatter convert my-document.txt --include-source
```

##### 開発・デバッグ用

```bash
# 詳細なプログレス表示
kumihan-formatter convert large-file.txt --progress-level verbose

# エラー処理の緩和
kumihan-formatter convert draft.txt --graceful-errors --continue-on-error

# 構文チェックをスキップして高速変換
kumihan-formatter convert trusted-file.txt --no-syntax-check
```

##### 監視モード

```bash
# ファイル変更を監視して自動変換
kumihan-formatter convert document.txt --watch --output ./dist

# 監視モード + プレビュー無効
kumihan-formatter convert document.txt --watch --no-preview
```

##### プログレスログ出力

```bash
# JSON形式でプログレスログを記録
kumihan-formatter convert document.txt --progress-log ./logs/progress.json

# ログ内容例
{
  "timestamp": "2025-01-28T10:30:45",
  "current_line": 150,
  "total_lines": 500,
  "progress_percent": 30.0,
  "processing_rate": 125.5,
  "eta_seconds": 45
}
```

### check-syntax

Kumihanテキストの構文チェックを実行。

```bash
kumihan-formatter check-syntax [INPUT_FILE]
```

**機能:**
- 構文エラーの検出
- 記法の検証
- 修正提案の表示

### generate-sample

サンプルドキュメントの生成。

```bash
kumihan-formatter generate-sample [OPTIONS]
```

**機能:**
- サンプルKumihanテキストの生成
- 記法デモンストレーション
- テスト用データの作成

## プログラムAPI

### CLI関数の直接呼び出し

```python
from kumihan_formatter.cli import cli

# Click コンテキストでの実行
import click
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(cli, ['convert', 'input.txt', '--output', './dist'])
print(result.output)
print(f"終了コード: {result.exit_code}")
```

### コマンドクラスの直接使用

```python
from kumihan_formatter.commands.convert.convert_command import ConvertCommand

# ConvertCommandの直接実行
command = ConvertCommand()
command.execute(
    input_file="document.txt",
    output="./dist",
    no_preview=True,
    watch=False,
    config=None,
    show_test_cases=False,
    template_name=None,
    include_source=False,
    syntax_check=True,
    progress_level="detailed",
    show_progress_tooltip=True,
    enable_cancellation=True,
    progress_style="bar",
    progress_log=None,
    continue_on_error=False,
    graceful_errors=False,
    error_level="normal",
    no_suggestions=False,
    no_statistics=False,
)
```

## エラーハンドリング

### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | 一般的なエラー |
| 2 | 構文エラー（`--error-level strict`時） |
| 3 | ファイルI/Oエラー |
| 4 | 設定エラー |

### エラーメッセージ形式

```bash
# 構文エラー例
❌ 構文エラー: 行15: 未完了のブロック記法 '#太字 内容'
💡 修正提案: '##'を追加してブロックを完了してください

# ファイルエラー例
❌ ファイルエラー: 入力ファイル 'missing.txt' が見つかりません
```

## 設定ファイル連携

### 設定ファイル形式

**YAML形式**（`kumihan.yml`）:
```yaml
# Kumihan-Formatter 設定
template: "custom-template"
output_dir: "./build"
include_source: true
progress_level: "minimal"
error_level: "lenient"
```

**TOML形式**（`kumihan.toml`）:
```toml
[kumihan]
template = "custom-template"
output_dir = "./build"
include_source = true
progress_level = "minimal"
error_level = "lenient"
```

### 設定の優先順位

1. コマンドラインオプション（最高優先）
2. 環境変数
3. 設定ファイル（`--config`で指定）
4. デフォルト値

## 統合例

### シェルスクリプトでの自動化

```bash
#!/bin/bash
# document_builder.sh

# 複数ファイルの一括変換
for file in documents/*.txt; do
    echo "変換中: $file"
    kumihan-formatter convert "$file" \
        --output "./build" \
        --no-preview \
        --progress-level minimal \
        --graceful-errors
done

echo "すべての変換が完了しました"
```

### Pythonスクリプトでの統合

```python
import subprocess
import sys
from pathlib import Path

def batch_convert(input_dir: str, output_dir: str):
    """ディレクトリ内のすべてのテキストファイルを変換"""
    
    input_path = Path(input_dir)
    txt_files = list(input_path.glob("*.txt"))
    
    for txt_file in txt_files:
        print(f"変換中: {txt_file}")
        
        result = subprocess.run([
            sys.executable, "-m", "kumihan_formatter",
            "convert", str(txt_file),
            "--output", output_dir,
            "--no-preview",
            "--graceful-errors"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {txt_file.name} 変換完了")
        else:
            print(f"❌ {txt_file.name} 変換失敗: {result.stderr}")

# 使用例
batch_convert("./documents", "./build")
```

### GitHub Actions統合

```yaml
# .github/workflows/docs.yml
name: Documentation Build

on:
  push:
    paths:
      - 'docs/**/*.txt'

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install Kumihan-Formatter
        run: pip install -e .
      
      - name: Convert Documents
        run: |
          kumihan-formatter convert docs/source.txt \
            --output ./docs-build \
            --no-preview \
            --progress-level minimal \
            --graceful-errors
      
      - name: Deploy to Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs-build
```

## デバッグ・トラブルシューティング

### 詳細ログ出力

```bash
# 詳細なデバッグ情報
PYTHONPATH=. python -m kumihan_formatter convert document.txt \
    --progress-level verbose \
    --progress-log debug.json

# ログファイルの確認
cat debug.json | jq '.'
```

### プロファイリング

```bash
# パフォーマンス測定
python -m cProfile -o profile.stats \
    -m kumihan_formatter convert large-document.txt

# プロファイル結果の分析
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

## 開発者向け統合

### カスタムコマンドの追加

```python
# custom_command.py
import click
from kumihan_formatter.cli import cli

@click.command()
@click.argument('input_file')
def my_custom_command(input_file: str):
    """カスタムコマンドの実装"""
    print(f"カスタム処理: {input_file}")

# コマンドの登録
cli.add_command(my_custom_command, name="custom")
```

### プラグインシステム

```python
# plugin_example.py
from kumihan_formatter.core.plugins import PluginManager

class MyPlugin:
    def process_before_parse(self, text: str) -> str:
        """パース前の前処理"""
        return text.replace("OLD", "NEW")
    
    def process_after_render(self, html: str) -> str:
        """レンダリング後の後処理"""
        return html + "<!-- Custom footer -->"

# プラグインの登録
plugin_manager = PluginManager()
plugin_manager.register(MyPlugin())
```

## テスト・検証

### 構文チェック

```bash
# 構文の検証のみ
kumihan-formatter check-syntax document.txt

# 出力例
✅ 構文チェック完了: エラーなし
📊 統計: 見出し 5個, ブロック記法 12個, インライン記法 8個
```

### サンプル生成

```bash
# サンプルドキュメントの生成
kumihan-formatter generate-sample

# 特定の記法のサンプル
kumihan-formatter generate-sample --type headings
kumihan-formatter generate-sample --type blocks
kumihan-formatter generate-sample --type inline
```

## パフォーマンス最適化

### 大容量ファイル処理

```bash
# 大容量ファイル用の最適化
kumihan-formatter convert huge-document.txt \
    --progress-level minimal \
    --no-progress-tooltip \
    --progress-style percentage
```

### 並列処理

並列処理は自動的に以下の条件で有効化されます：

- ファイルサイズ > 1MB
- 行数 > 1000行
- 利用可能CPU数 > 1

### メモリ使用量制御

```bash
# メモリ制限環境での実行
KUMIHAN_MEMORY_LIMIT=100 \
    kumihan-formatter convert document.txt
```

## エラーリカバリ

### グレースフルエラーハンドリング

```bash
# エラーがあっても変換を継続
kumihan-formatter convert problematic.txt \
    --graceful-errors \
    --continue-on-error \
    --error-level lenient
```

### エラー詳細分析

```bash
# エラー統計を含む詳細分析
kumihan-formatter convert document.txt \
    --graceful-errors \
    --error-level strict \
    --progress-level verbose
```

## 関連ドキュメント

- [Parser API](parser_api.md) - パーサーAPI詳細
- [Renderer API](renderer_api.md) - レンダラーAPI詳細
- [開発環境構築](../dev/getting_started.md) - 開発者向けセットアップ
- [アーキテクチャ](../dev/architecture.md) - システム設計思想
- [ユーザーガイド](../user/user-guide.md) - エンドユーザー向けガイド