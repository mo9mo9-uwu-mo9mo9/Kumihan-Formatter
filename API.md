# Kumihan-Formatter API仕様書

**統合API版**: 2025年最適化版  
**エントリーポイント**: unified_api.py

---

## 🎯 統合API概要 (2025年版アーキテクチャ)

### KumihanFormatter (メインクラス)
```python
from kumihan_formatter.unified_api import KumihanFormatter

class KumihanFormatter:
    """統合フォーマッター - 新統合Managerシステム対応"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None)
    def convert(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        template: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]
```

### 統合Managerシステム (5つのManager)
```python
# 初期化時に自動構築される内部システム
self.core_manager = CoreManager(config)           # ファイル入出力・基盤機能
self.parsing_manager = ParsingManager(config)     # 解析処理制御
self.optimization_manager = OptimizationManager(config)  # 最適化処理
self.plugin_manager = PluginManager(config)       # プラグインシステム
self.distribution_manager = DistributionManager(config)  # 配布・出力管理

# メインコンポーネント
self.main_parser = MainParser(config)             # 統合パーサー
self.main_renderer = MainRenderer(config)         # 統合レンダラー
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

## 🚀 使用例 (2025年版アーキテクチャ)

### 基本的な使用パターン
```python
from kumihan_formatter.unified_api import KumihanFormatter

# パターン1: 基本変換
formatter = KumihanFormatter()
result = formatter.convert("input.txt", "output.html")

# パターン2: 設定ファイル指定
formatter = KumihanFormatter(config_path="config.json")
result = formatter.convert("input.txt", "output.html", template="custom")

# パターン3: オプション指定
options = {"enable_toc": True, "style": "modern"}
result = formatter.convert("input.txt", "output.html", options=options)

# パターン4: 出力パス自動決定
result = formatter.convert("input.txt")  # → input.html
```

### バッチ処理
```python
from pathlib import Path
from kumihan_formatter.unified_api import KumihanFormatter

formatter = KumihanFormatter()
input_dir = Path("documents/")
output_dir = Path("html/")

for text_file in input_dir.glob("*.txt"):
    output_file = output_dir / f"{text_file.stem}.html"
    result = formatter.convert(text_file, output_file)
    print(f"変換完了: {text_file} → {output_file}")
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