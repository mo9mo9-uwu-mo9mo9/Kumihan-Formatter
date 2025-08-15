#!/usr/bin/env python3
"""
統合ワークフローデータベース - 既存システム統合

既存のGemini協業システムとの統合・移行機能
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from workflow_database import (
    WorkflowDatabase, WorkflowAnalytics,
    ProjectInfo, OrchestrationLog, FailurePattern
)


class WorkflowIntegrator:
    """既存システム統合クラス"""

    def __init__(self, db_path: str = "tmp/workflow_logs.db"):
        self.db = WorkflowDatabase(db_path)
        self.analytics = WorkflowAnalytics(self.db)

    def migrate_orchestration_logs(self, log_file_path: str, project_name: str) -> int:
        """orchestration_log.jsonからの移行"""
        if not os.path.exists(log_file_path):
            print(f"⚠️ ログファイルが見つかりません: {log_file_path}")
            return 0

        print(f"🔄 {log_file_path} からデータを移行中...")

        # プロジェクト取得または作成
        project_id = self.db.get_or_create_project(project_name)

        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            migrated_count = 0

            # 様々なJSONフォーマットに対応
            if isinstance(data, list):
                # リスト形式
                for entry in data:
                    if self._migrate_single_entry(entry, project_id):
                        migrated_count += 1

            elif isinstance(data, dict):
                # 辞書形式
                if 'logs' in data:
                    # { "logs": [...] } 形式
                    for entry in data['logs']:
                        if self._migrate_single_entry(entry, project_id):
                            migrated_count += 1
                elif 'entries' in data:
                    # { "entries": [...] } 形式
                    for entry in data['entries']:
                        if self._migrate_single_entry(entry, project_id):
                            migrated_count += 1
                else:
                    # 単一エントリ形式
                    if self._migrate_single_entry(data, project_id):
                        migrated_count += 1

            print(f"✅ {migrated_count}件のログを移行しました")
            return migrated_count

        except Exception as e:
            print(f"❌ 移行中にエラーが発生しました: {e}")
            return 0

    def _migrate_single_entry(self, entry: Dict, project_id: int) -> bool:
        """単一エントリの移行"""
        try:
            # タイムスタンプ変換
            timestamp = None
            if 'timestamp' in entry:
                if isinstance(entry['timestamp'], str):
                    timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                elif isinstance(entry['timestamp'], (int, float)):
                    timestamp = datetime.fromtimestamp(entry['timestamp'])

            # OrchestrationLogオブジェクト作成
            log = OrchestrationLog(
                project_id=project_id,
                session_id=entry.get('session_id'),
                user_request=entry.get('user_request', entry.get('request', 'Migrated entry')),
                task_type=entry.get('task_type', entry.get('type')),
                complexity=entry.get('complexity'),
                automation_level=entry.get('automation_level'),
                status=entry.get('status', 'completed'),
                success=entry.get('success', entry.get('status') == 'completed'),
                execution_time_seconds=entry.get('execution_time_seconds', entry.get('execution_time')),
                claude_tokens_input=entry.get('claude_tokens_input', entry.get('claude_tokens', {}).get('input', 0)),
                claude_tokens_output=entry.get('claude_tokens_output', entry.get('claude_tokens', {}).get('output', 0)),
                gemini_tokens_input=entry.get('gemini_tokens_input', entry.get('gemini_tokens', {}).get('input', 0)),
                gemini_tokens_output=entry.get('gemini_tokens_output', entry.get('gemini_tokens', {}).get('output', 0)),
                claude_cost=entry.get('claude_cost', 0.0),
                gemini_cost=entry.get('gemini_cost', 0.0),
                total_cost=entry.get('total_cost', 0.0),
                cost_savings=entry.get('cost_savings', 0.0),
                executed_by=entry.get('executed_by', entry.get('executor')),
                timestamp=timestamp or datetime.now()
            )

            # データベースに記録
            self.db.log_orchestration(log)

            # 失敗エントリの場合、失敗パターンも記録
            if not log.success and 'error' in entry:
                failure = FailurePattern(
                    project_id=project_id,
                    task_description=log.user_request,
                    failure_type=entry.get('error', {}).get('type', 'UNKNOWN_ERROR'),
                    error_message=entry.get('error', {}).get('message', 'No error message'),
                    error_context=json.dumps(entry.get('error', {}), ensure_ascii=False),
                    recovery_action=entry.get('recovery_action'),
                    recovery_success=entry.get('recovery_success')
                )
                self.db.log_failure_pattern(failure)

            return True

        except Exception as e:
            print(f"⚠️ エントリ移行失敗: {e}")
            return False

    def scan_and_migrate_all_logs(self, base_dir: str = ".") -> Dict[str, int]:
        """指定ディレクトリから全ログファイルを検索・移行"""
        print(f"🔍 {base_dir} 配下のログファイルを検索中...")

        log_patterns = [
            "**/orchestration_log*.json",
            "**/workflow_log*.json",
            "**/gemini_log*.json",
            "**/collaboration_log*.json",
            "**/*_log*.json"
        ]

        results = {}
        base_path = Path(base_dir)

        for pattern in log_patterns:
            for log_file in base_path.glob(pattern):
                if log_file.is_file():
                    # プロジェクト名を推定
                    project_name = self._extract_project_name(log_file)

                    print(f"📄 発見: {log_file} (プロジェクト: {project_name})")

                    migrated_count = self.migrate_orchestration_logs(str(log_file), project_name)
                    results[str(log_file)] = migrated_count

        total_migrated = sum(results.values())
        print(f"\n✅ 移行完了: {len(results)}ファイル、{total_migrated}エントリ")

        return results

    def _extract_project_name(self, log_file: Path) -> str:
        """ログファイルパスからプロジェクト名を推定"""
        # パスから推定を試行
        parts = log_file.parts

        # よくあるプロジェクト名パターン
        project_indicators = [
            'kumihan-formatter', 'kumihan_formatter',
            'claude-gemini', 'workflow-engine',
            'project', 'src', 'app'
        ]

        for part in reversed(parts):
            if any(indicator in part.lower() for indicator in project_indicators):
                return part.lower()

        # ディレクトリ名から推定
        if len(parts) > 2:
            return parts[-2].lower()

        # デフォルト
        return "unknown-project"

    def create_project_config_template(self, project_name: str, output_path: str = None) -> str:
        """プロジェクト設定テンプレート作成"""
        if not output_path:
            output_path = f"tmp/{project_name}_config_template.py"

        template_content = f'''#!/usr/bin/env python3
"""
{project_name} プロジェクト設定

