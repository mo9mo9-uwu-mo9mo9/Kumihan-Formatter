# Kumihan-Formatter クイックスタートガイド

**最新版**: 2025年統合最適化版  
**対象**: 初回利用者・基本操作習得

---

## 🚀 インストール・基本利用

### インストール
```bash
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter
pip install -e .
```

### 基本的な使い方
```python
# 統合API使用 (推奨)
from kumihan_formatter.unified_api import KumihanFormatter
from kumihan_formatter.core.utilities.api_utils import quick_convert

# 簡単変換
result = quick_convert("input.kumihan")

# 詳細制御
with KumihanFormatter() as formatter:
    result = formatter.convert("input.kumihan", "output.html")
```

### CLI使用
```bash
# 基本変換（エントリポイントは kumihan）
kumihan input.kumihan [output.html]

# Pythonモジュールとしての実行
python -m kumihan_formatter input.kumihan [output.html]

# ヘルプ / バージョン
kumihan --help
kumihan --version

# 破壊的操作の安全ガード
# 既存の output.html が存在する場合:
kumihan input.kumihan output.html --dry-run   # 削除/書き込みを行わず確認
kumihan input.kumihan output.html --force    # 強制上書き

# 環境変数でも強制可能
KUMIHAN_FORCE=1 kumihan input.kumihan output.html
```

---

## 📝 Kumihan記法基本

### ブロック記法
```
# 太字 #テキスト##          → <strong>テキスト</strong>
# イタリック #テキスト##     → <em>テキスト</em>
# 見出し1 #タイトル##        → <h1>タイトル</h1>
# 見出し2 #タイトル##        → <h2>タイトル</h2>
```

### リスト記法
```
- 項目1
- 項目2
  - サブ項目1
  - サブ項目2

1. 順序リスト1
2. 順序リスト2
```

---

## 🔧 開発・カスタマイズ

### 品質チェック
```bash
make lint       # コード品質チェック
make test       # テスト実行
make test-unit  # 高速単体テスト
```

### 設定カスタマイズ
```python
from kumihan_formatter.unified_api import KumihanFormatter

formatter = KumihanFormatter()
formatter.config.set_template('modern')  # テンプレート切り替え
result = formatter.convert_text(content)
```

---

## Deprecation Notice (Phase 1 until 2025-09-15)
- The compatibility classes `DummyParser` / `DummyRenderer` in `kumihan_formatter.unified_api` are deprecated.
- Instantiate them only if you must; they now emit DeprecationWarning.
- Migrate to:
  - `KumihanFormatter().parse_text(text)` instead of `DummyParser().parse(text)`
  - `KumihanFormatter().convert_text(text)` instead of `DummyRenderer().render(node, ctx)`

## 📚 さらに詳しく

- **統合API詳細**: API.md
- **アーキテクチャ**: ARCHITECTURE.md
- **開発ガイド**: AGENTS.md（Codex運用）
- **変更履歴**: CHANGELOG.md
- **移行ガイド**: docs/DEPRECATION_MIGRATION.md
