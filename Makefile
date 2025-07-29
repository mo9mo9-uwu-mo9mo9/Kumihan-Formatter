# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint

# デフォルトターゲット
help:
	@echo "Kumihan-Formatter Build System"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make setup         - 開発環境セットアップ"
	@echo "  make lint          - コード品質チェック"
	@echo "  make clean         - 一時ファイル削除"
	@echo ""

# 基本コマンド実装
setup:
	@echo "🚀 開発環境セットアップ中..."
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	@echo "✅ セットアップ完了"

lint:
	@echo "🔍 コード品質チェック中..."
	$(PYTHON) -m black --check $(SRC_DIR)
	$(PYTHON) -m isort --check-only $(SRC_DIR)
	$(PYTHON) -m flake8 $(SRC_DIR)
	$(PYTHON) -m mypy $(SRC_DIR)
	@echo "✅ リントチェック完了"

clean:
	@echo "🧹 一時ファイル削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "✅ クリーンアップ完了"