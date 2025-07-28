#!/usr/bin/env python3
"""
Phase Integration Test - Issue #640 統合テスト
Phase1〜3間の相互作用テストシステム

目的: Phase間の統合テスト・相互作用検証
- Phase1 TDD基盤システム統合テスト
- Phase2 リアルタイム監視システム統合テスト  
- Phase3 セキュリティ・統合テスト基盤統合テスト
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PhaseTestResult:
    """Phaseテスト結果"""
    phase_name: str
    test_count: int
    passed_tests: int
    failed_tests: int
    duration: float
    errors: List[str]
    success_rate: float

class PhaseIntegrationTester:
    """Phase統合テストシステム"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.phase_results = {}
        
    def run_all_phase_tests(self) -> Dict[str, PhaseTestResult]:
        """全Phaseテスト実行"""
        logger.info("🚀 Phase1〜3統合テスト開始")
        
        phases = [
            ("Phase1_TDD", self._test_phase1_tdd_systems),
            ("Phase2_Monitoring", self._test_phase2_monitoring_systems),
            ("Phase3_Security", self._test_phase3_security_systems),
            ("Integration", self._test_phase_integration)
        ]
        
        for phase_name, test_func in phases:
            logger.info(f"📊 {phase_name} テスト開始...")
            start_time = time.time()
            
            try:
                result = test_func()
                duration = time.time() - start_time
                
                self.phase_results[phase_name] = PhaseTestResult(
                    phase_name=phase_name,
                    test_count=result.get('total', 0),
                    passed_tests=result.get('passed', 0),
                    failed_tests=result.get('failed', 0),
                    duration=duration,
                    errors=result.get('errors', []),
                    success_rate=result.get('success_rate', 0.0)
                )
                
                logger.info(f"✅ {phase_name} テスト完了: {duration:.2f}秒")
                
            except Exception as e:
                duration = time.time() - start_time
                self.phase_results[phase_name] = PhaseTestResult(
                    phase_name=phase_name,
                    test_count=1,
                    passed_tests=0,
                    failed_tests=1,
                    duration=duration,
                    errors=[str(e)],
                    success_rate=0.0
                )
                logger.error(f"❌ {phase_name} テスト失敗: {e}")
        
        return self.phase_results
    
    def _test_phase1_tdd_systems(self) -> Dict[str, Any]:
        """Phase1 TDD基盤システムテスト"""
        results = {"total": 0, "passed": 0, "failed": 0, "errors": []}
        
        tdd_modules = [
            'tdd_system_base', 'tdd_foundation', 'tdd_automation',
            'tdd_cycle_manager', 'tdd_session_manager', 
            'tdd_test_runner', 'tdd_spec_generator'
        ]
        
        for module_name in tdd_modules:
            results["total"] += 1
            try:
                module = __import__(module_name)
                results["passed"] += 1
                logger.debug(f"✅ {module_name} import成功")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{module_name}: {e}")
                logger.debug(f"❌ {module_name} import失敗: {e}")
        
        results["success_rate"] = (results["passed"] / results["total"]) * 100
        return results
    
    def _test_phase2_monitoring_systems(self) -> Dict[str, Any]:
        """Phase2 リアルタイム監視システムテスト"""
        results = {"total": 0, "passed": 0, "failed": 0, "errors": []}
        
        monitoring_modules = [
            'realtime_quality_monitor', 'quality_gate_checker',
            'performance_optimizer', 'resource_manager'
        ]
        
        for module_name in monitoring_modules:
            results["total"] += 1
            try:
                module = __import__(module_name)
                results["passed"] += 1
                logger.debug(f"✅ {module_name} import成功")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{module_name}: {e}")
                logger.debug(f"❌ {module_name} import失敗: {e}")
        
        results["success_rate"] = (results["passed"] / results["total"]) * 100
        return results
    
    def _test_phase3_security_systems(self) -> Dict[str, Any]:
        """Phase3 セキュリティテストシステム"""
        results = {"total": 0, "passed": 0, "failed": 0, "errors": []}
        
        security_tests = [
            ('security_sql_injection_test', '--unit-test'),
            ('security_xss_test', '--unit-test')
        ]
        
        for test_module, test_arg in security_tests:
            results["total"] += 1
            try:
                import subprocess
                result = subprocess.run([
                    sys.executable, f"{test_module}.py", test_arg
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    results["passed"] += 1
                    logger.debug(f"✅ {test_module} 単体テスト成功")
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{test_module}: テスト失敗")
                    logger.debug(f"❌ {test_module} 単体テスト失敗")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{test_module}: {e}")
                logger.debug(f"❌ {test_module} 実行エラー: {e}")
        
        results["success_rate"] = (results["passed"] / results["total"]) * 100
        return results
    
    def _test_phase_integration(self) -> Dict[str, Any]:
        """Phase間統合テスト"""
        results = {"total": 0, "passed": 0, "failed": 0, "errors": []}
        
        integration_tests = [
            ("設定ファイル共有", self._test_shared_config),
            ("ログシステム統合", self._test_logging_integration),
            ("エラーハンドリング統合", self._test_error_handling_integration)
        ]
        
        for test_name, test_func in integration_tests:
            results["total"] += 1
            try:
                if test_func():
                    results["passed"] += 1
                    logger.debug(f"✅ {test_name} 統合テスト成功")
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{test_name}: テスト失敗")
                    logger.debug(f"❌ {test_name} 統合テスト失敗")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{test_name}: {e}")
                logger.debug(f"❌ {test_name} 統合テストエラー: {e}")
        
        results["success_rate"] = (results["passed"] / results["total"]) * 100
        return results
    
    def _test_shared_config(self) -> bool:
        """設定ファイル共有テスト"""
        try:
            from security_utils import load_security_config
            config = load_security_config()
            return len(config) > 0
        except:
            return False
    
    def _test_logging_integration(self) -> bool:
        """ログシステム統合テスト"""
        try:
            from kumihan_formatter.core.utilities.logger import get_logger
            test_logger = get_logger("integration_test")
            test_logger.info("統合テストログメッセージ")
            return True
        except:
            return False
    
    def _test_error_handling_integration(self) -> bool:
        """エラーハンドリング統合テスト"""
        try:
            from tdd_system_base import TDDSystemError
            # エラークラスのインスタンス化テスト
            error = TDDSystemError("テストエラー")
            return isinstance(error, Exception)
        except:
            return False
    
    def generate_report(self):
        """統合テストレポート生成"""
        logger.info("📋 Phase統合テスト結果サマリー:")
        
        total_tests = sum(result.test_count for result in self.phase_results.values())
        total_passed = sum(result.passed_tests for result in self.phase_results.values())
        total_failed = sum(result.failed_tests for result in self.phase_results.values())
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"  総テスト数: {total_tests}")
        logger.info(f"  成功: {total_passed}, 失敗: {total_failed}")
        logger.info(f"  成功率: {overall_success_rate:.1f}%")
        
        for phase_name, result in self.phase_results.items():
            logger.info(f"  {phase_name}: {result.success_rate:.1f}% ({result.passed_tests}/{result.test_count})")
            
            if result.errors:
                logger.warning(f"    エラー: {len(result.errors)}件")
                for error in result.errors[:3]:  # 上位3件のみ表示
                    logger.warning(f"      - {error}")

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    logger.info("🚀 Issue #640 Phase統合テスト開始")
    
    tester = PhaseIntegrationTester(project_root)
    results = tester.run_all_phase_tests()
    tester.generate_report()
    
    # 総合成功率による終了コード
    total_tests = sum(result.test_count for result in results.values())
    total_passed = sum(result.passed_tests for result in results.values())
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    if success_rate >= 80:
        logger.info("🎉 Phase統合テスト成功！")
        return 0
    else:
        logger.warning("⚠️ Phase統合テストに問題があります")
        return 1

if __name__ == "__main__":
    sys.exit(main())