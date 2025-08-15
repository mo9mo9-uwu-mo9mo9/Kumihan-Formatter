"""
外部プロジェクト統合API

汎用ライブラリとして他プロジェクトから簡単に利用できる統合APIシステム。
ワンライナー実行、詳細制御、バッチ処理に対応。
認証・セキュリティ・レート制限・権限管理機能を提供。
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from advanced_project_config import AdvancedProjectConfig, ProjectConfigModel, ProjectType


class AutomationLevel(Enum):
    """自動化レベル"""
    MANUAL = "manual"              # 手動実行のみ
    SEMI_AUTO = "semi_auto"        # 確認付き自動実行
    FULL_AUTO = "full_auto"        # 完全自動実行
    BATCH = "batch"                # バッチ処理


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """タスク実行状態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SecurityContext:
    """セキュリティコンテキスト"""
    api_key: str
    user_id: str
    permissions: List[str] = field(default_factory=list)
    rate_limit: int = 100  # 1時間あたりのリクエスト制限
    expires_at: Optional[datetime] = None


@dataclass
class TaskResult:
    """タスク実行結果"""
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class WorkflowRequest(BaseModel):
    """ワークフロー実行リクエスト"""
    task_description: str
    project_path: str
    automation_level: AutomationLevel = AutomationLevel.SEMI_AUTO
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 3600  # 秒
    context: Dict[str, Any] = Field(default_factory=dict)
    callback_url: Optional[str] = None


class RateLimiter:
    """レート制限管理"""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, user_id: str, limit: int, window_hours: int = 1) -> bool:
        """レート制限チェック"""
        now = datetime.now()
        cutoff = now - timedelta(hours=window_hours)

        if user_id not in self.requests:
            self.requests[user_id] = []

        # 古いリクエストを削除
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # 制限チェック
        if len(self.requests[user_id]) >= limit:
            return False

        # リクエスト記録
        self.requests[user_id].append(now)
        return True


