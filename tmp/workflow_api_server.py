"""
統合ログシステム FastAPI サーバー
===============================

REST API・WebSocket・認証・セキュリティを提供する統合APIサーバー
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import secrets
import hashlib
import jwt
from pathlib import Path

# FastAPI関連
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
import uvicorn

# ローカルインポート
from dashboard_config import get_config, get_alert_config, get_metrics_config

# 設定読み込み
config = get_config()
alert_config = get_alert_config()
metrics_config = get_metrics_config()

# セキュリティ
security = HTTPBearer()

# アプリケーション初期化
app = FastAPI(
    title="Kumihan Workflow API",
    description="統合ログシステム API サーバー",
    version="1.0.0",
    docs_url=config.api.docs_url if config.api.enable_docs else None,
    redoc_url=config.api.redoc_url if config.api.enable_docs else None
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 信頼できるホスト設定
if config.api.host != "0.0.0.0":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[config.api.host, "localhost", "127.0.0.1"]
    )


# ==========================================
# データモデル
# ==========================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    role: str = Field(default="user")


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrchestrationLog(BaseModel):
    project_id: str
    task_type: str
    complexity: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    gemini_tokens: int = 0
    claude_tokens: int = 0
    success: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertRule(BaseModel):
    name: str
    condition: str
    threshold: float
    enabled: bool = True
    notification_channels: List[str] = []


class MetricsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    project_ids: Optional[List[str]] = None
    interval: str = "1h"


# ==========================================
# データストレージ（簡易実装）
# ==========================================

class InMemoryDatabase:
    """インメモリデータベース（デモ用）"""

    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.projects: Dict[str, Dict] = {}
        self.orchestration_logs: List[Dict] = []
        self.alert_rules: Dict[str, Dict] = {}
        self.api_keys: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self._init_sample_data()

    def _init_sample_data(self):
        """サンプルデータ初期化"""
        # デフォルトユーザー
        self.users["admin"] = {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": self._hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.now()
        }

        # サンプルプロジェクト
        self.projects["kumihan-formatter"] = {
            "id": "kumihan-formatter",
            "name": "Kumihan Formatter",
            "description": "メインプロジェクト",
            "settings": {"target_success_rate": 0.95},
            "created_at": datetime.now()
        }

        # サンプルログ
        base_time = datetime.now() - timedelta(hours=24)
        for i in range(20):
            log_time = base_time + timedelta(hours=i * 1.2)
            self.orchestration_logs.append({
                "id": f"log_{i}",
                "project_id": "kumihan-formatter",
                "task_type": "implementation",
                "complexity": "moderate",
                "start_time": log_time,
                "end_time": log_time + timedelta(minutes=15),
                "status": "completed" if i % 5 != 0 else "failed",
                "gemini_tokens": 500 + i * 10,
                "claude_tokens": 50 + i * 2,
                "success": i % 5 != 0,
                "error_message": "テストエラー" if i % 5 == 0 else None,
                "metadata": {"version": "1.0", "branch": "main"}
            })

    def _hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """パスワード検証"""
        return self._hash_password(password) == password_hash


# データベースインスタンス
db = InMemoryDatabase()


# ==========================================
# 認証・セキュリティ
# ==========================================

def create_access_token(data: dict) -> str:
    """アクセストークン作成"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=config.security.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.security.secret_key, algorithm=config.security.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """リフレッシュトークン作成"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=config.security.refresh_token_expire_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.security.secret_key, algorithm=config.security.jwt_algorithm)


