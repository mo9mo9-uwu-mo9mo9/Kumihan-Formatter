# Repository Guidelines

## Project Structure & Module Organization
- Source: `kumihan_formatter/` (CLI entry: `project.scripts.kumihan` → `core.utilities.api_utils:main`).
- Tests: `tests/unit/`, `tests/integration/`（必要に応じて `tests/performance/`, `tests/manual/`）。
- Support: `scripts/`, `examples/`, `output/`, `tmp/`, `.github/`。
- Config: `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`。

## Build, Test, and Development Commands
- 初期セットアップ: `make setup`（開発・テスト依存をインストール）。
- 主要品質チェック: `make quality-check`（依存監査→lint→unit→性能）。
- Lint: `make lint` / 厳格版: `make lint-strict`。
- テスト: `make test`（カバレッジ付き）/ `make test-unit` / `make test-integration`。
- 事前フック: `make pre-commit`（ローカル統合チェック）。
- 実行例: インストール後は `kumihan --help`。開発中は `python -m kumihan_formatter --help`。

## Coding Style & Naming Conventions
- フォーマッタ: Black（行長 88）。インデント: 4スペース。
- 型: mypy strict 必須。すべての新規/変更関数に型注釈。
- 命名: modules/files = `snake_case`、classes = `PascalCase`、functions/vars = `snake_case`、constants = `UPPER_SNAKE_CASE`。
- テンプレート/アセットは `kumihan_formatter/templates|assets` に配置。

## Testing Guidelines
- フレームワーク: pytest（`pyproject.toml`に設定）。
- 実行: `pytest -q` も可。カバレッジは HTML を `tmp/htmlcov/` に出力。
- しきい値: 現在 `--cov-fail-under=6`（段階的に引き上げ予定）。
- 命名: ファイルは `test_*.py`、関数は `test_*`。`@pytest.mark.unit|integration|slow|e2e` を適切に付与。

## Commit & Pull Request Guidelines
- コミット傾向: 先頭に絵文字＋種別＋Issue参照（例: `🎯 Fix #1234: 説明`）。主語省略・命令形で要点を短く。
- ブランチ規約: `{type}/issue-{番号}-{英語概要}`（例: `feat/issue-123-add-user-auth`）。日本語ブランチ名は禁止。
- PR 要件: 目的・変更点・関連Issue（`Closes #123`）・動作確認・スクリーンショット/出力例（必要時）。`make lint` と `make test` が通ること。必要に応じて `CHANGELOG.md` 更新。

## Security & Configuration Tips
- Python 3.12 以上を使用。機密情報をコミットしない（環境変数で注入）。
- 依存監査: `make dependency-audit`。一時生成物は `tmp/` 配下に限定。
- 大きな変更は小さなPRに分割し、`quality-check` を通してから提出。

## Agent-Specific Instructions
- 既存スタイル（Black/mypy/pytest/Makefile）の遵守を最優先。
- 新規ファイルは既存の配置ルールと命名に合わせ、最小限の差分で提案。
- 提案前に `make lint` と `make test` をローカル実行して自己検証。

## Automation Workflow (Fully Auto)
- 手順: 1) Issue作成 → 2) Issueに基づく作業 → 3) セルフレビュー → 4) 改善実装 → 5) 最小差分PR作成 → 6) 3-5をループ → 問題がなくなったらPRをマージ（squash）→ ブランチ削除。
- 権限/前提: gh認証済み、ブランチ保護で必須レビュー・必須CIを要求しない（またはセルフレビュー許可）。GitHub Actionsは導入しない。
- 品質ゲート: `scripts/run_quality_check.sh` を用い、`make lint && make test` 成功を必須とする。
- ラベル: `P0`/`P1`/`P2` を標準化。`scripts/set_issue_priorities.sh` で一括付与可能。
- PR運用: 最小差分・1Issue=1PR。`scripts/create_minimal_pr.sh` でPR作成、`scripts/pr_merge_and_cleanup.sh` でsquashマージとブランチ掃除。
- ログ: 自動化ログは `tmp/automation-logs/` に保存（git管理外）。

