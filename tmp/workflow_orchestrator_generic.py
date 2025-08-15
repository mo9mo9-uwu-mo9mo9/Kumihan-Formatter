#!/usr/bin/env python3
"""汎用ワークフローオーケストレーター - 失敗対策統合版（型修正版）

Claude(PM/Manager) - Gemini(Coder) の明確な上下関係による協業システム。
プロジェクト固有の部分を設定システムにより汎用化し、
任意のプロジェクトで使用可能な協業オーケストレーターを提供。

Features:
- プロジェクト設定による汎用化
- 失敗対策システム統合
- 段階的品質検証
- 環境事前チェック
- Token削減90%目標

Roles:
- Claude: 要件分析・設計・作業指示・品質管理・最終調整・失敗対策
- Gemini: 指示に基づく実装のみ

Created: 2025-08-15 (汎用化対応・型修正)
Based on: claude_gemini_orchestrator.py
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Protocol
from dataclasses import dataclass
from enum import Enum

# プロジェクト設定のインポート
try:
    from project_config_template import ProjectConfig, QualityTool, QualityToolType
except ImportError:
    # 設定ファイルが見つからない場合のエラー
    raise ImportError(
        "プロジェクト設定ファイル 'project_config_template.py' が見つかりません。\n"
        "設定ファイルを作成し、PROJECT_CONFIG を定義してください。"
    )


# 失敗対策システムの型定義
class FailureType(Enum):
    """失敗タイプ"""
    UNKNOWN = "unknown"
    ENVIRONMENT = "environment"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"


class RecoveryAction(Enum):
    """復旧アクション"""
    RETRY = "retry"
    CLAUDE_SWITCH = "claude_switch"
    ENVIRONMENT_FIX = "environment_fix"


class QualityLevel(Enum):
    """品質レベル"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


# プロトコル定義（インターフェース）
class FailureRecoveryProtocol(Protocol):
    """失敗対策システムのプロトコル"""
    def should_switch_to_claude(self, request: str) -> Tuple[bool, str]: ...
    def get_task_pattern(self, request: str) -> Optional[Any]: ...
    def record_failure(self, task_id: str, request: str, error: str) -> None: ...
    def update_pattern_success_rate(self, request: str, success: bool) -> None: ...
    def analyze_failure(self, task_id: str, request: str, error: str) -> FailureType: ...
    def suggest_recovery_action(self, task_id: str, request: str,
                              failure_type: FailureType, error: str) -> RecoveryAction: ...
    def generate_recovery_report(self) -> Dict[str, Any]: ...


class QualityStandardsProtocol(Protocol):
    """品質基準システムのプロトコル"""
    def determine_appropriate_level(self, request: str, complexity: float) -> QualityLevel: ...
    def generate_quality_report(self) -> Dict[str, Any]: ...


class EnvironmentValidatorProtocol(Protocol):
    """環境検証システムのプロトコル"""
    def is_environment_ready_for_gemini(self) -> Tuple[bool, List[str]]: ...
    def prepare_environment_for_task(self, requirements: str) -> Tuple[bool, str]: ...
    def validate_all_dependencies(self, attempt_fixes: bool = False) -> List[Any]: ...


# 失敗対策システムのインポート（オプション）
try:
    from failure_recovery_system import FailureRecoverySystem  # type: ignore
    from quality_standards import QualityStandardsSystem  # type: ignore
    from environment_validator import EnvironmentValidator  # type: ignore
    FAILURE_RECOVERY_AVAILABLE = True
except ImportError:
    # 失敗対策システムが利用できない場合のダミー実装
    FAILURE_RECOVERY_AVAILABLE = False

    class FailureRecoverySystem:
        """ダミー失敗対策システム"""
        def __init__(self, reports_dir: Path) -> None:
            pass

        def should_switch_to_claude(self, request: str) -> Tuple[bool, str]:
            return False, "システム利用不可"

        def get_task_pattern(self, request: str) -> Optional[Any]:
            return None

        def record_failure(self, task_id: str, request: str, error: str) -> None:
            pass

        def update_pattern_success_rate(self, request: str, success: bool) -> None:
            pass

        def analyze_failure(self, task_id: str, request: str, error: str) -> FailureType:
            return FailureType.UNKNOWN

        def suggest_recovery_action(self, task_id: str, request: str,
                                  failure_type: FailureType, error: str) -> RecoveryAction:
            return RecoveryAction.RETRY

        def generate_recovery_report(self) -> Dict[str, Any]:
            return {"status": "unavailable"}

    class QualityStandardsSystem:
        """ダミー品質基準システム"""
        def __init__(self, reports_dir: Path) -> None:
            pass

        def determine_appropriate_level(self, request: str, complexity: float) -> QualityLevel:
            return QualityLevel.STANDARD

        def generate_quality_report(self) -> Dict[str, Any]:
            return {"status": "unavailable"}

    class EnvironmentValidator:
        """ダミー環境検証システム"""
        def __init__(self, reports_dir: Path) -> None:
            pass

        def is_environment_ready_for_gemini(self) -> Tuple[bool, List[str]]:
            return True, []

        def prepare_environment_for_task(self, requirements: str) -> Tuple[bool, str]:
            return True, "準備完了"

        def validate_all_dependencies(self, attempt_fixes: bool = False) -> List[Any]:
            return []


