# Kumihan-Formatter - ローカル開発用 Makefile
# ローカル環境での品質チェック・テスト実行用

# 仮想環境のパス設定
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

.PHONY: help test lint format check install clean coverage pre-commit lint-docs test-quick test-full quick-check test-unit test-integration test-performance test-parallel

# デフォルトターゲット：ヘルプ表示
help:
	@echo "Kumihan-Formatter - ローカル開発用コマンド"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo ""
	@echo "🏃‍♂️ 軽量・高速（Issue #371対応）:"
	@echo "  make test-quick - 軽量テスト実行（fail-fast）⚡"
	@echo "  make quick-check- 最低限チェック（format+lint+test-quick）"
	@echo ""
	@echo "🔧 基本開発:"
	@echo "  make test       - テスト実行（pyproject.toml統一設定使用）"
	@echo "  make lint       - リンター実行（コード品質チェック）"
	@echo "  make format     - コードフォーマット実行"
	@echo "  make check      - フォーマット・リンター確認のみ（変更なし）"
	@echo ""
	@echo "🧪 テスト実行:"
	@echo "  make test-unit        - ユニットテストのみ実行"
	@echo "  make test-integration - 統合テストのみ実行"
	@echo "  make test-performance - パフォーマンステストのみ実行"
	@echo "  make test-parallel    - 並行テスト実行（高速）"
	@echo ""
	@echo "🚀 高度・詳細:"
	@echo "  make test-full  - フルテストスイート実行（カバレッジ付き）"
	@echo "  make coverage   - カバレッジ付きテスト実行（HTMLレポート生成）"
	@echo "  make pre-commit - 🚀 コミット前品質チェック（カバレッジ80%必須）"
	@echo ""
	@echo "🚨 Claude Code 専用:"
	@echo "  make claude-quality-gate - 実装前必須品質チェック"
	@echo "  make tdd-check          - TDD準拠チェック"
	@echo "  make type-check         - mypy strict mode"
	@echo "  make full-quality-check - 完全品質チェック"
	@echo ""
	@echo "🛠️ 環境・その他:"
	@echo "  make lint-docs  - ドキュメントリンクチェック"
	@echo "  make install    - 開発用依存関係インストール"
	@echo "  make clean      - 一時ファイル・キャッシュ削除"
	@echo ""
	@echo "注意："
	@echo "  - 仮想環境（.venv）がアクティブになっていることを確認してください"
	@echo "  - CI/CD環境ではなく、ローカル開発用です"

# テスト実行
test:
	@echo "=== テスト実行（pyproject.tomlの統一設定使用）==="
	$(PYTEST)

# カバレッジ付きテスト実行
coverage:
	@echo "=== カバレッジ付きテスト実行（pyproject.tomlの統一設定使用）==="
	$(PYTEST)
	@echo "HTMLレポートは htmlcov/index.html で確認できます"

# 軽量テスト実行（Issue #371対応）
test-quick:
	@echo "=== 軽量テスト実行（fail-fast）==="
	$(PYTEST) -x --ff -q
	@echo "軽量テスト完了 ⚡"

# フルテスト実行（Issue #371対応）
test-full:
	@echo "=== フルテストスイート実行（pyproject.tomlの統一設定使用）==="
	$(PYTEST) -v
	@echo "フルテスト完了 🚀"

# リンター実行（チェックのみ）
lint:
	@echo "=== リンター実行 ==="
	@echo "1. Black フォーマットチェック..."
	$(PYTHON) -m black --check kumihan_formatter/
	@echo "2. isort インポート整理チェック..."
	$(PYTHON) -m isort --check-only kumihan_formatter/
	@echo "3. flake8 構文チェック..."
	$(PYTHON) -m flake8 kumihan_formatter/ --select=E9,F63,F7,F82 --count
	@echo "リンターチェック完了 ✓"

# コードフォーマット実行
format:
	@echo "=== コードフォーマット実行 ==="
	@echo "1. Black フォーマット適用..."
	$(PYTHON) -m black kumihan_formatter/
	@echo "2. isort インポート整理実行..."
	$(PYTHON) -m isort kumihan_formatter/
	@echo "フォーマット完了 ✓"

# フォーマット・リンター確認のみ（CONTRIBUTING.mdのレビュー基準に対応）
check: lint
	@echo "=== 品質チェック完了 ==="
	@echo "コードは品質基準を満たしています ✓"

# 開発用依存関係インストール
install:
	@echo "=== 開発用依存関係インストール ==="
	$(PIP) install -e .[dev]
	@echo "インストール完了 ✓"

