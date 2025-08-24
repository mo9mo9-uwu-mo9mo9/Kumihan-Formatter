# Kumihan-Formatter Makefile - シンプル版（個人開発最適化）

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint claude-check test test-unit

# デフォルトターゲット
help:
	@echo "Kumihan-Formatter Build System（シンプル版）"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make setup         - 開発環境セットアップ"
	@echo "  make lint          - コード品質チェック（Black + mypy）"
	@echo "  make clean         - 一時ファイル削除"
	@echo "  make claude-check  - CLAUDE.md管理・検証"
	@echo ""
	@echo "🧪 テスト実行システム（シンプル版）:"
	@echo "  make test          - 基本テスト実行"
	@echo "  make test-unit     - 単体テストのみ（高速）"
	@echo ""

# 基本コマンド実装
setup:
	@echo "🚀 開発環境セットアップ中..."
	$(PIP) install -e ".[dev,test]"
	@echo "✅ セットアップ完了"

lint:
	@echo "🔍 シンプル品質チェック実行中..."
	$(PYTHON) -m black --check $(SRC_DIR)
	$(PYTHON) -m mypy $(SRC_DIR) --ignore-missing-imports
	@echo "✅ 品質チェック完了"

clean:
	@echo "🧹 一時ファイル削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf tmp/
	@echo "✅ クリーンアップ完了"

# テスト実行システム（シンプル版）
test:
	@echo "🧪 基本テスト実行中..."
	$(PYTHON) -m pytest
	@echo "✅ テスト完了"

test-unit:
	@echo "⚡ 単体テスト実行中（高速）..."
	$(PYTHON) -m pytest tests/unit
	@echo "✅ 単体テスト完了"

# CLAUDE.md管理システム
claude-check:
	@echo "📋 CLAUDE.md管理・検証中..."
	@$(PYTHON) -c "import os, sys; \
	CLAUDE_MD = 'CLAUDE.md'; \
	RECOMMENDED_LINES = 150; RECOMMENDED_BYTES = 8192; \
	WARNING_LINES = 250; WARNING_BYTES = 12288; \
	CAUTION_LINES = 300; CAUTION_BYTES = 15360; \
	CRITICAL_LINES = 400; CRITICAL_BYTES = 20480; \
	content = open(CLAUDE_MD, 'r', encoding='utf-8').read() if os.path.exists(CLAUDE_MD) else ''; \
	lines = len(content.splitlines()); bytes_count = len(content.encode('utf-8')); \
	sections = content.count('#'); deep_nesting = content.count('####'); \
	print(f'📊 CLAUDE.md Statistics (段階制限システム):'); \
	print(f'   Lines: {lines} (推奨≤{RECOMMENDED_LINES}, 警告≤{WARNING_LINES}, 注意≤{CAUTION_LINES}, 限界≤{CRITICAL_LINES})'); \
	print(f'   Bytes: {bytes_count} ({bytes_count/1024:.1f}KB) (推奨≤{RECOMMENDED_BYTES/1024:.1f}KB, 警告≤{WARNING_BYTES/1024:.1f}KB, 注意≤{CAUTION_BYTES/1024:.1f}KB, 限界≤{CRITICAL_BYTES/1024:.1f}KB)'); \
	print(f'   Sections: {sections}, Deep nesting: {deep_nesting}'); \
	status = '✅ GOOD'; exit_code = 0; \
	(print(f'🚨 CRITICAL: Critical limit exceeded! Immediate action required.'), globals().update(status='🚨 CRITICAL', exit_code=1)) if lines > CRITICAL_LINES or bytes_count > CRITICAL_BYTES else None; \
	(print(f'⚠️ CAUTION: Caution limit exceeded. Consider content reduction.'), globals().update(status='⚠️ CAUTION')) if (lines > CAUTION_LINES or bytes_count > CAUTION_BYTES) and exit_code == 0 else None; \
	(print(f'💡 WARNING: Warning limit exceeded. Review recommended.'), globals().update(status='💡 WARNING')) if (lines > WARNING_LINES or bytes_count > WARNING_BYTES) and exit_code == 0 else None; \
	(print(f'📝 INFO: Recommended limit exceeded. Consider optimization.'), globals().update(status='📝 INFO')) if (lines > RECOMMENDED_LINES or bytes_count > RECOMMENDED_BYTES) and status == '✅ GOOD' else None; \
	print(f'⚠️ WARNING: Too much nesting') if deep_nesting > 10 else None; \
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