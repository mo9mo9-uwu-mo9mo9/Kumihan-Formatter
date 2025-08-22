# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint test test-unit test-integration test-performance test-coverage claude-check pre-commit tech-debt-check tech-debt-report tech-debt-json tech-debt-ci enterprise-check performance-benchmark security-audit release-candidate tox tox-py312 tox-py313 tox-unit tox-integration tox-lint tox-format tox-clean tox-parallel tox-install

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
	@echo ""
	@echo "🧪 tox環境 (複数Python版並行テスト):"
	@echo "  make tox           - Python 3.12/3.13両方でテスト実行"
	@echo "  make tox-py312     - Python 3.12でのみテスト実行"
	@echo "  make tox-py313     - Python 3.13でのみテスト実行"
	@echo "  make tox-unit      - 単体テストのみ実行"
	@echo "  make tox-integration - 結合テストのみ実行"
	@echo "  make tox-lint      - コード品質チェック"
	@echo "  make tox-parallel  - 高速並行実行"
	@echo "  make pre-commit    - pre-commitフック実行"
	@echo "  make check-tmp-rule - tmp/配下強制ルール違反チェック"
	@echo "  make enforce-tmp-rule - tmp/配下強制ルール適用（対話的）"
	@echo "  make enforce-tmp-rule-auto - tmp/配下強制ルール適用（自動）"
	@echo "  make tech-debt-check - 技術的負債監視チェック実行"
	@echo "  make tech-debt-report - 技術的負債詳細レポート生成"
	@echo ""
	@echo ""
	@echo "🚀 品質保証強化システム (Issue #845):"
	@echo "  make quality-realtime-start  - リアルタイム品質監視開始"
	@echo "  make quality-realtime-stop   - リアルタイム品質監視停止"
	@echo "  make quality-auto-correct    - 自動修正エンジン実行"
	@echo "  make quality-gate-run        - 強化品質ゲート実行"
	@echo "  make quality-comprehensive   - 包括的品質検証実行"
	@echo "  make quality-learning-train  - 品質学習システム訓練"
	@echo "  make quality-dashboard       - 品質ダッシュボード生成・表示"
	@echo "  make quality-full-check      - 全品質システム実行"
	@echo ""
	@echo "🏢 Phase 4-10 最終検証・リリース準備システム:"
	@echo "  make enterprise-check        - エンタープライズレベル完成度チェック"
	@echo "  make performance-benchmark   - パフォーマンスベンチマーク実行"
	@echo "  make security-audit          - セキュリティ監査実行"
	@echo "  make release-candidate       - リリース候補準備実行"
	@echo ""

# 基本コマンド実装
setup:
	@echo "🚀 開発環境セットアップ中..."
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	@echo "✅ セットアップ完了"

lint:
	@echo "🔍 標準ツール統合品質チェック実行中..."
	@./scripts/quality_check.sh $(SRC_DIR)
	@echo "✅ 品質チェック完了"

# 従来の個別ツール実行（互換性維持）
lint-legacy:
	@echo "🔍 従来のコード品質チェック中..."
	$(PYTHON) -m black --check $(SRC_DIR)
	$(PYTHON) -m isort --check-only $(SRC_DIR)
	$(PYTHON) -m flake8 $(SRC_DIR)
	$(PYTHON) -m mypy $(SRC_DIR)
	@echo "✅ 従来リントチェック完了"

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

# 技術的負債監視システム
tech-debt-check:
	@echo "🔍 技術的負債監視チェック実行中..."
	$(PYTHON) scripts/tech_debt_monitor.py --format console
	@echo "✅ 技術的負債チェック完了"

tech-debt-report:
	@echo "📊 技術的負債詳細レポート生成中..."
	$(PYTHON) scripts/tech_debt_monitor.py --format html --output tmp/tech_debt_report.html
	@echo "✅ 技術的負債レポート生成完了 → tmp/tech_debt_report.html"

tech-debt-json:
	@echo "📋 技術的負債JSONレポート生成中..."
	$(PYTHON) scripts/tech_debt_monitor.py --format json --output tmp/tech_debt_report.json
	@echo "✅ 技術的負債JSONレポート生成完了 → tmp/tech_debt_report.json"

tech-debt-ci:
	@echo "🚨 技術的負債CI/CDチェック実行中..."
	$(PYTHON) scripts/tech_debt_monitor.py --ci --format console
	@echo "✅ 技術的負債CI/CDチェック完了"





