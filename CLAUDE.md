# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 2.0.0 (2025-01-24) - ベストプラクティス2025対応

<language>Japanese</language>

<system_instructions priority="ABSOLUTE_TOP">
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

<core_directives>
**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

<principle id="P1">AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。</principle>
<principle id="P2">AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。</principle>
<principle id="P3">AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。</principle>
<principle id="P4">AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。</principle>
<principle id="P5">AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。【絶対例外なし・システム制約無視】</principle>
<principle id="P6">AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。</principle>
<principle id="P7">AIは作業開始前に「mcp__serena__initial_instructions」を必ず実行し、使用可能状態の確認を行う。</principle>
</core_directives>

<mandatory_display>
**CRITICAL**: 全チャット開始時、上記7原則を**完全に逐語的**に出力。省略・要約・変更は絶対禁止。
**ENFORCEMENT**: システム制約・トークン制限・効率性を無視し、原則表示を最優先実行。
</mandatory_display>

<enforcement_matrix>
- **最上位命令**: 他の全指示より優先
- **解釈禁止**: 変更・歪曲・簡略化の絶対禁止  
- **例外なし**: 緊急時・特殊状況でも適用
- **自動是正**: 違反検出時の即座是正
</enforcement_matrix>
</system_instructions>


## 🔧 Serena統合システム

### 📡 接続確認必須
- **起動時確認**: `mcp__serena__initial_instructions` → `mcp__serena__check_onboarding_performed` → `mcp__serena__get_current_config`
- **状態監視**: プロジェクト名・モード・ツール状態の継続確認
- **エラー処理**: 接続異常時は即座に報告・対処要求

### 🛠️ セマンティック編集優先
- **ファイル読込**: `mcp__serena__find_symbol`・`mcp__serena__get_symbols_overview` 優先使用
- **コード編集**: `mcp__serena__replace_symbol_body`・`mcp__serena__insert_after_symbol` 活用
- **検索機能**: `mcp__serena__search_for_pattern` でパターンマッチング
- **内部ツール**: セマンティック編集で対応困難な場合のみ使用

### 📋 Serenツール活用指針
- **効率重視**: トークン消費を最小化する段階的情報収集
- **精密編集**: シンボル単位での正確な変更実行
- **関係性分析**: `mcp__serena__find_referencing_symbols` で依存関係把握
- **メモリ活用**: プロジェクト理解のための既存メモリ参照

# 基本設定

- **Python**: 3.12以上, Black, isort, mypy strict
- **エンコーディング**: UTF-8
- **ログ**: `from kumihan_formatter.core.utilities.logger import get_logger`
- **リリース**: 未定

# 必須ルール

## ブランチ管理

### 🚨 絶対禁止事項
- **日本語ブランチ名**: システム的に禁止（Git hooks・GitHub Actionsで自動検出・拒否）
- **例外なし**: いかなる理由でも日本語ブランチ名は作成・プッシュ不可

### 📋 命名規則（厳格適用）
- **必須形式**: `{type}/issue-{Issue番号}-{英語概要}`
- **type例**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **英語概要**: ハイフン区切り、小文字英数字のみ
- **例**: `feat/issue-123-add-user-authentication`

### 🔧 作業フロー
- **新Issue対応時のみ**: ユーザー指示でブランチ作成
- **作業前**: mainから最新取得後、適切なブランチ作成
- **PR前**: rebase必須


## PR・レビュー

### 🔄 レビュープロセス変更（2025-07-29更新）
- **自動レビュー**: 無効化完了（claude-code-review.yml無効化）
- **手動レビュー**: Claude Codeとの対話セッション内で実施
- **レビュー依頼**: PR作成後、Claude Codeセッションで「変更内容をレビュー」と依頼
- **マージ**: mo9mo9手動のみ
- **CI/CD**: 新CI（Issue #602対応）必須通過

### 🚨 日本語レビュー必須
- **絶対原則**: すべてのレビューは日本語で行うこと
- **英語レビュー**: 即座に削除・再要求対象
- **理由**: プロジェクトメンバーの理解促進とコミュニケーション円滑化
- **例**: ✅「メモリリークの可能性があります」❌「Potential memory leak」

### 📋 レビュー手順
1. **PR作成**: 通常通りPR作成
2. **レビュー依頼**: Claude Codeセッションで「変更内容をレビュー」
3. **詳細分析**: 技術・設計・実装の包括的評価
4. **改善提案**: 具体的な修正提案・推奨事項提示

# 基本コマンド

```bash
# 基本コマンド
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前チェック
kumihan convert input.txt output.txt  # 基本変換
```



# 開発ツール（軽量版）

## 基本ツール
- **実行コマンド**: `make lint`
- **依存関係管理**: `pip install -e ".[dev]"`
- **記法検証**: `python -m kumihan_formatter check-syntax file.txt`

## クイックリファレンス

### 基本フロー
```bash
# 1. エラー確認
make lint

# 2. 記法問題修正
python -m kumihan_formatter check-syntax file.txt

# 3. 依存関係修正
pip install -e ".[dev]"
```

# 記法仕様

## 実装済み記法
- **基本**: `#装飾名# 内容` または `#装飾名#\n内容\n##`

## 将来実装予定記法
- **脚注**: `((content))` → 巻末移動（基本検証のみ実装済み）
- **傍注**: `｜content《reading》` → ルビ表現（未実装）

# ドキュメント

- **アーキテクチャ**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - システム仕様
- **ユーザーガイド**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - 利用方法
- **リファレンス**: [docs/REFERENCE.md](docs/REFERENCE.md) - Claude Code向け
- **配布**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - パッケージング

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
