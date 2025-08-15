#!/usr/bin/env python3
"""Claude-Gemini オーケストレーション体制

Claude(PM/Manager) - Gemini(Coder) の明確な上下関係による協業システム。
Token削減90%を目標に、シンプルで効果的な役割分担を実現する。

Roles:
- Claude: 要件分析・設計・作業指示・品質管理・最終調整
- Gemini: 指示に基づく実装のみ

Created: 2025-08-15 (Issue #888)
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

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

    def __post_init__(self):
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

    def __post_init__(self):
        if not self.executed_at:
            self.executed_at = datetime.now().isoformat()

class ClaudeGeminiOrchestrator:
    """Claude-Gemini オーケストレーター

    Claude(PM/Manager)とGemini(Coder)の協業を管理し、
    明確な役割分担によるToken削減を実現する。
    """

    def __init__(self):
        """初期化"""
        self.reports_dir = Path(__file__).parent
        self.work_instructions_dir = self.reports_dir / "work_instructions"
        self.execution_results_dir = self.reports_dir / "execution_results"
        self.orchestration_log = self.reports_dir / "orchestration_log.json"

        # ディレクトリ作成
        self.work_instructions_dir.mkdir(exist_ok=True)
        self.execution_results_dir.mkdir(exist_ok=True)

    def analyze_requirements(self, user_request: str) -> Dict[str, Any]:
        """要件分析（Claude専任）

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

        # タスクタイプ別テンプレート選択（改良版）
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
        print(f"🤖 実際のGemini API実行開始: {instruction.title}")
        print(f"📋 タスクID: {instruction.task_id}")
        print(f"⚙️ 複雑度: {instruction.complexity.value}")

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
            from .gemini_api_executor import GeminiAPIExecutor
            from .api_config import GeminiAPIConfig

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
            result.errors.append(f"Gemini API実行エラー: {str(e)}")
            print(f"❌ Gemini API実行失敗: {e}")

        # 実行時間計算
        end_time = datetime.now()
        result.execution_time = int((end_time - start_time).total_seconds())

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
        """Claudeによる品質レビュー・調整

        Args:
            result: Geminiの実行結果

        Returns:
            調整後の結果
        """
        print(f"👑 Claude品質レビュー開始: {result.task_id}")

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
        """完全ワークフロー実行

        Args:
            user_request: ユーザー要求

        Returns:
            最終実行結果
        """
        print(f"🎯 オーケストレーション開始: {user_request[:50]}...")

        # Phase 1: Claude による要件分析
        print("📋 Phase 1: 要件分析 (Claude)")
        analysis = self.analyze_requirements(user_request)

        if not analysis["gemini_suitable"]:
            print("⚠️ このタスクはClaude専任が適切です")
            return self._create_claude_only_result(user_request)

        # Phase 2: Claude による作業指示書作成
        print("📝 Phase 2: 作業指示書作成 (Claude)")
        instruction = self.create_work_instruction(analysis)

        # Phase 3: Gemini による実装
        print("⚡ Phase 3: 実装実行 (Gemini)")
        result = await self.execute_with_gemini(instruction)

        # Phase 4: Claude による品質レビュー・調整
        print("👑 Phase 4: 品質レビュー・調整 (Claude)")
        final_result = await self.review_and_adjust(result)

        # オーケストレーションログ記録
        self._log_orchestration(user_request, analysis, instruction, final_result)

        print(f"🎉 オーケストレーション完了: {final_result.status.value}")
        return final_result

    def get_orchestration_stats(self) -> Dict[str, Any]:
        """オーケストレーション統計取得

        Returns:
            統計情報
        """
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0,
            "avg_execution_time": 0,
            "token_savings": {
                "total_claude_tokens": 0,
                "total_gemini_tokens": 0,
                "estimated_saved_tokens": 0,
                "savings_rate": 0
            },
            "complexity_breakdown": {
                "simple": 0,
                "moderate": 0,
                "complex": 0
            },
            "last_updated": datetime.now().isoformat()
        }

        # ログファイルから統計算出
        if self.orchestration_log.exists():
            with open(self.orchestration_log, "r", encoding="utf-8") as f:
                logs = json.load(f)

            stats["total_tasks"] = len(logs)
            stats["completed_tasks"] = sum(
                1 for log in logs
                if log.get("final_result", {}).get("status") == "completed"
            )
            stats["failed_tasks"] = stats["total_tasks"] - stats["completed_tasks"]

            if stats["total_tasks"] > 0:
                stats["success_rate"] = stats["completed_tasks"] / stats["total_tasks"]

        return stats

    # === プライベートメソッド ===

    def _determine_complexity(self, request: str) -> str:
        """複雑度判定"""
        request_lower = request.lower()

        # 単純パターン
        simple_patterns = ["lint", "format", "mypy", "flake8", "black", "isort", "型注釈"]
        if any(pattern in request_lower for pattern in simple_patterns):
            return TaskComplexity.SIMPLE.value

        # 複雑パターン
        complex_patterns = ["アーキテクチャ", "設計", "新機能", "大規模", "リファクタリング"]
        if any(pattern in request_lower for pattern in complex_patterns):
            return TaskComplexity.COMPLEX.value

        return TaskComplexity.MODERATE.value

    def _classify_task_type(self, request: str) -> str:
        """タスク種別分類"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["lint", "format", "整形"]):
            return "formatting"
        elif any(word in request_lower for word in ["mypy", "型", "注釈"]):
            return "type_annotation"
        elif any(word in request_lower for word in ["テスト", "test"]):
            return "testing"
        elif any(word in request_lower for word in ["バグ", "修正", "fix"]):
            return "bugfix"
        elif any(word in request_lower for word in ["機能", "実装", "追加"]):
            return "feature"
        else:
            return "other"

    def _estimate_effort(self, request: str) -> int:
        """工数推定（分）"""
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

        high_risk_patterns = ["削除", "破壊的", "アーキテクチャ", "データベース"]
        if any(pattern in request_lower for pattern in high_risk_patterns):
            return "high"

        low_risk_patterns = ["format", "lint", "型注釈", "コメント"]
        if any(pattern in request_lower for pattern in low_risk_patterns):
            return "low"

        return "medium"

    def _is_gemini_suitable(self, request: str) -> bool:
        """Gemini適性判定"""
        # 明確に定義されたコーディング作業はGemini適
        suitable_patterns = [
            "mypy", "lint", "flake8", "black", "isort", "型注釈",
            "バグ修正", "テスト", "実装", "修正"
        ]

        request_lower = request.lower()
        return any(pattern in request_lower for pattern in suitable_patterns)

    def _needs_breakdown(self, request: str) -> bool:
        """タスク分割必要性判定"""
        complex_indicators = ["複数", "大規模", "統合", "全体", "システム"]
        request_lower = request.lower()
        return any(indicator in request_lower for indicator in complex_indicators)

    def _get_instruction_template(self, complexity: str) -> Dict[str, List[str]]:
        """複雑度別テンプレート取得"""
        templates = {
            TaskComplexity.SIMPLE.value: {
                "implementation_details": [
                    "指定されたツールを実行してください",
                    "エラーが発生した場合は自動修正してください",
                    "全ファイルが品質基準を満たすまで繰り返してください"
                ],
                "quality_criteria": [
                    "MyPy strict mode 全通過",
                    "Flake8 エラー0件",
                    "Black/isort 適用済み"
                ],
                "prohibited_actions": [
                    "独自判断での仕様変更",
                    "品質基準の緩和",
                    "未承認ツールの使用"
                ],
                "expected_files": ["修正対象ファイルのみ"],
                "dependencies": []
            },
            TaskComplexity.MODERATE.value: {
                "implementation_details": [
                    "要件に従って機能を実装してください",
                    "既存コードとの整合性を保ってください",
                    "適切なテストを追加してください"
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
                "expected_files": ["実装ファイル", "テストファイル", "ドキュメント"],
                "dependencies": ["既存システムとの整合性確認"]
            },
            TaskComplexity.COMPLEX.value: {
                "implementation_details": [
                    "アーキテクチャ設計に従って実装してください",
                    "段階的に実装し、各段階で品質確認してください",
                    "詳細な進捗報告を作成してください"
                ],
                "quality_criteria": [
                    "アーキテクチャ設計通りの実装",
                    "全体テストの通過",
                    "パフォーマンス基準の達成",
                    "セキュリティ要件の満足"
                ],
                "prohibited_actions": [
                    "設計からの逸脱",
                    "未承認ライブラリの使用",
                    "パフォーマンス要件の無視"
                ],
                "expected_files": ["複数モジュール", "統合テスト", "設計書更新"],
                "dependencies": ["他モジュールとの依存関係確認"]
            }
        }

        return templates.get(complexity, templates[TaskComplexity.MODERATE.value])

    def _get_enhanced_instruction_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """タスク内容に基づく強化されたテンプレート選択

        Args:
            analysis: 要件分析結果

        Returns:
            適切なテンプレート
        """
        request = analysis["original_request"].lower()
        task_type = analysis.get("task_type", "")

        # MyPy修正専用テンプレート
        if any(keyword in request for keyword in ['mypy', '型注釈', 'type annotation', 'エラー修正']):
            return self._get_mypy_fix_template(analysis)

        # Lint修正専用テンプレート
        if any(keyword in request for keyword in ['flake8', 'lint', 'black', 'isort']):
            return self._get_lint_fix_template(analysis)

        # 既存ファイル修正テンプレート
        if any(keyword in request for keyword in ['修正', 'fix', '改修', 'バグ']) and \
           any(dir_name in request for dir_name in ['gemini_reports/', 'kumihan_formatter/', 'core/']):
            return self._get_file_modification_template(analysis)

        # デフォルトテンプレート（従来の方式）
        return self._get_instruction_template(analysis["complexity"])

    def _get_mypy_fix_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """MyPy修正専用テンプレート"""
        request = analysis["original_request"]

        # 対象ディレクトリを特定
        target_dir = "gemini_reports/"
        if "kumihan_formatter" in request:
            target_dir = "kumihan_formatter/"
        elif "core/" in request:
            target_dir = "kumihan_formatter/core/"

        return {
            "implementation_details": [
                f"対象ディレクトリ: {target_dir}",
                "以下の形式で既存ファイルを修正してください:",
                "",
                "# ファイル: 実際のファイルパス（例: gemini_reports/api_config.py）",
                "```python",
                "修正後の完全なファイル内容",
                "```",
                "",
                "主要な修正パターン:",
                "- 関数・メソッドに型注釈追加: def func(param: int) -> str:",
                "- 変数の型注釈: variable: Optional[str] = None",
                "- import文の最適化: from typing import Optional, Dict, List",
                "- Any型の具体的型への変更",
                "- Noneチェックの追加: if value is not None:",
                "",
                "⚠️ 重要: 新規ファイル作成ではなく、既存ファイルの直接修正を行ってください"
            ],
            "quality_criteria": [
                "MyPy strict mode 完全通過",
                "全関数・メソッドに適切な型注釈",
                "typing importの最適化完了",
                "既存機能の動作保証"
            ],
            "prohibited_actions": [
                "新規ファイルの作成",
                "tmp/配下への保存",
                "機能の削除・変更",
                "APIの破壊的変更"
            ],
            "expected_files": [
                f"{target_dir}内の既存Pythonファイル",
                "修正対象ファイルのみ（新規作成不可）"
            ],
            "dependencies": [
                "typing モジュール",
                "既存コードとの互換性維持"
            ]
        }

    def _get_lint_fix_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Lint修正専用テンプレート"""
        return {
            "implementation_details": [
                "Black/isort/flake8エラーの修正を実行:",
                "- コードフォーマット統一",
                "- import文の整理",
                "- 行長制限の遵守",
                "- 未使用import削除",
                "既存ファイルを直接修正してください"
            ],
            "quality_criteria": [
                "Black通過: 行長88文字",
                "isort通過: import順序正規化",
                "Flake8通過: エラー0件"
            ],
            "prohibited_actions": [
                "機能の変更",
                "新規ファイル作成"
            ],
            "expected_files": ["修正対象ファイルのみ"],
            "dependencies": []
        }

    def _get_file_modification_template(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """既存ファイル修正テンプレート"""
        return {
            "implementation_details": [
                "既存ファイルの修正・改良を実行",
                "現在の機能を維持しつつ改善",
                "適切な形式でファイルパスを指定",
                "バックアップ不要（Git管理下）"
            ],
            "quality_criteria": [
                "既存機能の動作保証",
                "コード品質の向上",
                "適切なエラーハンドリング"
            ],
            "prohibited_actions": [
                "機能の削除",
                "API仕様の変更",
                "新規ファイル作成"
            ],
            "expected_files": ["修正対象ファイルのみ"],
            "dependencies": ["既存システムとの整合性"]
        }

    def _save_work_instruction(self, instruction: WorkInstruction) -> None:
        """作業指示書保存"""
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

    def _create_gemini_script(self, instruction: WorkInstruction) -> Path:
        """Gemini実行スクリプト生成"""
        script_file = self.reports_dir / f"gemini_script_{instruction.task_id}.py"

        script_content = f'''#!/usr/bin/env python3
"""Gemini実行スクリプト
タスクID: {instruction.task_id}
タイトル: {instruction.title}
複雑度: {instruction.complexity.value}
"""

import subprocess
import sys
import json
from pathlib import Path

def execute_task():
    """タスク実行"""
    print("🤖 Gemini実行開始")
    print(f"タスク: {instruction.title}")

    results = {{
        "task_id": "{instruction.task_id}",
        "implemented_files": [],
        "modified_lines": 0,
        "quality_checks": {{}},
        "output": "",
        "errors": []
    }}

    try:
        # 複雑度別実行ロジック
        if "{instruction.complexity.value}" == "simple":
            results = execute_simple_task()
        elif "{instruction.complexity.value}" == "moderate":
            results = execute_moderate_task()
        else:
            results = execute_complex_task()

    except Exception as e:
        results["errors"].append(str(e))
        return False

    # 結果をJSONで出力（Claude解析用）
    print("GEMINI_RESULT_START")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("GEMINI_RESULT_END")

    return len(results["errors"]) == 0

def execute_simple_task():
    """単純タスク実行"""
    results = {{"implemented_files": [], "modified_lines": 0, "output": ""}}

    # MyPy, Flake8, Blackなどの実行
    commands = [
        ["python3", "-m", "mypy", "kumihan_formatter", "--strict"],
        ["python3", "-m", "flake8", "kumihan_formatter"],
        ["python3", "-m", "black", "kumihan_formatter"],
        ["python3", "-m", "isort", "kumihan_formatter"]
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        results["output"] += f"Command: {{' '.join(cmd)}}\\n"
        results["output"] += f"Return code: {{result.returncode}}\\n"
        results["output"] += f"Stdout: {{result.stdout}}\\n"
        if result.stderr:
            results["output"] += f"Stderr: {{result.stderr}}\\n"
        results["output"] += "\\n"

    return results

def execute_moderate_task():
    """中規模タスク実行"""
    results = {{"implemented_files": [], "modified_lines": 0, "output": ""}}

    # TODO: より複雑な実装ロジック
    results["output"] = "中規模タスク実行（実装予定）"

    return results

def execute_complex_task():
    """複雑タスク実行"""
    results = {{"implemented_files": [], "modified_lines": 0, "output": ""}}

    # TODO: 複雑なアーキテクチャ実装
    results["output"] = "複雑タスク実行（実装予定）"

    return results

if __name__ == "__main__":
    success = execute_task()
    sys.exit(0 if success else 1)
'''

        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        script_file.chmod(0o755)
        return script_file

    def _extract_implemented_files(self, output: str) -> List[str]:
        """実装ファイル抽出"""
        # TODO: Gemini出力から実装ファイルリストを抽出
        return []

    def _count_modified_lines(self, output: str) -> int:
        """修正行数カウント"""
        # TODO: 修正行数を算出
        return 0

    def _save_execution_result(self, result: ExecutionResult) -> None:
        """実行結果保存"""
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
        """品質チェック実行"""
        checks = {}

        # MyPyチェック
        mypy_result = subprocess.run(
            ["python3", "-m", "mypy", "kumihan_formatter", "--strict"],
            capture_output=True, text=True
        )
        checks["mypy_pass"] = mypy_result.returncode == 0

        # Flake8チェック
        flake8_result = subprocess.run(
            ["python3", "-m", "flake8", "kumihan_formatter"],
            capture_output=True, text=True
        )
        checks["flake8_pass"] = flake8_result.returncode == 0

        # Blackチェック
        black_result = subprocess.run(
            ["python3", "-m", "black", "--check", "kumihan_formatter"],
            capture_output=True, text=True
        )
        checks["black_pass"] = black_result.returncode == 0

        return checks

    def _perform_claude_adjustment(self, result: ExecutionResult) -> Dict[str, Any]:
        """Claude調整実行"""
        print("👑 Claude調整実行中...")

        adjustment = {
            "adjustments_made": [],
            "warnings": []
        }

        # 品質問題に応じた調整
        if not result.quality_checks.get("black_pass", True):
            subprocess.run(["python3", "-m", "black", "kumihan_formatter"])
            adjustment["adjustments_made"].append("Blackフォーマット適用")

        if not result.quality_checks.get("flake8_pass", True):
            adjustment["warnings"].append("Flake8エラーの手動確認が必要")

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
        logs = []
        if self.orchestration_log.exists():
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

        with open(self.orchestration_log, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

async def main():
    """CLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude-Gemini オーケストレーター")
    parser.add_argument("--request", help="ユーザー要求")
    parser.add_argument("--analyze", help="要件分析のみ実行")
    parser.add_argument("--stats", action="store_true", help="統計情報表示")

    args = parser.parse_args()

    orchestrator = ClaudeGeminiOrchestrator()

    if args.stats:
        stats = orchestrator.get_orchestration_stats()
        print("📊 オーケストレーション統計")
        print("=" * 50)
        print(f"総タスク数: {stats['total_tasks']}")
        print(f"完了タスク: {stats['completed_tasks']}")
        print(f"失敗タスク: {stats['failed_tasks']}")
        print(f"成功率: {stats['success_rate']:.1%}")
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
