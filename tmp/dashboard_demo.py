"""
統合ログシステム ダッシュボード デモ・テストシステム
================================================

テストデータ生成・API/WebSocketテスト・自動起動スクリプトを提供
"""

import os
import sys
import subprocess
import time
import json
import asyncio
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import websockets

# ローカルインポート
from dashboard_config import get_config

# 設定読み込み
config = get_config("development")


# ==========================================
# テストデータ生成
# ==========================================

class TestDataGenerator:
    """テストデータ生成器"""

    def __init__(self):
        self.projects = self._generate_projects()
        self.task_types = ["implementation", "bugfix", "testing", "refactor", "documentation"]
        self.complexities = ["simple", "moderate", "complex"]
        self.error_types = [
            "timeout", "syntax_error", "memory_error", "network_error",
            "permission_error", "dependency_error", "validation_error"
        ]

    def _generate_projects(self) -> List[Dict]:
        """プロジェクトデータ生成"""
        return [
            {
                "id": "kumihan-formatter",
                "name": "Kumihan Formatter",
                "description": "メインフォーマッタープロジェクト",
                "settings": {"target_success_rate": 0.95, "max_tokens": 1000}
            },
            {
                "id": "test-automation",
                "name": "Test Automation",
                "description": "自動テストシステム",
                "settings": {"target_success_rate": 0.90, "max_tokens": 800}
            },
            {
                "id": "ci-cd-pipeline",
                "name": "CI/CD Pipeline",
                "description": "継続的インテグレーション・デプロイメント",
                "settings": {"target_success_rate": 0.98, "max_tokens": 600}
            },
            {
                "id": "monitoring-system",
                "name": "Monitoring System",
                "description": "システム監視・アラート",
                "settings": {"target_success_rate": 0.99, "max_tokens": 400}
            }
        ]

    def generate_orchestration_logs(self, count: int = 100, days: int = 30) -> List[Dict]:
        """オーケストレーションログ生成"""
        logs = []
        base_time = datetime.now() - timedelta(days=days)

        for i in range(count):
            # 時間分散（営業時間重視）
            day_offset = random.uniform(0, days)
            hour_offset = random.choices([8, 9, 10, 11, 13, 14, 15, 16, 17], weights=[1, 2, 3, 3, 2, 3, 3, 2, 1])[0]
            minute_offset = random.randint(0, 59)

            start_time = base_time + timedelta(
                days=day_offset,
                hours=hour_offset - base_time.hour,
                minutes=minute_offset - base_time.minute
            )

            # プロジェクト選択（重み付き）
            project = random.choices(
                self.projects,
                weights=[0.4, 0.3, 0.2, 0.1]  # メインプロジェクトを重視
            )[0]

            # タスク特性決定
            task_type = random.choice(self.task_types)
            complexity = random.choices(
                self.complexities,
                weights=[0.5, 0.3, 0.2]  # simple寄り
            )[0]

            # 成功率計算（プロジェクトと複雑度に依存）
            base_success_rate = project["settings"]["target_success_rate"]
            complexity_modifier = {"simple": 0.05, "moderate": 0, "complex": -0.1}
            success_rate = base_success_rate + complexity_modifier[complexity]

            # 時間帯による成功率調整（夜間は低下）
            if start_time.hour < 8 or start_time.hour > 18:
                success_rate -= 0.1

            success = random.random() < success_rate

            # Token使用量計算
            base_tokens = {"simple": 300, "moderate": 600, "complex": 1000}[complexity]
            gemini_tokens = int(random.gauss(base_tokens, base_tokens * 0.2))
            gemini_tokens = max(100, gemini_tokens)  # 最低100Token

            claude_tokens = int(gemini_tokens * random.uniform(0.05, 0.2))  # Geminiの5-20%

            # 実行時間計算
            base_duration = {"simple": 5, "moderate": 15, "complex": 30}[complexity]
            duration_minutes = int(random.gauss(base_duration, base_duration * 0.3))
            duration_minutes = max(1, duration_minutes)

            end_time = start_time + timedelta(minutes=duration_minutes)

            # エラーメッセージ生成
            error_message = None
            if not success:
                error_type = random.choice(self.error_types)
                error_details = [
                    "Connection timeout after 30 seconds",
                    "Syntax error in generated code",
                    "Memory limit exceeded",
                    "Network unreachable",
                    "Permission denied",
                    "Missing dependency",
                    "Validation failed"
                ]
                error_message = f"{error_type}: {random.choice(error_details)}"

            # メタデータ生成
            metadata = {
                "version": "1.0",
                "branch": random.choices(["main", "develop", "feature/*"], weights=[0.6, 0.3, 0.1])[0],
                "user": random.choice(["claude", "gemini", "auto"]),
                "environment": "development",
                "retry_count": random.randint(0, 3) if not success else 0,
                "prompt_tokens": gemini_tokens + claude_tokens,
                "completion_tokens": random.randint(50, 200) if success else 0
            }

            log = {
                "id": f"log_{i:06d}",
                "project_id": project["id"],
                "task_type": task_type,
                "complexity": complexity,
                "start_time": start_time,
                "end_time": end_time,
                "status": "completed" if success else "failed",
                "gemini_tokens": gemini_tokens,
                "claude_tokens": claude_tokens,
                "success": success,
                "error_message": error_message,
                "metadata": metadata,
                "created_at": start_time
            }

            logs.append(log)

        # 時系列でソート
        logs.sort(key=lambda x: x["start_time"])

        return logs

    def generate_failure_patterns(self, logs: List[Dict]) -> Dict:
        """失敗パターン分析データ生成"""
        failed_logs = [log for log in logs if not log["success"]]

        patterns = {}
        for log in failed_logs:
            if log["error_message"]:
                error_type = log["error_message"].split(":")[0]
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
            pattern["recent_occurrences"] = sorted(pattern["recent_occurrences"])[-10:]

        return {"patterns": patterns}

    def generate_suggestions(self, logs: List[Dict], projects: List[Dict]) -> Dict:
        """改善提案データ生成"""
        suggestions = []

        # プロジェクトごとの分析
        for project in projects:
            project_logs = [log for log in logs if log["project_id"] == project["id"]]

            if not project_logs:
                continue

            success_rate = sum(1 for log in project_logs if log["success"]) / len(project_logs)
            avg_tokens = sum(log["gemini_tokens"] + log["claude_tokens"] for log in project_logs) / len(project_logs)
            failed_count = sum(1 for log in project_logs if not log["success"])

            # 成功率低下アラート
            if success_rate < 0.85:
                suggestions.append({
                    "type": "success_rate",
                    "priority": "high" if success_rate < 0.7 else "medium",
                    "project_id": project["id"],
                    "message": f"プロジェクト {project['name']} の成功率が {success_rate:.1%} と目標を下回っています",
                    "action": "failure_analysis",
                    "impact": f"{failed_count}件の失敗",
                    "urgency": "high" if failed_count > 10 else "medium"
                })

            # Token使用量超過アラート
            max_tokens = project["settings"]["max_tokens"]
            if avg_tokens > max_tokens:
                suggestions.append({
                    "type": "token_usage",
                    "priority": "medium",
                    "project_id": project["id"],
                    "message": f"平均Token使用量が {avg_tokens:.0f} と上限({max_tokens})を超過しています",
                    "action": "optimize_prompts",
                    "impact": f"コスト超過率: {((avg_tokens - max_tokens) / max_tokens):.1%}",
                    "urgency": "medium"
                })

            # 実行時間異常アラート
            recent_logs = project_logs[-20:]  # 最新20件
            if recent_logs:
                avg_duration = sum((log["end_time"] - log["start_time"]).total_seconds() for log in recent_logs) / len(recent_logs)
                if avg_duration > 1800:  # 30分超過
                    suggestions.append({
                        "type": "performance",
                        "priority": "medium",
                        "project_id": project["id"],
                        "message": f"平均実行時間が {avg_duration/60:.1f} 分と長時間です",
                        "action": "performance_optimization",
                        "impact": f"処理時間: {avg_duration:.0f}秒",
                        "urgency": "low"
                    })

        # 全体的な改善提案
        total_logs = len(logs)
        if total_logs > 50:
            overall_success_rate = sum(1 for log in logs if log["success"]) / total_logs

            if overall_success_rate < 0.9:
                suggestions.append({
                    "type": "system_wide",
                    "priority": "high",
                    "project_id": None,
                    "message": f"システム全体の成功率が {overall_success_rate:.1%} と低下しています",
                    "action": "system_review",
                    "impact": f"{total_logs - sum(1 for log in logs if log['success'])}件の失敗",
                    "urgency": "high"
                })

        return {"suggestions": suggestions}

    def save_test_data(self, filepath: str):
        """テストデータをファイルに保存"""
        logs = self.generate_orchestration_logs(200, 45)

        test_data = {
            "projects": self.projects,
            "orchestration_logs": logs,
            "failure_patterns": self.generate_failure_patterns(logs),
            "suggestions": self.generate_suggestions(logs, self.projects),
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "total_logs": len(logs),
                "success_rate": sum(1 for log in logs if log["success"]) / len(logs),
                "total_tokens": sum(log["gemini_tokens"] + log["claude_tokens"] for log in logs),
                "date_range": {
                    "start": min(log["start_time"] for log in logs).isoformat(),
                    "end": max(log["start_time"] for log in logs).isoformat()
                }
            }
        }

        # JSON serializableに変換
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2, default=serialize_datetime)

        print(f"📊 テストデータ生成完了: {filepath}")
        print(f"   - プロジェクト数: {len(self.projects)}")
        print(f"   - ログ数: {len(logs)}")
        print(f"   - 成功率: {test_data['stats']['success_rate']:.1%}")
        print(f"   - 総Token数: {test_data['stats']['total_tokens']:,}")

        return test_data


