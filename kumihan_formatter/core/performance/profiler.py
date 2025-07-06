"""
高度なプロファイラー - パフォーマンス最適化用

詳細なパフォーマンス分析とボトルネック検出
Issue #402対応 - パフォーマンス最適化
"""

import cProfile
import io
import pstats
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...utilities.logger import get_logger


@dataclass
class FunctionProfile:
    """関数プロファイル情報"""

    name: str
    module: str
    calls: int = 0
    total_time: float = 0.0
    cumulative_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float("inf")
    memory_usage: Optional[int] = None
    memory_delta: Optional[int] = None


@dataclass
class ProfilingSession:
    """プロファイリングセッション"""

    name: str
    start_time: float
    end_time: Optional[float] = None
    function_profiles: Dict[str, FunctionProfile] = field(default_factory=dict)
    total_calls: int = 0
    total_time: float = 0.0
    memory_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """セッション持続時間"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.perf_counter() - self.start_time


class AdvancedProfiler:
    """高度なプロファイリングシステム

    機能:
    - cProfileベースの詳細プロファイリング
    - メモリ使用量の追跡
    - 関数レベルのパフォーマンス分析
    - ボトルネック自動検出
    - プロファイル結果の保存・比較
    """

    def __init__(self, enable_memory_tracking: bool = True):
        """プロファイラーを初期化

        Args:
            enable_memory_tracking: メモリ追跡を有効にするか
        """
        self.logger = get_logger(__name__)
        self.logger.info(
            f"AdvancedProfiler初期化開始: memory_tracking={enable_memory_tracking}"
        )

        self.enable_memory_tracking = enable_memory_tracking
        self.sessions: Dict[str, ProfilingSession] = {}
        self.active_sessions: Dict[str, ProfilingSession] = {}
        self._lock = threading.Lock()

        self.logger.debug("プロファイラー初期化完了")

        # メモリ追跡用
        self._memory_tracker = None
        if enable_memory_tracking:
            try:
                import psutil

                self._memory_tracker = psutil.Process()
                self.logger.info("メモリ追跡機能を有効化")
            except ImportError:
                self.logger.warning("psutilが利用できないため、メモリ追跡機能を無効化")

    @contextmanager
    def profile_session(self, session_name: str):
        """プロファイリングセッションのコンテキストマネージャー

        Args:
            session_name: セッション名
        """
        self.logger.info(f"プロファイリングセッション開始: {session_name}")
        session = self._start_session(session_name)
        profiler = cProfile.Profile()

        try:
            if self._memory_tracker:
                try:
                    memory_info = {
                        "timestamp": time.perf_counter(),
                        "memory_mb": self._memory_tracker.memory_info().rss
                        / 1024
                        / 1024,
                        "cpu_percent": self._memory_tracker.cpu_percent(),
                    }
                    session.memory_snapshots.append(memory_info)
                    self.logger.debug(
                        f"メモリスナップショット記録: {memory_info['memory_mb']:.1f}MB"
                    )
                except Exception as e:
                    self.logger.error(f"メモリ情報取得エラー: {e}")

            profiler.enable()
            yield session

        finally:
            profiler.disable()
            self.logger.debug(f"プロファイリング測定終了: {session_name}")

            if self._memory_tracker:
                try:
                    final_memory_info = {
                        "timestamp": time.perf_counter(),
                        "memory_mb": self._memory_tracker.memory_info().rss
                        / 1024
                        / 1024,
                        "cpu_percent": self._memory_tracker.cpu_percent(),
                    }
                    session.memory_snapshots.append(final_memory_info)
                    self.logger.debug(
                        f"最終メモリスナップショット: {final_memory_info['memory_mb']:.1f}MB"
                    )
                except Exception as e:
                    self.logger.error(f"最終メモリ情報取得エラー: {e}")

            self._end_session(session_name, profiler)
            self.logger.info(f"プロファイリングセッション完了: {session_name}")

    def profile_function(self, func_name: Optional[str] = None):
        """関数プロファイリング用デコレーター

        Args:
            func_name: 関数名（未指定時は自動取得）
        """

        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_memory = self._get_memory_usage()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    end_memory = self._get_memory_usage()

                    execution_time = end_time - start_time
                    memory_delta = (
                        end_memory - start_memory
                        if start_memory and end_memory
                        else None
                    )

                    self._record_function_call(name, execution_time, memory_delta)

            return wrapper

        return decorator

    def analyze_performance_bottlenecks(
        self,
        session_name: str,
        threshold_percent: float = 5.0,
    ) -> Dict[str, Any]:
        """パフォーマンスボトルネックを分析

        Args:
            session_name: 分析するセッション名
            threshold_percent: ボトルネック判定の閾値（%）

        Returns:
            分析結果
        """
        self.logger.info(
            f"ボトルネック分析開始: session={session_name}, threshold={threshold_percent}%"
        )

        if session_name not in self.sessions:
            error_msg = f"Session '{session_name}' not found"
            self.logger.error(error_msg)
            return {"error": error_msg}

        session = self.sessions[session_name]

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
            "session": session_name,
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

    def generate_performance_report(self, session_name: str) -> str:
        """パフォーマンスレポートを生成

        Args:
            session_name: レポート対象のセッション名

        Returns:
            フォーマットされたレポート文字列
        """
        analysis = self.analyze_performance_bottlenecks(session_name)

        if "error" in analysis:
            return f"Error: {analysis['error']}"

        report_lines = [
            f"Performance Report: {session_name}",
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

    def save_profile_data(self, session_name: str, output_dir: Path) -> Path:
        """プロファイルデータを保存

        Args:
            session_name: 保存するセッション名
            output_dir: 出力ディレクトリ

        Returns:
            保存されたファイルのパス
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 分析結果を保存
        analysis = self.analyze_performance_bottlenecks(session_name)

        import json

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"profile_{session_name}_{timestamp}.json"
        output_file = output_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        return output_file

    def compare_sessions(self, session1: str, session2: str) -> Dict[str, Any]:
        """セッション間の比較

        Args:
            session1: 比較元セッション名
            session2: 比較先セッション名

        Returns:
            比較結果
        """
        if session1 not in self.sessions or session2 not in self.sessions:
            return {"error": "One or both sessions not found"}

        s1 = self.sessions[session1]
        s2 = self.sessions[session2]

        # 時間の比較
        time_comparison = {
            "session1_time": s1.total_time,
            "session2_time": s2.total_time,
            "time_difference": s2.total_time - s1.total_time,
            "time_ratio": s2.total_time / s1.total_time if s1.total_time > 0 else 0,
            "improvement_percent": (
                ((s1.total_time - s2.total_time) / s1.total_time * 100)
                if s1.total_time > 0
                else 0
            ),
        }

        # 関数レベルの比較
        function_comparison = {}
        all_functions = set(s1.function_profiles.keys()) | set(
            s2.function_profiles.keys()
        )

        for func_name in all_functions:
            f1 = s1.function_profiles.get(func_name)
            f2 = s2.function_profiles.get(func_name)

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
            "session1": session1,
            "session2": session2,
            "time_comparison": time_comparison,
            "function_comparison": function_comparison,
            "winner": (
                session1 if time_comparison["improvement_percent"] > 0 else session2
            ),
        }

    def _start_session(self, session_name: str) -> ProfilingSession:
        """セッションを開始"""
        with self._lock:
            session = ProfilingSession(
                name=session_name,
                start_time=time.perf_counter(),
            )
            self.active_sessions[session_name] = session
            return session

    def _end_session(self, session_name: str, profiler: cProfile.Profile):
        """セッションを終了"""
        with self._lock:
            if session_name in self.active_sessions:
                session = self.active_sessions.pop(session_name)
                session.end_time = time.perf_counter()
                session.total_time = session.duration

                # cProfileの結果を解析
                self._parse_cprofile_results(session, profiler)

                self.sessions[session_name] = session

    def _parse_cprofile_results(
        self, session: ProfilingSession, profiler: cProfile.Profile
    ):
        """cProfileの結果を解析"""
        # 統計を文字列バッファに出力
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats()

        # 結果を解析して関数プロファイルを作成
        stats_output = s.getvalue()
        lines = stats_output.split("\n")

        parsing_functions = False
        for line in lines:
            if "ncalls" in line and "tottime" in line:
                parsing_functions = True
                continue

            if parsing_functions and line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        ncalls = int(parts[0].split("/")[0])
                        tottime = float(parts[1])
                        cumtime = float(parts[3])

                        # 関数名を取得
                        func_info = " ".join(parts[5:])
                        if "(" in func_info:
                            func_name = func_info.split("(")[0]
                            module_name = (
                                func_name.split(".")[-2]
                                if "." in func_name
                                else "unknown"
                            )

                            profile = FunctionProfile(
                                name=func_name,
                                module=module_name,
                                calls=ncalls,
                                total_time=tottime,
                                cumulative_time=cumtime,
                                avg_time=tottime / ncalls if ncalls > 0 else 0,
                            )

                            session.function_profiles[func_name] = profile
                            session.total_calls += ncalls

                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"プロファイル結果解析エラー: {e}")
                        continue

    def _analyze_memory_usage(
        self, session: ProfilingSession
    ) -> Optional[Dict[str, Any]]:
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

    def _generate_performance_warnings(self, session: ProfilingSession) -> List[str]:
        """パフォーマンス警告を生成"""
        warnings = []

        # 実行時間が長い関数を検出
        for func_name, profile in session.function_profiles.items():
            if profile.avg_time > 0.1:  # 100ms以上
                warnings.append(
                    f"Slow function: {func_name} (avg: {profile.avg_time:.3f}s)"
                )

        # 呼び出し回数が多い関数を検出
        for func_name, profile in session.function_profiles.items():
            if profile.calls > 1000:
                warnings.append(
                    f"High call count: {func_name} ({profile.calls:,} calls)"
                )

        # メモリ使用量の警告
        memory_analysis = self._analyze_memory_usage(session)
        if memory_analysis and memory_analysis["peak_memory"] > 500:  # 500MB以上
            warnings.append(
                f"High memory usage: {memory_analysis['peak_memory']:.1f} MB"
            )

        return warnings

    def _get_memory_usage(self) -> Optional[int]:
        """現在のメモリ使用量を取得"""
        if self._memory_tracker:
            try:
                memory_usage = self._memory_tracker.memory_info().rss
                self.logger.debug(
                    f"メモリ使用量取得: {memory_usage / 1024 / 1024:.1f}MB"
                )
                return memory_usage
            except Exception as e:
                self.logger.error(f"メモリ使用量取得エラー: {e}")
                return None
        return None

    def _record_function_call(
        self, func_name: str, execution_time: float, memory_delta: Optional[int]
    ):
        """関数呼び出しを記録"""
        # 現在のアクティブセッションに記録
        for session in self.active_sessions.values():
            if func_name not in session.function_profiles:
                session.function_profiles[func_name] = FunctionProfile(
                    name=func_name,
                    module=func_name.split(".")[0] if "." in func_name else "unknown",
                )

            profile = session.function_profiles[func_name]
            profile.calls += 1
            profile.total_time += execution_time
            profile.avg_time = profile.total_time / profile.calls
            profile.max_time = max(profile.max_time, execution_time)
            profile.min_time = min(profile.min_time, execution_time)

            if memory_delta:
                profile.memory_delta = memory_delta

    def clear_sessions(self):
        """全セッションをクリア"""
        with self._lock:
            session_count = len(self.sessions)
            self.sessions.clear()
            self.active_sessions.clear()
            self.logger.info(
                f"全セッションクリア完了: {session_count}個のセッションを削除"
            )

    def get_session_names(self) -> List[str]:
        """セッション名のリストを取得"""
        session_names = list(self.sessions.keys())
        self.logger.debug(f"セッション名取得: {len(session_names)}個のセッション")
        return session_names
