# GitHub Actions監視スクリプト

Issue #559対応: CI/CD実行状況の継続監視スクリプト

## 概要

`monitor_github_actions.py`は、GitHub ActionsのCI/CD実行状況を監視し、問題の早期発見・報告を行うためのスクリプトです。

## インストール

```bash
# requestsライブラリのインストール
pip install requests
```

## 使用方法

### 基本的な使用

```bash
# 最近10件の実行状況を表示
python scripts/monitor_github_actions.py

# 特定ブランチの実行状況を確認
python scripts/monitor_github_actions.py --branch main

# Markdown形式でレポート生成
python scripts/monitor_github_actions.py --format markdown > ci_report.md
```

### 失敗したワークフローの検出

```bash
# 失敗したワークフローのみ表示
python scripts/monitor_github_actions.py --check-failures
```

### GitHub Token設定（推奨）

API制限を回避するため、GitHub Personal Access Tokenの設定を推奨します：

```bash
export GITHUB_TOKEN=your_github_token_here
python scripts/monitor_github_actions.py
```

## オプション

- `--repo REPO`: 監視するリポジトリ（デフォルト: mo9mo9-uwu-mo9mo9/Kumihan-Formatter）
- `--branch BRANCH`: 監視するブランチ
- `--limit N`: 取得する実行数（デフォルト: 10）
- `--format FORMAT`: 出力形式（text/json/markdown、デフォルト: text）
- `--check-failures`: 失敗したワークフローのみ表示

## 出力例

### Text形式

```
GitHub Actions CI/CD実行状況レポート
リポジトリ: mo9mo9-uwu-mo9mo9/Kumihan-Formatter
生成日時: 2025-01-21 10:00:00
================================================================================

✅ Quality Check
  ブランチ: main
  コミット: abc1234
  状態: completed (success)
  実行時間: 0:05:23
  URL: https://github.com/...
```

### Markdown形式

| 状態 | ワークフロー | ブランチ | 実行時間 | コミット | リンク |
|------|--------------|----------|----------|----------|--------|
| ✅ | Quality Check | main | 0:05:23 | abc1234 | [詳細](URL) |
| ❌ | Build | feature | 0:10:15 | def5678 | [詳細](URL) |

## 定期実行の設定

### cronでの定期実行

```bash
# 毎時間実行してSlackに通知（例）
0 * * * * /path/to/venv/bin/python /path/to/scripts/monitor_github_actions.py --check-failures || curl -X POST -H 'Content-type: application/json' --data '{"text":"CI/CD失敗を検出"}' YOUR_SLACK_WEBHOOK_URL
```

### GitHub Actionsでの定期監視

`.github/workflows/monitor.yml`:

```yaml
name: CI/CD Monitor
on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install requests
      - name: Run monitor
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/monitor_github_actions.py --format markdown > report.md
          if python scripts/monitor_github_actions.py --check-failures; then
            echo "✅ No failures detected"
          else
            echo "❌ Failures detected"
            exit 1
          fi
```

## トラブルシューティング

### API制限エラー

```
Error: API rate limit exceeded
```

→ GITHUB_TOKENを設定してください

### 権限エラー

```
Error: 403 Forbidden
```

→ トークンにrepo権限があることを確認してください