# ==========================================
# API・WebSocketテスト
# ==========================================

class APITester:
    """API・WebSocketテスト"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()

    def login(self, username: str = "admin", password: str = "admin123") -> bool:
        """ログインテスト"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers["Authorization"] = f"Bearer {self.token}"
                print(f"✅ ログイン成功: {username}")
                return True
            else:
                print(f"❌ ログイン失敗: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ ログインエラー: {e}")
            return False

    def test_health_check(self) -> bool:
        """ヘルスチェックテスト"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ ヘルスチェック成功: {data['status']}")
                return True
            else:
                print(f"❌ ヘルスチェック失敗: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ ヘルスチェックエラー: {e}")
            return False

    def test_projects_api(self) -> bool:
        """プロジェクトAPI テスト"""
        try:
            # プロジェクト一覧取得
            response = self.session.get(f"{self.base_url}/api/projects", timeout=10)

            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                print(f"✅ プロジェクト一覧取得成功: {len(projects)}件")
                return True
            else:
                print(f"❌ プロジェクト一覧取得失敗: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ プロジェクトAPIエラー: {e}")
            return False

    def test_logs_api(self) -> bool:
        """ログAPI テスト"""
        try:
            # ログ一覧取得
            response = self.session.get(
                f"{self.base_url}/api/orchestration/logs",
                params={"limit": 10},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                print(f"✅ ログ一覧取得成功: {len(logs)}件")
                return True
            else:
                print(f"❌ ログ一覧取得失敗: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ ログAPIエラー: {e}")
            return False

    def test_analytics_api(self) -> bool:
        """分析API テスト"""
        try:
            # 失敗パターン取得
            response = self.session.get(f"{self.base_url}/api/failures/patterns", timeout=10)

            if response.status_code == 200:
                data = response.json()
                patterns = data.get("patterns", {})
                print(f"✅ 失敗パターン取得成功: {len(patterns)}パターン")

                # 改善提案取得
                response = self.session.get(f"{self.base_url}/api/suggestions", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    suggestions = data.get("suggestions", [])
                    print(f"✅ 改善提案取得成功: {len(suggestions)}件")
                    return True

            print(f"❌ 分析API失敗: {response.status_code}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 分析APIエラー: {e}")
            return False

    async def test_websocket(self) -> bool:
        """WebSocket テスト"""
        try:
            uri = f"ws://localhost:{config.api.port}/ws/realtime"

            async with websockets.connect(uri) as websocket:
                # Ping送信
                await websocket.send(json.dumps({"type": "ping"}))

                # レスポンス受信
                response = await websocket.recv()
                data = json.loads(response)

                if data.get("type") == "pong":
                    print("✅ WebSocket通信成功")
                    return True
                else:
                    print(f"❌ WebSocket応答エラー: {data}")
                    return False

        except Exception as e:
            print(f"❌ WebSocketエラー: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """全テスト実行"""
        print("🧪 API・WebSocketテスト開始")
        print("=" * 50)

        results = {}

        # ヘルスチェック
        results["health"] = self.test_health_check()

        # ログイン
        results["login"] = self.login()

        if results["login"]:
            # 認証が必要なAPIテスト
            results["projects"] = self.test_projects_api()
            results["logs"] = self.test_logs_api()
            results["analytics"] = self.test_analytics_api()
        else:
            results["projects"] = False
            results["logs"] = False
            results["analytics"] = False

        # WebSocketテスト（非同期）
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results["websocket"] = loop.run_until_complete(self.test_websocket())
            loop.close()
        except Exception as e:
            print(f"❌ WebSocketテストエラー: {e}")
            results["websocket"] = False

        print("=" * 50)
        print("📊 テスト結果:")
        for test_name, result in results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"   {test_name}: {status}")

        success_rate = sum(results.values()) / len(results)
        print(f"\n🎯 総合成功率: {success_rate:.1%}")

        return results


# ==========================================
# サーバー起動・管理
# ==========================================

class ServerManager:
    """サーバー起動・管理"""

    def __init__(self):
        self.api_process = None
        self.dashboard_process = None

    def start_api_server(self) -> bool:
        """APIサーバー起動"""
        try:
            print("🚀 APIサーバー起動中...")

            cmd = [
                sys.executable,
                "-m", "uvicorn",
                "tmp.workflow_api_server:app",
                "--host", config.api.host,
                "--port", str(config.api.port),
                "--reload" if config.api.debug else "--no-reload",
                "--log-level", config.api.log_level
            ]

            self.api_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 起動確認
            time.sleep(3)
            if self.api_process.poll() is None:
                print(f"✅ APIサーバー起動成功: {config.api.host}:{config.api.port}")
                return True
            else:
                print("❌ APIサーバー起動失敗")
                return False

        except Exception as e:
            print(f"❌ APIサーバー起動エラー: {e}")
            return False

    def start_dashboard(self) -> bool:
        """ダッシュボード起動"""
        try:
            print("🖥️ ダッシュボード起動中...")

            cmd = [
                sys.executable,
                "-m", "streamlit",
                "run",
                "tmp/workflow_dashboard.py",
                "--server.port", "8501",
                "--server.address", "localhost",
                "--server.headless", "true"
            ]

            self.dashboard_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 起動確認
            time.sleep(5)
            if self.dashboard_process.poll() is None:
                print("✅ ダッシュボード起動成功: http://localhost:8501")
                return True
            else:
                print("❌ ダッシュボード起動失敗")
                return False

        except Exception as e:
            print(f"❌ ダッシュボード起動エラー: {e}")
            return False

    def stop_servers(self):
        """サーバー停止"""
        print("🛑 サーバー停止中...")

        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
            print("✅ APIサーバー停止")

        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process.wait()
            print("✅ ダッシュボード停止")

    def start_all(self) -> bool:
        """全サーバー起動"""
        print("🌟 統合ダッシュボードシステム起動")
        print("=" * 50)

        # APIサーバー起動
        api_success = self.start_api_server()

        # ダッシュボード起動
        dashboard_success = self.start_dashboard()

        if api_success and dashboard_success:
            print("=" * 50)
            print("✨ 全システム起動完了!")
            print("📊 ダッシュボード: http://localhost:8501")
            print("🔗 API: http://localhost:8000")
            print("📚 API ドキュメント: http://localhost:8000/docs")
            print("=" * 50)
            return True
        else:
            self.stop_servers()
            return False


# ==========================================
# パフォーマンステスト
# ==========================================

class PerformanceTester:
    """パフォーマンステスト"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_api_response_time(self, endpoint: str, iterations: int = 10) -> Dict:
        """API応答時間テスト"""
        response_times = []

        for i in range(iterations):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
                end_time = time.time()

                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                else:
                    print(f"❌ エラーレスポンス: {response.status_code}")

            except Exception as e:
                print(f"❌ リクエストエラー: {e}")

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            return {
                "endpoint": endpoint,
                "iterations": len(response_times),
                "avg_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "success_rate": len(response_times) / iterations
            }
        else:
            return {
                "endpoint": endpoint,
                "iterations": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "success_rate": 0
            }

    def run_performance_tests(self) -> Dict:
        """パフォーマンステスト実行"""
        print("⚡ パフォーマンステスト開始")
        print("=" * 50)

        endpoints = [
            "/api/health",
            "/api/projects",
            "/api/orchestration/logs?limit=50",
            "/api/failures/patterns",
            "/api/suggestions"
        ]

        results = {}

        for endpoint in endpoints:
            print(f"🔄 テスト中: {endpoint}")
            result = self.test_api_response_time(endpoint, 5)
            results[endpoint] = result

            status = "✅" if result["success_rate"] > 0.8 else "❌"
            print(f"{status} 平均応答時間: {result['avg_response_time']:.3f}秒")

        print("=" * 50)
        print("📊 パフォーマンステスト結果:")

        for endpoint, result in results.items():
            print(f"\n🔗 {endpoint}")
            print(f"   成功率: {result['success_rate']:.1%}")
            print(f"   平均応答時間: {result['avg_response_time']:.3f}秒")
            print(f"   最小応答時間: {result['min_response_time']:.3f}秒")
            print(f"   最大応答時間: {result['max_response_time']:.3f}秒")

        return results


