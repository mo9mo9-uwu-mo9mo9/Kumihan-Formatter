#!/usr/bin/env python3
"""Gemini失敗対策・回復システム

Geminiの実装失敗を検知・分析し、適切な回復策を講じるシステム。
82%の失敗率を20%以下に改善することを目標とする。

主要機能:
- 失敗パターンの分析・分類
- 2回失敗ルール（Claude自動切り替え）
- 失敗予測・予防機能
- 学習機能（失敗履歴からの改善）

Created: 2025-08-15 (Issue #823 Gemini失敗対策)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """失敗タイプの分類"""
    EXECUTION_ERROR = "execution_error"      # 実行エラー (import, syntax等)
    QUALITY_VALIDATION = "quality_validation"  # 品質検証失敗 (MyPy, lint等)
    TIMEOUT = "timeout"                     # タイムアウト
    ENVIRONMENT_ISSUE = "environment_issue"  # 環境問題 (依存関係等)
    API_ERROR = "api_error"                 # Gemini API エラー


class RecoveryAction(Enum):
    """回復アクション"""
    RETRY_WITH_FIX = "retry_with_fix"      # 修正してリトライ
    CLAUDE_TAKEOVER = "claude_takeover"    # Claude に切り替え
    ENVIRONMENT_FIX = "environment_fix"    # 環境修正
    SKIP_TASK = "skip_task"               # タスクスキップ


@dataclass
class FailureRecord:
    """失敗記録"""
    timestamp: str
    task_id: str
    task_description: str
    failure_type: FailureType
    error_message: str
    file_path: Optional[str] = None
    recovery_attempted: bool = False
    recovery_action: Optional[RecoveryAction] = None
    recovery_success: bool = False


@dataclass
class TaskPattern:
    """タスクパターン"""
    pattern_id: str
    description: str
    keywords: List[str]
    estimated_difficulty: float  # 0.0-1.0
    historical_success_rate: float  # 0.0-1.0
    recommended_executor: str  # "gemini" or "claude"


class FailureRecoverySystem:
    """Gemini失敗対策・回復システム"""

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        """
        初期化処理

        Args:
            reports_dir: レポートディレクトリ。Noneの場合は現在のディレクトリ
        """
        self.reports_dir = reports_dir or Path(__file__).parent
        self.failure_log_path = self.reports_dir / "failure_recovery_log.json"
        self.task_patterns_path = self.reports_dir / "task_patterns.json"
        self.recovery_stats_path = self.reports_dir / "recovery_statistics.json"

        # 失敗記録を読み込み
        self.failure_records: List[FailureRecord] = self._load_failure_records()
        self.task_patterns: List[TaskPattern] = self._load_task_patterns()

        # 失敗閾値設定
        self.max_failures_per_pattern = 2  # 同一パターンでの最大失敗回数
        self.failure_rate_threshold = 0.8  # Claude切り替え判定の失敗率閾値
        self.lookback_hours = 24  # 失敗判定の対象時間（時間）

    def _load_failure_records(self) -> List[FailureRecord]:
        """失敗記録を読み込む"""
        if not self.failure_log_path.exists():
            return []

        try:
            with open(self.failure_log_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            records = []
            for item in data:
                # FailureType の変換
                failure_type = FailureType(item["failure_type"])
                recovery_action = RecoveryAction(item["recovery_action"]) if item.get("recovery_action") else None

                record = FailureRecord(
                    timestamp=item["timestamp"],
                    task_id=item["task_id"],
                    task_description=item["task_description"],
                    failure_type=failure_type,
                    error_message=item["error_message"],
                    file_path=item.get("file_path"),
                    recovery_attempted=item.get("recovery_attempted", False),
                    recovery_action=recovery_action,
                    recovery_success=item.get("recovery_success", False)
                )
                records.append(record)

            return records
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"失敗記録の読み込みに失敗: {e}")
            return []

    def _save_failure_records(self) -> None:
        """失敗記録を保存する"""
        try:
            data = []
            for record in self.failure_records:
                item = asdict(record)
                item["failure_type"] = record.failure_type.value
                if record.recovery_action:
                    item["recovery_action"] = record.recovery_action.value
                data.append(item)

            with open(self.failure_log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"失敗記録の保存に失敗: {e}")

    def _load_task_patterns(self) -> List[TaskPattern]:
        """タスクパターンを読み込む"""
        if not self.task_patterns_path.exists():
            return self._create_default_task_patterns()

        try:
            with open(self.task_patterns_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            patterns = []
            for item in data:
                pattern = TaskPattern(**item)
                patterns.append(pattern)

            return patterns
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"タスクパターンの読み込みに失敗: {e}")
            return self._create_default_task_patterns()

    def _create_default_task_patterns(self) -> List[TaskPattern]:
        """デフォルトタスクパターンを作成"""
        default_patterns = [
            TaskPattern(
                pattern_id="mypy_type_annotation",
                description="MyPy型注釈修正",
                keywords=["mypy", "型注釈", "type annotation", "no-untyped-def"],
                estimated_difficulty=0.6,
                historical_success_rate=0.3,  # 現状30%成功率
                recommended_executor="claude"  # 失敗率高いのでClaude推奨
            ),
            TaskPattern(
                pattern_id="lint_formatting",
                description="リント・フォーマット修正",
                keywords=["flake8", "black", "isort", "lint"],
                estimated_difficulty=0.3,
                historical_success_rate=0.7,
                recommended_executor="gemini"
            ),
            TaskPattern(
                pattern_id="external_library_deps",
                description="外部ライブラリ依存関係",
                keywords=["pandas", "plotly", "library stubs", "import-not-found"],
                estimated_difficulty=0.8,
                historical_success_rate=0.2,
                recommended_executor="claude"
            ),
            TaskPattern(
                pattern_id="complex_refactoring",
                description="複雑なリファクタリング",
                keywords=["リファクタリング", "アーキテクチャ", "設計"],
                estimated_difficulty=0.9,
                historical_success_rate=0.1,
                recommended_executor="claude"
            ),
            TaskPattern(
                pattern_id="simple_bug_fix",
                description="単純なバグ修正",
                keywords=["バグ修正", "bug fix", "修正"],
                estimated_difficulty=0.4,
                historical_success_rate=0.6,
                recommended_executor="gemini"
            )
        ]

        # デフォルトパターンを保存
        self._save_task_patterns(default_patterns)
        return default_patterns

    def _save_task_patterns(self, patterns: List[TaskPattern]) -> None:
        """タスクパターンを保存"""
        try:
            data = [asdict(pattern) for pattern in patterns]
            with open(self.task_patterns_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"タスクパターンの保存に失敗: {e}")

    def analyze_failure(self, task_id: str, task_description: str,
                       error_message: str, file_path: Optional[str] = None) -> FailureType:
        """
        失敗を分析して分類する

        Args:
            task_id: タスクID
            task_description: タスク説明
            error_message: エラーメッセージ
            file_path: 対象ファイルパス

        Returns:
            失敗タイプ
        """
        error_lower = error_message.lower()

        # 実行エラー判定
        execution_keywords = [
            "import error", "syntax error", "indentation error",
            "attempted relative import", "module not found",
            "name error", "attribute error"
        ]
        if any(keyword in error_lower for keyword in execution_keywords):
            return FailureType.EXECUTION_ERROR

        # 品質検証失敗判定
        quality_keywords = [
            "mypy", "flake8", "black", "lint", "type check",
            "no-untyped-def", "no-any-return", "import-untyped"
        ]
        if any(keyword in error_lower for keyword in quality_keywords):
            return FailureType.QUALITY_VALIDATION

        # 環境問題判定
        env_keywords = [
            "library stubs not installed", "package not found",
            "dependency", "requirements", "pip install"
        ]
        if any(keyword in error_lower for keyword in env_keywords):
            return FailureType.ENVIRONMENT_ISSUE

        # タイムアウト判定
        if "timeout" in error_lower or "time limit" in error_lower:
            return FailureType.TIMEOUT

        # API エラー判定
        api_keywords = ["api error", "authentication", "rate limit", "quota"]
        if any(keyword in error_lower for keyword in api_keywords):
            return FailureType.API_ERROR

        return FailureType.EXECUTION_ERROR  # デフォルト

    def record_failure(self, task_id: str, task_description: str,
                      error_message: str, file_path: Optional[str] = None) -> None:
        """
        失敗を記録する

        Args:
            task_id: タスクID
            task_description: タスク説明
            error_message: エラーメッセージ
            file_path: 対象ファイルパス
        """
        failure_type = self.analyze_failure(task_id, task_description, error_message, file_path)

        record = FailureRecord(
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            task_description=task_description,
            failure_type=failure_type,
            error_message=error_message,
            file_path=file_path
        )

        self.failure_records.append(record)
        self._save_failure_records()

        logger.info(f"失敗記録追加: {task_id} - {failure_type.value}")

    def get_task_pattern(self, task_description: str) -> Optional[TaskPattern]:
        """
        タスク説明からパターンを特定する

        Args:
            task_description: タスク説明

        Returns:
            マッチしたタスクパターン
        """
        task_lower = task_description.lower()

        best_match = None
        best_score = 0.0

        for pattern in self.task_patterns:
            score = 0
            for keyword in pattern.keywords:
                if keyword.lower() in task_lower:
                    score += 1

            # キーワードマッチ率を計算
            match_rate = score / len(pattern.keywords) if pattern.keywords else 0

            if match_rate > best_score and match_rate > 0.3:  # 30%以上マッチで候補
                best_match = pattern
                best_score = float(match_rate)

        return best_match

    def should_switch_to_claude(self, task_description: str) -> Tuple[bool, str]:
        """
        Claudeに切り替えるべきかを判定する

        Args:
            task_description: タスク説明

        Returns:
            (切り替えるべきか, 理由)
        """
        # タスクパターンチェック
        pattern = self.get_task_pattern(task_description)
        if pattern and pattern.recommended_executor == "claude":
            return True, f"タスクパターン推奨: {pattern.description} (成功率: {pattern.historical_success_rate:.1%})"

        # 最近の失敗履歴チェック
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        recent_failures = [
            record for record in self.failure_records
            if datetime.fromisoformat(record.timestamp) > cutoff_time
        ]

        if not recent_failures:
            return False, "失敗履歴なし"

        # 同一パターンでの連続失敗チェック
        if pattern:
            pattern_failures = [
                record for record in recent_failures
                if self.get_task_pattern(record.task_description) == pattern
            ]

            if len(pattern_failures) >= self.max_failures_per_pattern:
                return True, f"同一パターンで{len(pattern_failures)}回連続失敗"

        # 全体的な失敗率チェック
        total_recent_tasks = len(recent_failures)
        if total_recent_tasks >= 3:  # 最低3タスク以上で判定
            failure_rate = total_recent_tasks / total_recent_tasks  # 現在は全て失敗として扱う

            if failure_rate >= self.failure_rate_threshold:
                return True, f"失敗率が閾値を超過: {failure_rate:.1%} >= {self.failure_rate_threshold:.1%}"

        return False, "切り替え条件に該当せず"

    def suggest_recovery_action(self, task_id: str, task_description: str,
                              failure_type: FailureType, error_message: str) -> RecoveryAction:
        """
        回復アクションを提案する

        Args:
            task_id: タスクID
            task_description: タスク説明
            failure_type: 失敗タイプ
            error_message: エラーメッセージ

        Returns:
            推奨回復アクション
        """
        # 環境問題は環境修正を優先
        if failure_type == FailureType.ENVIRONMENT_ISSUE:
            return RecoveryAction.ENVIRONMENT_FIX

        # Claude切り替え判定
        should_switch, reason = self.should_switch_to_claude(task_description)
        if should_switch:
            logger.info(f"Claude切り替え推奨: {reason}")
            return RecoveryAction.CLAUDE_TAKEOVER

        # API エラーはスキップ
        if failure_type == FailureType.API_ERROR:
            return RecoveryAction.SKIP_TASK

        # その他は修正してリトライ
        return RecoveryAction.RETRY_WITH_FIX

    def update_pattern_success_rate(self, task_description: str, success: bool) -> None:
        """
        パターンの成功率を更新する

        Args:
            task_description: タスク説明
            success: 成功したかどうか
        """
        pattern = self.get_task_pattern(task_description)
        if not pattern:
            return

        # 成功率を更新（指数移動平均）
        alpha = 0.2  # 学習率
        new_rate = 1.0 if success else 0.0
        pattern.historical_success_rate = (
            (1 - alpha) * pattern.historical_success_rate + alpha * new_rate
        )

        # 成功率に基づいて推奨実行者を更新
        if pattern.historical_success_rate < 0.4:
            pattern.recommended_executor = "claude"
        elif pattern.historical_success_rate > 0.7:
            pattern.recommended_executor = "gemini"

        # パターンを保存
        self._save_task_patterns(self.task_patterns)

        logger.info(f"パターン更新: {pattern.description} - 成功率: {pattern.historical_success_rate:.1%}")

    def generate_recovery_report(self) -> Dict[str, Any]:
        """
        回復統計レポートを生成する

        Returns:
            回復統計レポート
        """
        if not self.failure_records:
            return {"message": "失敗記録なし"}

        # 最近24時間の統計
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_failures = [
            record for record in self.failure_records
            if datetime.fromisoformat(record.timestamp) > cutoff_time
        ]

        # 失敗タイプ別統計
        failure_type_counts: Dict[str, int] = {}
        for record in recent_failures:
            failure_type = record.failure_type.value
            failure_type_counts[failure_type] = failure_type_counts.get(failure_type, 0) + 1

        # パターン別統計
        pattern_stats = {}
        for pattern in self.task_patterns:
            pattern_failures = [
                record for record in recent_failures
                if self.get_task_pattern(record.task_description) == pattern
            ]
            pattern_stats[pattern.pattern_id] = {
                "description": pattern.description,
                "recent_failures": len(pattern_failures),
                "success_rate": pattern.historical_success_rate,
                "recommended_executor": pattern.recommended_executor
            }

        report = {
            "report_generated": datetime.now().isoformat(),
            "period": "24時間",
            "total_failures": len(recent_failures),
            "failure_rate": len(recent_failures) / max(len(recent_failures), 1),  # 暫定計算
            "failure_by_type": failure_type_counts,
            "pattern_statistics": pattern_stats,
            "claude_switch_recommendations": [
                pattern.pattern_id for pattern in self.task_patterns
                if pattern.recommended_executor == "claude"
            ]
        }

        # レポートを保存
        try:
            with open(self.recovery_stats_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"回復統計レポートの保存に失敗: {e}")

        return report


def main() -> None:
    """メイン処理（テスト用）"""
    logging.basicConfig(level=logging.INFO)

    system = FailureRecoverySystem()

    # テスト用の失敗記録
    test_tasks = [
        ("task_001", "MyPy型注釈エラー修正", "no-untyped-def エラーが発生"),
        ("task_002", "pandas データ分析実装", "Library stubs not installed for pandas"),
        ("task_003", "flake8 lint修正", "E501 line too long"),
    ]

    for task_id, description, error in test_tasks:
        system.record_failure(task_id, description, error)

        should_switch, reason = system.should_switch_to_claude(description)
        print(f"{description}: Claude切り替え={should_switch} - {reason}")

    # レポート生成
    report = system.generate_recovery_report()
    print("\n=== 回復統計レポート ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