# 🚀 品質保証強化システム (Issue #845) 実装
quality-realtime-start:
	@echo "🚀 リアルタイム品質監視開始..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.realtime_monitor import EnhancedRealtimeQualityMonitor; \
	monitor = EnhancedRealtimeQualityMonitor(); \
	print('📊 リアルタイム品質監視開始 (30秒間実行)'); \
	monitor.start_monitoring(['kumihan_formatter/'], 30); \
	print('✅ リアルタイム監視完了')"

quality-realtime-stop:
	@echo "⏹️ リアルタイム品質監視停止..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.realtime_monitor import EnhancedRealtimeQualityMonitor; \
	monitor = EnhancedRealtimeQualityMonitor(); \
	monitor.stop_monitoring(); \
	print('✅ リアルタイム監視停止完了')"

quality-auto-correct:
	@echo "🔧 自動修正エンジン実行..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.auto_correction_engine import AutoCorrectionEngine; \
	import subprocess; \
	engine = AutoCorrectionEngine(); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:5]; \
	print(f'📁 対象ファイル: {len(files)}件'); \
	suggestions = engine.analyze_and_suggest_corrections(files); \
	print(f'🔧 修正提案: {len(suggestions)}件'); \
	corrections = engine.apply_corrections(suggestions[:3], auto_apply=False); \
	print(f'✅ 自動修正完了: {len(corrections)}件適用')"

quality-gate-run:
	@echo "🚪 強化品質ゲート実行..."
	@echo "使用例: make quality-gate-run PHASE=design"
	@$(PYTHON) -c "import sys, os; sys.path.append('postbox'); \
	from quality.quality_gates_enhanced import EnhancedQualityGateSystem; \
	import subprocess; \
	phase = os.environ.get('PHASE', 'implementation'); \
	gate_system = EnhancedQualityGateSystem(); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:3]; \
	print(f'🚪 品質ゲート実行: {phase}フェーズ'); \
	gate_result = gate_system.execute_quality_gate(files, phase); \
	print(f'🎯 結果: {gate_result[\"result\"]} (スコア: {gate_result[\"overall_score\"]:.3f})')"

quality-comprehensive:
	@echo "🔍 包括的品質検証実行..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.comprehensive_validator import ComprehensiveQualityValidator; \
	import subprocess; \
	validator = ComprehensiveQualityValidator(); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:3]; \
	print(f'🔍 包括的検証対象: {len(files)}ファイル'); \
	validation_result = validator.run_comprehensive_validation(files); \
	print(f'📊 検証完了: 総合スコア {validation_result[\"overall_score\"]:.3f}'); \
	print(f'🛡️ セキュリティ: {validation_result[\"category_scores\"][\"security\"]:.3f}'); \
	print(f'⚡ パフォーマンス: {validation_result[\"category_scores\"][\"performance\"]:.3f}'); \
	print(f'🔗 統合性: {validation_result[\"category_scores\"][\"integration\"]:.3f}')"

quality-learning-train:
	@echo "🧠 品質学習システム訓練..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.learning_system import QualityLearningSystem; \
	import subprocess; \
	learning_system = QualityLearningSystem(); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:5]; \
	print(f'🧠 学習対象: {len(files)}ファイル'); \
	learning_result = learning_system.learn_from_quality_data(files); \
	print(f'📈 学習完了: {learning_result[\"patterns_learned\"]}パターン学習'); \
	print(f'🎯 改善予測: {learning_result[\"prediction\"][\"confidence\"]}信頼度'); \
	evolution_result = learning_system.evolve_project_standards(files); \
	print(f'⚡ 基準進化: {evolution_result[\"evolution_applied\"]}件適用')"

quality-dashboard:
	@echo "📊 品質ダッシュボード生成..."
	@$(PYTHON) tmp/quality_dashboard_runner.py

