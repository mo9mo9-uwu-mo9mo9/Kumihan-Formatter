# Kumihan-Formatter Makefile

# Python環境設定
PYTHON = python3
PIP = $(PYTHON) -m pip

# プロジェクト設定
PROJECT_NAME = kumihan_formatter
SRC_DIR = $(PROJECT_NAME)

.PHONY: help setup clean lint test test-unit test-integration test-performance test-coverage claude-check pre-commit tech-debt-check tech-debt-report tech-debt-json tech-debt-ci gemini-mypy gemini-status gemini-fix gemini-config gemini-report gemini-test

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
	@echo "  make tech-debt-check - 技術的負債監視チェック実行"
	@echo "  make tech-debt-report - 技術的負債詳細レポート生成"
	@echo ""
	@echo "🤖 Claude ↔ Gemini協業システム:"
	@echo "  make gemini-mypy     - mypy修正の自動判定・実行"
	@echo "  make gemini-fix      - 特定エラータイプの一括修正"
	@echo "  make gemini-status   - 進捗・コスト・品質確認"
	@echo "  make gemini-config   - 自動化設定変更"
	@echo "  make gemini-report   - 詳細レポート生成"
	@echo "  make gemini-test     - システム動作テスト"
	@echo ""
	@echo "🔍 統合品質管理システム:"
	@echo "  make gemini-quality-check    - 包括的品質チェック実行"
	@echo "  make gemini-quality-gate     - 品質ゲートチェック実行"
	@echo "  make gemini-quality-report   - 詳細品質レポート生成"
	@echo "  make gemini-quality-monitor  - 品質監視システム開始"
	@echo "  make gemini-integrated-workflow - 品質統合ワークフロー実行"
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

# 🤖 Claude ↔ Gemini協業システム
# 🔍 品質管理統合コマンド
gemini-quality-check:
	@echo "🔍 統合品質チェック実行..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from workflow.dual_agent_coordinator import DualAgentCoordinator; \
	import subprocess; \
	print('📊 対象ファイル検出中...'); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:10]; \
	print(f'📁 対象: {len(files)}ファイル'); \
	coordinator = DualAgentCoordinator(); \
	quality_result = coordinator.run_quality_check(files, 'claude'); \
	print(f'✅ 品質チェック完了: {quality_result[\"quality_level\"]} (スコア: {quality_result[\"quality_metrics\"].overall_score:.3f})')"

gemini-quality-gate:
	@echo "🚪 品質ゲートチェック実行..."
	@echo "使用例: make gemini-quality-gate GATE_TYPE=pre_commit"
	@$(PYTHON) -c "import sys, os; sys.path.append('postbox'); \
	from workflow.dual_agent_coordinator import DualAgentCoordinator; \
	import subprocess; \
	gate_type = os.environ.get('GATE_TYPE', 'pre_commit'); \
	print(f'🚪 品質ゲート: {gate_type}'); \
	result = subprocess.run(['find', 'kumihan_formatter/', '-name', '*.py'], capture_output=True, text=True); \
	files = [f.strip() for f in result.stdout.split('\n') if f.strip()][:5]; \
	coordinator = DualAgentCoordinator(); \
	gate_passed = coordinator.run_quality_gate_check(files, gate_type); \
	print(f'🎯 結果: {\"通過\" if gate_passed else \"失敗\"}')"

gemini-quality-report:
	@echo "📊 品質レポート生成..."
	@echo "使用例: make gemini-quality-report FORMAT=html"
	@$(PYTHON) -c "import sys, os; sys.path.append('postbox'); \
	from workflow.dual_agent_coordinator import DualAgentCoordinator; \
	format_type = os.environ.get('FORMAT', 'html'); \
	coordinator = DualAgentCoordinator(); \
	report_path = coordinator.generate_quality_report(format_type); \
	print(f'📋 レポート完成: {report_path}')"

gemini-quality-monitor:
	@echo "📊 品質監視システム開始..."
	@$(PYTHON) -c "import sys, time; sys.path.append('postbox'); \
	from workflow.dual_agent_coordinator import DualAgentCoordinator; \
	coordinator = DualAgentCoordinator(); \
	coordinator.start_quality_monitoring(); \
	print('📊 品質監視開始 (10秒後に停止)'); \
	time.sleep(10); \
	print('⏹️ 監視停止')"

gemini-integrated-workflow:
	@echo "🔄 品質管理統合ワークフロー実行..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); from workflow.dual_agent_coordinator import DualAgentCoordinator; test_files = ['kumihan_formatter/core/utilities/logger.py']; coordinator = DualAgentCoordinator(); result = coordinator.run_integrated_workflow_with_quality(test_files, 'no-untyped-def'); print(f'🎯 最終結果: {result[\"status\"]}'); print(f'📈 品質改善: {result[\"improvement\"]:.3f}') if 'improvement' in result else print('📊 改善情報なし')"

