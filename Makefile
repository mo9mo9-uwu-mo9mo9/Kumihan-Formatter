# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint test test-unit test-integration test-performance test-coverage claude-check pre-commit

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
	@echo "  make claude-check  - CLAUDE.md管理・検証"
	@echo "  make pre-commit    - pre-commitフック実行"
	@echo "  make check-tmp-rule - tmp/配下強制ルール違反チェック"
	@echo "  make enforce-tmp-rule - tmp/配下強制ルール適用（対話的）"
	@echo "  make enforce-tmp-rule-auto - tmp/配下強制ルール適用（自動）"
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

# CLAUDE.md管理システム
claude-check:
	@echo "📋 CLAUDE.md管理・検証中..."
	@$(PYTHON) -c "import os, sys; \
	CLAUDE_MD = 'CLAUDE.md'; \
	RECOMMENDED_LINES = 150; RECOMMENDED_BYTES = 8192; \
	WARNING_LINES = 200; WARNING_BYTES = 10240; \
	content = open(CLAUDE_MD, 'r', encoding='utf-8').read() if os.path.exists(CLAUDE_MD) else ''; \
	lines = len(content.splitlines()); bytes_count = len(content.encode('utf-8')); \
	sections = content.count('#'); deep_nesting = content.count('####'); \
	print(f'📊 CLAUDE.md Statistics:'); \
	print(f'   Lines: {lines}'); print(f'   Bytes: {bytes_count} ({bytes_count/1024:.1f}KB)'); \
	print(f'   Sections: {sections}'); print(f'   Deep nesting: {deep_nesting}'); \
	status = '✅ GOOD'; \
	exit_code = 0; \
	(print(f'🚨 CRITICAL: Size limit exceeded!'), globals().update(status='🚨 CRITICAL', exit_code=1)) if lines > WARNING_LINES or bytes_count > WARNING_BYTES else None; \
	(print(f'⚠️  WARNING: Approaching limits'), globals().update(status='⚠️  WARNING')) if lines > RECOMMENDED_LINES or bytes_count > RECOMMENDED_BYTES and exit_code == 0 else None; \
	print(f'⚠️  WARNING: Too much nesting') if deep_nesting > 10 else None; \
	print(f'📊 Overall Status: {status}'); \
	sys.exit(exit_code)"
	@echo "✅ CLAUDE.md検証完了"

pre-commit:
	@echo "🔒 pre-commitフック実行中..."
	@$(PYTHON) -c "import subprocess, sys; \
	result = subprocess.run(['make', 'claude-check'], capture_output=True, text=True); \
	print('📋 CLAUDE.md Check:', '✅ PASSED' if result.returncode == 0 else '❌ FAILED'); \
	result2 = subprocess.run(['make', 'lint'], capture_output=True, text=True); \
	print('🔍 Lint Check:', '✅ PASSED' if result2.returncode == 0 else '❌ FAILED'); \
	sys.exit(max(result.returncode, result2.returncode))"
	@echo "✅ pre-commitフック完了"

# 拡張ファイル整理システム
deep-clean:
	@echo "🧹 完全クリーンアップ実行中..."
	$(PYTHON) scripts/cleanup.py --auto
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf build/
	rm -rf dist/
	rm -rf .cache/
	rm -rf .performance_cache/
	rm -rf .quality_data/
	rm -rf .benchmarks/
	@echo "✅ 完全クリーンアップ完了"

organize:
	@echo "📁 ファイル整理実行中..."
	$(PYTHON) scripts/file-organizer.py --interactive
	@echo "✅ ファイル整理完了"

organize-auto:
	@echo "🤖 自動ファイル整理実行中..."
	$(PYTHON) scripts/file-organizer.py --organize
	@echo "✅ 自動ファイル整理完了"

scan-files:
	@echo "🔍 ファイルスキャン実行中..."
	$(PYTHON) scripts/file-organizer.py --scan
	@echo "✅ ファイルスキャン完了"

find-duplicates:
	@echo "🔍 重複ファイル検出実行中..."
	$(PYTHON) scripts/file-organizer.py --duplicates
	@echo "✅ 重複ファイル検出完了"

cleanup-preview:
	@echo "👀 クリーンアップ対象プレビュー中..."
	$(PYTHON) scripts/cleanup.py --dry-run
	@echo "✅ プレビュー完了"

cleanup-interactive:
	@echo "💬 対話的クリーンアップ実行中..."
	$(PYTHON) scripts/cleanup.py --interactive
	@echo "✅ 対話的クリーンアップ完了"

# tmp/配下強制ルール関連タスク
check-tmp-rule:
	@echo "🔍 tmp/配下強制ルール違反チェック中..."
	$(PYTHON) scripts/cleanup.py --check-tmp-rule
	@echo "✅ tmp/配下強制ルールチェック完了"

enforce-tmp-rule:
	@echo "🔧 tmp/配下強制ルール適用中..."
	$(PYTHON) scripts/cleanup.py --enforce-tmp-rule
	@echo "✅ tmp/配下強制ルール適用完了"

enforce-tmp-rule-auto:
	@echo "🤖 tmp/配下強制ルール自動適用中..."
	$(PYTHON) scripts/cleanup.py --enforce-tmp-rule-auto
	@echo "✅ tmp/配下強制ルール自動適用完了"

tmp-organizer:
	@echo "📁 tmp/配下強制ルール（file-organizer版）適用中..."
	$(PYTHON) scripts/file-organizer.py --enforce-tmp-rule
	@echo "✅ tmp/配下強制ルール（file-organizer版）適用完了"
