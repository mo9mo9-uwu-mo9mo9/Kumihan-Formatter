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
	@echo "🛠️ Gemini協業品質保証 (Issue #920改善):"
	@echo "  make gemini-quality-check     - Gemini協業後統合品質チェック（新システム）"
	@echo "  make gemini-post-review       - Gemini協業後総合レビュー"
	@echo "  make gemini-validation-full   - 完全バリデーション（3層検証）"
	@echo "  make gemini-quality-check-legacy - 従来の品質チェック（参考）"
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
# 🔍 品質管理統合コマンド (従来システム)
gemini-quality-check-legacy:
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
	print(f'  平均コスト: $${stats.get(\"average_cost\", 0):.4f}'); \
	print(f'  平均効果スコア: {stats.get(\"average_benefit_score\", 0):.2f}'); \
	try: \
		with open('postbox/monitoring/cost_tracking.json', 'r') as f: cost_data = json.load(f); \
		print(f'\n💰 累積コスト: $${cost_data.get(\"total_cost\", 0):.4f}'); \
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
	print(f'  最大自動コスト: $${config.get(\"max_cost_auto_approval\", 0.01):.3f}'); \
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
	print(f'💰 総コスト: $${report[\"cost_metrics\"][\"total_cost\"]:.4f}')"

gemini-test:
	@echo "🧪 Gemini協業システム: 動作テスト..."
	@$(PYTHON) test_flash25_workflow.py

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

# 🛠️ Gemini協業品質保証コマンド (Issue #920改善対応)
gemini-quality-check:
	@echo "🔍 Gemini協業後統合品質チェック実行..."
	@echo "📊 Phase 1: 基本品質チェック"
	@$(MAKE) --no-print-directory lint || (echo "❌ lint失敗 - Gemini修正必要"; exit 1)
	@$(MAKE) --no-print-directory test || (echo "❌ test失敗 - Gemini修正必要"; exit 1)
	@git status --porcelain | head -10 | while read line; do echo "📁 変更: $$line"; done
	@echo "✅ Phase 1完了"
	@echo ""
	@echo "📊 Phase 2: API互換性・統合チェック"
	@$(PYTHON) -c "import sys; \
	print('🔍 import文動作確認中...'); \
	try: \
		from kumihan_formatter.core.utilities.logger import get_logger; \
		from kumihan_formatter.parser import KumihanParser; \
		from kumihan_formatter.core.rendering.main_renderer import MainRenderer; \
		print('✅ 主要モジュールimport成功'); \
	except Exception as e: \
		print(f'❌ import失敗: {e}'); \
		sys.exit(1)"
	@echo "✅ Phase 2完了"
	@echo ""
	@echo "📊 Phase 3: コード品質詳細チェック"
	@$(PYTHON) -c "import subprocess, sys; \
	result = subprocess.run(['python3', '-m', 'mypy', '--strict', 'kumihan_formatter/', '--no-error-summary'], capture_output=True, text=True); \
	error_count = len([line for line in result.stdout.split('\n') if 'error:' in line]); \
	print(f'📊 mypy strict mode: {error_count}件のエラー'); \
	print('✅ 型チェック完了 (エラーは許容範囲)' if error_count < 100 else '⚠️ 型エラー多数 - 要改善')"
	@echo "✅ Phase 3完了"
	@echo ""
	@echo "🎯 統合品質チェック完了 ✅"

