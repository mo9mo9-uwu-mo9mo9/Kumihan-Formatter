#!/usr/bin/env python3
"""
Performance Benchmark Script - Phase 4-10最終検証システム
全システムのパフォーマンス測定・ベンチマーク実行

Phase 4-8で達成した性能指標の再検証:
- 入力検証: 17,241 inputs/sec目標
- データサニタイズ: 58,987 ops/sec目標
- 監査ログ: 4,443 events/sec目標
- メモリ使用量・CPU使用率測定
- レスポンス時間・スループット測定
"""

import gc
import json
import os
import statistics
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from kumihan_formatter.core.logging.audit_logger import AuditLogger
    from kumihan_formatter.core.logging.structured_logger import get_structured_logger
    from kumihan_formatter.core.rendering.main_renderer import MainRenderer
    from kumihan_formatter.core.security.input_validation import SecureInputValidator
    from kumihan_formatter.core.security.sanitizer import DataSanitizer
    from kumihan_formatter.core.utilities.logger import get_logger
    from kumihan_formatter.parser import KumihanParser
except ImportError as e:
    print(f"❌ Critical: Failed to import required modules: {e}")
    sys.exit(1)


class PerformanceBenchmark:
    """パフォーマンスベンチマーク実行クラス"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.structured_logger = get_structured_logger("performance_benchmark")
        self.process = psutil.Process()

        # Phase 4-8目標値（実際の実装で達成した値）
        self.performance_targets = {
            "input_validation_ops_per_sec": 17241,
            "data_sanitization_ops_per_sec": 58987,
            "audit_logging_events_per_sec": 4443,
            "structured_logging_ops_per_sec": 1000,
            "parsing_chars_per_sec": 500000,
            "rendering_elements_per_sec": 10000,
            "memory_usage_limit_mb": 512,
            "cpu_usage_limit_percent": 80,
        }

        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "phase": "Phase 4-10 Performance Benchmark",
            "targets": self.performance_targets,
            "benchmarks": {},
            "summary": {
                "total_benchmarks": 0,
                "passed_benchmarks": 0,
                "failed_benchmarks": 0,
                "overall_performance_score": 0.0,
            },
            "system_info": self._collect_system_info(),
        }

    def _collect_system_info(self) -> Dict[str, Any]:
        """システム情報収集"""
        try:
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            memory = psutil.virtual_memory()

            return {
                "cpu_physical_cores": cpu_count,
                "cpu_logical_cores": cpu_count_logical,
                "total_memory_gb": round(memory.total / (1024**3), 2),
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "memory_usage_percent": memory.percent,
                "platform": sys.platform,
                "python_version": sys.version.split()[0],
            }
        except Exception as e:
            return {"error": str(e)}

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """全ベンチマーク実行"""
        self.logger.info("⚡ Starting Performance Benchmark Suite...")
        self.structured_logger.info(
            "Performance benchmark initiated",
            extra={"phase": "4-10", "benchmark_type": "comprehensive"},
        )

        benchmark_methods = [
            ("input_validation", self._benchmark_input_validation),
            ("data_sanitization", self._benchmark_data_sanitization),
            ("audit_logging", self._benchmark_audit_logging),
            ("structured_logging", self._benchmark_structured_logging),
            ("kumihan_parsing", self._benchmark_kumihan_parsing),
            ("html_rendering", self._benchmark_html_rendering),
            ("memory_performance", self._benchmark_memory_performance),
            ("concurrent_operations", self._benchmark_concurrent_operations),
            ("system_resources", self._benchmark_system_resources),
        ]

        for benchmark_name, benchmark_method in benchmark_methods:
            try:
                self.logger.info(f"⚡ Running benchmark: {benchmark_name}")

                # ガベージコレクションでクリーンな状態に
                gc.collect()

                result = benchmark_method()
                self.results["benchmarks"][benchmark_name] = result

                # 統計更新
                self.results["summary"]["total_benchmarks"] += 1
                if result.get("target_achieved", False):
                    self.results["summary"]["passed_benchmarks"] += 1
                else:
                    self.results["summary"]["failed_benchmarks"] += 1

            except Exception as e:
                self.logger.error(f"❌ Benchmark {benchmark_name} failed: {e}")
                self.results["benchmarks"][benchmark_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
                self.results["summary"]["total_benchmarks"] += 1
                self.results["summary"]["failed_benchmarks"] += 1

        # 総合パフォーマンススコア計算
        self._calculate_overall_score()

        self._save_results()
        self._print_summary()

        return self.results

    def _benchmark_input_validation(self) -> Dict[str, Any]:
        """入力検証パフォーマンステスト"""
        validator = SecureInputValidator()
        target = self.performance_targets["input_validation_ops_per_sec"]

        # テストデータ準備
        test_inputs = (
            [f"test_file_{i}.txt" for i in range(1000)]
            + [f"path/to/file_{i}.log" for i in range(1000)]
            + [f"../dangerous_path_{i}" for i in range(100)]  # 危険なパス
        )

        # ウォームアップ
        for i in range(100):
            validator.validate_file_path(test_inputs[i])

        # 実際の計測
        iterations = len(test_inputs)
        start_memory = self.process.memory_info().rss
        start_time = time.perf_counter()

        for test_input in test_inputs:
            validator.validate_file_path(test_input)

        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss

        duration = end_time - start_time
        ops_per_sec = iterations / duration
        memory_delta_mb = (end_memory - start_memory) / (1024 * 1024)

        return {
            "ops_per_sec": round(ops_per_sec, 2),
            "target": target,
            "target_achieved": ops_per_sec >= target * 0.8,  # 80%以上で達成とみなす
            "duration_seconds": round(duration, 4),
            "iterations": iterations,
            "memory_delta_mb": round(memory_delta_mb, 2),
            "efficiency_ratio": round(ops_per_sec / target, 3),
        }

    def _benchmark_data_sanitization(self) -> Dict[str, Any]:
        """データサニタイゼーションパフォーマンステスト"""
        sanitizer = DataSanitizer()
        target = self.performance_targets["data_sanitization_ops_per_sec"]

        # テストデータ準備
        test_html = (
            '<script>alert("xss")</script><p>Normal content</p><div>More content</div>'
        )
        test_sql = "'; DROP TABLE users; SELECT * FROM sensitive_data; --"
        test_json = {
            "password": "secret123",
            "api_key": "key_abc123",
            "data": "normal content",
        }

        test_data = [
            ("html", test_html),
            ("sql", test_sql),
            ("json", test_json),
        ] * 1000  # 3,000 operations total

        # ウォームアップ
        for i in range(100):
            data_type, data = test_data[i]
            if data_type == "html":
                sanitizer.sanitize_html(data)
            elif data_type == "sql":
                sanitizer.escape_sql_input(data)
            else:
                sanitizer.sanitize_json_for_logging(data)

        # 実際の計測
        iterations = len(test_data)
        start_time = time.perf_counter()

        for data_type, data in test_data:
            if data_type == "html":
                sanitizer.sanitize_html(data)
            elif data_type == "sql":
                sanitizer.escape_sql_input(data)
            else:
                sanitizer.sanitize_json_for_logging(data)

        end_time = time.perf_counter()

        duration = end_time - start_time
        ops_per_sec = iterations / duration

        return {
            "ops_per_sec": round(ops_per_sec, 2),
            "target": target,
            "target_achieved": ops_per_sec >= target * 0.8,
            "duration_seconds": round(duration, 4),
            "iterations": iterations,
            "efficiency_ratio": round(ops_per_sec / target, 3),
        }

    def _benchmark_audit_logging(self) -> Dict[str, Any]:
        """監査ログパフォーマンステスト"""
        audit_logger = AuditLogger()
        target = self.performance_targets["audit_logging_events_per_sec"]

        # テストイベント準備
        test_events = [
            ("file_operation", f"test_file_{i}.txt", {"action": "read"}),
            ("security_event", f"auth_attempt_{i}", {"user": f"user_{i}"}),
            ("system_event", f"system_op_{i}", {"component": "test"}),
            ("compliance_event", f"compliance_{i}", {"regulation": "test_reg"}),
        ] * 250  # 1,000 events total

        # ウォームアップ
        for i in range(50):
            event_type, event_name, details = test_events[i]
            if event_type == "file_operation":
                audit_logger.log_file_operation(
                    event_name, "read", success=True, metadata=details
                )
            elif event_type == "security_event":
                audit_logger.log_security_event(
                    "test", event_name, success=True, details=details
                )
            elif event_type == "system_event":
                audit_logger.log_system_event("test", event_name, details=details)
            else:
                audit_logger.log_compliance_event(
                    "test", event_name, success=True, details=details
                )

        # 実際の計測
        iterations = len(test_events)
        start_time = time.perf_counter()

        for event_type, event_name, details in test_events:
            if event_type == "file_operation":
                audit_logger.log_file_operation(
                    event_name, "read", success=True, metadata=details
                )
            elif event_type == "security_event":
                audit_logger.log_security_event(
                    "test", event_name, success=True, details=details
                )
            elif event_type == "system_event":
                audit_logger.log_system_event("test", event_name, details=details)
            else:
                audit_logger.log_compliance_event(
                    "test", event_name, success=True, details=details
                )

        end_time = time.perf_counter()

        duration = end_time - start_time
        events_per_sec = iterations / duration

        return {
            "events_per_sec": round(events_per_sec, 2),
            "target": target,
            "target_achieved": events_per_sec >= target * 0.8,
            "duration_seconds": round(duration, 4),
            "iterations": iterations,
            "efficiency_ratio": round(events_per_sec / target, 3),
        }

    def _benchmark_structured_logging(self) -> Dict[str, Any]:
        """構造化ログパフォーマンステスト"""
        logger = get_structured_logger("perf_test_structured")
        target = self.performance_targets["structured_logging_ops_per_sec"]

        # ウォームアップ
        for i in range(100):
            logger.info(f"Warmup message {i}", extra={"iteration": i})

        # 実際の計測
        iterations = 2000
        start_time = time.perf_counter()

        for i in range(iterations):
            if i % 4 == 0:
                logger.info(f"Info message {i}", extra={"type": "info", "id": i})
            elif i % 4 == 1:
                logger.warning(
                    f"Warning message {i}", extra={"type": "warning", "id": i}
                )
            elif i % 4 == 2:
                logger.performance_log(f"operation_{i}", 0.1, extra={"perf_test": True})
            else:
                logger.security_event("test_event", {"event_id": i, "safe": True})

        end_time = time.perf_counter()

        duration = end_time - start_time
        ops_per_sec = iterations / duration

        return {
            "ops_per_sec": round(ops_per_sec, 2),
            "target": target,
            "target_achieved": ops_per_sec >= target * 0.8,
            "duration_seconds": round(duration, 4),
            "iterations": iterations,
            "efficiency_ratio": round(ops_per_sec / target, 3),
        }

    def _benchmark_kumihan_parsing(self) -> Dict[str, Any]:
        """Kumihanパーシングパフォーマンステスト"""
        try:
            parser = KumihanParser()
            target = self.performance_targets["parsing_chars_per_sec"]

            # テストコンテンツ作成
            test_content = """
