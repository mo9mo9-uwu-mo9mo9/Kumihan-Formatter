# Kumihan-Formatter API 仕様書

**バージョン**: 0.9.0-alpha.8  
**最終更新**: 2025年8月24日  
**対応Issue**: #1172 アーキテクチャ最適化最終フェーズ

---

## 📖 概要

Kumihan-Formatter は、日本語テキストを美しいHTMLに変換する専用ツールです。独自のブロック記法 (`# 装飾名 #内容##`) を使用して、直感的で高品質な文書生成を実現します。

---

## 🔧 Core API

### 1. Parser API

#### `kumihan_formatter.parser.Parser`

**基本的なパーシングエンジン**

```python
from kumihan_formatter.parser import Parser

parser = Parser()
result = parser.parse(text: str) -> List[Dict[str, Any]]
```

**メソッド**:
- `parse(text: str)`: テキストをパースしてAST構造を返す
- `parse_line(line: str)`: 単一行をパース
- `get_errors()`: パースエラーの一覧を取得
- `has_graceful_errors()`: 回復可能エラーの有無確認

**使用例**:
```python
parser = Parser()
content = "# 見出し #メインタイトル##\n通常のテキスト"
ast = parser.parse(content)
```

#### `kumihan_formatter.parsers.*` (詳細パーサー)

**ブロックパーサー**: `kumihan_formatter.parsers.block_parser.BlockParser`
**キーワードパーサー**: `kumihan_formatter.parsers.keyword_parser.KeywordParser`  
**リストパーサー**: `kumihan_formatter.parsers.list_parser.ListParser`

### 2. Renderer API

#### `kumihan_formatter.renderer.Renderer`

**HTMLレンダリングエンジン**

```python
from kumihan_formatter.renderer import Renderer

renderer = Renderer()
html = renderer.render(ast_nodes: List[Node]) -> str
```

**メソッド**:
- `render(ast_nodes)`: AST構造をHTMLに変換
- `render_to_file(ast_nodes, output_path)`: ファイルに直接出力
- `set_template(template_name)`: 使用テンプレートの設定

### 3. CLI API

#### `kumihan_formatter.cli`

**コマンドラインインターフェース**

```bash
# 基本的な変換
kumihan-formatter convert input.txt

# 出力ファイル指定
kumihan-formatter convert input.txt --output output.html

# ファイル監視モード
kumihan-formatter convert input.txt --watch

# ヘルプ表示
kumihan-formatter --help
kumihan-formatter convert --help
```

**利用可能コマンド**:
- `convert`: ファイル変換
- `sample`: サンプル生成
- `--version`: バージョン表示
- `--help`: ヘルプ表示

---

## ⚙️ Configuration API

### 1. 設定管理

#### `kumihan_formatter.config.ConfigManager`

```python
from kumihan_formatter.config import ConfigManager

manager = ConfigManager()
config = manager.get_config()
```

#### `kumihan_formatter.simple_config.SimpleConfig`

```python
from kumihan_formatter.simple_config import get_simple_config

config = get_simple_config()
```

### 2. 設定ファイル形式

**YAML形式** (推奨):
```yaml
output:
  format: html
  encoding: utf-8
  template: default

processing:
  parallel: true
  threads: 4
  
debug:
  enabled: false
  log_level: INFO
```

**TOML形式**:
```toml
[output]
format = "html"
encoding = "utf-8"
template = "default"

[processing]
parallel = true
threads = 4
```

---

## 📝 Kumihan記法仕様

### 基本記法

**ブロック記法**: `# 装飾名 #内容##`

```
# 見出し1 #メインタイトル##
# 見出し2 #サブタイトル##
# 太字 #重要な情報##
# イタリック #斜体テキスト##
# ハイライト color=yellow #注目ポイント##
```

### リスト記法

```
# リスト #
- 項目1
- 項目2
  - サブ項目2-1
  - サブ項目2-2
- 項目3
##
```

### 複合記法

```
# 見出し1 #章: データ処理##

通常のパラグラフテキスト。

# 太字 #重要: 必ず確認してください##

# リスト #
- チェック項目1
- チェック項目2
##

# コード #
def example_function():
    return "Hello, Kumihan!"
##
```

---

## 🔌 プラグイン API

### プラグインマネージャー

#### `kumihan_formatter.managers.plugin_manager.PluginManager`

```python
from kumihan_formatter.managers.plugin_manager import PluginManager

plugin_manager = PluginManager()
plugin_manager.load_plugin(plugin_path, plugin_info)
```

### カスタムパーサープラグイン

```python
from kumihan_formatter.parsers.parser_protocols import ParserProtocol

class CustomParser:
    def parse(self, text: str) -> List[Node]:
        # カスタムパース処理
        return nodes
    
    def validate(self, text: str) -> bool:
        # 入力検証
        return True
```

---

## 🛠️ Utilities API

### ファイル操作

#### `kumihan_formatter.core.io.*`

```python
# ファイルマネージャー
from kumihan_formatter.core.io import FileManager

file_manager = FileManager()
content = file_manager.read_file(file_path)
file_manager.write_file(output_path, content)
```

### エンコーディング検出

#### `kumihan_formatter.core.encoding_detector.EncodingDetector`

```python
from kumihan_formatter.core.encoding_detector import EncodingDetector

detector = EncodingDetector()
encoding = detector.detect_file_encoding(file_path)
```

