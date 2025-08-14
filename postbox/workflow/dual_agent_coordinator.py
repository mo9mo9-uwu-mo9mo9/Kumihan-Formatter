#!/usr/bin/env python3
"""
Dual-Agent Workflow Coordinator
Claude Code ↔ Gemini CLI 協業統合システム
"""

import json
import os
import subprocess
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import datetime

# プロジェクトルートからpostboxユーティリティをインポート
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.task_manager import TaskManager
from utils.gemini_helper import GeminiHelper
from utils.task_analyzer import TaskAnalyzer
from templates.flash_templates import Flash25Templates
from templates.enhanced_flash_templates import EnhancedFlash25Templates
from quality.syntax_validator import SyntaxValidator, TypeAnnotationTemplate
from core.workflow_decision_engine import WorkflowDecisionEngine, AutomationLevel
from quality.quality_manager import QualityManager
from monitoring.quality_monitor import QualityMonitor
from reporting.quality_reporter import QualityReporter

# TokenMeasurementSystem統合
try:
    from utils.token_measurement import TokenMeasurementSystem
except ImportError:
    print("⚠️ TokenMeasurementSystemのインポートに失敗しました")
    TokenMeasurementSystem = None

# Issue #844: ハイブリッド実装フロー統合
from workflow.hybrid_implementation_flow import HybridImplementationFlow, HybridImplementationSpec
from phases.phase_a_architecture import PhaseAArchitecture
from phases.phase_b_implementation import PhaseBImplementation
from phases.phase_c_integration import PhaseCIntegration
from monitoring.success_rate_monitor import SuccessRateMonitor

# Issue #870: 高度開発システム統合
from advanced.dependency_analyzer import DependencyAnalyzer
from advanced.multi_file_coordinator import MultiFileCoordinator
from advanced.pattern_implementation_engine import PatternImplementationEngine
from advanced.refactoring_engine import RefactoringEngine
from advanced.performance_optimizer import PerformanceOptimizer

