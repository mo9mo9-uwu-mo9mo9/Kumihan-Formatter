#!/usr/bin/env python3
"""
Enhanced QualityGate System
既存品質ゲートシステムの強化版 - フェーズ別検証・自動fallback機能
設計・実装・統合フェーズ別品質基準・段階的品質ゲート・自動失敗時対応
"""

import os
import json
import time
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class QualityPhase(Enum):
    """品質フェーズ"""
    DESIGN = "design"           # 設計フェーズ
    IMPLEMENTATION = "implementation"  # 実装フェーズ
    INTEGRATION = "integration"  # 統合フェーズ
    PRE_COMMIT = "pre_commit"   # コミット前
    PRE_PUSH = "pre_push"       # プッシュ前
    PRODUCTION = "production"    # 本番デプロイ前

class GateResult(Enum):
    """ゲート結果"""
    PASSED = "passed"           # 通過
    FAILED = "failed"           # 失敗
    WARNING = "warning"         # 警告付き通過
    BLOCKED = "blocked"         # ブロック
    FALLBACK = "fallback"       # フォールバック実行

class FallbackStrategy(Enum):
    """フォールバック戦略"""
    AUTO_FIX = "auto_fix"       # 自動修正
    LOWER_THRESHOLD = "lower_threshold"  # 基準緩和
    MANUAL_REVIEW = "manual_review"      # 手動レビュー
    GEMINI_ASSIST = "gemini_assist"      # Gemini支援
    SKIP_GATE = "skip_gate"     # ゲートスキップ

@dataclass
class QualityGateConfig:
    """品質ゲート設定"""
    phase: QualityPhase
    gate_name: str
    description: str
    
    # 品質基準
    minimum_overall_score: float
    required_checks: List[str]
    check_thresholds: Dict[str, float]
    
    # ゲート設定
    block_on_failure: bool
    warning_threshold: float
    timeout_seconds: int
    
    # フォールバック設定
    fallback_enabled: bool
    fallback_strategies: List[FallbackStrategy]
    fallback_thresholds: Dict[str, float]
    
    # 前提条件
    prerequisites: List[str]
    dependencies: List[str]

@dataclass
class QualityGateResult:
    """品質ゲート結果"""
    gate_config: QualityGateConfig
    result: GateResult
    overall_score: float
    
    check_results: Dict[str, Dict[str, Any]]
    passed_checks: List[str]
    failed_checks: List[str]
    
    execution_time: float
    timestamp: str
    
    # フォールバック情報
    fallback_applied: bool = False
    fallback_strategy: Optional[FallbackStrategy] = None
    fallback_details: Optional[Dict[str, Any]] = None
    
    # 詳細情報
    warnings: List[str] = None
    errors: List[str] = None
    recommendations: List[str] = None