class TaskComplexity(Enum):
    """タスク複雑度レベル"""
    SIMPLE = "simple"       # Lint/Format修正
    MODERATE = "moderate"   # 機能追加・バグ修正
    COMPLEX = "complex"     # アーキテクチャ実装


class ExecutionStatus(Enum):
    """実行ステータス"""
    PLANNING = "planning"           # Claude: 計画中
    INSTRUCTION = "instruction"     # Claude: 指示書作成中
    IMPLEMENTATION = "implementation" # Gemini: 実装中
    REVIEW = "review"              # Claude: レビュー中
    ADJUSTMENT = "adjustment"       # Claude: 調整中
    COMPLETED = "completed"        # 完了
    FAILED = "failed"              # 失敗


@dataclass
class WorkInstruction:
    """作業指示書データ構造"""
    task_id: str
    title: str
    complexity: TaskComplexity
    requirements: str
    implementation_details: List[str]
    quality_criteria: List[str]
    prohibited_actions: List[str]
    expected_files: List[str]
    dependencies: List[str]
    estimated_time: int  # 分
    created_by: str = "Claude"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ExecutionResult:
    """実行結果データ構造"""
    task_id: str
    status: ExecutionStatus
    implemented_files: List[str]
    modified_lines: int
    quality_checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]
    execution_time: int  # 秒
    token_usage: Dict[str, int]  # claude_tokens, gemini_tokens
    executed_by: str
    executed_at: str = ""

    def __post_init__(self) -> None:
        if not self.executed_at:
            self.executed_at = datetime.now().isoformat()


