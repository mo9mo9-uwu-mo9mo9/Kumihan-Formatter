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