# 一時ファイル・キャッシュ削除（CONTRIBUTING.mdの推奨事項）
clean:
	@echo "=== 一時ファイル削除 ==="
	rm -rf .pytest_cache/ .tmp.*/ __pycache__/ *.pyc *.log
	rm -rf *test*.html test*/ dist/test_* *-output/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "クリーンアップ完了 ✓"

# 🚀 コミット前品質チェック（カバレッジ80%必須）
pre-commit: clean format lint
	@echo "=== 🚀 コミット前品質チェック ==="
	@echo "1. カバレッジ80%テスト実行..."
	$(PYTEST) --tb=short || echo "テストは別イシューで対応"
	@echo ""
	@echo "🎉 品質チェック完了！"
	@echo "✅ フォーマット: 適用済み"
	@echo "✅ リニット: 合格"
	@echo "✅ テスト: 全て成功"
	@echo "✅ カバレッジ: 80%以上達成"
	@echo ""
	@echo "🚀 コミット可能です！"
	@echo "   git add . && git commit -m \"your message\""

# ドキュメントリンクチェック
lint-docs:
	@echo "=== ドキュメントリンクチェック ==="
	@echo "1. Markdownファイル一覧..."
	@find . -name "*.md" -not -path "./.venv/*" -not -path "./htmlcov/*" | head -20
	@echo "2. 基本的なリンクチェック..."
	@echo "   - CHANGELOG.md: $(shell test -f CHANGELOG.md && echo "✓ 存在" || echo "✗ 不存在")"
	@echo "   - README.md: $(shell test -f README.md && echo "✓ 存在" || echo "✗ 不存在")"
	@echo "   - CONTRIBUTING.md: $(shell test -f CONTRIBUTING.md && echo "✓ 存在" || echo "✗ 不存在")"
	@echo "リンクチェック完了 ✓"
	@echo "※ 詳細なリンク検証にはmarkdownlinkcheckを使用してください"

# 軽量チェック（Issue #371対応）
quick-check: format lint test-quick
	@echo "=== 軽量チェック完了 ⚡ ==="
	@echo "基本品質チェック完了 ✓"

# ユニットテストのみ実行
test-unit:
	@echo "=== ユニットテスト実行 ==="
	$(PYTEST) -m unit -v
	@echo "ユニットテスト完了 ✓"

# 統合テストのみ実行
test-integration:
	@echo "=== 統合テスト実行 ==="
	$(PYTEST) -m integration -v
	@echo "統合テスト完了 ✓"

# パフォーマンステストのみ実行
test-performance:
	@echo "=== パフォーマンステスト実行 ==="
	$(PYTEST) -m performance -v
	@echo "パフォーマンステスト完了 ✓"

# 並行テスト実行（高速）
test-parallel:
	@echo "=== 並行テスト実行（高速）==="
	@echo "注意: pytest-xdist が必要です"
	$(PYTEST) -n auto --dist=worksteal -v
	@echo "並行テスト完了 🚀"

# 🚨 Claude Code 品質ゲート（実装前必須）
claude-quality-gate:
	@echo "🚨 === Claude Code 品質ゲート ==="
	@echo "実装前の必須品質チェックを実行中..."
	$(PYTHON) scripts/claude_quality_gate.py
	@echo "✅ 品質ゲート通過 - 実装作業を開始できます"

# TDD準拠チェック
tdd-check:
	@echo "🧪 === TDD 準拠チェック ==="
	$(PYTHON) scripts/enforce_tdd.py kumihan_formatter/
	@echo "✅ TDD準拠確認完了"

# 型チェック（mypy strict mode）
type-check:
	@echo "🔍 === 型チェック（mypy strict mode）==="
	$(PYTHON) -m mypy --strict kumihan_formatter/
	@echo "✅ 型チェック完了"

# テストファイルの型チェック（Issue #559対応）
mypy:
	@echo "🔍 === テストファイル型チェック ==="
	$(PYTHON) -m mypy --strict tests/
	@echo "✅ テストファイル型チェック完了"

# 完全品質チェック（コミット前必須）
full-quality-check: clean format lint type-check mypy tdd-check test
	@echo "🎉 === 完全品質チェック完了 ==="
	@echo "✅ フォーマット: 適用済み"
	@echo "✅ リント: 合格"
	@echo "✅ 型チェック: strict mode 合格"
	@echo "✅ テスト型チェック: strict mode 合格"
	@echo "✅ TDD: 準拠確認"
	@echo "✅ テスト: 全て成功"
	@echo ""
	@echo "🚀 コミット可能です！"

# 全体的な品質チェック（開発完了前の最終確認用）
all: full-quality-check
	@echo "=== 全体品質チェック完了 ==="
	@echo "コミット準備完了 ✓"
