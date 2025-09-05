# Kumihan-Formatter

![Status](https://img.shields.io/badge/status-Development-orange.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

> CoC6th同人シナリオなどのテキストファイルを、**ワンコマンドで美しいHTML**に変換する日本語ツール

**⚠️ 現在のステータス**: 開発中 (Development) - 統合最適化完了 (2025年版アーキテクチャ)

**🇯🇵 言語サポート**: 本ツールは**日本語専用**です。英語やその他の言語への対応予定はありません。

### 🏆 最新アップデート (2025年版)
- **パーサー統合完了**: 統合パーサーシステム構築 (unified_api.py)
- **アーキテクチャ最適化**: ディレクトリ構造最適化 (14層モジュール構造)
- **統合API**: `KumihanFormatter`による統一エントリーポイント
- **Manager統合**: 5つの統合Managerシステム構築
- **テスト強化**: 17テストファイル、品質保証体制構築

## ✨ 特徴

- **🎯 直感的な改行処理** - 改行したら、そのまま改行される
- **🎨 プロ品質の出力** - 美しい組版、A4印刷対応
- **📱 クロスプラットフォーム** - Windows・macOS対応

## 🚀 クイックスタート

**CLIツール**:
```bash
# 開発環境セットアップ
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 開発環境セットアップ（ローカル）
make setup

# 開発用CLI使用例（サブコマンドなし）
kumihan input.txt [output.html]
# または
python -m kumihan_formatter input.txt [output.html]

# 開発ログの有効化（任意）
KUMIHAN_DEV_LOG=true kumihan input.txt

# 品質チェック（pyproject準拠のmypy strict）
make lint
```

### 🌟 開発参加者向け重要事項

**ブランチ命名規則**（厳格適用）:
```bash
# ✅ 正しいブランチ名
feat/issue-123-add-user-authentication
fix/issue-456-fix-parsing-error
docs/issue-789-update-readme

# ❌ 禁止（システム的に拒否される）
feat/issue-123-ユーザー認証追加  # 日本語禁止
feature-branch                    # Issue番号なし
```

**システム的制約**:
- 日本語ブランチ名は禁止（運用ルールで厳守）
- **一時ファイル出力は `tmp/` 配下必須** - プロジェクトルート直下への出力は禁止
- 詳細は [AGENTS.md](./AGENTS.md) を参照（CLAUDE.md は廃止）

### 🚀 初回セットアップガイド

開発環境の初回セットアップは以下の順序で実行してください：

```bash
# 1. リポジトリクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# 2. 依存関係インストール
make setup

# 3. Git hooks インストール（重要！）
./scripts/install-hooks.sh

# 4. 動作確認
make lint
```

**⚠️ 重要**: `./scripts/install-hooks.sh` を実行しないと、日本語ブランチ名でのプッシュ時にローカルでエラーが発生しません。GitHub Actions でのみ検出されるため、必ず実行してください。

## ⚙️ オプション依存関係

Kumihan-Formatterでは、特定機能を利用する際に追加パッケージのインストールが必要です：

### 📊 パフォーマンス監視機能
```bash
# メモリ使用量追跡機能を利用する場合
pip install "kumihan-formatter[performance]"

# または個別インストール
pip install psutil>=5.9
```

**利用可能な機能**:
- リアルタイムメモリ使用量表示
- プログレスバーでのメモリ統計
- パフォーマンス監視レポート

**対応コマンド**:
```bash
# メモリ監視付き変換（psutil必須）
kumihan convert input.txt --progress-level verbose

# プログレスログ出力（メモリ統計含む）
kumihan convert input.txt --progress-log progress.json
```

## 💡 基本的な記法（α-dev）

```
#見出し1#
シナリオタイトル
##

このシナリオは...

#太字#
重要な情報
##

#ハイライト color=yellow#
注目すべきポイント
##

#目次#
##
```

→ **プロ品質のHTML出力**

**⚠️ 重要変更**: α-devから全記法がブロック形式に統一され、単一行記法は完全廃止されました。

## 📁 プロジェクト構造

```
Kumihan-Formatter/
├── kumihan_formatter/   # メインパッケージ
├── tests/               # テスト
├── scripts/             # ユーティリティスクリプト
├── examples/            # 使用例
├── output/              # 出力（gitignore対象）
├── tmp/                 # 一時生成物（git管理外）
├── AGENTS.md            # コントリビュータ向けガイド
├── README.md            # 本ファイル
├── CONTRIBUTING.md      # 貢献ガイド
├── ARCHITECTURE.md      # 概要アーキテクチャ
├── API.md               # APIの概要
├── API_GUIDELINES.md    # API設計方針
└── pyproject.toml       # プロジェクト設定
```

## Deprecation Notice: DummyParser/DummyRenderer（Phase 1: 〜2025-09-15）
- `kumihan_formatter.unified_api.DummyParser` / `DummyRenderer` は非推奨です（実行時に DeprecationWarning を出力）。
- Phase 2（〜2025-10-15）ではトップレベル再エクスポートを停止済み、直接インポートへ移行してください。
- Phase 3（〜2025-11-30）でレガシーAPIの削除を段階的に進めます。詳細と移行手順は [Deprecation Migration Guide](./docs/DEPRECATION_MIGRATION.md) を参照。
- Migration examples:
  - Before: `DummyParser().parse(text)` → After: `KumihanFormatter().parse_text(text)`
  - Before: `DummyRenderer().render(node, ctx)` → After: `KumihanFormatter().convert_text(text)`

## 📖 ドキュメント

### クイックリファレンス（存在するもののみ）
- [QUICKSTART.md](./QUICKSTART.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [API.md](./API.md)
- [API_GUIDELINES.md](./API_GUIDELINES.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [AGENTS.md](./AGENTS.md)
- [CHANGELOG.md](./CHANGELOG.md)
- [Deprecation Migration Guide](./docs/DEPRECATION_MIGRATION.md)

## 🔧 開発者向け機能

### デバッグ
CLIはサブコマンド無しのシンプル構成です（convert等は未提供）。

```bash
# 基本形式（サブコマンドなし）
kumihan input.txt [output.html]
```

### 環境変数（開発・実験）
- `KUMIHAN_DEV_WARNINGS=1`:
  - `parser` など一部モジュールの統合完了メッセージ（UserWarning）を有効化します（既定は非表示）。
- `KUMIHAN_COMPAT_WARNINGS=1`:
  - 互換レイヤ（compatibility_layer）利用時のDeprecationWarningを有効化します（既定は非表示）。
- `KUMIHAN_RAISE_KUMIHAN_ERRORS=1`:
  - I/O層の一部で、標準例外を `KumihanFileError` へラップして送出します（既定は従来どおり標準例外）。

- `KUMIHAN_PROFILE=conservative|aggressive`:
  - 実行時プロファイル（非機能要件のチューニング）を切り替えます。デフォルトは未設定（従来挙動）。
    - `conservative`: `large_parse_chunk_size=600`、`performance_monitoring=false`
    - `aggressive`: `large_parse_chunk_size=2000`、`performance_monitoring=true`
  - いずれのプロファイルも公開APIや出力仕様は変更しません（内部最適化のみ）。


## 🤝 サポート

- **バグ報告・機能要望**: [Issues](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/issues)
- **使い方相談**: [Discussions](https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/discussions)
- **開発に参加**: [Contributing Guide](CONTRIBUTING.md)

### 🚨 コードレビュー規則
**重要**: このプロジェクトでは **日本語でのレビューを義務付け** しています。
- ✅ すべてのPRレビューは日本語で行ってください
- ❌ 英語でのレビューは受け付けません
- 詳細: [CONTRIBUTING.md](CONTRIBUTING.md#-日本語レビュー必須規則)

## 📄 ライセンス

Proprietary License - Copyright © 2025 mo9mo9-uwu-mo9mo9
All rights reserved.
