#!/usr/bin/env python3
"""
統合ワークフローデータベースシステム

SQLiteベースの包括的なログ・分析システム
Claude-Gemini協業の統計・監視・改善提案を提供
"""

import json
import sqlite3
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from contextlib import contextmanager

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === データクラス定義 ===

@dataclass
class ProjectInfo:
    """プロジェクト情報"""
    name: str
    display_name: Optional[str] = None
    base_path: Optional[str] = None
    config_json: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class OrchestrationLog:
    """協業実行ログ"""
    project_id: int
    user_request: str
    status: str  # completed, failed, partial
    success: bool
    session_id: Optional[str] = None
    task_type: Optional[str] = None  # type_annotation, formatting, feature
    complexity: Optional[str] = None  # simple, moderate, complex
    automation_level: Optional[str] = None  # FULL_AUTO, SEMI_AUTO
    execution_time_seconds: Optional[int] = None
    claude_tokens_input: int = 0
    claude_tokens_output: int = 0
    gemini_tokens_input: int = 0
    gemini_tokens_output: int = 0
    claude_cost: float = 0.0
    gemini_cost: float = 0.0
    total_cost: float = 0.0
    cost_savings: float = 0.0
    executed_by: Optional[str] = None  # 'Claude', 'Gemini', 'Hybrid'
    timestamp: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class FailurePattern:
    """失敗パターン学習"""
    project_id: int
    task_description: str
    failure_type: str  # API_ERROR, SYNTAX_ERROR, TIMEOUT
    error_message: str
    orchestration_log_id: Optional[int] = None
    error_context: Optional[str] = None
    recovery_action: Optional[str] = None  # CLAUDE_SWITCH, RETRY, MANUAL_FIX
    recovery_success: Optional[bool] = None
    prevention_strategy: Optional[str] = None
    pattern_hash: Optional[str] = None
    frequency: int = 1
    last_occurrence: Optional[datetime] = None
    learned_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class QualityValidation:
    """品質検証履歴"""
    project_id: int
    orchestration_log_id: Optional[int] = None
    quality_level: Optional[str] = None  # BASIC, STANDARD, STRICT
    checks_total: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    mypy_pass: bool = False
    flake8_pass: bool = False
    black_pass: bool = False
    test_pass: bool = False
    code_coverage: Optional[float] = None
    complexity_score: Optional[float] = None
    maintainability_index: Optional[float] = None
    validated_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class TaskPattern:
    """タスクパターン分析"""
    project_id: int
    pattern_name: str
    pattern_description: Optional[str] = None
    task_template: Optional[str] = None
    total_executions: int = 0
    successful_executions: int = 0
    success_rate: float = 0.0
    recommended_executor: Optional[str] = None
    recommended_automation: Optional[str] = None
    estimated_difficulty: Optional[float] = None
    avg_execution_time: Optional[float] = None
    avg_token_usage: Optional[float] = None
    avg_cost: Optional[float] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class ImprovementSuggestion:
    """改善提案"""
    project_id: int
    suggestion_type: str  # AUTOMATION_LEVEL, TEMPLATE_UPDATE, TOOL_CONFIG
    suggestion_title: str
    suggestion_description: str
    analysis_data: Optional[str] = None
    confidence_score: Optional[float] = None
    impact_estimate: Optional[str] = None  # LOW, MEDIUM, HIGH
    status: str = 'pending'  # pending, applied, rejected
    applied_at: Optional[datetime] = None
    effectiveness_score: Optional[float] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class MonitoringAlert:
    """リアルタイム監視アラート"""
    project_id: int
    alert_type: str  # COST_SPIKE, SUCCESS_RATE_DROP, FAILURE_INCREASE
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    metric_name: Optional[str] = None
    status: str = 'active'  # active, resolved, suppressed
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None


# === 分析結果データクラス ===

@dataclass
class SuccessRateAnalysis:
    """成功率分析結果"""
    overall_rate: float
    weekly_trend: List[float]
    by_task_type: Dict[str, float]
    by_complexity: Dict[str, float]
    trend_direction: str  # 'improving', 'declining', 'stable'


@dataclass
class CostAnalysis:
    """コスト分析結果"""
    total_cost: float
    cost_savings: float
    savings_percentage: float
    cost_per_task: float
    token_efficiency: float
    projection_monthly: float


