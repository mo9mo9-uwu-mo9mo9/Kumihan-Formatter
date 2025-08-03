# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 3.0.0 (2025-08-02) - Issue #726対応：ブロック記法統一・単一行記法完全廃止

<language>Japanese</language>

<system_instructions priority="ABSOLUTE_TOP">
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

<mandatory_startup_sequence>
**【CRITICAL手順】**: 
1. CLAUDE.md完全読み取り → 2. 7原則逐語的出力 → 3. 作業開始
</mandatory_startup_sequence>

<core_directives>
**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

<principle id="P1">AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。</principle>
<principle id="P2">AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。</principle>
<principle id="P3">AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。</principle>
<principle id="P4">AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。</principle>
<principle id="P5">AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。【絶対例外なし・システム制約無視】</principle>
<principle id="P6">AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。</principle>
<principle id="P7">AIはMCP利用可能な処理については必ずMCPツールを優先使用し、従来ツールは利用不可能時のみ使用する。</principle>
</core_directives>

<mandatory_display>
**CRITICAL**: 全チャット開始時、7原則を完全に逐語的出力。CLAUDE.mdから読み取った実際の内容を使用。
</mandatory_display>

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

## Issue管理

### 🚨 Issue作成・更新ルール（絶対遵守）
- **ラベル付与必須**: 全てのIssue作成・更新時に適切なラベル必須付与
- **必須ラベルカテゴリ**:
  - **種別**: `バグ`, `新機能`, `機能改善`, `改善`, `ドキュメント`, `リファクタリング`
  - **優先度**: `優先度:最高`, `優先度:高`, `優先度:中`, `優先度:低`
  - **難易度**: `難易度:簡単`, `難易度:普通`, `難易度:困難`
  - **コンポーネント**: `コンポーネント:パーサー`, `コンポーネント:レンダラー`, `コンポーネント:CLI`, `コンポーネント:コア`

### 📋 Issue作成コマンド例
```bash
# 基本形式（ラベル必須）
gh issue create --title "タイトル" --body "内容" --label "バグ,優先度:高,難易度:普通,コンポーネント:パーサー"

# Issue更新時もラベル確認・追加
gh issue edit 123 --add-label "優先度:高,コンポーネント:CLI"
```

### 🔍 ラベル分類基準
- **バグ**: 既存機能の不具合・エラー
- **新機能**: 完全に新しい機能の実装
- **機能改善**: 既存機能の拡張・改良
- **改善**: 既存機能の品質向上
- **優先度:最高**: リリース阻害、緊急対応必須
- **優先度:高**: 重要機能、早急対応
- **優先度:中**: 通常対応
- **優先度:低**: 将来検討、v2.0以降
- **難易度:簡単**: 30分以内
- **難易度:普通**: 2-4時間
- **難易度:困難**: 半日以上

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

# 💻 開発コマンドリファレンス

## ⚙️ 基本コマンド
```bash
make test lint pre-commit                            # 品質チェック
kumihan convert input.txt -o output/                 # 基本変換
python -m kumihan_formatter check-syntax file.txt   # 記法検証
pip install -e ".[dev]"                             # 依存関係
```

# 記法仕様

## 実装済み記法（v3.0.0、Issue #726対応）
- **基本**: `# 装飾名 #
内容
##` ブロック記法のみ（**単一行記法完全廃止**）
- **統一仕様**: 全記法がブロック形式、終了マーカー`##`必須
- **マーカー**: 半角`#`・全角`＃`両対応（混在厳格禁止）
- **対応キーワード**: 太字、イタリック、下線、取り消し線、コード、引用、枠線、ハイライト、見出し1-5、折りたたみ、ネタバレ、中央寄せ、注意、情報、コードブロック
- **color属性**: 16進数カラーコード（#ff0000）、英単語色名30種（red/Red/RED全形式対応）
- **目次**: 見出し1-5から自動生成、唯一の空ブロック許可記法

## 将来実装予定記法
- **脚注**: `((content))` → 巻末移動（基本検証のみ実装済み）
- **ルビ**: `#ルビ content(reading)#` → ルビ表現（Issue #661で実装）
- **表**: 複雑な表構造（Phase 3で個別Issue化）

## 履歴・削除済み記法
- **単一行記法**: v3.0.0で完全廃止（`#太字# 内容` → `#太字#
内容
##`）
- **;;;記法**: Issue #679 Phase 1で完全削除（v2.1.0-alpha）
- **alt属性・画像キーワード**: Phase 1で完全削除
- **後方互換性**: v2.x以前の全記法を即時無効化

# 📚 ドキュメントリンク

## 主要ドキュメント
| カテゴリ | ファイル | 説明 |
|----------|--------|------|
| 🏢 アーキテクチャ | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | システム設計・構造 |
| 📖 ユーザーガイド | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 利用者向け使用方法 |
| 🤖 Claudeリファレンス | [docs/REFERENCE.md](docs/REFERENCE.md) | Claude Code専用ガイド |
| 📦 デプロイガイド | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | パッケージング・配布 |

## 詳細仕様書
| カテゴリ | ファイル | 説明 |
|----------|--------|------|
| 📝 記法仕様 | [docs/specs/notation.md](docs/specs/notation.md) | Kumihan記法の完全仕様 |
| ⚙️ 機能仕様 | [docs/specs/functional.md](docs/specs/functional.md) | システム機能の詳細仕様 |
| ❗ エラー仕様 | [docs/specs/error-messages.md](docs/specs/error-messages.md) | エラーメッセージ一覧 |

---

# ⚡ 重要指示リマインダー

## 🎯 作業原則
- **ミニマル作業**: 求められたことのみを実行、余分な作業は禁止
- **ファイル作成制限**: 目的達成に絶対必要な場合のみファイル作成
- **編集優先**: 新規作成より既存ファイルの編集を優先
- **ドキュメント作成禁止**: ユーザーの明示的要求なしに*.mdファイルやREADME作成禁止

## 🔄 品質保証  
- **コード品質**: Black, isort, mypy strictに準拠
- **テスト必須**: 重要な変更はテスト実行で確認
- **既存パターン遵守**: プロジェクトのコードスタイルとアーキテクチャに沿って実装

---
*✨ Generated by Claude Code for Kumihan-Formatter v3.0.0*
