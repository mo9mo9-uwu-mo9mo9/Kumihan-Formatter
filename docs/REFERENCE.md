# Claude Code リファレンス

> Kumihan-Formatter をClaude Codeで効率的に扱うためのリファレンス

## 📋 ファイル構造（Claude Code最適化済み）

```
Kumihan-Formatter/
├── README.md                    # プロジェクト概要
├── CLAUDE.md                    # Claude Code指示ファイル（最重要）
├── CONTRIBUTING.md              # 開発プロセス
├── CHANGELOG.md                 # 変更履歴
├── Makefile                     # 開発コマンド
└── docs/                        # ドキュメント集
    ├── REFERENCE.md             # 本ファイル（Claude Code用）
    ├── ARCHITECTURE.md          # システム全体仕様
    ├── DEVELOPMENT_GUIDE.md     # 開発ガイド（統合版）
    ├── USER_GUIDE.md            # ユーザーガイド（統合版）
    ├── DEPLOYMENT.md            # 配布・運用ガイド（統合版）
    └── specifications/          # 詳細仕様書
        ├── NOTATION_SPEC.md     # 記法仕様詳細
        ├── FUNCTIONAL_SPEC.md   # 機能仕様
        └── ERROR_MESSAGES_SPEC.md # エラーメッセージ仕様
```

## 🎯 Claude Code推奨ワークフロー

### 1. プロジェクト理解フェーズ
1. **CLAUDE.md** - AI運用原則・基本設定を把握
2. **README.md** - プロジェクト全体像を把握
3. **docs/ARCHITECTURE.md** - システム構造・技術仕様を理解

### 2. 開発作業フェーズ
1. **docs/DEVELOPMENT_GUIDE.md** - 開発環境・プロセスを確認
2. **CONTRIBUTING.md** - 具体的な作業手順を確認
3. **Makefile** - 利用可能コマンドを確認

### 3. ユーザー視点フェーズ
1. **docs/USER_GUIDE.md** - エンドユーザー向け機能を理解
2. **docs/DEPLOYMENT.md** - 配布・運用方法を理解

## 🚀 よく使うClaude Codeパターン

### プロジェクト初回理解
```
1. CLAUDE.md → 基本方針理解
2. README.md → 概要把握
3. docs/ARCHITECTURE.md → 詳細理解
```

### 機能追加・修正
```
1. CLAUDE.md → 作業原則確認
2. CONTRIBUTING.md → 作業手順確認
3. docs/DEVELOPMENT_GUIDE.md → 開発詳細確認
4. 実装作業
5. Makefile → lint実行
```

### バグ調査・修正
```
1. docs/ARCHITECTURE.md → システム構造理解
2. ソースコード調査
3. docs/USER_GUIDE.md → 期待動作確認
4. 修正・テスト
```

## 📖 ファイル別詳細ガイド

### 🔥 CLAUDE.md（最重要）
- **内容**: AI運用7原則、基本設定、コマンド一覧
- **Claude Code用途**: 全作業の基本方針
- **参照タイミング**: 必ず最初に読む

### 📋 README.md
- **内容**: プロジェクト概要、クイックスタート
- **Claude Code用途**: プロジェクト全体像の把握
- **参照タイミング**: プロジェクト理解時

### 🏗️ docs/ARCHITECTURE.md
- **内容**: システム全体仕様、記法詳細、クラス構造
- **Claude Code用途**: 技術的詳細の理解
- **参照タイミング**: 実装・修正作業時

### 👨‍💻 docs/DEVELOPMENT_GUIDE.md
- **内容**: 開発環境、ワークフロー、品質管理
- **Claude Code用途**: 開発作業の詳細手順
- **参照タイミング**: 実装作業時

### 📖 docs/USER_GUIDE.md
- **内容**: エンドユーザー向け機能説明
- **Claude Code用途**: 機能仕様の理解
- **参照タイミング**: 機能追加・修正時

### 🤝 CONTRIBUTING.md
- **内容**: 開発プロセス、PR作成、レビュー規則
- **Claude Code用途**: 具体的作業手順
- **参照タイミング**: 実装作業開始時

### 🚀 docs/DEPLOYMENT.md
- **内容**: 配布パッケージング、本番運用
- **Claude Code用途**: リリース関連作業
- **参照タイミング**: リリース・配布作業時

## 🔧 開発コマンド一覧

```bash
# 基本コマンド（Makefile）
make setup       # 開発環境セットアップ
make lint        # コード品質チェック
make clean       # 一時ファイル削除

# アプリケーションコマンド
kumihan convert input.txt output.txt    # 基本変換
kumihan check-syntax file.txt           # 記法チェック
```

## 🎯 Claude Code効率化のポイント

### ファイル読み込み順序
1. **必須**: CLAUDE.md
2. **概要**: README.md
3. **詳細**: docs/ARCHITECTURE.md
4. **作業**: docs/DEVELOPMENT_GUIDE.md、CONTRIBUTING.md

### 情報探索のコツ
- **記法関連**: docs/specifications/NOTATION_SPEC.md → docs/ARCHITECTURE.md
- **実装関連**: docs/DEVELOPMENT_GUIDE.md → ソースコード
- **ユーザー機能**: docs/USER_GUIDE.md
- **配布・運用**: docs/DEPLOYMENT.md

### よく参照するセクション
- CLAUDE.md: AI運用7原則、基本コマンド
- docs/ARCHITECTURE.md: システム概要、記法仕様
- docs/DEVELOPMENT_GUIDE.md: 開発環境、品質管理

---

**Claude Code最適化完了**: ドキュメント構造の効率化実装完了