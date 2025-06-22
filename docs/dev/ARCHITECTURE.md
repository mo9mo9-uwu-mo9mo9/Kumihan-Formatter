# Kumihan-Formatter アーキテクチャガイド

## 概要

Kumihan-Formatterは、モジュラーな設計に基づいたテキスト→HTML変換ツールです。

## コンポーネント構成

```
kumihan_formatter/
├── cli.py          # CLIエントリポイント (Click)
├── parser.py       # テキスト解析 → AST生成
├── renderer.py     # AST → HTML変換 (Jinja2)
├── config.py       # 設定ファイル管理
├── sample_content.py  # サンプル生成機能
└── templates/      # HTMLテンプレート
```

## データフロー

```
入力テキスト
    ↓
Parser (parser.py)
    ↓ [AST: Node型の配列]
Renderer (renderer.py)
    ↓ [HTML文字列]
出力HTML
```

## 主要クラス

### Parser
- `parse()`: メインの解析メソッド
- `_parse_block_marker()`: ブロックマーカー解析
- `_parse_list_item()`: リスト項目解析

### Renderer
- `render()`: メインのレンダリングメソッド
- `_render_node()`: 個別ノードのHTML変換
- `_generate_toc_html()`: 目次生成

### Node
```python
@dataclass
class Node:
    type: str  # 'paragraph', 'h1', 'image', etc.
    content: str
    children: List['Node'] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
```

## 拡張ポイント

1. **新しいマーカー追加**: `parser.py`の`MARKERS`辞書
2. **新しいスタイル追加**: `config.py`のデフォルト設定
3. **レンダリングカスタマイズ**: `renderer.py`の`_render_node()`

## テスト戦略

- ユニットテスト: 各コンポーネントの境界値テスト
- 統合テスト: エンドツーエンドの変換テスト
- ゴールデンテスト: 期待出力との比較