統合ワークフローデータベース用の設定定義
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json

@dataclass
class ProjectConfig:
    """プロジェクト設定"""
    name: str = "{project_name}"
    display_name: str = "{project_name.replace('-', ' ').title()}"
    base_path: str = "/path/to/{project_name}"

    # 技術スタック
    language: str = "Python"
    tech_stack: List[str] = None

    # 品質要件
    quality_requirements: Dict = None

    # Gemini協業設定
    gemini_collaboration: Dict = None

    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = ["Python 3.12+", "Black", "isort", "mypy"]

        if self.quality_requirements is None:
            self.quality_requirements = {{
                "mypy_strict": True,
                "black_format": True,
                "test_coverage": 80.0,
                "max_complexity": 10
            }}

        if self.gemini_collaboration is None:
            self.gemini_collaboration = {{
                "enabled": True,
                "auto_switch_threshold": 1000,  # Token数
                "preferred_tasks": ["formatting", "type_annotation", "testing"],
                "quality_check_level": "STRICT"
            }}

    def to_json(self) -> str:
        """JSON形式で出力"""
        return json.dumps({{
            "name": self.name,
            "display_name": self.display_name,
            "base_path": self.base_path,
            "language": self.language,
            "tech_stack": self.tech_stack,
            "quality_requirements": self.quality_requirements,
            "gemini_collaboration": self.gemini_collaboration
        }}, ensure_ascii=False, indent=2)


# 使用例
if __name__ == "__main__":
    config = ProjectConfig()
    print("プロジェクト設定:")
    print(config.to_json())