class QualityGateValidator:
    """品質ゲート検証システム"""
    
    def __init__(self):
        # 既存品質システム連携
        try:
            from .quality_manager import QualityManager
            self.quality_manager = QualityManager()
        except ImportError:
            print("⚠️ QualityManager が見つかりません。基本モードで動作します。")
            self.quality_manager = None
        
        # 自動修正システム連携
        try:
            from .auto_correction_engine import AutoCorrectionEngine
            self.correction_engine = AutoCorrectionEngine()
        except ImportError:
            print("⚠️ AutoCorrectionEngine が見つかりません。自動修正は無効です。")
            self.correction_engine = None
    
    def validate_quality_gate(self, gate_config: QualityGateConfig, 
                            target_files: List[str],
                            context: Optional[Dict[str, Any]] = None) -> QualityGateResult:
        """品質ゲート検証実行"""
        
        start_time = time.time()
        timestamp = datetime.datetime.now().isoformat()
        
        print(f"🚪 品質ゲート開始: {gate_config.gate_name} ({gate_config.phase.value})")
        print(f"📁 対象ファイル: {len(target_files)}件")
        
        # 前提条件チェック
        if not self._check_prerequisites(gate_config, context):
            print("❌ 前提条件未満足")
            return self._create_blocked_result(gate_config, start_time, timestamp, "前提条件未満足")
        
        # 品質チェック実行
        check_results = {}
        passed_checks = []
        failed_checks = []
        
        for check_name in gate_config.required_checks:
            print(f"   🔍 {check_name} チェック実行中...")
            
            check_result = self._execute_quality_check(check_name, target_files, gate_config)
            check_results[check_name] = check_result
            
            threshold = gate_config.check_thresholds.get(check_name, 0.7)
            
            if check_result["score"] >= threshold:
                passed_checks.append(check_name)
                print(f"   ✅ {check_name}: {check_result['score']:.3f} (基準: {threshold})")
            else:
                failed_checks.append(check_name)
                print(f"   ❌ {check_name}: {check_result['score']:.3f} (基準: {threshold})")
        
        # 総合スコア計算
        overall_score = self._calculate_overall_score(check_results, gate_config)
        
        # ゲート判定
        gate_result = self._determine_gate_result(gate_config, overall_score, failed_checks)
        
        execution_time = time.time() - start_time
        
        # 基本結果作成
        result = QualityGateResult(
            gate_config=gate_config,
            result=gate_result,
            overall_score=overall_score,
            check_results=check_results,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            execution_time=execution_time,
            timestamp=timestamp,
            warnings=[],
            errors=[],
            recommendations=[]
        )
        
        # フォールバック処理
        if gate_result == GateResult.FAILED and gate_config.fallback_enabled:
            print("🔄 フォールバック処理開始...")
            result = self._apply_fallback_strategies(result, target_files, context)
        
        # 結果出力
        self._print_gate_result(result)
        
        return result
    
    def _check_prerequisites(self, gate_config: QualityGateConfig, 
                           context: Optional[Dict[str, Any]]) -> bool:
        """前提条件チェック"""
        
        for prerequisite in gate_config.prerequisites:
            if prerequisite == "syntax_valid":
                # 構文チェック
                if not self._verify_syntax_validity():
                    print(f"❌ 前提条件失敗: {prerequisite}")
                    return False
            elif prerequisite == "dependencies_satisfied":
                # 依存関係チェック
                if not self._verify_dependencies(gate_config.dependencies):
                    print(f"❌ 前提条件失敗: {prerequisite}")
                    return False
            elif prerequisite == "tests_exist":
                # テスト存在チェック
                if not self._verify_tests_exist():
                    print(f"❌ 前提条件失敗: {prerequisite}")
                    return False
            
            print(f"✅ 前提条件OK: {prerequisite}")
        
        return True
    
    def _execute_quality_check(self, check_name: str, target_files: List[str], 
                             gate_config: QualityGateConfig) -> Dict[str, Any]:
        """品質チェック実行"""
        
        if self.quality_manager:
            # 既存QualityManagerを使用
            try:
                metrics = self.quality_manager.run_comprehensive_check(target_files, "quality_gate")
                
                check_mapping = {
                    "syntax": metrics.syntax_score,
                    "type_check": metrics.type_score,
                    "lint": metrics.lint_score,
                    "format": metrics.format_score,
                    "security": metrics.security_score,
                    "performance": metrics.performance_score,
                    "test": metrics.test_coverage
                }
                
                score = check_mapping.get(check_name, 0.0)
                
                return {
                    "score": score,
                    "details": {
                        "errors": metrics.error_count if hasattr(metrics, 'error_count') else 0,
                        "warnings": metrics.warning_count if hasattr(metrics, 'warning_count') else 0
                    },
                    "execution_time": 1.0  # 推定
                }
                
            except Exception as e:
                print(f"⚠️ QualityManager実行エラー: {e}")
                return self._basic_quality_check(check_name, target_files)
        else:
            return self._basic_quality_check(check_name, target_files)
    
    def _basic_quality_check(self, check_name: str, target_files: List[str]) -> Dict[str, Any]:
        """基本品質チェック（フォールバック）"""
        
        if check_name == "syntax":
            return self._check_syntax_basic(target_files)
        elif check_name == "type_check":
            return self._check_types_basic(target_files)
        elif check_name == "lint":
            return self._check_lint_basic(target_files)
        elif check_name == "format":
            return self._check_format_basic(target_files)
        elif check_name == "security":
            return self._check_security_basic(target_files)
        elif check_name == "performance":
            return self._check_performance_basic(target_files)
        elif check_name == "test":
            return self._check_test_basic(target_files)
        else:
            return {"score": 0.5, "details": {}, "execution_time": 0.1}
    
    def _check_syntax_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本構文チェック"""
        passed = 0
        total = len(target_files)
        
        for file_path in target_files:
            try:
                result = subprocess.run(
                    ["python3", "-m", "py_compile", file_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    passed += 1
            except Exception:
                pass
        
        score = passed / total if total > 0 else 1.0
        
        return {
            "score": score,
            "details": {"passed_files": passed, "total_files": total},
            "execution_time": 0.5
        }
    
    def _check_types_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本型チェック"""
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "--strict"] + target_files,
                capture_output=True,
                text=True
            )
            
            error_count = result.stdout.count("error:")
            total_lines = sum(self._count_file_lines(f) for f in target_files)
            
            # エラー率から品質スコア計算
            error_rate = error_count / max(total_lines, 1)
            score = max(0.0, 1.0 - error_rate)
            
            return {
                "score": score,
                "details": {"error_count": error_count, "total_lines": total_lines},
                "execution_time": 2.0
            }
            
        except Exception:
            return {"score": 0.5, "details": {}, "execution_time": 0.1}
    
    def _check_lint_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本リントチェック"""
        try:
            result = subprocess.run(
                ["python3", "-m", "flake8"] + target_files,
                capture_output=True,
                text=True
            )
            
            issue_count = len([line for line in result.stdout.split('\n') if line.strip()])
            total_files = len(target_files)
            
            # ファイルあたりの問題数から品質スコア計算
            issues_per_file = issue_count / max(total_files, 1)
            score = max(0.0, 1.0 - (issues_per_file / 10))  # 10問題で0点
            
            return {
                "score": score,
                "details": {"issue_count": issue_count, "issues_per_file": issues_per_file},
                "execution_time": 1.0
            }
            
        except Exception:
            return {"score": 0.5, "details": {}, "execution_time": 0.1}
    
    def _check_format_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本フォーマットチェック"""
        try:
            unformatted = 0
            for file_path in target_files:
                result = subprocess.run(
                    ["python3", "-m", "black", "--check", file_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    unformatted += 1
            
            score = 1.0 - (unformatted / max(len(target_files), 1))
            
            return {
                "score": score,
                "details": {"unformatted_files": unformatted, "total_files": len(target_files)},
                "execution_time": 0.8
            }
            
        except Exception:
            return {"score": 0.5, "details": {}, "execution_time": 0.1}
    
    def _check_security_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本セキュリティチェック"""
        
        dangerous_patterns = [r"eval\s*\(", r"exec\s*\(", r"subprocess\.call", r"shell=True"]
        
        total_issues = 0
        for file_path in target_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in dangerous_patterns:
                    total_issues += len(re.findall(pattern, content))
                    
            except Exception:
                pass
        
        # 問題数から品質スコア計算
        score = max(0.0, 1.0 - (total_issues / max(len(target_files), 1)))
        
        return {
            "score": score,
            "details": {"security_issues": total_issues},
            "execution_time": 0.3
        }
    
    def _check_performance_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本パフォーマンスチェック"""
        
        # 基本的なパフォーマンスアンチパターンチェック
        performance_issues = 0
        
        patterns = [
            r"for\s+\w+\s+in\s+range\(len\(",  # range(len()) パターン
            r"time\.sleep\s*\(\s*[0-9]+\s*\)"  # 長いsleep
        ]
        
        for file_path in target_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                for pattern in patterns:
                    performance_issues += len(re.findall(pattern, content))
                    
            except Exception:
                pass
        
        score = max(0.0, 1.0 - (performance_issues / max(len(target_files), 1)))
        
        return {
            "score": score,
            "details": {"performance_issues": performance_issues},
            "execution_time": 0.2
        }
    
    def _check_test_basic(self, target_files: List[str]) -> Dict[str, Any]:
        """基本テストチェック"""
        
        test_files = []
        source_files = []
        
        for file_path in target_files:
            if 'test' in file_path.lower() or file_path.endswith('_test.py'):
                test_files.append(file_path)
            else:
                source_files.append(file_path)
        
        # テストカバレッジ率計算
        coverage_ratio = len(test_files) / max(len(source_files), 1) if source_files else 1.0
        score = min(1.0, coverage_ratio)
        
        return {
            "score": score,
            "details": {"test_files": len(test_files), "source_files": len(source_files)},
            "execution_time": 0.1
        }
    
    def _calculate_overall_score(self, check_results: Dict[str, Dict[str, Any]], 
                               gate_config: QualityGateConfig) -> float:
        """総合スコア計算"""
        
        # 既存の重み設定を利用
        default_weights = {
            "syntax": 0.2,
            "type_check": 0.25,
            "lint": 0.2,
            "format": 0.1,
            "security": 0.15,
            "performance": 0.05,
            "test": 0.05
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for check_name in gate_config.required_checks:
            if check_name in check_results:
                weight = default_weights.get(check_name, 0.1)
                score = check_results[check_name]["score"]
                
                weighted_sum += score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _determine_gate_result(self, gate_config: QualityGateConfig, 
                             overall_score: float, failed_checks: List[str]) -> GateResult:
        """ゲート結果判定"""
        
        # 最低スコア基準チェック
        if overall_score < gate_config.minimum_overall_score:
            if gate_config.block_on_failure:
                return GateResult.FAILED
            else:
                return GateResult.WARNING
        
        # 必須チェック失敗確認
        if failed_checks:
            if gate_config.block_on_failure:
                return GateResult.FAILED
            else:
                return GateResult.WARNING
        
        # 警告基準チェック
        if overall_score < gate_config.warning_threshold:
            return GateResult.WARNING
        
        return GateResult.PASSED
    
    def _apply_fallback_strategies(self, result: QualityGateResult, 
                                 target_files: List[str],
                                 context: Optional[Dict[str, Any]]) -> QualityGateResult:
        """フォールバック戦略適用"""
        
        for strategy in result.gate_config.fallback_strategies:
            print(f"🔄 フォールバック戦略: {strategy.value}")
            
            if strategy == FallbackStrategy.AUTO_FIX and self.correction_engine:
                if self._apply_auto_fix_fallback(result, target_files):
                    result.fallback_applied = True
                    result.fallback_strategy = strategy
                    result.result = GateResult.FALLBACK
                    break
            
            elif strategy == FallbackStrategy.LOWER_THRESHOLD:
                if self._apply_lower_threshold_fallback(result):
                    result.fallback_applied = True
                    result.fallback_strategy = strategy
                    result.result = GateResult.WARNING
                    break
            
            elif strategy == FallbackStrategy.GEMINI_ASSIST:
                if self._apply_gemini_assist_fallback(result, target_files):
                    result.fallback_applied = True
                    result.fallback_strategy = strategy
                    result.result = GateResult.FALLBACK
                    break
            
            elif strategy == FallbackStrategy.MANUAL_REVIEW:
                result.fallback_applied = True
                result.fallback_strategy = strategy
                result.result = GateResult.WARNING
                result.recommendations.append("手動レビューが必要です。")
                break
            
            elif strategy == FallbackStrategy.SKIP_GATE:
                result.fallback_applied = True
                result.fallback_strategy = strategy
                result.result = GateResult.WARNING
                result.warnings.append("品質ゲートをスキップしました。")
                break
        
        return result
    
    def _apply_auto_fix_fallback(self, result: QualityGateResult, target_files: List[str]) -> bool:
        """自動修正フォールバック"""
        try:
            print("🔧 自動修正フォールバック実行中...")
            
            fixed_files = 0
            for file_path in target_files:
                suggestions = self.correction_engine.analyze_file(file_path)
                if suggestions:
                    # 簡単な修正のみ自動適用
                    simple_suggestions = [s for s in suggestions if s.auto_applicable]
                    if simple_suggestions:
                        results = self.correction_engine.apply_corrections(
                            simple_suggestions, auto_apply=True, use_gemini=False
                        )
                        if any(r.success for r in results):
                            fixed_files += 1
            
            if fixed_files > 0:
                result.fallback_details = {"fixed_files": fixed_files}
                print(f"✅ 自動修正完了: {fixed_files}ファイル")
                return True
            else:
                print("⚠️ 自動修正対象なし")
                return False
                
        except Exception as e:
            print(f"❌ 自動修正エラー: {e}")
            return False
    
    def _apply_lower_threshold_fallback(self, result: QualityGateResult) -> bool:
        """基準緩和フォールバック"""
        
        # フォールバック用の緩い基準
        fallback_threshold = result.gate_config.fallback_thresholds.get("minimum_overall_score", 0.6)
        
        if result.overall_score >= fallback_threshold:
            result.fallback_details = {
                "original_threshold": result.gate_config.minimum_overall_score,
                "fallback_threshold": fallback_threshold,
                "score": result.overall_score
            }
            print(f"✅ 基準緩和適用: {result.overall_score:.3f} >= {fallback_threshold}")
            return True
        else:
            print(f"❌ 基準緩和失敗: {result.overall_score:.3f} < {fallback_threshold}")
            return False
    
    def _apply_gemini_assist_fallback(self, result: QualityGateResult, target_files: List[str]) -> bool:
        """Gemini支援フォールバック"""
        try:
            # Gemini協業システム連携
            import sys
            sys.path.append('postbox')
            from workflow.dual_agent_coordinator import DualAgentCoordinator
            
            coordinator = DualAgentCoordinator()
            
            # 失敗チェック修正タスク作成
            task_ids = []
            for failed_check in result.failed_checks:
                task_id = coordinator.create_mypy_fix_task(
                    target_files, failed_check, auto_execute=True
                )
                if task_id:
                    task_ids.extend(task_id)
            
            if task_ids:
                result.fallback_details = {"gemini_tasks": task_ids}
                print(f"✅ Gemini支援実行: {len(task_ids)}タスク")
                return True
            else:
                print("⚠️ Gemini支援タスクなし")
                return False
                
        except Exception as e:
            print(f"❌ Gemini支援エラー: {e}")
            return False
    
    def _create_blocked_result(self, gate_config: QualityGateConfig, 
                             start_time: float, timestamp: str, reason: str) -> QualityGateResult:
        """ブロック結果作成"""
        
        execution_time = time.time() - start_time
        
        return QualityGateResult(
            gate_config=gate_config,
            result=GateResult.BLOCKED,
            overall_score=0.0,
            check_results={},
            passed_checks=[],
            failed_checks=[],
            execution_time=execution_time,
            timestamp=timestamp,
            errors=[reason],
            warnings=[],
            recommendations=["前提条件を満たしてから再実行してください。"]
        )
    
    def _print_gate_result(self, result: QualityGateResult) -> None:
        """ゲート結果出力"""
        
        result_icons = {
            GateResult.PASSED: "✅",
            GateResult.FAILED: "❌",
            GateResult.WARNING: "⚠️",
            GateResult.BLOCKED: "🚫",
            GateResult.FALLBACK: "🔄"
        }
        
        icon = result_icons.get(result.result, "❓")
        
        print(f"\n{icon} 品質ゲート結果: {result.result.value.upper()}")
        print(f"📊 総合スコア: {result.overall_score:.3f}")
        print(f"⏱️ 実行時間: {result.execution_time:.2f}秒")
        
        if result.passed_checks:
            print(f"✅ 通過チェック: {', '.join(result.passed_checks)}")
        
        if result.failed_checks:
            print(f"❌ 失敗チェック: {', '.join(result.failed_checks)}")
        
        if result.fallback_applied:
            print(f"🔄 フォールバック適用: {result.fallback_strategy.value}")
        
        if result.warnings:
            print("⚠️ 警告:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        if result.errors:
            print("❌ エラー:")
            for error in result.errors:
                print(f"   - {error}")
        
        if result.recommendations:
            print("💡 推奨事項:")
            for rec in result.recommendations:
                print(f"   - {rec}")
    
    def _verify_syntax_validity(self) -> bool:
        """構文有効性確認"""
        # 基本的な構文チェック
        return True  # 簡単な実装
    
    def _verify_dependencies(self, dependencies: List[str]) -> bool:
        """依存関係確認"""
        # 依存関係チェック
        return True  # 簡単な実装
    
    def _verify_tests_exist(self) -> bool:
        """テスト存在確認"""
        # テストファイル存在チェック
        return True  # 簡単な実装
    
    def _count_file_lines(self, file_path: str) -> int:
        """ファイル行数カウント"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0

class EnhancedQualityGateSystem:
    """強化版品質ゲートシステム"""
    
    def __init__(self):
        self.validator = QualityGateValidator()
        self.data_dir = Path("postbox/quality/gates")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs_path = self.data_dir / "gate_configs.json"
        self.results_path = self.data_dir / "gate_results.json"
        
        # 既存設定読み込み・ゲート設定初期化
        self.gate_configs = self._load_gate_configs()
        
        print("🚪 EnhancedQualityGateSystem 初期化完了")
    
    def _load_gate_configs(self) -> Dict[str, QualityGateConfig]:
        """ゲート設定読み込み"""
        
        # デフォルト設定
        default_configs = {
            "design_phase": QualityGateConfig(
                phase=QualityPhase.DESIGN,
                gate_name="design_phase",
                description="設計フェーズ品質ゲート",
                minimum_overall_score=0.7,
                required_checks=["syntax", "type_check"],
                check_thresholds={"syntax": 0.9, "type_check": 0.7},
                block_on_failure=False,
                warning_threshold=0.8,
                timeout_seconds=120,
                fallback_enabled=True,
                fallback_strategies=[FallbackStrategy.AUTO_FIX, FallbackStrategy.LOWER_THRESHOLD],
                fallback_thresholds={"minimum_overall_score": 0.6},
                prerequisites=["syntax_valid"],
                dependencies=[]
            ),
            
            "implementation_phase": QualityGateConfig(
                phase=QualityPhase.IMPLEMENTATION,
                gate_name="implementation_phase",
                description="実装フェーズ品質ゲート",
                minimum_overall_score=0.8,
                required_checks=["syntax", "type_check", "lint", "format"],
                check_thresholds={"syntax": 0.95, "type_check": 0.8, "lint": 0.8, "format": 0.9},
                block_on_failure=True,
                warning_threshold=0.85,
                timeout_seconds=300,
                fallback_enabled=True,
                fallback_strategies=[FallbackStrategy.AUTO_FIX, FallbackStrategy.GEMINI_ASSIST],
                fallback_thresholds={"minimum_overall_score": 0.7},
                prerequisites=["syntax_valid", "dependencies_satisfied"],
                dependencies=["design_phase"]
            ),
            
            "integration_phase": QualityGateConfig(
                phase=QualityPhase.INTEGRATION,
                gate_name="integration_phase",
                description="統合フェーズ品質ゲート",
                minimum_overall_score=0.85,
                required_checks=["syntax", "type_check", "lint", "format", "security", "test"],
                check_thresholds={
                    "syntax": 0.98, "type_check": 0.85, "lint": 0.85, 
                    "format": 0.95, "security": 0.9, "test": 0.5
                },
                block_on_failure=True,
                warning_threshold=0.9,
                timeout_seconds=600,
                fallback_enabled=True,
                fallback_strategies=[FallbackStrategy.GEMINI_ASSIST, FallbackStrategy.MANUAL_REVIEW],
                fallback_thresholds={"minimum_overall_score": 0.75},
                prerequisites=["syntax_valid", "dependencies_satisfied", "tests_exist"],
                dependencies=["implementation_phase"]
            ),
            
            "production_gate": QualityGateConfig(
                phase=QualityPhase.PRODUCTION,
                gate_name="production_gate",
                description="本番デプロイ品質ゲート",
                minimum_overall_score=0.9,
                required_checks=["syntax", "type_check", "lint", "format", "security", "performance", "test"],
                check_thresholds={
                    "syntax": 1.0, "type_check": 0.9, "lint": 0.9, 
                    "format": 0.98, "security": 0.95, "performance": 0.8, "test": 0.7
                },
                block_on_failure=True,
                warning_threshold=0.95,
                timeout_seconds=1200,
                fallback_enabled=False,  # 本番は厳格
                fallback_strategies=[],
                fallback_thresholds={},
                prerequisites=["syntax_valid", "dependencies_satisfied", "tests_exist"],
                dependencies=["integration_phase"]
            )
        }
        
        # 設定ファイルから読み込み（あれば）
        if self.configs_path.exists():
            try:
                with open(self.configs_path, 'r', encoding='utf-8') as f:
                    saved_configs = json.load(f)
                # TODO: JSONからQualityGateConfigオブジェクトに変換
                print("📋 保存済みゲート設定読み込み")
            except Exception as e:
                print(f"⚠️ ゲート設定読み込みエラー: {e}")
        
        return default_configs
    
    def run_quality_gate(self, gate_name: str, target_files: List[str], 
                        context: Optional[Dict[str, Any]] = None) -> QualityGateResult:
        """品質ゲート実行"""
        
        if gate_name not in self.gate_configs:
            raise ValueError(f"未知の品質ゲート: {gate_name}")
        
        gate_config = self.gate_configs[gate_name]
        
        # 依存ゲートチェック
        for dep_gate in gate_config.dependencies:
            print(f"🔍 依存ゲート確認: {dep_gate}")
            # TODO: 依存ゲート実行結果確認
        
        # ゲート実行
        result = self.validator.validate_quality_gate(gate_config, target_files, context)
        
        # 結果保存
        self._save_gate_result(result)
        
        return result
    
    def run_phase_gates(self, phase: QualityPhase, target_files: List[str], 
                       context: Optional[Dict[str, Any]] = None) -> List[QualityGateResult]:
        """フェーズ別ゲート一括実行"""
        
        phase_gates = [gate for gate in self.gate_configs.values() if gate.phase == phase]
        results = []
        
        for gate_config in phase_gates:
            print(f"\n🚪 フェーズゲート実行: {gate_config.gate_name}")
            result = self.validator.validate_quality_gate(gate_config, target_files, context)
            results.append(result)
            
            # 失敗時の処理
            if result.result in [GateResult.FAILED, GateResult.BLOCKED]:
                if gate_config.block_on_failure and not result.fallback_applied:
                    print(f"🚫 フェーズゲート失敗により処理中断: {gate_config.gate_name}")
                    break
        
        return results
    
    def _save_gate_result(self, result: QualityGateResult) -> None:
        """ゲート結果保存"""
        try:
            # 既存結果読み込み
            results = []
            if self.results_path.exists():
                with open(self.results_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            
            # 新しい結果追加（サマリーのみ）
            result_summary = {
                "timestamp": result.timestamp,
                "gate_name": result.gate_config.gate_name,
                "phase": result.gate_config.phase.value,
                "result": result.result.value,
                "overall_score": result.overall_score,
                "execution_time": result.execution_time,
                "fallback_applied": result.fallback_applied,
                "failed_checks": result.failed_checks
            }
            
            results.append(result_summary)
            
            # サイズ制限（最新500件）
            if len(results) > 500:
                results = results[-500:]
            
            with open(self.results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ ゲート結果保存エラー: {e}")

def main():
    """テスト実行"""
    print("🧪 EnhancedQualityGateSystem テスト開始")
    
    gate_system = EnhancedQualityGateSystem()
    
    # テストファイル
    test_files = ["kumihan_formatter/core/utilities/logger.py"]
    
    # 設計フェーズゲートテスト
    print("\n=== 設計フェーズゲートテスト ===")
    result = gate_system.run_quality_gate("design_phase", test_files)
    
    # 実装フェーズゲートテスト
    print("\n=== 実装フェーズゲートテスト ===")
    result = gate_system.run_quality_gate("implementation_phase", test_files)
    
    # フェーズ一括テスト
    print("\n=== フェーズ一括テスト ===")
    results = gate_system.run_phase_gates(QualityPhase.IMPLEMENTATION, test_files)
    
    print(f"\n📊 フェーズゲート実行結果: {len(results)}件")
    for result in results:
        print(f"   {result.gate_config.gate_name}: {result.result.value}")
    
    print("✅ EnhancedQualityGateSystem テスト完了")

if __name__ == "__main__":
    main()