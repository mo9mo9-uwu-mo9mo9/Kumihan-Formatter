# 開発で使用する重要コマンド

## 開発環境セットアップ
```bash
# 基本セットアップ
python -m pip install -e .
python -m pip install -r requirements-dev.txt

# Git hooks セットアップ（必須）
./scripts/install-hooks.sh
```

## 基本コマンド
```bash
# コード品質チェック（重要）
make lint

# 基本変換コマンド
kumihan convert input.txt output.txt
python -m kumihan_formatter convert input.txt

# 記法検証
python -m kumihan_formatter check-syntax file.txt

# クリーンアップ
make clean
```

## デバッグコマンド
```bash
# CLI開発ログ有効化
KUMIHAN_DEV_LOG=true python -m kumihan_formatter convert input.txt

# GUIデバッグモード
KUMIHAN_GUI_DEBUG=true python3 -m kumihan_formatter.gui_launcher
```

## 品質チェック詳細
```bash
# 個別実行
python -m black --check kumihan_formatter
python -m isort --check-only kumihan_formatter
python -m flake8 kumihan_formatter
python -m mypy kumihan_formatter
```

## システムコマンド（macOS）
- `ls`, `cd`, `grep`, `find` - 標準Unix コマンド
- `git` - バージョン管理