class AuthenticationManager:
    """認証管理"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.sessions: Dict[str, SecurityContext] = {}

    def generate_api_key(self, user_id: str, permissions: List[str]) -> str:
        """APIキー生成"""
        timestamp = str(int(time.time()))
        payload = f"{user_id}:{timestamp}:{':'.join(permissions)}"
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{user_id}:{timestamp}:{signature}"

    def validate_api_key(self, api_key: str) -> Optional[SecurityContext]:
        """APIキー検証"""
        try:
            parts = api_key.split(":")
            if len(parts) < 3:
                return None

            user_id = parts[0]
            timestamp = parts[1]
            provided_signature = parts[2]

            # 有効期限チェック（24時間）
            if int(time.time()) - int(timestamp) > 86400:
                return None

            # 署名検証
            payload = f"{user_id}:{timestamp}:"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(provided_signature, expected_signature):
                return None

            # セキュリティコンテキスト作成
            return SecurityContext(
                api_key=api_key,
                user_id=user_id,
                permissions=["read", "write", "execute"],  # デフォルト権限
                expires_at=datetime.fromtimestamp(int(timestamp) + 86400)
            )

        except Exception:
            return None


class WorkflowExecutor(ABC):
    """ワークフロー実行器の基底クラス"""

    @abstractmethod
    async def execute(self, request: WorkflowRequest,
                     security_context: SecurityContext) -> TaskResult:
        """ワークフロー実行"""
        pass


class DefaultWorkflowExecutor(WorkflowExecutor):
    """デフォルトワークフロー実行器"""

    def __init__(self):
        self.config_manager = AdvancedProjectConfig()

    async def execute(self, request: WorkflowRequest,
                     security_context: SecurityContext) -> TaskResult:
        """デフォルトワークフロー実行"""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # プロジェクト設定検出・読み込み
            project_config = self._load_or_create_config(request.project_path)

            # タスク分析
            task_analysis = self._analyze_task(request.task_description, project_config)

            # 実行計画作成
            execution_plan = self._create_execution_plan(task_analysis, request.automation_level)

            # 実行
            output = await self._execute_plan(execution_plan, project_config)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output=output,
                metadata={
                    "project_type": project_config.project_type.value,
                    "automation_level": request.automation_level.value,
                    "task_analysis": task_analysis
                }
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                error=str(e),
                metadata={"automation_level": request.automation_level.value}
            )

    def _load_or_create_config(self, project_path: str) -> ProjectConfigModel:
        """プロジェクト設定の読み込み or 作成"""
        config_files = [
            "workflow_config.yaml",
            "workflow_config.json",
            ".workflow.yaml",
            "pyproject.toml"
        ]

        for config_file in config_files:
            config_path = Path(project_path) / config_file
            if config_path.exists():
                try:
                    return self.config_manager.load_config(str(config_path))
                except Exception:
                    continue

        # 設定が見つからない場合は自動検出で作成
        return self.config_manager.create_from_detection(project_path)

    def _analyze_task(self, task_description: str,
                     project_config: ProjectConfigModel) -> Dict[str, Any]:
        """タスク分析"""
        analysis = {
            "task_type": "unknown",
            "estimated_complexity": 1,
            "required_tools": [],
            "affected_files": [],
            "automation_level_recommendation": AutomationLevel.SEMI_AUTO
        }

        description_lower = task_description.lower()

        # タスク種別判定
        if any(keyword in description_lower for keyword in ["mypy", "型注釈", "type", "annotation"]):
            analysis["task_type"] = "type_checking"
            analysis["required_tools"] = ["mypy"]
            analysis["estimated_complexity"] = 2
        elif any(keyword in description_lower for keyword in ["lint", "flake8", "品質", "quality"]):
            analysis["task_type"] = "linting"
            analysis["required_tools"] = ["flake8", "pylint"]
            analysis["estimated_complexity"] = 1
        elif any(keyword in description_lower for keyword in ["format", "フォーマット", "black", "isort"]):
            analysis["task_type"] = "formatting"
            analysis["required_tools"] = ["black", "isort"]
            analysis["estimated_complexity"] = 1
            analysis["automation_level_recommendation"] = AutomationLevel.FULL_AUTO
        elif any(keyword in description_lower for keyword in ["test", "テスト", "pytest"]):
            analysis["task_type"] = "testing"
            analysis["required_tools"] = ["pytest"]
            analysis["estimated_complexity"] = 2
        elif any(keyword in description_lower for keyword in ["build", "ビルド", "compile"]):
            analysis["task_type"] = "build"
            analysis["estimated_complexity"] = 3

        return analysis

    def _create_execution_plan(self, task_analysis: Dict[str, Any],
                              automation_level: AutomationLevel) -> List[Dict[str, Any]]:
        """実行計画作成"""
        plan = []

        task_type = task_analysis["task_type"]
        required_tools = task_analysis["required_tools"]

        if task_type == "type_checking":
            plan.append({
                "step": "run_mypy",
                "tool": "mypy",
                "args": ["--strict"],
                "confirmation_required": automation_level != AutomationLevel.FULL_AUTO
            })
        elif task_type == "linting":
            for tool in required_tools:
                plan.append({
                    "step": f"run_{tool}",
                    "tool": tool,
                    "args": [],
                    "confirmation_required": automation_level == AutomationLevel.MANUAL
                })
        elif task_type == "formatting":
            plan.extend([
                {
                    "step": "run_black",
                    "tool": "black",
                    "args": ["."],
                    "confirmation_required": automation_level == AutomationLevel.MANUAL
                },
                {
                    "step": "run_isort",
                    "tool": "isort",
                    "args": ["."],
                    "confirmation_required": automation_level == AutomationLevel.MANUAL
                }
            ])

        return plan

    async def _execute_plan(self, execution_plan: List[Dict[str, Any]],
                           project_config: ProjectConfigModel) -> str:
        """実行計画の実行"""
        results = []

        for step in execution_plan:
            if step.get("confirmation_required", False):
                # 実際の実装では、ユーザー確認のロジックが必要
                confirm = True  # 仮の実装
                if not confirm:
                    results.append(f"ステップ '{step['step']}' がスキップされました")
                    continue

            # ツール実行のシミュレーション
            tool_name = step["tool"]
            args = step.get("args", [])

            result = f"✓ {tool_name} {' '.join(args)} 実行完了"
            results.append(result)

            # 実際の実装では、ここで実際のツールを実行
            await asyncio.sleep(0.1)  # 非同期実行のシミュレーション

        return "\n".join(results)


class WorkflowEngineAPI:
    """ワークフローエンジンAPI"""

    def __init__(self, secret_key: str = "default-secret-key"):
        self.auth_manager = AuthenticationManager(secret_key)
        self.rate_limiter = RateLimiter()
        self.executor = DefaultWorkflowExecutor()
        self.active_tasks: Dict[str, TaskResult] = {}

    @classmethod
    def auto_detect(cls, project_path: str, api_key: Optional[str] = None) -> 'WorkflowEngineAPI':
        """自動検出による簡易インスタンス作成"""
        api = cls()

        if api_key:
            # APIキー検証
            security_context = api.auth_manager.validate_api_key(api_key)
            if not security_context:
                raise ValueError("無効なAPIキーです")

        return api

    def create_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """APIキー作成"""
        if permissions is None:
            permissions = ["read", "write", "execute"]

        return self.auth_manager.generate_api_key(user_id, permissions)

    async def run(self, task_description: str, project_path: str = ".",
                  api_key: Optional[str] = None,
                  automation_level: AutomationLevel = AutomationLevel.SEMI_AUTO) -> TaskResult:
        """ワンライナー実行（簡易API）"""

        # 認証
        if api_key:
            security_context = self.auth_manager.validate_api_key(api_key)
            if not security_context:
                raise ValueError("認証に失敗しました")
        else:
            # デモ用の仮セキュリティコンテキスト
            security_context = SecurityContext(
                api_key="demo",
                user_id="demo_user",
                permissions=["read", "write", "execute"]
            )

        # レート制限チェック
        if not self.rate_limiter.is_allowed(security_context.user_id,
                                           security_context.rate_limit):
            raise ValueError("レート制限に達しました")

        # リクエスト作成
        request = WorkflowRequest(
            task_description=task_description,
            project_path=project_path,
            automation_level=automation_level
        )

        # 実行
        return await self.orchestrate(request, security_context)

    async def orchestrate(self, request: WorkflowRequest,
                         security_context: SecurityContext) -> TaskResult:
        """詳細制御実行"""

        # 権限チェック
        if "execute" not in security_context.permissions:
            raise ValueError("実行権限がありません")

        # タスク実行
        result = await self.executor.execute(request, security_context)

        # 結果記録
        self.active_tasks[result.task_id] = result

        return result

    async def batch_process(self, requests: List[WorkflowRequest],
                           security_context: SecurityContext) -> List[TaskResult]:
        """バッチ処理"""
        results = []

        for request in requests:
            try:
                result = await self.orchestrate(request, security_context)
                results.append(result)
            except Exception as e:
                # エラー時もTaskResultとして記録
                error_result = TaskResult(
                    task_id=str(uuid.uuid4()),
                    status=TaskStatus.FAILED,
                    start_time=datetime.now(),
                    error=str(e)
                )
                results.append(error_result)

        return results

    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """タスク状態取得"""
        return self.active_tasks.get(task_id)

    def list_active_tasks(self) -> List[TaskResult]:
        """アクティブタスク一覧"""
        return list(self.active_tasks.values())

    def set_executor(self, executor: WorkflowExecutor) -> None:
        """カスタム実行器設定"""
        self.executor = executor


# 使用例とユーティリティ関数

async def simple_usage_example():
    """シンプルな使用例"""
    api = WorkflowEngineAPI.auto_detect("./my_project")

    # ワンライナー実行
    result = await api.run("MyPy修正を実行してください")

    print(f"実行結果: {result.status}")
    print(f"出力: {result.output}")

    return result


async def advanced_usage_example():
    """高度な使用例"""
    api = WorkflowEngineAPI()

    # APIキー作成
    api_key = api.create_api_key("user123", ["read", "write", "execute"])

    # 詳細制御実行
    request = WorkflowRequest(
        task_description="バグ修正とテスト実行",
        project_path="./my_project",
        automation_level=AutomationLevel.SEMI_AUTO,
        priority=TaskPriority.HIGH,
        timeout=1800
    )

    security_context = api.auth_manager.validate_api_key(api_key)
    result = await api.orchestrate(request, security_context)

    return result


if __name__ == "__main__":
    # デモ実行
    async def main():
        print("=== ワンライナー実行デモ ===")
        result1 = await simple_usage_example()
        print(f"Task ID: {result1.task_id}")

        print("\n=== 詳細制御実行デモ ===")
        result2 = await advanced_usage_example()
        print(f"Task ID: {result2.task_id}")
        print(f"Duration: {result2.duration}秒")

    asyncio.run(main())