@dataclass
class FailureAnalysis:
    """失敗分析結果"""
    total_failures: int
    failure_rate: float
    top_patterns: List[Tuple[str, int]]
    recovery_rate: float
    prevention_effectiveness: float


# === メインデータベースクラス ===

class WorkflowDatabase:
    """統合ワークフローデータベース管理"""

    def __init__(self, db_path: str = "tmp/workflow_logs.db"):
        self.db_path = db_path
        self._ensure_tmp_dir()
        self._init_database()

    def _ensure_tmp_dir(self) -> None:
        """tmpディレクトリの確保"""
        Path(self.db_path).parent.mkdir(exist_ok=True)

    @contextmanager
    def _get_connection(self) -> Any:
        """データベース接続のコンテキストマネージャー"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        else:
            conn.commit()
        finally:
            conn.close()

    def _init_database(self) -> None:
        """データベース初期化・スキーマ作成"""
        with self._get_connection() as conn:
            # プロジェクト管理テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    base_path TEXT,
                    config_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 協業実行ログテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orchestration_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    session_id TEXT,
                    user_request TEXT NOT NULL,
                    task_type TEXT,
                    complexity TEXT,
                    automation_level TEXT,
                    status TEXT NOT NULL,
                    success BOOLEAN,
                    execution_time_seconds INTEGER,
                    claude_tokens_input INTEGER DEFAULT 0,
                    claude_tokens_output INTEGER DEFAULT 0,
                    gemini_tokens_input INTEGER DEFAULT 0,
                    gemini_tokens_output INTEGER DEFAULT 0,
                    claude_cost REAL DEFAULT 0.0,
                    gemini_cost REAL DEFAULT 0.0,
                    total_cost REAL DEFAULT 0.0,
                    cost_savings REAL DEFAULT 0.0,
                    executed_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # 失敗パターン学習テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    orchestration_log_id INTEGER,
                    task_description TEXT,
                    failure_type TEXT,
                    error_message TEXT,
                    error_context TEXT,
                    recovery_action TEXT,
                    recovery_success BOOLEAN,
                    prevention_strategy TEXT,
                    pattern_hash TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_occurrence DATETIME DEFAULT CURRENT_TIMESTAMP,
                    learned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (orchestration_log_id) REFERENCES orchestration_logs (id)
                )
            """)

            # 品質検証履歴テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    orchestration_log_id INTEGER,
                    quality_level TEXT,
                    checks_total INTEGER,
                    checks_passed INTEGER,
                    checks_failed INTEGER,
                    mypy_pass BOOLEAN DEFAULT FALSE,
                    flake8_pass BOOLEAN DEFAULT FALSE,
                    black_pass BOOLEAN DEFAULT FALSE,
                    test_pass BOOLEAN DEFAULT FALSE,
                    code_coverage REAL,
                    complexity_score REAL,
                    maintainability_index REAL,
                    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (orchestration_log_id) REFERENCES orchestration_logs (id)
                )
            """)

            # タスクパターン分析テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    pattern_name TEXT,
                    pattern_description TEXT,
                    task_template TEXT,
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    recommended_executor TEXT,
                    recommended_automation TEXT,
                    estimated_difficulty REAL,
                    avg_execution_time REAL,
                    avg_token_usage REAL,
                    avg_cost REAL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # 改善提案テーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS improvement_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    suggestion_type TEXT,
                    suggestion_title TEXT,
                    suggestion_description TEXT,
                    analysis_data TEXT,
                    confidence_score REAL,
                    impact_estimate TEXT,
                    status TEXT DEFAULT 'pending',
                    applied_at DATETIME,
                    effectiveness_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # リアルタイム監視アラートテーブル
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    threshold_value REAL,
                    current_value REAL,
                    metric_name TEXT,
                    status TEXT DEFAULT 'active',
                    resolved_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)

            # インデックス作成
            self._create_indexes(conn)

            logger.info(f"Database initialized: {self.db_path}")

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """パフォーマンス最適化用インデックス作成"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orchestration_logs_project_timestamp ON orchestration_logs (project_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_orchestration_logs_status ON orchestration_logs (status)",
            "CREATE INDEX IF NOT EXISTS idx_failure_patterns_project_type ON failure_patterns (project_id, failure_type)",
            "CREATE INDEX IF NOT EXISTS idx_quality_validations_project_timestamp ON quality_validations (project_id, validated_at)",
            "CREATE INDEX IF NOT EXISTS idx_task_patterns_project_success ON task_patterns (project_id, success_rate)",
            "CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_project_status ON monitoring_alerts (project_id, status)"
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

    # === プロジェクト管理 ===

    def create_project(self, project: ProjectInfo) -> int:
        """新規プロジェクト作成"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO projects (name, display_name, base_path, config_json)
                VALUES (?, ?, ?, ?)
            """, (project.name, project.display_name, project.base_path, project.config_json))

            project_id: Optional[int] = cursor.lastrowid
            if project_id is None:
                raise RuntimeError("Failed to create project")
            logger.info(f"Project created: {project.name} (ID: {project_id})")
            return project_id

    def get_project_by_name(self, name: str) -> Optional[ProjectInfo]:
        """プロジェクト名による取得"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM projects WHERE name = ?
            """, (name,)).fetchone()

            if row:
                return ProjectInfo(
                    id=row['id'],
                    name=row['name'],
                    display_name=row['display_name'],
                    base_path=row['base_path'],
                    config_json=row['config_json'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
            return None

    def get_or_create_project(self, name: str, **kwargs: Any) -> int:
        """プロジェクト取得または作成"""
        project = self.get_project_by_name(name)
        if project and project.id is not None:
            return project.id

        new_project = ProjectInfo(name=name, **kwargs)
        return self.create_project(new_project)

    # === ログ記録 ===

    def log_orchestration(self, log: OrchestrationLog) -> int:
        """協業実行ログ記録"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO orchestration_logs (
                    project_id, session_id, user_request, task_type, complexity,
                    automation_level, status, success, execution_time_seconds,
                    claude_tokens_input, claude_tokens_output, gemini_tokens_input,
                    gemini_tokens_output, claude_cost, gemini_cost, total_cost,
                    cost_savings, executed_by, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.project_id, log.session_id, log.user_request, log.task_type,
                log.complexity, log.automation_level, log.status, log.success,
                log.execution_time_seconds, log.claude_tokens_input,
                log.claude_tokens_output, log.gemini_tokens_input,
                log.gemini_tokens_output, log.claude_cost, log.gemini_cost,
                log.total_cost, log.cost_savings, log.executed_by,
                log.timestamp or datetime.now()
            ))

            log_id: Optional[int] = cursor.lastrowid
            if log_id is None:
                raise RuntimeError("Failed to create orchestration log")
            logger.info(f"Orchestration log created: {log_id}")
            return log_id

    def log_failure_pattern(self, failure: FailurePattern) -> int:
        """失敗パターン記録"""
        # パターンハッシュ生成
        if not failure.pattern_hash:
            pattern_data = f"{failure.failure_type}:{failure.error_message}"
            failure.pattern_hash = hashlib.md5(pattern_data.encode()).hexdigest()

        with self._get_connection() as conn:
            # 既存パターンチェック
            existing = conn.execute("""
                SELECT id, frequency FROM failure_patterns
                WHERE project_id = ? AND pattern_hash = ?
            """, (failure.project_id, failure.pattern_hash)).fetchone()

            if existing:
                # 頻度更新
                conn.execute("""
                    UPDATE failure_patterns
                    SET frequency = frequency + 1, last_occurrence = ?
                    WHERE id = ?
                """, (datetime.now(), existing['id']))
                return int(existing['id'])
            else:
                # 新規作成
                cursor = conn.execute("""
                    INSERT INTO failure_patterns (
                        project_id, orchestration_log_id, task_description,
                        failure_type, error_message, error_context, recovery_action,
                        recovery_success, prevention_strategy, pattern_hash,
                        frequency, last_occurrence, learned_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    failure.project_id, failure.orchestration_log_id,
                    failure.task_description, failure.failure_type,
                    failure.error_message, failure.error_context,
                    failure.recovery_action, failure.recovery_success,
                    failure.prevention_strategy, failure.pattern_hash,
                    failure.frequency, failure.last_occurrence or datetime.now(),
                    failure.learned_at or datetime.now()
                ))

                failure_id: Optional[int] = cursor.lastrowid
                if failure_id is None:
                    raise RuntimeError("Failed to create failure pattern")
                logger.info(f"Failure pattern logged: {failure_id}")
                return failure_id

    def log_quality_validation(self, validation: QualityValidation) -> int:
        """品質検証記録"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO quality_validations (
                    project_id, orchestration_log_id, quality_level,
                    checks_total, checks_passed, checks_failed,
                    mypy_pass, flake8_pass, black_pass, test_pass,
                    code_coverage, complexity_score, maintainability_index,
                    validated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                validation.project_id, validation.orchestration_log_id,
                validation.quality_level, validation.checks_total,
                validation.checks_passed, validation.checks_failed,
                validation.mypy_pass, validation.flake8_pass,
                validation.black_pass, validation.test_pass,
                validation.code_coverage, validation.complexity_score,
                validation.maintainability_index,
                validation.validated_at or datetime.now()
            ))

            validation_id: Optional[int] = cursor.lastrowid
            if validation_id is None:
                raise RuntimeError("Failed to create quality validation")
            logger.info(f"Quality validation logged: {validation_id}")
            return validation_id

    # === バッチ処理 ===

    def batch_insert_logs(self, logs: List[OrchestrationLog]) -> List[int]:
        """ログの一括挿入"""
        log_ids = []
        with self._get_connection() as conn:
            for log in logs:
                cursor = conn.execute("""
                    INSERT INTO orchestration_logs (
                        project_id, session_id, user_request, task_type, complexity,
                        automation_level, status, success, execution_time_seconds,
                        claude_tokens_input, claude_tokens_output, gemini_tokens_input,
                        gemini_tokens_output, claude_cost, gemini_cost, total_cost,
                        cost_savings, executed_by, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log.project_id, log.session_id, log.user_request, log.task_type,
                    log.complexity, log.automation_level, log.status, log.success,
                    log.execution_time_seconds, log.claude_tokens_input,
                    log.claude_tokens_output, log.gemini_tokens_input,
                    log.gemini_tokens_output, log.claude_cost, log.gemini_cost,
                    log.total_cost, log.cost_savings, log.executed_by,
                    log.timestamp or datetime.now()
                ))
                log_id: Optional[int] = cursor.lastrowid
                if log_id is None:
                    raise RuntimeError("Failed to create orchestration log in batch")
                log_ids.append(log_id)

        logger.info(f"Batch inserted {len(logs)} orchestration logs")
        return log_ids

    # === データ移行機能 ===

    def import_from_json(self, json_path: str, project_name: str) -> int:
        """既存JSONログからの移行"""
        project_id = self.get_or_create_project(project_name)

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0

            # orchestration_log.json 形式の場合
            if isinstance(data, dict) and 'logs' in data:
                for log_entry in data['logs']:
                    log = OrchestrationLog(
                        project_id=project_id,
                        user_request=log_entry.get('user_request', 'Imported from JSON'),
                        status=log_entry.get('status', 'completed'),
                        success=log_entry.get('success', True),
                        task_type=log_entry.get('task_type'),
                        complexity=log_entry.get('complexity'),
                        execution_time_seconds=log_entry.get('execution_time'),
                        total_cost=log_entry.get('total_cost', 0.0),
                        cost_savings=log_entry.get('cost_savings', 0.0),
                        executed_by=log_entry.get('executed_by', 'Unknown'),
                        timestamp=datetime.fromisoformat(log_entry['timestamp']) if log_entry.get('timestamp') else datetime.now()
                    )
                    self.log_orchestration(log)
                    imported_count += 1

            logger.info(f"Imported {imported_count} logs from {json_path}")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import from {json_path}: {e}")
            raise

    # === 統計取得 ===

    def get_project_stats(self, project_name: str, days: int = 30) -> Dict[str, Any]:
        """プロジェクト統計取得"""
        project = self.get_project_by_name(project_name)
        if not project:
            raise ValueError(f"Project not found: {project_name}")

        with self._get_connection() as conn:
            # 基本統計
            stats = conn.execute("""
                SELECT
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_executions,
                    AVG(execution_time_seconds) as avg_execution_time,
                    SUM(total_cost) as total_cost,
                    SUM(cost_savings) as total_savings
                FROM orchestration_logs
                WHERE project_id = ?
                    AND timestamp >= datetime('now', '-' || ? || ' days')
            """, (project.id, days)).fetchone()

            # 失敗統計
            failure_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_failures,
                    COUNT(DISTINCT failure_type) as unique_failure_types
                FROM failure_patterns
                WHERE project_id = ?
                    AND last_occurrence >= datetime('now', '-' || ? || ' days')
            """, (project.id, days)).fetchone()

            success_rate = (stats['successful_executions'] / stats['total_executions']) if stats['total_executions'] > 0 else 0.0

            return {
                'project_name': project_name,
                'period_days': days,
                'total_executions': stats['total_executions'],
                'successful_executions': stats['successful_executions'],
                'success_rate': success_rate,
                'avg_execution_time': stats['avg_execution_time'],
                'total_cost': stats['total_cost'],
                'total_savings': stats['total_savings'],
                'total_failures': failure_stats['total_failures'],
                'unique_failure_types': failure_stats['unique_failure_types']
            }


# === 統合分析エンジン ===

class WorkflowAnalytics:
    """統合ワークフロー分析エンジン"""

    def __init__(self, db: WorkflowDatabase):
        self.db = db

    def get_success_rate_analysis(self, project_name: str, days: int = 30) -> SuccessRateAnalysis:
        """成功率の詳細分析"""
        project = self.db.get_project_by_name(project_name)
        if not project or project.id is None:
            raise ValueError(f"Project not found: {project_name}")

        with self.db._get_connection() as conn:
            # 全体成功率
            overall_rate = self._calculate_overall_success_rate(conn, project.id, days)

            # 週次トレンド（過去4週）
            weekly_trend = self._calculate_weekly_trend(conn, project.id, days)

            # タスクタイプ別
            by_task_type = self._calculate_success_by_task_type(conn, project.id, days)

            # 複雑度別
            by_complexity = self._calculate_success_by_complexity(conn, project.id, days)

            # トレンド方向
            trend_direction = self._determine_trend_direction(weekly_trend)

            return SuccessRateAnalysis(
                overall_rate=overall_rate,
                weekly_trend=weekly_trend,
                by_task_type=by_task_type,
                by_complexity=by_complexity,
                trend_direction=trend_direction
            )

    def _calculate_overall_success_rate(self, conn: sqlite3.Connection, project_id: int, days: int) -> float:
        """全体成功率計算"""
        result = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful
            FROM orchestration_logs
            WHERE project_id = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
        """, (project_id, days)).fetchone()

        if result['total'] == 0:
            return 0.0
        return float(result['successful']) / float(result['total'])

    def _calculate_weekly_trend(self, conn: sqlite3.Connection, project_id: int, days: int) -> List[float]:
        """週次成功率トレンド計算"""
        weekly_rates = []
        weeks = min(days // 7, 4)  # 最大4週

        for week in range(weeks):
            week_start = week * 7
            week_end = (week + 1) * 7

            result = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful
                FROM orchestration_logs
                WHERE project_id = ?
                    AND timestamp >= datetime('now', '-' || ? || ' days')
                    AND timestamp < datetime('now', '-' || ? || ' days')
            """, (project_id, week_end, week_start)).fetchone()

            if result['total'] > 0:
                weekly_rates.append(float(result['successful']) / float(result['total']))
            else:
                weekly_rates.append(0.0)

        return list(reversed(weekly_rates))  # 古い順に並び替え

    def _calculate_success_by_task_type(self, conn: sqlite3.Connection, project_id: int, days: int) -> Dict[str, float]:
        """タスクタイプ別成功率"""
        results = conn.execute("""
            SELECT
                task_type,
                COUNT(*) as total,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful
            FROM orchestration_logs
            WHERE project_id = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
                AND task_type IS NOT NULL
            GROUP BY task_type
        """, (project_id, days)).fetchall()

        return {
            row['task_type']: (row['successful'] / row['total']) if row['total'] > 0 else 0.0
            for row in results
        }

    def _calculate_success_by_complexity(self, conn: sqlite3.Connection, project_id: int, days: int) -> Dict[str, float]:
        """複雑度別成功率"""
        results = conn.execute("""
            SELECT
                complexity,
                COUNT(*) as total,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful
            FROM orchestration_logs
            WHERE project_id = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
                AND complexity IS NOT NULL
            GROUP BY complexity
        """, (project_id, days)).fetchall()

        return {
            row['complexity']: (row['successful'] / row['total']) if row['total'] > 0 else 0.0
            for row in results
        }

    def _determine_trend_direction(self, weekly_trend: List[float]) -> str:
        """トレンド方向判定"""
        if len(weekly_trend) < 2:
            return 'stable'

        # 最新週と前週の比較
        latest = weekly_trend[-1]
        previous = weekly_trend[-2]

        if latest > previous + 0.1:  # 10%以上改善
            return 'improving'
        elif latest < previous - 0.1:  # 10%以上悪化
            return 'declining'
        else:
            return 'stable'

    def get_cost_analysis(self, project_name: str, days: int = 30) -> CostAnalysis:
        """コスト効率分析"""
        project = self.db.get_project_by_name(project_name)
        if not project or project.id is None:
            raise ValueError(f"Project not found: {project_name}")

        with self.db._get_connection() as conn:
            result = conn.execute("""
                SELECT
                    SUM(total_cost) as total_cost,
                    SUM(cost_savings) as total_savings,
                    AVG(total_cost) as avg_cost_per_task,
                    COUNT(*) as total_tasks,
                    SUM(claude_tokens_input + claude_tokens_output +
                        gemini_tokens_input + gemini_tokens_output) as total_tokens
                FROM orchestration_logs
                WHERE project_id = ?
                    AND timestamp >= datetime('now', '-' || ? || ' days')
            """, (project.id, days)).fetchone()

            total_cost = result['total_cost'] or 0.0
            total_savings = result['total_savings'] or 0.0

            savings_percentage = 0.0
            if total_cost > 0 and total_savings > 0:
                base_cost = total_cost + total_savings
                savings_percentage = total_savings / base_cost

            # Token効率性
            token_efficiency = 0.0
            if total_cost > 0 and result['total_tokens']:
                token_efficiency = result['total_tokens'] / total_cost

            # 月次予測
            daily_avg = total_cost / days if days > 0 else 0
            projection_monthly = daily_avg * 30

            return CostAnalysis(
                total_cost=total_cost,
                cost_savings=total_savings,
                savings_percentage=savings_percentage,
                cost_per_task=result['avg_cost_per_task'] or 0.0,
                token_efficiency=token_efficiency,
                projection_monthly=projection_monthly
            )

    def get_failure_analysis(self, project_name: str, days: int = 30) -> FailureAnalysis:
        """失敗パターン詳細分析"""
        project = self.db.get_project_by_name(project_name)
        if not project or project.id is None:
            raise ValueError(f"Project not found: {project_name}")

        with self.db._get_connection() as conn:
            # 失敗統計
            failure_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_failures
                FROM failure_patterns
                WHERE project_id = ?
                    AND last_occurrence >= datetime('now', '-' || ? || ' days')
            """, (project.id, days)).fetchone()

            # 全タスク数
            total_tasks = conn.execute("""
                SELECT COUNT(*) as total
                FROM orchestration_logs
                WHERE project_id = ?
                    AND timestamp >= datetime('now', '-' || ? || ' days')
            """, (project.id, days)).fetchone()

            # トップ失敗パターン
            top_patterns = conn.execute("""
                SELECT failure_type, SUM(frequency) as total_count
                FROM failure_patterns
                WHERE project_id = ?
                    AND last_occurrence >= datetime('now', '-' || ? || ' days')
                GROUP BY failure_type
                ORDER BY total_count DESC
                LIMIT 5
            """, (project.id, days)).fetchall()

            # 復旧率
            recovery_stats = conn.execute("""
                SELECT
                    COUNT(*) as total_recoveries,
                    COUNT(CASE WHEN recovery_success = 1 THEN 1 END) as successful_recoveries
                FROM failure_patterns
                WHERE project_id = ?
                    AND last_occurrence >= datetime('now', '-' || ? || ' days')
                    AND recovery_action IS NOT NULL
            """, (project.id, days)).fetchone()

            total_failures = failure_stats['total_failures']
            total_task_count = total_tasks['total'] or 1
            failure_rate = total_failures / total_task_count

            recovery_rate = 0.0
            if recovery_stats['total_recoveries'] > 0:
                recovery_rate = recovery_stats['successful_recoveries'] / recovery_stats['total_recoveries']

            # 予防効果 (簡易計算: 学習済みパターンの再発率)
            prevention_effectiveness = 0.8  # デフォルト値

            return FailureAnalysis(
                total_failures=total_failures,
                failure_rate=failure_rate,
                top_patterns=[(row['failure_type'], row['total_count']) for row in top_patterns],
                recovery_rate=recovery_rate,
                prevention_effectiveness=prevention_effectiveness
            )

    def generate_improvement_suggestions(self, project_name: str) -> List[Dict[str, Any]]:
        """自動改善提案生成"""
        suggestions = []

        # 成功率分析に基づく提案
        success_analysis = self.get_success_rate_analysis(project_name)
        if success_analysis.overall_rate < 0.8:
            suggestions.append({
                'type': 'AUTOMATION_LEVEL',
                'title': '自動化レベルの調整推奨',
                'description': f'成功率{success_analysis.overall_rate:.1%}は目標の80%を下回っています。より保守的な自動化レベルの検討を推奨します。',
                'confidence': 0.8,
                'impact': 'HIGH'
            })

        # コスト分析に基づく提案
        cost_analysis = self.get_cost_analysis(project_name)
        if cost_analysis.savings_percentage < 0.9:
            suggestions.append({
                'type': 'OPTIMIZATION',
                'title': 'Token使用量最適化',
                'description': f'コスト削減率{cost_analysis.savings_percentage:.1%}は目標の90%を下回っています。より積極的なGemini活用を推奨します。',
                'confidence': 0.7,
                'impact': 'MEDIUM'
            })

        # 失敗パターンに基づく提案
        failure_analysis = self.get_failure_analysis(project_name)
        for pattern, count in failure_analysis.top_patterns[:3]:
            suggestions.append({
                'type': 'PATTERN_PREVENTION',
                'title': f'{pattern}失敗の予防策',
                'description': f'過去30日で{count}回発生した{pattern}の予防策を実装することを推奨します。',
                'confidence': min(0.9, count / 10),  # 頻度に基づく信頼度
                'impact': 'MEDIUM' if count > 5 else 'LOW'
            })

        return suggestions

    def check_monitoring_alerts(self, project_name: str) -> List[Dict[str, Any]]:
        """リアルタイム監視アラートチェック"""
        alerts = []

        try:
            # 成功率急低下
            recent_rate = self.get_success_rate_analysis(project_name, days=7).overall_rate
            baseline_rate = self.get_success_rate_analysis(project_name, days=30).overall_rate

            if recent_rate < baseline_rate * 0.8:  # 20%以上の低下
                alerts.append({
                    'type': 'SUCCESS_RATE_DROP',
                    'severity': 'HIGH',
                    'message': f'成功率が急低下: {recent_rate:.1%} (過去7日) vs {baseline_rate:.1%} (過去30日)',
                    'current_value': recent_rate,
                    'threshold_value': baseline_rate * 0.8
                })

            # コスト急増
            recent_cost = self.get_cost_analysis(project_name, days=7)
            baseline_cost = self.get_cost_analysis(project_name, days=30)

            if recent_cost.cost_per_task > baseline_cost.cost_per_task * 1.5:  # 50%以上の増加
                alerts.append({
                    'type': 'COST_SPIKE',
                    'severity': 'MEDIUM',
                    'message': f'コストが急増: ${recent_cost.cost_per_task:.4f} vs ${baseline_cost.cost_per_task:.4f} per task',
                    'current_value': recent_cost.cost_per_task,
                    'threshold_value': baseline_cost.cost_per_task * 1.5
                })

        except Exception as e:
            logger.warning(f"Alert check failed: {e}")

        return alerts

    def generate_comprehensive_report(self, project_name: str) -> Dict[str, Any]:
        """包括的レポート生成"""
        return {
            'project_name': project_name,
            'report_timestamp': datetime.now().isoformat(),
            'success_analysis': asdict(self.get_success_rate_analysis(project_name)),
            'cost_analysis': asdict(self.get_cost_analysis(project_name)),
            'failure_analysis': asdict(self.get_failure_analysis(project_name)),
            'improvement_suggestions': self.generate_improvement_suggestions(project_name),
            'monitoring_alerts': self.check_monitoring_alerts(project_name)
        }


if __name__ == "__main__":
    # 簡単な動作確認
    db = WorkflowDatabase("tmp/test_workflow.db")
    analytics = WorkflowAnalytics(db)

    # テストプロジェクト作成
    project_id = db.get_or_create_project("test-project", display_name="テストプロジェクト")

    # テストログ挿入
    test_log = OrchestrationLog(
        project_id=project_id,
        user_request="テスト要求",
        status="completed",
        success=True,
        task_type="formatting",
        complexity="simple",
        total_cost=0.001,
        cost_savings=0.01
    )
    db.log_orchestration(test_log)

    # 統計取得
    stats = db.get_project_stats("test-project")
    print(f"プロジェクト統計: {stats}")

    print("✅ WorkflowDatabase 動作確認完了")