# ==========================================
# メイン実行
# ==========================================

def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="統合ログシステム ダッシュボード デモ・テスト")
    parser.add_argument("--mode", choices=["demo", "test", "data", "performance", "start"],
                       default="demo", help="実行モード")
    parser.add_argument("--data-file", default="tmp/test_data.json",
                       help="テストデータファイルパス")
    parser.add_argument("--no-server", action="store_true",
                       help="サーバー起動をスキップ")

    args = parser.parse_args()

    print("🚀 Kumihan Workflow Dashboard デモ・テストシステム")
    print("=" * 60)

    if args.mode == "data":
        # テストデータ生成のみ
        print("📊 テストデータ生成モード")
        generator = TestDataGenerator()
        generator.save_test_data(args.data_file)

    elif args.mode == "test":
        # APIテストのみ
        print("🧪 APIテストモード")
        tester = APITester()
        results = tester.run_all_tests()

        # 結果をファイルに保存
        test_results_file = "tmp/test_results.json"
        with open(test_results_file, "w") as f:
            json.dump({
                "test_results": results,
                "timestamp": datetime.now().isoformat(),
                "success_rate": sum(results.values()) / len(results)
            }, f, indent=2)
        print(f"\n📄 テスト結果保存: {test_results_file}")

    elif args.mode == "performance":
        # パフォーマンステストのみ
        print("⚡ パフォーマンステストモード")
        perf_tester = PerformanceTester()
        perf_results = perf_tester.run_performance_tests()

        # 結果をファイルに保存
        perf_results_file = "tmp/performance_results.json"
        with open(perf_results_file, "w") as f:
            json.dump({
                "performance_results": perf_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        print(f"\n📄 パフォーマンス結果保存: {perf_results_file}")

    elif args.mode == "start":
        # サーバー起動のみ
        print("🌟 サーバー起動モード")
        server_manager = ServerManager()

        try:
            if server_manager.start_all():
                print("\n⏳ システム実行中... (Ctrl+C で停止)")
                while True:
                    time.sleep(1)
            else:
                print("❌ システム起動失敗")
                return 1

        except KeyboardInterrupt:
            print("\n🛑 停止要求受信")
            server_manager.stop_servers()
            print("✅ システム停止完了")

    else:  # demo
        # フルデモモード
        print("🎭 フルデモモード")

        # 1. テストデータ生成
        print("\n📊 ステップ1: テストデータ生成")
        generator = TestDataGenerator()
        test_data = generator.save_test_data(args.data_file)

        if not args.no_server:
            # 2. サーバー起動
            print("\n🚀 ステップ2: サーバー起動")
            server_manager = ServerManager()

            if not server_manager.start_all():
                print("❌ サーバー起動失敗")
                return 1

            try:
                # 3. APIテスト
                print("\n🧪 ステップ3: APIテスト")
                time.sleep(5)  # サーバー安定化待機
                tester = APITester()
                test_results = tester.run_all_tests()

                # 4. パフォーマンステスト
                print("\n⚡ ステップ4: パフォーマンステスト")
                perf_tester = PerformanceTester()
                perf_results = perf_tester.run_performance_tests()

                # 5. 総合結果
                print("\n🎯 ステップ5: 総合結果")
                print("=" * 60)
                print("✨ デモシステム準備完了!")
                print(f"📊 テストデータ: {len(test_data['orchestration_logs'])}件のログ")
                print(f"🧪 APIテスト成功率: {sum(test_results.values()) / len(test_results):.1%}")
                print(f"⚡ API平均応答時間: {sum(r['avg_response_time'] for r in perf_results.values()) / len(perf_results):.3f}秒")
                print("\n🌐 アクセスURL:")
                print("   📊 ダッシュボード: http://localhost:8501")
                print("   🔗 API: http://localhost:8000")
                print("   📚 API ドキュメント: http://localhost:8000/docs")
                print("\n📝 ログイン情報:")
                print("   ユーザー名: admin")
                print("   パスワード: admin123")
                print("=" * 60)

                print("\n⏳ デモシステム実行中... (Ctrl+C で停止)")
                while True:
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 停止要求受信")
                server_manager.stop_servers()
                print("✅ デモシステム停止完了")

        else:
            print("ℹ️ サーバー起動はスキップされました (--no-server)")

    return 0


if __name__ == "__main__":
    exit(main())
