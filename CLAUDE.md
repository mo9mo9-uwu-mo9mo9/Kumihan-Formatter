# CLAUDE.md

> **Kumihan-Formatter** - Claude Code プロジェクト設定ファイル  
> **Status**: Development - 2025年版最適化済み

---

## 🎯 プロジェクト概要

- **言語**: 日本語メインプロジェクト
- **技術スタック**: Python 3.12+, Black, isort, mypy (strict)
- **エンコーディング**: UTF-8
- **記法**: Kumihan独自ブロック記法 (`# 装飾名 #内容##`)

## 📋 開発原則

### コア原則
1. **作業計画の事前報告**: ファイル変更・実行前に必ず計画を報告
2. **ユーザー主導**: AIは提案のみ、決定権はユーザーが保持
3. **指示の厳格遵守**: 非効率でもユーザー指示を最優先
4. **透明性の確保**: 全作業プロセスを明確に報告
5. **🤖 Gemini協業優先**: Token節約・コスト効率化のため積極活用

### 基本ルール
- **新規Issue対応時のみ**: 適切なブランチ作成・切り替え実施
- **一時ファイル**: 全て `tmp/` 配下に出力（絶対遵守）
- **日本語使用**: コメント・レビュー・ドキュメントは日本語
- **ログ使用**: `from kumihan_formatter.core.utilities.logger import get_logger`
### 🤖 Gemini協業指針
- **モデル**: gemini-2.5-flash（コスト最適化）
- **Token節約**: 90%以上目標
- **トリガー**: 「Geminiと協業」「Gemini協業」「一緒に」等
- **協業パターン**: SIMPLE（lint/型）、MODERATE（機能追加）、COMPLEX（アーキテクチャ）
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
# Issue作成（ラベル必須）
gh issue create --title "タイトル" --body "内容" \
  --label "バグ,優先度:高,難易度:普通,コンポーネント:パーサー"

# PR作成
gh pr create --title "タイトル" --body "詳細説明"
```

### テスト・品質管理
```bash
make lint       # Black, isort, flake8, mypy
make test       # pytest
```

#### 品質管理基盤 (Issue #831対応済み)
- **設定統一**: pre-commit ↔ mypy 完全統一（pyproject.toml基準）
- **現状**: 73件エラー（段階的解決計画策定済み）
- **後続対応**: Issue #832(unreachable), #833(return-value)で段階的改善

---

## 👑 Claude-Gemini 直接協業体制

> **Claude(PM/Manager) - Gemini(Coder)** - シンプルで確実な90%Token削減

### Claude(PM/Manager)責任範囲
- **📋 要件分析・設計**: ユーザー要求の分析・アーキテクチャ設計・詳細作業指示書作成
- **👀 監督・レビュー**: Gemini成果物の品質チェック・最終調整・品質責任
- **👥 コミュニケーション**: ユーザー対話・意思決定・問題解決

### Gemini(Coder)責任範囲
- **👤 指示実行**: Task toolを通じて受け取る作業指示書の忠実な実行
- **⚡ 実装作業**: コード修正・型注釈・バグ修正・コード整形・テスト実行
- **🚫 判断禁止**: 独自判断・仕様変更・品質基準の変更は禁止

### 💰 Token節約戦略（目標: 90%削減）
- **モデル選択**: gemini-2.5-flash使用でコスト最適化
- **シンプル実行**: Task tool 1回呼び出しで完了
- **コスト効率**: 複雑なシステム不要で真のコスト削減
- **品質維持**: Claude最終責任で品質保証

### 📋 協業フロー
1. ユーザー要求 → 2. Claude要件分析・指示書作成 → 3. Gemini実装 
→ 4. Claude品質レビュー → 5. 完成

---

## 🛡️ 品質保証システム（3層検証体制）

### Layer 1: 構文検証（自動）
- AST解析による構文エラー検出、型注釈パターン自動修正、禁止構文の事前検証

### Layer 2: 品質検証（自動）
```bash
make lint        # Black, isort, flake8 通過必須
make mypy        # strict mode 通過必須  
make test        # 既存テスト全通過必須
```

### Layer 3: Claude最終承認（手動）
- **コードレビュー**: Gemini成果物の詳細確認
- **品質責任**: 最終的な品質保証・承認
- **統合確認**: 全体システムとの整合性検証

### 🔄 フェイルセーフ機能
- Gemini実行失敗時: 自動的にClaude代替実行
- 品質基準未達時: 自動的な追加修正指示
- エラー時: 詳細ログ記録・学習データ化

### 📊 品質監視
- **コード品質**: `make lint` / `make test` で確認
- **品質履歴追跡**: Git履歴による改善トレンド分析
- **コスト・品質バランス**: シンプルな直接協業によるROI最適化

---

## 📝 コーディング標準

### Python コードスタイル
- **フォーマット**: Black (line-length=88)
- **インポート**: isort設定に従う
- **型注釈**: mypy strict mode必須
- **ログ**: プロジェクト標準ロガー使用

### ファイル出力・エラーハンドリング
- **出力**: 必ず`tmp/`配下に保存（`os.makedirs("tmp", exist_ok=True)`）
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **例外**: try-except-raiseパターンでログ記録

---

## 🎨 Kumihan記法仕様

### 基本記法
- **ブロック記法**: `# 装飾名 #内容##` （太字・イタリック・見出し等）
- **構造要素**: 見出し・リスト・目次・リンク対応
- **詳細仕様**: [記法完全仕様](docs/specs/notation.md)

