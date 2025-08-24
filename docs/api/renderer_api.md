# Renderer API リファレンス

> Kumihan-Formatter レンダラーAPIの完全ガイド

## 概要

レンダラーAPIは、パーサーが生成したASTノードを美しいHTMLに変換する機能を提供します。

## メインクラス: Renderer

### クラス概要

```python
from kumihan_formatter.renderer import Renderer

# 基本的な使用方法
renderer = Renderer()
html = renderer.render(ast_nodes)
```

### 初期化

```python
def __init__(self, template_dir: Path | None = None)
```

**パラメータ:**
- `template_dir`: カスタムテンプレートディレクトリ（デフォルト: パッケージテンプレート）

**初期化例:**
```python
# デフォルトテンプレートを使用
renderer = Renderer()

# カスタムテンプレートディレクトリを指定
from pathlib import Path
renderer = Renderer(template_dir=Path("./custom_templates"))
```

## 主要メソッド

### render()

メインのレンダリング処理。ASTノードを完全なHTMLドキュメントに変換します。

```python
def render(
    self,
    ast: list[Node],
    config: Any | None = None,
    template: str | None = None,
    title: str | None = None,
    source_text: str | None = None,
    source_filename: str | None = None,
    navigation_html: str | None = None,
    original_source_text: str | None = None,
) -> str
```

**パラメータ:**
- `ast`: レンダリング対象のASTノードリスト
- `config`: レンダリング設定（BaseConfigまたはConfigManager）
- `template`: 使用するテンプレート名
- `title`: ページタイトル
- `source_text`: ソース表示機能用のテキスト
- `source_filename`: ソース表示機能用のファイル名
- `navigation_html`: ナビゲーションHTML
- `original_source_text`: 脚注処理用の元テキスト

**戻り値:**
- `str`: 完全なHTMLドキュメント

**使用例:**
```python
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer

# パースとレンダリング
parser = Parser()
renderer = Renderer()

text = "# 見出し1 #\\nメインタイトル\\n##"
ast_nodes = parser.parse(text)

# 基本的なレンダリング
html = renderer.render(ast_nodes, title="マイドキュメント")

# ソース表示機能付き
html = renderer.render(
    ast_nodes,
    title="マイドキュメント",
    source_text=text,
    source_filename="document.txt"
)

# カスタムテンプレート使用
html = renderer.render(
    ast_nodes,
    template="custom-template",
    title="カスタムドキュメント"
)
```

### render_nodes_only()

テンプレートラッパーなしでノードのみをレンダリング。

```python
def render_nodes_only(self, nodes: list[Node]) -> str
```

**用途:**
- 部分的なHTMLコンテンツの生成
- 他のシステムとの統合

**使用例:**
```python
# ノードのみをHTML化
html_content = renderer.render_nodes_only(ast_nodes)
# 結果: <h1>タイトル</h1><p>内容</p> など
```

### render_with_custom_context()

カスタムテンプレートコンテキストでレンダリング。

```python
def render_with_custom_context(
    self, ast: list[Node], template_name: str, custom_context: dict[str, Any]
) -> str
```

**使用例:**
```python
# カスタムコンテキスト
custom_vars = {
    "site_name": "My Site",
    "author": "作成者名",
    "version": "1.0.0"
}

html = renderer.render_with_custom_context(
    ast_nodes,
    "custom-template",
    custom_vars
)
```

## ユーティリティメソッド

### 目次（TOC）関連

```python
# 目次データの取得
toc_data = renderer.get_toc_data(ast_nodes)
print(f"目次あり: {toc_data['has_toc']}")
print(f"目次HTML: {toc_data['html']}")

# 見出し一覧の取得
headings = renderer.get_headings(ast_nodes)
for heading in headings:
    print(f"レベル{heading['level']}: {heading['text']}")
```

### テンプレート管理

```python
# テンプレート検証
is_valid, error = renderer.validate_template("my-template")
if not is_valid:
    print(f"テンプレートエラー: {error}")

# 利用可能なテンプレート一覧
templates = renderer.get_available_templates()
print("利用可能テンプレート:", templates)
```

### キャッシュ管理

```python
# 内部キャッシュのクリア
renderer.clear_caches()
```

## 内部コンポーネント

### HTMLRenderer

ノードをHTMLに変換する中核コンポーネント。

**主要機能:**
- ASTノード → HTML変換
- 見出し収集
- カウンター管理

### TemplateManager

Jinja2テンプレート管理。

**主要機能:**
- テンプレート選択・検証
- テンプレートレンダリング
- キャッシュ管理

### TOCGenerator

目次生成処理。

**主要機能:**
- 見出しからの目次生成
- 階層構造の自動構築
- HTML形式での出力

## レンダリングコンテキスト

### RenderContext

レンダリング時のコンテキスト構築ヘルパー。

```python
from kumihan_formatter.core.rendering import RenderContext

context = (
    RenderContext()
    .title("ドキュメントタイトル")
    .body_content(body_html)
    .toc_html(toc_html)
    .has_toc(True)
    .css_vars(css_variables)
    .source_toggle(source_text, filename)
    .navigation(nav_html)
    .custom("custom_var", "custom_value")
)
```

## 出力形式

### 標準HTMLテンプレート

- **base.html.j2**: 基本テンプレート
- **docs.html.j2**: ドキュメント専用テンプレート
- **base-with-source-toggle.html.j2**: ソース表示機能付き

### CSS統合

レンダラーは以下のCSSコンポーネントを統合します：

- **base-styles.css**: 基本スタイル
- **blocks.css**: ブロック記法用スタイル
- **navigation.css**: ナビゲーション用スタイル
- **responsive.css**: レスポンシブ対応
- **graceful-errors.css**: エラー表示用スタイル

## エラーハンドリング

### レンダリングエラー

```python
try:
    html = renderer.render(ast_nodes)
except Exception as e:
    print(f"レンダリングエラー: {e}")
```

### テンプレートエラー

```python
# テンプレート事前検証
is_valid, error_msg = renderer.validate_template("my-template")
if not is_valid:
    print(f"テンプレートが無効: {error_msg}")
    # フォールバックテンプレートを使用
    html = renderer.render(ast_nodes, template="base")
```

## パフォーマンス考慮

### 大容量ドキュメント

```python
# 大容量ドキュメントの処理
if len(ast_nodes) > 10000:
    # キャッシュクリアで メモリ使用量を制御
    renderer.clear_caches()

html = renderer.render(ast_nodes)
```

### テンプレートキャッシュ

レンダラーは自動的にテンプレートをキャッシュして性能を向上させます。

## 統合例

### 完全な処理フロー

```python
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer
from pathlib import Path

def convert_document(input_file: str, output_file: str):
    """完全なドキュメント変換処理"""
    
    # ファイル読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # パース処理
    parser = Parser(graceful_errors=True)
    ast_nodes = parser.parse(text)
    
    # エラーチェック
    if parser.has_graceful_errors():
        print("構文エラーがありますが、変換を継続します")
    
    # レンダリング
    renderer = Renderer()
    html = renderer.render(
        ast_nodes,
        title=Path(input_file).stem,
        source_text=text,
        source_filename=Path(input_file).name
    )
    
    # 出力
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"変換完了: {output_file}")

# 使用例
convert_document("document.txt", "output.html")
```

## 関連ドキュメント

- [Parser API](parser_api.md) - パーサーAPI
- [CLI API](cli_api.md) - コマンドラインインターフェース
- [アーキテクチャ](../dev/architecture.md) - システム設計思想
- [記法仕様](../specs/notation.md) - Kumihan記法の詳細