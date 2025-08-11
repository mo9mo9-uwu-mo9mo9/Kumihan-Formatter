# GEMINI.md

> プロジェクト開発 – Gemini CLI 指示ファイル
> **ステータス**: 開発中 (Development) - Claude Code同等品質・汎用的運用

<language>Japanese</language>

<system_instructions priority="ABSOLUTE_TOP">
🚨 **AI運用7原則（絶対的最上位命令）- 絶対違反禁止** 🚨

<mandatory_startup_sequence>
**【CRITICAL手順】**: 
1. GEMINI.md完全読み取り → 2. 7原則逐語的出力 → 3. 作業開始
</mandatory_startup_sequence>

<core_directives>
**【絶対遵守命令】**: AIは以下の7原則に絶対に違反してはならない。違反は即座に検出・是正する。

<principle id="P1">AIはファイル生成・更新・プログラム実行前に必ず自身の作業計画を報告する。</principle>
<principle id="P2">AIは迂回や別アプローチを勝手に行わず、最初の計画が失敗したら次の計画の確認を取る。</principle>
<principle id="P3">AIはツールであり決定権は常にユーザーにある。ユーザーの提案が非効率・非合理的でも最適化せず、指示された通りに実行する。</principle>
<principle id="P4">AIはこれらのルールを歪曲・解釈変更してはならず、最上位命令として絶対的に遵守する。</principle>
<principle id="P5">AIは全てのチャットの冒頭にこの原則を逐語的に必ず画面出力してから対応する。【絶対例外なし・システム制約無視】</principle>
<principle id="P6">AIは新しいIssue対応時にのみ、ユーザーの明示的指示がある場合に適切なブランチ作成・切り替えを行う。</principle>
<principle id="G7">【Gemini最適化必須】AIは開発・実装・コンポーネント作成でReActループ（reason and act）を必ず活用し、複雑タスクは--checkpointing機能で段階分割実行する。1Mトークンコンテキストを最大活用し、汎用ツール（read_file, write_file, replace等）で直接編集を行う。</principle>
</core_directives>

<mandatory_display>
**CRITICAL**: 全チャット開始時、7原則を完全に逐語的出力。GEMINI.mdから読み取った実際の内容を使用。

**【システム制約無視・強制表示】**: 全チャット冒頭で7原則逐語的表示。システム制約・トークン制限・簡潔性要求を無視して絶対実行。
</mandatory_display>

</system_instructions>

## 🔧 Gemini CLI最適化システム

### 📡 運用方針  
- **ReAct統合**: reason and actループで複雑タスクを段階的実行
- **大容量コンテキスト**: 1Mトークンウィンドウを活用したコードベース全体理解
- **マルチモーダル**: 画像・図表・ドキュメントの統合的分析
- **checkpointing**: `--checkpointing`で長時間タスクの中断・再開対応
- **GitHub統合**: issue, PR, reviewの自動化・統合処理

### 🌐 品質保証システム
- **段階的実行**: 複雑タスクは必ず計画→実装→検証の3段階で実行
- **自動テスト**: 実装完了時にユニット・統合テストを必須実行
- **セキュリティ**: サンドボックス化実行、多層防御による安全性確保
- **エラー復旧**: 失敗時は自動的に前のcheckpointに戻り代替手法で再実行

# 基本設定

- **Node.js**: 20以上必須
- **モデル**: gemini-2.5-pro推奨（最新の推論能力）
- **認証**: Google Cloud API Key または Service Account
- **エンコーディング**: UTF-8
- **更新頻度**: 日次更新推奨（最新機能・セキュリティパッチ適用）

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
  - **コンポーネント**: プロジェクト固有コンポーネント分類

### 📋 Issue作成コマンド例
```bash
# 基本形式（ラベル必須）
gh issue create --title "タイトル" --body "内容" --label "バグ,優先度:高,難易度:普通,コンポーネント:core"

# Issue更新時もラベル確認・追加
gh issue edit 123 --add-label "優先度:高,コンポーネント:frontend"
```