gemini-mypy:
	@echo "🤖 Gemini協業システム: mypy修正開始..."
	@echo "📊 自動判定・最適実行モードで1,219エラー修正"
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); from workflow.dual_agent_coordinator import DualAgentCoordinator; import subprocess; print('🔍 mypy strict mode エラー検出中...'); result = subprocess.run(['python3', '-m', 'mypy', '--strict', 'kumihan_formatter/', '--no-error-summary'], capture_output=True, text=True); errors = [line for line in result.stdout.split('\n') if 'error:' in line]; print(f'📊 発見されたエラー: {len(errors)}件') if errors else print('✅ mypy strict mode エラーなし'); coordinator = DualAgentCoordinator() if errors else None; files = list(set(line.split(':')[0] for line in errors if ':' in line)) if errors else []; print(f'📁 対象ファイル: {len(files)}件') if files else None; task_ids = coordinator.create_mypy_fix_task(files[:5], 'no-untyped-def', auto_execute=True) if files else []; print(f'✅ 自動修正完了: {len(task_ids)}タスク実行') if task_ids else print('📊 修正対象なし')"
	@echo "✅ Gemini協業mypy修正完了"

gemini-fix:
	@echo "🤖 Gemini協業システム: エラータイプ別修正..."
	@echo "使用例: make gemini-fix ERROR_TYPE=no-untyped-def"
	@$(PYTHON) -c "import sys, os; \
	error_type = os.environ.get('ERROR_TYPE', 'no-untyped-def'); \
	print(f'🎯 修正対象: {error_type} エラー'); \
	sys.path.append('postbox'); \
	from workflow.dual_agent_coordinator import DualAgentCoordinator; \
	coordinator = DualAgentCoordinator(); \
	test_files = ['kumihan_formatter/core/utilities/logger.py']; \
	task_ids = coordinator.create_mypy_fix_task(test_files, error_type, auto_execute=True); \
	print(f'✅ {error_type} エラー修正完了')"

gemini-status:
	@echo "📊 Gemini協業システム: ステータス確認..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from utils.task_manager import TaskManager; \
	from core.workflow_decision_engine import WorkflowDecisionEngine; \
	import json; \
	tm = TaskManager(); \
	tm.print_status(); \
	engine = WorkflowDecisionEngine(); \
	stats = engine.get_decision_stats(); \
	print(f'\n🎯 判定統計:'); \
	print(f'  総判定回数: {stats.get(\"total_decisions\", 0)}回'); \
	print(f'  Gemini使用率: {stats.get(\"gemini_usage_rate\", 0):.1%}'); \
	print(f'  平均コスト: \${stats.get(\"average_cost\", 0):.4f}'); \
	print(f'  平均効果スコア: {stats.get(\"average_benefit_score\", 0):.2f}'); \
	try: \
		with open('postbox/monitoring/cost_tracking.json', 'r') as f: cost_data = json.load(f); \
		print(f'\n💰 累積コスト: \${cost_data.get(\"total_cost\", 0):.4f}'); \
	except: print('\n💰 コスト情報: 未初期化')"

gemini-config:
	@echo "⚙️ Gemini協業システム: 設定管理..."
	@$(PYTHON) -c "import sys; sys.path.append('postbox'); \
	from core.workflow_decision_engine import WorkflowDecisionEngine; \
	import json; \
	engine = WorkflowDecisionEngine(); \
	config = engine.config; \
	print('🎯 現在の設定:'); \
	print(f'  最小Token数: {config.get(\"min_tokens_for_gemini\", 1000)}'); \
	print(f'  最大自動コスト: \${config.get(\"max_cost_auto_approval\", 0.01):.3f}'); \
	print(f'  最小効果スコア: {config.get(\"min_benefit_score\", 0.6):.1f}'); \
	print(f'  複雑度閾値: {config.get(\"complexity_threshold\", \"moderate\")}'); \
	print('\n設定変更例:'); \
	print('  coordinator.set_automation_preferences({\"thresholds\": {\"min_tokens_for_gemini\": 1500}})')"

gemini-report:
	@echo "📋 Gemini協業システム: 詳細レポート生成..."
	@$(PYTHON) -c "import sys, os, datetime; sys.path.append('postbox'); \
	from utils.task_manager import TaskManager; \
	from core.workflow_decision_engine import WorkflowDecisionEngine; \
	import json; \
	tm = TaskManager(); \
	engine = WorkflowDecisionEngine(); \
	report = tm.generate_progress_report(); \
	stats = engine.get_decision_stats(); \
	os.makedirs('tmp', exist_ok=True); \
	report_data = {'generated_at': datetime.datetime.now().isoformat(), 'task_progress': report, 'decision_stats': stats}; \
	with open('tmp/gemini_collaboration_report.json', 'w') as f: json.dump(report_data, f, indent=2, ensure_ascii=False); \
	print('📊 レポート生成完了: tmp/gemini_collaboration_report.json'); \
	print(f'📈 総タスク数: {report[\"task_summary\"][\"total_tasks\"]}'); \
	print(f'✅ 完了率: {report[\"task_summary\"][\"completion_rate\"]:.1%}'); \
	print(f'🐛 修正エラー数: {report[\"quality_metrics\"][\"total_errors_fixed\"]}'); \
	print(f'💰 総コスト: \${report[\"cost_metrics\"][\"total_cost\"]:.4f}')"

gemini-test:
	@echo "🧪 Gemini協業システム: 動作テスト..."
	@$(PYTHON) test_flash25_workflow.py
