#!/usr/bin/env python3
"""
Flash 2.5対応システム実証テスト
実際のエラーがあるファイルでの動作確認
"""

import sys
from pathlib import Path

# postboxモジュールをインポート
sys.path.append(str(Path(__file__).parent / "postbox"))

from workflow.dual_agent_coordinator import DualAgentCoordinator

def test_flash25_system():
    """Flash 2.5対応システムの実証テスト"""

    print("🧪 Flash 2.5対応システム実証テスト開始")
    print("=" * 60)

    # テスト対象ファイル（実際にエラーがあるファイル）
    test_file = "kumihan_formatter/core/keyword_parsing/models/parse_result.py"

    print(f"📄 テスト対象: {test_file}")
    print(f"🎯 エラータイプ: no-untyped-def")

    # 1. システム初期化
    coordinator = DualAgentCoordinator()

    # 2. タスク作成（微細分化テスト）
    print("\n🔍 Step 1: タスク作成・微細分化")
    task_ids = coordinator.create_mypy_fix_task(
        target_files=[test_file],
        error_type="no-untyped-def",
        priority="high",
        use_micro_tasks=True
    )

    print(f"✅ 作成されたタスク: {len(task_ids)}件")
    for task_id in task_ids:
        print(f"  - {task_id}")

    # 3. ワークフロー実行
    print("\n🚀 Step 2: ワークフロー実行")
    result = coordinator.execute_workflow_cycle()

    print(f"📊 実行結果: {result['status']}")

    # 4. 結果分析
    print("\n📋 Step 3: 結果分析")
    claude_review = result.get("claude_review", {})
    approval = claude_review.get("approval", "unknown")
    confidence = claude_review.get("confidence_score", 0)

    print(f"🎯 Claude承認: {approval}")
    print(f"📈 信頼度スコア: {confidence:.2f}")

    if claude_review.get("detailed_assessment"):
        assessment = claude_review["detailed_assessment"]
        print(f"🔧 コード品質: {assessment.get('code_quality', {}).get('level', 'unknown')}")
        print(f"📊 完了度: {assessment.get('completeness', {}).get('level', 'unknown')}")
        print(f"⚠️ リスクレベル: {assessment.get('risk_evaluation', {}).get('level', 'unknown')}")

    # 5. 推奨アクション表示
    if claude_review.get("recommendations"):
        print("\n💡 推奨アクション:")
        for rec in claude_review["recommendations"][:3]:
            print(f"  • {rec}")

    if claude_review.get("required_actions"):
        print("\n🚨 必須アクション:")
        for action in claude_review["required_actions"][:3]:
            print(f"  • {action}")

    # 6. Flash 2.5最適化効果測定
    print("\n⚡ Flash 2.5最適化効果:")
    gemini_result = result.get("gemini_result", {})
    modifications = gemini_result.get("modifications", {})

    errors_fixed = modifications.get("total_errors_fixed", 0)
    execution_time = result.get("execution_time", 0)

    print(f"🐛 修正エラー数: {errors_fixed}件")
    print(f"⏱️ 実行時間: {execution_time:.1f}秒")

    # 7. コスト効率性
    print("\n💰 コスト効率性:")
    # コスト追跡ファイルから最新のコスト情報を取得
    try:
        import json
        with open("postbox/monitoring/cost_tracking.json", "r") as f:
            cost_data = json.load(f)

        latest_cost = cost_data["tasks"][-1]["estimated_cost"] if cost_data["tasks"] else 0
        total_cost = cost_data["total_cost"]

        print(f"📊 今回のコスト: ${latest_cost:.4f}")
        print(f"📈 累積コスト: ${total_cost:.4f}")
        print(f"💡 コスト効率: ${latest_cost/max(1, errors_fixed):.4f}/エラー修正")

    except Exception as e:
        print(f"⚠️ コスト情報取得エラー: {e}")

    # 8. 総合評価
    print("\n" + "=" * 60)
    print("🏆 総合評価")
    print("=" * 60)

    if approval == "approved" and errors_fixed > 0:
        print("✅ Flash 2.5対応システム: 成功")
        print("🎯 複雑タスク処理能力: 確認済み")
        print("⚡ 微細分化システム: 効果的")
    elif approval in ["approved_with_conditions", "requires_review"]:
        print("⚠️ Flash 2.5対応システム: 部分的成功")
        print("🔍 改善の余地あり")
    else:
        print("❌ Flash 2.5対応システム: 問題あり")
        print("🚨 システム改善が必要")

    return result

if __name__ == "__main__":
    result = test_flash25_system()