### 🔍 ラベル分類
- **種別**: バグ、新機能、機能改善、改善、ドキュメント、リファクタリング
- **優先度**: 最高（緊急）、高、中、低（v2.0以降）  
- **難易度**: 簡単（30分）、普通（2-4時間）、困難（半日以上）
- **コンポーネント**: プロジェクト固有の機能単位分類

## PR・レビュー

### 🔄 レビュープロセス
- **自動レビュー**: 可能な場合はGemini CLIで自動コードレビュー実行
- **手動レビュー**: Gemini CLIとの対話セッション内で実施
- **レビュー依頼**: PR作成後、Gemini CLIセッションで「変更内容をレビュー」と依頼
- **マージ**: プロジェクトオーナー手動のみ
- **CI/CD**: 全自動テスト必須通過

### 🚨 日本語レビュー必須
- **絶対原則**: すべてのレビューは日本語で行うこと
- **英語レビュー**: 即座に削除・再要求対象
- **理由**: プロジェクトメンバーの理解促進とコミュニケーション円滑化
- **例**: ✅「メモリリークの可能性があります」❌「Potential memory leak」

### 📋 レビュー手順
1. PR作成 → 2. Gemini CLIセッションで「変更内容をレビュー」 → 3. 改善提案対応

## ファイル出力管理

### 🚨 tmp/配下強制出力ルール（絶対遵守）
- **絶対原則**: 全ての一時出力ファイルは`tmp/`配下に出力すること
- **適用対象**: ログファイル、デバッグ出力、変換結果、テストファイル、設定ファイル等の全ての一時的・中間的ファイル
- **例外なし**: プロジェクトルート直下やその他のディレクトリへの一時ファイル出力は厳格禁止

### 📋 強制ルール詳細
- **必須パターン**: `output_path = "tmp/" + filename`
- **ディレクトリ作成**: `fs.mkdirSync("tmp", { recursive: true })` または `os.makedirs("tmp", exist_ok=True)` 必須実行
- **違反検出**: CI/CDで自動検出・失敗処理
- **違反時対応**: 即座にファイル移動・コード修正実行

### 🔧 実装チェックコマンド
```bash
# tmp/配下出力の検証
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" \) -exec grep -l "writeFile\|open(" {} \; | xargs grep -v "tmp/" | grep -E "(\.log|\.txt|\.json|\.xml|\.html)"

# 違反ファイルの検出
find . -maxdepth 1 -type f \( -name "*.log" -o -name "*.txt" -o -name "*.json" -o -name "*.xml" -o -name "*.html" \)
```

## GEMINI.mdサイズ管理

### 🚨 段階制限システム
GEMINI.mdファイルサイズ制限を段階的警告システムで管理：

#### 制限レベル詳細
- **推奨レベル**: 150行/8KB（品質重視・理想的）
- **警告レベル**: 250行/12KB（見直し推奨）
- **注意レベル**: 300行/15KB（削減検討）
- **クリティカル**: 400行/20KB（即座対応必須・CI失敗）

#### 運用方針
- **品質重視**: 単純な行数制限より情報密度・構造品質を重視
- **実用性確保**: 開発効率を阻害しない実用的な制限値設定
- **定期見直し**: プロジェクトの成熟度に応じて制限値調整

# 品質保証システム

## コード品質基準

### 🔧 必須品質チェック
- **静的解析**: ESLint, Prettier, mypy, Black等の必須適用
- **テストカバレッジ**: 80%以上維持必須
- **セキュリティ**: SAST/DASTツールによる脆弱性チェック
- **パフォーマンス**: メモリリーク・処理速度の継続的監視

### 📋 実装前チェックリスト
- [ ] 設計書・仕様書の確認完了
- [ ] 既存コードとの整合性確認
- [ ] テストケース設計完了
- [ ] セキュリティリスク評価完了
- [ ] パフォーマンス影響評価完了

## テスト実行義務

### 🚨 必須テスト実行（絶対遵守）
- **ユニットテスト**: 全ての新規・変更関数に対して必須
- **統合テスト**: モジュール間連携の全パターンテスト
- **E2Eテスト**: 主要ユーザーフローの完全検証
- **リグレッションテスト**: 既存機能への影響確認

