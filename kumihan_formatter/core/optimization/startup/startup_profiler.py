"""
起動時間プロファイラー

起動時間の詳細計測とボトルネック特定による
パフォーマンス最適化支援システム
"""

import gc
import json
import os
import sys
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProfilerMeasurement:
    """プロファイラー計測データ"""

    timestamp: float
    event: str
    duration_ms: float
    memory_mb: float
    cpu_percent: float
    details: Dict[str, Any]


@dataclass
class StartupProfile:
    """起動プロファイル結果"""

    total_time_ms: float
    memory_peak_mb: float
    cpu_avg_percent: float
    measurements: List[ProfilerMeasurement]
    bottlenecks: List[Dict[str, Any]]
    optimization_suggestions: List[str]
    comparison_baseline: Optional[Dict[str, Any]] = None


class StartupProfiler:
    """起動時間プロファイラークラス"""

    def __init__(self, enable_memory_tracking: bool = True):
        self.enable_memory_tracking = enable_memory_tracking
        self.measurements: List[ProfilerMeasurement] = []
        self.start_time: Optional[float] = None
        self.process = psutil.Process()

        if enable_memory_tracking:
            tracemalloc.start()

    def start_profiling(self) -> None:
        """プロファイリング開始"""
        self.start_time = time.time()
        self.measurements.clear()

        # ベースライン計測
        self._record_measurement(
            "profiling_start",
            0,
            {
                "python_version": sys.version,
                "platform": sys.platform,
                "process_id": os.getpid(),
            },
        )

        logger.info("Startup profiling started")

    @contextmanager
    def measure_section(
        self, section_name: str, details: Optional[Dict[str, Any]] = None
    ):
        """セクション計測コンテキストマネージャー"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self.process.cpu_percent()

        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            end_cpu = self.process.cpu_percent()

            measurement_details = details or {}
            measurement_details.update(
                {
                    "memory_delta_mb": end_memory - start_memory,
                    "cpu_delta_percent": end_cpu - start_cpu,
                }
            )

            self._record_measurement(
                f"section:{section_name}", duration_ms, measurement_details
            )

    def measure_import(self, module_name: str) -> Any:
        """モジュールインポート計測"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            import importlib

            module = importlib.import_module(module_name)

            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()

            self._record_measurement(
                f"import:{module_name}",
                duration_ms,
                {
                    "module_size": sys.getsizeof(module) if module else 0,
                    "memory_delta_mb": end_memory - start_memory,
                    "cached": module_name in sys.modules,
                },
            )

            return module

        except ImportError as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_measurement(
                f"import_failed:{module_name}", duration_ms, {"error": str(e)}
            )
            raise

    def measure_function_call(
        self, func_name: str, func_callable, *args, **kwargs
    ) -> Any:
        """関数呼び出し計測"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            result = func_callable(*args, **kwargs)

            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()

            self._record_measurement(
                f"function:{func_name}",
                duration_ms,
                {
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "memory_delta_mb": end_memory - start_memory,
                    "result_size": sys.getsizeof(result) if result else 0,
                },
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_measurement(
                f"function_failed:{func_name}",
                duration_ms,
                {"error": str(e), "error_type": type(e).__name__},
            )
            raise

    def finish_profiling(self) -> StartupProfile:
        """プロファイリング完了と結果生成"""
        if self.start_time is None:
            raise RuntimeError("Profiling not started")

        total_time_ms = (time.time() - self.start_time) * 1000

        # 最終計測
        self._record_measurement(
            "profiling_end",
            0,
            {
                "total_measurements": len(self.measurements),
                "gc_collections": gc.get_stats() if hasattr(gc, "get_stats") else [],
            },
        )

        # メモリ統計
        memory_peak_mb = (
            max(m.memory_mb for m in self.measurements) if self.measurements else 0
        )
        cpu_avg_percent = (
            sum(m.cpu_percent for m in self.measurements) / len(self.measurements)
            if self.measurements
            else 0
        )

        # ボトルネック分析
        bottlenecks = self._analyze_bottlenecks()

        # 最適化提案
        optimization_suggestions = self._generate_optimization_suggestions()

        profile = StartupProfile(
            total_time_ms=total_time_ms,
            memory_peak_mb=memory_peak_mb,
            cpu_avg_percent=cpu_avg_percent,
            measurements=self.measurements,
            bottlenecks=bottlenecks,
            optimization_suggestions=optimization_suggestions,
        )

        logger.info(f"Startup profiling completed: {total_time_ms:.2f}ms total")
        return profile

    def _record_measurement(
        self, event: str, duration_ms: float, details: Dict[str, Any]
    ) -> None:
        """計測データ記録"""
        timestamp = time.time()
        memory_mb = self._get_memory_usage()
        cpu_percent = self.process.cpu_percent()

        measurement = ProfilerMeasurement(
            timestamp=timestamp,
            event=event,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            details=details,
        )

        self.measurements.append(measurement)

    def _get_memory_usage(self) -> float:
        """メモリ使用量取得（MB）"""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """ボトルネック分析"""
        bottlenecks = []

        # 時間のかかる処理 Top 5
        time_sorted = sorted(
            [m for m in self.measurements if m.duration_ms > 0],
            key=lambda x: x.duration_ms,
            reverse=True,
        )[:5]

        for measurement in time_sorted:
            bottlenecks.append(
                {
                    "type": "slow_operation",
                    "event": measurement.event,
                    "duration_ms": measurement.duration_ms,
                    "impact": "high" if measurement.duration_ms > 100 else "medium",
                    "suggestion": self._get_optimization_hint(measurement.event),
                }
            )

        # メモリ使用量の急激な増加
        memory_deltas = []
        for i in range(1, len(self.measurements)):
            prev_mem = self.measurements[i - 1].memory_mb
            curr_mem = self.measurements[i].memory_mb
            delta = curr_mem - prev_mem

            if delta > 5:  # 5MB以上の増加
                memory_deltas.append(
                    {
                        "type": "memory_spike",
                        "event": self.measurements[i].event,
                        "memory_delta_mb": delta,
                        "impact": "high" if delta > 20 else "medium",
                    }
                )

        bottlenecks.extend(memory_deltas[:3])  # Top 3

        return bottlenecks

    def _generate_optimization_suggestions(self) -> List[str]:
        """最適化提案生成"""
        suggestions = []

        # インポート最適化
        import_measurements = [
            m for m in self.measurements if m.event.startswith("import:")
        ]
        if import_measurements:
            slow_imports = [m for m in import_measurements if m.duration_ms > 50]
            if slow_imports:
                suggestions.append(
                    f"{len(slow_imports)}個の重いインポートを遅延ロードに変更することで起動時間を短縮可能"
                )

        # 関数呼び出し最適化
        function_measurements = [
            m for m in self.measurements if m.event.startswith("function:")
        ]
        if function_measurements:
            slow_functions = [m for m in function_measurements if m.duration_ms > 30]
            if slow_functions:
                suggestions.append(
                    f"{len(slow_functions)}個の重い関数処理をキャッシュ化または非同期処理に変更を検討"
                )

        # メモリ最適化
        peak_memory = (
            max(m.memory_mb for m in self.measurements) if self.measurements else 0
        )
        if peak_memory > 50:
            suggestions.append(
                f"ピークメモリ使用量{peak_memory:.1f}MBを削減するため、オブジェクトプールやメモリリサイクルを検討"
            )

        # 総合的な提案
        total_time = (
            self.measurements[-1].timestamp - self.measurements[0].timestamp
            if len(self.measurements) >= 2
            else 0
        )
        if total_time > 1:  # 1秒以上
            suggestions.append(
                "起動時間1秒以上のため、段階的な初期化パターンの導入を推奨"
            )

        return suggestions

    def _get_optimization_hint(self, event: str) -> str:
        """イベント別最適化ヒント"""
        if event.startswith("import:"):
            return "遅延インポートまたはインポート順序の最適化を検討"
        elif event.startswith("function:"):
            return "処理のキャッシュ化または非同期実行を検討"
        elif event.startswith("section:"):
            return "セクション内の処理を細分化して最適化"
        else:
            return "処理時間の短縮方法を検討"

    def save_profile(self, profile: StartupProfile, output_path: Path) -> None:
        """プロファイル結果保存"""
        try:
            os.makedirs("tmp", exist_ok=True)

            # JSON形式で保存
            profile_data = {
                "total_time_ms": profile.total_time_ms,
                "memory_peak_mb": profile.memory_peak_mb,
                "cpu_avg_percent": profile.cpu_avg_percent,
                "measurements": [asdict(m) for m in profile.measurements],
                "bottlenecks": profile.bottlenecks,
                "optimization_suggestions": profile.optimization_suggestions,
                "metadata": {
                    "timestamp": time.time(),
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "measurement_count": len(profile.measurements),
                },
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Profile saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            raise

    def load_profile(self, input_path: Path) -> StartupProfile:
        """プロファイル結果読み込み"""
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            measurements = [ProfilerMeasurement(**m) for m in data["measurements"]]

            return StartupProfile(
                total_time_ms=data["total_time_ms"],
                memory_peak_mb=data["memory_peak_mb"],
                cpu_avg_percent=data["cpu_avg_percent"],
                measurements=measurements,
                bottlenecks=data["bottlenecks"],
                optimization_suggestions=data["optimization_suggestions"],
            )

        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            raise

    def compare_profiles(
        self, baseline: StartupProfile, current: StartupProfile
    ) -> Dict[str, Any]:
        """プロファイル比較"""
        comparison = {
            "time_improvement": {
                "baseline_ms": baseline.total_time_ms,
                "current_ms": current.total_time_ms,
                "improvement_ms": baseline.total_time_ms - current.total_time_ms,
                "improvement_percent": (
                    (baseline.total_time_ms - current.total_time_ms)
                    / baseline.total_time_ms
                )
                * 100,
            },
            "memory_improvement": {
                "baseline_mb": baseline.memory_peak_mb,
                "current_mb": current.memory_peak_mb,
                "improvement_mb": baseline.memory_peak_mb - current.memory_peak_mb,
                "improvement_percent": (
                    (baseline.memory_peak_mb - current.memory_peak_mb)
                    / baseline.memory_peak_mb
                )
                * 100,
            },
            "bottleneck_changes": {
                "baseline_count": len(baseline.bottlenecks),
                "current_count": len(current.bottlenecks),
                "improvement": len(baseline.bottlenecks) - len(current.bottlenecks),
            },
        }

        return comparison


def profile_application_startup(app_entry_point: str) -> StartupProfile:
    """アプリケーション起動プロファイリング"""
    profiler = StartupProfiler()
    profiler.start_profiling()

    try:
        with profiler.measure_section("application_startup"):
            # アプリケーション固有の初期化処理
            with profiler.measure_section("import_phase"):
                # 主要モジュールのインポート計測
                main_modules = [
                    "kumihan_formatter.core.utilities.logger",
                    "kumihan_formatter.core.optimization",
                    "argparse",
                    "pathlib",
                ]

                for module in main_modules:
                    try:
                        profiler.measure_import(module)
                    except ImportError:
                        logger.warning(f"Failed to import {module}")

            with profiler.measure_section("initialization"):
                # 初期化処理のシミュレーション
                time.sleep(0.01)  # 10ms のシミュレート処理

        return profiler.finish_profiling()

    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        raise


def main():
    """CLI エントリーポイント"""
    import argparse

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Startup profiler")
    parser.add_argument("--profile", action="store_true", help="Run startup profiling")
    parser.add_argument("--compare", nargs=2, help="Compare two profile files")
    parser.add_argument(
        "--output",
        type=str,
        default="tmp/startup_profile.json",
        help="Output file path",
    )
    parser.add_argument(
        "--iterations", type=int, default=5, help="Number of profiling iterations"
    )

    args = parser.parse_args()

    if args.profile:
        print("Running startup profiling...")

        profiles = []
        for i in range(args.iterations):
            print(f"Iteration {i+1}/{args.iterations}")
            profile = profile_application_startup("kumihan_formatter")
            profiles.append(profile)

        # 平均プロファイル計算
        avg_time = sum(p.total_time_ms for p in profiles) / len(profiles)
        avg_memory = sum(p.memory_peak_mb for p in profiles) / len(profiles)
        avg_cpu = sum(p.cpu_avg_percent for p in profiles) / len(profiles)

        # 最適プロファイル（最短時間）選択
        best_profile = min(profiles, key=lambda p: p.total_time_ms)

        print(f"Average startup time: {avg_time:.2f}ms")
        print(f"Average memory peak: {avg_memory:.2f}MB")
        print(f"Average CPU usage: {avg_cpu:.1f}%")
        print(f"Best startup time: {best_profile.total_time_ms:.2f}ms")

        # 結果保存
        profiler = StartupProfiler()
        profiler.save_profile(best_profile, Path(args.output))

        print(f"Profile saved to {args.output}")

        # 最適化提案表示
        print("\nOptimization Suggestions:")
        for suggestion in best_profile.optimization_suggestions:
            print(f"  - {suggestion}")

        # ボトルネック表示
        print("\nTop Bottlenecks:")
        for bottleneck in best_profile.bottlenecks[:3]:
            print(
                f"  - {bottleneck['event']}: {bottleneck.get('duration_ms', 'N/A')}ms"
            )

    elif args.compare:
        print("Comparing profiles...")
        profiler = StartupProfiler()

        baseline = profiler.load_profile(Path(args.compare[0]))
        current = profiler.load_profile(Path(args.compare[1]))

        comparison = profiler.compare_profiles(baseline, current)

        print("Comparison Results:")
        print(
            f"Time improvement: {comparison['time_improvement']['improvement_ms']:.2f}ms "
            f"({comparison['time_improvement']['improvement_percent']:.1f}%)"
        )
        print(
            f"Memory improvement: {comparison['memory_improvement']['improvement_mb']:.2f}MB "
            f"({comparison['memory_improvement']['improvement_percent']:.1f}%)"
        )

        # 比較結果保存
        comparison_path = "tmp/profile_comparison.json"
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)

        print(f"Comparison saved to {comparison_path}")

    else:
        print("No action specified. Use --help for usage information.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
