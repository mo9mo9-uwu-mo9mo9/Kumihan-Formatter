# Kumihan-Formatter - 簡潔で効果的な開発用 Makefile
# Issue #590対応: 必要最小限のコマンドに整理

# 仮想環境のパス設定
VENV = .venv
PYTHON = $(VENV)/bin/python
PYTEST = $(VENV)/bin/pytest

.PHONY: help test lint format check install clean coverage quality-gate pre-commit ci-critical ci-important ci-full platform-check

# デフォルトターゲット：ヘルプ表示
help:
	@echo "Kumihan-Formatter - 簡潔な開発コマンド"
	@echo ""
	@echo "必須コマンド："
	@echo "  make test         - テスト実行"
	@echo "  make lint         - リンター実行（チェックのみ）"
	@echo "  make format       - コードフォーマット適用"
	@echo "  make check        - format + lint + test（開発完了時）"
	@echo "  make pre-commit   - コミット前チェック（Issue #589対応）"
	@echo ""
	@echo "品質管理（Issue #589新機能）:"
	@echo "  make quality-gate - ティア別品質ゲート実行"
	@echo "  make coverage     - カバレッジ付きテスト"
	@echo ""
	@echo "CI最適化（Issue #610新機能）:"
	@echo "  make ci-critical  - Critical Tierテスト（2-4分）"
	@echo "  make ci-important - Important Tierテスト（5-8分）"
	@echo "  make ci-full      - 全テスト実行（10-15分）"
	@echo "  make platform-check - プラットフォーム互換性診断"
	@echo ""
	@echo "その他:"
	@echo "  make install      - 開発用依存関係インストール"
	@echo "  make clean        - 一時ファイル削除"

# テスト実行
test:
	@echo "=== テスト実行 ==="
	$(PYTEST)

# リンター実行（チェックのみ）
lint:
	@echo "=== リンター実行 ==="
	$(PYTHON) -m black --check kumihan_formatter/
	$(PYTHON) -m isort --check-only kumihan_formatter/
	$(PYTHON) -m flake8 kumihan_formatter/ --select=E9,F63,F7,F82 --count
	@echo "リンターチェック完了 ✓"

# コードフォーマット適用
format:
	@echo "=== コードフォーマット実行 ==="
	$(PYTHON) -m black kumihan_formatter/
	$(PYTHON) -m isort kumihan_formatter/
	@echo "フォーマット完了 ✓"

# 開発完了時の統合チェック
check: format lint test
	@echo "=== 開発完了チェック完了 ✓ ==="

# カバレッジ付きテスト
coverage:
	@echo "=== カバレッジ付きテスト実行 ==="
	$(PYTEST) --cov=kumihan_formatter --cov-report=html
	@echo "HTMLレポートは htmlcov/index.html で確認できます"

# 開発用依存関係インストール
install:
	@echo "=== 開発用依存関係インストール ==="
	pip install -e .[dev]
	@echo "インストール完了 ✓"

# Issue #589: ティア別品質ゲート（新システム）
quality-gate:
	@echo "=== ティア別品質ゲート実行 ==="
	$(PYTHON) scripts/tiered_quality_gate.py
	@echo "品質ゲートチェック完了 ✓"

# Issue #589: コミット前チェック（統合）
pre-commit: format lint test
	@echo "=== コミット前チェック完了 ✓ ==="
	@echo "安全にコミットできます"

# 一時ファイル削除
clean:
	@echo "=== 一時ファイル削除 ==="
	rm -rf .pytest_cache/ __pycache__/ *.pyc htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "クリーンアップ完了 ✓"

# Issue #610: CI最適化コマンド
ci-critical:
	@echo "=== Critical Tier テスト（並列実行）==="
	$(PYTHON) scripts/ci_optimizer.py critical
	@echo "Critical Tier完了 ✓"

ci-important:
	@echo "=== Important Tier テスト（並列実行）==="
	$(PYTHON) scripts/ci_optimizer.py important
	@echo "Important Tier完了 ✓"

ci-full:
	@echo "=== 全テスト実行（並列最適化）==="
	$(PYTHON) scripts/ci_optimizer.py all
	@echo "全テスト完了 ✓"

platform-check:
	@echo "=== プラットフォーム互換性診断 ==="
	$(PYTHON) scripts/cross_platform_diagnostics.py --output platform_diagnosis.json
	@echo "プラットフォーム診断完了 ✓"
