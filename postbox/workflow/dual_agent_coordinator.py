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
from core.workflow_decision_engine import WorkflowDecisionEngine, AutomationLevel
from quality.quality_manager import QualityManager
from monitoring.quality_monitor import QualityMonitor
from reporting.quality_reporter import QualityReporter

class DualAgentCoordinator:
    """Claude ↔ Gemini協業の統合コーディネーター"""

    def __init__(self):
        self.task_manager = TaskManager()
        self.gemini_helper = GeminiHelper()
        self.task_analyzer = TaskAnalyzer()
        self.flash_templates = Flash25Templates()
        self.decision_engine = WorkflowDecisionEngine()
        self.quality_manager = QualityManager()
        self.quality_monitor = QualityMonitor()
        self.quality_reporter = QualityReporter()
        self.session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"🤖 Dual-Agent Workflow 開始 (Flash 2.5 最適化)")
        print(f"📋 セッションID: {self.session_id}")
        print(f"🔄 Claude Code ↔ Gemini CLI 協業システム")
        print(f"🧠 タスク微分化エンジン: 有効")
        print(f"📝 Flash 2.5 テンプレート: 有効")
        print(f"🎯 自動判定エンジン: 有効")
        print(f"🔍 統合品質管理: 有効")
        print(f"📊 品質監視システム: 有効")

    def create_mypy_fix_task(self,
                           target_files: List[str],
                           error_type: str = "no-untyped-def",
                           priority: str = "high",
                           use_micro_tasks: bool = True,
                           force_mode: str = None,
                           auto_execute: bool = True) -> List[str]:
        """mypy修正タスク作成（自動判定・実行機能付き）"""

        print(f"🔍 タスク作成開始: {error_type} エラー修正")
        print(f"📁 対象ファイル: {len(target_files)}件")
        print(f"🧠 微分化モード: {'有効' if use_micro_tasks else '無効'}")

        # ===== 自動判定フェーズ =====
        task_description = f"{error_type} エラー修正 - {len(target_files)}ファイル"

        # タスク分析実行
        task_analysis = self.decision_engine.analyze_task(
            task_description, target_files, error_type,
            context={"priority": priority, "session_id": self.session_id}
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
                target_files, error_type, priority, use_micro_tasks, decision
            )
        else:
            print(f"\n🧠 Claude単独モードで実行")
            created_task_ids = self._create_with_claude_mode(
                target_files, error_type, priority, decision
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

    def _create_with_gemini_mode(self, target_files: List[str], error_type: str,
                                priority: str, use_micro_tasks: bool, decision) -> List[str]:
        """Gemini協業モードでのタスク作成"""

        created_task_ids = []

        for file_path in target_files:
            print(f"\n📄 ファイル分析: {file_path}")

            if use_micro_tasks:
                # タスク微分化: ファイル → 関数レベル分割
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
                                priority: str, decision) -> List[str]:
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

        # Flash 2.5向け具体的指示生成
        flash_instruction = self._generate_batch_flash_instruction(tasks, error_type)

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

    def _generate_batch_flash_instruction(self, tasks: List[Dict], error_type: str) -> str:
        """バッチ用Flash 2.5指示生成"""

        template = self.flash_templates.get_template(error_type)
        base_instruction = template.get("flash_instruction_template", "")

        # バッチ固有の指示
        batch_instruction = f"""
🚀 Flash 2.5 バッチ修正指示

📦 バッチ概要:
- 修正対象: {len(tasks)}個の関数
- エラータイプ: {template.get('name', error_type)}
- 難易度: {template.get('difficulty', 'medium')}

{base_instruction}

📋 修正対象リスト:
"""

        for i, task in enumerate(tasks, 1):
            func_name = task.get('target_function', 'unknown')
            error_count = task.get('error_count', 0)
            batch_instruction += f"{i}. {func_name}関数 ({error_count}エラー)\n"

        batch_instruction += f"""
⚡ Flash 2.5 最適化ルール:
1. 上記リストの順番で1つずつ修正
2. 各関数の修正完了後、次の関数へ
3. 分からない場合は type: ignore 使用
4. 修正時間: 1関数あたり最大5分

🎯 成功パターン:
- 例に従った正確な修正
- 既存コードの最小変更
- 段階的な進行
"""

        return batch_instruction

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
        """Gemini CLI でのタスク実行"""

        try:
            # Gemini Helper経由で実行
            result = self.gemini_helper.execute_task(task_data)

            # コスト追跡
            token_usage = {
                "input_tokens": 1500,  # 推定値
                "output_tokens": 800,   # 推定値
                "model": "gemini-2.5-flash"
            }

            self.task_manager.track_cost(task_data["task_id"], token_usage)

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_data["task_id"]
            }

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
        print(f"  総コスト: ${progress_report['cost_metrics']['total_cost']:.4f}")

        print("\n🎉 Dual-Agent Workflow セッション完了!")

    def run_quality_check(self, target_files: List[str], ai_agent: str = "claude") -> Dict[str, Any]:
        """品質チェック実行"""
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

    def _check_quality_standards(self, metrics) -> bool:
        """品質基準チェック"""

        # 最低品質基準 (standards.jsonから取得)
        minimum_score = 0.7
        maximum_errors = 10

        standards_met = True

        if metrics.overall_score < minimum_score:
            standards_met = False

        if metrics.error_count > maximum_errors:
            standards_met = False

        # 重要な品質指標の個別チェック
        if metrics.type_score < 0.8:  # 型チェックは特に重要
            standards_met = False

        if metrics.security_score < 0.9:  # セキュリティも重要
            standards_met = False

        return standards_met

    def generate_quality_report(self, format_type: str = "html") -> str:
        """品質レポート生成"""
        print(f"📊 品質レポート生成中 (形式: {format_type})")

        report_path = self.quality_reporter.generate_comprehensive_report(format_type)

        print(f"✅ 品質レポート生成完了: {report_path}")
        return report_path

    def start_quality_monitoring(self) -> None:
        """品質監視開始"""
        print("📊 品質監視システム開始")
        self.quality_monitor.start_monitoring()

        # アラート通知設定
        def alert_handler(alert):
            print(f"🚨 品質アラート: {alert.message}")

        self.quality_monitor.subscribe_to_alerts(alert_handler)

    def get_quality_status(self) -> Dict[str, Any]:
        """現在の品質ステータス取得"""

        # 品質監視システムのステータス
        monitor_status = self.quality_monitor.get_current_status()

        # 品質レポートデータ
        quality_report_data = self.quality_manager.get_quality_report()

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