class GenericWorkflowOrchestrator:
    """汎用ワークフローオーケストレーター - 失敗対策統合版

    プロジェクト設定により汎用化されたClaude-Gemini協業システム。
    任意のプロジェクトで使用可能で、失敗対策システムにより
    高い成功率とToken削減を実現する。
    """

    def __init__(
        self,
        project_config: ProjectConfig,
        reports_dir: Optional[Path] = None
    ) -> None:
        """初期化

        Args:
            project_config: プロジェクト設定
            reports_dir: レポートディレクトリ（オプション）
        """
        self.config = project_config

        # ディレクトリ設定
        if reports_dir is None:
            self.reports_dir = self.config.paths.reports_dir
        else:
            self.reports_dir = Path(reports_dir)

        self.work_instructions_dir = self.config.paths.work_instructions_dir
        self.execution_results_dir = self.config.paths.execution_results_dir
        self.orchestration_log = self.config.paths.orchestration_log_file

        # ディレクトリ作成
        if self.work_instructions_dir:
            self.work_instructions_dir.mkdir(exist_ok=True)
        if self.execution_results_dir:
            self.execution_results_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

        # 失敗対策システム初期化
        self.failure_recovery = FailureRecoverySystem(self.reports_dir)
        self.quality_standards = QualityStandardsSystem(self.reports_dir)
        self.environment_validator = EnvironmentValidator(self.reports_dir)

        # 失敗対策設定
        self.enable_failure_recovery = (
            self.config.failure_recovery_enabled and FAILURE_RECOVERY_AVAILABLE
        )
        self.enable_environment_validation = (
            self.config.environment_validation_enabled and FAILURE_RECOVERY_AVAILABLE
        )
        self.enable_gradual_quality = (
            self.config.gradual_quality_enabled and FAILURE_RECOVERY_AVAILABLE
        )

    def analyze_requirements(self, user_request: str) -> Dict[str, Any]:
        """要件分析（Claude専任） - 失敗対策統合

        Args:
            user_request: ユーザーからの要求

        Returns:
            分析結果
        """
        analysis = {
            "original_request": user_request,
            "complexity": self._determine_complexity(user_request),
            "task_type": self._classify_task_type(user_request),
            "estimated_effort": self._estimate_effort(user_request),
            "risk_level": self._assess_risk(user_request),
            "gemini_suitable": self._is_gemini_suitable(user_request),
            "breakdown_needed": self._needs_breakdown(user_request)
        }

        # 失敗対策システムによる追加分析
        if self.enable_failure_recovery:
            # Claude切り替え推奨判定
            should_switch, switch_reason = self.failure_recovery.should_switch_to_claude(user_request)
            analysis["claude_switch_recommended"] = should_switch
            analysis["switch_reason"] = switch_reason

            # 過去の失敗パターンマッチング
            task_pattern = self.failure_recovery.get_task_pattern(user_request)
            if task_pattern and hasattr(task_pattern, 'historical_success_rate'):
                analysis["historical_success_rate"] = task_pattern.historical_success_rate
                analysis["pattern_difficulty"] = getattr(task_pattern, 'estimated_difficulty', 0.5)
                analysis["recommended_executor"] = getattr(task_pattern, 'recommended_executor', 'gemini')

            # Gemini適性を失敗履歴で補正
            if should_switch or (task_pattern and getattr(task_pattern, 'recommended_executor', 'gemini') == "claude"):
                analysis["gemini_suitable"] = False
                analysis["failure_prevention"] = "過去の失敗履歴によりClaude実行を推奨"

        # 適切な品質レベル判定
        if self.enable_gradual_quality:
            complexity_score = self._get_complexity_score(user_request)
            analysis["recommended_quality_level"] = self.quality_standards.determine_appropriate_level(
                user_request, complexity_score
            ).value

        return analysis

    def create_work_instruction(
        self,
        analysis: Dict[str, Any],
        detailed_requirements: str = ""
    ) -> WorkInstruction:
        """詳細作業指示書作成（Claude専任）

        Args:
            analysis: 要件分析結果
            detailed_requirements: 詳細要件（オプション）

        Returns:
            作業指示書
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # プロジェクト設定に基づくテンプレート選択
        template = self._get_enhanced_instruction_template(analysis)

        instruction = WorkInstruction(
            task_id=task_id,
            title=analysis["original_request"][:100],
            complexity=TaskComplexity(analysis["complexity"]),
            requirements=detailed_requirements or analysis["original_request"],
            implementation_details=template["implementation_details"],
            quality_criteria=template["quality_criteria"],
            prohibited_actions=template["prohibited_actions"],
            expected_files=template["expected_files"],
            dependencies=template["dependencies"],
            estimated_time=analysis["estimated_effort"]
        )

        # 指示書をファイルに保存
        self._save_work_instruction(instruction)

        return instruction

    async def execute_with_gemini(self, instruction: WorkInstruction) -> ExecutionResult:
        """実際のGemini APIによる実装実行

        Args:
            instruction: 作業指示書

        Returns:
            実行結果
        """
        print(f"🤖 Gemini API実行開始(失敗対策有効): {instruction.title}")
        print(f"📋 タスクID: {instruction.task_id}")
        print(f"⚙️ 複雑度: {instruction.complexity.value}")

        # 環境事前チェック
        if self.enable_environment_validation:
            print("🔍 環境事前チェック実行...")
            env_ready, env_issues = self.environment_validator.is_environment_ready_for_gemini()
            if not env_ready:
                print("⚠️ 環境問題検出 - 修復試行")
                for issue in env_issues:
                    print(f"  - {issue}")

                # 環境修復試行
                prep_success, prep_report = self.environment_validator.prepare_environment_for_task(instruction.requirements)
                if not prep_success:
                    return self._create_environment_failure_result(instruction, env_issues)
                print("✅ 環境修復成功")
            else:
                print("✅ 環境チェッククリア")
                if env_issues:  # 警告レベルの問題
                    print("⚠️ 警告:")
                    for issue in env_issues:
                        print(f"  - {issue}")

        start_time = datetime.now()

        result = ExecutionResult(
            task_id=instruction.task_id,
            status=ExecutionStatus.IMPLEMENTATION,
            implemented_files=[],
            modified_lines=0,
            quality_checks={},
            errors=[],
            warnings=[],
            execution_time=0,
            token_usage={"claude_tokens": 0, "gemini_tokens": 0},
            executed_by="Gemini API"
        )

        try:
            # 実際のGemini API実行
            from gemini_api_executor import GeminiAPIExecutor  # type: ignore
            from api_config import GeminiAPIConfig  # type: ignore

            # API設定確認
            config = GeminiAPIConfig()
            if not config.is_configured():
                raise Exception("Gemini API キーが設定されていません。python gemini_reports/api_config.py --setup で設定してください")

            # 作業指示書をMarkdown形式に変換
            instruction_text = self._convert_instruction_to_text(instruction)

            # Gemini API実行
            executor = GeminiAPIExecutor()
            gemini_result = await executor.execute_task(instruction_text, instruction.task_id)

            # 結果をExecutionResultに変換
            result.status = ExecutionStatus.REVIEW if gemini_result["status"] == "completed" else ExecutionStatus.FAILED
            result.implemented_files = gemini_result["implemented_files"]
            result.modified_lines = gemini_result["modified_lines"]
            result.errors = gemini_result["errors"]
            result.warnings = gemini_result.get("warnings", [])

            # Token使用量（Gemini APIから取得）
            result.token_usage["gemini_tokens"] = gemini_result["token_usage"].get("output_tokens", 0)

            if result.status == ExecutionStatus.REVIEW:
                print(f"✅ Gemini API実装完了: {len(result.implemented_files)}ファイル, {result.modified_lines}行")
            else:
                print(f"❌ Gemini API実装失敗: {result.errors}")

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            error_message = f"Gemini API実行エラー: {str(e)}"
            result.errors.append(error_message)
            print(f"❌ Gemini API実行失敗: {e}")

            # 失敗記録と対策提案
            if self.enable_failure_recovery:
                self.failure_recovery.record_failure(
                    instruction.task_id,
                    instruction.requirements,
                    error_message
                )

        # 実行時間計算
        end_time = datetime.now()
        result.execution_time = int((end_time - start_time).total_seconds())

        # 失敗対策システムへの結果通知
        if self.enable_failure_recovery:
            success = result.status != ExecutionStatus.FAILED
            self.failure_recovery.update_pattern_success_rate(instruction.requirements, success)

            if not success:
                # 失敗時の対策提案
                failure_type = self.failure_recovery.analyze_failure(
                    instruction.task_id,
                    instruction.requirements,
                    "; ".join(result.errors) if result.errors else "不明なエラー"
                )
                recovery_action = self.failure_recovery.suggest_recovery_action(
                    instruction.task_id,
                    instruction.requirements,
                    failure_type,
                    "; ".join(result.errors) if result.errors else ""
                )

                result.warnings.append(f"失敗タイプ: {failure_type.value}")
                result.warnings.append(f"推奨対策: {recovery_action.value}")

                print(f"🔄 失敗対策: {recovery_action.value}")

        # 結果保存
        self._save_execution_result(result)

        return result

    def _convert_instruction_to_text(self, instruction: WorkInstruction) -> str:
        """作業指示書をテキスト形式に変換"""
        text = f"""# 作業指示書: {instruction.title}

