# Kumihan-Formatter API仕様書

**統合API版**: 2025年最適化版  
**エントリーポイント**: unified_api.py

---

## 🎯 統合API概要

### KumihanFormatter (メインクラス)
```python
from kumihan_formatter.unified_api import KumihanFormatter

class KumihanFormatter:
    """統合フォーマッター - 単一エントリーポイント"""
    
    def __init__(self, config_path: Optional[Path] = None)
    def convert(self, input_path: Path, output_path: Path) -> bool
    def convert_text(self, text: str) -> str
    def parse_text(self, text: str) -> ParseResult
    def validate_syntax(self, text: str) -> ValidationResult
```

### クイック関数群
```python
# 高速変換
quick_convert(input_path: str, output_path: str = None) -> str

# 高速パース
quick_parse(text: str) -> ParseResult

# 統合パース (自動パーサー選択)
unified_parse(content: str, parser_type: str = "auto") -> ParseResult

# 構文検証
validate_kumihan_syntax(text: str) -> ValidationResult
```

---

## 📋 主要パーサー

### SimpleKumihanParser
```python
from kumihan_formatter.simple_parser import SimpleKumihanParser

parser = SimpleKumihanParser()
result = parser.parse(text)  # ParseResult返却
```

**対応記法**:
- ブロック記法: `# 装飾 #内容##`
- 見出し記法: `# 見出し1 #タイトル##`
- リスト記法: `-` `1.` 記法
- インライン記法: 太字・イタリック

### 統合パーサー群
```python
# 自動選択 (推奨)
result = unified_parse(content, "auto")

# 個別指定
result = unified_parse(content, "content")  # ContentParser
result = unified_parse(content, "block")    # BlockParser
result = unified_parse(content, "list")     # ListParser
```

---

## 🎨 主要レンダラー

### SimpleHTMLRenderer
```python
from kumihan_formatter.simple_renderer import SimpleHTMLRenderer

renderer = SimpleHTMLRenderer()
html = renderer.render(parse_result)  # HTML出力
```

**出力特徴**:
- モダンCSS内蔵
- レスポンシブ対応
- アクセシビリティ準拠
- カスタマイズ可能

---

## 🔧 設定・カスタマイズ

### 設定システム
```python
formatter = KumihanFormatter()

# テンプレート設定
templates = formatter.get_available_templates()
formatter.config.template = 'modern'

# システム情報
info = formatter.get_system_info()
print(info['version'], info['parsers'])
```

### エラーハンドリング
```python
try:
    result = formatter.convert_text(text)
    if result.success:
        print("変換成功:", result.html)
    else:
        print("変換エラー:", result.errors)
except KumihanSyntaxError as e:
    print("構文エラー:", e.message)
except KumihanProcessingError as e:
    print("処理エラー:", e.details)
```

---

## 🚀 使用例

### 基本的な使用パターン
```python
# パターン1: ワンライン変換
html = quick_convert("document.kumihan")

# パターン2: 詳細制御
with KumihanFormatter() as formatter:
    # 構文検証
    validation = formatter.validate_syntax(text)
    if validation.is_valid:
        # パース
        parsed = formatter.parse_text(text)
        # レンダリング (自動実行)
        result = formatter.convert_text(text)

# パターン3: ファイル処理
formatter = KumihanFormatter()
success = formatter.convert("input.kumihan", "output.html")
```

### バッチ処理
```python
from pathlib import Path

formatter = KumihanFormatter()
input_dir = Path("documents/")
output_dir = Path("html/")

for kumihan_file in input_dir.glob("*.kumihan"):
    output_file = output_dir / f"{kumihan_file.stem}.html"
    formatter.convert(kumihan_file, output_file)
```

---

## 📊 パフォーマンス

### 最適化済み機能
- **高速インポート**: 0.015秒
- **チャンク処理**: 大容量ファイル対応
- **並列処理**: CPU効率化
- **メモリ効率**: ストリーミング処理

### 推奨使用方法
- **小規模**: quick_convert使用
- **中規模**: KumihanFormatter + with文
- **大規模**: チャンク処理 + 並列化
- **バッチ**: 統合API + ループ処理

---

## 🔍 トラブルシューティング

### よくあるエラー
```python
# 構文エラー
KumihanSyntaxError: "無効な記法: '# 見出し #内容#'"
→ 正しい記法: '# 見出し1 #内容##'

# ファイルエラー  
FileNotFoundError: "入力ファイルが見つかりません"
→ パス確認、存在チェック実行

# 処理エラー
KumihanProcessingError: "レンダリングに失敗"
→ 入力データ検証、ログ確認
```

### デバッグ方法
```python
# ログ有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# システム情報確認
formatter = KumihanFormatter()
print(formatter.get_system_info())

# 段階的処理
parsed = formatter.parse_text(text)
print("Parse result:", parsed.elements)
```

**詳細**: CLAUDE.md開発ガイド参照