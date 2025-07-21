"""
高度なプロファイラー - パフォーマンス最適化用

詳細なパフォーマンス分析とボトルネック検出
Issue #402対応 - パフォーマンス最適化

このモジュールは、プロファイリング機能の統合レイヤーとして機能し、
後方互換性を維持しながら実際の処理は専用モジュールに委譲します。
"""

from contextlib import _GeneratorContextManager
from pathlib import Path
from typing import Any, Callable

from ..utilities.logger import get_logger
from .profiler_analysis import ProfilingAnalyzer, ProfilingReporter
from .profiler_core import FunctionProfiler, MemoryTracker, ProfilingSessionManager
from .profiler_types import ProfilingSession


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

        # コンポーネント初期化
        self.session_manager = ProfilingSessionManager()
        self.memory_tracker = MemoryTracker(enable_memory_tracking)
        self.function_profiler = FunctionProfiler(
            self.session_manager, self.memory_tracker
        )
        self.analyzer = ProfilingAnalyzer()
        self.reporter = ProfilingReporter(self.analyzer)

        self.logger.debug("プロファイラー初期化完了")

    def profile_session(
        self, session_name: str
    ) -> _GeneratorContextManager[ProfilingSession]:
        """プロファイリングセッションのコンテキストマネージャー

        Args:
            session_name: セッション名
        """
        return self.function_profiler.profile_session(session_name)

    def profile_function(
        self, func_name: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """関数プロファイリング用デコレーター

        Args:
            func_name: 関数名（未指定時は自動取得）
        """
        return self.function_profiler.profile_function(func_name)

    def analyze_performance_bottlenecks(
        self,
        session_name: str,
        threshold_percent: float = 5.0,
    ) -> dict[str, Any]:
        """パフォーマンスボトルネックを分析

        Args:
            session_name: 分析するセッション名
            threshold_percent: ボトルネック判定の閾値（%）

        Returns:
            分析結果
        """
        session = self.session_manager.get_session(session_name)
        if not session:
            error_msg = f"Session '{session_name}' not found"
            self.logger.error(error_msg)
            return {"error": error_msg}

        return self.analyzer.analyze_performance_bottlenecks(session, threshold_percent)

    def generate_performance_report(self, session_name: str) -> str:
        """パフォーマンスレポートを生成

        Args:
            session_name: レポート対象のセッション名

        Returns:
            フォーマットされたレポート文字列
        """
        session = self.session_manager.get_session(session_name)
        if not session:
            return f"Error: Session '{session_name}' not found"

        return self.reporter.generate_performance_report(session)

    def save_profile_data(self, session_name: str, output_dir: Path) -> Path:
        """プロファイルデータを保存

        Args:
            session_name: 保存するセッション名
            output_dir: 出力ディレクトリ

        Returns:
            保存されたファイルのパス
        """
        session = self.session_manager.get_session(session_name)
        if not session:
            raise ValueError(f"Session '{session_name}' not found")

        return self.reporter.save_profile_data(session, output_dir)

    def compare_sessions(self, session1: str, session2: str) -> dict[str, Any]:
        """セッション間の比較

        Args:
            session1: 比較元セッション名
            session2: 比較先セッション名

        Returns:
            比較結果
        """
        s1 = self.session_manager.get_session(session1)
        s2 = self.session_manager.get_session(session2)

        if not s1 or not s2:
            return {"error": "One or both sessions not found"}

        return self.analyzer.compare_sessions(s1, s2)

    def clear_sessions(self) -> None:
        """全セッションをクリア"""
        self.session_manager.clear_sessions()

    def get_session_names(self) -> list[str]:
        """セッション名のリストを取得"""
        return self.session_manager.get_session_names()

    # 後方互換性のためのプロパティ
    @property
    def sessions(self) -> dict[str, ProfilingSession]:
        """セッション辞書への読み取り専用アクセス"""
        return self.session_manager.sessions.copy()

    @property
    def active_sessions(self) -> dict[str, ProfilingSession]:
        """アクティブセッション辞書への読み取り専用アクセス"""
        return self.session_manager.active_sessions.copy()
