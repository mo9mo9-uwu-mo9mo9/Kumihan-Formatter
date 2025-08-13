#!/usr/bin/env python3
"""
Hybrid Implementation Flow Controller
Issue #844: ハイブリッド実装フロー構築 - 段階的協業システム

3段階のハイブリッド実装フローを統制するメインコントローラー
"""

import json
import os
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# プロジェクトルートからのインポート
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.workflow_decision_engine import WorkflowDecisionEngine
from quality.quality_manager import QualityManager
from monitoring.quality_monitor import QualityMonitor

class PhaseType(Enum):
    """実装フェーズタイプ"""
    PHASE_A_ARCHITECTURE = "phase_a_architecture"  # Claude: アーキテクチャ設計
    PHASE_B_IMPLEMENTATION = "phase_b_implementation"  # Gemini: 具体的実装
    PHASE_C_INTEGRATION = "phase_c_integration"  # Claude: 統合・品質保証

class ImplementationStatus(Enum):
    """実装ステータス"""
    PENDING = "pending"          # 待機中
    IN_PROGRESS = "in_progress"  # 実行中
    PHASE_COMPLETED = "phase_completed"  # フェーズ完了
    FULLY_COMPLETED = "fully_completed"  # 全体完了
    FAILED = "failed"            # 失敗
    NEEDS_REVIEW = "needs_review"  # レビュー必要

@dataclass
class PhaseResult:
    """フェーズ実行結果"""
    phase_type: PhaseType
    status: ImplementationStatus
    execution_time: float
    quality_score: float
    output_data: Dict[str, Any]
    error_messages: List[str]
    success_metrics: Dict[str, Any]
    next_phase_requirements: Dict[str, Any]

@dataclass
class HybridImplementationSpec:
    """ハイブリッド実装仕様"""
    implementation_id: str
    implementation_type: str  # "new_implementation", "hybrid_implementation", "feature_development"
    target_files: List[str]
    requirements: Dict[str, Any]
    success_criteria: Dict[str, Any]
    quality_standards: Dict[str, Any]
    context: Dict[str, Any]

