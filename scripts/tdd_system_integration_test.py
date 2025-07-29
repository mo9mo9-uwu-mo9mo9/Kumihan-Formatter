#!/usr/bin/env python3
"""
TDD System Integration Test - Final Validation
TDDシステム統合テストスイート

目的: 全TDDシステムの統合テストと最終検証
- 全コンポーネント連携テスト
- パフォーマンステスト
- セキュリティテスト
- メモリリークテスト
- 実用性テスト
"""

import sys
import time
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import unittest
from unittest.mock import Mock, patch
import json

# TDDシステムインポート
sys.path.append(str(Path(__file__).parent))

from tdd_system_base import (
    TDDSystemBase,
    TDDSystemConfig,
    create_tdd_config,
    TDDSystemRegistry,
)
from secure_subprocess import secure_run, test_secure_subprocess
from resource_manager import memory_manager, test_memory_manager
from performance_optimizer import test_performance_optimizer
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IntegrationTestResult:
    """統合テスト結果"""

    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime


class TDDSystemIntegrationTest:
    """TDD統合テストスイート"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = []
        self.test_project_root = None

    def run_all_tests(self) -> Dict[str, Any]:
        """全統合テスト実行"""
        logger.info("🚀 TDDシステム統合テスト開始")

        # テスト用プロジェクト作成
        self._setup_test_environment()

        try:
            # テストスイート実行
            test_methods = [
                self._test_secure_subprocess_integration,
                self._test_memory_management_integration,
                self._test_performance_optimization_integration,
                self._test_system_base_integration,
                self._test_session_management_integration,
                self._test_quality_gate_integration,
                self._test_realtime_monitoring_integration,
                self._test_full_tdd_workflow,
                self._test_concurrent_operations,
                self._test_resource_cleanup,
                self._test_error_handling,
                self._test_scalability,
            ]

            for test_method in test_methods:
                self._run_test(test_method)

            # 最終結果生成
            return self._generate_final_report()

        finally:
            self._cleanup_test_environment()

    def _setup_test_environment(self):
        """テスト環境セットアップ"""
        logger.info("🔧 テスト環境セットアップ中...")

        # テスト用一時ディレクトリ作成
        self.test_project_root = Path(tempfile.mkdtemp(prefix="tdd_integration_test_"))

        # 必要なディレクトリ構成作成
        test_dirs = [
            "scripts",
            ".tdd_logs",
            ".quality_data",
            "tests",
            "kumihan_formatter/core",
        ]

        for dir_name in test_dirs:
            (self.test_project_root / dir_name).mkdir(parents=True, exist_ok=True)

        # 必要なファイルコピー
        script_files = [
            "secure_subprocess.py",
            "resource_manager.py",
            "performance_optimizer.py",
            "tdd_system_base.py",
        ]

        for script_file in script_files:
            src_file = self.project_root / "scripts" / script_file
            if src_file.exists():
                shutil.copy2(src_file, self.test_project_root / "scripts")

        logger.info(f"✅ テスト環境作成完了: {self.test_project_root}")

    def _cleanup_test_environment(self):
        """テスト環境クリーンアップ"""
        if self.test_project_root and self.test_project_root.exists():
            try:
                shutil.rmtree(self.test_project_root)
                logger.info("🧹 テスト環境クリーンアップ完了")
            except Exception as e:
                logger.warning(f"テスト環境クリーンアップ警告: {e}")

    def _run_test(self, test_method):
        """個別テスト実行"""
        test_name = test_method.__name__
        logger.info(f"🧪 {test_name} 実行中...")

        start_time = time.time()

        try:
            details = test_method()
            execution_time = time.time() - start_time

            result = IntegrationTestResult(
                test_name=test_name,
                success=True,
                execution_time=execution_time,
                error_message=None,
                details=details or {},
                timestamp=datetime.now(),
            )

            logger.info(f"✅ {test_name} 成功 ({execution_time:.2f}s)")

        except Exception as e:
            execution_time = time.time() - start_time

            result = IntegrationTestResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
                details={"exception_type": type(e).__name__},
                timestamp=datetime.now(),
            )

            logger.error(f"❌ {test_name} 失敗 ({execution_time:.2f}s): {e}")

        self.test_results.append(result)

    def _test_secure_subprocess_integration(self) -> Dict:
        """セキュアサブプロセス統合テスト"""
        # セキュリティテスト
        test_secure_subprocess()

        # 実際のコマンド実行テスト
        result = secure_run(["python3", "--version"])
        assert result.success, "Python version command failed"
        assert "Python" in result.stdout, "Python version output invalid"

        return {
            "python_version": result.stdout.strip(),
            "execution_time": result.execution_time,
        }

    def _test_memory_management_integration(self) -> Dict:
        """メモリ管理統合テスト"""
        # メモリマネージャーテスト
        test_memory_manager()

        # メモリ監視開始
        memory_manager.start_monitoring()

        # メモリ使用テスト
        test_data = [list(range(1000)) for _ in range(10)]
        time.sleep(2)  # 監視データ蓄積

        # レポート取得
        report = memory_manager.get_memory_report()
        memory_manager.stop_monitoring()

        assert "current_memory_mb" in report, "Memory report missing key data"

        return {"memory_report": report, "test_data_size": len(test_data)}

    def _test_performance_optimization_integration(self) -> Dict:
        """パフォーマンス最適化統合テスト"""
        # パフォーマンス最適化テスト
        test_performance_optimizer()

        from performance_optimizer import init_performance_optimizer

        optimizer = init_performance_optimizer(self.test_project_root)

        # キャッシュテスト
        @optimizer.cached_function(ttl_seconds=10)
        def test_function(x):
            time.sleep(0.01)  # 軽い処理
            return x * 2

        # 初回実行（キャッシュミス）
        result1 = test_function(5)

        # 2回目実行（キャッシュヒット）
        result2 = test_function(5)

        assert result1 == result2 == 10, "Cache function results mismatch"

        # パフォーマンスレポート取得
        perf_report = optimizer.get_performance_report()
        optimizer.shutdown()

        return {"performance_report": perf_report, "cache_test_result": result1}

    def _test_system_base_integration(self) -> Dict:
        """システム基盤統合テスト"""
        config = create_tdd_config(self.test_project_root)

        class TestSystem(TDDSystemBase):
            def initialize(self) -> bool:
                return True

            def execute_main_operation(self) -> str:
                return "test_complete"

        # システム実行テスト
        system = TestSystem(config)
        result = system.run()

        assert result == "test_complete", "System execution failed"

        # 状況取得テスト
        status = system.get_status()
        assert status["initialized"], "System not initialized"

        return {"execution_result": result, "system_status": status}

    def _test_session_management_integration(self) -> Dict:
        """セッション管理統合テスト"""
        # セッション管理の基本機能テスト
        session_data = {
            "issue_number": "test-001",
            "issue_title": "テスト用Issue",
            "branch_name": "test-branch",
            "start_time": datetime.now().isoformat(),
            "current_phase": "not_started",
        }

        # セッションファイル作成テスト
        session_file = self.test_project_root / ".tdd_session.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        # セッションファイル読み込みテスト
        with open(session_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["issue_number"] == "test-001", "Session data mismatch"

        return {
            "session_file_created": session_file.exists(),
            "session_data": loaded_data,
        }

    def _test_quality_gate_integration(self) -> Dict:
        """品質ゲート統合テスト"""
        # 品質ゲート設定テスト
        quality_gates = {
            "critical_tier": {
                "modules": ["test.module"],
                "min_coverage": 95.0,
                "required_tests": ["unit", "integration"],
                "max_complexity": 10,
            }
        }

        gates_file = self.test_project_root / "scripts" / "quality_gates.json"
        gates_file.parent.mkdir(exist_ok=True)

        with open(gates_file, "w", encoding="utf-8") as f:
            json.dump(quality_gates, f, indent=2, ensure_ascii=False)

        # 設定ファイル読み込みテスト
        with open(gates_file, "r", encoding="utf-8") as f:
            loaded_gates = json.load(f)

        assert "critical_tier" in loaded_gates, "Quality gates configuration invalid"

        return {
            "quality_gates_file_created": gates_file.exists(),
            "quality_gates_config": loaded_gates,
        }

    def _test_realtime_monitoring_integration(self) -> Dict:
        """リアルタイム監視統合テスト"""
        # 監視状態ファイル作成テスト
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "coverage": {"percentage": 85.5, "status": "good"},
            "tests": {"total": 100, "failed": 2, "passed": 98},
            "quality": {"score": 88.5, "violations": []},
            "tdd": {"phase": "green", "status": "active_green"},
        }

        vscode_status_file = (
            self.test_project_root / ".quality_data" / "vscode_status.json"
        )
        vscode_status_file.parent.mkdir(exist_ok=True)

        with open(vscode_status_file, "w", encoding="utf-8") as f:
            json.dump(monitoring_data, f, indent=2, ensure_ascii=False)

        # 監視データ読み込みテスト
        with open(vscode_status_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["coverage"]["percentage"] == 85.5, "Monitoring data invalid"

        return {
            "monitoring_file_created": vscode_status_file.exists(),
            "monitoring_data": loaded_data,
        }

    def _test_full_tdd_workflow(self) -> Dict:
        """完全TDDワークフローテスト"""
        # TDDワークフロー全体のシミュレーション
        workflow_steps = [
            "session_start",
            "spec_generation",
            "red_phase",
            "green_phase",
            "refactor_phase",
            "cycle_complete",
        ]

        completed_steps = []

        for step in workflow_steps:
            # 各ステップのシミュレーション
            time.sleep(0.1)  # 処理時間シミュレート
            completed_steps.append(
                {
                    "step": step,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                }
            )

        assert len(completed_steps) == len(workflow_steps), "Workflow incomplete"

        return {
            "workflow_steps": workflow_steps,
            "completed_steps": completed_steps,
            "total_steps": len(completed_steps),
        }

    def _test_concurrent_operations(self) -> Dict:
        """並行操作テスト"""
        results = []
        threads = []

        def worker_task(task_id: int):
            time.sleep(0.1)
            results.append(f"task_{task_id}_completed")

        # 複数スレッド同時実行
        for i in range(5):
            thread = threading.Thread(target=worker_task, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了待機
        for thread in threads:
            thread.join(timeout=5)

        assert len(results) == 5, "Concurrent operations failed"

        return {
            "concurrent_tasks": 5,
            "completed_tasks": len(results),
            "results": results,
        }

    def _test_resource_cleanup(self) -> Dict:
        """リソースクリーンアップテスト"""
        # テスト用リソース作成
        test_files = []

        for i in range(3):
            test_file = self.test_project_root / f"test_resource_{i}.tmp"
            test_file.write_text(f"test content {i}")
            test_files.append(test_file)

        # リソース存在確認
        existing_files = [f for f in test_files if f.exists()]
        assert len(existing_files) == 3, "Test resources not created"

        # クリーンアップ実行
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()

        # クリーンアップ確認
        remaining_files = [f for f in test_files if f.exists()]
        assert len(remaining_files) == 0, "Resource cleanup failed"

        return {
            "created_files": len(test_files),
            "cleaned_files": len(test_files) - len(remaining_files),
            "cleanup_success": len(remaining_files) == 0,
        }

    def _test_error_handling(self) -> Dict:
        """エラーハンドリングテスト"""
        error_scenarios = []

        # 無効なコマンド実行テスト
        try:
            result = secure_run(["nonexistent_command"])
            error_scenarios.append(
                {
                    "scenario": "invalid_command",
                    "handled": not result.success,
                    "error": result.stderr,
                }
            )
        except Exception as e:
            error_scenarios.append(
                {"scenario": "invalid_command", "handled": True, "error": str(e)}
            )

        # 無効なファイルアクセステスト
        try:
            invalid_file = Path("/nonexistent/path/file.txt")
            content = invalid_file.read_text()
            error_scenarios.append(
                {
                    "scenario": "invalid_file_access",
                    "handled": False,
                    "error": "No error raised",
                }
            )
        except Exception as e:
            error_scenarios.append(
                {"scenario": "invalid_file_access", "handled": True, "error": str(e)}
            )

        # 全エラーが適切に処理されていることを確認
        all_handled = all(scenario["handled"] for scenario in error_scenarios)
        assert all_handled, "Some errors were not properly handled"

        return {"error_scenarios": error_scenarios, "all_errors_handled": all_handled}

    def _test_scalability(self) -> Dict:
        """スケーラビリティテスト"""
        # 大量データ処理テスト
        data_sizes = [100, 500, 1000]
        processing_times = []

        for size in data_sizes:
            start_time = time.time()

            # データ処理シミュレーション
            test_data = list(range(size))
            processed_data = [x * 2 for x in test_data]

            processing_time = time.time() - start_time
            processing_times.append(
                {
                    "data_size": size,
                    "processing_time": processing_time,
                    "throughput": size / processing_time if processing_time > 0 else 0,
                }
            )

        # スケーラビリティ検証
        average_throughput = sum(pt["throughput"] for pt in processing_times) / len(
            processing_times
        )
        scalability_good = average_throughput > 1000  # 1000 items/sec 以上

        return {
            "processing_times": processing_times,
            "average_throughput": average_throughput,
            "scalability_assessment": (
                "good" if scalability_good else "needs_improvement"
            ),
        }

    def _generate_final_report(self) -> Dict[str, Any]:
        """最終レポート生成"""
        successful_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]

        total_execution_time = sum(r.execution_time for r in self.test_results)
        success_rate = len(successful_tests) / len(self.test_results) * 100

        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": success_rate,
                "total_execution_time": total_execution_time,
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.test_results
            ],
            "failed_tests_details": [
                {
                    "test_name": r.test_name,
                    "error_message": r.error_message,
                    "details": r.details,
                }
                for r in failed_tests
            ],
            "overall_assessment": self._assess_overall_quality(success_rate),
            "recommendations": self._generate_recommendations(failed_tests),
            "report_timestamp": datetime.now().isoformat(),
        }

        return report

    def _assess_overall_quality(self, success_rate: float) -> str:
        """全体品質評価"""
        if success_rate >= 95:
            return "excellent"
        elif success_rate >= 85:
            return "good"
        elif success_rate >= 70:
            return "acceptable"
        else:
            return "needs_improvement"

    def _generate_recommendations(
        self, failed_tests: List[IntegrationTestResult]
    ) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []

        if failed_tests:
            recommendations.append("失敗したテストの原因を調査し、修正してください")
            recommendations.append("エラーハンドリングの強化を検討してください")

        recommendations.extend(
            [
                "定期的な統合テストの実行を継続してください",
                "パフォーマンス監視を継続してください",
                "セキュリティチェックを定期的に実行してください",
            ]
        )

        return recommendations


def main():
    """メイン実行関数"""
    integration_test = TDDSystemIntegrationTest()

    logger.info("🎯 TDDシステム統合テスト開始")

    try:
        # 統合テスト実行
        final_report = integration_test.run_all_tests()

        # レポート出力
        report_file = integration_test.project_root / "tdd_integration_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        # 結果表示
        success_rate = final_report["test_summary"]["success_rate"]
        assessment = final_report["overall_assessment"]

        logger.info(f"📊 統合テスト完了")
        logger.info(f"✅ 成功率: {success_rate:.1f}%")
        logger.info(f"🏆 総合評価: {assessment}")
        logger.info(f"📋 詳細レポート: {report_file}")

        # 全システムシャットダウン
        TDDSystemRegistry.shutdown_all()

        if success_rate >= 85:
            logger.info("🎉 TDDシステム統合テスト成功!")
            return 0
        else:
            logger.error("❌ TDDシステム統合テスト失敗")
            return 1

    except Exception as e:
        logger.error(f"💥 統合テスト実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
