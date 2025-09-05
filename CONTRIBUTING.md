# 🤝 Kumihan-Formatter Contributing Guide

## 📋 目次

- [開発環境のセットアップ](#開発環境のセットアップ)
- [ブランチ戦略](#ブランチ戦略)
- [コーディング規約](#コーディング規約)
- [📁 ファイル配置ルール](#-ファイル配置ルール)
- [テスト](#テスト)
- [プルリクエスト](#プルリクエスト)
- [日本語レビュー必須規則](#日本語レビュー必須規則)

## 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter.git
cd Kumihan-Formatter

# Python依存関係インストール
python3 -m pip install -e .

# 開発用一括インストール（推奨）
python3 -m pip install -e ".[dev]"

# pre-commit 相当のローカル統合チェック（フック導入は任意）
make pre-commit
```

## ブランチ戦略

### 🚨 絶対禁止事項
- **日本語ブランチ名は絶対禁止**（Git hooks・GitHub Actionsで自動拒否）

### 📋 ブランチ命名規則
```
{type}/issue-{Issue番号}-{英語概要}
```

- **type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **例**: `feat/issue-123-add-user-authentication`

## コーディング規約

### Python
- **バージョン**: 3.12以上
- **フォーマッター**: Black
- **型チェック**: mypy strict

### 必須コマンド
```bash
# コード品質チェック
make lint
make test

# または個別実行
black .
mypy .
pytest
```

## 📁 ファイル配置ルール

### 🎯 ルートディレクトリ管理方針
プロジェクトルートは**最小限のファイルのみ**を配置し、整理された状態を保つ。

### ✅ ルートディレクトリに配置すべきファイル

| カテゴリ | 対象ファイル | 理由 |
|---------|------------|------|
| **プロジェクト設定** | `pyproject.toml`, `setup.py`, `setup.cfg` | Pythonパッケージの基本設定 |
| **Git/GitHub設定** | `.gitignore`, `.gitattributes` | リポジトリの基本設定 |
| **CI/CD設定** | `.pre-commit-config.yaml`, `.github/` | 自動化ツールがルートを参照 |
| **ライセンス** | `LICENSE` | GitHubが自動認識 |
| **主要README** | `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | プロジェクトの顔となる文書 |
| **Codex関連** | `AGENTS.md` | Codex CLI 用ガイド |
| **ビルドツール** | `Makefile` | 開発コマンドの集約 |
| **開発スクリプト** | `scripts/*.sh`, `scripts/*.py` | プロジェクトの各種ユーティリティ |
| **Linter設定** | `.markdownlint.json` | ツールがルートを参照 |

### 🚫 ルートディレクトリに配置してはいけないファイル

| カテゴリ | 誤った配置例 | 正しい配置先 | 理由 |
|---------|------------|------------|------|
| **テストデータ** | `test_*.txt`, `sample_*.txt` | `tests/manual/` または `tests/fixtures/` | テスト用ファイルは専用ディレクトリへ |
| **Issue報告書** | `issue_XXX_report.md` | `docs/issues/` | Issue関連文書は専用フォルダで管理 |
| **詳細ドキュメント** | `SERENA_README.md`, `DEPLOYMENT_GUIDE.md` | `docs/` | 補助的なドキュメントはdocs配下へ |
| **開発スクリプト** | `check_*.sh`, `analyze_*.py` | `scripts/` | 開発補助ツールは専用ディレクトリへ |
| **ツール類** | 特定用途のユーティリティ | `tools/` | プロジェクト固有ツールは専用ディレクトリへ |
| **一時ファイル** | `*.tmp`, `*.bak`, `debug.log` | 削除またはignore | 一時ファイルはコミット対象外 |

### 📝 新規ファイル作成時のチェックリスト

1. **ファイルの役割を明確にする**
   - プロジェクト全体に必要？ → ルートに配置
   - 特定の用途のみ？ → 適切なサブディレクトリへ

2. **既存のパターンに従う**
   - 同種のファイルがどこにあるか確認
   - 命名規則を統一（例：テストファイルは`test_`で始める）

3. **ドキュメントの場合**
   - 主要3文書（README, CHANGELOG, CONTRIBUTING）以外は`docs/`へ
   - Issue関連は必ず`docs/issues/`へ

4. **スクリプトの場合**
   - プロジェクト起動用 → ルート
   - 開発補助用 → `scripts/`
   - テスト用 → `tests/`配下の適切な場所

### 🔍 配置先に迷ったら

```bash
# 類似ファイルの配置を確認
find . -name "*.txt" -o -name "*.md" | grep -v node_modules | sort

# ディレクトリ構造を確認
tree -d -L 2
```

### 🚨 レビュー時の確認事項

PRレビュー時は以下を確認：
- [ ] ルートディレクトリに新規ファイルが追加されていないか
- [ ] 追加される場合、上記の「配置すべきファイル」に該当するか
- [ ] テストデータやサンプルファイルが適切な場所にあるか

## テスト

### テストポリシー（2025-09 時点）
- カバレッジ閾値: `--cov-fail-under=45`（`pyproject.toml`に準拠）。段階的に引き上げます。
- 破壊的操作は既定で禁止。必要な網羅は `--dry-run` または `KUMIHAN_FORCE=1` を用いて安全に行うこと。
- 実ファイル書き込みが必要な場合は `tmp_path` 等の一時ディレクトリを使用し、リポジトリ直下に生成しないこと。
- CLIテストは `kumihan --help/--version` と `--dry-run/--force` を中心にスモークする（副作用なし）。
- 型チェックは `mypy --strict` を準拠。オプショナル依存（`watchdog`, `rich`等）は `pyproject.toml` の overrides で missing imports を無効化済み。

### テストの実行
```bash
# 全テスト実行
make test

# 特定のテストのみ
pytest tests/unit/test_specific.py

# カバレッジ付き
pytest --cov=kumihan_formatter
```

### テストファイルの配置
- **単体テスト**: `tests/unit/`
- **統合テスト**: `tests/integration/`
- **パフォーマンステスト**: `tests/performance/`
- **手動テスト用データ**: `tests/manual/`

## プルリクエスト

### PR作成前のチェックリスト
- [ ] ブランチ名が英語で命名規則に従っている
- [ ] `make lint`が通る
- [ ] `make test`が通る
- [ ] ファイルが適切な場所に配置されている
- [ ] CHANGELOG.mdを更新した（機能追加/変更の場合）

### PRテンプレート
```markdown
## 概要
変更の概要を記載

## 関連Issue
Closes #XXX

## 変更内容
- 変更点1
- 変更点2

## テスト
- [ ] 単体テストを追加/更新
- [ ] 手動テストで動作確認
```

## 日本語レビュー必須規則

### 🚨 絶対原則
**すべてのコードレビューは日本語で行うこと**

### 理由
- プロジェクトメンバーの理解促進
- コミュニケーションの円滑化
- 技術用語の適切な日本語化

### 例
- ✅ 良い例：「このメソッドでメモリリークの可能性があります」
- ❌ 悪い例：「Potential memory leak in this method」

---

## 🤖 自動化されているチェック

### Git Hooks（ローカル）
- pre-commit: コード品質チェック
- commit-msg: 日本語ブランチ名の拒否

### GitHub Actions（CI/CD）
- ブランチ名の検証
- コード品質チェック
- テストの実行
- ファイル配置ルールのチェック（今後実装予定）

---

*最終更新: 2025-01-31*