## Deprecation Policy（段階的廃止方針）
- 対象（棚卸し）:
  - core/parsing/markdown_parser.py（Deprecated警告あり）
  - core/parsing/legacy_parser.py（レガシー互換API）
  - parsers/parser_utils.py（get_keyword_categories/validate_keyword_legacy のDeprecated）
  - parsers/specialized_parser.py（parse_marker/new_format/ruby のDeprecated）
  - parsers/core_parser.py（legacy parse系のDeprecated）
  - core/syntax/__init__.py / core/ast_nodes/__init__.py（後方互換の再エクスポート）
  - unified_api.py の DummyParser/DummyRenderer（互換目的）

- フェーズ計画（目安）:
  - Phase 1（〜2025-09-15）: RuntimeのDeprecationWarningを明示・Doc整備・移行案内（DummyParser/DummyRenderer はインスタンス化時に警告を発する）
  - Phase 2（〜2025-10-15）: 後方互換エイリアスを非公開化（内部用に限定）/ import時に一次ブロック可
  - Phase 3（〜2025-11-30）: レガシーAPIの削除（上記対象の段階削除）

- 運用:
  - 1 Issue = 1 PR 原則で小分けに削除
  - 各PRで README/QUICKSTART の参照を追随
- 影響範囲（public import）に変更が出る場合は minor version を上げる

## 公開API（現時点）
- パーサーファサード: `kumihan_formatter.parser.Parser`, `kumihan_formatter.parser.parse`
- 統合API: `kumihan_formatter.unified_api.KumihanFormatter`
- 構文チェック: `kumihan_formatter.core.syntax.SyntaxReporter`, `check_files`, `format_error_report`
- ASTノード: `kumihan_formatter.core.ast_nodes.node.Node`, `...factories.*`（直接import推奨）
- 互換レイヤ（最小）: `kumihan_formatter.core.utilities.compatibility_layer.MasterParser`, `parse_text`, `parse_file`, `parse_stream`

## GPT-5 Best Practices（2025-09 最新）
- **推奨モデル:** `gpt-5`（高品質）/ `gpt-5-mini`（低レイテンシ）/ `gpt-5-nano`（大量並列・CI向け）。CLIの既定は `gpt-5`。
- **新パラメータ:** `reasoning_effort` と `verbosity` に対応。
  - `reasoning_effort`: `minimal`/`low`/`medium`(既定)/`high`。CLIは既定 `low`、深い分析が必要なときのみ `medium/high` を使用。
  - `verbosity`: `low`/`medium`(既定)/`high`。CLIの対話は `low` を基本にし、ドキュメント生成や設計レビューのみ `medium/high` を使用。
- **モデル選択指針:**
  - **計画/設計/難所デバッグ:** `gpt-5` + `reasoning_effort=medium`。
  - **反復的な編集/小修正:** `gpt-5-mini` + `reasoning_effort=low` + ストリーミング。
  - **大規模バッチ整形/移行:** `gpt-5-nano` + Batch API（後述）。

### プロンプト/ツール利用
- **システム指示:** 役割・出力形式・安全境界（禁止事項/データ取り扱い）を明確化。CLIは「簡潔・根拠提示・安全第一」を既定の原則にする。
- **プリフライト（前置き）:** ツール実行前に1行で「何を・なぜ」を宣言（例:「依存監査のPython化をPR化します」）。
- **Structured Outputs:** 可能な限りJSON Schemaを定義し、厳格な型で受け取る（理由: 後工程の自動処理・失敗復元が容易）。
- **Tool Calling:**
  - 失敗に強い実装にする（ツールの例外→要約して再試行・フォールバック）。
  - 可能な場合は並列実行を使い、長時間ジョブは粒度を小さく分割。
  - 「カスタムツール」の文法制約（CFG）を活用し、テキスト引数でも堅牢性を確保。
- **Web/File Search:** 「最新」「価格」「規約」「スケジュール」「固有名詞」など時間変化の可能性がある場合は必ず検索→根拠を添付。

### 応答品質/安全
- **低冗長:** 既定 `verbosity=low`。説明は必要最小限、根拠や選択肢が価値を生む時のみ展開。
- **最小思考:** まず `reasoning_effort=low`（もしくは `minimal`）。失敗/あいまいさ検出時に段階的に引き上げる。
- **安全配慮:** ポリシーに抵触する依頼は代替案と方針説明で誘導。リスクの高い操作は明示の合意を取る。

