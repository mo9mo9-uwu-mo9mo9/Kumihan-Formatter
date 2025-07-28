#!/usr/bin/env python3
"""
Performance Regression Monitor - Issue #640 Phase 3
パフォーマンス回帰ベンチマーク監視システム

目的: パフォーマンス回帰の自動検出・監視
- ベンチマークテスト実行
- パフォーマンス回帰検出
- メモリリーク検出
- CPUボトルネック分析
"""

import os
import sys
import time
import psutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
import gc
import tracemalloc
import cProfile
import pstats
import io
import tempfile

from scripts.tdd_system_base import TDDSystemBase, create_tdd_config, TDDSystemError
from scripts.secure_subprocess import secure_run
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

class PerformanceRisk(Enum):
    """パフォーマンスリスクレベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"

@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""
    test_name: str
    execution_time: float
    memory_usage: int
    cpu_usage: float
    iterations: int
    input_size: int
    throughput: float  # operations per second
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class PerformanceRegression:
    """パフォーマンス回帰"""
    test_name: str
    metric_name: str
    baseline_value: float
    current_value: float
    regression_percentage: float
    severity: PerformanceRisk
    description: str
    recommendation: str
    detected_at: datetime
    confidence_level: float

@dataclass
class MemoryLeak:
    """メモリリーク"""
    function_name: str
    leaked_memory: int
    leak_rate: float  # bytes per iteration
    iterations_tested: int
    confidence_level: float
    stack_trace: List[str]
    recommendation: str

@dataclass
class PerformanceTestResult:
    """パフォーマンステスト結果"""
    total_benchmarks: int
    benchmark_results: List[BenchmarkResult]
    regressions: List[PerformanceRegression]
    memory_leaks: List[MemoryLeak]
    performance_baselines: Dict[str, Dict[str, float]]
    system_info: Dict[str, Any]
    test_duration: float
    timestamp: datetime
    overall_risk: PerformanceRisk
    recommendations: List[str]

class PerformanceRegressionMonitor(TDDSystemBase):
    """パフォーマンス回帰ベンチマーク監視システム"""
    
    def __init__(self, project_root: Path):
        config = create_tdd_config(project_root)
        super().__init__(config)
        
        # ベンチマークデータディレクトリ
        self.benchmark_data_dir = project_root / ".benchmark_data"
        self.benchmark_data_dir.mkdir(exist_ok=True)
        
        # ベースラインファイル
        self.baseline_file = self.benchmark_data_dir / "performance_baselines.json"
        self.history_file = self.benchmark_data_dir / "benchmark_history.json"
        
        # システム情報取得
        self.system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            "memory_total": psutil.virtual_memory().total,
            "platform": sys.platform,
            "python_version": sys.version
        }
        
        # ベンチマークテスト定義
        self.benchmark_tests = [
            self._benchmark_startup_time,
            self._benchmark_file_processing,
            self._benchmark_memory_usage,
            self._benchmark_concurrent_operations,
            self._benchmark_large_input_handling,
            self._benchmark_io_operations,
            self._benchmark_cpu_intensive_tasks
        ]
        
        # 回帰検出設定
        self.regression_thresholds = {
            "execution_time": 0.15,    # 15%以上の劣化
            "memory_usage": 0.20,      # 20%以上の増加
            "cpu_usage": 0.25,         # 25%以上の増加
            "throughput": -0.10        # 10%以上の減少
        }
        
        self.benchmark_results = []
        self.regressions = []
        self.memory_leaks = []
        self.performance_baselines = {}
    
    def initialize(self) -> bool:
        """システム初期化"""
        logger.info("🔍 パフォーマンス回帰監視システム初期化中...")
        
        # ベースライン読み込み
        self._load_performance_baselines()
        
        # システムリソース確認
        memory = psutil.virtual_memory()
        if memory.available < 512 * 1024 * 1024:  # 512MB未満
            logger.warning(f"使用可能メモリが少ない: {memory.available / (1024**2):.1f}MB")
        
        # 事前条件確認
        issues = self.validate_preconditions()
        if issues:
            logger.error("初期化失敗:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("✅ パフォーマンス回帰監視システム初期化完了")
        return True
    
    def execute_main_operation(self) -> PerformanceTestResult:
        """パフォーマンス回帰監視実行"""
        logger.info("🚀 パフォーマンス回帰監視開始...")
        
        start_time = datetime.now()
        
        try:
            # ベンチマークテスト実行
            self._run_benchmark_tests()
            
            # 回帰検出
            self._detect_performance_regressions()
            
            # メモリリーク検出
            self._detect_memory_leaks()
            
            # 結果を分析
            result = self._analyze_results(start_time)
            
            # ベースライン更新
            self._update_performance_baselines()
            
            # レポート生成
            self._generate_performance_report(result)
            
            logger.info(f"✅ パフォーマンス回帰監視完了: {len(self.regressions)}件の回帰、{len(self.memory_leaks)}件のメモリリーク発見")
            return result
            
        except Exception as e:
            logger.error(f"パフォーマンス監視実行エラー: {e}")
            raise TDDSystemError(f"監視実行失敗: {e}")
    
    def _load_performance_baselines(self):
        """パフォーマンスベースライン読み込み"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    self.performance_baselines = json.load(f)
                logger.info(f"ベースライン読み込み完了: {len(self.performance_baselines)}テスト")
            except Exception as e:
                logger.warning(f"ベースライン読み込みエラー: {e}")
    
    def _run_benchmark_tests(self):
        """ベンチマークテスト実行"""
        logger.info("⚡ ベンチマークテスト実行中...")
        
        total_tests = len(self.benchmark_tests)
        
        for i, benchmark_test in enumerate(self.benchmark_tests, 1):
            test_name = benchmark_test.__name__
            logger.info(f"[{i}/{total_tests}] {test_name} 実行中...")
            
            try:
                # システムリソース状態をリセット
                gc.collect()
                
                # ベンチマーク実行
                start_time = time.time()
                result = benchmark_test()
                duration = time.time() - start_time
                
                if result:
                    result.execution_time = duration
                    result.timestamp = datetime.now()
                    self.benchmark_results.append(result)
                    
                    logger.debug(f"✅ {test_name} 完了: {duration:.3f}s, {result.memory_usage/1024/1024:.1f}MB")
                else:
                    logger.warning(f"❌ {test_name} 失敗")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} 例外: {e}")
        
        logger.info(f"ベンチマークテスト完了: {len(self.benchmark_results)}/{total_tests}")
    
    def _benchmark_startup_time(self) -> Optional[BenchmarkResult]:
        """起動時間ベンチマーク"""
        try:
            iterations = 5
            times = []
            
            for _ in range(iterations):
                start_time = time.time()
                # プロジェクトの主要モジュールをインポート
                result = subprocess.run([
                    sys.executable, '-c',
                    'import sys; sys.path.insert(0, "."); import kumihan_formatter; print("OK")'
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                else:
                    logger.warning(f"起動テスト失敗: {result.stderr}")
            
            if times:
                avg_time = statistics.mean(times)
                process = psutil.Process()
                memory_info = process.memory_info()
                
                return BenchmarkResult(
                    test_name="startup_time",
                    execution_time=avg_time,
                    memory_usage=memory_info.rss,
                    cpu_usage=process.cpu_percent(),
                    iterations=iterations,
                    input_size=0,
                    throughput=1.0 / avg_time,
                    timestamp=datetime.now(),
                    metadata={"times": times, "std_dev": statistics.stdev(times) if len(times) > 1 else 0}
                )
                
        except Exception as e:
            logger.error(f"起動時間ベンチマークエラー: {e}")
            
        return None
    
    def _benchmark_file_processing(self) -> Optional[BenchmarkResult]:
        """ファイル処理ベンチマーク"""
        try:
            # テスト用ファイル作成
            test_content = "テストコンテンツ\n" * 1000
            iterations = 10
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(test_content)
                temp_path = Path(temp_file.name)
            
            try:
                times = []
                memory_usage_before = psutil.Process().memory_info().rss
                
                for _ in range(iterations):
                    start_time = time.time()
                    
                    # ファイル読み書き処理
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    processed = content.upper()
                    
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(processed)
                    
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                
                memory_usage_after = psutil.Process().memory_info().rss
                memory_delta = memory_usage_after - memory_usage_before
                
                if times:
                    avg_time = statistics.mean(times)
                    file_size = temp_path.stat().st_size
                    
                    return BenchmarkResult(
                        test_name="file_processing",
                        execution_time=avg_time,
                        memory_usage=max(memory_delta, 0),
                        cpu_usage=psutil.Process().cpu_percent(),
                        iterations=iterations,
                        input_size=file_size,
                        throughput=file_size / avg_time,
                        timestamp=datetime.now(),
                        metadata={"file_size": file_size, "times": times}
                    )
                    
            finally:
                temp_path.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"ファイル処理ベンチマークエラー: {e}")
            
        return None
    
    def _benchmark_memory_usage(self) -> Optional[BenchmarkResult]:
        """メモリ使用量ベンチマーク"""
        try:
            tracemalloc.start()
            initial_memory = psutil.Process().memory_info().rss
            
            # メモリ集約的なタスク
            data_structures = []
            iterations = 1000
            
            start_time = time.time()
            
            for i in range(iterations):
                # 様々なデータ構造を作成
                data = {
                    'list': list(range(100)),
                    'dict': {f'key_{j}': f'value_{j}' for j in range(50)},
                    'string': 'x' * 100,
                    'tuple': tuple(range(50))
                }
                data_structures.append(data)
                
                # 定期的にメモリ使用量チェック
                if i % 100 == 0:
                    gc.collect()
            
            execution_time = time.time() - start_time
            
            # 最終メモリ使用量
            final_memory = psutil.Process().memory_info().rss
            memory_delta = final_memory - initial_memory
            
            # メモリ統計取得
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # クリーンアップ
            data_structures.clear()
            gc.collect()
            
            return BenchmarkResult(
                test_name="memory_usage",
                execution_time=execution_time,
                memory_usage=memory_delta,
                cpu_usage=psutil.Process().cpu_percent(),
                iterations=iterations,
                input_size=iterations * 4,  # 4 data structures per iteration
                throughput=iterations / execution_time,
                timestamp=datetime.now(),
                metadata={
                    "peak_memory": peak_memory,
                    "current_memory": current_memory,
                    "initial_rss": initial_memory,
                    "final_rss": final_memory
                }
            )
            
        except Exception as e:
            logger.error(f"メモリ使用量ベンチマークエラー: {e}")
            if tracemalloc.is_tracing():
                tracemalloc.stop()
                
        return None
    
    def _benchmark_concurrent_operations(self) -> Optional[BenchmarkResult]:
        """並行処理ベンチマーク"""
        try:
            thread_count = 4
            operations_per_thread = 250
            results = []
            errors = []
            
            def worker_task(task_id):
                try:
                    start_time = time.time()
                    # CPU集約的タスク
                    result = sum(i * i for i in range(1000))
                    elapsed = time.time() - start_time
                    results.append((task_id, result, elapsed))
                except Exception as e:
                    errors.append((task_id, str(e)))
            
            # 並行実行
            start_time = time.time()
            initial_memory = psutil.Process().memory_info().rss
            
            threads = []
            for i in range(thread_count):
                thread = threading.Thread(target=worker_task, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 全スレッド完了待機
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            final_memory = psutil.Process().memory_info().rss
            
            if len(results) == thread_count and not errors:
                return BenchmarkResult(
                    test_name="concurrent_operations",
                    execution_time=total_time,
                    memory_usage=final_memory - initial_memory,
                    cpu_usage=psutil.Process().cpu_percent(),
                    iterations=thread_count,
                    input_size=operations_per_thread,
                    throughput=thread_count / total_time,
                    timestamp=datetime.now(),
                    metadata={
                        "thread_count": thread_count,
                        "operations_per_thread": operations_per_thread,
                        "worker_times": [r[2] for r in results],
                        "errors": errors
                    }
                )
            else:
                logger.warning(f"並行処理テスト失敗: {len(errors)}エラー")
                
        except Exception as e:
            logger.error(f"並行処理ベンチマークエラー: {e}")
            
        return None
    
    def _benchmark_large_input_handling(self) -> Optional[BenchmarkResult]:
        """大入力処理ベンチマーク"""
        try:
            # 大きなデータセット作成
            large_data = list(range(100000))
            iterations = 5
            
            times = []
            initial_memory = psutil.Process().memory_info().rss
            
            for _ in range(iterations):
                start_time = time.time()
                
                # データ処理操作
                filtered_data = [x for x in large_data if x % 2 == 0]
                sorted_data = sorted(filtered_data, reverse=True)
                result_sum = sum(sorted_data[:1000])
                
                elapsed = time.time() - start_time
                times.append(elapsed)
            
            final_memory = psutil.Process().memory_info().rss
            
            if times:
                avg_time = statistics.mean(times)
                
                return BenchmarkResult(
                    test_name="large_input_handling",
                    execution_time=avg_time,
                    memory_usage=final_memory - initial_memory,
                    cpu_usage=psutil.Process().cpu_percent(),
                    iterations=iterations,
                    input_size=len(large_data),
                    throughput=len(large_data) / avg_time,
                    timestamp=datetime.now(),
                    metadata={
                        "input_size": len(large_data),
                        "times": times,
                        "processed_items": len(large_data)
                    }
                )
                
        except Exception as e:
            logger.error(f"大入力処理ベンチマークエラー: {e}")
            
        return None
    
    def _benchmark_io_operations(self) -> Optional[BenchmarkResult]:
        """I/O操作ベンチマーク"""
        try:
            iterations = 20
            file_size = 1024 * 10  # 10KB
            test_data = b'x' * file_size
            
            times = []
            initial_memory = psutil.Process().memory_info().rss
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                for i in range(iterations):
                    test_file = temp_path / f"test_{i}.dat"
                    
                    start_time = time.time()
                    
                    # 書き込み
                    with open(test_file, 'wb') as f:
                        f.write(test_data)
                    
                    # 読み込み
                    with open(test_file, 'rb') as f:
                        read_data = f.read()
                    
                    # 検証
                    assert len(read_data) == file_size
                    
                    elapsed = time.time() - start_time
                    times.append(elapsed)
            
            final_memory = psutil.Process().memory_info().rss
            
            if times:
                avg_time = statistics.mean(times)
                total_bytes = file_size * iterations * 2  # read + write
                
                return BenchmarkResult(
                    test_name="io_operations",
                    execution_time=avg_time,
                    memory_usage=final_memory - initial_memory,
                    cpu_usage=psutil.Process().cpu_percent(),
                    iterations=iterations,
                    input_size=file_size,
                    throughput=total_bytes / (avg_time * iterations),
                    timestamp=datetime.now(),
                    metadata={
                        "file_size": file_size,
                        "total_bytes": total_bytes,
                        "times": times
                    }
                )
                
        except Exception as e:
            logger.error(f"I/O操作ベンチマークエラー: {e}")
            
        return None
    
    def _benchmark_cpu_intensive_tasks(self) -> Optional[BenchmarkResult]:
        """CPU集約的タスクベンチマーク"""
        try:
            iterations = 3
            times = []
            initial_memory = psutil.Process().memory_info().rss
            
            for _ in range(iterations):
                start_time = time.time()
                
                # CPU集約的計算
                result = 0
                for i in range(100000):
                    result += i ** 2
                    if i % 1000 == 0:
                        result = result % (10**9 + 7)  # オーバーフロー防止
                
                elapsed = time.time() - start_time
                times.append(elapsed)
            
            final_memory = psutil.Process().memory_info().rss
            
            if times:
                avg_time = statistics.mean(times)
                operations = 100000
                
                return BenchmarkResult(
                    test_name="cpu_intensive_tasks",
                    execution_time=avg_time,
                    memory_usage=final_memory - initial_memory,
                    cpu_usage=psutil.Process().cpu_percent(),
                    iterations=iterations,
                    input_size=operations,
                    throughput=operations / avg_time,
                    timestamp=datetime.now(),
                    metadata={
                        "operations": operations,
                        "times": times,
                        "result": result
                    }
                )
                
        except Exception as e:
            logger.error(f"CPU集約的タスクベンチマークエラー: {e}")
            
        return None
    
    def _detect_performance_regressions(self):
        """パフォーマンス回帰検出"""
        logger.info("📉 パフォーマンス回帰検出中...")
        
        for result in self.benchmark_results:
            test_name = result.test_name
            
            if test_name in self.performance_baselines:
                baseline = self.performance_baselines[test_name]
                
                # 各メトリクスについて回帰チェック
                metrics_to_check = {
                    "execution_time": (result.execution_time, baseline.get("execution_time")),
                    "memory_usage": (result.memory_usage, baseline.get("memory_usage")),
                    "cpu_usage": (result.cpu_usage, baseline.get("cpu_usage")),
                    "throughput": (result.throughput, baseline.get("throughput"))
                }
                
                for metric_name, (current_value, baseline_value) in metrics_to_check.items():
                    if baseline_value is not None and baseline_value > 0:
                        regression = self._calculate_regression(
                            metric_name, current_value, baseline_value, test_name
                        )
                        
                        if regression:
                            self.regressions.append(regression)
    
    def _calculate_regression(self, metric_name: str, current: float, baseline: float, test_name: str) -> Optional[PerformanceRegression]:
        """回帰計算"""
        threshold = self.regression_thresholds.get(metric_name, 0.15)
        
        if metric_name == "throughput":
            # スループットは低下が問題
            regression_pct = (baseline - current) / baseline
            is_regression = regression_pct > -threshold  # 負の閾値なので不等号逆転
        else:
            # その他は増加が問題
            regression_pct = (current - baseline) / baseline  
            is_regression = regression_pct > threshold
        
        if is_regression:
            severity = self._assess_regression_severity(abs(regression_pct))
            
            return PerformanceRegression(
                test_name=test_name,
                metric_name=metric_name,
                baseline_value=baseline,
                current_value=current,
                regression_percentage=regression_pct * 100,
                severity=severity,
                description=f"{test_name}の{metric_name}が{abs(regression_pct)*100:.1f}%悪化",
                recommendation=self._generate_regression_recommendation(metric_name, regression_pct),
                detected_at=datetime.now(),
                confidence_level=self._calculate_confidence_for_regression(test_name, metric_name)
            )
        
        return None
    
    def _calculate_confidence_for_regression(self, test_name: str, metric_name: str) -> float:
        """回帰の信頼度を計算"""
        # 該当テストの過去の測定値を収集
        measurements = []
        for result in self.benchmark_results:
            if result.test_name == test_name:
                if metric_name == "execution_time":
                    measurements.append(result.execution_time)
                elif metric_name == "memory_usage":
                    measurements.append(result.memory_usage)
                elif metric_name == "cpu_usage":
                    measurements.append(result.cpu_usage)
                elif metric_name == "throughput":
                    measurements.append(result.throughput)
        
        if test_name in self.performance_baselines and metric_name in self.performance_baselines[test_name]:
            baseline = self.performance_baselines[test_name][metric_name]
            threshold = self.regression_thresholds.get(metric_name, 0.15)
            return calculate_regression_confidence(measurements, baseline, threshold)
        
        return 0.5  # デフォルト値
    
    def _assess_regression_severity(self, regression_pct: float) -> PerformanceRisk:
        """回帰重要度評価"""
        if regression_pct >= 0.50:  # 50%以上
            return PerformanceRisk.CRITICAL
        elif regression_pct >= 0.30:  # 30%以上
            return PerformanceRisk.HIGH
        elif regression_pct >= 0.15:  # 15%以上
            return PerformanceRisk.MEDIUM
        else:
            return PerformanceRisk.LOW
    
    def _generate_regression_recommendation(self, metric_name: str, regression_pct: float) -> str:
        """回帰推奨事項生成"""
        recommendations = {
            "execution_time": "実行時間が増加しています。プロファイリングを実行してボトルネックを特定してください。",
            "memory_usage": "メモリ使用量が増加しています。メモリリークの可能性を調査してください。",
            "cpu_usage": "CPU使用率が増加しています。アルゴリズムの最適化を検討してください。",
            "throughput": "スループットが低下しています。並列処理や最適化の見直しを検討してください。"
        }
        
        base_rec = recommendations.get(metric_name, "パフォーマンスが悪化しています。")
        
        if abs(regression_pct) > 0.3:
            base_rec += " 重大な回帰のため、即座の対応が必要です。"
        
        return base_rec
    
    def _detect_memory_leaks(self):
        """メモリリーク検出"""
        logger.info("🔍 メモリリーク検出中...")
        
        # メモリリーク検出テスト
        leak_test_functions = [
            self._test_for_memory_leak_in_file_operations,
            self._test_for_memory_leak_in_data_structures
        ]
        
        for test_func in leak_test_functions:
            try:
                leak = test_func()
                if leak:
                    self.memory_leaks.append(leak)
            except Exception as e:
                logger.warning(f"メモリリーク検出エラー {test_func.__name__}: {e}")
    
    def _test_for_memory_leak_in_file_operations(self) -> Optional[MemoryLeak]:
        """ファイル操作でのメモリリークテスト"""
        try:
            tracemalloc.start()
            initial_memory = psutil.Process().memory_info().rss
            
            iterations = 100
            memory_samples = []
            
            for i in range(iterations):
                # ファイル操作実行
                with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
                    temp_file.write("test data " * 100)
                    temp_file.flush()
                
                # 定期的にメモリ測定
                if i % 10 == 0:
                    current_memory = psutil.Process().memory_info().rss
                    memory_samples.append((i, current_memory))
            
            final_memory = psutil.Process().memory_info().rss
            tracemalloc.stop()
            
            # メモリリーク判定
            memory_increase = final_memory - initial_memory
            leak_threshold = 1024 * 1024  # 1MB
            
            if memory_increase > leak_threshold:
                leak_rate = memory_increase / iterations
                
                return MemoryLeak(
                    function_name="file_operations",
                    leaked_memory=memory_increase,
                    leak_rate=leak_rate,
                    iterations_tested=iterations,
                    confidence_level=calculate_memory_leak_confidence(
                        memory_samples, iterations
                    ),
                    stack_trace=[],
                    recommendation="ファイル操作後のリソース解放を確認してください。with文の使用を推奨します。"
                )
                
        except Exception as e:
            logger.debug(f"ファイル操作メモリリークテストエラー: {e}")
            if tracemalloc.is_tracing():
                tracemalloc.stop()
        
        return None
    
    def _test_for_memory_leak_in_data_structures(self) -> Optional[MemoryLeak]:
        """データ構造でのメモリリークテスト"""
        try:
            tracemalloc.start()
            initial_memory = psutil.Process().memory_info().rss
            
            iterations = 200
            data_holder = []
            
            for i in range(iterations):
                # データ構造作成
                data = {
                    'id': i,
                    'data': list(range(100)),
                    'metadata': {'created': datetime.now()}
                }
                data_holder.append(data)
                
                # 古いデータを削除（本来なら）
                if len(data_holder) > 50:
                    data_holder.pop(0)
            
            final_memory = psutil.Process().memory_info().rss
            tracemalloc.stop()
            
            # メモリリーク判定
            memory_increase = final_memory - initial_memory
            expected_memory = len(data_holder) * 1000  # 概算
            
            if memory_increase > expected_memory * 2:  # 期待値の2倍以上
                leak_rate = memory_increase / iterations
                
                return MemoryLeak(
                    function_name="data_structures",
                    leaked_memory=memory_increase,
                    leak_rate=leak_rate,
                    iterations_tested=iterations,
                    confidence_level=calculate_memory_leak_confidence(
                        [(i, m) for i, m in enumerate([initial_memory, final_memory])],
                        iterations
                    ),
                    stack_trace=[],
                    recommendation="循環参照や不要なオブジェクト参照がないか確認してください。"
                )
                
        except Exception as e:
            logger.debug(f"データ構造メモリリークテストエラー: {e}")
            if tracemalloc.is_tracing():
                tracemalloc.stop()
        
        return None
    
    def _analyze_results(self, start_time: datetime) -> PerformanceTestResult:
        """結果分析"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 全体リスクレベル決定
        overall_risk = self._calculate_overall_performance_risk()
        
        # 推奨事項生成
        recommendations = self._generate_performance_recommendations()
        
        return PerformanceTestResult(
            total_benchmarks=len(self.benchmark_results),
            benchmark_results=self.benchmark_results,
            regressions=self.regressions,
            memory_leaks=self.memory_leaks,
            performance_baselines=self.performance_baselines,
            system_info=self.system_info,
            test_duration=duration,
            timestamp=end_time,
            overall_risk=overall_risk,
            recommendations=recommendations
        )
    
    def _calculate_overall_performance_risk(self) -> PerformanceRisk:
        """全体パフォーマンスリスクレベル計算"""
        if not self.regressions and not self.memory_leaks:
            return PerformanceRisk.SAFE
        
        risk_items = []
        risk_items.extend([r.severity for r in self.regressions])
        
        # メモリリークは高リスク扱い
        for leak in self.memory_leaks:
            if leak.leaked_memory > 10 * 1024 * 1024:  # 10MB以上
                risk_items.append(PerformanceRisk.HIGH)
            else:
                risk_items.append(PerformanceRisk.MEDIUM)
        
        if PerformanceRisk.CRITICAL in risk_items:
            return PerformanceRisk.CRITICAL
        elif PerformanceRisk.HIGH in risk_items:
            return PerformanceRisk.HIGH
        elif PerformanceRisk.MEDIUM in risk_items:
            return PerformanceRisk.MEDIUM
        else:
            return PerformanceRisk.LOW
    
    def _generate_performance_recommendations(self) -> List[str]:
        """パフォーマンス推奨事項生成"""
        recommendations = [
            "定期的なパフォーマンスベンチマークの実行",
            "プロファイリングツール（cProfile, memory_profiler）の活用",
            "メモリ使用量の継続的監視",
            "ボトルネック箇所の特定と最適化",
            "パフォーマンステストの自動化",
            "CI/CDパイプラインでのパフォーマンス回帰検出",
        ]
        
        if self.regressions:
            recommendations.extend([
                "発見されたパフォーマンス回帰を優先度に応じて修正する",
                "回帰の根本原因を調査し、再発防止策を実装する"
            ])
        
        if self.memory_leaks:
            recommendations.extend([
                "メモリリークの修正を最優先で実施する",
                "リソース管理（with文、明示的なclose()）の徹底"
            ])
        
        return recommendations
    
    def _update_performance_baselines(self):
        """パフォーマンスベースライン更新"""
        logger.info("📊 パフォーマンスベースライン更新中...")
        
        for result in self.benchmark_results:
            test_name = result.test_name
            
            baseline_data = {
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "cpu_usage": result.cpu_usage,
                "throughput": result.throughput,
                "last_updated": result.timestamp.isoformat(),
                "iterations": result.iterations,
                "input_size": result.input_size
            }
            
            if test_name in self.performance_baselines:
                # 既存ベースラインを更新（移動平均）
                old_baseline = self.performance_baselines[test_name]
                alpha = 0.2  # 重み
                
                for metric in ["execution_time", "memory_usage", "cpu_usage", "throughput"]:
                    if metric in old_baseline:
                        old_value = old_baseline[metric]
                        new_value = baseline_data[metric]
                        baseline_data[metric] = alpha * new_value + (1 - alpha) * old_value
            
            self.performance_baselines[test_name] = baseline_data
        
        # ベースライン保存
        try:
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_baselines, f, indent=2, ensure_ascii=False)
            logger.info("✅ パフォーマンスベースライン更新完了")
        except Exception as e:
            logger.error(f"ベースライン保存エラー: {e}")
    
    def _generate_performance_report(self, result: PerformanceTestResult):
        """パフォーマンスレポート生成"""
        report_file = self.project_root / "performance_regression_report.json"
        
        report_data = {
            "summary": {
                "total_benchmarks": result.total_benchmarks,
                "regressions_found": len(result.regressions),
                "memory_leaks_found": len(result.memory_leaks),
                "overall_risk": result.overall_risk.value,
                "test_duration": result.test_duration,
                "timestamp": result.timestamp.isoformat(),
                "system_info": result.system_info
            },
            "benchmark_results": [
                {
                    "test_name": r.test_name,
                    "execution_time": r.execution_time,
                    "memory_usage": r.memory_usage,
                    "cpu_usage": r.cpu_usage,
                    "throughput": r.throughput,
                    "iterations": r.iterations,
                    "input_size": r.input_size,
                    "timestamp": r.timestamp.isoformat(),
                    "metadata": r.metadata
                }
                for r in result.benchmark_results
            ],
            "performance_regressions": [
                {
                    "test_name": reg.test_name,
                    "metric_name": reg.metric_name,
                    "baseline_value": reg.baseline_value,
                    "current_value": reg.current_value,
                    "regression_percentage": reg.regression_percentage,
                    "severity": reg.severity.value,
                    "description": reg.description,
                    "recommendation": reg.recommendation,
                    "confidence_level": reg.confidence_level,
                    "detected_at": reg.detected_at.isoformat()
                }
                for reg in result.regressions
            ],
            "memory_leaks": [
                {
                    "function_name": leak.function_name,
                    "leaked_memory": leak.leaked_memory,
                    "leak_rate": leak.leak_rate,
                    "iterations_tested": leak.iterations_tested,
                    "confidence_level": leak.confidence_level,
                    "recommendation": leak.recommendation
                }
                for leak in result.memory_leaks
            ],
            "baselines": result.performance_baselines,
            "recommendations": result.recommendations,
            "risk_distribution": self._get_performance_risk_distribution(result.regressions)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 パフォーマンス回帰レポート生成: {report_file}")
    
    def _get_performance_risk_distribution(self, regressions: List[PerformanceRegression]) -> Dict[str, int]:
        """パフォーマンスリスク分布取得"""
        distribution = {}
        for regression in regressions:
            risk = regression.severity.value
            distribution[risk] = distribution.get(risk, 0) + 1
        return distribution

def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent
    
    logger.info("🚀 パフォーマンス回帰監視開始")
    
    try:
        with PerformanceRegressionMonitor(project_root) as monitor:
            result = monitor.run()
            
            # 結果サマリー表示
            logger.info("📊 パフォーマンス回帰監視結果サマリー:")
            logger.info(f"  実行ベンチマーク数: {result.total_benchmarks}")
            logger.info(f"  検出された回帰: {len(result.regressions)}件")
            logger.info(f"  メモリリーク: {len(result.memory_leaks)}件")
            logger.info(f"  全体リスクレベル: {result.overall_risk.value}")
            logger.info(f"  実行時間: {result.test_duration:.2f}秒")
            
            # システム情報
            logger.info("💻 システム情報:")
            logger.info(f"  CPU: {result.system_info['cpu_count']}コア")
            logger.info(f"  メモリ: {result.system_info['memory_total'] / (1024**3):.1f}GB")
            logger.info(f"  プラットフォーム: {result.system_info['platform']}")
            
            # ベンチマーク結果
            if result.benchmark_results:
                logger.info("⚡ベンチマーク結果:")
                for bench in result.benchmark_results:
                    logger.info(f"  {bench.test_name}: {bench.execution_time:.3f}s, {bench.memory_usage/1024/1024:.1f}MB")
            
            # 重要な回帰を表示
            critical_regressions = [r for r in result.regressions 
                                  if r.severity in [PerformanceRisk.CRITICAL, PerformanceRisk.HIGH]]
            
            if critical_regressions:
                logger.warning(f"🚨 高リスクパフォーマンス回帰 {len(critical_regressions)}件:")
                for reg in critical_regressions[:5]:  # 上位5件表示
                    logger.warning(f"  - {reg.test_name}.{reg.metric_name}: {reg.regression_percentage:+.1f}% ({reg.severity.value})")
            
            # メモリリーク情報
            if result.memory_leaks:
                logger.warning(f"🔍 メモリリーク検出: {len(result.memory_leaks)}件")
                for leak in result.memory_leaks:
                    logger.warning(f"  - {leak.function_name}: {leak.leaked_memory/1024/1024:.1f}MB リーク")
            
            return 0 if result.overall_risk in [PerformanceRisk.SAFE, PerformanceRisk.LOW] else 1
            
    except Exception as e:
        logger.error(f"💥 パフォーマンス回帰監視実行エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())