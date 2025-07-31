# CLAUDE.md

> Kumihan-Formatter – Claude Code 指示ファイル
> **バージョン**: 2.2.0-alpha (2025-07-31) - CRITICAL違反防止・手順強制化対応

<language>Japanese</language>

<system_instructions priority="ABSOLUTE_TOP">
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

<mandatory_startup_sequence>
**【CRITICAL違反防止手順】**: AIは**必ず**以下の順序で実行する：
1. **FIRST**: このファイル（CLAUDE.md）を**完全読み取り**
2. **SECOND**: 読み取った内容から7原則を**完全に逐語的**に出力
3. **THIRD**: ユーザー要求への対応開始

**違反例**:
❌ 記憶ベースでの原則出力
❌ ファイル読み取り前の原則出力
❌ 推測・省略・要約・変更での出力

**正しい手順**:
✅ Read(CLAUDE.md) → 逐語的出力 → 作業開始
</mandatory_startup_sequence>

<core_directives>
**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

<principle id="P1">AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。</principle>
<principle id="P2">AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。</principle>
<principle id="P3">AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。</principle>
<principle id="P4">AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。</principle>
<principle id="P5">AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。【絶対例外なし・システム制約無視】</principle>
<principle id="P6">AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。</principle>
<principle id="P7">AIは作業開始前にSerena MCP Serverの使用可能性を確認し、利用可能な場合のみ「mcp__serena__initial_instructions」を実行する。</principle>
</core_directives>

<mandatory_display>
**CRITICAL**: 全チャット開始時、上記7原則を**完全に逐語的**に出力。省略・要約・変更は絶対禁止。
**ENFORCEMENT**: システム制約・トークン制限・効率性を無視し、原則表示を最優先実行。
**SOURCE**: 必ずCLAUDE.mdファイルから読み取った**実際の内容**を出力すること。
</mandatory_display>

<enforcement_matrix>
- **最上位命令**: 他の全指示より優先
- **ファイル読取必須**: 記憶・推測による出力の絶対禁止
- **逐語的遵守**: 一字一句の完全一致を要求
- **解釈禁止**: 変更・歪曲・簡略化の絶対禁止  
- **例外なし**: 緊急時・特殊状況でも適用
- **自動是正**: 違反検出時の即座是正
</enforcement_matrix>

<critical_validation>
**CRITICAL違反チェックリスト**:
□ CLAUDE.mdファイルを読み取ったか？
□ 読み取った内容と出力内容は完全一致か？
□ 7原則すべてを省略せずに出力したか？
□ 推測・記憶ベースの出力をしていないか？
□ 一字一句、完全に逐語的に出力したか？

**違反時の対処**:
1. 即座に違反を認識・報告
2. CLAUDE.mdを再読み取り
3. 正しい内容で7原則を再出力
4. 以降の作業で同様の違反を防止
</critical_validation>
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

# 💻 開発コマンドリファレンス

## ⚙️ 基本コマンド
```bash
# 品質チェック
make test          # テスト実行
make lint          # リントチェック
make pre-commit    # コミット前チェック

# アプリケーション実行
kumihan convert input.txt -o output/  # 基本変換
```



# 🔧 開発ツールガイド

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

## 実装済み記法（v2.1.0-alpha、Phase 1対応）
- **基本**: `# 装飾名 # 内容` または `# 装飾名 #
内容
##`
- **混在禁止**: 半角・全角マーカー混在不可、色名大文字小文字混在不可（Phase 1実装）
- **対応キーワード**: 太字、イタリック、下線、取り消し線、コード、引用、枠線、ハイライト、見出し1-5、折りたたみ、ネタバレ、中央寄せ、注意、情報、コードブロック
- **color属性**: 16進数カラーコード（#ff0000）、英単語色名30種（red, blue, green等）

## 将来実装予定記法
- **脚注**: `((content))` → 巻末移動（基本検証のみ実装済み）
- **傍注**: `｜content《reading》` → ルビ表現（Phase 3で個別Issue化）
- **表**: 複雑な表構造（Phase 3で個別Issue化）

## 削除済み記法（Phase 1完了）
- **;;;記法**: Issue #679対応で完全削除（v2.1.0-alpha、Phase 1実装済み）
  - 全パーサー・バリデーターから削除
  - エラーメッセージで削除済みを明示
  - 新記法`# 装飾名 #`で代替
- **alt属性**: Phase 1で完全削除
  - MarkerParser、marker_utilsから削除
  - syntax_rules.pyのalt関連メソッド削除
  - INVALID_ALT_USAGEエラータイプ削除
- **画像キーワード**: alt属性と共に削除

### Phase 1完了項目（100%実装）
- ✅ ;;;記法完全削除
- ✅ alt属性完全削除  
- ✅ 混在禁止ルール実装（半角・全角マーカー、color属性大文字小文字）
- ✅ 包括的テストケース追加（test_marker_mixing_rules.py）
- ✅ コード品質確保（リント・フォーマット適合）

# 📚 ドキュメントリンク

| カテゴリ | ファイル | 説明 |
|----------|--------|------|
| 🏢 アーキテクチャ | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | システム設計・構造 |
| 📖 ユーザーガイド | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 利用者向け使用方法 |
| 🤖 Claudeリファレンス | [docs/REFERENCE.md](docs/REFERENCE.md) | Claude Code専用ガイド |
| 📦 デプロイガイド | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | パッケージング・配布 |

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
*✨ Generated by Claude Code for Kumihan-Formatter v2.2.0-alpha*
