# CLAUDE_COMMANDS.md

> Kumihan-Formatter – よく使うコマンド集
> **目的**: 開発・デバッグで頻繁に使用するコマンドのリファレンス
> **バージョン**: 1.0.0 (2025-01-15)

## 開発用コマンド
```bash
make test          # テスト実行
make lint          # リントチェック
make format        # コードフォーマット
make coverage      # カバレッジレポート生成
make pre-commit    # コミット前の全チェック実行
```

## デバッグ用コマンド
```bash
# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher

# 詳細ログレベル設定
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_LOG_LEVEL=DEBUG python3 -m kumihan_formatter.gui_launcher

# コンソール出力も有効化
KUMIHAN_GUI_DEBUG=true KUMIHAN_GUI_CONSOLE_LOG=true python3 -m kumihan_formatter.gui_launcher

# 開発ログ機能（Issue#446）
KUMIHAN_DEV_LOG=true kumihan convert input.txt output.txt

# 構造化ログ機能（Issue#472）- JSON形式でClaude Code解析しやすく
KUMIHAN_DEV_LOG=true KUMIHAN_DEV_LOG_JSON=true kumihan convert input.txt output.txt

# 詳細ログ出力
KUMIHAN_DEBUG=1 kumihan convert input.txt output.txt

# プロファイリング
python -m cProfile -s cumulative cli.py
```

### デバッグオプション
- ログレベル: `--debug`オプション使用
- エラートレース: `--traceback`オプション

## CLI使用例
```bash
# 基本的な変換
kumihan convert input.txt output.txt

# 記法サンプル表示
kumihan sample --notation footnote

# 構文チェック
kumihan check-syntax manuscript.txt
```

## Git関連コマンド

### PR作成
```bash
# PR作成
gh pr create --title "タイトル" --body "内容"

# オートマージは使用しない（手動でマージ）
# gh pr merge PR番号 --auto --merge  # 使用禁止

# オートマージが自動有効化された場合は明示的に無効化
gh pr merge PR番号 --disable-auto
```

## 環境変数一覧

| 環境変数 | 説明 | 値 |
|---------|------|-----|
| `KUMIHAN_GUI_DEBUG` | GUIデバッグモード有効化 | `true` |
| `KUMIHAN_GUI_LOG_LEVEL` | GUIログレベル設定 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `KUMIHAN_GUI_CONSOLE_LOG` | コンソールログ出力有効化 | `true` |
| `KUMIHAN_DEV_LOG` | 開発ログ有効化 | `true` |
| `KUMIHAN_DEV_LOG_JSON` | JSON形式ログ出力 | `true` |
| `KUMIHAN_DEBUG` | 詳細デバッグ出力 | `1` |