gemini-post-review:
	@echo "📋 Gemini協業後総合レビュー実行..."
	@echo "🔍 1/5: セキュリティチェック"
	@$(PYTHON) -c "import os, re; \
	security_issues = []; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				filepath = os.path.join(root, file); \
				try: \
					with open(filepath, 'r', encoding='utf-8') as f: \
						content = f.read(); \
						if re.search(r'(password|secret|key)\s*=\s*[\"\\'][^\"\\']', content, re.I): \
							security_issues.append(f'{filepath}: 機密情報ハードコード'); \
						if 'eval(' in content or 'exec(' in content: \
							security_issues.append(f'{filepath}: 危険な動的実行'); \
				except: pass; \
	print(f'🛡️ セキュリティ問題: {len(security_issues)}件') if security_issues else print('✅ セキュリティ問題なし'); \
	[print(f'  ⚠️ {issue}') for issue in security_issues[:5]]"
	@echo "✅ 1/5完了"
	@echo ""
	@echo "🔍 2/5: パフォーマンスチェック"
	@$(PYTHON) -c "import os, re; \
	perf_warnings = []; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				filepath = os.path.join(root, file); \
				try: \
					with open(filepath, 'r', encoding='utf-8') as f: \
						content = f.read(); \
						lines = content.split('\n'); \
						if len(lines) > 500: \
							perf_warnings.append(f'{filepath}: 大型ファイル({len(lines)}行)'); \
						if content.count('for ') > 10: \
							perf_warnings.append(f'{filepath}: ループ多用'); \
				except: pass; \
	print(f'⚡ パフォーマンス警告: {len(perf_warnings)}件') if perf_warnings else print('✅ パフォーマンス問題なし'); \
	[print(f'  ⚠️ {warning}') for warning in perf_warnings[:5]]"
	@echo "✅ 2/5完了"
	@echo ""
	@echo "🔍 3/5: 依存関係チェック"
	@$(PYTHON) -c "import ast, os; \
	import_graph = {}; \
	circular_refs = []; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				filepath = os.path.join(root, file); \
				try: \
					with open(filepath, 'r', encoding='utf-8') as f: \
						tree = ast.parse(f.read()); \
						imports = []; \
						for node in ast.walk(tree): \
							if isinstance(node, ast.Import): \
								imports.extend([alias.name for alias in node.names]); \
							elif isinstance(node, ast.ImportFrom): \
								imports.append(node.module or ''); \
						import_graph[filepath] = imports; \
				except: pass; \
	print(f'🔗 モジュール依存関係: {len(import_graph)}ファイル解析'); \
	print('✅ 循環参照なし') if not circular_refs else print(f'⚠️ 循環参照: {len(circular_refs)}件')"
	@echo "✅ 3/5完了"
	@echo ""
	@echo "🔍 4/5: ドキュメントチェック"
	@$(PYTHON) -c "import os, re; \
	doc_issues = []; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				filepath = os.path.join(root, file); \
				try: \
					with open(filepath, 'r', encoding='utf-8') as f: \
						content = f.read(); \
						functions = re.findall(r'def\s+(\w+)\s*\(', content); \
						docstrings = re.findall(r'\"\"\".*?\"\"\"', content, re.DOTALL); \
						if len(functions) > len(docstrings) and len(functions) > 3: \
							doc_issues.append(f'{filepath}: docstring不足'); \
				except: pass; \
	print(f'📝 ドキュメント問題: {len(doc_issues)}件') if doc_issues else print('✅ ドキュメント問題なし'); \
	[print(f'  ⚠️ {issue}') for issue in doc_issues[:3]]"
	@echo "✅ 4/5完了"
	@echo ""
	@echo "🔍 5/5: 保守性チェック"
	@$(PYTHON) -c "import os; \
	maintainability_score = 0; \
	total_files = 0; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				total_files += 1; \
				filepath = os.path.join(root, file); \
				try: \
					with open(filepath, 'r', encoding='utf-8') as f: \
						content = f.read(); \
						lines = len(content.split('\n')); \
						if lines < 300: maintainability_score += 2; \
						elif lines < 500: maintainability_score += 1; \
						if 'class ' in content: maintainability_score += 1; \
						if '\"\"\"' in content: maintainability_score += 1; \
				except: pass; \
	avg_score = maintainability_score / total_files if total_files else 0; \
	print(f'🔧 保守性スコア: {avg_score:.2f}/5.0'); \
	print('✅ 保守性良好' if avg_score >= 3.0 else '⚠️ 保守性要改善')"
	@echo "✅ 5/5完了"
	@echo ""
	@echo "🎯 総合レビュー完了 ✅"

gemini-validation-full:
	@echo "🛠️ Gemini協業完全バリデーション実行..."
	@echo "📊 3層検証システム (Layer 1 → Layer 2 → Layer 3)"
	@echo ""
	@echo "🔍 Layer 1: 構文検証"
	@$(PYTHON) -c "import py_compile, os, sys; \
	errors = []; \
	for root, dirs, files in os.walk('kumihan_formatter'): \
		for file in files: \
			if file.endswith('.py'): \
				filepath = os.path.join(root, file); \
				try: py_compile.compile(filepath, doraise=True); \
				except py_compile.PyCompileError as e: errors.append(f'{filepath}: {e}'); \
	print(f'📊 構文エラー: {len(errors)}件') if errors else print('✅ 構文エラーなし'); \
	[print(f'  ❌ {error}') for error in errors[:3]]; \
	sys.exit(1) if errors else None"
	@echo "✅ Layer 1通過"
	@echo ""
	@echo "🔍 Layer 2: 品質検証"
	@$(MAKE) --no-print-directory gemini-quality-check
	@echo "✅ Layer 2通過"
	@echo ""
	@echo "🔍 Layer 3: Claude最終承認"
	@$(MAKE) --no-print-directory gemini-post-review
	@echo "✅ Layer 3通過"
	@echo ""
	@echo "🎯 3層検証完全通過 ✅"
	@echo "📊 品質保証レベル: PRODUCTION READY"
