# ファイル配置ガイドライン

> Kumihan-Formatter プロジェクトのファイル配置ルールと整理方針

## 🎯 基本方針

このプロジェクトでは、コードの可読性と保守性を向上させるため、厳格なファイル配置ルールを採用しています。

## 📁 ディレクトリ構造

```
Kumihan-Formatter/
├── kumihan_formatter/          # メインアプリケーションコード
│   ├── core/                   # コア機能
│   ├── commands/               # CLIコマンド
│   └── utils/                  # ユーティリティ
├── tests/                      # テストスイート
│   ├── unit/                   # ユニットテスト
│   ├── integration/            # 統合テスト
│   └── performance/            # パフォーマンステスト
├── scripts/                    # 開発・運用スクリプト
├── docs/                       # ドキュメント
│   ├── dev/                    # 開発者向け
│   ├── user/                   # ユーザー向け
│   └── specs/                  # 仕様書
├── tmp/                        # 一時ファイル（必須）
├── examples/                   # 使用例・サンプル
└── tools/                      # 開発ツール
```

## 🚨 tmp/配下強制出力ルール（絶対遵守）

### 基本原則

**全ての一時出力ファイルは必ずtmp/配下に出力すること**

### 適用対象

以下のファイルは例外なくtmp/配下に配置：

- ✅ ログファイル（*.log）
- ✅ デバッグ出力ファイル
- ✅ 変換結果ファイル（一時的なもの）
- ✅ テスト実行結果ファイル
- ✅ 設定・キャッシュファイル（一時的なもの）
- ✅ プロファイリング結果
- ✅ レポート・統計ファイル（一時的なもの）

### 実装パターン

#### ✅ 正しい実装

```python
from pathlib import Path

# tmp/ディレクトリの作成・使用
tmp_dir = Path("tmp")
tmp_dir.mkdir(exist_ok=True)

# 出力ファイルパス
output_file = tmp_dir / "performance_metrics.json"
log_file = tmp_dir / "debug.log"
result_file = tmp_dir / f"test_results_{timestamp}.json"

# ファイル書き込み
with open(output_file, "w") as f:
    json.dump(data, f)
```

#### ❌ 間違った実装

```python
# プロジェクトルート直下への出力（禁止）
output_file = "performance_metrics.json"
log_file = "debug.log"

# 他ディレクトリへの出力（禁止）
output_file = "output/results.json"
log_file = "logs/debug.log"
```

### 違反検出・修正

```bash
# 違反チェック
make check-tmp-rule

# 自動修正
make enforce-tmp-rule

# 手動確認
python scripts/cleanup.py --check-tmp-rule
```

## 📋 ファイル分類ルール

### コード関連

| 種類 | 配置場所 | 例 |
|------|----------|-----|
| メインコード | `kumihan_formatter/` | 変換エンジン、パーサー |
| テストコード | `tests/` | ユニット・統合・性能テスト |
| スクリプト | `scripts/` | 開発・デプロイスクリプト |
| ツール | `tools/` | 開発支援ツール |

### ドキュメント関連

| 種類 | 配置場所 | 例 |
|------|----------|-----|
| 仕様書 | `docs/specs/` | 記法仕様、機能仕様 |
| 開発ドキュメント | `docs/dev/` | アーキテクチャ、コーディング規約 |
| ユーザードキュメント | `docs/user/` | ユーザーガイド、チュートリアル |
| プロジェクト文書 | プロジェクトルート | README、LICENSE、CHANGELOG |

### 一時・出力ファイル

| 種類 | 配置場所 | 例 |
|------|----------|-----|
| 一時ファイル | `tmp/` | ログ、キャッシュ、テスト結果 |
| サンプル・例 | `examples/` | 使用例、サンプルファイル |

## 🛡️ 禁止事項

### ❌ 絶対に禁止

1. **プロジェクトルート汚染**
   - 一時ファイルのルート直下作成
   - テスト結果ファイルの散乱
   - デバッグ出力の放置

2. **不適切なディレクトリ作成**
   - `output/`, `temp/`, `cache/` の独自作成
   - 日本語ディレクトリ名
   - 目的不明なディレクトリ

3. **ファイル命名違反**
   - 日本語ファイル名
   - 空白を含むファイル名
   - 拡張子なしの実行ファイル

## 🔧 自動管理システム

### ツール一覧

```bash
# ファイル整理
make organize                  # 対話的整理
make organize-auto            # 自動整理
make scan-files              # スキャンのみ

# クリーンアップ
make cleanup-preview         # 削除対象プレビュー
make cleanup-interactive     # 対話的削除
make deep-clean             # 完全自動削除

# tmp/ルール管理
make check-tmp-rule         # 違反チェック
make enforce-tmp-rule       # 違反修正

# 重複ファイル処理
make find-duplicates        # 重複検出
```

### 設定ファイル

- **`.cleanup.yml`**: クリーンアップ設定
- **`.gitignore`**: Git除外パターン
- **`Makefile`**: ショートカットタスク

## 📊 品質管理

### 継続的チェック

1. **開発時チェック**
   - pre-commitフックでファイル配置確認
   - tmp/ルール違反の自動検出

2. **定期チェック**
   - 週次ファイル整理の自動実行
   - 不要ファイル検出・削除提案

### メトリクス

- プロジェクトルート直下のファイル数
- tmp/配下ファイル総サイズ
- 重複ファイル数・無駄容量
- ファイル分類精度

## 🚀 ベストプラクティス

### 開発時の心がけ

1. **一時ファイル作成時**
   ```python
   # 常にtmp/配下を使用
   tmp_dir = Path("tmp")
   tmp_dir.mkdir(exist_ok=True)
   file_path = tmp_dir / "your_file.ext"
   ```

2. **新機能開発時**
   - 適切なディレクトリ配置を設計
   - 一時ファイル出力箇所の確認
   - テスト時のファイル配置検証

3. **レビュー時**
   - ファイル配置ルール準拠確認
   - tmp/配下出力の徹底確認
   - 不要ファイル作成の防止

### トラブルシューティング

```bash
# プロジェクト構造確認
tree -I '.venv*|__pycache__'

# 不要ファイル検出
python scripts/cleanup.py --dry-run

# ファイル分類状況確認
python scripts/file-organizer.py --scan
```

## 📚 関連ドキュメント

- [CLAUDE.md](../../CLAUDE.md) - プロジェクト開発指針
- [アーキテクチャ](architecture.md) - システム設計
- [コーディング規約](coding-standards.md) - コード品質基準

---

**重要**: このガイドラインは、プロジェクトの品質と保守性を保つための必須ルールです。例外は認められません。疑問がある場合は、必ず確認してから実装してください。