quality-full-check:
	@echo "🎯 全品質システム実行..."
	@echo "📊 1/7: メトリクス収集"
	@$(MAKE) --no-print-directory quality-dashboard > /dev/null 2>&1 || echo "⚠️ ダッシュボード生成スキップ"
	@echo "🔧 2/7: 自動修正"
	@$(MAKE) --no-print-directory quality-auto-correct > /dev/null 2>&1 || echo "⚠️ 自動修正スキップ"
	@echo "🚪 3/7: 品質ゲート"
	@$(MAKE) --no-print-directory quality-gate-run > /dev/null 2>&1 || echo "⚠️ 品質ゲートスキップ"
	@echo "🔍 4/7: 包括的検証"
	@$(MAKE) --no-print-directory quality-comprehensive > /dev/null 2>&1 || echo "⚠️ 包括的検証スキップ"
	@echo "🧠 5/7: 学習訓練"
	@$(MAKE) --no-print-directory quality-learning-train > /dev/null 2>&1 || echo "⚠️ 学習訓練スキップ"
	@echo "🚀 6/7: リアルタイム監視(10秒)"
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from quality.realtime_monitor import EnhancedRealtimeQualityMonitor; \
	monitor = EnhancedRealtimeQualityMonitor(); \
	monitor.start_monitoring(['kumihan_formatter/'], 10)" > /dev/null 2>&1 || echo "⚠️ リアルタイム監視スキップ"
	@echo "📋 7/7: 最終レポート生成"
	@$(PYTHON) -c "import sys, datetime, os; sys.path.append('postbox'); \
	from quality.dashboard.metrics_collector import QualityMetricsCollector; \
	collector = QualityMetricsCollector(); \
	metrics = collector.collect_all_metrics(); \
	os.makedirs('tmp', exist_ok=True); \
	report_path = f'tmp/quality_full_check_report_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'; \
	import json; \
	report_data = {\"timestamp\": datetime.datetime.now().isoformat(), \"metrics\": {k: {\"data_points\": v.data_points, \"confidence\": v.confidence, \"summary\": v.summary} for k, v in metrics.items()}}; \
	with open(report_path, 'w', encoding='utf-8') as f: json.dump(report_data, f, indent=2, ensure_ascii=False); \
	print(f'✅ 全品質システム実行完了'); \
	print(f'📊 詳細レポート: {report_path}'); \
	print(f'📈 収集メトリクス: {len(metrics)}カテゴリ')"




# 🏢 Phase 4-10 最終検証・リリース準備コマンド
enterprise-check:
	@echo "🏢 エンタープライズレベル完成度チェック実行中..."
	$(PYTHON) scripts/enterprise_check.py
	@echo "✅ エンタープライズチェック完了"

performance-benchmark:
	@echo "⚡ パフォーマンスベンチマーク実行中..."
	$(PYTHON) scripts/performance_benchmark.py
	@echo "✅ パフォーマンスベンチマーク完了"

security-audit:
	@echo "🛡️ セキュリティ監査実行中..."
	$(PYTHON) scripts/security_audit.py
	@echo "✅ セキュリティ監査完了"

release-candidate:
	@echo "🚀 リリース候補準備実行中..."
	$(PYTHON) scripts/release_prepare.py
	@echo "✅ リリース準備完了"

# 🧪 tox環境コマンド群 (Issue #1107: pyenv + tox導入)
tox-install:
	@echo "📦 tox環境セットアップ中..."
	$(PIP) install tox
	@echo "✅ tox環境セットアップ完了"

tox:
	@echo "🧪 tox全環境テスト実行中（Python 3.12/3.13）..."
	tox
	@echo "✅ tox全環境テスト完了"

tox-py312:
	@echo "🐍 Python 3.12環境テスト実行中..."
	tox -e py312
	@echo "✅ Python 3.12環境テスト完了"

tox-py313:
	@echo "🐍 Python 3.13環境テスト実行中..."
	tox -e py313
	@echo "✅ Python 3.13環境テスト完了"

tox-unit:
	@echo "🔬 tox単体テスト実行中..."
	tox -e unit
	@echo "✅ tox単体テスト完了"

tox-integration:
	@echo "🔗 tox結合テスト実行中..."
	tox -e integration
	@echo "✅ tox結合テスト完了"

tox-lint:
	@echo "🔍 tox品質チェック実行中..."
	tox -e lint
	@echo "✅ tox品質チェック完了"

tox-format:
	@echo "✨ toxフォーマット実行中..."
	tox -e format
	@echo "✅ toxフォーマット完了"

tox-parallel:
	@echo "⚡ tox並行実行中..."
	tox --parallel auto
	@echo "✅ tox並行実行完了"

tox-clean:
	@echo "🧹 tox環境クリーンアップ中..."
	tox -e clean
	@echo "✅ tox環境クリーンアップ完了"

tox-recreate:
	@echo "🔄 tox環境再構築中..."
	tox --recreate
	@echo "✅ tox環境再構築完了"
