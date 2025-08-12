#!/usr/bin/env python3
"""
Execution Controller for Postbox System
依存関係ベース実行制御・並行実行・エラー時fallback制御
"""

import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import datetime


class ExecutionStatus(Enum):
    """実行ステータス"""
    PENDING = "pending"              # 実行待ち
    READY = "ready"                  # 実行可能
    RUNNING = "running"              # 実行中
    COMPLETED = "completed"          # 完了
    FAILED = "failed"                # 失敗
    SKIPPED = "skipped"              # スキップ
    BLOCKED = "blocked"              # ブロック中


@dataclass
class TaskExecution:
    """タスク実行情報"""
    task_id: str
    status: ExecutionStatus
    dependencies: List[str]          # 依存タスクID
    dependents: List[str]            # このタスクに依存するタスクID
    priority: int                    # 優先度（0が最高）
    estimated_time: int              # 推定実行時間（分）
    retry_count: int = 0             # リトライ回数
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionPlan:
    """実行計画"""
    total_tasks: int
    execution_batches: List[List[str]]  # バッチ実行順序
    parallel_groups: List[List[str]]    # 並行実行グループ
    critical_path: List[str]            # クリティカルパス
    estimated_total_time: int           # 総推定時間


class ExecutionController:
    """高度な実行制御システム"""

    def __init__(self, postbox_dir: str = "postbox"):
        self.postbox_dir = Path(postbox_dir)
        self.todo_dir = self.postbox_dir / "todo"
        self.completed_dir = self.postbox_dir / "completed"
        self.monitoring_dir = self.postbox_dir / "monitoring"
        
        # 実行管理
        self.task_executions: Dict[str, TaskExecution] = {}
        self.execution_lock = threading.Lock()
        self.max_concurrent_tasks = 3  # 最大並行実行数
        
        print("🎛️ ExecutionController 初期化完了")
        print(f"📊 最大並行実行数: {self.max_concurrent_tasks}")

    def create_execution_plan(self, task_ids: List[str]) -> ExecutionPlan:
        """依存関係を考慮した実行計画作成"""
        
        print(f"📋 実行計画作成開始: {len(task_ids)}タスク")
        
        # タスク情報収集
        task_info = self._gather_task_info(task_ids)
        
        # 依存関係分析
        dependencies = self._analyze_dependencies(task_info)
        
        # 実行可能性チェック
        self._validate_dependencies(dependencies)
        
        # バッチ実行順序計算
        execution_batches = self._calculate_execution_batches(dependencies)
        
        # 並行実行グループ識別
        parallel_groups = self._identify_parallel_groups(execution_batches, dependencies)
        
        # クリティカルパス計算
        critical_path = self._calculate_critical_path(dependencies, task_info)
        
        # 総実行時間推定
        total_time = self._estimate_total_execution_time(parallel_groups, task_info)
        
        plan = ExecutionPlan(
            total_tasks=len(task_ids),
            execution_batches=execution_batches,
            parallel_groups=parallel_groups,
            critical_path=critical_path,
            estimated_total_time=total_time
        )
        
        print(f"✅ 実行計画作成完了:")
        print(f"   バッチ数: {len(execution_batches)}")
        print(f"   並行グループ: {len(parallel_groups)}")
        print(f"   推定実行時間: {total_time}分")
        
        return plan

    def execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """実行計画に基づく並行実行"""
        
        print(f"🚀 実行計画開始: {execution_plan.total_tasks}タスク")
        
        start_time = datetime.datetime.now()
        execution_log = {
            "start_time": start_time.isoformat(),
            "plan": asdict(execution_plan),
            "execution_results": [],
            "errors": [],
            "performance_metrics": {}
        }
        
        try:
            # 並行実行グループを順次実行
            for group_idx, group in enumerate(execution_plan.parallel_groups):
                print(f"\n📦 実行グループ {group_idx + 1}/{len(execution_plan.parallel_groups)}")
                print(f"   並行タスク: {len(group)}個")
                
                group_results = self._execute_parallel_group(group)
                execution_log["execution_results"].extend(group_results)
                
                # エラーチェック
                failed_tasks = [r for r in group_results if r["status"] == "failed"]
                if failed_tasks:
                    print(f"⚠️ グループ内で{len(failed_tasks)}タスク失敗")
                    
                    # 失敗時の依存関係チェック
                    should_continue = self._handle_group_failures(failed_tasks, execution_plan)
                    if not should_continue:
                        print("❌ 重要タスク失敗により実行中断")
                        break
        
        except Exception as e:
            print(f"❌ 実行制御エラー: {e}")
            execution_log["errors"].append({
                "type": "execution_control_error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        finally:
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds() / 60  # 分
            
            execution_log["end_time"] = end_time.isoformat()
            execution_log["actual_execution_time"] = execution_time
            execution_log["performance_metrics"] = self._calculate_performance_metrics(
                execution_log["execution_results"], execution_time
            )
            
            # 実行ログ保存
            self._save_execution_log(execution_log)
            
            print(f"\n📊 実行完了:")
            print(f"   実行時間: {execution_time:.1f}分")
            print(f"   推定時間: {execution_plan.estimated_total_time}分")
            print(f"   効率性: {execution_plan.estimated_total_time/execution_time*100:.1f}%")
        
        return execution_log

    def _gather_task_info(self, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """タスク情報収集"""
        
        task_info = {}
        
        for task_id in task_ids:
            task_file = self.todo_dir / f"{task_id}.json"
            
            if not task_file.exists():
                print(f"⚠️ タスクファイルが見つかりません: {task_id}")
                continue
            
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)
                
                task_info[task_id] = {
                    "data": task_data,
                    "target_files": task_data.get("target_files", []),
                    "priority": task_data.get("priority", "medium"),
                    "task_type": task_data.get("type", "unknown"),
                    "estimated_time": self._estimate_task_time(task_data)
                }
                
            except Exception as e:
                print(f"⚠️ タスクデータ読み込みエラー {task_id}: {e}")
        
        return task_info

    def _analyze_dependencies(self, task_info: Dict[str, Dict[str, Any]]) -> Dict[str, TaskExecution]:
        """依存関係分析"""
        
        dependencies = {}
        
        # ファイルベース依存関係の分析
        file_to_tasks = {}  # ファイル -> タスクID のマッピング
        
        # 各タスクの対象ファイルを記録
        for task_id, info in task_info.items():
            target_files = info["target_files"]
            for file_path in target_files:
                if file_path not in file_to_tasks:
                    file_to_tasks[file_path] = []
                file_to_tasks[file_path].append(task_id)
        
        # 依存関係構築
        for task_id, info in task_info.items():
            target_files = info["target_files"]
            task_dependencies = []
            
            # 同一ファイルを操作する他のタスクとの依存関係
            for file_path in target_files:
                for other_task_id in file_to_tasks.get(file_path, []):
                    if other_task_id != task_id:
                        # より早いタスクに依存（FIFO順序）
                        if other_task_id < task_id:
                            task_dependencies.append(other_task_id)
            
            # TaskExecution オブジェクト作成
            priority_map = {"high": 0, "medium": 1, "low": 2}
            dependencies[task_id] = TaskExecution(
                task_id=task_id,
                status=ExecutionStatus.PENDING,
                dependencies=task_dependencies,
                dependents=[],  # 後で設定
                priority=priority_map.get(info["priority"], 1),
                estimated_time=info["estimated_time"]
            )
        
        # 逆依存関係設定
        for task_id, execution in dependencies.items():
            for dep_id in execution.dependencies:
                if dep_id in dependencies:
                    dependencies[dep_id].dependents.append(task_id)
        
        return dependencies

    def _validate_dependencies(self, dependencies: Dict[str, TaskExecution]) -> None:
        """依存関係の妥当性チェック"""
        
        # 循環依存チェック
        def has_cycle(task_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep_id in dependencies[task_id].dependencies:
                if dep_id not in dependencies:
                    continue
                if dep_id not in visited:
                    if has_cycle(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        visited = set()
        for task_id in dependencies:
            if task_id not in visited:
                if has_cycle(task_id, visited, set()):
                    raise ValueError(f"循環依存を検出: {task_id} 周辺")
        
        print("✅ 依存関係検証: 循環依存なし")

    def _calculate_execution_batches(self, dependencies: Dict[str, TaskExecution]) -> List[List[str]]:
        """依存関係を考慮したバッチ実行順序計算"""
        
        batches = []
        remaining = set(dependencies.keys())
        
        while remaining:
            # 現在のバッチで実行可能なタスクを特定
            current_batch = []
            
            for task_id in list(remaining):
                execution = dependencies[task_id]
                
                # 全ての依存タスクが完了している
                deps_completed = all(
                    dep_id not in remaining for dep_id in execution.dependencies
                )
                
                if deps_completed:
                    current_batch.append(task_id)
            
            if not current_batch:
                # デッドロック検出
                raise ValueError(f"依存関係デッドロック: 残りタスク {remaining}")
            
            # 優先度順でソート
            current_batch.sort(key=lambda tid: (
                dependencies[tid].priority,
                -dependencies[tid].estimated_time  # 時間が長いものを先に
            ))
            
            batches.append(current_batch)
            remaining.difference_update(current_batch)
        
        return batches

    def _identify_parallel_groups(self, execution_batches: List[List[str]], 
                                 dependencies: Dict[str, TaskExecution]) -> List[List[str]]:
        """並行実行グループ識別"""
        
        parallel_groups = []
        
        for batch in execution_batches:
            # バッチ内のタスクを並行実行グループに分割
            remaining_tasks = batch.copy()
            
            while remaining_tasks:
                parallel_group = []
                
                for task_id in remaining_tasks.copy():
                    # リソース競合チェック
                    if self._can_run_parallel(task_id, parallel_group, dependencies):
                        parallel_group.append(task_id)
                        remaining_tasks.remove(task_id)
                        
                        # 最大並行数に達したら次のグループへ
                        if len(parallel_group) >= self.max_concurrent_tasks:
                            break
                
                if parallel_group:
                    parallel_groups.append(parallel_group)
                else:
                    # 並行実行不可の場合は1つずつ
                    parallel_groups.append([remaining_tasks.pop(0)])
        
        return parallel_groups

    def _can_run_parallel(self, task_id: str, current_group: List[str], 
                         dependencies: Dict[str, TaskExecution]) -> bool:
        """並行実行可能性チェック"""
        
        if not current_group:
            return True
        
        task_execution = dependencies[task_id]
        task_files = set()
        
        # 現在のタスクのファイルリストを取得（簡易版）
        for other_id in current_group:
            other_execution = dependencies[other_id]
            # ファイル競合チェック（実装省略）
            # 実際の実装では task_data から target_files を取得
        
        return True  # 簡易版では常に並行実行可能とする

    def _calculate_critical_path(self, dependencies: Dict[str, TaskExecution],
                                task_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """クリティカルパス計算"""
        
        # 各ノードの最早開始時間を計算
        earliest_start = {}
        
        def calculate_earliest_start(task_id: str) -> int:
            if task_id in earliest_start:
                return earliest_start[task_id]
            
            if not dependencies[task_id].dependencies:
                earliest_start[task_id] = 0
            else:
                max_predecessor_finish = max(
                    calculate_earliest_start(dep_id) + dependencies[dep_id].estimated_time
                    for dep_id in dependencies[task_id].dependencies
                    if dep_id in dependencies
                )
                earliest_start[task_id] = max_predecessor_finish
            
            return earliest_start[task_id]
        
        # 全タスクの最早開始時間を計算
        for task_id in dependencies:
            calculate_earliest_start(task_id)
        
        # 最終時間が最大のタスクからバックトラック
        finish_times = {
            task_id: earliest_start[task_id] + execution.estimated_time
            for task_id, execution in dependencies.items()
        }
        
        end_task = max(finish_times.keys(), key=lambda t: finish_times[t])
        
        # クリティカルパス構築
        critical_path = []
        current = end_task
        
        while current:
            critical_path.append(current)
            
            # 最も遅い依存タスクを選択
            if dependencies[current].dependencies:
                current = max(
                    dependencies[current].dependencies,
                    key=lambda dep: finish_times.get(dep, 0)
                )
            else:
                current = None
        
        return list(reversed(critical_path))

    def _estimate_total_execution_time(self, parallel_groups: List[List[str]], 
                                     task_info: Dict[str, Dict[str, Any]]) -> int:
        """総実行時間推定"""
        
        total_time = 0
        
        for group in parallel_groups:
            # グループ内の最大実行時間
            group_time = max(
                task_info[task_id]["estimated_time"]
                for task_id in group
                if task_id in task_info
            ) if group else 0
            
            total_time += group_time
        
        return total_time

    def _execute_parallel_group(self, task_group: List[str]) -> List[Dict[str, Any]]:
        """並行実行グループの実行"""
        
        print(f"🔄 並行実行開始: {len(task_group)}タスク")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=min(len(task_group), self.max_concurrent_tasks)) as executor:
            # タスク実行をスレッドプールに投入
            future_to_task = {
                executor.submit(self._execute_single_task, task_id): task_id
                for task_id in task_group
            }
            
            # 完了を待機
            for future in as_completed(future_to_task):
                task_id = future_to_task[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "completed":
                        print(f"✅ {task_id}: 完了")
                    else:
                        print(f"❌ {task_id}: {result['status']}")
                
                except Exception as e:
                    print(f"💥 {task_id}: 例外発生 - {e}")
                    results.append({
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    })
        
        print(f"📊 グループ実行完了: 成功{len([r for r in results if r['status'] == 'completed'])}/{len(results)}")
        
        return results

    def _execute_single_task(self, task_id: str) -> Dict[str, Any]:
        """単一タスクの実行"""
        
        start_time = datetime.datetime.now()
        
        try:
            # GeminiHelperインポート（循環インポート回避のため遅延）
            import sys
            sys.path.append(str(self.postbox_dir))
            from utils.gemini_helper import GeminiHelper
            
            helper = GeminiHelper()
            
            # タスクデータ取得
            task_file = self.todo_dir / f"{task_id}.json"
            if not task_file.exists():
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "タスクファイルが見つかりません",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # タスク実行
            result = helper.execute_task(task_data)
            
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "task_id": task_id,
                "status": result.get("status", "unknown"),
                "execution_time": execution_time,
                "result": result,
                "timestamp": end_time.isoformat()
            }
        
        except Exception as e:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "execution_time": (datetime.datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.datetime.now().isoformat()
            }

    def _handle_group_failures(self, failed_tasks: List[Dict[str, Any]], 
                              execution_plan: ExecutionPlan) -> bool:
        """グループ失敗時の処理"""
        
        failed_ids = [task["task_id"] for task in failed_tasks]
        
        # クリティカルパスのタスクが失敗した場合
        critical_failures = set(failed_ids) & set(execution_plan.critical_path)
        if critical_failures:
            print(f"🚨 クリティカルパス失敗: {critical_failures}")
            return False  # 実行中断
        
        print(f"⚠️ 非クリティカルタスク失敗: {failed_ids}")
        return True  # 実行継続

    def _estimate_task_time(self, task_data: Dict[str, Any]) -> int:
        """タスク実行時間推定"""
        
        # 基本時間（タスクタイプ別）
        base_times = {
            "code_modification": 10,
            "new_implementation": 30,
            "hybrid_implementation": 45,
            "new_feature_development": 60,
            "micro_code_modification": 5
        }
        
        task_type = task_data.get("type", "code_modification")
        base_time = base_times.get(task_type, 15)
        
        # ファイル数による調整
        target_files = task_data.get("target_files", [])
        file_factor = len(target_files) * 0.3
        
        return int(base_time * (1 + file_factor))

    def _calculate_performance_metrics(self, execution_results: List[Dict[str, Any]], 
                                     actual_time: float) -> Dict[str, Any]:
        """パフォーマンスメトリクス計算"""
        
        successful_tasks = [r for r in execution_results if r["status"] == "completed"]
        failed_tasks = [r for r in execution_results if r["status"] == "failed"]
        
        avg_execution_time = (
            sum(r.get("execution_time", 0) for r in execution_results) / 
            len(execution_results) if execution_results else 0
        )
        
        return {
            "total_tasks": len(execution_results),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(execution_results) if execution_results else 0,
            "average_task_time": avg_execution_time,
            "total_execution_time": actual_time,
            "throughput": len(execution_results) / actual_time if actual_time > 0 else 0
        }

    def _save_execution_log(self, execution_log: Dict[str, Any]) -> None:
        """実行ログ保存"""
        
        log_file = self.monitoring_dir / f"execution_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(execution_log, f, indent=2, ensure_ascii=False)
        
        print(f"📝 実行ログ保存: {log_file}")


def main():
    """テスト実行"""
    controller = ExecutionController()
    
    # テスト用タスクID
    test_task_ids = [
        "task_20250812_201916",
        "task_20250812_201920", 
        "task_20250812_201924"
    ]
    
    try:
        # 実行計画作成
        plan = controller.create_execution_plan(test_task_ids)
        
        print("\n📋 実行計画:")
        print(f"   総タスク数: {plan.total_tasks}")
        print(f"   推定実行時間: {plan.estimated_total_time}分")
        print(f"   並行グループ数: {len(plan.parallel_groups)}")
        
        # 実行実行（テスト時は実際の実行をスキップ）
        print("\n🚀 実行テスト（実際の実行はスキップ）")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")


if __name__ == "__main__":
    main()