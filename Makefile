# Kumihan-Formatter Makefile
# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PYTEST = $(PYTHON) -m pytest
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)
TEST_DIR = tests
SCRIPTS_DIR = scripts

# プロジェクト設定
ISSUE_NUMBER ?= $(shell git branch --show-current | grep -o 'issue-[0-9]*' | grep -o '[0-9]*' || echo "unknown")

# カバレッジ設定
COVERAGE_TARGET = 90
CRITICAL_COVERAGE_TARGET = 90
IMPORTANT_COVERAGE_TARGET = 80
SUPPORTIVE_COVERAGE_TARGET = 60

.PHONY: help setup clean test lint coverage quality-check

# デフォルトターゲット
help:
	@echo "Kumihan-Formatter Build System"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make setup         - 開発環境セットアップ"
	@echo "  make test          - 全テスト実行"
	@echo "  make lint          - コード品質チェック"
	@echo "  make coverage      - カバレッジレポート生成"
	@echo "  make clean         - 一時ファイル削除"
	@echo ""
	@echo ""
	@echo "品質管理:"
	@echo "  make quality-check             - 品質ゲートチェック"
	@echo "  make pre-commit                - コミット前チェック"

# 基本コマンド実装
setup:
	@echo "🚀 開発環境セットアップ中..."
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	@echo "✅ セットアップ完了"

test:
	@echo "🧪 全テスト実行中..."
	$(PYTEST) --tb=short -v
	@echo "✅ テスト実行完了"

lint:
	@echo "🔍 コード品質チェック中..."
	$(PYTHON) -m black --check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m isort --check-only $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m flake8 $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m mypy $(SRC_DIR)
	@echo "✅ リントチェック完了"

coverage:
	@echo "📊 カバレッジレポート生成中..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing --cov-report=json
	@echo "✅ カバレッジレポート生成完了"

clean:
	@echo "🧹 一時ファイル削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.json
	rm -rf .pytest_cache/
	@echo "✅ クリーンアップ完了"


# 品質管理コマンド
quality-check:
	@echo "🚦 品質ゲートチェック実行中..."
	@$(PYTHON) $(SCRIPTS_DIR)/quality_gate_checker.py
	@echo "✅ 品質ゲートチェック完了"

pre-commit: lint quality-check test
	@echo "✅ コミット前チェック完了"

# 開発用便利コマンド

install-hooks:
	@echo "🪝 Git hooks インストール中..."
	@cp scripts/pre-commit-hook .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Git hooks インストール完了"

# CI/CD用コマンド
ci-test:
	@echo "🔄 CI/CDテスト実行中..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=xml --cov-fail-under=$(COVERAGE_TARGET) --maxfail=5
	@echo "✅ CI/CDテスト完了"

ci-quality:
	@echo "🔍 CI/CD品質チェック中..."
	@$(PYTHON) $(SCRIPTS_DIR)/quality_gate_checker.py --ci-mode
	@echo "✅ CI/CD品質チェック完了"

# セキュリティテストコマンド
security-test:
	@echo "🛡️ セキュリティテスト実行中..."
	@$(PYTHON) $(SCRIPTS_DIR)/security_sql_injection_test.py
	@$(PYTHON) $(SCRIPTS_DIR)/security_xss_test.py  
	@$(PYTHON) $(SCRIPTS_DIR)/security_csrf_test.py
	@$(PYTHON) $(SCRIPTS_DIR)/security_file_upload_test.py
	@echo "✅ セキュリティテスト完了"

# デバッグ用コマンド  
debug-coverage:
	@echo "🐛 カバレッジデバッグ情報表示..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing:skip-covered --cov-branch -v