### パフォーマンス/コスト最適化
- **Prompt Caching:** 繰り返し使う長いシステム/コンテキストはキャッシュ（大規模対話で効果大）。
- **Batch API:** 非同期バルク処理はBatchで50%割引。キュー上限/レートはモデルごとに異なるため、監視とリトライ戦略を組み込む。
- **ストリーミング:** CLI対話はSSEストリームで早期可視化。ツール実行と並行して進捗を提示。
- **モデルの粒度:** 小タスクは `mini/nano` で高速化し、難所のみ `gpt-5` にエスカレーション。

### 再現性/運用
- **決定性:** `seed` を設定して差分検証を容易に。出力形式はStructured Outputsで固定化。
- **評価/Evals:** 重要なプロンプトは回帰用のスモークEvalsを用意し、モデル/プロンプト変更時に自動検証。
- **ロギング:** 入出力・ツール呼び出し・モデル/パラメータ・トークン使用量を記録。機密はスコープを限定する。

### CLI実装規約（GPT-5対応）
- **デフォルト:** `gpt-5`, `reasoning_effort=low`, `verbosity=low`, ストリーミング有効。
- **長時間処理:** 事前にPlanを提示→サブタスクごとにコミットポイントを設ける（Issue-first運用）。
- **失敗時のふるまい:** 原因→最小修正→再実行の順に報告。外部依存（ネット/権限/レート）起因は待避策も提示。
- **根拠提示:** ウェブ参照は出典と日時を明記し、変化点（価格/規約）は絶対日付で記述。

## Codex CLI 既定設定（GPT‑5）
- 目的: コマンド一発で「安全・低冗長・低推論コスト」の既定を適用。
- 既定値（2025‑09‑01）:
  - `model`: `gpt-5`（重タスクは `gpt-5-thinking`、軽タスクは `gpt-5-mini`）
  - `reasoning_effort`: `low`（必要時のみ `medium/high`。極短応答は `minimal`）
  - `verbosity`: `low`（設計/レビューのみ `medium/high`）
  - `stream`: `on`
- 推奨起動例（環境変数で明示）:
  - POSIX:
    - `export OPENAI_MODEL=gpt-5`
    - `export OPENAI_REASONING_EFFORT=low`
    - `export OPENAI_VERBOSITY=low`
    - `export OPENAI_STREAMING=true`
  - Windows (PowerShell):
    - `$env:OPENAI_MODEL='gpt-5'`
    - `$env:OPENAI_REASONING_EFFORT='low'`
    - `$env:OPENAI_VERBOSITY='low'`
    - `$env:OPENAI_STREAMING='true'`
- 運用ルール:
  - 小さな修正/反復編集は `gpt-5-mini`、設計・難所デバッグは `gpt-5`、大量整形は `gpt-5-nano` を明示選択。
  - 「もっと詳しく」等の明示要求がない限り `verbosity=low` を維持。
  - `reasoning_effort` は失敗や曖昧性検知時に段階引き上げ。

## Serena MCP 連携（推奨設定）
- 目的: セマンティック検索・記号操作・安全な編集をMCP経由で提供し、CLIの生産性を底上げ。
- プロジェクト設定: 本リポジトリは `.serena/project.yml` を同梱。以下を推奨:
  - `ignore_all_files_in_gitignore: true`（不要資産の索引除外）
  - `read_only: false`（編集ツール有効化）
  - `excluded_tools: []`（原則すべて許可。危険操作はCLI側で承認フロー）
- 初回インデックス（大規模時・一度だけ）:
  - `uvx --from git+https://github.com/oraios/serena index-project`（または `uv run --directory /path/to/serena index-project`）
- MCPクライアントへの登録（例: Claude Desktop）:
  - `File > Settings > Developer > MCP Servers > Edit Config` で以下を追加（パスは環境に合わせて調整）:
    - `{"mcpServers": {"serena": {"command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena-mcp-server"]}}}`
  - 代替: `--transport sse --port 9121` で常駐→クライアントからSSE接続。
- 推奨コンテキスト/モード:
  - `--context ide-assistant`（IDE連携最適化）
  - `--mode planning --mode editing`（計画→編集の往復を高速化）
- 運用Tips:
  - 大規模プロジェクトは索引前提（初回だけ数分）。
  - ツール名は明示指定（クライアントがサーバー名を解決しない場合あり）。
  - ゾンビプロセス対策にWebダッシュボードを有効化可（`serena_config.yml` の `web_dashboard: true`）。
