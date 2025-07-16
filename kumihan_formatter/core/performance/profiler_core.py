"""プロファイラーコア機能

このモジュールは、プロファイリングシステムの核となる
セッション管理、メモリ追跡、関数プロファイリング機能を提供します。
"""

import cProfile
import io
import pstats
import threading
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator

from ..utilities.logger import get_logger
from .profiler_types import FunctionProfile, ProfilingSession


class ProfilingSessionManager:
    """プロファイリングセッション管理クラス"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.sessions: dict[str, ProfilingSession] = {}
        self.active_sessions: dict[str, ProfilingSession] = {}
        self._lock = threading.Lock()

    def start_session(self, session_name: str) -> ProfilingSession:
        """セッションを開始"""
        with self._lock:
            session = ProfilingSession(
                name=session_name,
                start_time=time.perf_counter(),
            )
            self.active_sessions[session_name] = session
            self.logger.info(f"プロファイリングセッション開始: {session_name}")
            return session

    def end_session(self, session_name: str, profiler: cProfile.Profile) -> None:
        """セッションを終了"""
        with self._lock:
            if session_name in self.active_sessions:
                session = self.active_sessions.pop(session_name)
                session.end_time = time.perf_counter()
                session.total_time = session.duration

                # cProfileの結果を解析
                self._parse_cprofile_results(session, profiler)

                self.sessions[session_name] = session
                self.logger.info(f"プロファイリングセッション完了: {session_name}")

    def _parse_cprofile_results(
        self, session: ProfilingSession, profiler: cProfile.Profile
    ) -> None:
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

    def get_session(self, session_name: str) -> ProfilingSession | None:
        """セッションを取得"""
        return self.sessions.get(session_name)

    def clear_sessions(self) -> None:
        """全セッションをクリア"""
        with self._lock:
            session_count = len(self.sessions)
            self.sessions.clear()
            self.active_sessions.clear()
            self.logger.info(
                f"全セッションクリア完了: {session_count}個のセッションを削除"
            )

    def get_session_names(self) -> list[str]:
        """セッション名のリストを取得"""
        session_names = list(self.sessions.keys())
        self.logger.debug(f"セッション名取得: {len(session_names)}個のセッション")
        return session_names


class MemoryTracker:
    """メモリ追跡クラス"""

    def __init__(self, enable_memory_tracking: bool = True):
        self.logger = get_logger(__name__)
        self.enable_memory_tracking = enable_memory_tracking
        self._memory_tracker = None

        if enable_memory_tracking:
            try:
                import psutil

                self._memory_tracker = psutil.Process()
                self.logger.info("メモリ追跡機能を有効化")
            except ImportError:
                self.logger.warning("psutilが利用できないため、メモリ追跡機能を無効化")

    def get_memory_usage(self) -> int | None:
        """現在のメモリ使用量を取得"""
        if self._memory_tracker:
            try:
                memory_usage = self._memory_tracker.memory_info().rss
                self.logger.debug(
                    f"メモリ使用量取得: {memory_usage / 1024 / 1024:.1f}MB"
                )
                return int(memory_usage)
            except Exception as e:
                self.logger.error(f"メモリ使用量取得エラー: {e}")
                return None
        return None

    def take_memory_snapshot(self) -> dict[str, Any] | None:
        """メモリスナップショットを取得"""
        if self._memory_tracker:
            try:
                memory_info = {
                    "timestamp": time.perf_counter(),
                    "memory_mb": self._memory_tracker.memory_info().rss / 1024 / 1024,
                    "cpu_percent": self._memory_tracker.cpu_percent(),
                }
                self.logger.debug(
                    f"メモリスナップショット記録: {memory_info['memory_mb']:.1f}MB"
                )
                return memory_info
            except Exception as e:
                self.logger.error(f"メモリ情報取得エラー: {e}")
                return None
        return None


class FunctionProfiler:
    """関数プロファイリングクラス"""

    def __init__(
        self, session_manager: ProfilingSessionManager, memory_tracker: MemoryTracker
    ):
        self.session_manager = session_manager
        self.memory_tracker = memory_tracker
        self.logger = get_logger(__name__)

    def profile_function(
        self, func_name: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """関数プロファイリング用デコレーター"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.perf_counter()
                start_memory = self.memory_tracker.get_memory_usage()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    end_memory = self.memory_tracker.get_memory_usage()

                    execution_time = end_time - start_time
                    memory_delta = (
                        end_memory - start_memory
                        if start_memory and end_memory
                        else None
                    )

                    self._record_function_call(name, execution_time, memory_delta)

            return wrapper

        return decorator

    def _record_function_call(
        self, func_name: str, execution_time: float, memory_delta: int | None
    ) -> None:
        """関数呼び出しを記録"""
        # 現在のアクティブセッションに記録
        for session in self.session_manager.active_sessions.values():
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

    @contextmanager
    def profile_session(
        self, session_name: str
    ) -> Generator[ProfilingSession, None, None]:
        """プロファイリングセッションのコンテキストマネージャー"""
        session = self.session_manager.start_session(session_name)
        profiler = cProfile.Profile()

        try:
            # 初期メモリスナップショット
            memory_snapshot = self.memory_tracker.take_memory_snapshot()
            if memory_snapshot:
                session.memory_snapshots.append(memory_snapshot)

            profiler.enable()
            yield session

        finally:
            profiler.disable()
            self.logger.debug(f"プロファイリング測定終了: {session_name}")

            # 最終メモリスナップショット
            final_memory_snapshot = self.memory_tracker.take_memory_snapshot()
            if final_memory_snapshot:
                session.memory_snapshots.append(final_memory_snapshot)

            self.session_manager.end_session(session_name, profiler)
