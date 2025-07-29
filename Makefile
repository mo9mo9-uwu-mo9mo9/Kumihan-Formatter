# Kumihan-Formatter Makefile
# Issue #640 Phase 2: TDD実行基盤実装

# Python環境設定
PYTHON = python3
PYTEST = $(PYTHON) -m pytest
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)
TEST_DIR = tests
SCRIPTS_DIR = scripts

# TDD設定
TDD_SESSION_FILE = .tdd_session.json
TDD_SPEC_TEMPLATE = scripts/tdd_spec_template.py
TDD_LOG_DIR = .tdd_logs
ISSUE_NUMBER ?= $(shell git branch --show-current | grep -o 'issue-[0-9]*' | grep -o '[0-9]*' || echo "unknown")

# カバレッジ設定
COVERAGE_TARGET = 80
CRITICAL_COVERAGE_TARGET = 95
IMPORTANT_COVERAGE_TARGET = 85

.PHONY: help setup clean test lint coverage tdd-start tdd-spec tdd-red tdd-green tdd-refactor tdd-complete tdd-status quality-check

# デフォルトターゲット
help:
	@echo "Kumihan-Formatter TDD実行基盤 - Issue #640 Phase 2"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make setup         - 開発環境セットアップ"
	@echo "  make test          - 全テスト実行"
	@echo "  make lint          - コード品質チェック"
	@echo "  make coverage      - カバレッジレポート生成"
	@echo "  make clean         - 一時ファイル削除"
	@echo ""
	@echo "TDD専用コマンド:"
	@echo "  make tdd-start <ISSUE_NUMBER>  - Issue番号からTDDセッション開始"
	@echo "  make tdd-spec                  - テスト仕様テンプレート生成"
	@echo "  make tdd-red                   - Red phase: テスト失敗確認"
	@echo "  make tdd-green                 - Green phase: 最小実装"
	@echo "  make tdd-refactor              - Refactor phase: 品質改善"
	@echo "  make tdd-complete              - TDDサイクル完了・品質確認"
	@echo "  make tdd-status                - 現在のTDDセッション状況表示"
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
	rm -rf $(TDD_LOG_DIR)/
	rm -f $(TDD_SESSION_FILE)
	@echo "✅ クリーンアップ完了"

# TDD専用コマンド実装
tdd-start:
	@echo "🎯 TDDセッション開始 - Issue #$(ISSUE_NUMBER)"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_session_manager.py start --issue=$(ISSUE_NUMBER)
	@echo "✅ TDDセッション開始完了"

tdd-spec:
	@echo "📋 テスト仕様テンプレート生成中..."
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_spec_generator.py
	@echo "✅ テスト仕様テンプレート生成完了"

tdd-red:
	@echo "🔴 TDD Red Phase: テスト失敗確認"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_cycle_manager.py red
	@echo "✅ Red Phase完了"

tdd-green:
	@echo "🟢 TDD Green Phase: 最小実装"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_cycle_manager.py green
	@echo "✅ Green Phase完了"

tdd-refactor:
	@echo "🔵 TDD Refactor Phase: 品質改善"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_cycle_manager.py refactor
	@echo "✅ Refactor Phase完了"

tdd-complete:
	@echo "🏁 TDDサイクル完了・品質確認"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_cycle_manager.py complete
	@echo "✅ TDDサイクル完了"

tdd-security:
	@echo "🔒 TDD Security Phase: セキュリティテスト実行"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_security_test.py
	@echo "✅ Security Phase完了"

tdd-status:
	@echo "📊 現在のTDDセッション状況"
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_session_manager.py status

# 品質管理コマンド
quality-check:
	@echo "🚦 品質ゲートチェック実行中..."
	@$(PYTHON) $(SCRIPTS_DIR)/quality_gate_checker.py
	@echo "✅ 品質ゲートチェック完了"

pre-commit: lint quality-check test
	@echo "✅ コミット前チェック完了"

# 開発用便利コマンド
watch-tests:
	@echo "👀 テストファイル監視開始..."
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_automation.py

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

# デバッグ用コマンド  
debug-coverage:
	@echo "🐛 カバレッジデバッグ情報表示..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing:skip-covered --cov-branch -v

debug-tdd:
	@echo "🐛 TDDセッション詳細表示..."
	@$(PYTHON) $(SCRIPTS_DIR)/tdd_session_manager.py debug