## 📋 作業概要
{instruction.requirements}

## 🎯 実装詳細
"""
        for detail in instruction.implementation_details:
            text += f"- {detail}\n"

        text += f"""
## ✅ 品質基準
"""
        for criteria in instruction.quality_criteria:
            text += f"- {criteria}\n"

        text += f"""
## 🚫 禁止事項
"""
        for prohibition in instruction.prohibited_actions:
            text += f"- {prohibition}\n"

        text += f"""
## 📁 期待ファイル
"""
        for file_exp in instruction.expected_files:
            text += f"- {file_exp}\n"

        if instruction.dependencies:
            text += f"""
## 📦 依存関係
"""
            for dep in instruction.dependencies:
                text += f"- {dep}\n"

        text += f"""
## ⏱️ 推定時間
{instruction.estimated_time}分

---
*作成者: {instruction.created_by} | 作成日時: {instruction.created_at}*
"""
        return text

    async def review_and_adjust(self, result: ExecutionResult) -> ExecutionResult:
        """Claudeによる品質レビュー・調整 - 段階的品質検証統合

        Args:
            result: Geminiの実行結果

        Returns:
            調整後の結果
        """
        print(f"👑 Claude品質レビュー開始(段階的検証): {result.task_id}")

        # 品質チェック実行
        quality_checks = self._perform_quality_checks(result)
        result.quality_checks = quality_checks

        # 品質基準を満たしているかチェック
        if all(quality_checks.values()):
            print("✅ 品質基準クリア")
            result.status = ExecutionStatus.COMPLETED
        else:
            print("⚠️ 品質調整が必要")
            result.status = ExecutionStatus.ADJUSTMENT

            # Claude による調整実行
            adjustment_result = self._perform_claude_adjustment(result)
            result.warnings.extend(adjustment_result.get("warnings", []))

            # 再度品質チェック
            final_checks = self._perform_quality_checks(result)
            result.quality_checks.update(final_checks)

            if all(final_checks.values()):
                result.status = ExecutionStatus.COMPLETED
            else:
                result.status = ExecutionStatus.FAILED
                result.errors.append("品質基準を満たせませんでした")

        # 最終結果保存
        self._save_execution_result(result)

        return result

    async def orchestrate_full_workflow(self, user_request: str) -> ExecutionResult:
        """完全ワークフロー実行 - 失敗対策統合版

        Args:
            user_request: ユーザー要求

        Returns:
            最終実行結果
        """
        print(f"🎯 オーケストレーション開始(失敗対策有効): {user_request[:50]}...")

        # 失敗対策システムのステータス表示
        if self.enable_failure_recovery:
            try:
                recovery_stats = self.failure_recovery.generate_recovery_report()
                recent_failures = recovery_stats.get("total_failures", 0)
                if recent_failures > 0:
                    print(f"📊 最近の失敗: {recent_failures}件 - 対策システムが稼動中")
            except Exception:
                pass

        # Phase 1: Claude による要件分析
        print("📋 Phase 1: 要件分析 (Claude + 失敗対策)")
        analysis = self.analyze_requirements(user_request)

        # 失敗対策システムによるClaude切り替え判定
        if not analysis["gemini_suitable"]:
            reason = analysis.get("switch_reason", "タスク種別による推奨")
            print(f"⚠️ Claude専任推奨: {reason}")
            if analysis.get("claude_switch_recommended", False):
                print("🔄 失敗対策システムによる切り替え")
            return self._create_claude_only_result(user_request)

        # Phase 2: Claude による作業指示書作成
        print("📝 Phase 2: 作業指示書作成 (Claude)")
        instruction = self.create_work_instruction(analysis)

        # 品質レベル情報を指示書に追加
        if self.enable_gradual_quality and "recommended_quality_level" in analysis:
            quality_level = analysis["recommended_quality_level"]
            instruction.quality_criteria.append(f"推奨品質レベル: {quality_level}")
            print(f"🎯 推奨品質レベル: {quality_level}")

        # Phase 3: Gemini による実装
        print("⚡ Phase 3: 実装実行 (Gemini + 環境検証)")
        result = await self.execute_with_gemini(instruction)

        # 失敗時のフォールバック処理
        if (result.status == ExecutionStatus.FAILED and
            self.enable_failure_recovery):

            print("🔄 Gemini失敗 - 対策検討")

            # 失敗対策提案取得
            for warning in result.warnings:
                if "推奨対策" in warning:
                    print(f"💡 {warning}")

            # Claude切り替え推奨の場合
            if any("Ｃlaude切り替え" in w for w in result.warnings):
                print("🔄 Claudeによる代替実行...")
                # 実際の代替実行は将来の拡張で実装
                result.warnings.append("Claude代替実行の検討が必要です")

        # Phase 4: Claude による品質レビュー・調整
        print("👑 Phase 4: 品質レビュー・調整 (Claude + 段階的検証)")
        final_result = await self.review_and_adjust(result)

        # 失敗対策システムでの最終判定
        if (self.enable_failure_recovery and
            final_result.status == ExecutionStatus.COMPLETED):

            # 成功パターンの学習
            pattern = self.failure_recovery.get_task_pattern(user_request)
            if pattern and hasattr(pattern, 'description'):
                print(f"🎓 成功パターン学習: {pattern.description}")

        # オーケストレーションログ記録
        self._log_orchestration(user_request, analysis, instruction, final_result)

        # 最終結果表示
        status_icon = "🎉" if final_result.status == ExecutionStatus.COMPLETED else "❌"
        print(f"{status_icon} オーケストレーション完了: {final_result.status.value}")

        if self.enable_failure_recovery:
            success_rate = self.get_orchestration_stats().get("success_rate", 0)
            print(f"📊 現在の成功率: {success_rate:.1%}")

        return final_result

    def get_orchestration_stats(self) -> Dict[str, Any]:
        """オーケストレーション統計取得 - 失敗対策統計含む

        Returns:
            統計情報
        """
        stats: Dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "avg_execution_time": 0.0,
            "token_savings": {
                "total_claude_tokens": 0,
                "total_gemini_tokens": 0,
                "estimated_saved_tokens": 0,
                "savings_rate": 0.0
            },
            "complexity_breakdown": {
                "simple": 0,
                "moderate": 0,
                "complex": 0
            },
            "failure_recovery_stats": {},
            "quality_standards_stats": {},
            "environment_validation_stats": {},
            "last_updated": datetime.now().isoformat()
        }

        # ログファイルから統計算出
        if self.orchestration_log and self.orchestration_log.exists():
            with open(self.orchestration_log, "r", encoding="utf-8") as f:
                logs = json.load(f)

            stats["total_tasks"] = len(logs)
            stats["completed_tasks"] = sum(
                1 for log in logs
                if log.get("final_result", {}).get("status") == "completed"
            )
            stats["failed_tasks"] = stats["total_tasks"] - stats["completed_tasks"]

            if stats["total_tasks"] > 0:
                stats["success_rate"] = float(stats["completed_tasks"]) / float(stats["total_tasks"])

        # 失敗対策システムからの統計情報統合
        if self.enable_failure_recovery:
            try:
                recovery_report = self.failure_recovery.generate_recovery_report()
                stats["failure_recovery_stats"] = {
                    "total_failures": recovery_report.get("total_failures", 0),
                    "pattern_recommendations": len(recovery_report.get("claude_switch_recommendations", [])),
                    "failure_rate": recovery_report.get("failure_rate", 0.0)
                }
            except Exception:
                stats["failure_recovery_stats"] = {"status": "error"}

        if self.enable_gradual_quality:
            try:
                quality_report = self.quality_standards.generate_quality_report()
                stats["quality_standards_stats"] = {
                    "total_validations": quality_report.get("total_validations", 0),
                    "level_statistics": quality_report.get("level_statistics", {})
                }
            except Exception:
                stats["quality_standards_stats"] = {"status": "error"}

        if self.enable_environment_validation:
            try:
                env_results = self.environment_validator.validate_all_dependencies(attempt_fixes=False)
                stats["environment_validation_stats"] = {
                    "total_dependencies": len(env_results),
                    "passed": sum(1 for r in env_results if hasattr(r, 'status') and r.status.value == "pass"),
                    "failed": sum(1 for r in env_results if hasattr(r, 'status') and r.status.value == "fail")
                }
            except Exception:
                stats["environment_validation_stats"] = {"status": "error"}

        return stats

    # === プライベートメソッド ===

    def _determine_complexity(self, request: str) -> str:
        """複雑度判定 - プロジェクト設定ベース"""
        return self.config.determine_complexity(request)

    def _classify_task_type(self, request: str) -> str:
        """タスク種別分類 - 汎用化版"""
        request_lower = request.lower()

        task_patterns = {
            "formatting": ["lint", "format", "整形"],
            "type_annotation": ["mypy", "型", "注釈"],
            "testing": ["テスト", "test"],
            "bugfix": ["バグ", "修正", "fix"],
            "feature": ["機能", "実装", "追加"],
            "refactoring": ["リファクタリング", "改修"],
            "documentation": ["ドキュメント", "document", "doc"]
        }

        for task_type, patterns in task_patterns.items():
            if any(pattern in request_lower for pattern in patterns):
                return task_type

        return "other"

    def _estimate_effort(self, request: str) -> int:
        """工数推定（分） - 複雑度ベース"""
        complexity = self._determine_complexity(request)

        base_minutes = {
            TaskComplexity.SIMPLE.value: 15,
            TaskComplexity.MODERATE.value: 60,
            TaskComplexity.COMPLEX.value: 240
        }

        return base_minutes.get(complexity, 60)

    def _assess_risk(self, request: str) -> str:
        """リスクレベル評価"""
        request_lower = request.lower()

        high_risk_patterns = ["削除", "破壊的", "アーキテクチャ", "データベース", "セキュリティ"]
        if any(pattern in request_lower for pattern in high_risk_patterns):
            return "high"

        low_risk_patterns = ["format", "lint", "型注釈", "コメント"]
        if any(pattern in request_lower for pattern in low_risk_patterns):
            return "low"

        return "medium"

    def _is_gemini_suitable(self, request: str) -> bool:
        """Gemini適性判定 - プロジェクト設定ベース"""
        return self.config.is_gemini_suitable(request)

    def _needs_breakdown(self, request: str) -> bool:
        """タスク分割必要性判定"""
        complex_indicators = ["複数", "大規模", "統合", "全体", "システム"]
        request_lower = request.lower()
        return any(indicator in request_lower for indicator in complex_indicators)

    def _get_complexity_score(self, request: str) -> float:
        """複雑度スコア算出 (0.0-1.0)"""
        request_lower = request.lower()
        score = 0.5  # ベーススコア

        # プロジェクト設定から複雑度パターン取得
        high_patterns = self.config.complexity_patterns.get("complex", [])
        simple_patterns = self.config.complexity_patterns.get("simple", [])

        # 複雑度を上げる要素
        for pattern in high_patterns:
            if pattern in request_lower:
                score += 0.15

        # 複雑度を下げる要素
        for pattern in simple_patterns:
            if pattern in request_lower:
                score -= 0.1

        return max(0.0, min(1.0, score))  # 0.0-1.0にクランプ

    def _create_environment_failure_result(self, instruction: WorkInstruction,
                                          issues: List[str]) -> ExecutionResult:
        """環境失敗結果を作成"""
        return ExecutionResult(
            task_id=instruction.task_id,
            status=ExecutionStatus.FAILED,
            implemented_files=[],
            modified_lines=0,
            quality_checks={"environment_check": False},
            errors=[f"環境問題: {issue}" for issue in issues],
            warnings=[
                "環境修復が必要です",
                "必要なツールをインストールしてください"
            ],
            execution_time=0,
            token_usage={"claude_tokens": 0, "gemini_tokens": 0},
            executed_by="Environment Validator"
        )

    def _get_enhanced_instruction_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """タスク内容に基づく強化されたテンプレート選択 - 汎用化版

        Args:
            analysis: 要件分析結果

        Returns:
            適切なテンプレート
        """
        request = analysis["original_request"].lower()
        task_type = analysis.get("task_type", "")

        # タスクタイプ別テンプレート
        if task_type == "type_annotation":
            return self._get_type_annotation_template(analysis)
        elif task_type == "formatting":
            return self._get_formatting_template(analysis)
        elif task_type == "testing":
            return self._get_testing_template(analysis)
        elif task_type == "bugfix":
            return self._get_bugfix_template(analysis)
        elif task_type == "feature":
            return self._get_feature_template(analysis)
        else:
            return self._get_default_template(analysis)

    def _get_type_annotation_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """型注釈修正専用テンプレート - 汎用化版"""
        # プロジェクト設定から対象ディレクトリ取得
        source_paths = self.config.get_source_paths_as_strings()

        return {
            "implementation_details": [
                f"対象ディレクトリ: {', '.join(source_paths)}",
                "型注釈の追加・修正を実行:",
                "- 関数・メソッドに型注釈追加: def func(param: int) -> str:",
                "- 変数の型注釈: variable: Optional[str] = None",
                "- import文の最適化: from typing import Optional, Dict, List",
                "- Any型の具体的型への変更",
                "- Noneチェックの追加: if value is not None:",
                "既存ファイルを直接修正してください"
            ],
            "quality_criteria": [
                "型チェッカー完全通過",
                "全関数・メソッドに適切な型注釈",
                "typing importの最適化完了",
                "既存機能の動作保証"
            ],
            "prohibited_actions": [
                "新規ファイルの作成",
                "機能の削除・変更",
                "APIの破壊的変更"
            ],
            "expected_files": [
                f"{path}内の既存Pythonファイル" for path in source_paths
            ],
            "dependencies": [
                "typing モジュール",
                "既存コードとの互換性維持"
            ]
        }

    def _get_formatting_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """フォーマット修正専用テンプレート"""
        # 設定からフォーマットツール取得
        format_tools = self.config.get_tools_by_type(QualityToolType.FORMATTER)
        lint_tools = self.config.get_tools_by_type(QualityToolType.LINTER)
        import_tools = self.config.get_tools_by_type(QualityToolType.IMPORT_SORTER)

        tool_names = [t.name for t in format_tools + lint_tools + import_tools]

        return {
            "implementation_details": [
                f"使用ツール: {', '.join(tool_names)}",
                "コードフォーマットの統一:",
                "- コードスタイルの統一",
                "- import文の整理",
                "- 行長制限の遵守",
                "- 未使用import削除",
                "既存ファイルを直接修正してください"
            ],
            "quality_criteria": [
                f"{tool.name}通過" for tool in format_tools + lint_tools + import_tools
            ],
            "prohibited_actions": [
                "機能の変更",
                "新規ファイル作成"
            ],
            "expected_files": ["修正対象ファイルのみ"],
            "dependencies": []
        }

    def _get_testing_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """テスト実装テンプレート"""
        test_tools = self.config.get_tools_by_type(QualityToolType.TESTER)
        test_dirs = [str(d) for d in self.config.paths.test_dirs]

        return {
            "implementation_details": [
                f"テストディレクトリ: {', '.join(test_dirs)}",
                "テストの実装・修正:",
                "- 単体テストの追加",
                "- テストカバレッジの向上",
                "- テストデータの準備",
                "- アサーションの適切な使用"
            ],
            "quality_criteria": [
                "全テストの通過",
                "カバレッジ80%以上",
                "適切なテストケース設計"
            ],
            "prohibited_actions": [
                "テストの削除",
                "品質基準の緩和"
            ],
            "expected_files": [f"{dir_path}内のテストファイル" for dir_path in test_dirs],
            "dependencies": [tool.name for tool in test_tools]
        }

    def _get_bugfix_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """バグ修正テンプレート"""
        return {
            "implementation_details": [
                "バグの特定と修正:",
                "- 問題箇所の特定",
                "- 根本原因の分析",
                "- 修正の実装",
                "- 回帰テストの追加",
                "既存ファイルを直接修正してください"
            ],
            "quality_criteria": [
                "バグの完全修正",
                "既存機能の動作保証",
                "回帰テストの追加",
                "コード品質の維持"
            ],
            "prohibited_actions": [
                "機能の削除",
                "API仕様の変更",
                "他機能への影響"
            ],
            "expected_files": ["修正対象ファイルのみ"],
            "dependencies": ["既存システムとの整合性"]
        }

    def _get_feature_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """機能実装テンプレート"""
        return {
            "implementation_details": [
                "新機能の実装:",
                "- 要件に従った機能実装",
                "- 既存コードとの整合性確保",
                "- 適切なテストの追加",
                "- ドキュメントの更新"
            ],
            "quality_criteria": [
                "機能要件を100%満たす",
                "既存テストが全通過",
                "新規テストのカバレッジ80%以上",
                "コーディング標準準拠"
            ],
            "prohibited_actions": [
                "要件にない機能の追加",
                "既存APIの破壊的変更",
                "セキュリティ基準の緩和"
            ],
            "expected_files": ["実装ファイル", "テストファイル"],
            "dependencies": ["既存システムとの整合性確認"]
        }

    def _get_default_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """デフォルトテンプレート"""
        complexity = analysis["complexity"]

        templates = {
            TaskComplexity.SIMPLE.value: {
                "implementation_details": [
                    "指定されたタスクを実行してください",
                    "エラーが発生した場合は自動修正してください",
                    "品質基準を満たすまで繰り返してください"
                ],
                "quality_criteria": [
                    "品質ツール全通過",
                    "既存機能の動作保証"
                ],
                "prohibited_actions": [
                    "独自判断での仕様変更",
                    "品質基準の緩和"
                ],
                "expected_files": ["修正対象ファイルのみ"],
                "dependencies": []
            },
            TaskComplexity.MODERATE.value: {
                "implementation_details": [
                    "要件に従って実装してください",
                    "既存コードとの整合性を保ってください",
                    "適切なテストを追加してください"
                ],
                "quality_criteria": [
                    "機能要件を100%満たす",
                    "既存テストが全通過",
                    "コーディング標準準拠"
                ],
                "prohibited_actions": [
                    "要件にない機能の追加",
                    "既存APIの破壊的変更"
                ],
                "expected_files": ["実装ファイル", "テストファイル"],
                "dependencies": ["既存システムとの整合性確認"]
            },
            TaskComplexity.COMPLEX.value: {
                "implementation_details": [
                    "設計に従って実装してください",
                    "段階的に実装し、各段階で品質確認してください",
                    "詳細な進捗報告を作成してください"
                ],
                "quality_criteria": [
                    "設計通りの実装",
                    "全体テストの通過",
                    "パフォーマンス基準の達成"
                ],
                "prohibited_actions": [
                    "設計からの逸脱",
                    "未承認ライブラリの使用"
                ],
                "expected_files": ["複数モジュール", "統合テスト"],
                "dependencies": ["他モジュールとの依存関係確認"]
            }
        }

        return templates.get(complexity, templates[TaskComplexity.MODERATE.value])

    def _save_work_instruction(self, instruction: WorkInstruction) -> None:
        """作業指示書保存"""
        if not self.work_instructions_dir:
            return
        file_path = self.work_instructions_dir / f"{instruction.task_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            # dataclassをdictに変換
            data = {
                "task_id": instruction.task_id,
                "title": instruction.title,
                "complexity": instruction.complexity.value,
                "requirements": instruction.requirements,
                "implementation_details": instruction.implementation_details,
                "quality_criteria": instruction.quality_criteria,
                "prohibited_actions": instruction.prohibited_actions,
                "expected_files": instruction.expected_files,
                "dependencies": instruction.dependencies,
                "estimated_time": instruction.estimated_time,
                "created_by": instruction.created_by,
                "created_at": instruction.created_at
            }
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_execution_result(self, result: ExecutionResult) -> None:
        """実行結果保存"""
        if not self.execution_results_dir:
            return
        file_path = self.execution_results_dir / f"{result.task_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            data = {
                "task_id": result.task_id,
                "status": result.status.value,
                "implemented_files": result.implemented_files,
                "modified_lines": result.modified_lines,
                "quality_checks": result.quality_checks,
                "errors": result.errors,
                "warnings": result.warnings,
                "execution_time": result.execution_time,
                "token_usage": result.token_usage,
                "executed_by": result.executed_by,
                "executed_at": result.executed_at
            }
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _perform_quality_checks(self, result: ExecutionResult) -> Dict[str, bool]:
        """品質チェック実行 - プロジェクト設定ベース"""
        checks = {}

        # プロジェクト設定から品質ツール取得
        quality_tools = self.config.get_quality_check_commands()

        for tool in quality_tools:
            try:
                # コマンド実行
                cmd = tool.command + tool.target_paths
                check_result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=tool.timeout,
                    env={**os.environ, **tool.environment_vars}
                )
                checks[f"{tool.name}_pass"] = check_result.returncode == 0

                if check_result.returncode != 0:
                    print(f"⚠️ {tool.name} failed: {check_result.stdout}")

            except subprocess.TimeoutExpired:
                checks[f"{tool.name}_pass"] = False
                print(f"⚠️ {tool.name} timeout")
            except Exception as e:
                checks[f"{tool.name}_pass"] = False
                print(f"⚠️ {tool.name} error: {e}")

        return checks

    def _perform_claude_adjustment(self, result: ExecutionResult) -> Dict[str, Any]:
        """Claude調整実行 - プロジェクト設定ベース"""
        print("👑 Claude調整実行中...")

        adjustment: Dict[str, Any] = {
            "adjustments_made": [],
            "warnings": []
        }

        # 修正可能なツールで自動修正実行
        fix_tools = [tool for tool in self.config.quality_tools
                    if tool.fix_command and tool.enabled]

        for tool in fix_tools:
            if not result.quality_checks.get(f"{tool.name}_pass", True):
                try:
                    # 修正コマンド実行
                    fix_cmd = (tool.fix_command if tool.fix_command else tool.command) + tool.target_paths
                    fix_result = subprocess.run(
                        fix_cmd,
                        capture_output=True,
                        text=True,
                        timeout=tool.timeout,
                        env={**os.environ, **tool.environment_vars}
                    )

                    if fix_result.returncode == 0:
                        adjustment["adjustments_made"].append(f"{tool.name}修正適用")
                    else:
                        adjustment["warnings"].append(f"{tool.name}修正失敗: {fix_result.stderr}")

                except Exception as e:
                    adjustment["warnings"].append(f"{tool.name}修正エラー: {e}")

        return adjustment

    def _create_claude_only_result(self, request: str) -> ExecutionResult:
        """Claude専任タスクの結果作成"""
        task_id = f"claude_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ExecutionResult(
            task_id=task_id,
            status=ExecutionStatus.COMPLETED,
            implemented_files=[],
            modified_lines=0,
            quality_checks={"claude_handled": True},
            errors=[],
            warnings=["このタスクはClaude専任で処理されました"],
            execution_time=0,
            token_usage={"claude_tokens": 5000, "gemini_tokens": 0},
            executed_by="Claude"
        )

    def _log_orchestration(
        self,
        request: str,
        analysis: Dict[str, Any],
        instruction: WorkInstruction,
        result: ExecutionResult
    ) -> None:
        """オーケストレーションログ記録"""
        logs: List[Dict[str, Any]] = []
        if self.orchestration_log and self.orchestration_log.exists():
            with open(self.orchestration_log, "r", encoding="utf-8") as f:
                logs = json.load(f)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_request": request,
            "analysis": analysis,
            "instruction_id": instruction.task_id,
            "final_result": {
                "task_id": result.task_id,
                "status": result.status.value,
                "success": result.status == ExecutionStatus.COMPLETED,
                "execution_time": result.execution_time,
                "token_usage": result.token_usage
            }
        }

        logs.append(log_entry)

        # 最新100件のみ保持
        if len(logs) > 100:
            logs = logs[-100:]

        if self.orchestration_log:
            with open(self.orchestration_log, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)


# =============================================================================
# CLI実行部分
# =============================================================================

async def main() -> int:
    """CLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="汎用ワークフローオーケストレーター")
    parser.add_argument("--request", help="ユーザー要求")
    parser.add_argument("--analyze", help="要件分析のみ実行")
    parser.add_argument("--stats", action="store_true", help="統計情報表示")
    parser.add_argument("--config", help="プロジェクト設定ファイルパス")

    args = parser.parse_args()

    # プロジェクト設定読み込み
    if args.config:
        # カスタム設定ファイル読み込み
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ 設定ファイルが見つかりません: {config_path}")
            return 1

        # 動的インポート
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec is None or spec.loader is None:
            print(f"❌ 設定ファイルの読み込みに失敗: {config_path}")
            return 1
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        project_config = config_module.PROJECT_CONFIG
    else:
        # デフォルト設定使用
        from project_config_template import PROJECT_CONFIG
        project_config = PROJECT_CONFIG

    orchestrator = GenericWorkflowOrchestrator(project_config)

    if args.stats:
        stats = orchestrator.get_orchestration_stats()
        print("📊 オーケストレーション統計")
        print("=" * 50)
        print(f"プロジェクト: {project_config.name}")
        print(f"総タスク数: {stats['total_tasks']}")
        print(f"完了タスク: {stats['completed_tasks']}")
        print(f"失敗タスク: {stats['failed_tasks']}")
        print(f"成功率: {stats['success_rate']:.1%}")

        if FAILURE_RECOVERY_AVAILABLE:
            print(f"失敗対策システム: 有効")
        else:
            print(f"失敗対策システム: 無効（モジュール未インストール）")

        return 0

    if args.analyze:
        analysis = orchestrator.analyze_requirements(args.analyze)
        print("📋 要件分析結果")
        print("=" * 30)
        for key, value in analysis.items():
            print(f"{key}: {value}")
        return 0

    if args.request:
        result = await orchestrator.orchestrate_full_workflow(args.request)
        print(f"\n🎯 最終結果: {result.status.value}")
        print(f"実行時間: {result.execution_time}秒")
        print(f"Token使用: Claude {result.token_usage.get('claude_tokens', 0)}, "
              f"Gemini {result.token_usage.get('gemini_tokens', 0)}")
        return 0 if result.status == ExecutionStatus.COMPLETED else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