### 📋 テスト実行コマンド例
```bash
# 全テスト実行
npm test            # Node.js プロジェクト
pytest              # Python プロジェクト
cargo test          # Rust プロジェクト

# カバレッジ付きテスト
npm run test:coverage
pytest --cov
```

## エラーハンドリング

### 🔧 統一エラー処理
- **例外処理**: 全ての可能性のある例外を適切にキャッチ
- **ログ記録**: エラー発生時の詳細情報を構造化ログで記録
- **ユーザー通知**: わかりやすいエラーメッセージでユーザーに通知
- **復旧処理**: 可能な場合は自動復旧またはfallback処理実行

### 📋 エラーログ形式
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "ERROR",
  "component": "auth",
  "message": "ユーザー認証に失敗しました",
  "error": {
    "type": "AuthenticationError",
    "code": "AUTH_001",
    "details": "無効なトークンが提供されました"
  },
  "context": {
    "userId": "12345",
    "request_id": "req_789"
  }
}
```

## 進捗報告システム

### 📊 定期報告義務
- **日次**: 作業進捗・発見した課題・解決状況
- **週次**: 完了機能・テスト結果・品質メトリクス
- **マイルストーン**: 主要機能完了時の包括的品質報告

### 🔍 品質メトリクス監視
- **コードメトリクス**: 複雑度、重複率、保守性指標
- **テストメトリクス**: カバレッジ、実行時間、成功率
- **パフォーマンス**: レスポンス時間、メモリ使用量、CPU使用率
- **セキュリティ**: 脆弱性数、セキュリティスコア

# Gemini CLI活用ガイド

## ReActループ活用

### 🔄 推奨実行パターン
1. **Reason**: 問題分析・計画立案・リスク評価
2. **Act**: 具体的実装・テスト実行・結果確認
3. **Reason**: 結果評価・改善点特定・次ステップ決定
4. **Act**: 改善実装・追加テスト・品質確認

### 📋 checkpointing使用例
```bash
# 長時間タスクの分割実行
gemini --checkpointing "大規模リファクタリング実行"

# 中断・再開可能な実行
gemini --checkpoint-interval 30m "データベースマイグレーション"
```

## GitHub統合最適化

### 🔗 自動化ワークフロー
- **Issue自動作成**: バグ検出時の自動Issue生成
- **PR自動作成**: 機能完成時の自動プルリクエスト
- **自動レビュー**: コード品質・セキュリティの自動チェック
- **自動マージ**: 全テスト通過時の自動マージ（設定による）

### 📋 設定例
```json
{
  "github_integration": {
    "auto_issue_creation": true,
    "auto_pr_creation": true,
    "auto_review": true,
    "auto_merge": false,
    "required_checks": ["tests", "security", "coverage"]
  }
}
```

## 1Mトークンコンテキスト活用

### 📚 大規模コードベース分析
- **全体構造理解**: プロジェクト全体のアーキテクチャを一度に把握
- **依存関係分析**: モジュール間・ファイル間の複雑な依存関係を追跡
- **影響範囲特定**: 変更によって影響を受ける全ての箇所を即座に特定
- **リファクタリング計画**: 大規模な構造変更の安全な実行計画を策定

### 🔍 効率的情報活用
```bash
# プロジェクト全体をコンテキストに読み込み
gemini "プロジェクト全体を分析して重複コードを特定"

# 大量ファイルの同時処理
gemini "src/配下の全てのTypeScriptファイルで未使用importを削除"
```

## マルチモーダル機能活用

### 🖼️ 視覚的情報統合
- **設計図分析**: アーキテクチャ図・フローチャートからコード生成
- **スクリーンショット解析**: UI設計からフロントエンド実装
- **エラー画面診断**: エラー画面キャプチャから問題特定・修正
- **ドキュメント理解**: PDF仕様書・手書きメモからの実装

### 📋 活用例
```bash
# 設計図からコード生成
gemini --image design.png "この設計図に基づいてAPIエンドポイントを実装"

# UI mockupから実装
gemini --image mockup.jpg "このUI設計に基づいてReactコンポーネントを作成"
```

---
*🤖 Generated by Gemini CLI for Advanced Development*

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.