#!/usr/bin/env python3
"""
Task Manager for Claude ↔ Gemini Dual-Agent Workflow
タスク管理・進捗監視・コスト追跡のユーティリティ
"""

import json
import os
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TaskManager:
    """Claude ↔ Gemini協業のタスク管理"""

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.todo_dir = self.postbox_dir / "todo"
        self.completed_dir = self.postbox_dir / "completed"
        self.planning_dir = self.postbox_dir / "planning"
        self.monitoring_dir = self.postbox_dir / "monitoring"

        # ディレクトリ作成
        for dir_path in [self.todo_dir, self.completed_dir, self.planning_dir, self.monitoring_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def create_task(self,
                   task_type: str,
                   description: str,
                   target_files: List[str],
                   priority: str = "medium",
                   requirements: Optional[Dict] = None,
                   claude_analysis: str = "",
                   **kwargs) -> str:
        """タスク作成"""

        timestamp = datetime.datetime.now()
        task_id = f"task_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        task_data = {
            "task_id": task_id,
            "type": task_type,
            "priority": priority,
            "description": description,
            "target_files": target_files,
            "requirements": requirements or {},
            "claude_analysis": claude_analysis,
            "expected_outcome": kwargs.get("expected_outcome", ""),
            "constraints": kwargs.get("constraints", []),
            "context": kwargs.get("context", {}),
            "timestamp": timestamp.isoformat(),
            "created_by": "claude_code"
        }

        task_file = self.todo_dir / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        print(f"✅ タスク作成完了: {task_id}")
        print(f"📁 ファイル: {task_file}")

        return task_id

    def list_pending_tasks(self) -> List[Dict]:
        """未完了タスク一覧"""
        pending_tasks = []

        for task_file in self.todo_dir.glob("task_*.json"):
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                pending_tasks.append(task_data)

        # 優先度・作成日時でソート
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending_tasks.sort(key=lambda x: (
            priority_order.get(x.get("priority", "medium"), 1),
            x.get("timestamp", "")
        ))

        return pending_tasks

    def get_completed_results(self) -> List[Dict]:
        """完了結果一覧"""
        completed_results = []

        for result_file in self.completed_dir.glob("result_*.json"):
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
                completed_results.append(result_data)

        # 完了日時でソート（新しい順）
        completed_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return completed_results

    def track_cost(self, task_id: str, token_usage: Dict[str, Any]) -> None:
        """コスト追跡"""
        cost_file = self.monitoring_dir / "cost_tracking.json"

        # 既存データ読み込み
        if cost_file.exists():
            with open(cost_file, 'r', encoding='utf-8') as f:
                cost_data = json.load(f)
        else:
            cost_data = {"total_cost": 0.0, "tasks": []}

        # 新しいコストデータ追加
        cost_entry = {
            "task_id": task_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "token_usage": token_usage,
            "estimated_cost": self._calculate_cost(token_usage)
        }

        cost_data["tasks"].append(cost_entry)
        cost_data["total_cost"] += cost_entry["estimated_cost"]

        # 保存
        with open(cost_file, 'w', encoding='utf-8') as f:
            json.dump(cost_data, f, indent=2, ensure_ascii=False)

    def _calculate_cost(self, token_usage: Dict[str, Any]) -> float:
        """Gemini 2.5 Flash コスト計算"""
        input_tokens = token_usage.get("input_tokens", 0)
        output_tokens = token_usage.get("output_tokens", 0)

        # Gemini 2.5 Flash価格 (per 1M tokens)
        input_price = 0.30  # $0.30/1M tokens
        output_price = 2.50  # $2.50/1M tokens

        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price

        return input_cost + output_cost

    def generate_progress_report(self) -> Dict[str, Any]:
        """進捗レポート生成"""
        pending_tasks = self.list_pending_tasks()
        completed_results = self.get_completed_results()

        # 統計計算
        total_tasks = len(pending_tasks) + len(completed_results)
        completion_rate = len(completed_results) / total_tasks if total_tasks > 0 else 0

        # エラー修正統計
        total_errors_fixed = sum(
            result.get("modifications", {}).get("total_errors_fixed", 0)
            for result in completed_results
        )

        # コスト統計
        cost_file = self.monitoring_dir / "cost_tracking.json"
        total_cost = 0.0
        if cost_file.exists():
            with open(cost_file, 'r', encoding='utf-8') as f:
                cost_data = json.load(f)
                total_cost = cost_data.get("total_cost", 0.0)

        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "task_summary": {
                "total_tasks": total_tasks,
                "completed": len(completed_results),
                "pending": len(pending_tasks),
                "completion_rate": completion_rate
            },
            "quality_metrics": {
                "total_errors_fixed": total_errors_fixed,
                "average_errors_per_task": total_errors_fixed / len(completed_results) if completed_results else 0
            },
            "cost_metrics": {
                "total_cost": total_cost,
                "average_cost_per_task": total_cost / len(completed_results) if completed_results else 0
            },
            "recent_activity": completed_results[:5]  # 最近の5件
        }

        return report

    def print_status(self) -> None:
        """現在のステータス表示"""
        pending_tasks = self.list_pending_tasks()
        completed_results = self.get_completed_results()
        report = self.generate_progress_report()

        print("\n🤖 Claude ↔ Gemini Dual-Agent Workflow Status")
        print("=" * 60)
        print(f"📋 未完了タスク: {len(pending_tasks)}件")
        print(f"✅ 完了タスク: {len(completed_results)}件")
        print(f"📊 完了率: {report['task_summary']['completion_rate']:.1%}")
        print(f"🐛 修正エラー数: {report['quality_metrics']['total_errors_fixed']}件")
        print(f"💰 総コスト: ${report['cost_metrics']['total_cost']:.4f}")

        if pending_tasks:
            print("\n📋 次のタスク:")
            for task in pending_tasks[:3]:
                print(f"  • {task['task_id']}: {task['description'][:50]}...")

        print("\n" + "=" * 60)

def main():
    """メイン実行"""
    import sys

    tm = TaskManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            tm.print_status()
        elif command == "list":
            tasks = tm.list_pending_tasks()
            for task in tasks:
                print(f"{task['task_id']}: {task['description']}")
        elif command == "report":
            report = tm.generate_progress_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"Unknown command: {command}")
    else:
        tm.print_status()

if __name__ == "__main__":
    main()