# タイトル #見出し1##
この文書はパフォーマンステスト用のサンプルです。

# 装飾 #太字##の文章と# 装飾 #斜体##の文章があります。
# リスト #番号なし##
- 項目1
- 項目2
- 項目3

# リスト #番号あり##
1. 最初の項目
2. 2番目の項目
3. 3番目の項目

# 特殊ブロック #コード##
```python
def test_function():
    return "Hello World"
```

# 装飾 #下線##テキストもサポートされています。
            """

            # より大きなコンテンツを生成
            large_content = test_content * 100  # 約50,000文字
            total_chars = len(large_content)

            # ウォームアップ
            for _ in range(5):
                parser.parse(test_content)

            # 実際の計測
            iterations = 10
            start_time = time.perf_counter()

            for _ in range(iterations):
                result = parser.parse(large_content)

            end_time = time.perf_counter()

            duration = end_time - start_time
            total_chars_processed = total_chars * iterations
            chars_per_sec = total_chars_processed / duration

            return {
                "chars_per_sec": round(chars_per_sec, 2),
                "target": target,
                "target_achieved": chars_per_sec >= target * 0.8,
                "duration_seconds": round(duration, 4),
                "total_chars_processed": total_chars_processed,
                "iterations": iterations,
                "efficiency_ratio": round(chars_per_sec / target, 3),
            }

        except Exception as e:
            return {"error": str(e), "target_achieved": False, "chars_per_sec": 0}

    def _benchmark_html_rendering(self) -> Dict[str, Any]:
        """HTMLレンダリングパフォーマンステスト"""
        try:
            parser = KumihanParser()
            renderer = MainRenderer()
            target = self.performance_targets["rendering_elements_per_sec"]

            # パース済みコンテンツでレンダリングテスト
            test_content = (
                """
