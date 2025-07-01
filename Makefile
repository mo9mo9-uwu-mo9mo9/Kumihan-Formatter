# Kumihan-Formatter - ローカル開発用 Makefile
# ローカル環境での品質チェック・テスト実行用

# 仮想環境のパス設定
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

.PHONY: help test lint format check install clean coverage pre-commit lint-docs

# デフォルトターゲット：ヘルプ表示
help:
	@echo "Kumihan-Formatter - ローカル開発用コマンド"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  make test       - テスト実行（pytest）"
	@echo "  make lint       - リンター実行（コード品質チェック）"
	@echo "  make format     - コードフォーマット実行"
	@echo "  make check      - フォーマット・リンター確認のみ（変更なし）"
	@echo "  make coverage   - カバレッジ付きテスト実行（HTMLレポート生成）"
	@echo "  make pre-commit - 🚀 コミット前品質チェック（カバレッジ100%必須）"
	@echo "  make lint-docs  - ドキュメントリンクチェック"
	@echo "  make install    - 開発用依存関係インストール"
	@echo "  make clean      - 一時ファイル・キャッシュ削除"
	@echo ""
	@echo "注意："
	@echo "  - 仮想環境（.venv）がアクティブになっていることを確認してください"
	@echo "  - CI/CD環境ではなく、ローカル開発用です"

# テスト実行
test:
	@echo "=== テスト実行 ==="
	$(PYTEST) -v

# カバレッジ付きテスト実行
coverage:
	@echo "=== カバレッジ付きテスト実行 ==="
	$(PYTEST) --cov=kumihan_formatter --cov-report=html --cov-report=term
	@echo "HTMLレポートは htmlcov/index.html で確認できます"

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

# 🚀 コミット前品質チェック（カバレッジ100%必須）
pre-commit: clean format lint
	@echo "=== 🚀 コミット前品質チェック ==="
	@echo "1. カバレッジ100%テスト実行..."
	$(PYTEST) --cov=kumihan_formatter --cov-report=term --cov-fail-under=100 --cov-report=html
	@echo ""
	@echo "🎉 品質チェック完了！"
	@echo "✅ フォーマット: 適用済み"
	@echo "✅ リニット: 合格"
	@echo "✅ テスト: 全て成功"
	@echo "✅ カバレッジ: 100%達成"
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

# 全体的な品質チェック（開発完了前の最終確認用）
all: clean format test
	@echo "=== 全体品質チェック完了 ==="
	@echo "コミット準備完了 ✓"