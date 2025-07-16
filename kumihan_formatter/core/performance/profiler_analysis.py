"""プロファイラー分析機能

このモジュールは、プロファイリング結果の分析、
レポート生成、セッション比較機能を提供します。
"""

import json
import time
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .profiler_types import PROFILER_CONSTANTS, ProfilingSession


class ProfilingAnalyzer:
    """プロファイリング分析クラス"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def analyze_performance_bottlenecks(
        self,
        session: ProfilingSession,
        threshold_percent: float = PROFILER_CONSTANTS["BOTTLENECK_THRESHOLD_PERCENT"],
    ) -> dict[str, Any]:
        """パフォーマンスボトルネックを分析"""
        self.logger.info(
            f"ボトルネック分析開始: session={session.name}, threshold={threshold_percent}%"
        )

        # 実行時間でソート
        sorted_functions = sorted(
            session.function_profiles.values(), key=lambda x: x.total_time, reverse=True
        )

        # 合計時間を計算
        total_time = sum(func.total_time for func in sorted_functions)

        # ボトルネック関数を特定
        bottlenecks = []
        for func in sorted_functions:
            if func.total_time > 0:
                percent = (func.total_time / total_time) * 100
                if percent >= threshold_percent:
                    bottleneck_info = {
                        "function": func.name,
                        "module": func.module,
                        "time_percent": percent,
                        "total_time": func.total_time,
                        "avg_time": func.avg_time,
                        "calls": func.calls,
                    }
                    bottlenecks.append(bottleneck_info)
                    self.logger.debug(f"ボトルネック検出: {func.name} ({percent:.1f}%)")

        # メモリ使用量の分析
        memory_analysis = self._analyze_memory_usage(session)

        result = {
            "session": session.name,
            "total_time": total_time,
            "total_calls": session.total_calls,
            "bottlenecks": bottlenecks,
            "memory_analysis": memory_analysis,
            "top_functions": bottlenecks[:10],
            "performance_warnings": self._generate_performance_warnings(session),
        }

        self.logger.info(
            f"ボトルネック分析完了: {len(bottlenecks)}個のボトルネック検出"
        )
        return result

    def _analyze_memory_usage(self, session: ProfilingSession) -> dict[str, Any] | None:
        """メモリ使用量を分析"""
        if not session.memory_snapshots:
            return None

        memory_values = [snapshot["memory_mb"] for snapshot in session.memory_snapshots]

        if not memory_values:
            return None

        return {
            "peak_memory": max(memory_values),
            "min_memory": min(memory_values),
            "avg_memory": sum(memory_values) / len(memory_values),
            "memory_delta": max(memory_values) - min(memory_values),
            "snapshots": session.memory_snapshots,
        }

    def _generate_performance_warnings(self, session: ProfilingSession) -> list[str]:
        """パフォーマンス警告を生成"""
        warnings = []

        slow_threshold = PROFILER_CONSTANTS["SLOW_FUNCTION_THRESHOLD_SECONDS"]
        high_calls_threshold = PROFILER_CONSTANTS["HIGH_CALL_COUNT_THRESHOLD"]
        memory_threshold = PROFILER_CONSTANTS["MEMORY_WARNING_THRESHOLD_MB"]

        # 実行時間が長い関数を検出
        for func_name, profile in session.function_profiles.items():
            if profile.avg_time > slow_threshold:
                warnings.append(
                    f"Slow function: {func_name} (avg: {profile.avg_time:.3f}s)"
                )

        # 呼び出し回数が多い関数を検出
        for func_name, profile in session.function_profiles.items():
            if profile.calls > high_calls_threshold:
                warnings.append(
                    f"High call count: {func_name} ({profile.calls:,} calls)"
                )

        # メモリ使用量の警告
        memory_analysis = self._analyze_memory_usage(session)
        if memory_analysis and memory_analysis["peak_memory"] > memory_threshold:
            warnings.append(
                f"High memory usage: {memory_analysis['peak_memory']:.1f} MB"
            )

        return warnings

    def compare_sessions(
        self, session1: ProfilingSession, session2: ProfilingSession
    ) -> dict[str, Any]:
        """セッション間の比較"""
        # 時間の比較
        time_comparison = {
            "session1_time": session1.total_time,
            "session2_time": session2.total_time,
            "time_difference": session2.total_time - session1.total_time,
            "time_ratio": (
                session2.total_time / session1.total_time
                if session1.total_time > 0
                else 0
            ),
            "improvement_percent": (
                (
                    (session1.total_time - session2.total_time)
                    / session1.total_time
                    * 100
                )
                if session1.total_time > 0
                else 0
            ),
        }

        # 関数レベルの比較
        function_comparison = {}
        all_functions = set(session1.function_profiles.keys()) | set(
            session2.function_profiles.keys()
        )

        for func_name in all_functions:
            f1 = session1.function_profiles.get(func_name)
            f2 = session2.function_profiles.get(func_name)

            if f1 and f2:
                function_comparison[func_name] = {
                    "time_difference": f2.total_time - f1.total_time,
                    "calls_difference": f2.calls - f1.calls,
                    "improvement_percent": (
                        ((f1.total_time - f2.total_time) / f1.total_time * 100)
                        if f1.total_time > 0
                        else 0
                    ),
                }

        return {
            "session1": session1.name,
            "session2": session2.name,
            "time_comparison": time_comparison,
            "function_comparison": function_comparison,
            "winner": (
                session1.name
                if time_comparison["improvement_percent"] > 0
                else session2.name
            ),
        }


class ProfilingReporter:
    """プロファイリングレポート生成クラス"""

    def __init__(self, analyzer: ProfilingAnalyzer):
        self.analyzer = analyzer
        self.logger = get_logger(__name__)

    def generate_performance_report(self, session: ProfilingSession) -> str:
        """パフォーマンスレポートを生成"""
        analysis = self.analyzer.analyze_performance_bottlenecks(session)

        report_lines = [
            f"Performance Report: {session.name}",
            "=" * 50,
            f"Total Time: {analysis['total_time']:.3f}s",
            f"Total Calls: {analysis['total_calls']:,}",
            "",
            "Top Performance Bottlenecks:",
            "-" * 30,
        ]

        for bottleneck in analysis["bottlenecks"][:10]:
            report_lines.append(f"  {bottleneck['function']} ({bottleneck['module']})")
            report_lines.append(
                f"    Time: {bottleneck['total_time']:.3f}s ({bottleneck['time_percent']:.1f}%)"
            )
            report_lines.append(
                f"    Calls: {bottleneck['calls']:,} | Avg: {bottleneck['avg_time']:.6f}s"
            )
            report_lines.append("")

        # メモリ分析
        memory_analysis = analysis["memory_analysis"]
        if memory_analysis:
            report_lines.extend(
                [
                    "Memory Analysis:",
                    "-" * 15,
                    f"  Peak Memory: {memory_analysis.get('peak_memory', 0):.1f} MB",
                    f"  Memory Delta: {memory_analysis.get('memory_delta', 0):.1f} MB",
                    f"  Average Memory: {memory_analysis.get('avg_memory', 0):.1f} MB",
                    "",
                ]
            )

        # 警告
        warnings = analysis["performance_warnings"]
        if warnings:
            report_lines.extend(
                [
                    "Performance Warnings:",
                    "-" * 20,
                ]
            )
            for warning in warnings:
                report_lines.append(f"  ⚠️  {warning}")
            report_lines.append("")

        return "\n".join(report_lines)

    def save_profile_data(self, session: ProfilingSession, output_dir: Path) -> Path:
        """プロファイルデータを保存"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 分析結果を保存
        analysis = self.analyzer.analyze_performance_bottlenecks(session)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"profile_{session.name}_{timestamp}.json"
        output_file = output_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        self.logger.info(f"プロファイルデータ保存: {output_file}")
        return output_file