# タイトル #見出し1##
# 装飾 #太字##重要なテキスト
# リスト #番号なし##
- アイテム1
- アイテム2
- アイテム3
            """
                * 50
            )  # より多くの要素

            parsed_content = parser.parse(test_content)

            # ウォームアップ
            for _ in range(5):
                renderer.render(parsed_content)

            # 実際の計測
            iterations = 50
            start_time = time.perf_counter()

            rendered_results = []
            for _ in range(iterations):
                rendered = renderer.render(parsed_content)
                rendered_results.append(rendered)

            end_time = time.perf_counter()

            duration = end_time - start_time
            # 要素数推定（簡易的に）
            estimated_elements = len(parsed_content.split("\n")) * iterations
            elements_per_sec = estimated_elements / duration

            # レンダリング結果の品質チェック
            sample_result = rendered_results[0] if rendered_results else ""
            quality_ok = "<html>" in sample_result and len(sample_result) > 100

            return {
                "elements_per_sec": round(elements_per_sec, 2),
                "target": target,
                "target_achieved": elements_per_sec >= target * 0.8 and quality_ok,
                "duration_seconds": round(duration, 4),
                "iterations": iterations,
                "estimated_elements": estimated_elements,
                "rendering_quality_ok": quality_ok,
                "efficiency_ratio": round(elements_per_sec / target, 3),
            }

        except Exception as e:
            return {"error": str(e), "target_achieved": False, "elements_per_sec": 0}

    def _benchmark_memory_performance(self) -> Dict[str, Any]:
        """メモリ使用量パフォーマンステスト"""
        target_limit_mb = self.performance_targets["memory_usage_limit_mb"]

        # ベースラインメモリ使用量
        gc.collect()
        baseline_memory = self.process.memory_info().rss / (1024 * 1024)

        memory_samples = []

        # 重い処理を実行しながらメモリ監視
        large_data = []

        for i in range(100):
            # 大きなデータ構造作成
            test_data = {
                "content": "x" * 1000,  # 1KB of data
                "metadata": {"id": i, "timestamp": time.time()},
                "large_list": list(range(100)),
            }
            large_data.append(test_data)

            # メモリ使用量サンプリング
            if i % 10 == 0:
                current_memory = self.process.memory_info().rss / (1024 * 1024)
                memory_samples.append(current_memory)

        # 最終メモリ使用量
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        peak_memory = max(memory_samples) if memory_samples else final_memory

        # メモリ解放テスト
        del large_data
        gc.collect()

        after_cleanup_memory = self.process.memory_info().rss / (1024 * 1024)
        memory_leak = after_cleanup_memory - baseline_memory

        return {
            "baseline_memory_mb": round(baseline_memory, 2),
            "peak_memory_mb": round(peak_memory, 2),
            "final_memory_mb": round(final_memory, 2),
            "after_cleanup_memory_mb": round(after_cleanup_memory, 2),
            "memory_delta_mb": round(final_memory - baseline_memory, 2),
            "memory_leak_mb": round(memory_leak, 2),
            "target_limit_mb": target_limit_mb,
            "target_achieved": peak_memory < target_limit_mb
            and memory_leak < 10,  # 10MB未満のリークは許容
            "memory_efficient": memory_leak < 5,  # 5MB未満なら効率的
        }

    def _benchmark_concurrent_operations(self) -> Dict[str, Any]:
        """並行処理パフォーマンステスト"""

        def worker_task(task_id: int) -> Dict[str, Any]:
            """ワーカータスク"""
            logger = get_structured_logger(f"concurrent_worker_{task_id}")
            validator = SecureInputValidator()
            sanitizer = DataSanitizer()

            operations = 0
            start_time = time.perf_counter()

            # 各ワーカーで様々な処理を実行
            for i in range(50):
                # 入力検証
                validator.validate_file_path(f"test_file_{task_id}_{i}.txt")
                operations += 1

                # データサニタイズ
                sanitizer.sanitize_html(f"<p>Content {task_id} {i}</p>")
                operations += 1

                # ログ出力
                logger.info(f"Worker {task_id} operation {i}")
                operations += 1

            duration = time.perf_counter() - start_time
            return {
                "task_id": task_id,
                "operations": operations,
                "duration": duration,
                "ops_per_sec": operations / duration,
            }

        # 並行実行テスト
        num_workers = 4
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            worker_results = [future.result() for future in as_completed(futures)]

        total_duration = time.perf_counter() - start_time

        # 結果集計
        total_operations = sum(r["operations"] for r in worker_results)
        average_ops_per_sec = statistics.mean(
            [r["ops_per_sec"] for r in worker_results]
        )
        overall_ops_per_sec = total_operations / total_duration

        return {
            "num_workers": num_workers,
            "total_operations": total_operations,
            "total_duration_seconds": round(total_duration, 4),
            "average_worker_ops_per_sec": round(average_ops_per_sec, 2),
            "overall_ops_per_sec": round(overall_ops_per_sec, 2),
            "worker_results": worker_results,
            "target_achieved": overall_ops_per_sec > 1000,  # 1000 ops/sec以上を目標
            "concurrency_effective": overall_ops_per_sec > average_ops_per_sec * 0.8,
        }

    def _benchmark_system_resources(self) -> Dict[str, Any]:
        """システムリソース使用量測定"""
        target_cpu_limit = self.performance_targets["cpu_usage_limit_percent"]

        cpu_samples = []
        memory_samples = []

        # リソース集約的な処理を実行
        start_time = time.perf_counter()

        for i in range(50):
            # CPU集約的処理
            result = sum(j**2 for j in range(1000))

            # サンプリング
            if i % 5 == 0:
                cpu_percent = self.process.cpu_percent()
                memory_mb = self.process.memory_info().rss / (1024 * 1024)
                cpu_samples.append(cpu_percent)
                memory_samples.append(memory_mb)

            time.sleep(0.01)  # 小さな待機

        duration = time.perf_counter() - start_time

        # 統計計算
        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
        peak_cpu = max(cpu_samples) if cpu_samples else 0
        avg_memory = statistics.mean(memory_samples) if memory_samples else 0
        peak_memory = max(memory_samples) if memory_samples else 0

        return {
            "duration_seconds": round(duration, 4),
            "cpu_usage": {
                "average_percent": round(avg_cpu, 2),
                "peak_percent": round(peak_cpu, 2),
                "samples": len(cpu_samples),
            },
            "memory_usage": {
                "average_mb": round(avg_memory, 2),
                "peak_mb": round(peak_memory, 2),
                "samples": len(memory_samples),
            },
            "target_cpu_limit": target_cpu_limit,
            "target_achieved": peak_cpu < target_cpu_limit,
            "resource_efficient": avg_cpu < target_cpu_limit * 0.7,
        }

    def _calculate_overall_score(self):
        """総合パフォーマンススコア計算"""
        total_benchmarks = self.results["summary"]["total_benchmarks"]
        passed_benchmarks = self.results["summary"]["passed_benchmarks"]

        if total_benchmarks > 0:
            # 基本スコア（通過率）
            basic_score = passed_benchmarks / total_benchmarks

            # 効率性ボーナス（各ベンチマークの効率比率の平均）
            efficiency_ratios = []
            for benchmark in self.results["benchmarks"].values():
                if isinstance(benchmark, dict) and "efficiency_ratio" in benchmark:
                    efficiency_ratios.append(
                        min(benchmark["efficiency_ratio"], 2.0)
                    )  # 2.0でキャップ

            efficiency_bonus = 0
            if efficiency_ratios:
                avg_efficiency = statistics.mean(efficiency_ratios)
                if avg_efficiency > 1.0:
                    efficiency_bonus = (avg_efficiency - 1.0) * 0.2  # 最大20%ボーナス

            overall_score = min(basic_score + efficiency_bonus, 1.0)
            self.results["summary"]["overall_performance_score"] = round(
                overall_score, 3
            )
        else:
            self.results["summary"]["overall_performance_score"] = 0.0

    def _save_results(self):
        """結果をJSONファイルに保存"""
        try:
            output_dir = Path("tmp")
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"performance_benchmark_report_{timestamp}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"⚡ Performance benchmark report saved: {output_file}")

            # 最新レポートとしてもコピー保存
            latest_file = output_dir / "performance_benchmark_report.json"
            with open(latest_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def _print_summary(self):
        """結果サマリーを表示"""
        summary = self.results["summary"]
        score = summary["overall_performance_score"]

        print("\n" + "=" * 60)
        print("⚡ PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        print(f"🎯 Overall Performance Score: {score:.1%}")
        print(f"✅ Passed Benchmarks: {summary['passed_benchmarks']}")
        print(f"❌ Failed Benchmarks: {summary['failed_benchmarks']}")
        print(f"📊 Total Benchmarks: {summary['total_benchmarks']}")

        # システム情報
        sys_info = self.results["system_info"]
        print(f"\n🖥️  System Info:")
        print(
            f"   CPU Cores: {sys_info.get('cpu_physical_cores', 'N/A')} physical, {sys_info.get('cpu_logical_cores', 'N/A')} logical"
        )
        print(
            f"   Memory: {sys_info.get('total_memory_gb', 'N/A')}GB total, {sys_info.get('available_memory_gb', 'N/A')}GB available"
        )
        print(f"   Platform: {sys_info.get('platform', 'N/A')}")

        # 主要ベンチマーク結果
        print("\n📈 Key Performance Metrics:")
        print("-" * 50)

        key_benchmarks = [
            ("input_validation", "Input Validation", "ops_per_sec"),
            ("data_sanitization", "Data Sanitization", "ops_per_sec"),
            ("audit_logging", "Audit Logging", "events_per_sec"),
            ("structured_logging", "Structured Logging", "ops_per_sec"),
        ]

        for bench_key, bench_name, metric_key in key_benchmarks:
            if bench_key in self.results["benchmarks"]:
                result = self.results["benchmarks"][bench_key]
                if metric_key in result:
                    value = result[metric_key]
                    target = result.get("target", 0)
                    status = "✅" if result.get("target_achieved", False) else "❌"
                    print(f"{status} {bench_name}: {value:,.0f} ({target:,.0f} target)")

        # パフォーマンスレベル判定
        if score >= 0.9:
            level = "🚀 EXCELLENT PERFORMANCE"
        elif score >= 0.8:
            level = "⚡ GOOD PERFORMANCE"
        elif score >= 0.7:
            level = "🔧 ACCEPTABLE PERFORMANCE (Needs Optimization)"
        else:
            level = "❌ PERFORMANCE ISSUES (Requires Attention)"

        print(f"\n🏆 Performance Level: {level}")
        print("=" * 60)


def main():
    """メイン実行関数"""
    try:
        print("⚡ Starting Performance Benchmark Suite...")
        benchmark = PerformanceBenchmark()
        results = benchmark.run_all_benchmarks()

        # 終了コード決定
        score = results["summary"]["overall_performance_score"]
        if score >= 0.8:
            exit_code = 0  # Success
        elif score >= 0.6:
            exit_code = 1  # Warning
        else:
            exit_code = 2  # Performance issues

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️ Performance benchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Critical error in performance benchmark: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
