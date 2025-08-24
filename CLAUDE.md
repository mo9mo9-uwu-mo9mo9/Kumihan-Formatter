# CLAUDE.md

> **Kumihan-Formatter** - Claude Code プロジェクト設定ファイル  
> **Status**: Development - 2025年版最適化済み

---

## 🎯 プロジェクト概要

- **言語**: 日本語メインプロジェクト
- **技術スタック**: Python 3.12+, Black, mypy (strict), pytest, Serena MCP
- **記法**: Kumihan独自ブロック記法 (`# 装飾名 #内容##`)

## 📋 開発原則

### コア原則
1. **作業計画の事前報告**: ファイル変更・実行前に必ず計画を報告
2. **ユーザー主導**: AIは提案のみ、決定権はユーザーが保持
3. **指示の厳格遵守**: 非効率でもユーザー指示を最優先
4. **透明性の確保**: 全作業プロセスを明確に報告

### 基本ルール
- **一時ファイル**: 全て `tmp/` 配下に出力（絶対遵守）
- **日本語使用**: コメント・レビュー・ドキュメントは日本語
- **ログ使用**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **効率的コード探索**: Serenaツール優先、ファイル全読み込み最小化
- **セマンティック編集**: シンボル単位での精密な編集実行

---

## 🔧 開発ワークフロー

### ブランチ管理
```bash
# 必須形式: {type}/issue-{番号}-{英語概要}
git checkout -b feat/issue-123-description
```

### Issue・PR管理
```bash
gh issue create --title "タイトル" --body "内容" --label "ラベル"
gh pr create --title "タイトル" --body "詳細説明"
```

### テスト・品質管理（シンプル版）
```bash
make lint       # Black + mypy（高速）
make test       # pytest（基本テスト）
make test-unit  # 単体テストのみ（超高速）
```

---

## 🛡️ 品質保証システム

### Layer 0: セマンティック解析（Serena MCP）
- シンボル関係性の事前検証、影響範囲の正確な特定
- 型安全性の事前確保、mypy strictモードとの統合検証
- リファクタリング前の依存関係マップ生成

### Layer 1: 構文検証（自動）
- AST解析による構文エラー検出、型注釈パターン自動修正

### Layer 2: 品質検証（自動・シンプル版）
```bash
make lint        # Black + mypy 通過必須
make test        # pytest 全通過必須
```

### Layer 3: Claude最終承認（手動）
- **コードレビュー**: 成果物の詳細確認・品質責任
- **統合確認**: 全体システムとの整合性検証

---

## 🧠 コード解析・編集ツール

### Serena MCP活用方針
- **セマンティック解析優先**: `find_symbol`, `find_referencing_symbols`による精密な検索
- **効率的探索**: ファイル全体読み込み回避、シンボル単位での対象解析
- **関係性追跡**: パーサー・レンダラー間の依存関係の正確な把握
- **型安全編集**: mypy strictモードとの連携による安全なリファクタリング

### コード探索戦略
1. **概要把握**: `get_symbols_overview` でファイル構造理解
2. **シンボル検索**: `find_symbol` で対象の特定・詳細取得
3. **影響範囲調査**: `find_referencing_symbols` で変更影響の事前確認
4. **精密編集**: `replace_symbol_body`, `insert_after_symbol` での安全な変更

### 適用場面
- **大規模リファクタリング**: パーサーエンジンの改修時
- **新機能実装**: レンダラーとパーサーの統合処理追加
- **バグ修正**: 複雑な依存関係を持つモジュール間の問題解決
- **型安全性向上**: mypy strict準拠のための段階的修正

---

## 📝 コーディング標準

### Python コードスタイル（シンプル版）
- **フォーマット**: Black (line-length=88)
- **型注釈**: mypy strict mode必須
- **ログ**: プロジェクト標準ロガー使用

### ファイル出力・エラーハンドリング
- **出力**: 必ず`tmp/`配下に保存
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`

---

## 🎨 Kumihan記法仕様

### 基本記法
- **ブロック記法**: `# 装飾名 #内容##` （太字・イタリック・見出し等）
- **構造要素**: 見出し・リスト・目次・リンク対応

---

## 📊 プロジェクト構造

### 主要コンポーネント
- **パーサー**: `core/` - 記法解析エンジン  
- **レンダラー**: `core/rendering/` - HTML出力・テンプレート処理
- **CLI**: `cli.py + commands/` - コマンドライン interface

---

## ⚙️ 重要な実行時注意事項

### 禁止事項
- ❌ 日本語ブランチ名（システム的に拒否）
- ❌ プロジェクトルート直下への一時ファイル出力
- ❌ 英語でのレビュー・コメント
- ❌ **`python`コマンド使用**（必ず`python3`を使用）

### 必須事項
- ✅ 作業前の計画報告
- ✅ tmp/ 配下での一時ファイル管理
- ✅ 品質チェック（lint/typecheck）の実行

---

## 🚀 品質保証コマンド（シンプル版）

```bash
# 基本品質チェック
make claude-check            # CLAUDE.mdサイズ・構造チェック
make lint                   # Black + mypy（高速）
make test                   # pytest全テスト実行
make test-unit              # 単体テストのみ（超高速）
```

---

*🎯 Claude Code最適化済み - シンプル版（個人開発特化）*