---

## 📊 プロジェクト構造

### 主要コンポーネント
- **パーサー**: `core/` - 記法解析エンジン（block_parser, utilities含む）
- **レンダラー**: `core/rendering/` - HTML出力・テンプレート処理
- **CLI**: `cli.py + commands/` - コマンドライン interface  
- **設定**: `config/` - 設定管理・品質基準

---

## 🔍 品質・性能指標

### サイズ管理
- **推奨**: 150行/8KB以下 | **警告**: 200行/10KB | **限界**: 250行/12KB
- **監視**: `make claude-check`

### ドキュメント
- [Gemini協業テンプレート](docs/claude/) | [アーキテクチャ](docs/dev/architecture.md)
- [記法仕様](docs/specs/notation.md) | [利用ガイド](docs/user/user-guide.md)

---

## ⚙️ 重要な実行時注意事項

### 禁止事項
- ❌ 日本語ブランチ名（システム的に拒否）
- ❌ プロジェクトルート直下への一時ファイル出力
- ❌ 英語でのレビュー・コメント
- ❌ 未承認でのファイル作成・変更
- ❌ **`python`コマンド使用**（必ず`python3`を使用）
- ❌ **Gemini品質基準未達成でのマージ**（3層検証必須）

### 必須事項
- ✅ 作業前の計画報告
- ✅ tmp/ 配下での一時ファイル管理
- ✅ 適切なラベル付きIssue作成
- ✅ 品質チェック（lint/typecheck）の実行
- ✅ **🤖 Gemini協業の明示実行**（「Geminiと一緒に」等の協業表現で自動起動）
- ✅ **3層品質検証**: 構文→品質→Claude最終承認
- ✅ **Token節約1000以上時Gemini検討**（コスト効率優先）

### 🤖 Gemini協業時の特別注意事項
- **品質責任**: Gemini成果物でもClaude最終責任
- **シンプル実行**: Task toolによる直接指示で確実性重視
- **継続改善**: 結果蓄積・学習データ化・品質向上

---

## 🚀 Gemini協業品質保証（Issue #920改善）

### 📋 協業フロー統合
1. **開始前**: `docs/claude/gemini_instruction_template.md`で指示書作成
2. **実行中**: 33%/66%/100%時点で`make lint`/`make test`実行
3. **完了後**: `make gemini-quality-check`で統合品質確認

### ✅ 品質基準・チェックリスト
詳細は`docs/claude/quality_checklist_template.md`参照
- lint/flake8/test: 0エラー必須
- API互換性・セキュリティ: 維持確認
- 作業漏れ防止: 5項目チェック（機能・依存・エラー・型・ログ）

### 🔧 品質保証コマンド
```bash
make gemini-quality-check    # 3フェーズ統合品質チェック
make gemini-post-review      # 5項目総合レビュー  
make gemini-validation-full  # 3層完全検証
```

### 📊 継続改善
- 成功/失敗パターン分析・テンプレート改良・自動化推進
- Token節約50%・品質維持95%目標

---

*🎯 Claude Code最適化済み - Issue #920改善対応版*