### ログ機能

#### `kumihan_formatter.core.utilities.logger`

```python
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)
logger.info("処理開始")
logger.error("エラーが発生しました")
```

---

## 📊 パフォーマンス特性

### 処理性能

| データサイズ | 要素数 | 処理時間 | スループット |
|-------------|--------|----------|-------------|
| 小規模 | ~10要素 | 0.0004秒 | 25,000要素/秒 |
| 中規模 | 100要素 | 0.0033秒 | 30,303要素/秒 |
| 大規模 | 1,000要素 | 0.0334秒 | 29,940要素/秒 |

### メモリ使用量

- **基本処理**: ~1-5MB
- **中規模文書**: ~10-20MB  
- **大規模文書**: ~50-100MB

### 推奨ハードウェア

- **最小**: 2GB RAM, 1CPU Core
- **推奨**: 4GB RAM, 2CPU Cores
- **大規模**: 8GB RAM, 4CPU Cores

---

## 🚨 エラーハンドリング

### 例外体系

```python
# 基底例外
from kumihan_formatter.core.common.error_base import KumihanError

# 具体的な例外
from kumihan_formatter.core.common.error_types import (
    ParsingError,        # パース処理エラー
    RenderingError,      # レンダリングエラー  
    ConfigurationError,  # 設定エラー
    ValidationError      # 検証エラー
)
```

### エラーハンドラー

```python
from kumihan_formatter.core.common.error_handler import ErrorHandler

handler = ErrorHandler()
try:
    # 処理
    result = process_document(content)
except KumihanError as e:
    handler.handle_error(e)
    error_summary = handler.get_error_summary()
```

---

## 🔄 統合 API

### 統一API

#### `kumihan_formatter.unified_api.KumihanFormatter`

**最も簡単な使用方法**

```python
from kumihan_formatter.unified_api import KumihanFormatter

# 基本的な変換
formatter = KumihanFormatter()
html = formatter.convert_text(kumihan_text)

# ファイル変換
formatter.convert_file(input_path, output_path)

# 設定付き変換
formatter = KumihanFormatter(config={
    'output': {'template': 'custom'},
    'processing': {'parallel': True}
})
```

### 関数API

```python
# シンプルな関数API
from kumihan_formatter import parse, render, convert

# パース専用
ast = parse(text)

# レンダリング専用  
html = render(ast)

# 一括変換
html = convert(text)
```

---

## 📚 使用例

### 基本的な使用

```python
from kumihan_formatter import convert

kumihan_text = """
# 見出し1 #ドキュメント作成ガイド##

このドキュメントは、Kumihan-Formatter の使用方法を説明します。

# 見出し2 #基本的な使い方##

# 太字 #重要: 必ずお読みください##

# リスト #
- ステップ1: テキストファイルを準備
- ステップ2: Kumihan記法で装飾  
- ステップ3: HTML変換実行
##

# イタリック #補足: 詳細は公式サイトを参照##
"""

html_output = convert(kumihan_text)
print(html_output)
```

### 高度な使用

```python
from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer
from kumihan_formatter.config import ConfigManager

# 設定読み込み
config_manager = ConfigManager(config_file='custom_config.yaml')
config = config_manager.get_config()

# パーサー初期化
parser = Parser(config=config)

# 文書パース
ast = parser.parse(source_text)

# カスタムレンダラー
renderer = Renderer(template='custom_template')
html = renderer.render(ast)

# ファイル出力
with open('output.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

---

## 🔧 開発者向けAPI

### パーサー拡張

```python
from kumihan_formatter.parsers.parser_protocols import ParserProtocol

class CustomKeywordParser(ParserProtocol):
    def parse(self, text: str) -> List[Node]:
        # カスタム解析ロジック
        pass
    
    def validate(self, text: str) -> bool:
        # 入力検証
        pass
```

### レンダラー拡張

```python
from kumihan_formatter.core.rendering.base_renderer import BaseRenderer

class CustomRenderer(BaseRenderer):
    def render_node(self, node: Node) -> str:
        # カスタムレンダリングロジック
        pass
```

---

## ⚠️ 既知の制限事項

### 現在の制限

1. **型システム**: mypy strict対応中 (186エラー)
2. **テストカバレッジ**: 19% (目標95%)
3. **レンダラー**: Node/dict型の不整合
4. **英語サポート**: 日本語専用（英語未対応）

### パフォーマンス制限

1. **単一スレッド**: 基本的にシングルスレッド処理
2. **メモリ制約**: 大規模文書(>100MB)では注意が必要
3. **ファイルサイズ**: 推奨最大 10MB/ファイル

---

## 🔮 今後の拡張計画

### 短期改善 (v0.9.1)
- mypy strict対応完了
- レンダラー型修正
- カバレッジ25%達成

### 中期改善 (v1.0.0)  
- API安定化
- パフォーマンス向上
- カバレッジ50%達成

### 長期改善 (v1.1.0+)
- 並列処理対応
- プラグインエコシステム
- カバレッジ95%達成

---

## 📞 サポート・連絡先

- **GitHub Issues**: [Kumihan-Formatter Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **開発者**: mo9mo9-uwu-mo9mo9
- **ライセンス**: Proprietary

---

*🔄 この仕様書は Issue #1172 アーキテクチャ最適化の一環として作成されました*