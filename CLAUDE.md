# CLAUDE.md

> **Kumihan-Formatter** - Claude Code プロジェクト設定ファイル  
> **Status**: Development - 2025年版最適化済み

---

## 🎯 プロジェクト概要

- **言語**: 日本語メインプロジェクト
- **技術スタック**: Python 3.12+, Black, isort, mypy (strict)
- **記法**: Kumihan独自ブロック記法 (`# 装飾名 #内容##`)

## 📋 開発原則

### コア原則
1. **作業計画の事前報告**: ファイル変更・実行前に必ず計画を報告
2. **ユーザー主導**: AIは提案のみ、決定権はユーザーが保持
3. **指示の厳格遵守**: 非効率でもユーザー指示を最優先
4. **透明性の確保**: 全作業プロセスを明確に報告
5. **🤖 Gemini協業優先**: Token節約・コスト効率化のため積極活用

### 基本ルール
- **一時ファイル**: 全て `tmp/` 配下に出力（絶対遵守）
- **日本語使用**: コメント・レビュー・ドキュメントは日本語
- **ログ使用**: `from kumihan_formatter.core.utilities.logger import get_logger`

### 🤖 Gemini協業指針
- **モデル**: gemini-2.5-flash（コスト最適化）
- **Token節約**: 90%以上目標
- **トリガー**: 「Geminiと協業」「Gemini協業」「一緒に」等
- **責任分担**: Claude(設計・品質) / Gemini(実装)

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

### テスト・品質管理
```bash
make lint       # Black, isort, flake8, mypy
make test       # pytest
```

---

## 👑 Claude-Gemini 直接協業体制

> **Claude(PM/Manager) - Gemini(Coder)** - 90%Token削減目標

### 責任分担
- **Claude**: 要件分析・設計・品質レビュー・最終責任
- **Gemini**: Task tool指示実行・実装作業・コード修正

### Token節約戦略
- **モデル選択**: gemini-2.5-flash使用
- **シンプル実行**: Task tool 1回呼び出しで完了  
- **品質維持**: Claude最終責任で品質保証

### 協業フロー
1. ユーザー要求 → 2. Claude指示書作成 → 3. Gemini実装 → 4. Claude品質レビュー → 5. 完成

---

## 🛡️ 品質保証システム（3層検証体制）

### Layer 1: 構文検証（自動）
- AST解析による構文エラー検出、型注釈パターン自動修正

### Layer 2: 品質検証（自動）
```bash
make lint        # Black, isort, flake8 通過必須
make test        # 既存テスト全通過必須
```

### Layer 3: Claude最終承認（手動）
- **コードレビュー**: Gemini成果物の詳細確認・品質責任
- **統合確認**: 全体システムとの整合性検証

### フェイルセーフ機能
- Gemini実行失敗時: Claude代替実行
- 品質基準未達時: 追加修正指示

---

## 🤖 Gemini協業最適化システム

### タスク難易度自動判定

#### 🟢 SIMPLE (Gemini推奨)  
- **対象**: 設定ファイル、テンプレート、ドキュメント
- **成功率**: 90%以上

#### 🟡 MODERATE (分割検討)  
- **対象**: ビジネスロジック、API統合、テスト実装
- **戦略**: 2ファイル以下に分割してGemini適用

#### 🔴 COMPLEX (Claude必須)
- **対象**: メモリ管理、セキュリティ、並行処理、最適化
- **必須**: Claude直接実装

### 自動判定ルール
```python
CLAUDE_REQUIRED = ["memory", "security", "parallel", "async", "optimization"]
GEMINI_SUITABLE = [".yaml", ".json", ".md", ".html", "config", "template"]
```

### 協業実績 (Issue #922 Phase 4完了)
- **Token節約**: 約7,500 tokens
- **成功率**: 80% (4/5フェーズ)
- **時間効率**: 平均50%短縮

---

## 📝 コーディング標準

### Python コードスタイル
- **フォーマット**: Black (line-length=88)
- **インポート**: isort設定に従う
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
- ❌ **Gemini品質基準未達成でのマージ**（3層検証必須）

### 必須事項
- ✅ 作業前の計画報告
- ✅ tmp/ 配下での一時ファイル管理
- ✅ 品質チェック（lint/typecheck）の実行
- ✅ **🤖 Gemini協業の明示実行**（「Geminiと一緒に」等で自動起動）
- ✅ **3層品質検証**: 構文→品質→Claude最終承認
- ✅ **Token節約1000以上時Gemini検討**（コスト効率優先）

### 🤖 Gemini協業時の特別注意事項
- **品質責任**: Gemini成果物でもClaude最終責任
- **シンプル実行**: Task toolによる直接指示で確実性重視

---

## 🚀 品質保証コマンド

```bash
make claude-check            # CLAUDE.mdサイズ・構造チェック
make lint                   # Black, isort, flake8, mypy
make test                   # pytest全テスト実行
make gemini-quality-check   # 3フェーズ統合品質チェック
```

---

*🎯 Claude Code最適化済み - Issue #920改善対応版*