'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        print(f"✅ プロジェクト設定テンプレート作成: {output_path}")
        return output_path

    def integrate_with_orchestrator(self, orchestrator_config: Dict) -> Dict:
        """workflow_orchestrator_generic.py との統合設定"""
        integration_config = {
            "database": {
                "enabled": True,
                "db_path": self.db.db_path,
                "auto_log": True,
                "log_quality_checks": True
            },
            "analytics": {
                "enabled": True,
                "real_time_monitoring": True,
                "alert_thresholds": {
                    "success_rate_drop": 0.2,  # 20%低下でアラート
                    "cost_spike": 1.5,  # 50%増加でアラート
                    "failure_rate_increase": 0.1  # 10%増加でアラート
                }
            },
            "automation": {
                "auto_suggestions": True,
                "apply_suggestions": False,  # 手動承認必須
                "suggestion_confidence_threshold": 0.8
            }
        }

        # 既存設定とマージ
        merged_config = {**orchestrator_config, **integration_config}

        return merged_config

    def generate_migration_report(self, project_name: str) -> Dict:
        """移行レポート生成"""
        project = self.db.get_project_by_name(project_name)
        if not project:
            return {"error": f"Project '{project_name}' not found"}

        stats = self.db.get_project_stats(project_name, days=365)  # 1年分

        report = {
            "project_name": project_name,
            "migration_timestamp": datetime.now().isoformat(),
            "database_path": self.db.db_path,
            "statistics": stats,
            "data_coverage": {
                "total_logs": stats['total_executions'],
                "oldest_entry": None,
                "newest_entry": None,
                "data_quality": "Good" if stats['total_executions'] > 0 else "No data"
            },
            "recommendations": []
        }

        # データ範囲確認
        with self.db._get_connection() as conn:
            date_range = conn.execute("""
                SELECT
                    MIN(timestamp) as oldest,
                    MAX(timestamp) as newest
                FROM orchestration_logs
                WHERE project_id = ?
            """, (project.id,)).fetchone()

            if date_range['oldest']:
                report["data_coverage"]["oldest_entry"] = date_range['oldest']
                report["data_coverage"]["newest_entry"] = date_range['newest']

        # 推奨事項
        if stats['total_executions'] < 10:
            report["recommendations"].append("データ量が少ないため、より多くのログ収集を推奨")

        if stats['success_rate'] < 0.8:
            report["recommendations"].append("成功率改善のための分析・対策を推奨")

        if stats['total_cost'] == 0:
            report["recommendations"].append("コスト情報の記録を開始することを推奨")

        return report


def run_integration_example():
    """統合例の実行"""
    print("🔗 既存システム統合デモ")
    print("="*50)

    integrator = WorkflowIntegrator("tmp/integration_demo.db")

    # 1. サンプルログファイル作成
    sample_log = {
        "logs": [
            {
                "timestamp": "2025-08-15T10:00:00",
                "user_request": "MyPy型注釈修正",
                "task_type": "type_annotation",
                "status": "completed",
                "success": True,
                "execution_time": 120,
                "claude_tokens": {"input": 500, "output": 200},
                "gemini_tokens": {"input": 1200, "output": 600},
                "total_cost": 0.008,
                "cost_savings": 0.032,
                "executed_by": "Hybrid"
            },
            {
                "timestamp": "2025-08-15T11:00:00",
                "user_request": "新機能実装",
                "task_type": "feature",
                "status": "failed",
                "success": False,
                "execution_time": 300,
                "claude_tokens": {"input": 2000, "output": 800},
                "total_cost": 0.024,
                "executed_by": "Claude",
                "error": {
                    "type": "SYNTAX_ERROR",
                    "message": "Invalid syntax in generated code"
                }
            }
        ]
    }

    sample_file = "tmp/sample_orchestration_log.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_log, f, ensure_ascii=False, indent=2)

    print(f"📄 サンプルログファイル作成: {sample_file}")

    # 2. ログファイル移行
    migrated_count = integrator.migrate_orchestration_logs(sample_file, "integration-test")
    print(f"📥 移行完了: {migrated_count}件")

    # 3. プロジェクト設定テンプレート作成
    config_file = integrator.create_project_config_template("integration-test")

    # 4. 移行レポート生成
    report = integrator.generate_migration_report("integration-test")

    print(f"\n📊 移行レポート:")
    print(f"  • プロジェクト: {report['project_name']}")
    print(f"  • 総ログ数: {report['statistics']['total_executions']}")
    print(f"  • 成功率: {report['statistics']['success_rate']:.1%}")
    print(f"  • データ品質: {report['data_coverage']['data_quality']}")

    if report['recommendations']:
        print(f"  • 推奨事項:")
        for rec in report['recommendations']:
            print(f"    - {rec}")

    # 5. レポート保存
    with open("tmp/integration_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ 統合デモ完了！")
    print(f"📁 生成ファイル:")
    print(f"  • {sample_file}")
    print(f"  • {config_file}")
    print(f"  • tmp/integration_report.json")


if __name__ == "__main__":
    run_integration_example()