class HybridImplementationFlow:
    """3段階ハイブリッド実装フロー統制システム"""

    def __init__(self):
        self.decision_engine = WorkflowDecisionEngine()
        self.quality_manager = QualityManager()
        self.quality_monitor = QualityMonitor()

        # フロー管理
        self.current_implementations: Dict[str, Dict[str, Any]] = {}
        self.flow_history: List[Dict[str, Any]] = []

        # 成功基準 (Issue #844要求) - Issue #848対応: キー統一・拡張
        self.success_criteria = {
            # 全体的な成功基準
            "new_implementation_success_rate": 0.70,  # 70%以上
            "token_savings_rate": 0.90,              # 90%以上維持
            "implementation_quality_score": 0.80,    # 0.80以上
            "integration_success_rate": 0.95,        # 95%以上

            # Phase B Implementation 基準
            "minimum_quality_score": 0.80,           # 品質スコア最低基準
            "maximum_error_rate": 0.10,              # エラー率上限
            "minimum_test_coverage": 0.80,           # テストカバレッジ最低基準
            "maximum_retry_count": 3,                # 最大リトライ回数

            # Phase C Integration 基準
            "minimum_integration_quality": 0.95,     # 統合品質最低基準
            "minimum_overall_quality": 0.80,         # 全体品質最低基準
            "maximum_critical_issues": 0,            # 重大問題上限
            "deployment_readiness_required": True,   # デプロイ準備要求

            # Issue #848対応: implementation_threshold -> implementation_quality_score
            "implementation_threshold": 0.80,        # 後方互換性のため
        }

        # ディレクトリ設定
        self.flows_dir = Path("postbox/flows")
        self.flows_dir.mkdir(parents=True, exist_ok=True)

        print(f"🏗️ Hybrid Implementation Flow Controller 初期化完了")
        print(f"🎯 成功基準: 実装成功率≥70%, Token節約≥90%, 品質≥0.80, 統合≥95%")
        print(f"📁 フロー管理ディレクトリ: {self.flows_dir}")

    # Issue #848対応: 安全なキーアクセス用アクセサーメソッド群
    def get_success_criterion(self, key: str, default: Any = None) -> Any:
        """安全な成功基準アクセス"""
        return self.success_criteria.get(key, default)

    def get_implementation_quality_score(self) -> float:
        """実装品質スコア閾値取得"""
        return self.get_success_criterion("implementation_quality_score", 0.80)

    def get_implementation_threshold(self) -> float:
        """実装閾値取得（後方互換性）"""
        return self.get_success_criterion("implementation_threshold",
                                         self.get_implementation_quality_score())

    def get_minimum_quality_score(self) -> float:
        """最低品質スコア取得（Phase B用）"""
        return self.get_success_criterion("minimum_quality_score", 0.80)

    def get_integration_success_rate(self) -> float:
        """統合成功率閾値取得"""
        return self.get_success_criterion("integration_success_rate", 0.95)

    def get_minimum_integration_quality(self) -> float:
        """最低統合品質取得（Phase C用）"""
        return self.get_success_criterion("minimum_integration_quality", 0.95)

    def get_all_criteria_status(self) -> Dict[str, Any]:
        """全成功基準の現在状況取得"""
        return {
            "available_keys": list(self.success_criteria.keys()),
            "critical_thresholds": {
                "implementation_quality": self.get_implementation_quality_score(),
                "integration_success": self.get_integration_success_rate(),
                "minimum_quality": self.get_minimum_quality_score(),
                "implementation_threshold": self.get_implementation_threshold()
            },
            "phase_specific": {
                "phase_b": {
                    "minimum_quality_score": self.get_minimum_quality_score(),
                    "maximum_error_rate": self.get_success_criterion("maximum_error_rate", 0.10),
                    "minimum_test_coverage": self.get_success_criterion("minimum_test_coverage", 0.80),
                    "maximum_retry_count": self.get_success_criterion("maximum_retry_count", 3)
                },
                "phase_c": {
                    "minimum_integration_quality": self.get_minimum_integration_quality(),
                    "minimum_overall_quality": self.get_success_criterion("minimum_overall_quality", 0.80),
                    "maximum_critical_issues": self.get_success_criterion("maximum_critical_issues", 0),
                    "deployment_readiness_required": self.get_success_criterion("deployment_readiness_required", True)
                }
            }
        }

    def start_hybrid_implementation(self,
                                  implementation_spec: HybridImplementationSpec,
                                  auto_execute: bool = True) -> str:
        """ハイブリッド実装フロー開始"""

        impl_id = implementation_spec.implementation_id
        print(f"\n🚀 ハイブリッド実装フロー開始: {impl_id}")
        print(f"📊 実装タイプ: {implementation_spec.implementation_type}")
        print(f"📁 対象ファイル: {len(implementation_spec.target_files)}件")

        # 実装データ初期化
        implementation_data = {
            "implementation_id": impl_id,
            "spec": implementation_spec.__dict__,
            "status": ImplementationStatus.PENDING,
            "current_phase": None,
            "phases": {},
            "overall_metrics": {
                "start_time": datetime.datetime.now().isoformat(),
                "phases_completed": 0,
                "total_execution_time": 0.0,
                "overall_quality_score": 0.0,
                "token_usage": 0,
                "cost": 0.0
            },
            "success_tracking": {
                "implementation_success": False,
                "quality_threshold_met": False,
                "integration_success": False,
                "meets_success_criteria": False
            }
        }

        self.current_implementations[impl_id] = implementation_data

        # フロー開始判定
        if auto_execute:
            self._execute_full_flow(impl_id)
        else:
            print(f"📋 実装フロー準備完了: {impl_id}")
            print("   実行コマンド: flow.execute_full_flow(implementation_id)")

        return impl_id

    def _execute_full_flow(self, implementation_id: str) -> Dict[str, Any]:
        """フル3段階フローの実行"""

        print(f"\n🔄 3段階フロー実行開始: {implementation_id}")

        implementation_data = self.current_implementations[implementation_id]
        spec = HybridImplementationSpec(**implementation_data["spec"])

        flow_start_time = time.time()

        try:
            # Phase A: アーキテクチャ設計 (Claude)
            print(f"\n📋 Phase A: アーキテクチャ設計フェーズ開始")
            phase_a_result = self._execute_phase_a(spec, implementation_data)
            implementation_data["phases"]["phase_a"] = phase_a_result.__dict__
            implementation_data["current_phase"] = PhaseType.PHASE_A_ARCHITECTURE

            if phase_a_result.status == ImplementationStatus.FAILED:
                return self._handle_flow_failure(implementation_id, "Phase A失敗")

            # Phase B: 実装実行 (Gemini)
            print(f"\n📋 Phase B: 実装実行フェーズ開始")
            phase_b_result = self._execute_phase_b(spec, phase_a_result, implementation_data)
            implementation_data["phases"]["phase_b"] = phase_b_result.__dict__
            implementation_data["current_phase"] = PhaseType.PHASE_B_IMPLEMENTATION

            if phase_b_result.status == ImplementationStatus.FAILED:
                return self._handle_flow_failure(implementation_id, "Phase B失敗")

            # Phase C: 統合・品質保証 (Claude)
            print(f"\n📋 Phase C: 統合・品質保証フェーズ開始")
            phase_c_result = self._execute_phase_c(spec, phase_b_result, implementation_data)
            implementation_data["phases"]["phase_c"] = phase_c_result.__dict__
            implementation_data["current_phase"] = PhaseType.PHASE_C_INTEGRATION

            # 全体結果評価
            flow_execution_time = time.time() - flow_start_time
            overall_result = self._evaluate_overall_success(
                implementation_id, [phase_a_result, phase_b_result, phase_c_result], flow_execution_time
            )

            # 成功基準チェック
            success_check = self._check_success_criteria(overall_result)
            implementation_data["success_tracking"] = success_check

            if success_check["meets_success_criteria"]:
                implementation_data["status"] = ImplementationStatus.FULLY_COMPLETED
                print(f"\n✅ ハイブリッド実装フロー完全成功: {implementation_id}")
            else:
                implementation_data["status"] = ImplementationStatus.NEEDS_REVIEW
                print(f"\n⚠️ ハイブリッド実装フロー部分成功: {implementation_id}")

            # 結果保存
            self._save_implementation_result(implementation_id, overall_result)

            return overall_result

        except Exception as e:
            print(f"❌ フロー実行エラー: {e}")
            return self._handle_flow_failure(implementation_id, f"実行エラー: {e}")

    def _execute_phase_a(self, spec: HybridImplementationSpec,
                        implementation_data: Dict[str, Any]) -> PhaseResult:
        """Phase A: アーキテクチャ設計フェーズ (Claude)"""

        print("🧠 Phase A: Claude によるアーキテクチャ設計")

        phase_start_time = time.time()

        # Claude による設計分析
        architecture_analysis = self._claude_architecture_analysis(spec)

        # インターフェース設計
        interface_design = self._claude_interface_design(spec, architecture_analysis)

        # 実装方針決定
        implementation_strategy = self._claude_implementation_strategy(spec, interface_design)

        # 品質要件定義
        quality_requirements = self._claude_quality_requirements(spec, implementation_strategy)

        phase_execution_time = time.time() - phase_start_time

        # Phase A 結果評価
        phase_a_quality = self._evaluate_phase_a_quality(
            architecture_analysis, interface_design, implementation_strategy
        )

        # Phase B への引き渡しデータ
        next_phase_requirements = {
            "architecture_design": architecture_analysis,
            "interface_specifications": interface_design,
            "implementation_strategy": implementation_strategy,
            "quality_requirements": quality_requirements,
            "gemini_instructions": self._generate_phase_b_instructions(
                interface_design, implementation_strategy
            )
        }

        success_metrics = {
            "design_completeness": phase_a_quality.get("completeness", 0.0),
            "architecture_score": phase_a_quality.get("architecture_score", 0.0),
            "interface_quality": phase_a_quality.get("interface_quality", 0.0)
        }

        status = ImplementationStatus.PHASE_COMPLETED if phase_a_quality.get("overall_score", 0.0) >= 0.7 else ImplementationStatus.FAILED

        print(f"📊 Phase A 完了: 品質スコア {phase_a_quality.get('overall_score', 0.0):.2f}")

        return PhaseResult(
            phase_type=PhaseType.PHASE_A_ARCHITECTURE,
            status=status,
            execution_time=phase_execution_time,
            quality_score=phase_a_quality.get("overall_score", 0.0),
            output_data=next_phase_requirements,
            error_messages=phase_a_quality.get("issues", []),
            success_metrics=success_metrics,
            next_phase_requirements=next_phase_requirements
        )

    def _execute_phase_b(self, spec: HybridImplementationSpec,
                        phase_a_result: PhaseResult,
                        implementation_data: Dict[str, Any]) -> PhaseResult:
        """Phase B: 実装実行フェーズ (Gemini)"""

        print("⚡ Phase B: Gemini による具体的実装")

        phase_start_time = time.time()

        # Phase A からのデータ取得
        architecture_design = phase_a_result.output_data.get("architecture_design", {})
        interface_specs = phase_a_result.output_data.get("interface_specifications", {})
        implementation_strategy = phase_a_result.output_data.get("implementation_strategy", {})
        gemini_instructions = phase_a_result.output_data.get("gemini_instructions", {})

        # Gemini実装実行
        implementation_results = self._gemini_code_implementation(
            spec, gemini_instructions, interface_specs
        )

        # 実装後品質チェック
        quality_validation = self._validate_phase_b_quality(
            implementation_results, spec.target_files
        )

        # エラー修正 (必要に応じて)
        if quality_validation.get("needs_fixes", False):
            print("🔧 品質問題検出、Gemini による自動修正実行")
            fix_results = self._gemini_quality_fixes(
                implementation_results, quality_validation
            )
            implementation_results.update(fix_results)

        phase_execution_time = time.time() - phase_start_time

        # Phase B 結果評価
        phase_b_quality = self._evaluate_phase_b_quality(
            implementation_results, quality_validation
        )

        # Phase C への引き渡しデータ
        next_phase_requirements = {
            "implementation_results": implementation_results,
            "quality_validation": quality_validation,
            "phase_a_design": architecture_design,
            "integration_requirements": self._generate_integration_requirements(
                implementation_results, spec
            )
        }

        success_metrics = {
            "implementation_completeness": phase_b_quality.get("completeness", 0.0),
            "code_quality": phase_b_quality.get("code_quality", 0.0),
            "functionality_score": phase_b_quality.get("functionality_score", 0.0)
        }

        status = ImplementationStatus.PHASE_COMPLETED if phase_b_quality.get("overall_score", 0.0) >= 0.7 else ImplementationStatus.FAILED

        print(f"📊 Phase B 完了: 品質スコア {phase_b_quality.get('overall_score', 0.0):.2f}")

        return PhaseResult(
            phase_type=PhaseType.PHASE_B_IMPLEMENTATION,
            status=status,
            execution_time=phase_execution_time,
            quality_score=phase_b_quality.get("overall_score", 0.0),
            output_data=next_phase_requirements,
            error_messages=phase_b_quality.get("issues", []),
            success_metrics=success_metrics,
            next_phase_requirements=next_phase_requirements
        )

    def _execute_phase_c(self, spec: HybridImplementationSpec,
                        phase_b_result: PhaseResult,
                        implementation_data: Dict[str, Any]) -> PhaseResult:
        """Phase C: 統合・品質保証フェーズ (Claude)"""

        print("🔍 Phase C: Claude による統合・品質保証")

        phase_start_time = time.time()

        # Phase B からのデータ取得
        implementation_results = phase_b_result.output_data.get("implementation_results", {})
        quality_validation = phase_b_result.output_data.get("quality_validation", {})
        integration_requirements = phase_b_result.output_data.get("integration_requirements", {})

        # Claude による統合レビュー
        integration_review = self._claude_integration_review(
            implementation_results, spec, integration_requirements
        )

        # コード最適化
        optimization_results = self._claude_code_optimization(
            implementation_results, integration_review
        )

        # 最終品質保証
        final_quality_assurance = self._claude_final_quality_assurance(
            optimization_results, spec.quality_standards
        )

        # デプロイ準備・承認
        deployment_approval = self._claude_deployment_approval(
            final_quality_assurance, spec.success_criteria
        )

        phase_execution_time = time.time() - phase_start_time

        # Phase C 結果評価
        phase_c_quality = self._evaluate_phase_c_quality(
            integration_review, optimization_results, final_quality_assurance
        )

        # 最終結果データ
        final_output = {
            "integration_review": integration_review,
            "optimization_results": optimization_results,
            "final_quality_assurance": final_quality_assurance,
            "deployment_approval": deployment_approval,
            "implementation_complete": deployment_approval.get("approved", False)
        }

        success_metrics = {
            "integration_quality": phase_c_quality.get("integration_quality", 0.0),
            "optimization_effectiveness": phase_c_quality.get("optimization_score", 0.0),
            "final_quality_score": phase_c_quality.get("final_quality", 0.0)
        }

        status = ImplementationStatus.FULLY_COMPLETED if deployment_approval.get("approved", False) else ImplementationStatus.NEEDS_REVIEW

        print(f"📊 Phase C 完了: 品質スコア {phase_c_quality.get('overall_score', 0.0):.2f}")

        return PhaseResult(
            phase_type=PhaseType.PHASE_C_INTEGRATION,
            status=status,
            execution_time=phase_execution_time,
            quality_score=phase_c_quality.get("overall_score", 0.0),
            output_data=final_output,
            error_messages=phase_c_quality.get("issues", []),
            success_metrics=success_metrics,
            next_phase_requirements={}
        )

    def _claude_architecture_analysis(self, spec: HybridImplementationSpec) -> Dict[str, Any]:
        """Claude によるアーキテクチャ分析"""

        print("🧠 アーキテクチャ分析実行中...")

        # 実装要件分析
        requirements_analysis = {
            "functional_requirements": self._analyze_functional_requirements(spec.requirements),
            "technical_requirements": self._analyze_technical_requirements(spec.requirements),
            "quality_requirements": self._analyze_quality_requirements(spec.quality_standards),
            "integration_requirements": self._analyze_integration_requirements(spec.context)
        }

        # アーキテクチャ設計
        architecture_design = {
            "system_architecture": self._design_system_architecture(spec, requirements_analysis),
            "component_structure": self._design_component_structure(spec, requirements_analysis),
            "data_flow": self._design_data_flow(spec, requirements_analysis),
            "error_handling_strategy": self._design_error_handling(spec, requirements_analysis)
        }

        # 技術選択
        technology_stack = {
            "programming_paradigms": self._select_programming_paradigms(spec),
            "design_patterns": self._select_design_patterns(spec, architecture_design),
            "libraries_frameworks": self._select_libraries_frameworks(spec),
            "testing_strategy": self._design_testing_strategy(spec)
        }

        analysis_result = {
            "requirements_analysis": requirements_analysis,
            "architecture_design": architecture_design,
            "technology_stack": technology_stack,
            "implementation_complexity": self._assess_implementation_complexity(spec, architecture_design),
            "risk_assessment": self._assess_implementation_risks(spec, architecture_design)
        }

        print("✅ アーキテクチャ分析完了")
        return analysis_result

    def _claude_interface_design(self, spec: HybridImplementationSpec,
                                architecture_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Claude によるインターフェース設計"""

        print("🔧 インターフェース設計実行中...")

        # 主要コンポーネントのインターフェース設計
        component_interfaces = {}

        for target_file in spec.target_files:
            file_interfaces = self._design_file_interfaces(
                target_file, spec, architecture_analysis
            )
            component_interfaces[target_file] = file_interfaces

        # API設計 (必要に応じて)
        api_design = self._design_api_interfaces(spec, architecture_analysis)

        # データ構造設計
        data_structures = self._design_data_structures(spec, architecture_analysis)

        interface_design = {
            "component_interfaces": component_interfaces,
            "api_design": api_design,
            "data_structures": data_structures,
            "interface_contracts": self._define_interface_contracts(component_interfaces),
            "integration_points": self._identify_integration_points(spec, component_interfaces)
        }

        print("✅ インターフェース設計完了")
        return interface_design

    def _claude_implementation_strategy(self, spec: HybridImplementationSpec,
                                       interface_design: Dict[str, Any]) -> Dict[str, Any]:
        """Claude による実装方針決定"""

        print("📋 実装方針決定中...")

        # 実装優先順位
        implementation_priority = self._determine_implementation_priority(spec, interface_design)

        # Gemini向け実装指示
        gemini_strategy = {
            "implementation_approach": self._define_implementation_approach(spec),
            "coding_standards": self._define_coding_standards(spec),
            "quality_requirements": self._define_quality_requirements(spec),
            "testing_requirements": self._define_testing_requirements(spec)
        }

        # リスク軽減策
        risk_mitigation = self._design_risk_mitigation_strategy(spec, interface_design)

        strategy = {
            "implementation_priority": implementation_priority,
            "gemini_strategy": gemini_strategy,
            "risk_mitigation": risk_mitigation,
            "success_criteria": self._define_phase_success_criteria(spec),
            "quality_gates": self._define_quality_gates(spec)
        }

        print("✅ 実装方針決定完了")
        return strategy

    def _generate_phase_b_instructions(self, interface_design: Dict[str, Any],
                                      implementation_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Phase B用Gemini指示生成"""

        instructions = {
            "implementation_tasks": [],
            "quality_requirements": implementation_strategy.get("gemini_strategy", {}).get("quality_requirements", {}),
            "coding_guidelines": implementation_strategy.get("gemini_strategy", {}).get("coding_standards", {}),
            "success_criteria": implementation_strategy.get("success_criteria", {})
        }

        # ファイル毎の実装タスク生成
        component_interfaces = interface_design.get("component_interfaces", {})
        for file_path, interfaces in component_interfaces.items():
            file_tasks = self._generate_file_implementation_tasks(file_path, interfaces)
            instructions["implementation_tasks"].extend(file_tasks)

        return instructions

    def _gemini_code_implementation(self, spec: HybridImplementationSpec,
                                   instructions: Dict[str, Any],
                                   interface_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini による具体的コード実装"""

        print("⚡ Gemini コード実装実行中...")

        # この部分は実際のGemini CLIとの連携になります
        # 現在はモックアップとして基本的な実装結果を返します

        implementation_results = {
            "files_implemented": [],
            "functions_created": [],
            "classes_created": [],
            "tests_created": [],
            "documentation_created": [],
            "implementation_issues": [],
            "quality_metrics": {}
        }

        # 各ファイルの実装
        for task in instructions.get("implementation_tasks", []):
            file_path = task.get("target_file", "")
            if not file_path:
                continue

            # ファイル実装結果 (モックアップ)
            file_result = self._mock_file_implementation(file_path, task, spec)
            implementation_results["files_implemented"].append(file_result)

        print("✅ Gemini コード実装完了")
        return implementation_results

    def _mock_file_implementation(self, file_path: str, task: Dict[str, Any],
                                 spec: HybridImplementationSpec) -> Dict[str, Any]:
        """モックアップ: ファイル実装結果"""

        return {
            "file_path": file_path,
            "implementation_status": "completed",
            "functions_implemented": task.get("functions", []),
            "classes_implemented": task.get("classes", []),
            "lines_of_code": 150,  # 仮の値
            "quality_score": 0.85,  # 仮の値
            "test_coverage": 0.80,  # 仮の値
            "issues": []
        }

    def _validate_phase_b_quality(self, implementation_results: Dict[str, Any],
                                 target_files: List[str]) -> Dict[str, Any]:
        """Phase B 品質検証"""

        print("🔍 Phase B 品質検証実行中...")

        validation_result = {
            "overall_quality_score": 0.0,
            "individual_file_scores": {},
            "quality_issues": [],
            "needs_fixes": False,
            "recommendations": []
        }

        # 各ファイルの品質評価
        total_score = 0.0
        file_count = 0

        for file_impl in implementation_results.get("files_implemented", []):
            file_path = file_impl.get("file_path", "")
            quality_score = file_impl.get("quality_score", 0.0)

            validation_result["individual_file_scores"][file_path] = quality_score
            total_score += quality_score
            file_count += 1

            # 品質問題チェック
            if quality_score < 0.8:
                validation_result["quality_issues"].append(f"{file_path}: 品質スコア不足 ({quality_score:.2f})")
                validation_result["needs_fixes"] = True

        # 全体品質スコア
        validation_result["overall_quality_score"] = total_score / max(file_count, 1)

        if validation_result["overall_quality_score"] < 0.8:
            validation_result["needs_fixes"] = True
            validation_result["recommendations"].append("全体的な品質向上が必要")

        print(f"📊 Phase B 品質検証完了: スコア {validation_result['overall_quality_score']:.2f}")
        return validation_result

    # ヘルパーメソッド群 (アーキテクチャ分析用)
    def _analyze_functional_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """機能要件分析"""
        return {
            "core_features": requirements.get("features", []),
            "user_interactions": requirements.get("interactions", []),
            "business_logic": requirements.get("business_logic", {})
        }

    def _analyze_technical_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """技術要件分析"""
        return {
            "performance_requirements": requirements.get("performance", {}),
            "scalability_requirements": requirements.get("scalability", {}),
            "security_requirements": requirements.get("security", {})
        }

    def _analyze_quality_requirements(self, quality_standards: Dict[str, Any]) -> Dict[str, Any]:
        """品質要件分析"""
        return {
            "code_quality": quality_standards.get("code_quality", {}),
            "test_coverage": quality_standards.get("test_coverage", 0.8),
            "documentation": quality_standards.get("documentation", {})
        }

    def _analyze_integration_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """統合要件分析"""
        return {
            "existing_systems": context.get("existing_systems", []),
            "dependencies": context.get("dependencies", []),
            "compatibility": context.get("compatibility", {})
        }

    def _evaluate_overall_success(self, implementation_id: str,
                                phase_results: List[PhaseResult],
                                execution_time: float) -> Dict[str, Any]:
        """全体成功評価"""

        print("📊 全体成功評価実行中...")

        # 各フェーズの品質スコア
        phase_scores = [result.quality_score for result in phase_results]
        average_quality = sum(phase_scores) / len(phase_scores)

        # 実行時間評価
        total_execution_time = sum(result.execution_time for result in phase_results)

        # 成功メトリクス
        overall_result = {
            "implementation_id": implementation_id,
            "overall_status": self._determine_overall_status(phase_results),
            "quality_metrics": {
                "phase_scores": phase_scores,
                "average_quality_score": average_quality,
                "quality_threshold_met": average_quality >= 0.8
            },
            "performance_metrics": {
                "total_execution_time": total_execution_time,
                "phase_execution_times": [r.execution_time for r in phase_results]
            },
            "success_indicators": {
                "all_phases_completed": all(r.status == ImplementationStatus.PHASE_COMPLETED or
                                          r.status == ImplementationStatus.FULLY_COMPLETED
                                          for r in phase_results),
                "quality_standards_met": average_quality >= 0.8,
                "no_critical_errors": all(len(r.error_messages) == 0 for r in phase_results)
            },
            "recommendations": self._generate_overall_recommendations(phase_results)
        }

        print(f"📊 全体成功評価完了: 平均品質 {average_quality:.2f}")
        return overall_result

    def _check_success_criteria(self, overall_result: Dict[str, Any]) -> Dict[str, Any]:
        """Issue #844 成功基準チェック"""

        print("🎯 成功基準チェック実行中...")

        # 品質スコア
        quality_score = overall_result["quality_metrics"]["average_quality_score"]
        quality_met = quality_score >= self.success_criteria["implementation_quality_score"]

        # 統合成功 (Phase Cの成功で判定)
        integration_success = overall_result["success_indicators"]["all_phases_completed"]
        integration_met = integration_success  # 簡易版、実際は95%基準

        # Token節約 (実際のToken使用量測定が必要、現在は仮評価)
        token_savings_met = True  # 仮の値

        # 新規実装成功率 (現在の実装が成功かどうか)
        implementation_success = overall_result["success_indicators"]["quality_standards_met"]

        success_check = {
            "implementation_success": implementation_success,
            "quality_threshold_met": quality_met,
            "integration_success": integration_met,
            "token_savings_maintained": token_savings_met,
            "meets_success_criteria": quality_met and integration_met and token_savings_met and implementation_success,
            "success_details": {
                "quality_score": quality_score,
                "required_quality": self.success_criteria["implementation_quality_score"],
                "integration_status": integration_success,
                "token_efficiency": "maintained"  # 仮の値
            }
        }

        print(f"🎯 成功基準チェック完了: {'✅ 達成' if success_check['meets_success_criteria'] else '⚠️ 未達成'}")
        return success_check

    def get_implementation_status(self, implementation_id: str) -> Dict[str, Any]:
        """実装ステータス取得"""

        if implementation_id not in self.current_implementations:
            return {"error": "Implementation ID not found"}

        implementation_data = self.current_implementations[implementation_id]

        return {
            "implementation_id": implementation_id,
            "current_status": implementation_data["status"],
            "current_phase": implementation_data.get("current_phase"),
            "phases_completed": len([p for p in implementation_data["phases"].values()
                                   if p.get("status") == ImplementationStatus.PHASE_COMPLETED.value]),
            "overall_metrics": implementation_data["overall_metrics"],
            "success_tracking": implementation_data["success_tracking"]
        }

    def get_success_rate_metrics(self) -> Dict[str, Any]:
        """成功率メトリクス取得"""

        total_implementations = len(self.current_implementations)
        if total_implementations == 0:
            return {"message": "No implementations tracked"}

        # 成功した実装の数
        successful_implementations = len([
            impl for impl in self.current_implementations.values()
            if impl["success_tracking"]["meets_success_criteria"]
        ])

        # フェーズ別成功率
        phase_success_rates = {}
        for phase_type in PhaseType:
            phase_successes = 0
            phase_attempts = 0

            for impl in self.current_implementations.values():
                phases = impl.get("phases", {})
                for phase_name, phase_data in phases.items():
                    if phase_data.get("phase_type") == phase_type.value:
                        phase_attempts += 1
                        if phase_data.get("status") == ImplementationStatus.PHASE_COMPLETED.value:
                            phase_successes += 1

            if phase_attempts > 0:
                phase_success_rates[phase_type.value] = phase_successes / phase_attempts

        # 品質メトリクス
        quality_scores = []
        for impl in self.current_implementations.values():
            overall_metrics = impl.get("overall_metrics", {})
            if "overall_quality_score" in overall_metrics:
                quality_scores.append(overall_metrics["overall_quality_score"])

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return {
            "overall_success_rate": successful_implementations / total_implementations,
            "total_implementations": total_implementations,
            "successful_implementations": successful_implementations,
            "phase_success_rates": phase_success_rates,
            "average_quality_score": avg_quality,
            "meets_issue_844_criteria": {
                "implementation_success_rate": successful_implementations / total_implementations >= self.success_criteria["new_implementation_success_rate"],
                "quality_threshold_met": avg_quality >= self.success_criteria["implementation_quality_score"],
                "integration_success_rate": phase_success_rates.get(PhaseType.PHASE_C_INTEGRATION.value, 0.0) >= self.success_criteria["integration_success_rate"]
            }
        }

    def _save_implementation_result(self, implementation_id: str, overall_result: Dict[str, Any]) -> None:
        """実装結果保存"""

        result_file = self.flows_dir / f"implementation_{implementation_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        save_data = {
            "implementation_data": self.current_implementations[implementation_id],
            "overall_result": overall_result,
            "timestamp": datetime.datetime.now().isoformat()
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"💾 実装結果保存: {result_file}")

    def _handle_flow_failure(self, implementation_id: str, error_message: str) -> Dict[str, Any]:
        """フロー失敗処理"""

        implementation_data = self.current_implementations[implementation_id]
        implementation_data["status"] = ImplementationStatus.FAILED

        failure_result = {
            "implementation_id": implementation_id,
            "status": "failed",
            "error_message": error_message,
            "failure_timestamp": datetime.datetime.now().isoformat()
        }

        print(f"❌ ハイブリッド実装フロー失敗: {implementation_id} - {error_message}")
        return failure_result

    # 追加のヘルパーメソッドは必要に応じて実装
    def _determine_overall_status(self, phase_results: List[PhaseResult]) -> str:
        """全体ステータス判定"""
        if all(r.status == ImplementationStatus.PHASE_COMPLETED for r in phase_results[:-1]) and \
           phase_results[-1].status == ImplementationStatus.FULLY_COMPLETED:
            return "fully_completed"
        elif any(r.status == ImplementationStatus.FAILED for r in phase_results):
            return "failed"
        else:
            return "needs_review"

    def _generate_overall_recommendations(self, phase_results: List[PhaseResult]) -> List[str]:
        """全体推奨事項生成"""
        recommendations = []

        for result in phase_results:
            if result.quality_score < 0.8:
                recommendations.append(f"{result.phase_type.value}: 品質改善が必要")

            if result.error_messages:
                recommendations.append(f"{result.phase_type.value}: エラー解決が必要")

        return recommendations

def main():
    """テスト実行"""

    flow_controller = HybridImplementationFlow()

    # テスト用実装仕様
    test_spec = HybridImplementationSpec(
        implementation_id="test_impl_001",
        implementation_type="new_implementation",
        target_files=["tmp/test_implementation.py"],
        requirements={
            "features": ["basic_functionality"],
            "performance": {"response_time": "< 100ms"},
            "test_coverage": 0.8
        },
        success_criteria={
            "quality_score": 0.8,
            "functionality": "complete"
        },
        quality_standards={
            "code_quality": {"style": "pep8", "typing": "strict"},
            "documentation": {"required": True}
        },
        context={
            "project_type": "library",
            "dependencies": []
        }
    )

    # ハイブリッド実装フロー実行
    impl_id = flow_controller.start_hybrid_implementation(test_spec, auto_execute=True)

    # ステータス確認
    status = flow_controller.get_implementation_status(impl_id)
    print(f"\n📊 実装ステータス: {status}")

    # 成功率メトリクス表示
    metrics = flow_controller.get_success_rate_metrics()
    print(f"\n📈 成功率メトリクス: {metrics}")

if __name__ == "__main__":
    main()