class DualAgentCoordinator:
    """Claude ↔ Gemini協業の統合コーディネーター"""

    def __init__(self):
        self.task_manager = TaskManager()
        self.gemini_helper = GeminiHelper()
        self.task_analyzer = TaskAnalyzer()
        self.flash_templates = Flash25Templates()
        self.enhanced_templates = EnhancedFlash25Templates()
        self.syntax_validator = SyntaxValidator()
        self.type_template = TypeAnnotationTemplate()
        self.decision_engine = WorkflowDecisionEngine()
        self.quality_manager = QualityManager()
        self.quality_monitor = QualityMonitor()

        # TokenMeasurementSystem初期化
        self.token_measurement = TokenMeasurementSystem() if TokenMeasurementSystem else None
        self.quality_reporter = QualityReporter()
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Issue #844: 3段階ハイブリッド実装フローシステム
        self.hybrid_flow = HybridImplementationFlow()
        self.phase_a = PhaseAArchitecture()
        self.phase_b = PhaseBImplementation(self.hybrid_flow.success_criteria)
        self.phase_c = PhaseCIntegration(self.hybrid_flow.success_criteria)
        self.success_monitor = SuccessRateMonitor()

        # 成功率監視開始
        self.success_monitor.start_monitoring(check_interval_seconds=300)

        # Issue #870: 高度開発システム統合
        self.dependency_analyzer = DependencyAnalyzer()
        self.multi_file_coordinator = MultiFileCoordinator()
        self.pattern_engine = PatternImplementationEngine()
        self.refactoring_engine = RefactoringEngine()
        self.performance_optimizer = PerformanceOptimizer()

        print(f"🤖 Dual-Agent Workflow 開始 (Flash 2.5 最適化)")
        print(f"📋 セッションID: {self.session_id}")
        print(f"🔄 Claude Code ↔ Gemini CLI 協業システム")
        print(f"🧠 タスク微分化エンジン: 有効")
        print(f"📝 Flash 2.5 テンプレート: 有効")
        print(f"🎯 自動判定エンジン: 有効")
        print(f"🔍 統合品質管理: 有効")
        print(f"📊 品質監視システム: 有効")
        print(f"🛡️ 構文エラー防止機構: 有効")
        print(f"✅ 品質保証テンプレート: 有効")
        print(f"🏗️ ハイブリッド実装フロー: 有効 (Issue #844)")
        print(f"📊 成功率監視システム: 有効 (目標: 実装≥70%, Token≥90%, 品質≥80%, 統合≥95%)")
        print(f"⚡ 高度開発システム: 5モジュール統合完了 (Issue #870)")

    def create_mypy_fix_task(self,
                           target_files: List[str],
                           error_type: str = "no-untyped-def",
                           priority: str = "high",
                           use_micro_tasks: bool = True,
                           force_mode: str = None,
                           auto_execute: bool = True) -> List[str]:
        """mypy修正タスク作成（自動判定・実行機能付き）"""
        return self._create_task_with_type(
            "code_modification", target_files, error_type, priority,
            use_micro_tasks, force_mode, auto_execute
        )

    def create_new_implementation_task(self,
                                     target_files: List[str],
                                     implementation_spec: Dict[str, Any],
                                     priority: str = "high",
                                     force_mode: str = None,
                                     auto_execute: bool = True) -> List[str]:
        """新規実装タスク作成"""
        return self._create_implementation_task(
            "new_implementation", target_files, implementation_spec,
            priority, force_mode, auto_execute
        )

    def create_hybrid_implementation_task(self,
                                        target_files: List[str],
                                        implementation_spec: Dict[str, Any],
                                        priority: str = "high",
                                        force_mode: str = None,
                                        auto_execute: bool = True) -> List[str]:
        """ハイブリッド実装タスク作成"""
        return self._create_implementation_task(
            "hybrid_implementation", target_files, implementation_spec,
            priority, force_mode, auto_execute
        )

    def create_feature_development_task(self,
                                      target_files: List[str],
                                      feature_spec: Dict[str, Any],
                                      priority: str = "high",
                                      force_mode: str = None,
                                      auto_execute: bool = True) -> List[str]:
        """新機能開発タスク作成"""
        return self._create_implementation_task(
            "new_feature_development", target_files, feature_spec,
            priority, force_mode, auto_execute
        )

    # === Issue #844: 3段階ハイブリッド実装フロー ===

    def execute_hybrid_implementation_flow(self,
                                         target_files: List[str],
                                         implementation_spec: Dict[str, Any],
                                         auto_execute: bool = True) -> str:
        """Issue #844: 3段階ハイブリッド実装フロー実行

        Args:
            target_files: 実装対象ファイルリスト
            implementation_spec: 実装仕様
            auto_execute: 自動実行フラグ

        Returns:
            str: 実装ID
        """

        print(f"🏗️ 3段階ハイブリッド実装フロー開始")
        print(f"📁 対象ファイル: {len(target_files)}件")

        # 実装仕様作成
        hybrid_spec = HybridImplementationSpec(
            implementation_id=f"hybrid_{self.session_id}_{int(time.time())}",
            implementation_type=implementation_spec.get("type", "hybrid_implementation"),
            target_files=target_files,
            requirements=implementation_spec.get("requirements", {}),
            success_criteria=implementation_spec.get("success_criteria", {
                "quality_score": 0.80,
                "functionality": "complete",
                "integration_success": 0.95
            }),
            quality_standards=implementation_spec.get("quality_standards", {
                "code_quality": {"style": "pep8", "typing": "strict"},
                "test_coverage": 0.8,
                "documentation": {"required": True}
            }),
            context=implementation_spec.get("context", {
                "session_id": self.session_id,
                "coordinator": "dual_agent"
            })
        )

        # フロー実行
        implementation_id = self.hybrid_flow.start_hybrid_implementation(
            hybrid_spec, auto_execute=auto_execute
        )

        print(f"✅ 3段階ハイブリッド実装フロー開始完了: {implementation_id}")
        return implementation_id

    def get_hybrid_implementation_status(self, implementation_id: str) -> Dict[str, Any]:
        """ハイブリッド実装ステータス取得

        Args:
            implementation_id: 実装ID

        Returns:
            Dict[str, Any]: 実装ステータス
        """

        return self.hybrid_flow.get_implementation_status(implementation_id)

    def execute_phase_a_only(self, target_files: List[str],
                           implementation_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Phase A (アーキテクチャ設計) のみ実行

        Args:
            target_files: 対象ファイル
            implementation_spec: 実装仕様

        Returns:
            Dict[str, Any]: Phase A実行結果
        """

        print(f"🧠 Phase A (アーキテクチャ設計) 単独実行開始")

        # Phase A実行
        analysis = self.phase_a.execute_architecture_analysis(implementation_spec)
        interfaces = self.phase_a.design_component_interfaces(analysis, target_files)
        strategy = self.phase_a.create_implementation_strategy(analysis, interfaces, implementation_spec)
        quality_eval = self.phase_a.evaluate_architecture_quality(analysis, interfaces, strategy)
        handoff = self.phase_a.generate_phase_b_handoff(analysis, interfaces, strategy)

        result = {
            "phase": "A",
            "status": "completed" if quality_eval["phase_a_pass"] else "needs_review",
            "architecture_analysis": analysis.__dict__,
            "interface_design": {k: v.__dict__ for k, v in interfaces.items()},
            "implementation_strategy": strategy,
            "quality_evaluation": quality_eval,
            "phase_b_handoff": handoff
        }

        # 成功率記録
        self.success_monitor.record_implementation_success(
            f"phase_a_{int(time.time())}", "phase_a", quality_eval["phase_a_pass"]
        )
        self.success_monitor.record_quality_score(
            f"phase_a_{int(time.time())}", "phase_a", quality_eval["overall_quality_score"]
        )

        print(f"✅ Phase A 完了: {'成功' if quality_eval['phase_a_pass'] else '要改善'}")
        return result

    def get_success_rate_dashboard(self) -> Dict[str, Any]:
        """Issue #844成功率ダッシュボードデータ取得

        Returns:
            Dict[str, Any]: ダッシュボードデータ
        """

        dashboard_data = self.success_monitor.get_metrics_dashboard_data()
        current_rates = self.success_monitor.get_current_success_rates()

        # 追加の統合情報
        dashboard_data["session_info"] = {
            "session_id": self.session_id,
            "coordinator_type": "dual_agent",
            "hybrid_flow_enabled": True,
            "monitoring_active": True
        }

        dashboard_data["issue_844_compliance"] = {
            "overall_success": current_rates["overall_success"],
            "criteria_summary": current_rates["summary"],
            "targets_met": {
                "implementation_success": current_rates["individual_metrics"]["implementation_success"]["meets_target"],
                "token_savings": current_rates["individual_metrics"]["token_savings"]["meets_target"],
                "quality_score": current_rates["individual_metrics"]["quality_score"]["meets_target"],
                "integration_success": current_rates["individual_metrics"]["integration_success"]["meets_target"]
            }
        }

        return dashboard_data

    def generate_hybrid_flow_report(self) -> Dict[str, Any]:
        """ハイブリッドフロー統合レポート生成

        Returns:
            Dict[str, Any]: 統合レポート
        """

        print(f"📊 ハイブリッドフロー統合レポート生成中...")

        # 各システムからデータ収集
        success_metrics = self.success_monitor.get_success_rate_metrics()
        current_rates = self.success_monitor.get_current_success_rates()

        report = {
            "report_timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.session_id,
            "system_status": {
                "hybrid_flow_active": True,
                "success_monitoring_active": self.success_monitor.monitoring_active,
                "phase_systems_loaded": {
                    "phase_a": bool(self.phase_a),
                    "phase_b": bool(self.phase_b),
                    "phase_c": bool(self.phase_c)
                }
            },
            "issue_844_compliance": {
                "overall_criteria_met": current_rates["overall_success"],
                "individual_targets": {
                    "implementation_success_rate": {
                        "current": current_rates["summary"]["implementation_success"],
                        "target": 0.70,
                        "met": current_rates["summary"]["implementation_success"] >= 0.70
                    },
                    "token_savings_rate": {
                        "current": current_rates["summary"]["token_savings"],
                        "target": 0.90,
                        "met": current_rates["summary"]["token_savings"] >= 0.90
                    },
                    "quality_score": {
                        "current": current_rates["summary"]["quality_score"],
                        "target": 0.80,
                        "met": current_rates["summary"]["quality_score"] >= 0.80
                    },
                    "integration_success_rate": {
                        "current": current_rates["summary"]["integration_success"],
                        "target": 0.95,
                        "met": current_rates["summary"]["integration_success"] >= 0.95
                    }
                },
                "compliance_percentage": sum(
                    1 for metric in current_rates["individual_metrics"].values()
                    if metric["meets_target"]
                ) / len(current_rates["individual_metrics"]) * 100
            },
            "performance_metrics": success_metrics,
            "recommendations": self._generate_integration_recommendations(current_rates),
            "next_actions": self._generate_next_actions(current_rates)
        }

        print(f"📊 統合レポート生成完了")
        print(f"🎯 Issue #844基準達成: {'✅' if report['issue_844_compliance']['overall_criteria_met'] else '❌'}")
        print(f"📈 達成率: {report['issue_844_compliance']['compliance_percentage']:.1f}%")

        return report

    def _generate_integration_recommendations(self, current_rates: Dict[str, Any]) -> List[str]:
        """統合推奨事項生成"""

        recommendations = []
        individual_metrics = current_rates["individual_metrics"]

        for metric_name, metric_data in individual_metrics.items():
            if not metric_data["meets_target"]:
                current = metric_data["current_rate"]
                target = metric_data["target_rate"]
                deficit = target - current

                if metric_name == "implementation_success":
                    recommendations.append(f"実装成功率改善が必要: {current:.1%} → {target:.1%} (+{deficit:.1%})")
                    recommendations.append("- Phase A設計品質の向上")
                    recommendations.append("- Gemini指示の具体性強化")
                elif metric_name == "token_savings":
                    recommendations.append(f"Token節約率改善が必要: {current:.1%} → {target:.1%} (+{deficit:.1%})")
                    recommendations.append("- タスク分割の最適化")
                    recommendations.append("- テンプレート効率化")
                elif metric_name == "quality_score":
                    recommendations.append(f"品質スコア改善が必要: {current:.2f} → {target:.2f} (+{deficit:.2f})")
                    recommendations.append("- コードレビュープロセス強化")
                    recommendations.append("- 自動品質チェック拡充")
                elif metric_name == "integration_success":
                    recommendations.append(f"統合成功率改善が必要: {current:.1%} → {target:.1%} (+{deficit:.1%})")
                    recommendations.append("- 統合テストの充実")
                    recommendations.append("- 依存関係管理改善")

        if not recommendations:
            recommendations.append("全ての成功基準を達成しています。現在の品質を維持してください。")

        return recommendations

    def _generate_next_actions(self, current_rates: Dict[str, Any]) -> List[str]:
        """次のアクション生成"""

        actions = []

        if current_rates["overall_success"]:
            actions.extend([
                "Issue #844基準達成を維持",
                "継続的な品質監視",
                "システム最適化の継続実施"
            ])
        else:
            actions.extend([
                "未達成基準の重点改善",
                "改善計画の策定・実行",
                "監視頻度の増加"
            ])

        return actions

    def cleanup_hybrid_systems(self) -> None:
        """ハイブリッドシステムクリーンアップ"""

        print("🧹 ハイブリッドシステムクリーンアップ開始")

        # 監視停止
        if hasattr(self, 'success_monitor'):
            self.success_monitor.stop_monitoring()
            print("📊 成功率監視停止")

        print("✅ ハイブリッドシステムクリーンアップ完了")

    def _create_task_with_type(self,
                             task_type: str,
                             target_files: List[str],
                             error_type: str,
                             priority: str,
                             use_micro_tasks: bool,
                             force_mode: str,
                             auto_execute: bool) -> List[str]:
        """タスク作成（タイプ別統一インターフェース）"""

        task_description = f"{error_type} エラー修正 - {len(target_files)}ファイル" if task_type == "code_modification" else f"{task_type} - {len(target_files)}ファイル"

        print(f"🔍 タスク作成開始: {task_description}")
        print(f"📁 対象ファイル: {len(target_files)}件")
        print(f"🧠 微分化モード: {'有効' if use_micro_tasks else '無効'}")

        # ===== 自動判定フェーズ =====

        # タスク分析実行
        task_analysis = self.decision_engine.analyze_task(
            task_description, target_files, error_type,
            context={"priority": priority, "session_id": self.session_id, "task_type": task_type}
        )

        # Gemini使用判定
        user_prefs = {"force_mode": force_mode} if force_mode else {}
        decision = self.decision_engine.make_decision(task_analysis, user_prefs)

        print(f"\n🎯 自動判定結果:")
        print(f"   Gemini使用: {'はい' if decision.use_gemini else 'いいえ'}")
        print(f"   自動化レベル: {decision.automation_level.value}")
        print(f"   推定コスト: ${decision.task_analysis.estimated_cost:.4f}")
        print(f"   効果スコア: {decision.task_analysis.gemini_benefit_score:.2f}")
        print(f"   理由: {decision.reasoning}")

        # ===== 実行方式決定 =====
        if decision.use_gemini:
            print(f"\n🚀 Gemini協業モードで実行")
            created_task_ids = self._create_with_gemini_mode(
                target_files, error_type, priority, use_micro_tasks, decision, task_type
            )
        else:
            print(f"\n🧠 Claude単独モードで実行")
            created_task_ids = self._create_with_claude_mode(
                target_files, error_type, priority, decision, task_type
            )

        # ===== 自動実行判定 =====
        if auto_execute and decision.automation_level in [AutomationLevel.FULL_AUTO, AutomationLevel.SEMI_AUTO]:
            print(f"\n⚡ 自動実行開始（レベル: {decision.automation_level.value}）")

            if decision.automation_level == AutomationLevel.SEMI_AUTO:
                # 重要な変更の場合のみ確認
                if decision.task_analysis.risk_level == "high" or decision.task_analysis.estimated_cost > 0.005:
                    print("⚠️ 重要な変更のため手動確認推奨")
                else:
                    self._auto_execute_tasks(created_task_ids, decision)
            else:
                self._auto_execute_tasks(created_task_ids, decision)

        elif decision.automation_level == AutomationLevel.APPROVAL_REQUIRED:
            print(f"\n🤚 承認必須: 実行前にユーザー確認が必要")
            print(f"   実行コマンド: coordinator.execute_workflow_cycle()")

        print(f"\n✅ タスク作成完了: {len(created_task_ids)}件")
        return created_task_ids

    def _create_implementation_task(self,
                                  task_type: str,
                                  target_files: List[str],
                                  implementation_spec: Dict[str, Any],
                                  priority: str,
                                  force_mode: str,
                                  auto_execute: bool) -> List[str]:
        """新規実装タスク作成（統一インターフェース）"""

        print(f"🎨 新規実装タスク作成開始: {task_type}")
        print(f"📁 対象ファイル: {len(target_files)}件")

        try:
            # 入力検証
            if not target_files:
                print("⚠️ 対象ファイルが指定されていません。デフォルトファイルを使用します。")
                target_files = [f"tmp/{task_type}_implementation.py"]

            if not implementation_spec:
                print("⚠️ 実装仕様が指定されていません。デフォルト仕様を使用します。")
                implementation_spec = {"template_type": "generic", "complexity": "medium"}

            # タスク分析実行
            task_description = f"{task_type} - {len(target_files)}ファイル実装"
            task_analysis = self.decision_engine.analyze_task(
                task_description, target_files, "new_implementation",
                context={
                    "priority": priority,
                    "session_id": self.session_id,
                    "task_type": task_type,
                    "implementation_spec": implementation_spec
                }
            )
        except Exception as e:
            print(f"❌ タスク分析エラー: {e}")
            print("🔄 フォールバック処理を実行します...")
            # フォールバック: 簡易的なタスク分析結果を作成
            from postbox.core.workflow_decision_engine import TaskAnalysis, TaskComplexity
            task_analysis = TaskAnalysis(
                complexity=TaskComplexity.MODERATE,
                estimated_time=60,
                estimated_tokens=self._estimate_task_tokens(task_description, target_files),
                estimated_cost=0.005,
                risk_level="medium",
                gemini_benefit_score=0.7,
                automation_recommendation=AutomationLevel.SEMI_AUTO,
                confidence=0.5
            )

        try:
            # Gemini使用判定
            user_prefs = {"force_mode": force_mode} if force_mode else {}
            decision = self.decision_engine.make_decision(task_analysis, user_prefs)

            print(f"\n🎯 自動判定結果:")
            print(f"   Gemini使用: {'はい' if decision.use_gemini else 'いいえ'}")
            print(f"   自動化レベル: {decision.automation_level.value}")
            print(f"   推定コスト: ${decision.task_analysis.estimated_cost:.4f}")
            print(f"   理由: {decision.reasoning}")

        except Exception as e:
            print(f"❌ Gemini判定エラー: {e}")
            print("🔄 デフォルト判定を使用します...")
            # フォールバック: デフォルト判定結果を作成
            from postbox.core.workflow_decision_engine import DecisionResult
            decision = DecisionResult(
                use_gemini=False,
                automation_level=AutomationLevel.SEMI_AUTO,
                task_analysis=task_analysis,
                reasoning="エラーによりデフォルト設定を使用",
                alternative_approaches=["手動実行"],
                cost_benefit_analysis={"estimated_cost": 0.005}
            )

        # 実装タスク作成
        created_task_ids = []

        for file_path in target_files:
            try:
                print(f"\n📄 実装タスク作成: {file_path}")

                # 実装タスク作成
                task_id = self._create_implementation_task_for_file(
                    file_path, task_type, implementation_spec, priority, decision
                )
                created_task_ids.append(task_id)

            except Exception as e:
                print(f"❌ タスク作成エラー ({file_path}): {e}")
                print("🔄 フォールバック処理でタスクを作成します...")
                # フォールバック: 簡易タスク作成
                try:
                    fallback_task_id = self._create_fallback_implementation_task(
                        file_path, task_type, implementation_spec, priority
                    )
                    created_task_ids.append(fallback_task_id)
                    print(f"✅ フォールバックタスク作成成功: {fallback_task_id}")
                except Exception as fallback_error:
                    print(f"❌ フォールバックタスク作成も失敗: {fallback_error}")
                    continue

        # 自動実行判定
        if auto_execute and decision.automation_level in [AutomationLevel.FULL_AUTO, AutomationLevel.SEMI_AUTO]:
            print(f"\n⚡ 自動実行開始（レベル: {decision.automation_level.value}）")

            if decision.automation_level == AutomationLevel.SEMI_AUTO:
                # 重要な変更の場合のみ確認
                if decision.task_analysis.risk_level == "high" or decision.task_analysis.estimated_cost > 0.005:
                    print("⚠️ 重要な変更のため手動確認推奨")
                else:
                    self._auto_execute_tasks(created_task_ids, decision)
            else:
                self._auto_execute_tasks(created_task_ids, decision)
        elif decision.automation_level == AutomationLevel.APPROVAL_REQUIRED:
            print(f"\n🤚 承認必須: 実行前にユーザー確認が必要")
            print(f"   実行コマンド: coordinator.execute_workflow_cycle()")

        print(f"\n✅ 実装タスク作成完了: {len(created_task_ids)}件")
        return created_task_ids

    def _create_implementation_task_for_file(self,
                                           file_path: str,
                                           task_type: str,
                                           implementation_spec: Dict[str, Any],
                                           priority: str,
                                           decision) -> str:
        """ファイル単位の実装タスク作成"""

        # Claudeによる詳細分析
        claude_analysis = self._claude_analyze_implementation_task(
            file_path, task_type, implementation_spec
        )

        # 実装指示生成
        implementation_instruction = self._generate_implementation_instruction(
            file_path, task_type, implementation_spec
        )

        task_id = self.task_manager.create_task(
            task_type=task_type,
            description=f"{task_type} - {file_path}",
            target_files=[file_path],
            priority=priority,
            requirements={
                "implementation_spec": implementation_spec,
                "task_type": task_type,
                "implementation_instruction": implementation_instruction,
                "quality_requirements": {
                    "syntax_check": True,
                    "type_check": True,
                    "style_check": True,
                    "test_creation": implementation_spec.get("create_tests", False)
                }
            },
            claude_analysis=claude_analysis,
            expected_outcome=f"{task_type}完了 - {file_path}",
            constraints=[
                "品質基準遵守",
                "テスト通過必須",
                "mypy strict mode適合"
            ],
            context={
                "task_type": task_type,
                "implementation_type": implementation_spec.get("template_type", "generic"),
                "decision_engine_result": {
                    "complexity": decision.task_analysis.complexity.value,
                    "estimated_time": decision.task_analysis.estimated_time,
                    "estimated_tokens": decision.task_analysis.estimated_tokens,
                    "estimated_cost": decision.task_analysis.estimated_cost,
                    "risk_level": decision.task_analysis.risk_level,
                    "gemini_benefit_score": decision.task_analysis.gemini_benefit_score,
                    "automation_recommendation": decision.task_analysis.automation_recommendation.value,
                    "confidence": decision.task_analysis.confidence
                },
                "automation_level": decision.automation_level.value,
                "session_id": self.session_id
            }
        )

        print(f"📄 実装タスク作成: {file_path}")
        return task_id

    def _claude_analyze_implementation_task(self,
                                          file_path: str,
                                          task_type: str,
                                          implementation_spec: Dict[str, Any]) -> str:
        """実装タスク用Claude分析"""

        template_type = implementation_spec.get("template_type", "generic")
        complexity_estimate = implementation_spec.get("complexity", "medium")

        analysis = f"""
📊 Claude 実装タスク分析 - {task_type}

🎯 実装対象:
- ファイル: {file_path}
- タスクタイプ: {task_type}
- テンプレート: {template_type}
- 複雑度: {complexity_estimate}

🧠 実装方針:
"""

        if task_type == "new_implementation":
            analysis += """
- 純粋新規実装アプローチ
- テンプレートベースのコード生成
- 品質基準適合を必須とした実装
"""
        elif task_type == "hybrid_implementation":
            analysis += """
- 既存コードとの統合を考慮
- 段階的な実装アプローチ
- 既存機能への影響最小化
"""
        elif task_type == "new_feature_development":
            analysis += """
- 包括的な機能開発アプローチ
- 関連ファイルとの整合性確保
- テストケースを含む完全実装
"""

        # 実装仕様の詳細
        if "class_name" in implementation_spec:
            analysis += f"\n🏷️ クラス実装: {implementation_spec['class_name']}"
        if "methods" in implementation_spec:
            analysis += f"\n🔧 メソッド数: {len(implementation_spec['methods'])}件"
        if "functions" in implementation_spec:
            analysis += f"\n⚙️ 関数数: {len(implementation_spec['functions'])}件"

        analysis += f"""

🛡️ 品質保証:
- mypy strict mode適合必須
- コードスタイルガイド遵守
- 必要に応じてテスト作成
- ドキュメントコメント必須

📝 推奨アプローチ:
1. テンプレートベースでの基本構造作成
2. 段階的な実装と確認
3. 品質チェックとテスト実行
4. ドキュメントとコメントの充実
"""

        return analysis

    def _generate_implementation_instruction(self,
                                           file_path: str,
                                           task_type: str,
                                           implementation_spec: Dict[str, Any]) -> str:
        """実装指示生成（強化版パラメータ処理）"""

        # パラメータ検証・正規化
        validated_spec = self._validate_and_sanitize_implementation_spec(implementation_spec)
        template_type = validated_spec["template_type"]

        instruction = f"""
🎯 {task_type}実装指示 - {file_path}

📄 基本情報:
- ファイル: {file_path}
- タスクタイプ: {task_type}
- テンプレート: {template_type}
- 複雑度: {validated_spec.get("complexity", "medium")}

🔧 実装手順:
"""

        if template_type == "class":
            class_info = self._process_class_parameters(validated_spec)
            instruction += f"""
1. クラス {class_info['name']} の定義作成
   - 継承: {class_info['inheritance']}
   - 型パラメータ: {class_info['type_params']}
2. __init__ メソッドの実装
   - 引数: {class_info['init_params']}
   - 型注釈完全対応
"""
            for i, method_info in enumerate(class_info['methods'], 3):
                instruction += f"{i}. {method_info['name']} メソッドの実装\n"
                instruction += f"   - 引数: {method_info['params']}\n"
                instruction += f"   - 戻り値: {method_info['return_type']}\n"
                if method_info.get('description'):
                    instruction += f"   - 目的: {method_info['description']}\n"

        elif template_type == "module":
            module_info = self._process_module_parameters(validated_spec)
            instruction += "1. モジュールレベルのインポート設定\n"
            instruction += f"   - 必須インポート: {module_info['required_imports']}\n"
            for i, func_info in enumerate(module_info['functions'], 2):
                instruction += f"{i}. {func_info['name']} 関数の実装\n"
                instruction += f"   - 引数: {func_info['params']}\n"
                instruction += f"   - 戻り値: {func_info['return_type']}\n"
                if func_info.get('description'):
                    instruction += f"   - 目的: {func_info['description']}\n"

        elif template_type == "function":
            func_info = self._process_function_parameters(validated_spec)
            instruction += f"""
1. {func_info['name']} 関数の定義作成
   - 引数: {func_info['params']}
   - 戻り値: {func_info['return_type']}
   - 目的: {func_info.get('description', '主要機能の実装')}
2. メイン実行部の設定
   - エラーハンドリング必須
   - ログ出力対応
"""

        # 品質要件の詳細化
        quality_requirements = self._generate_quality_requirements(validated_spec, task_type)
        instruction += f"""

📁 必須要件:
{quality_requirements['basic_requirements']}

🛠️ 品質チェック:
{quality_requirements['quality_checks']}

🎯 成功基準:
{quality_requirements['success_criteria']}

🔍 検証手順:
{quality_requirements['verification_steps']}
"""

        return instruction

    def _validate_and_sanitize_implementation_spec(self, implementation_spec: Dict[str, Any]) -> Dict[str, Any]:
        """実装仕様の検証・正規化（強化版）"""

        # デフォルト値設定
        validated_spec = {
            "template_type": "generic",
            "complexity": "medium",
            "class_name": "NewClass",
            "function_name": "main_function",
            "methods": [],
            "functions": [],
            "create_tests": False,
            "documentation_level": "standard"
        }

        # 入力値の検証・マージ
        if isinstance(implementation_spec, dict):
            for key, value in implementation_spec.items():
                if key == "template_type" and value in ["class", "module", "function", "generic"]:
                    validated_spec[key] = value
                elif key == "complexity" and value in ["simple", "medium", "complex"]:
                    validated_spec[key] = value
                elif key in ["class_name", "function_name"] and isinstance(value, str) and value.strip():
                    validated_spec[key] = value.strip()
                elif key in ["methods", "functions"] and isinstance(value, list):
                    validated_spec[key] = self._sanitize_method_function_list(value)
                elif key in ["create_tests", "documentation_level"]:
                    validated_spec[key] = value

        return validated_spec

    def _sanitize_method_function_list(self, items: List[Any]) -> List[Dict[str, Any]]:
        """メソッド・関数リストの正規化"""

        sanitized_items = []

        for i, item in enumerate(items):
            if isinstance(item, dict):
                # 辞書型の場合、必要なキーを確認・補完
                sanitized_item = {
                    "name": item.get("name", f"method_{i+1}" if "method" in str(type(item)).lower() else f"function_{i+1}"),
                    "params": item.get("params", "self" if "method" in str(type(item)).lower() else ""),
                    "return_type": item.get("return_type", "None"),
                    "description": item.get("description", "")
                }
            elif isinstance(item, str) and item.strip():
                # 文字列型の場合、基本情報を設定
                sanitized_item = {
                    "name": item.strip(),
                    "params": "self" if "method" in str(type(item)).lower() else "",
                    "return_type": "None",
                    "description": ""
                }
            else:
                # 無効な型の場合、デフォルト値を設定
                sanitized_item = {
                    "name": f"item_{i+1}",
                    "params": "",
                    "return_type": "None",
                    "description": ""
                }

            sanitized_items.append(sanitized_item)

        return sanitized_items

    def _process_class_parameters(self, validated_spec: Dict[str, Any]) -> Dict[str, Any]:
        """クラスパラメータ処理"""

        class_name = validated_spec["class_name"]
        methods = validated_spec["methods"]

        # 継承情報の処理
        inheritance = validated_spec.get("inheritance", "")
        if inheritance and not inheritance.startswith("("):
            inheritance = f"({inheritance})"

        # 型パラメータの処理
        type_params = validated_spec.get("type_params", "")

        # __init__パラメータの処理
        init_params = validated_spec.get("init_params", "self")
        if not init_params.startswith("self"):
            init_params = f"self, {init_params}"

        return {
            "name": class_name,
            "inheritance": inheritance or "適用なし",
            "type_params": type_params or "適用なし",
            "init_params": init_params,
            "methods": methods
        }

    def _process_module_parameters(self, validated_spec: Dict[str, Any]) -> Dict[str, Any]:
        """モジュールパラメータ処理"""

        functions = validated_spec["functions"]

        # 必須インポートの処理
        required_imports = [
            "from typing import Any, Dict, List, Optional",
            "from kumihan_formatter.core.utilities.logger import get_logger"
        ]

        # 追加インポートの処理
        additional_imports = validated_spec.get("additional_imports", [])
        if isinstance(additional_imports, list):
            required_imports.extend(additional_imports)

        return {
            "functions": functions,
            "required_imports": required_imports
        }

    def _process_function_parameters(self, validated_spec: Dict[str, Any]) -> Dict[str, Any]:
        """関数パラメータ処理"""

        func_name = validated_spec["function_name"]

        # パラメータの処理
        params = validated_spec.get("params", "")
        return_type = validated_spec.get("return_type", "None")
        description = validated_spec.get("description", "主要機能の実装")

        return {
            "name": func_name,
            "params": params or "適用なし",
            "return_type": return_type,
            "description": description
        }

    def _generate_quality_requirements(self, validated_spec: Dict[str, Any], task_type: str) -> Dict[str, str]:
        """品質要件生成"""

        complexity = validated_spec["complexity"]
        create_tests = validated_spec["create_tests"]
        doc_level = validated_spec["documentation_level"]

        # 基本要件
        basic_requirements = """- すべての関数・メソッドに型注釈必須（mypy strict mode対応）
- docstring でのドキュメント必須（Google Style推奨）
- from typing import の適切なインポート
- エラーハンドリングとログ出力の実装
- プロジェクト標準コーディング規約遵守"""

        # 複雑度別要件追加
        if complexity == "complex":
            basic_requirements += "\n- 詳細なコメントによる実装意図の説明\n- 複雑な処理の分割・モジュール化"

        # 品質チェック
        quality_checks = """1. 実装完了後に Python 構文チェック（py_compile）
2. mypy strict mode チェック実行
3. Black + isort によるコードフォーマットチェック
4. flake8 によるリントチェック
5. セキュリティチェック（基本パターン）"""

        if create_tests:
            quality_checks += "\n6. pytest による単体テスト実行"

        # 成功基準
        success_criteria = """✅ ファイルが正常に作成される
✅ 全ての関数・メソッドに適切な型注釈
✅ Python 構文エラー 0件
✅ mypy strict mode エラー 0件
✅ 適切な docstring ドキュメント
✅ コードスタイルガイド準拠（Black + isort）
✅ リントチェック合格（flake8）"""

        if create_tests:
            success_criteria += "\n✅ テストケース作成・実行成功"

        # 検証手順
        verification_steps = """1. 構文検証（Layer 1）- AST解析・基本型チェック
2. 品質検証（Layer 2）- リント・フォーマット・セキュリティ
3. Claude最終承認（Layer 3）- 総合品質評価・実装方針確認
4. 3層検証完全通過の確認"""

        return {
            "basic_requirements": basic_requirements,
            "quality_checks": quality_checks,
            "success_criteria": success_criteria,
            "verification_steps": verification_steps
        }

    def _create_with_gemini_mode(self, target_files: List[str], error_type: str,
                                priority: str, use_micro_tasks: bool, decision, task_type: str = "code_modification") -> List[str]:
        """Gemini協業モードでのタスク作成"""

        created_task_ids = []

        for file_path in target_files:
            print(f"\n📄 ファイル分析: {file_path}")

            if use_micro_tasks and task_type == "code_modification":
                # タスク微分化: ファイル → 関数レベル分割（コード修正タスクのみ）
                micro_tasks = self.task_analyzer.analyze_file_for_micro_tasks(file_path, error_type)

                if micro_tasks:
                    # 実行計画作成
                    execution_plan = self.task_analyzer.create_step_by_step_plan(micro_tasks)

                    print(f"🎯 微細タスク生成: {len(micro_tasks)}件")
                    print(f"⏱️ 総所要時間: {execution_plan['total_estimated_time']}分")

                    # バッチ処理でタスク作成
                    for batch in execution_plan['batch_recommendations']:
                        batch_task_id = self._create_batch_task(
                            batch, file_path, error_type, priority, execution_plan
                        )
                        created_task_ids.append(batch_task_id)

                else:
                    # フォールバック: ファイル全体タスク
                    fallback_task_id = self._create_file_level_task(
                        file_path, error_type, priority
                    )
                    created_task_ids.append(fallback_task_id)
            else:
                # 従来方式: ファイル単位処理
                file_task_id = self._create_file_level_task(file_path, error_type, priority)
                created_task_ids.append(file_task_id)

        return created_task_ids

    def _create_with_claude_mode(self, target_files: List[str], error_type: str,
                                priority: str, decision, task_type: str = "code_modification") -> List[str]:
        """Claude単独モードでのタスク作成"""

        print("📝 Claude単独モードでタスク作成（Gemini使用なし）")

        # 簡易ファイルレベルタスクのみ作成
        created_task_ids = []
        for file_path in target_files:
            task_id = self._create_claude_only_task(file_path, error_type, priority, decision)
            created_task_ids.append(task_id)

        return created_task_ids

    def _create_claude_only_task(self, file_path: str, error_type: str,
                                priority: str, decision) -> str:
        """Claude単独タスク作成"""

        claude_analysis = self._claude_analyze_files([file_path], error_type)

        task_id = self.task_manager.create_task(
            task_type="claude_only_modification",
            description=f"{error_type} Claude単独修正 - {file_path}",
            target_files=[file_path],
            priority=priority,
            requirements={
                "error_type": error_type,
                "fix_pattern": self._get_fix_pattern(error_type),
                "claude_only": True,
                "decision_reasoning": decision.reasoning
            },
            claude_analysis=claude_analysis,
            expected_outcome=f"{error_type} エラーをClaude単独で修正",
            constraints=[
                "Gemini使用なし",
                "Claude Code標準手法のみ使用",
                "段階的・確実な修正"
            ],
            context={
                "decision_engine_result": decision.task_analysis.__dict__,
                "automation_level": decision.automation_level.value,
                "session_id": self.session_id
            }
        )

        print(f"📄 Claude単独タスク作成: {file_path}")
        return task_id

    def _auto_execute_tasks(self, task_ids: List[str], decision) -> None:
        """自動実行"""

        print(f"⚡ 自動実行開始: {len(task_ids)}タスク")

        start_time = time.time()
        results = []

        for i, task_id in enumerate(task_ids, 1):
            print(f"\n🔄 自動実行 {i}/{len(task_ids)}: {task_id}")

            try:
                result = self.execute_workflow_cycle()
                results.append(result)

                # 実行結果チェック
                if result.get("status") != "completed":
                    print(f"⚠️ タスク {task_id} 実行失敗、自動実行を停止")
                    break

                # Claude品質レビュー
                claude_review = result.get("claude_review", {})
                approval = claude_review.get("approval", "unknown")

                if approval == "rejected":
                    print(f"❌ タスク {task_id} 品質不合格、自動実行を停止")
                    break
                elif approval == "requires_review":
                    print(f"🤚 タスク {task_id} 手動レビュー必要、自動実行を一時停止")
                    break

                print(f"✅ タスク {task_id} 自動実行成功 ({approval})")

            except Exception as e:
                print(f"❌ タスク {task_id} 実行エラー: {e}")
                break

        execution_time = time.time() - start_time

        # 自動実行サマリー
        successful = len([r for r in results if r.get("status") == "completed"])
        total_cost = sum(r.get("claude_review", {}).get("quality_metrics", {}).get("errors_fixed", 0)
                        for r in results) * decision.task_analysis.estimated_cost / max(1, len(task_ids))

        print(f"\n📊 自動実行サマリー:")
        print(f"   成功: {successful}/{len(task_ids)}タスク")
        print(f"   実行時間: {execution_time:.1f}秒")
        print(f"   推定コスト: ${total_cost:.4f}")
        print(f"   効率性: {decision.task_analysis.gemini_benefit_score:.2f}")

    def get_decision_stats(self) -> Dict[str, Any]:
        """判定統計情報取得"""
        return self.decision_engine.get_decision_stats()

    def set_automation_preferences(self, preferences: Dict[str, Any]) -> None:
        """自動化設定変更"""

        # WorkflowDecisionEngine設定更新
        self.decision_engine.thresholds.update(preferences.get("thresholds", {}))

        print(f"⚙️ 自動化設定更新: {preferences}")

    def _create_batch_task(self, batch: Dict[str, Any], file_path: str,
                          error_type: str, priority: str, execution_plan: Dict) -> str:
        """バッチタスク作成（Flash 2.5最適化）"""

        batch_id = batch['batch_id']
        tasks = batch['tasks']

        # Flash 2.5向け具体的指示生成（品質保証付き）
        flash_instruction = self._generate_batch_flash_instruction(tasks, error_type, file_path)

        # Claude による詳細分析
        claude_analysis = self._claude_analyze_micro_tasks(tasks, error_type, file_path)

        task_id = self.task_manager.create_task(
            task_type="micro_code_modification",
            description=f"{error_type} バッチ修正 - {file_path} Batch#{batch_id}",
            target_files=[file_path],
            priority=priority,
            requirements={
                "error_type": error_type,
                "batch_info": batch,
                "micro_tasks": tasks,
                "flash_instruction": flash_instruction,
                "max_context_tokens": 2000,
                "step_by_step": True
            },
            claude_analysis=claude_analysis,
            expected_outcome=f"バッチ内全タスク完了 ({len(tasks)}件)",
            constraints=[
                "Flash 2.5コンテキスト制限遵守",
                "1バッチ20分以内",
                "具体的指示に従った修正のみ"
            ],
            context={
                "batch_id": batch_id,
                "total_batches": len(execution_plan['batch_recommendations']),
                "execution_plan": execution_plan['flash25_optimization'],
                "session_id": self.session_id
            }
        )

        print(f"📦 バッチタスク作成: Batch#{batch_id} ({len(tasks)}件, {batch['estimated_time']}分)")
        return task_id

    def _create_file_level_task(self, file_path: str, error_type: str, priority: str) -> str:
        """ファイルレベルタスク作成（フォールバック）"""

        # 従来方式の分析
        claude_analysis = self._claude_analyze_files([file_path], error_type)

        task_id = self.task_manager.create_task(
            task_type="file_code_modification",
            description=f"{error_type} ファイル修正 - {file_path}",
            target_files=[file_path],
            priority=priority,
            requirements={
                "error_type": error_type,
                "fix_pattern": self._get_fix_pattern(error_type),
                "test_required": True,
                "quality_check": True
            },
            claude_analysis=claude_analysis,
            expected_outcome=f"{error_type} エラーを0件に削減",
            constraints=[
                "既存機能への影響最小化",
                "テスト通過必須",
                "pre-commit hooks通過必須"
            ],
            context={
                "fallback_mode": True,
                "session_id": self.session_id
            }
        )

        print(f"📄 ファイルタスク作成: {file_path}")
        return task_id

    def _generate_batch_flash_instruction(self, tasks: List[Dict], error_type: str, file_path: str = "") -> str:
        """品質保証付きバッチ用Flash 2.5指示生成"""

        # 強化版テンプレートを使用
        enhanced_instruction = self.enhanced_templates.generate_quality_assured_instruction(
            error_type, tasks, file_path
        )

        # エラー防止ガイドを追加
        error_prevention_guide = self.enhanced_templates.get_error_prevention_guide(error_type)

        final_instruction = f"""
{enhanced_instruction}

{error_prevention_guide}

🔒 品質保証チェックポイント:
1. 修正前: 対象関数の確認
2. 修正中: 構文エラーの即座確認
3. 修正後: Python構文検証実行
4. 完了後: 全体品質チェック実行

⚠️ エラー発生時の対応:
- 構文エラー → 禁止パターンをチェック・修正
- 型注釈エラー → 正解パターンを確認・適用
- import エラー → 'from typing import Any' を追加
- 不明時 → 'Any' 型を使用

🎯 最終確認項目:
□ 全関数に型注釈追加完了
□ Python構文エラー 0件
□ 必要なimport文追加完了
□ 修正内容が期待通り
"""

        return final_instruction

    def _claude_analyze_micro_tasks(self, tasks: List[Dict], error_type: str, file_path: str) -> str:
        """微細タスク用Claude分析"""

        analysis = f"""
📊 Claude微細タスク分析 - {error_type}

🎯 対象ファイル: {file_path}
🔧 エラータイプ: {error_type}
📦 バッチサイズ: {len(tasks)}件

🧠 分析結果:
"""

        for task in tasks:
            func_name = task.get('target_function', 'unknown')
            complexity = task.get('complexity', 'medium')
            error_count = task.get('error_count', 0)

            analysis += f"""
  • {func_name}関数:
    - エラー数: {error_count}件
    - 複雑度: {complexity}
    - 推定時間: {task.get('estimated_time', 10)}分
    - Flash指示: 適用済み
"""

        analysis += f"""
⚠️ Flash 2.5 考慮事項:
- コンテキスト制限: 2000トークン以内
- 具体的例示による指示
- 段階的実行による確実性
- エラー時の適切なフォールバック

📋 推奨アプローチ:
1. 関数単位での逐次処理
2. 修正パターンの厳格適用
3. 各ステップでの検証
4. 予期しない状況でのtype: ignore使用
"""

        return analysis

    def execute_workflow_cycle(self) -> Dict[str, Any]:
        """1サイクルのワークフロー実行"""

        print("\n🔄 ワークフロー サイクル開始")

        # Step 1: Claude - 次のタスクを取得
        task_data = self.gemini_helper.get_next_task()

        if not task_data:
            print("📭 実行待ちタスクなし")
            return {"status": "no_tasks", "message": "実行待ちタスクがありません"}

        print(f"📋 実行タスク: {task_data['task_id']}")
        print(f"📝 説明: {task_data['description']}")

        # Step 2: Gemini - タスク実行
        print("\n🚀 Gemini CLI でタスク実行中...")

        start_time = time.time()

        # Gemini CLI経由でタスク実行
        gemini_result = self._execute_with_gemini(task_data)

        execution_time = time.time() - start_time

        # Step 3: Claude - 結果レビュー・検証
        print("\n🔍 Claude による結果レビュー...")

        claude_review = self._claude_review_result(gemini_result)

        # Step 4: 統合レポート作成
        cycle_result = {
            "session_id": self.session_id,
            "cycle_timestamp": datetime.datetime.now().isoformat(),
            "task_executed": task_data,
            "gemini_result": gemini_result,
            "claude_review": claude_review,
            "execution_time": execution_time,
            "status": "completed",
            "next_recommendations": self._generate_next_recommendations(gemini_result, claude_review)
        }

        # セッションログ保存
        self._save_cycle_log(cycle_result)

        print(f"\n✅ ワークフローサイクル完了 ({execution_time:.1f}秒)")

        return cycle_result

    def run_continuous_workflow(self, max_cycles: int = 10) -> List[Dict[str, Any]]:
        """連続ワークフロー実行"""

        print(f"\n🔄 連続ワークフロー開始 (最大{max_cycles}サイクル)")

        results = []

        for cycle in range(max_cycles):
            print(f"\n" + "="*60)
            print(f"🔄 Cycle {cycle + 1}/{max_cycles}")
            print("="*60)

            cycle_result = self.execute_workflow_cycle()
            results.append(cycle_result)

            # タスクがない場合は終了
            if cycle_result["status"] == "no_tasks":
                print(f"\n🏁 全タスク完了 (実行サイクル: {cycle + 1})")
                break

            # 短い休息
            if cycle < max_cycles - 1:
                print("⏳ 次のサイクルまで3秒待機...")
                time.sleep(3)

        # 最終統計
        self._print_session_summary(results)

        return results

    def __del__(self):
        """デストラクタ - ハイブリッドシステムクリーンアップ"""
        if hasattr(self, 'success_monitor'):
            try:
                self.cleanup_hybrid_systems()
            except:
                pass

    def _claude_analyze_files(self, target_files: List[str], error_type: str) -> str:
        """Claude による詳細事前分析"""

        print(f"🧠 Claude分析開始: {error_type} エラー")

        analysis_results = []
        total_errors = 0
        complexity_factors = []

        for file_path in target_files:
            if not os.path.exists(file_path):
                continue

            # ファイル詳細分析
            file_analysis = self._analyze_file_complexity(file_path, error_type)
            analysis_results.append(file_analysis)
            total_errors += file_analysis.get("error_count", 0)
            complexity_factors.extend(file_analysis.get("complexity_factors", []))

        # 総合分析
        overall_complexity = self._assess_overall_complexity(analysis_results, error_type)
        risk_assessment = self._assess_modification_risk(analysis_results)
        recommended_strategy = self._recommend_fix_strategy(error_type, overall_complexity, total_errors)

        analysis = f"""
📊 Claude 詳細事前分析 - {error_type} エラー修正

🎯 対象範囲:
- ファイル数: {len(target_files)}件
- 総エラー数: {total_errors}件
- 修正複雑度: {overall_complexity['level']} ({overall_complexity['score']}/10)
- 推定所要時間: {overall_complexity['estimated_time']}分

📁 ファイル別分析:
{self._format_file_analysis(analysis_results)}

⚠️ リスク評価:
{self._format_risk_assessment(risk_assessment)}

🎯 推奨戦略:
{recommended_strategy}

🔧 Flash 2.5 最適化:
- 微細タスク分割: {'推奨' if total_errors > 10 else '不要'}
- バッチサイズ: {min(3, max(1, total_errors // 5))}タスク/バッチ
- コンテキスト制限: 2000トークン/タスク

📋 成功要因:
1. 段階的・確実な修正アプローチ
2. 各ステップでの品質確認
3. 既存機能への影響最小化
4. 適切なテスト実行
"""

        return analysis

    def _analyze_file_complexity(self, file_path: str, error_type: str) -> Dict[str, Any]:
        """ファイル複雑度分析"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 基本メトリクス
            lines = content.split('\n')
            line_count = len(lines)
            function_count = content.count('def ')
            class_count = content.count('class ')

            # エラー数カウント
            error_count = self._count_file_errors(file_path, error_type)

            # 複雑度要因特定
            complexity_factors = []
            if line_count > 500:
                complexity_factors.append("大規模ファイル")
            if function_count > 20:
                complexity_factors.append("多数の関数")
            if class_count > 5:
                complexity_factors.append("複数クラス")
            if 'import' in content and content.count('import') > 10:
                complexity_factors.append("多数のインポート")
            if 'typing' in content:
                complexity_factors.append("既存型注釈")

            # 複雑度スコア計算
            complexity_score = min(10, (
                line_count // 100 +
                function_count // 5 +
                class_count * 2 +
                error_count // 3
            ))

            return {
                "file_path": file_path,
                "line_count": line_count,
                "function_count": function_count,
                "class_count": class_count,
                "error_count": error_count,
                "complexity_score": complexity_score,
                "complexity_factors": complexity_factors,
                "estimated_time": max(5, error_count * 2 + complexity_score)
            }

        except Exception as e:
            return {
                "file_path": file_path,
                "error": str(e),
                "complexity_score": 5,
                "estimated_time": 10
            }

    def _count_file_errors(self, file_path: str, error_type: str) -> int:
        """ファイルのエラー数カウント"""
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict", file_path],
                capture_output=True,
                text=True
            )

            error_count = 0
            for line in result.stdout.split('\n'):
                if error_type in line and 'error:' in line:
                    error_count += 1

            return error_count
        except:
            return 0

    def _assess_overall_complexity(self, analysis_results: List[Dict], error_type: str) -> Dict[str, Any]:
        """全体複雑度評価"""

        if not analysis_results:
            return {"level": "低", "score": 1, "estimated_time": 10}

        avg_score = sum(a.get("complexity_score", 5) for a in analysis_results) / len(analysis_results)
        total_time = sum(a.get("estimated_time", 10) for a in analysis_results)

        if avg_score <= 3:
            level = "低"
        elif avg_score <= 6:
            level = "中"
        else:
            level = "高"

        return {
            "level": level,
            "score": round(avg_score, 1),
            "estimated_time": total_time
        }

    def _assess_modification_risk(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """修正リスク評価"""

        risk_factors = []
        mitigation_strategies = []

        for analysis in analysis_results:
            factors = analysis.get("complexity_factors", [])

            if "大規模ファイル" in factors:
                risk_factors.append("大規模ファイル修正による影響範囲拡大")
                mitigation_strategies.append("関数単位での段階的修正")

            if "既存型注釈" in factors:
                risk_factors.append("既存型注釈との整合性問題")
                mitigation_strategies.append("既存注釈の詳細確認")

            if "複数クラス" in factors:
                risk_factors.append("クラス間依存関係への影響")
                mitigation_strategies.append("クラス別修正・テスト実行")

        risk_level = "高" if len(risk_factors) > 3 else "中" if len(risk_factors) > 1 else "低"

        return {
            "level": risk_level,
            "factors": risk_factors,
            "mitigation": mitigation_strategies
        }

    def _recommend_fix_strategy(self, error_type: str, complexity: Dict, total_errors: int) -> str:
        """修正戦略推奨"""

        strategy = f"""
🎯 {error_type} 修正戦略:

"""

        if total_errors <= 5:
            strategy += "【シンプル戦略】\n- ファイル単位での一括修正\n- 標準的な修正パターン適用"
        elif total_errors <= 20:
            strategy += "【バランス戦略】\n- 関数単位での段階的修正\n- バッチ処理による効率化"
        else:
            strategy += "【微細分割戦略】\n- 関数レベルでの細分化\n- Flash 2.5最適化バッチ処理"

        if complexity["level"] == "高":
            strategy += "\n\n⚠️ 高複雑度対応:\n- 詳細な事前テスト\n- 修正後の全体影響確認\n- 段階的リリース推奨"

        return strategy

    def _format_file_analysis(self, analysis_results: List[Dict]) -> str:
        """ファイル分析結果フォーマット"""

        formatted = ""
        for analysis in analysis_results[:5]:  # 最大5件表示
            path = analysis.get("file_path", "unknown")
            errors = analysis.get("error_count", 0)
            score = analysis.get("complexity_score", 0)
            time = analysis.get("estimated_time", 0)

            formatted += f"  • {path}\n"
            formatted += f"    エラー: {errors}件, 複雑度: {score}/10, 時間: {time}分\n"

        if len(analysis_results) > 5:
            formatted += f"  ... 他{len(analysis_results) - 5}ファイル\n"

        return formatted

    def _format_risk_assessment(self, risk_assessment: Dict) -> str:
        """リスク評価フォーマット"""

        level = risk_assessment["level"]
        factors = risk_assessment["factors"]
        mitigation = risk_assessment["mitigation"]

        formatted = f"リスクレベル: {level}\n"

        if factors:
            formatted += "主要リスク要因:\n"
            for factor in factors[:3]:
                formatted += f"  - {factor}\n"

        if mitigation:
            formatted += "推奨対策:\n"
            for strategy in mitigation[:3]:
                formatted += f"  + {strategy}\n"

        return formatted

    def _get_fix_pattern(self, error_type: str) -> str:
        """エラータイプ別の修正パターン"""
        patterns = {
            "no-untyped-def": "add_return_type_annotations",
            "no-untyped-call": "add_type_ignore_or_stubs",
            "type-arg": "add_generic_type_parameters",
            "call-arg": "fix_function_arguments",
            "attr-defined": "fix_attribute_access"
        }
        return patterns.get(error_type, "generic_fix")

    def _execute_with_gemini(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """品質保証付きGemini CLI でのタスク実行"""

        try:
            # Gemini Helper経由で実行
            print("🔄 Gemini実行中...")
            raw_result = self.gemini_helper.execute_task(task_data)

            # 品質保証フェーズ
            print("🛡️ 構文検証・品質保証開始...")
            quality_assured_result = self._apply_quality_assurance(raw_result, task_data)

            # 実際のToken使用量でコスト追跡（動的測定）
            actual_token_usage = self._measure_actual_token_usage(
                quality_assured_result, task_id, "gemini-2.5-flash"
            )

            self.task_manager.track_cost(task_data["task_id"], actual_token_usage)

            print(f"💰 コスト追跡: 入力Token={actual_token_usage.get('input_tokens', 0)}, "
                  f"出力Token={actual_token_usage.get('output_tokens', 0)}")

            if "measurement_method" in actual_token_usage:
                print(f"📊 測定方式: {actual_token_usage['measurement_method']}")

            return quality_assured_result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_data["task_id"]
            }

    def _apply_quality_assurance(self, gemini_result: Dict[str, Any],
                                task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini結果への品質保証適用"""

        print("🔍 Gemini出力品質検証中...")

        modifications = gemini_result.get("modifications", {})
        files_modified = modifications.get("files_modified", [])

        quality_issues = []
        quality_fixes = []
        total_syntax_fixes = 0

        for file_mod in files_modified:
            file_path = file_mod.get("file", "")

            if not file_path or not os.path.exists(file_path):
                continue

            try:
                # 修正されたファイルの内容を読み取り
                with open(file_path, 'r', encoding='utf-8') as f:
                    modified_code = f.read()

                # 構文検証実行
                validation_result = self.syntax_validator.comprehensive_validation(
                    modified_code, file_path
                )

                print(f"📊 {file_path} 検証結果:")
                print(f"   構文OK: {validation_result['syntax_valid']}")
                print(f"   型注釈OK: {validation_result['type_annotations_valid']}")
                print(f"   品質スコア: {validation_result['validation_score']:.2f}")

                # 品質問題の記録
                if not validation_result['syntax_valid']:
                    quality_issues.extend(validation_result['syntax_errors'])

                if not validation_result['type_annotations_valid']:
                    quality_issues.extend(validation_result['type_errors'])

                # 自動修正の適用
                if validation_result['fixed_code'] and (
                    not validation_result['syntax_valid'] or
                    not validation_result['type_annotations_valid']
                ):
                    print(f"🔧 {file_path} 自動修正適用中...")

                    # 修正されたコードでファイルを更新
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(validation_result['fixed_code'])

                    quality_fixes.append(f"{file_path}: 構文エラー自動修正")
                    total_syntax_fixes += 1

                    # 修正後の再検証
                    revalidation = self.syntax_validator.comprehensive_validation(
                        validation_result['fixed_code'], file_path
                    )

                    print(f"✅ {file_path} 修正後: スコア {revalidation['validation_score']:.2f}")

                # ファイル修正情報の更新
                file_mod["quality_validation"] = {
                    "syntax_valid": validation_result['syntax_valid'],
                    "type_annotations_valid": validation_result['type_annotations_valid'],
                    "validation_score": validation_result['validation_score'],
                    "auto_fixed": bool(validation_result['fixed_code'])
                }

            except Exception as e:
                quality_issues.append(f"{file_path}: 品質検証エラー - {str(e)}")

        # 品質保証結果の統合
        enhanced_result = gemini_result.copy()
        enhanced_result["quality_assurance"] = {
            "syntax_validation_applied": True,
            "quality_issues_found": quality_issues,
            "quality_fixes_applied": quality_fixes,
            "total_syntax_fixes": total_syntax_fixes,
            "overall_quality_score": self._calculate_overall_quality_score(files_modified)
        }

        # 修正情報の更新
        if total_syntax_fixes > 0:
            enhanced_result["modifications"]["supervisor_fixes"] = total_syntax_fixes
            enhanced_result["modifications"]["quality_enhanced"] = True

            print(f"🔧 監督者品質修正: {total_syntax_fixes}件の構文エラー修正完了")

        if quality_issues:
            print(f"⚠️ 品質問題検出: {len(quality_issues)}件")
            for issue in quality_issues[:5]:  # 最初の5件のみ表示
                print(f"  - {issue}")
        else:
            print("✅ 品質検証: 問題なし")

        return enhanced_result

    def _calculate_overall_quality_score(self, files_modified: List[Dict]) -> float:
        """全体品質スコア計算"""

        if not files_modified:
            return 0.0

        total_score = 0.0
        valid_files = 0

        for file_mod in files_modified:
            quality_val = file_mod.get("quality_validation")
            if quality_val:
                total_score += quality_val.get("validation_score", 0.0)
                valid_files += 1

        return total_score / max(1, valid_files)

    def _claude_review_result(self, gemini_result: Dict[str, Any]) -> Dict[str, Any]:
        """Claude による詳細結果レビュー・品質評価"""

        print("🔍 Claude品質レビュー開始")

        status = gemini_result.get("status", "unknown")
        modifications = gemini_result.get("modifications", {})
        gemini_report = gemini_result.get("gemini_report", {})

        # 多角的品質評価
        quality_assessment = self._assess_code_quality(modifications)
        completeness_check = self._check_completeness(modifications, gemini_result)
        risk_evaluation = self._evaluate_modification_risk(modifications)
        test_validation = self._validate_test_results(modifications)

        # 総合判定
        overall_score = self._calculate_overall_score(
            quality_assessment, completeness_check, risk_evaluation, test_validation
        )

        approval_decision = self._make_approval_decision(overall_score, status)

        # リトライ・フォローアップ提案
        followup_actions = self._generate_followup_actions(
            approval_decision, quality_assessment, modifications
        )

        review = {
            "overall_quality": approval_decision["quality_level"],
            "approval": approval_decision["decision"],
            "confidence_score": overall_score,
            "detailed_assessment": {
                "code_quality": quality_assessment,
                "completeness": completeness_check,
                "risk_evaluation": risk_evaluation,
                "test_validation": test_validation
            },
            "quality_metrics": {
                "errors_fixed": modifications.get("total_errors_fixed", 0),
                "files_modified": len(modifications.get("files_modified", [])),
                "modification_scope": self._assess_modification_scope(modifications),
                "regression_risk": risk_evaluation.get("level", "medium")
            },
            "recommendations": followup_actions["recommendations"],
            "required_actions": followup_actions["required_actions"],
            "retry_strategy": followup_actions.get("retry_strategy"),
            "claude_feedback": self._generate_claude_feedback(gemini_report, overall_score)
        }

        print(f"📊 レビュー完了: {approval_decision['decision']} (信頼度: {overall_score:.2f})")

        return review

    def _assess_code_quality(self, modifications: Dict) -> Dict[str, Any]:
        """コード品質評価"""

        files_modified = modifications.get("files_modified", [])
        quality_checks = modifications.get("quality_checks", {})

        quality_score = 0.0
        quality_issues = []
        quality_positives = []

        # 修正内容の質評価
        for file_mod in files_modified:
            errors_fixed = file_mod.get("errors_fixed", 0)
            changes = file_mod.get("changes", "")

            if errors_fixed > 0:
                quality_positives.append(f"{file_mod['file']}: {errors_fixed}エラー修正")
                quality_score += 0.2

            if "type annotation" in changes or "type: ignore" in changes:
                quality_positives.append("適切な型処理")
                quality_score += 0.1

        # 品質チェック結果評価
        for tool, result in quality_checks.items():
            if result == "passed" or result == "available":
                quality_score += 0.15
            else:
                quality_issues.append(f"{tool}チェック失敗")

        # テスト通過状況
        if modifications.get("tests_passed", False):
            quality_positives.append("テスト全通過")
            quality_score += 0.3
        else:
            quality_issues.append("テスト未通過または未実行")

        return {
            "score": min(1.0, quality_score),
            "level": "high" if quality_score >= 0.7 else "medium" if quality_score >= 0.4 else "low",
            "positives": quality_positives,
            "issues": quality_issues
        }

    def _check_completeness(self, modifications: Dict, gemini_result: Dict) -> Dict[str, Any]:
        """完了度チェック"""

        task_data = gemini_result.get("task_executed", {})
        requirements = task_data.get("requirements", {})
        expected_fixes = requirements.get("error_count", 0) or 1
        actual_fixes = modifications.get("total_errors_fixed", 0)

        completion_rate = actual_fixes / max(1, expected_fixes)

        completeness_issues = []
        if completion_rate < 0.8:
            completeness_issues.append(f"修正完了率低: {completion_rate:.1%}")

        if not modifications.get("quality_checks"):
            completeness_issues.append("品質チェック未実行")

        return {
            "completion_rate": completion_rate,
            "level": "complete" if completion_rate >= 0.9 else "partial" if completion_rate >= 0.6 else "incomplete",
            "expected_fixes": expected_fixes,
            "actual_fixes": actual_fixes,
            "issues": completeness_issues
        }

    def _evaluate_modification_risk(self, modifications: Dict) -> Dict[str, Any]:
        """修正リスク評価"""

        files_modified = modifications.get("files_modified", [])

        risk_factors = []
        risk_score = 0.0

        for file_mod in files_modified:
            lines_changed = file_mod.get("lines_changed", 0)
            file_path = file_mod.get("file", "")

            if lines_changed > 50:
                risk_factors.append(f"大規模修正: {file_path}")
                risk_score += 0.3

            if "core" in file_path or "main" in file_path:
                risk_factors.append(f"重要ファイル修正: {file_path}")
                risk_score += 0.2

        # テスト失敗リスク
        if not modifications.get("tests_passed", False):
            risk_factors.append("テスト未通過")
            risk_score += 0.4

        risk_level = "high" if risk_score >= 0.7 else "medium" if risk_score >= 0.3 else "low"

        return {
            "level": risk_level,
            "score": risk_score,
            "factors": risk_factors
        }

    def _validate_test_results(self, modifications: Dict) -> Dict[str, Any]:
        """テスト結果検証"""

        tests_passed = modifications.get("tests_passed", False)
        quality_checks = modifications.get("quality_checks", {})

        validation_score = 0.0
        validation_issues = []

        if tests_passed:
            validation_score += 0.5
        else:
            validation_issues.append("テスト実行失敗または未実行")

        # 各品質チェックツールの結果
        for tool, result in quality_checks.items():
            if result in ["passed", "available"]:
                validation_score += 0.1
            else:
                validation_issues.append(f"{tool}検証失敗")

        return {
            "score": min(1.0, validation_score),
            "level": "passed" if validation_score >= 0.6 else "failed",
            "issues": validation_issues
        }

    def _calculate_overall_score(self, quality: Dict, completeness: Dict,
                                risk: Dict, test: Dict) -> float:
        """総合スコア計算"""

        # 重み付け平均
        weights = {
            "quality": 0.3,
            "completeness": 0.3,
            "risk": -0.2,  # リスクは負の重み
            "test": 0.3
        }

        score = (
            quality["score"] * weights["quality"] +
            completeness["completion_rate"] * weights["completeness"] +
            (1.0 - risk["score"]) * abs(weights["risk"]) +
            test["score"] * weights["test"]
        )

        return max(0.0, min(1.0, score))

    def _make_approval_decision(self, score: float, status: str) -> Dict[str, str]:
        """承認判定"""

        if status != "completed":
            return {"decision": "rejected", "quality_level": "failed"}

        if score >= 0.8:
            return {"decision": "approved", "quality_level": "excellent"}
        elif score >= 0.6:
            return {"decision": "approved_with_conditions", "quality_level": "good"}
        elif score >= 0.4:
            return {"decision": "requires_review", "quality_level": "needs_improvement"}
        else:
            return {"decision": "rejected", "quality_level": "poor"}

    def _generate_followup_actions(self, approval: Dict, quality: Dict,
                                  modifications: Dict) -> Dict[str, Any]:
        """フォローアップアクション生成"""

        recommendations = []
        required_actions = []
        retry_strategy = None

        decision = approval["decision"]

        if decision == "approved":
            recommendations.extend([
                "関連ファイルでの同様修正の実施",
                "統合テストの実行",
                "コードレビューの実施"
            ])

        elif decision == "approved_with_conditions":
            required_actions.extend([
                "追加テストの実行",
                "品質メトリクスの確認"
            ])
            recommendations.extend([
                "段階的リリースの検討",
                "監視体制の強化"
            ])

        elif decision == "requires_review":
            required_actions.extend([
                "手動コードレビューの実施",
                "影響範囲の詳細確認",
                "修正内容の検証"
            ])

            retry_strategy = {
                "approach": "manual_review",
                "priority": "high",
                "estimated_time": "30-60分"
            }

        elif decision == "rejected":
            required_actions.extend([
                "エラー原因の詳細分析",
                "修正アプローチの見直し",
                "タスクの再実行"
            ])

            retry_strategy = {
                "approach": "retry_with_modifications",
                "priority": "immediate",
                "estimated_time": "15-30分",
                "modifications": [
                    "より具体的な指示",
                    "段階的な修正アプローチ",
                    "エラー処理の強化"
                ]
            }

        # 品質問題に基づく追加推奨
        if quality["level"] == "low":
            recommendations.append("修正パターンの見直し")

        return {
            "recommendations": recommendations,
            "required_actions": required_actions,
            "retry_strategy": retry_strategy
        }

    def _assess_modification_scope(self, modifications: Dict) -> str:
        """修正範囲評価"""

        files_count = len(modifications.get("files_modified", []))
        total_errors = modifications.get("total_errors_fixed", 0)

        if files_count <= 1 and total_errors <= 5:
            return "minimal"
        elif files_count <= 3 and total_errors <= 15:
            return "moderate"
        else:
            return "extensive"

    def _generate_claude_feedback(self, gemini_report: Dict, score: float) -> str:
        """Claude フィードバック生成"""

        feedback = f"""
📝 Claude 品質レビューフィードバック

🎯 総合評価: {score:.2f}/1.0

"""

        if score >= 0.8:
            feedback += """✅ 優秀な修正結果
- Flash 2.5が適切に指示を理解し実行
- 期待される品質基準を満足
- 安全で確実な修正が完了"""

        elif score >= 0.6:
            feedback += """⚠️ 良好だが改善余地あり
- 基本的な修正は適切に実行
- 一部の品質指標で改善の余地
- フォローアップでの品質向上を推奨"""

        else:
            feedback += """❌ 修正品質に問題
- Flash 2.5の理解または実行に課題
- 指示の明確化または手法の見直しが必要
- リトライまたは手動確認を推奨"""

        # Geminiレポートの評価
        approach = gemini_report.get("approach", "")
        if approach:
            feedback += f"\n\n🤖 Gemini実行アプローチ: {approach}"

        return feedback

    def _generate_next_recommendations(self, gemini_result: Dict[str, Any], claude_review: Dict[str, Any]) -> List[str]:
        """次のアクション推奨生成"""

        recommendations = []

        if claude_review.get("approval") == "approved":
            recommendations.extend([
                "同様のエラータイプで次のファイル群を処理",
                "統合テストの実行",
                "品質メトリクスの更新"
            ])
        else:
            recommendations.extend([
                "エラー原因の詳細分析",
                "修正アプローチの見直し",
                "手動確認による問題特定"
            ])

        return recommendations

    def _save_cycle_log(self, cycle_result: Dict[str, Any]) -> None:
        """サイクル実行ログ保存"""

        log_file = self.task_manager.monitoring_dir / f"session_{self.session_id}.json"

        # 既存ログ読み込み
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                session_log = json.load(f)
        else:
            session_log = {
                "session_id": self.session_id,
                "start_time": datetime.datetime.now().isoformat(),
                "cycles": []
            }

        # 新しいサイクル追加
        session_log["cycles"].append(cycle_result)
        session_log["last_update"] = datetime.datetime.now().isoformat()

        # 保存
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(session_log, f, indent=2, ensure_ascii=False)

    def _print_session_summary(self, results: List[Dict[str, Any]]) -> None:
        """セッション統計表示"""

        print("\n" + "="*60)
        print("📊 セッション統計")
        print("="*60)

        total_cycles = len(results)
        successful_cycles = len([r for r in results if r.get("status") == "completed"])
        total_time = sum(r.get("execution_time", 0) for r in results)

        print(f"🔄 実行サイクル: {total_cycles}回")
        print(f"✅ 成功サイクル: {successful_cycles}回")
        print(f"⏱️ 総実行時間: {total_time:.1f}秒")
        print(f"📈 成功率: {successful_cycles/total_cycles*100:.1f}%" if total_cycles > 0 else "成功率: N/A")

        # 進捗レポート表示
        progress_report = self.task_manager.generate_progress_report()
        print(f"\n📋 タスク進捗:")
        print(f"  完了: {progress_report['task_summary']['completed']}件")
        print(f"  残り: {progress_report['task_summary']['pending']}件")
        print(f"  エラー修正: {progress_report['quality_metrics']['total_errors_fixed']}件")

    def _estimate_task_tokens(self, task_description: str, target_files: List[str]) -> int:
        """タスクのToken数を動的推定"""

        if self.token_measurement:
            # TokenMeasurementSystemを使用した推定
            try:
                # 簡易推定（実際のAPI呼び出しは後で測定）
                base_tokens = 500
                description_tokens = len(task_description.split()) * 2
                file_tokens = len(target_files) * 200

                estimated_total = base_tokens + description_tokens + file_tokens
                return max(estimated_total, 600)  # 最小600トークン

            except Exception as e:
                print(f"⚠️ Token推定エラー: {e}")

        # フォールバック: 従来の推定
        return max(len(task_description) * 3 + len(target_files) * 300, 800)

    def _measure_actual_token_usage(self, result: Dict[str, Any], task_id: str, model: str) -> Dict[str, Any]:
        """実際のToken使用量を測定"""

        if self.token_measurement:
            try:
                # API応答からToken情報を取得（もしあれば）
                api_response = result.get("api_response", {})

                if api_response:
                    # 実測定
                    usage = self.token_measurement.measure_actual_tokens(api_response, model)

                    # コスト追跡更新
                    self.token_measurement.update_cost_tracking(task_id, usage)

                    return {
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "total_tokens": usage.total_tokens,
                        "cost": usage.cost,
                        "model": usage.model,
                        "measurement_method": "api_response"
                    }
                else:
                    # 結果から推定測定
                    modifications = result.get("modifications", {})
                    files_count = len(modifications.get("files_modified", [])) + len(modifications.get("files_created", []))

                    estimated_input = max(600, files_count * 150)
                    estimated_output = max(400, files_count * 100)
                    cost = self.token_measurement.calculate_real_cost(estimated_input, estimated_output, model)

                    return {
                        "input_tokens": estimated_input,
                        "output_tokens": estimated_output,
                        "total_tokens": estimated_input + estimated_output,
                        "cost": cost,
                        "model": model,
                        "measurement_method": "result_estimation"
                    }

            except Exception as e:
                print(f"⚠️ Token測定エラー: {e}")

        # フォールバック: 基本推定
        return {
            "input_tokens": 800,
            "output_tokens": 500,
            "total_tokens": 1300,
            "cost": 0.00225,
            "model": model,
            "measurement_method": "fallback"
        }
        print(f"  総コスト: ${progress_report['cost_metrics']['total_cost']:.4f}")

        print("\n🎉 Dual-Agent Workflow セッション完了!")

    def run_quality_check(self, target_files: List[str] = None, ai_agent: str = "claude") -> Dict[str, Any]:
        """品質チェック実行"""
        # target_filesが指定されていない場合のデフォルト処理
        if target_files is None:
            target_files = []
            print("⚠️ 品質チェック: 対象ファイルが指定されていません。空のリストを使用します。")

        print(f"🔍 品質チェック開始: {len(target_files)}ファイル対象")

        # 包括的品質チェック実行
        metrics = self.quality_manager.run_comprehensive_check(target_files, ai_agent)

        # 品質基準チェック
        quality_passed = self._check_quality_standards(metrics)

        result = {
            "quality_metrics": metrics,
            "quality_passed": quality_passed,
            "recommendations": metrics.improvement_suggestions,
            "quality_level": metrics.quality_level.value
        }

        # 品質基準を満たさない場合の警告
        if not quality_passed:
            print(f"⚠️ 品質基準未達成: スコア {metrics.overall_score:.3f}")
            print("📝 改善提案:")
            for suggestion in metrics.improvement_suggestions:
                print(f"  - {suggestion}")
        else:
            print(f"✅ 品質基準達成: スコア {metrics.overall_score:.3f}")

        return result

    def _check_quality_standards(self, metrics: 'QualityMetrics') -> bool:
        """品質基準チェック（型安全性強化版）"""

        try:
            # 入力検証
            if not hasattr(metrics, 'overall_score') or not hasattr(metrics, 'error_count'):
                print("⚠️ 無効な品質メトリクスオブジェクト")
                return False

            # 最低品質基準 (standards.jsonから取得)
            minimum_score = 0.7
            maximum_errors = 10
            minimum_type_score = 0.8
            minimum_security_score = 0.9

            standards_met = True
            failed_criteria = []

            # 総合スコアチェック
            if metrics.overall_score < minimum_score:
                standards_met = False
                failed_criteria.append(f"総合スコア不足: {metrics.overall_score:.3f} < {minimum_score}")

            # エラー数チェック
            if metrics.error_count > maximum_errors:
                standards_met = False
                failed_criteria.append(f"エラー数超過: {metrics.error_count} > {maximum_errors}")

            # 重要な品質指標の個別チェック
            if hasattr(metrics, 'type_score') and metrics.type_score < minimum_type_score:
                standards_met = False
                failed_criteria.append(f"型チェック不足: {metrics.type_score:.3f} < {minimum_type_score}")

            if hasattr(metrics, 'security_score') and metrics.security_score < minimum_security_score:
                standards_met = False
                failed_criteria.append(f"セキュリティスコア不足: {metrics.security_score:.3f} < {minimum_security_score}")

            # 失敗基準のログ出力
            if failed_criteria:
                print(f"⚠️ 品質基準未達成: {len(failed_criteria)}件")
                for criteria in failed_criteria[:3]:  # 最初の3件のみ表示
                    print(f"  - {criteria}")
            else:
                print("✅ 全ての品質基準を満たしています")

            return standards_met

        except Exception as e:
            print(f"❌ 品質基準チェックエラー: {e}")
            return False

    def generate_quality_report(self, format_type: str = "html") -> str:
        """品質レポート生成"""
        print(f"📊 品質レポート生成中 (形式: {format_type})")

        report_path = self.quality_reporter.generate_comprehensive_report(format_type)

        print(f"✅ 品質レポート生成完了: {report_path}")
        return report_path

    def start_quality_monitoring(self) -> None:
        """品質監視開始（型安全性強化版）"""

        try:
            print("📊 品質監視システム開始")

            if not hasattr(self, 'quality_monitor') or self.quality_monitor is None:
                print("⚠️ 品質監視システムが初期化されていません")
                return

            self.quality_monitor.start_monitoring()

            # アラート通知設定（型安全性強化）
            def alert_handler(alert: Any) -> None:
                """Quality alert handler with enhanced error handling"""
                try:
                    if hasattr(alert, 'message'):
                        print(f"🚨 品質アラート: {alert.message}")
                    elif isinstance(alert, str):
                        print(f"🚨 品質アラート: {alert}")
                    else:
                        print(f"🚨 品質アラート: {str(alert)}")
                except Exception as handler_error:
                    print(f"❌ アラートハンドラーエラー: {handler_error}")

            self.quality_monitor.subscribe_to_alerts(alert_handler)
            print("✅ 品質監視システムとアラートハンドラーの設定が完了しました")

        except Exception as e:
            print(f"❌ 品質監視開始エラー: {e}")
            print("🔄 手動品質チェックモードで継続します")

    def get_quality_status(self) -> Dict[str, Any]:
        """現在の品質ステータス取得（エラーハンドリング強化版）"""

        try:
            status_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "monitor_status": None,
                "quality_report_data": None,
                "error_status": "none"
            }

            # 品質監視システムのステータス
            try:
                if hasattr(self, 'quality_monitor') and self.quality_monitor is not None:
                    status_data["monitor_status"] = self.quality_monitor.get_current_status()
                else:
                    status_data["monitor_status"] = {"error": "品質監視システムが利用できません"}
                    status_data["error_status"] = "monitor_unavailable"
            except Exception as monitor_error:
                print(f"⚠️ 品質監視システムステータス取得エラー: {monitor_error}")
                status_data["monitor_status"] = {"error": str(monitor_error)}
                status_data["error_status"] = "monitor_error"

            # 品質レポートデータ
            try:
                if hasattr(self, 'quality_manager') and self.quality_manager is not None:
                    status_data["quality_report_data"] = self.quality_manager.get_quality_report()
                else:
                    status_data["quality_report_data"] = {"error": "品質マネージャーが利用できません"}
                    status_data["error_status"] = "manager_unavailable" if status_data["error_status"] == "none" else "multiple_errors"
            except Exception as manager_error:
                print(f"⚠️ 品質マネージャーレポート取得エラー: {manager_error}")
                status_data["quality_report_data"] = {"error": str(manager_error)}
                status_data["error_status"] = "manager_error" if status_data["error_status"] == "none" else "multiple_errors"

            return status_data

        except Exception as e:
            print(f"❌ 品質ステータス取得エラー: {e}")
            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e),
                "error_status": "critical_failure"
            }

        return {
            "monitoring_status": monitor_status,
            "quality_report": quality_report_data,
            "session_id": self.session_id
        }

    def run_quality_gate_check(self, target_files: List[str], gate_type: str = "pre_commit") -> bool:
        """品質ゲートチェック実行"""
        print(f"🚪 品質ゲートチェック: {gate_type}")

        # 品質チェック実行
        quality_result = self.run_quality_check(target_files, "claude")
        metrics = quality_result["quality_metrics"]

        # ゲート種別による基準設定
        gate_standards = {
            "pre_commit": {"minimum_score": 0.8, "required_checks": ["syntax", "type_check", "lint", "format"]},
            "pre_push": {"minimum_score": 0.85, "required_checks": ["syntax", "type_check", "lint", "format", "security", "test"]},
            "production": {"minimum_score": 0.9, "required_checks": ["syntax", "type_check", "lint", "format", "security", "performance", "test"]}
        }

        standard = gate_standards.get(gate_type, gate_standards["pre_commit"])

        # 基準チェック
        gate_passed = metrics.overall_score >= standard["minimum_score"]

        if gate_passed:
            print(f"✅ 品質ゲート通過: {gate_type} (スコア: {metrics.overall_score:.3f})")
        else:
            print(f"❌ 品質ゲート失敗: {gate_type} (スコア: {metrics.overall_score:.3f})")
            print(f"   必要スコア: {standard['minimum_score']:.3f}")

        return gate_passed

    def run_integrated_workflow_with_quality(self, target_files: List[str],
                                           error_type: str = "no-untyped-def") -> Dict[str, Any]:
        """品質管理統合ワークフロー実行"""
        print("🔄 品質管理統合ワークフロー開始")

        # 1. 事前品質チェック
        print("\n📋 Step 1: 事前品質チェック")
        pre_quality = self.run_quality_check(target_files, "claude")

        # 2. 品質ゲートチェック
        print("\n📋 Step 2: 品質ゲートチェック")
        if not self.run_quality_gate_check(target_files, "pre_commit"):
            return {
                "status": "quality_gate_failed",
                "pre_quality": pre_quality,
                "message": "事前品質ゲートを通過しませんでした"
            }

        # 3. タスク作成・実行
        print("\n📋 Step 3: 修正タスク実行")
        task_ids = self.create_mypy_fix_task(
            target_files=target_files,
            error_type=error_type,
            auto_execute=True
        )

        # 4. 修正後品質チェック
        print("\n📋 Step 4: 修正後品質チェック")
        post_quality = self.run_quality_check(target_files, "claude")

        # 5. 品質改善確認
        print("\n📋 Step 5: 品質改善確認")
        improvement = post_quality["quality_metrics"].overall_score - pre_quality["quality_metrics"].overall_score

        if improvement > 0:
            print(f"✅ 品質改善: +{improvement:.3f}")
        else:
            print(f"⚠️ 品質改善なし: {improvement:.3f}")

        # 6. 最終品質ゲートチェック
        print("\n📋 Step 6: 最終品質ゲートチェック")
        final_gate_passed = self.run_quality_gate_check(target_files, "pre_push")

        return {
            "status": "completed" if final_gate_passed else "quality_gate_failed",
            "pre_quality": pre_quality,
            "post_quality": post_quality,
            "improvement": improvement,
            "task_ids": task_ids,
            "final_gate_passed": final_gate_passed
        }

    def _create_fallback_implementation_task(self,
                                           file_path: str,
                                           task_type: str,
                                           implementation_spec: Dict[str, Any],
                                           priority: str) -> str:
        """フォールバック用簡易実装タスク作成（型安全性強化版）"""

        try:
            # 入力値検証
            if not file_path or not isinstance(file_path, str):
                raise ValueError("有効なファイルパスが必要です")

            if not task_type or not isinstance(task_type, str):
                raise ValueError("有効なタスクタイプが必要です")

            if not isinstance(implementation_spec, dict):
                print("⚠️ 実装仕様が辞書型ではありません。デフォルト仕様を使用します")
                implementation_spec = {"template_type": "generic", "complexity": "simple"}

            if priority not in ["low", "medium", "high"]:
                print(f"⚠️ 無効な優先度'{priority}'。'medium'を使用します")
                priority = "medium"

            print(f"🔄 フォールバックタスク作成: {file_path}")
            print(f"   タスクタイプ: {task_type}")
            print(f"   優先度: {priority}")
            print(f"   実装仕様: {implementation_spec.get('template_type', 'unknown')}")

            # タスクマネージャーの存在確認
            if not hasattr(self, 'task_manager') or self.task_manager is None:
                raise RuntimeError("タスクマネージャーが初期化されていません")

            # 最小限の要件でタスク作成
            fallback_task_id = self.task_manager.create_task(
                task_type=f"fallback_{task_type}",
                description=f"フォールバック {task_type} - {file_path}",
                target_files=[file_path],
                priority=priority,
                requirements={
                    "implementation_spec": implementation_spec,
                    "task_type": task_type,
                    "fallback_mode": True,
                    "quality_requirements": {
                        "syntax_check": True,
                        "basic_implementation": True,
                        "error_tolerance": "high",  # フォールバック時は寛容
                        "minimum_functionality": True
                    }
                },
                claude_analysis=self._generate_fallback_analysis(file_path, task_type, implementation_spec),
                expected_outcome=f"基本的な{task_type}完了 - {file_path}",
                constraints=[
                    "最小限の実装要件",
                    "エラー時の安全な処理",
                    "基本品質基準遵守",
                    "フォールバック品質基準適用"
                ],
                context={
                    "fallback_task": True,
                    "original_error": "通常タスク作成失敗",
                    "session_id": getattr(self, 'session_id', 'unknown'),
                    "fallback_timestamp": datetime.datetime.now().isoformat(),
                    "reduced_quality_expectations": True
                }
            )

            print(f"✅ フォールバックタスク作成成功: {fallback_task_id}")
            return fallback_task_id

        except ValueError as ve:
            print(f"❌ フォールバックタスク作成失敗（入力値エラー）: {ve}")
            return self._generate_emergency_fallback_task_id("input_validation_error")

        except RuntimeError as re:
            print(f"❌ フォールバックタスク作成失敗（システムエラー）: {re}")
            return self._generate_emergency_fallback_task_id("system_error")

        except Exception as e:
            print(f"❌ フォールバックタスク作成失敗（予期しないエラー）: {e}")
            return self._generate_emergency_fallback_task_id("unexpected_error")

    def _generate_fallback_analysis(self, file_path: str, task_type: str, implementation_spec: Dict[str, Any]) -> str:
        """フォールバック用Claude分析生成"""

        return f"""
🔄 フォールバックタスク分析 - {task_type}

📄 対象情報:
- ファイル: {file_path}
- タスクタイプ: {task_type}
- 実装仕様: {implementation_spec.get('template_type', 'generic')}

🎯 フォールバック方針:
- 最小限の機能実装に焦点
- エラー耐性を重視した設計
- 基本的な品質基準を満たす実装
- 段階的な改善が可能な構造

⚠️ 注意事項:
- 通常タスク作成が失敗したため簡易版を実行
- 品質基準は通常より緩和されています
- 実装完了後に手動レビューを推奨
"""

    def _generate_emergency_fallback_task_id(self, error_type: str) -> str:
        """緊急フォールバックタスクID生成"""

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        task_id = f"emergency_fallback_{error_type}_{timestamp}"

        print(f"🆘 緊急フォールバックタスクID生成: {task_id}")
        print("   ⚠️ このタスクは手動処理が必要です")

        return task_id

    def run_three_layer_verification(self, target_files: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """3層検証体制実行（新規実装タスク向け）"""

        print("🔒 3層検証体制開始...")
        print(f"📁 対象ファイル: {len(target_files)}件")

        context = context or {}
        verification_start_time = datetime.datetime.now()

        # Layer 1: 構文検証
        print("\n" + "="*50)
        layer1_result = self.quality_manager.validate_syntax(target_files)

        # Layer 2: 品質検証
        print("\n" + "="*50)
        layer2_result = self.quality_manager.check_code_quality(target_files, layer1_result)

        # Layer 3: Claude最終承認
        print("\n" + "="*50)
        layer3_result = self.quality_manager.claude_final_approval(
            target_files, layer1_result, layer2_result, context
        )

        verification_end_time = datetime.datetime.now()
        verification_duration = str(verification_end_time - verification_start_time)

        # 統合結果作成
        overall_result = {
            "verification_type": "three_layer_verification",
            "execution_summary": {
                "start_time": verification_start_time.isoformat(),
                "end_time": verification_end_time.isoformat(),
                "duration": verification_duration,
                "target_files_count": len(target_files)
            },
            "layer_results": {
                "layer1_syntax": layer1_result,
                "layer2_quality": layer2_result,
                "layer3_approval": layer3_result
            },
            "overall_status": {
                "layer1_passed": layer1_result.get("passed", False),
                "layer2_passed": layer2_result.get("passed", False),
                "layer3_approved": layer3_result.get("approved", False),
                "all_layers_passed": (
                    layer1_result.get("passed", False) and
                    layer2_result.get("passed", False) and
                    layer3_result.get("approved", False)
                )
            },
            "quality_metrics": {
                "syntax_score": layer1_result.get("syntax_check", {}).get("score", 0),
                "type_score": layer1_result.get("type_check", {}).get("score", 0),
                "overall_quality_score": layer2_result.get("overall_quality_score", 0),
                "final_score": layer3_result.get("final_metrics", {}).get("overall_score", 0)
            },
            "context": context,
            "recommendations": self._generate_verification_recommendations(
                layer1_result, layer2_result, layer3_result
            ),
            "timestamp": verification_end_time.isoformat()
        }

        # 結果サマリー表示
        print("\n" + "="*50)
        print("🎯 3層検証体制結果サマリー")
        print("="*50)
        print(f"Layer 1 (構文): {'✅ PASS' if layer1_result.get('passed') else '❌ FAIL'}")
        print(f"Layer 2 (品質): {'✅ PASS' if layer2_result.get('passed') else '❌ FAIL'}")
        print(f"Layer 3 (承認): {'✅ APPROVED' if layer3_result.get('approved') else '❌ REJECTED'}")
        print(f"総合結果: {'🎉 完全通過' if overall_result['overall_status']['all_layers_passed'] else '⚠️ 要改善'}")
        print(f"実行時間: {verification_duration}")

        return overall_result

    def _generate_verification_recommendations(self, layer1_result: Dict, layer2_result: Dict, layer3_result: Dict) -> List[str]:
        """3層検証結果に基づく推奨事項生成"""

        recommendations = []

        # Layer 1の推奨事項
        if not layer1_result.get("passed", False):
            syntax_errors = layer1_result.get("syntax_check", {}).get("errors", 0)
            type_errors = layer1_result.get("type_check", {}).get("errors", 0)

            if syntax_errors > 0:
                recommendations.append(f"🔧 構文エラー{syntax_errors}件の修正が必要")
            if type_errors > 0:
                recommendations.append(f"🏷️ 型注釈エラー{type_errors}件の修正が必要")

        # Layer 2の推奨事項
        if not layer2_result.get("passed", False) and not layer2_result.get("skipped", False):
            quality_score = layer2_result.get("overall_quality_score", 0)
            recommendations.append(f"📊 品質スコア改善が必要 (現在: {quality_score:.2f}, 必要: 0.75以上)")

            # 個別品質チェックの推奨事項
            quality_checks = layer2_result.get("quality_checks", {})
            for check_name, check_result in quality_checks.items():
                if not check_result.get("passed", True):
                    recommendations.append(f"🔍 {check_name}品質の改善が必要")

        # Layer 3の推奨事項
        if not layer3_result.get("approved", False) and not layer3_result.get("skipped", False):
            final_score = layer3_result.get("final_metrics", {}).get("overall_score", 0)
            recommendations.append(f"👨‍💻 Claude最終承認基準未達 (現在: {final_score:.2f}, 必要: 0.80以上)")

            # 最終メトリクスの推奨事項
            final_recommendations = layer3_result.get("recommendations", [])
            recommendations.extend(final_recommendations)

        # 成功時の推奨事項
        if (layer1_result.get("passed") and layer2_result.get("passed") and layer3_result.get("approved")):
            recommendations.extend([
                "🎉 3層検証完全通過！品質基準を満たしています",
                "📈 継続的な品質監視を推奨します",
                "🔄 定期的なリファクタリングを検討してください"
            ])

        return recommendations

    # Issue #870: 高度開発システム統合メソッド

    def execute_complex_task_pattern(
        self,
        target_files: List[str],
        task_description: str,
        coordination_strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """複雑タスクパターン実行 - Issue #870対応"""

        print(f"🎯 複雑タスクパターン実行開始: {len(target_files)}ファイル")
        print(f"📋 タスク概要: {task_description}")
        print(f"🎛️ 協調戦略: {coordination_strategy}")

        # 1. 依存関係解析
        dependency_graph = self.dependency_analyzer.analyze_project_dependencies(target_files)
        print(f"🔍 依存関係解析完了: {len(dependency_graph.nodes)}ノード, {len(dependency_graph.edges)}エッジ")

        # 2. マルチファイル実装計画作成
        from advanced.multi_file_coordinator import CoordinationStrategy
        strategy_map = {
            "sequential": CoordinationStrategy.SEQUENTIAL,
            "parallel": CoordinationStrategy.PARALLEL,
            "hybrid": CoordinationStrategy.HYBRID,
            "dependency_driven": CoordinationStrategy.DEPENDENCY_DRIVEN
        }

        implementation_plan = self.multi_file_coordinator.create_implementation_plan(
            target_files=target_files,
            strategy=strategy_map.get(coordination_strategy, CoordinationStrategy.HYBRID)
        )
        print(f"📋 実装計画作成完了: {len(implementation_plan.implementation_phases)}フェーズ")

        # 3. 性能解析・最適化機会検出
        performance_issues = self.performance_optimizer.analyze_project_performance(target_files)
        total_issues = sum(len(issues) for issues in performance_issues.values())
        print(f"⚡ 性能解析完了: {total_issues}件の最適化機会")

        # 4. リファクタリング機会検出
        refactoring_analysis = self.refactoring_engine.analyze_project(target_files)
        total_refactoring_opportunities = sum(
            len(opportunities) for _, opportunities in refactoring_analysis.values()
        )
        print(f"🔧 リファクタリング解析完了: {total_refactoring_opportunities}件の改善機会")

        # 5. 実行結果統合
        execution_result = {
            "status": "completed",
            "target_files": target_files,
            "coordination_strategy": coordination_strategy,
            "dependency_analysis": {
                "nodes": len(dependency_graph.nodes),
                "edges": len(dependency_graph.edges),
                "cycles": len(dependency_graph.cycles),
                "implementation_levels": max(dependency_graph.levels.values()) if dependency_graph.levels else 0
            },
            "implementation_plan": {
                "phases": len(implementation_plan.implementation_phases),
                "parallel_groups": len(implementation_plan.parallel_groups),
                "estimated_duration": implementation_plan.estimated_duration
            },
            "performance_analysis": {
                "total_issues": total_issues,
                "critical_issues": sum(
                    len([issue for issue in issues if issue.severity == "critical"])
                    for issues in performance_issues.values()
                )
            },
            "refactoring_analysis": {
                "total_opportunities": total_refactoring_opportunities,
                "high_priority": sum(
                    len([op for _, ops in analysis.values() for op in ops if op.priority.value == "high"])
                    for analysis in [refactoring_analysis]
                )
            }
        }

        print(f"✅ 複雑タスクパターン実行完了")
        return execution_result

    def apply_design_pattern(
        self,
        pattern_name: str,
        target_classes: List[str],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """設計パターン自動実装 - Issue #870対応"""

        print(f"🎨 設計パターン実装開始: {pattern_name}")
        print(f"🎯 対象クラス: {target_classes}")

        try:
            from advanced.pattern_implementation_engine import DesignPattern, PatternCategory, PatternRequirement

            # パターン名からEnumに変換
            pattern_map = {
                "factory": DesignPattern.FACTORY,
                "observer": DesignPattern.OBSERVER,
                "strategy": DesignPattern.STRATEGY,
                "singleton": DesignPattern.SINGLETON,
                "decorator": DesignPattern.DECORATOR
            }

            pattern = pattern_map.get(pattern_name.lower())
            if not pattern:
                return {"status": "error", "message": f"サポートされていないパターン: {pattern_name}"}

            # パターン要件定義
            requirements = PatternRequirement(
                pattern=pattern,
                category=PatternCategory.CREATIONAL if pattern in [DesignPattern.FACTORY, DesignPattern.SINGLETON] else PatternCategory.BEHAVIORAL,
                target_classes=target_classes,
                interfaces=[target_classes[0]] if target_classes else [],
                methods=["execute", "operation"],
                properties=[],
                solid_principles=["SRP", "OCP", "DIP"],
                complexity_level=3,
                estimated_effort=4
            )

            # パターン実装
            implementation = self.pattern_engine.implement_pattern(pattern, requirements, output_path)

            # 実装ファイル保存
            self.pattern_engine.save_implementation(implementation)

            result = {
                "status": "success",
                "pattern": pattern_name,
                "file_path": implementation.file_path,
                "quality_score": implementation.quality_score,
                "solid_compliance": implementation.solid_compliance,
                "classes_generated": len(implementation.classes),
                "methods_generated": len(implementation.methods)
            }

            print(f"✅ パターン実装完了: {implementation.file_path}")
            print(f"⭐ 品質スコア: {implementation.quality_score:.2f}")

            return result

        except Exception as e:
            error_result = {"status": "error", "message": str(e)}
            print(f"❌ パターン実装エラー: {e}")
            return error_result

    def analyze_and_optimize_performance(
        self,
        target_files: List[str],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """性能解析・最適化実行 - Issue #870対応"""

        print(f"⚡ 性能解析・最適化開始: {len(target_files)}ファイル")

        # 性能解析実行
        analysis_results = self.performance_optimizer.analyze_project_performance(target_files)

        optimization_results = []

        for file_path, issues in analysis_results.items():
            if issues:
                print(f"📄 最適化対象: {os.path.relpath(file_path)}")

                # 高優先度問題を自動最適化
                high_priority_issues = [
                    issue for issue in issues
                    if issue.severity in ["critical", "high"]
                ]

                if high_priority_issues or auto_apply:
                    optimization_result = self.performance_optimizer.apply_optimizations(
                        file_path, issues, auto_apply
                    )
                    optimization_results.append(optimization_result)

                    print(f"  ✅ 最適化完了: {optimization_result.improvement_percentage:.1%}改善")

        # 性能レポート生成
        report = self.performance_optimizer.generate_performance_report(analysis_results)
        report_path = f"tmp/performance_report_{int(time.time())}.md"
        os.makedirs("tmp", exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        total_issues = sum(len(issues) for issues in analysis_results.values())
        total_optimizations = len(optimization_results)

        result = {
            "status": "completed",
            "analyzed_files": len(target_files),
            "total_issues": total_issues,
            "applied_optimizations": total_optimizations,
            "report_path": report_path,
            "optimization_summary": [
                {
                    "file": getattr(result, 'original_file', 'unknown'),
                    "improvement": getattr(result, 'improvement_percentage', 0.0),
                    "time_reduction": getattr(result, 'execution_time_reduction', 0.0),
                    "memory_reduction": getattr(result, 'memory_reduction', 0.0)
                }
                for result in optimization_results
            ]
        }

        print(f"✅ 性能解析・最適化完了")
        print(f"📊 解析ファイル: {len(target_files)}")
        print(f"🔍 検出問題: {total_issues}件")
        print(f"⚡ 適用最適化: {total_optimizations}件")
        print(f"📄 レポート: {report_path}")

        return result

    def execute_comprehensive_code_improvement(
        self,
        target_files: List[str],
        include_patterns: bool = True,
        include_refactoring: bool = True,
        include_performance: bool = True
    ) -> Dict[str, Any]:
        """包括的コード改善実行 - Issue #870統合機能"""

        print(f"🚀 包括的コード改善開始: {len(target_files)}ファイル")
        print(f"🎨 パターン適用: {'有効' if include_patterns else '無効'}")
        print(f"🔧 リファクタリング: {'有効' if include_refactoring else '無効'}")
        print(f"⚡ 性能最適化: {'有効' if include_performance else '無効'}")

        improvement_results = {
            "status": "completed",
            "target_files": target_files,
            "improvements_applied": [],
            "reports_generated": [],
            "quality_metrics": {}
        }

        # 1. 依存関係解析（必須）
        dependency_analysis = self.dependency_analyzer.analyze_project_dependencies(target_files)
        improvement_results["dependency_analysis"] = {
            "files_analyzed": len(dependency_analysis.nodes),
            "dependencies_found": len(dependency_analysis.edges),
            "circular_dependencies": len(dependency_analysis.cycles)
        }
        print(f"🔍 依存関係解析完了: {len(dependency_analysis.cycles)}件の循環依存")

        # 2. リファクタリング解析・適用
        if include_refactoring:
            refactoring_analysis = self.refactoring_engine.analyze_project(target_files)

            for file_path, (metrics, opportunities) in refactoring_analysis.items():
                high_confidence_ops = [
                    op for op in opportunities
                    if op.confidence_score > 0.8
                ]

                if high_confidence_ops:
                    refactoring_result = self.refactoring_engine.apply_refactorings(
                        file_path, high_confidence_ops, auto_apply=True
                    )
                    improvement_results["improvements_applied"].append({
                        "type": "refactoring",
                        "file": file_path,
                        "applied_count": len(refactoring_result.applied_refactorings),
                        "quality_improvement": refactoring_result.quality_improvement
                    })

            # リファクタリングレポート生成
            refactoring_report = self.refactoring_engine.generate_refactoring_report(refactoring_analysis)
            refactoring_report_path = f"tmp/refactoring_report_{int(time.time())}.md"
            with open(refactoring_report_path, 'w', encoding='utf-8') as f:
                f.write(refactoring_report)
            improvement_results["reports_generated"].append(refactoring_report_path)

            print(f"🔧 リファクタリング完了: レポート生成 {refactoring_report_path}")

        # 3. 性能最適化
        if include_performance:
            performance_result = self.analyze_and_optimize_performance(target_files, auto_apply=True)
            improvement_results["improvements_applied"].append({
                "type": "performance",
                "total_issues": performance_result["total_issues"],
                "optimizations": performance_result["applied_optimizations"]
            })
            improvement_results["reports_generated"].append(performance_result["report_path"])

            print(f"⚡ 性能最適化完了: {performance_result['applied_optimizations']}件適用")

        # 4. 設計パターン適用提案
        if include_patterns:
            pattern_opportunities = self.pattern_engine.analyze_code_for_patterns(target_files[0]) if target_files else []

            improvement_results["pattern_opportunities"] = len(pattern_opportunities)
            if pattern_opportunities:
                print(f"🎨 設計パターン機会: {len(pattern_opportunities)}件検出")

        # 5. 品質メトリクス計算
        improvement_results["quality_metrics"] = {
            "total_improvements": len(improvement_results["improvements_applied"]),
            "reports_generated": len(improvement_results["reports_generated"]),
            "dependency_health": "good" if len(dependency_analysis.cycles) == 0 else "needs_attention"
        }

        print(f"✅ 包括的コード改善完了")
        print(f"📊 総改善項目: {improvement_results['quality_metrics']['total_improvements']}")
        print(f"📄 生成レポート: {improvement_results['quality_metrics']['reports_generated']}件")

        return improvement_results

def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Dual-Agent Workflow Coordinator")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                       help="実行モード (single: 1サイクル, continuous: 連続実行)")
    parser.add_argument("--max-cycles", type=int, default=10,
                       help="連続実行時の最大サイクル数")
    parser.add_argument("--create-test-task", action="store_true",
                       help="テスト用タスクを作成")

    args = parser.parse_args()

    coordinator = DualAgentCoordinator()

    if args.create_test_task:
        # テスト用タスク作成
        test_files = ["kumihan_formatter/core/utilities/logger.py"]  # 例
        task_id = coordinator.create_mypy_fix_task(
            target_files=test_files,
            error_type="no-untyped-def",
            priority="high"
        )
        print(f"✅ テストタスク作成: {task_id}")
        return

    if args.mode == "single":
        # 単一サイクル実行
        result = coordinator.execute_workflow_cycle()
        print(f"\n📊 実行結果: {result['status']}")

    elif args.mode == "continuous":
        # 連続実行
        results = coordinator.run_continuous_workflow(max_cycles=args.max_cycles)
        print(f"\n📊 連続実行完了: {len(results)}サイクル")

if __name__ == "__main__":
    main()
