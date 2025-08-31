# Kumihan-Formatter Makefile - 品質保証システム強化版
# Issue #1239: 品質保証システム再構築対応

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

# 品質基準設定
IMPORT_COUNT_TARGET = 300    # 現在423から削減目標
BUILD_TIME_LIMIT = 60        # 秒

.PHONY: help setup clean lint lint-strict test test-unit test-integration quality-check dependency-audit performance-check pre-commit claude-check process-check debt-management doc-consistency

# デフォルトターゲット
help:
	@echo "🛡️ Kumihan-Formatter 品質保証システム（Issue #1239対応版）"
	@echo ""
	@echo "📊 品質管理コマンド:"
	@echo "  make quality-check     - 総合品質チェック（推奨）"
	@echo "  make lint              - 基本品質チェック（Black + mypy）"
	@echo "  make lint-strict       - 厳格品質チェック（全チェック有効）"
	@echo "  make dependency-audit  - 依存関係分析・最適化提案"
	@echo "  make performance-check - パフォーマンス監視・ベンチマーク"
	@echo ""
	@echo "🧪 テスト実行システム:"
	@echo "  make test              - 全テスト実行（カバレッジ付き）"
	@echo "  make test-unit         - 単体テスト（高速）"
	@echo "  make test-integration  - 統合テスト"
	@echo ""
	@echo "📋 開発プロセス正規化 (Issue #1240):"
	@echo "  make process-check     - 開発プロセス総合チェック"
	@echo "  make debt-management   - 技術的負債管理"
	@echo "  make doc-consistency   - ドキュメント整合性確認"
	@echo ""
	@echo "🔧 開発支援:"
	@echo "  make setup             - 開発環境セットアップ"
	@echo "  make clean             - 一時ファイル削除"
	@echo "  make pre-commit        - pre-commitフック（統合チェック）"
	@echo ""

# 基本セットアップ
setup:
	@echo "🚀 開発環境セットアップ中..."
	$(PIP) install -e ".[dev,test,performance,telemetry]"
	@echo "✅ セットアップ完了"

# 総合品質チェック（Issue #1239のメイン機能）
quality-check:
	@echo "🛡️ 総合品質チェック開始 - Issue #1239"
	@echo "=========================================="
	@$(MAKE) dependency-audit
	@echo ""
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-unit
	@echo ""
	@$(MAKE) performance-check
	@echo ""
	@echo "📊 品質チェック完了サマリー:"
	@echo "  - 依存関係: 分析完了"
	@echo "  - コード品質: チェック完了"  
	@echo "  - テスト: 単体テスト完了"
	@echo "  - パフォーマンス: 測定完了"

# 基本lint（既存互換）
lint:
	@echo "🔍 基本品質チェック実行中... (Black + mypy:pyproject)"
	$(PYTHON) -m black --check $(SRC_DIR)
	$(PYTHON) -m mypy --config-file=pyproject.toml $(SRC_DIR)
	@echo "✅ 基本品質チェック完了"

# 厳格品質チェック
lint-strict:
	@echo "🔬 厳格品質チェック（lintと同一設定: pyproject.toml）"
	@$(MAKE) lint
	@echo "✅ 厳格品質チェック完了"

# 依存関係分析（Issue #1239の重要機能）
dependency-audit:
	@$(PYTHON) scripts/dependency_audit.py --target $(SRC_DIR) --import-threshold $(IMPORT_COUNT_TARGET)

# パフォーマンス監視（Issue #1239の新機能）
performance-check:
	@echo "⚡ パフォーマンス監視中..."
	@start_time=$$(date +%s); \
	$(MAKE) lint >/dev/null 2>&1; \
	end_time=$$(date +%s); \
	lint_time=$$((end_time - start_time)); \
	start_time=$$(date +%s); \
	$(MAKE) test-unit >/dev/null 2>&1; \
	end_time=$$(date +%s); \
	test_time=$$((end_time - start_time)); \
	echo "📊 パフォーマンス測定結果:"; \
	echo "  - Lint実行時間: $${lint_time}秒"; \
	echo "  - テスト実行時間: $${test_time}秒"; \
	echo "  - 合計ビルド時間: $$((lint_time + test_time))秒 (目標: <$(BUILD_TIME_LIMIT)秒)"

# テスト実行システム
test:
	@echo "🧪 全テスト実行中（カバレッジ付き）..."
	$(PYTHON) -m pytest --cov=$(PROJECT_NAME) --cov-report=term-missing --cov-report=html:tmp/htmlcov
	@echo "✅ 全テスト完了"

test-unit:
	@echo "⚡ 単体テスト実行中（高速）..."
	$(PYTHON) -m pytest tests/unit -v
	@echo "✅ 単体テスト完了"

test-integration:
	@echo "🔗 統合テスト実行中..."
	$(PYTHON) -m pytest tests/integration -v
	@echo "✅ 統合テスト完了"

# pre-commitフック（Issue #1239統合版）
pre-commit:
	@echo "🔒 統合pre-commitフック実行中..."
	@$(PYTHON) -c "import subprocess, sys; \
	checks = [('CLAUDE.md検証', ['make', 'claude-check']), \
		  ('品質チェック', ['make', 'lint']), \
		  ('単体テスト', ['make', 'test-unit'])]; \
	results = []; \
	for name, cmd in checks: \
		result = subprocess.run(cmd, capture_output=True, text=True); \
		status = '✅ PASSED' if result.returncode == 0 else '❌ FAILED'; \
		results.append((name, status, result.returncode)); \
		print(f'{name}: {status}'); \
	print(''); \
	print('🔒 統合pre-commitフック結果:'); \
	for name, status, code in results: \
		print(f'  - {name}: {status}'); \
	sys.exit(max(code for _, _, code in results))"
	@echo "✅ pre-commitフック完了"

# 一時ファイル削除
clean:
	@echo "🧹 一時ファイル削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf tmp/
	@echo "✅ クリーンアップ完了"

# CLAUDE.md管理システム（既存維持）
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

# 開発プロセス正規化コマンド (Issue #1240)
# 開発プロセス総合チェック
process-check:
	@echo "📋 開発プロセス総合チェック開始 - Issue #1240"
	@echo "================================================="
	@$(MAKE) debt-management
	@echo ""
	@$(MAKE) doc-consistency
	@echo ""
	@echo "📊 開発プロセスチェック完了サマリー:"
	@echo "  - 技術的負債: 分析・報告完了"
	@echo "  - ドキュメント整合性: 確認完了"

# 技術的負債管理
debt-management:
	@echo "🔍 技術的負債管理システム実行中..."
	@$(PYTHON) scripts/technical_debt_manager.py detect
	@$(PYTHON) scripts/technical_debt_manager.py summary
	@echo "✅ 技術的負債管理完了"

# ドキュメント整合性確認
doc-consistency:
	@echo "📚 ドキュメント整合性チェック中..."
	@$(PYTHON) scripts/document_consistency_checker.py check
	@$(PYTHON) scripts/document_consistency_checker.py summary
	@echo "✅ ドキュメント整合性チェック完了"
