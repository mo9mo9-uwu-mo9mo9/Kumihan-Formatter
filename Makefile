# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint test test-unit test-integration test-performance test-coverage

# デフォルトターゲット
help:
	@echo "Kumihan-Formatter Build System"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make setup         - 開発環境セットアップ"
	@echo "  make lint          - コード品質チェック"
	@echo "  make test          - 全テスト実行"
	@echo "  make test-unit     - ユニットテスト実行"
	@echo "  make test-integration - 統合テスト実行"
	@echo "  make test-performance - パフォーマンステスト実行"
	@echo "  make test-coverage - カバレッジ付きテスト実行"
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

# テストコマンド実装
test:
	@echo "🧪 全テスト実行中..."
	$(PYTHON) -m pytest
	@echo "✅ テスト完了"

test-unit:
	@echo "🔬 ユニットテスト実行中..."
	$(PYTHON) -m pytest tests/unit -m unit
	@echo "✅ ユニットテスト完了"

test-integration:
	@echo "🔗 統合テスト実行中..."
	$(PYTHON) -m pytest tests/integration -m integration
	@echo "✅ 統合テスト完了"

test-performance:
	@echo "⚡ パフォーマンステスト実行中..."
	$(PYTHON) -m pytest tests/performance -m performance --benchmark-only
	@echo "✅ パフォーマンステスト完了"

test-coverage:
	@echo "📊 カバレッジ付きテスト実行中..."
	$(PYTHON) -m pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "✅ カバレッジテスト完了"

clean:
	@echo "🧹 一時ファイル削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	@echo "✅ クリーンアップ完了"