def verify_token(token: str) -> Dict[str, Any]:
    """トークン検証"""
    try:
        payload = jwt.decode(token, config.security.secret_key, algorithms=[config.security.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンが期限切れです"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """現在のユーザー取得"""
    payload = verify_token(credentials.credentials)
    username = payload.get("sub")

    if username is None or username not in db.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません"
        )

    return db.users[username]


def require_role(required_role: str):
    """ロール要求デコレータ"""
    def decorator(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role != "admin" and user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="権限が不足しています"
            )
        return current_user
    return decorator


# ==========================================
# WebSocket管理
# ==========================================

class WebSocketManager:
    """WebSocket接続管理"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        """接続受け入れ"""
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """接続切断"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_message(self, message: dict, websocket: WebSocket):
        """メッセージ送信"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """全接続にブロードキャスト"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)

        # 切断された接続を削除
        for connection in disconnected:
            self.active_connections.remove(connection)

    async def send_to_user(self, user_id: str, message: dict):
        """特定ユーザーに送信"""
        if user_id in self.user_connections:
            await self.send_message(message, self.user_connections[user_id])


websocket_manager = WebSocketManager()


# ==========================================
# API エンドポイント
# ==========================================

@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "environment": config.environment
    }


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """ログイン"""
    user = db.users.get(user_data.username)

    if not user or not db.verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが間違っています"
        )

    # トークン生成
    token_data = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.security.access_token_expire_minutes * 60
    )


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """トークンリフレッシュ"""
    payload = verify_token(refresh_token)
    username = payload.get("sub")

    if username not in db.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません"
        )

    user = db.users[username]
    token_data = {"sub": user["username"], "role": user["role"]}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=config.security.access_token_expire_minutes * 60
    )


@app.get("/api/projects")
async def get_projects(current_user: Dict = Depends(get_current_user)):
    """プロジェクト一覧取得"""
    projects = list(db.projects.values())

    # プロジェクトごとの統計を追加
    for project in projects:
        project_logs = [log for log in db.orchestration_logs if log["project_id"] == project["id"]]
        project["stats"] = {
            "total_executions": len(project_logs),
            "success_rate": sum(1 for log in project_logs if log["success"]) / len(project_logs) if project_logs else 0,
            "total_tokens": sum(log["gemini_tokens"] + log["claude_tokens"] for log in project_logs),
            "last_execution": max((log["start_time"] for log in project_logs), default=None)
        }

    return {"projects": projects}


@app.post("/api/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: Dict = Depends(require_role("admin"))
):
    """プロジェクト作成"""
    project_id = project_data.name.lower().replace(" ", "-")

    if project_id in db.projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="プロジェクトが既に存在します"
        )

    project = {
        "id": project_id,
        "name": project_data.name,
        "description": project_data.description,
        "settings": project_data.settings or {},
        "created_at": datetime.now(),
        "created_by": current_user["username"]
    }

    db.projects[project_id] = project

    # WebSocket通知
    await websocket_manager.broadcast({
        "type": "project_created",
        "data": project
    })

    return {"project": project}


@app.get("/api/projects/{project_id}/analytics")
async def get_project_analytics(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """プロジェクト分析データ取得"""
    if project_id not in db.projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )

    project_logs = [log for log in db.orchestration_logs if log["project_id"] == project_id]

    # 基本統計
    total_executions = len(project_logs)
    successful_executions = sum(1 for log in project_logs if log["success"])
    success_rate = successful_executions / total_executions if total_executions > 0 else 0

    # トークン使用量
    total_gemini_tokens = sum(log["gemini_tokens"] for log in project_logs)
    total_claude_tokens = sum(log["claude_tokens"] for log in project_logs)
    token_savings = total_gemini_tokens / (total_gemini_tokens + total_claude_tokens) if (total_gemini_tokens + total_claude_tokens) > 0 else 0

    # 時系列データ
    daily_stats = {}
    for log in project_logs:
        date_key = log["start_time"].date().isoformat()
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                "executions": 0,
                "successes": 0,
                "gemini_tokens": 0,
                "claude_tokens": 0
            }

        daily_stats[date_key]["executions"] += 1
        if log["success"]:
            daily_stats[date_key]["successes"] += 1
        daily_stats[date_key]["gemini_tokens"] += log["gemini_tokens"]
        daily_stats[date_key]["claude_tokens"] += log["claude_tokens"]

    # 失敗パターン分析
    failure_logs = [log for log in project_logs if not log["success"]]
    failure_patterns = {}
    for log in failure_logs:
        error_type = log.get("error_message", "Unknown").split(":")[0]
        failure_patterns[error_type] = failure_patterns.get(error_type, 0) + 1

    return {
        "project_id": project_id,
        "summary": {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "token_savings": token_savings,
            "total_tokens": total_gemini_tokens + total_claude_tokens
        },
        "daily_stats": daily_stats,
        "failure_patterns": failure_patterns,
        "recent_logs": project_logs[-10:]  # 最新10件
    }


@app.post("/api/orchestration")
async def create_orchestration_log(
    log_data: OrchestrationLog,
    current_user: Dict = Depends(get_current_user)
):
    """オーケストレーションログ作成"""
    log_entry = {
        "id": f"log_{len(db.orchestration_logs)}",
        **log_data.dict(),
        "created_by": current_user["username"],
        "created_at": datetime.now()
    }

    db.orchestration_logs.append(log_entry)

    # リアルタイム通知
    await websocket_manager.broadcast({
        "type": "orchestration_completed",
        "data": log_entry
    })

    # アラートチェック
    await check_alerts(log_entry)

    return {"log": log_entry}


@app.get("/api/orchestration/logs")
async def get_orchestration_logs(
    project_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """オーケストレーションログ取得"""
    logs = db.orchestration_logs

    # プロジェクトフィルタ
    if project_id:
        logs = [log for log in logs if log["project_id"] == project_id]

    # ページネーション
    total = len(logs)
    logs = logs[offset:offset + limit]

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/failures/patterns")
async def get_failure_patterns(current_user: Dict = Depends(get_current_user)):
    """失敗パターン分析"""
    failure_logs = [log for log in db.orchestration_logs if not log["success"]]

    patterns = {}
    for log in failure_logs:
        error_type = log.get("error_message", "Unknown").split(":")[0]
        if error_type not in patterns:
            patterns[error_type] = {
                "count": 0,
                "projects": set(),
                "recent_occurrences": []
            }

        patterns[error_type]["count"] += 1
        patterns[error_type]["projects"].add(log["project_id"])
        patterns[error_type]["recent_occurrences"].append(log["start_time"])

    # セットをリストに変換
    for pattern in patterns.values():
        pattern["projects"] = list(pattern["projects"])
        pattern["recent_occurrences"] = sorted(pattern["recent_occurrences"])[-5:]  # 最新5件

    return {"patterns": patterns}


@app.get("/api/suggestions")
async def get_suggestions(current_user: Dict = Depends(get_current_user)):
    """改善提案取得"""
    suggestions = []

    # プロジェクトごとの統計を分析
    for project_id, project in db.projects.items():
        project_logs = [log for log in db.orchestration_logs if log["project_id"] == project_id]

        if not project_logs:
            continue

        success_rate = sum(1 for log in project_logs if log["success"]) / len(project_logs)
        avg_tokens = sum(log["gemini_tokens"] + log["claude_tokens"] for log in project_logs) / len(project_logs)

        # 成功率が低い場合
        if success_rate < 0.8:
            suggestions.append({
                "type": "success_rate",
                "priority": "high",
                "project_id": project_id,
                "message": f"プロジェクト {project['name']} の成功率が {success_rate:.1%} と低いです。エラーパターンを確認してください。",
                "action": "failure_analysis"
            })

        # トークン使用量が多い場合
        if avg_tokens > 800:
            suggestions.append({
                "type": "token_usage",
                "priority": "medium",
                "project_id": project_id,
                "message": f"プロジェクト {project['name']} の平均トークン使用量が {avg_tokens:.0f} と高いです。",
                "action": "optimize_prompts"
            })

    return {"suggestions": suggestions}


@app.get("/api/metrics")
async def get_metrics(
    query: MetricsQuery = Depends(),
    current_user: Dict = Depends(get_current_user)
):
    """メトリクス取得"""
    logs = db.orchestration_logs

    # 日付フィルタ
    if query.start_date:
        logs = [log for log in logs if log["start_time"] >= query.start_date]
    if query.end_date:
        logs = [log for log in logs if log["start_time"] <= query.end_date]

    # プロジェクトフィルタ
    if query.project_ids:
        logs = [log for log in logs if log["project_id"] in query.project_ids]

    # メトリクス計算
    total_executions = len(logs)
    successful_executions = sum(1 for log in logs if log["success"])
    success_rate = successful_executions / total_executions if total_executions > 0 else 0

    total_tokens = sum(log["gemini_tokens"] + log["claude_tokens"] for log in logs)
    gemini_tokens = sum(log["gemini_tokens"] for log in logs)
    token_savings = gemini_tokens / total_tokens if total_tokens > 0 else 0

    return {
        "period": {
            "start": query.start_date,
            "end": query.end_date,
            "interval": query.interval
        },
        "metrics": {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "token_savings": token_savings,
            "total_tokens": total_tokens,
            "avg_execution_time": sum(
                (log["end_time"] - log["start_time"]).total_seconds()
                for log in logs if log["end_time"]
            ) / len([log for log in logs if log["end_time"]]) if logs else 0
        }
    }


# ==========================================
# WebSocket エンドポイント
# ==========================================

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """リアルタイム通信WebSocket"""
    await websocket_manager.connect(websocket)

    try:
        while True:
            # クライアントからのメッセージ受信
            data = await websocket.receive_text()
            message = json.loads(data)

            # メッセージタイプに応じた処理
            if message.get("type") == "ping":
                await websocket_manager.send_message({"type": "pong"}, websocket)
            elif message.get("type") == "subscribe":
                # 購読処理（実装省略）
                pass

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


# ==========================================
# アラート・通知システム
# ==========================================

async def check_alerts(log_entry: Dict):
    """アラートチェック"""
    alerts = []

    # 失敗率チェック
    project_logs = [log for log in db.orchestration_logs if log["project_id"] == log_entry["project_id"]]
    recent_logs = project_logs[-10:]  # 最新10件
    if len(recent_logs) >= 5:
        failure_rate = sum(1 for log in recent_logs if not log["success"]) / len(recent_logs)
        if failure_rate > alert_config.failure_rate_threshold:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "high",
                "message": f"プロジェクト {log_entry['project_id']} の失敗率が {failure_rate:.1%} に達しました",
                "project_id": log_entry["project_id"]
            })

    # トークン使用量チェック
    total_tokens = log_entry["gemini_tokens"] + log_entry["claude_tokens"]
    if total_tokens > alert_config.cost_threshold:
        alerts.append({
            "type": "high_token_usage",
            "severity": "medium",
            "message": f"タスクのトークン使用量が {total_tokens} Tokenに達しました",
            "project_id": log_entry["project_id"]
        })

    # アラート送信
    for alert in alerts:
        await websocket_manager.broadcast({
            "type": "alert",
            "data": alert
        })


# ==========================================
# バックグラウンドタスク
# ==========================================

@app.on_event("startup")
async def startup_event():
    """起動時処理"""
    print(f"🚀 Kumihan Workflow API Server 起動")
    print(f"📊 環境: {config.environment}")
    print(f"🔧 API: {config.api.host}:{config.api.port}")
    print(f"🔒 セキュリティ: JWT認証有効")


@app.on_event("shutdown")
async def shutdown_event():
    """終了時処理"""
    print("🛑 Kumihan Workflow API Server 終了")


# ==========================================
# メイン実行
# ==========================================

if __name__ == "__main__":
    uvicorn.run(
        "workflow_api_server:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        log_level=config.api.log_level,
        workers=1 if config.api.debug else config.api.workers
    )
