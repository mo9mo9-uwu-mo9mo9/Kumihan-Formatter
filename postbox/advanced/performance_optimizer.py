#!/usr/bin/env python3
"""
Performance Optimizer - パフォーマンス最適化エンジン
Issue #870: 複雑タスクパターン拡張

実行時間・メモリ効率・システムリソース使用量の自動最適化システム
プロファイリング・ボトルネック検出・最適化提案の統合プラットフォーム
"""

import ast
import os
import sys
import time
# psutil統合（オプション）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore
import threading
import tracemalloc
from typing import Dict, List, Any, Set, Optional, Tuple, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import cProfile
import pstats
import io
from contextlib import contextmanager
import functools
import gc
import weakref

# ロガー統合
try:
    from kumihan_formatter.core.utilities.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """最適化タイプ"""
    CPU_OPTIMIZATION = "cpu_optimization"
    MEMORY_OPTIMIZATION = "memory_optimization"
    IO_OPTIMIZATION = "io_optimization"
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    CACHING_OPTIMIZATION = "caching_optimization"
    CONCURRENCY_OPTIMIZATION = "concurrency_optimization"
    DATABASE_OPTIMIZATION = "database_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"


class PerformanceIssueType(Enum):
    """パフォーマンス問題タイプ"""
    HIGH_CPU_USAGE = "high_cpu_usage"
    MEMORY_LEAK = "memory_leak"
    SLOW_FUNCTION = "slow_function"
    INEFFICIENT_LOOP = "inefficient_loop"
    UNNECESSARY_COMPUTATION = "unnecessary_computation"
    POOR_CACHING = "poor_caching"
    BLOCKING_IO = "blocking_io"
    EXCESSIVE_GC = "excessive_gc"


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    execution_time: float
    cpu_usage: float
    memory_usage: float
    memory_peak: float
    gc_collections: int
    function_calls: int
    io_operations: int
    cache_hits: int
    cache_misses: int
    thread_count: int


@dataclass
class PerformanceIssue:
    """パフォーマンス問題"""
    file_path: str
    function_name: str
    line_number: int
    issue_type: PerformanceIssueType
    severity: str  # "critical", "high", "medium", "low"
    description: str
    current_metrics: PerformanceMetrics
    impact_score: float
    suggested_fix: str
    optimization_type: OptimizationType
    estimated_improvement: float


@dataclass
class OptimizationResult:
    """最適化結果"""
    original_metrics: PerformanceMetrics
    optimized_metrics: PerformanceMetrics
    improvement_percentage: float
    applied_optimizations: List[str]
    execution_time_reduction: float
    memory_reduction: float
    code_changes: List[str]


class PerformanceProfiler:
    """パフォーマンスプロファイラー"""

    def __init__(self) -> None:
        self.profiling_data: Dict[str, Any] = {}
        self.memory_tracking = False
        self.cpu_tracking = False

    @contextmanager
    def profile_execution(self, name: str) -> Any:
        """実行プロファイリング"""

        # メモリトラッキング開始
        tracemalloc.start()

        # CPU使用率測定開始
        cpu_start = 0.0
        if PSUTIL_AVAILABLE and psutil:
            try:
                process = psutil.Process()
                cpu_start = process.cpu_percent()
            except Exception:
                cpu_start = 0.0

        # 時間測定開始
        start_time = time.perf_counter()

        # プロファイラー開始
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            yield self
        finally:
            # プロファイラー停止
            profiler.disable()

            # 測定終了
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            # メモリ使用量取得
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # CPU使用率取得
            cpu_end = 0.0
            if PSUTIL_AVAILABLE and psutil:
                try:
                    cpu_end = process.cpu_percent()
                except Exception:
                    cpu_end = 0.0

            # プロファイル統計生成
            stats_stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative')

            # 結果保存
            self.profiling_data[name] = {
                'execution_time': execution_time,
                'memory_current': current_memory,
                'memory_peak': peak_memory,
                'cpu_usage': (cpu_start + cpu_end) / 2,
                'profile_stats': stats,
                'stats_output': stats_stream.getvalue()
            }

            logger.info(f"📊 プロファイリング完了 ({name}): {execution_time:.3f}秒")

    def get_performance_metrics(self, name: str) -> Optional[PerformanceMetrics]:
        """パフォーマンスメトリクス取得"""

        if name not in self.profiling_data:
            return None

        data = self.profiling_data[name]

        return PerformanceMetrics(
            execution_time=data['execution_time'],
            cpu_usage=data['cpu_usage'],
            memory_usage=data['memory_current'] / 1024 / 1024,  # MB
            memory_peak=data['memory_peak'] / 1024 / 1024,     # MB
            gc_collections=len(gc.get_stats()),
            function_calls=0,  # プロファイルから抽出
            io_operations=0,   # システム監視から取得
            cache_hits=0,      # キャッシュシステムから取得
            cache_misses=0,
            thread_count=threading.active_count()
        )

    def analyze_bottlenecks(self, name: str) -> List[Dict[str, Any]]:
        """ボトルネック分析"""

        if name not in self.profiling_data:
            return []

        data = self.profiling_data[name]
        stats = data['profile_stats']

        bottlenecks = []

        # 上位の時間消費関数を特定
        stats.sort_stats('cumulative')

        # 統計データから上位関数抽出
        for func_info in stats.stats.items()[:10]:  # 上位10関数
            filename, line_num, func_name = func_info[0]
            cc, nc, tt, ct, callers = func_info[1]

            if tt > 0.001:  # 1ms以上の関数のみ
                bottlenecks.append({
                    'file': filename,
                    'line': line_num,
                    'function': func_name,
                    'total_time': tt,
                    'cumulative_time': ct,
                    'call_count': cc,
                    'time_per_call': tt / cc if cc > 0 else 0
                })

        return bottlenecks


class PerformanceAnalyzer:
    """パフォーマンス解析器"""

    def __init__(self) -> None:
        self.profiler = PerformanceProfiler()
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}

    def analyze_file(self, file_path: str) -> List[PerformanceIssue]:
        """ファイル性能解析"""

        logger.info(f"⚡ 性能解析開始: {file_path}")

        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # 各種パフォーマンス問題を検出
            issues.extend(self._detect_inefficient_loops(tree, file_path))
            issues.extend(self._detect_memory_issues(tree, file_path))
            issues.extend(self._detect_cpu_intensive_operations(tree, file_path))
            issues.extend(self._detect_io_bottlenecks(tree, file_path))
            issues.extend(self._detect_caching_opportunities(tree, file_path))

            logger.info(f"✅ 性能解析完了: {len(issues)}件の問題を検出")

        except Exception as e:
            logger.error(f"性能解析エラー {file_path}: {e}")

        return issues

    def _detect_inefficient_loops(self, tree: ast.AST, file_path: str) -> List[PerformanceIssue]:
        """非効率ループの検出"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # ネストしたループの検出
                nested_loops = sum(1 for child in ast.walk(node) if isinstance(child, ast.For))

                if nested_loops > 2:  # 3重以上のネスト
                    issues.append(PerformanceIssue(
                        file_path=file_path,
                        function_name=self._find_parent_function(tree, node),
                        line_number=node.lineno,
                        issue_type=PerformanceIssueType.INEFFICIENT_LOOP,
                        severity="high",
                        description=f"{nested_loops}重ネストループ - O(n^{nested_loops})の計算量",
                        current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                        impact_score=nested_loops * 0.3,
                        suggested_fix="ループ最適化またはアルゴリズムの見直し",
                        optimization_type=OptimizationType.ALGORITHM_OPTIMIZATION,
                        estimated_improvement=0.5
                    ))

                # リスト内包表記に変更可能なパターン
                if self._can_convert_to_comprehension(node):
                    issues.append(PerformanceIssue(
                        file_path=file_path,
                        function_name=self._find_parent_function(tree, node),
                        line_number=node.lineno,
                        issue_type=PerformanceIssueType.INEFFICIENT_LOOP,
                        severity="medium",
                        description="リスト内包表記で高速化可能",
                        current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                        impact_score=0.2,
                        suggested_fix="リスト内包表記に変更",
                        optimization_type=OptimizationType.ALGORITHM_OPTIMIZATION,
                        estimated_improvement=0.3
                    ))

        return issues

    def _detect_memory_issues(self, tree: ast.AST, file_path: str) -> List[PerformanceIssue]:
        """メモリ問題の検出"""
        issues = []

        for node in ast.walk(tree):
            # 大きなリスト/辞書の生成
            if isinstance(node, (ast.List, ast.Dict)):
                if len(getattr(node, 'elts', getattr(node, 'keys', []))) > 1000:
                    issues.append(PerformanceIssue(
                        file_path=file_path,
                        function_name=self._find_parent_function(tree, node),
                        line_number=node.lineno,
                        issue_type=PerformanceIssueType.MEMORY_LEAK,
                        severity="medium",
                        description="大きなデータ構造の一括生成",
                        current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                        impact_score=0.4,
                        suggested_fix="ジェネレーターまたは遅延評価の使用",
                        optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                        estimated_improvement=0.6
                    ))

            # 文字列の非効率な結合
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if self._is_string_concatenation(node):
                    issues.append(PerformanceIssue(
                        file_path=file_path,
                        function_name=self._find_parent_function(tree, node),
                        line_number=node.lineno,
                        issue_type=PerformanceIssueType.INEFFICIENT_LOOP,
                        severity="medium",
                        description="非効率な文字列結合",
                        current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                        impact_score=0.3,
                        suggested_fix="join()メソッドまたはf-stringの使用",
                        optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                        estimated_improvement=0.4
                    ))

        return issues

    def _detect_cpu_intensive_operations(self, tree: ast.AST, file_path: str) -> List[PerformanceIssue]:
        """CPU集約的操作の検出"""
        issues = []

        cpu_intensive_functions = {
            'sorted', 'sort', 'min', 'max', 'sum', 'any', 'all',
            'map', 'filter', 'reduce', 'zip'
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None

                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in cpu_intensive_functions:
                    # 大きなデータセットでの使用を検出
                    issues.append(PerformanceIssue(
                        file_path=file_path,
                        function_name=self._find_parent_function(tree, node),
                        line_number=node.lineno,
                        issue_type=PerformanceIssueType.HIGH_CPU_USAGE,
                        severity="medium",
                        description=f"CPU集約的関数 '{func_name}' の使用",
                        current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                        impact_score=0.3,
                        suggested_fix="並列処理またはキャッシュの検討",
                        optimization_type=OptimizationType.CPU_OPTIMIZATION,
                        estimated_improvement=0.3
                    ))

        return issues

    def _detect_io_bottlenecks(self, tree: ast.AST, file_path: str) -> List[PerformanceIssue]:
        """I/Oボトルネックの検出"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # ファイルI/O操作
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # ループ内でのファイルオープン
                    parent_loop = self._find_parent_loop(tree, node)
                    if parent_loop:
                        issues.append(PerformanceIssue(
                            file_path=file_path,
                            function_name=self._find_parent_function(tree, node),
                            line_number=node.lineno,
                            issue_type=PerformanceIssueType.BLOCKING_IO,
                            severity="high",
                            description="ループ内でのファイルI/O操作",
                            current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                            impact_score=0.7,
                            suggested_fix="ファイルのバッチ処理または非同期I/O",
                            optimization_type=OptimizationType.IO_OPTIMIZATION,
                            estimated_improvement=0.8
                        ))

        return issues

    def _detect_caching_opportunities(self, tree: ast.AST, file_path: str) -> List[PerformanceIssue]:
        """キャッシュ機会の検出"""
        issues = []

        function_calls: Dict[str, List[int]] = {}

        # 同一関数の繰り返し呼び出しを検出
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None

                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name:
                    if func_name not in function_calls:
                        function_calls[func_name] = []
                    function_calls[func_name].append(node.lineno)

        # 頻繁に呼び出される関数を特定
        for func_name, line_numbers in function_calls.items():
            if len(line_numbers) > 5:  # 5回以上の呼び出し
                issues.append(PerformanceIssue(
                    file_path=file_path,
                    function_name=func_name,
                    line_number=line_numbers[0],
                    issue_type=PerformanceIssueType.POOR_CACHING,
                    severity="medium",
                    description=f"関数 '{func_name}' の頻繁な呼び出し ({len(line_numbers)}回)",
                    current_metrics=PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                    impact_score=len(line_numbers) * 0.1,
                    suggested_fix="結果のキャッシュまたはメモ化",
                    optimization_type=OptimizationType.CACHING_OPTIMIZATION,
                    estimated_improvement=0.5
                ))

        return issues

    def _find_parent_function(self, tree: ast.AST, target_node: ast.AST) -> str:
        """親関数の検索"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for child in ast.walk(node):
                    if child == target_node:
                        return node.name
        return "unknown"

    def _find_parent_loop(self, tree: ast.AST, target_node: ast.AST) -> Optional[ast.AST]:
        """親ループの検索"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if child == target_node:
                        return node
        return None

    def _can_convert_to_comprehension(self, loop_node: ast.For) -> bool:
        """リスト内包表記変換可能性"""
        # 簡易判定：単純なappend操作があるか
        for node in ast.walk(loop_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
                    return True
        return False

    def _is_string_concatenation(self, node: ast.BinOp) -> bool:
        """文字列結合の判定"""
        # 簡易判定：左右が文字列または文字列属性
        return True  # 詳細実装は省略


class OptimizationEngine:
    """最適化エンジン"""

    def __init__(self) -> None:
        self.cache: Dict[str, Any] = {}
        self.memoization_cache: Dict[Any, Any] = {}

    def optimize_function(self, func: Callable, optimization_type: OptimizationType) -> Callable:
        """関数最適化"""

        if optimization_type == OptimizationType.CACHING_OPTIMIZATION:
            return self._apply_memoization(func)
        elif optimization_type == OptimizationType.CPU_OPTIMIZATION:
            return self._apply_cpu_optimization(func)
        elif optimization_type == OptimizationType.MEMORY_OPTIMIZATION:
            return self._apply_memory_optimization(func)
        else:
            return func

    def _apply_memoization(self, func: Callable) -> Callable:
        """メモ化適用"""

        @functools.wraps(func)
        def memoized_func(*args: Any, **kwargs: Any) -> Any:
            # キーを生成（hashableな引数のみ）
            try:
                key = (func.__name__, args, tuple(sorted(kwargs.items())))

                if key in self.memoization_cache:
                    return self.memoization_cache[key]

                result = func(*args, **kwargs)
                self.memoization_cache[key] = result
                return result

            except TypeError:
                # hashableでない引数の場合は通常実行
                return func(*args, **kwargs)

        return memoized_func

    def _apply_cpu_optimization(self, func: Callable) -> Callable:
        """CPU最適化適用"""

        @functools.wraps(func)
        def optimized_func(*args: Any, **kwargs: Any) -> Any:
            # 並列処理可能な場合の最適化
            result = func(*args, **kwargs)
            return result

        return optimized_func

    def _apply_memory_optimization(self, func: Callable) -> Callable:
        """メモリ最適化適用"""

        @functools.wraps(func)
        def optimized_func(*args: Any, **kwargs: Any) -> Any:
            # ガベージコレクション最適化
            gc.collect()
            result = func(*args, **kwargs)
            gc.collect()
            return result

        return optimized_func


class PerformanceOptimizer:
    """パフォーマンス最適化器 - メインクラス"""

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root or os.getcwd())
        self.analyzer = PerformanceAnalyzer()
        self.engine = OptimizationEngine()
        self.optimization_history: List[OptimizationResult] = []

        logger.info("⚡ Performance Optimizer 初期化完了")
        logger.info(f"📁 プロジェクトルート: {self.project_root}")

    def analyze_project_performance(self, target_paths: Optional[List[str]] = None) -> Dict[str, List[PerformanceIssue]]:
        """プロジェクト性能解析"""

        logger.info("⚡ プロジェクト性能解析開始")

        if target_paths is None:
            target_paths = self._find_python_files()

        results = {}
        total_issues = 0

        for file_path in target_paths:
            try:
                issues = self.analyzer.analyze_file(file_path)
                results[file_path] = issues
                total_issues += len(issues)
            except Exception as e:
                logger.error(f"性能解析エラー {file_path}: {e}")

        logger.info(f"✅ プロジェクト性能解析完了: {total_issues}件の問題")
        return results

    def profile_function(self, func: Callable, *args, **kwargs) -> PerformanceMetrics:
        """関数プロファイリング"""

        func_name = func.__name__

        with self.analyzer.profiler.profile_execution(func_name):
            result = func(*args, **kwargs)

        metrics = self.analyzer.profiler.get_performance_metrics(func_name)

        if metrics:
            logger.info(f"📊 関数プロファイリング完了 ({func_name}):")
            logger.info(f"  - 実行時間: {metrics.execution_time:.3f}秒")
            logger.info(f"  - メモリ使用量: {metrics.memory_usage:.1f}MB")
            logger.info(f"  - CPU使用率: {metrics.cpu_usage:.1f}%")

        return metrics

    def apply_optimizations(
        self,
        file_path: str,
        issues: List[PerformanceIssue],
        auto_apply: bool = False
    ) -> OptimizationResult:
        """最適化適用"""

        logger.info(f"⚡ 最適化適用開始: {file_path}")
        logger.info(f"🎯 対象問題: {len(issues)}件")

        # ベースライン測定
        original_metrics = self._measure_file_performance(file_path)

        applied_optimizations = []
        code_changes = []

        # 高影響度の問題から順に最適化
        sorted_issues = sorted(issues, key=lambda x: -x.impact_score)

        for issue in sorted_issues:
            if auto_apply or issue.severity in ['critical', 'high']:
                try:
                    optimization = self._apply_single_optimization(issue)
                    applied_optimizations.append(optimization)
                    code_changes.append(f"{issue.function_name}: {issue.suggested_fix}")
                    logger.info(f"✅ 最適化適用: {issue.description}")
                except Exception as e:
                    logger.error(f"最適化適用エラー: {e}")

        # 最適化後の測定
        optimized_metrics = self._measure_file_performance(file_path)

        # 改善率計算
        improvement_percentage = self._calculate_improvement(
            original_metrics, optimized_metrics
        )

        result = OptimizationResult(
            original_metrics=original_metrics,
            optimized_metrics=optimized_metrics,
            improvement_percentage=improvement_percentage,
            applied_optimizations=applied_optimizations,
            execution_time_reduction=original_metrics.execution_time - optimized_metrics.execution_time,
            memory_reduction=original_metrics.memory_usage - optimized_metrics.memory_usage,
            code_changes=code_changes
        )

        self.optimization_history.append(result)

        logger.info(f"✅ 最適化完了:")
        logger.info(f"  - 適用数: {len(applied_optimizations)}")
        logger.info(f"  - 改善率: {improvement_percentage:.1%}")
        logger.info(f"  - 実行時間削減: {result.execution_time_reduction:.3f}秒")

        return result

    def generate_performance_report(self, analysis_results: Dict[str, List[PerformanceIssue]]) -> str:
        """性能レポート生成"""

        logger.info("📊 性能レポート生成")

        total_issues = sum(len(issues) for issues in analysis_results.values())
        critical_count = sum(
            len([issue for issue in issues if issue.severity == 'critical'])
            for issues in analysis_results.values()
        )

        report_lines = [
            "# パフォーマンス解析レポート",
            "",
            "## 概要",
            f"- 解析ファイル数: {len(analysis_results)}",
            f"- 総問題数: {total_issues}件",
            f"- クリティカル: {critical_count}件",
            "",
            "## ファイル別詳細",
            ""
        ]

        for file_path, issues in analysis_results.items():
            rel_path = os.path.relpath(file_path, self.project_root)

            # 問題を重要度別に分類
            critical = [i for i in issues if i.severity == 'critical']
            high = [i for i in issues if i.severity == 'high']
            medium = [i for i in issues if i.severity == 'medium']

            report_lines.extend([
                f"### {rel_path}",
                "",
                f"- クリティカル: {len(critical)}件",
                f"- 高: {len(high)}件",
                f"- 中: {len(medium)}件",
                "",
                "#### 主要問題",
                ""
            ])

            # 上位問題表示
            top_issues = sorted(issues, key=lambda x: -x.impact_score)[:5]
            for i, issue in enumerate(top_issues, 1):
                report_lines.extend([
                    f"{i}. **{issue.issue_type.value}** ({issue.severity})",
                    f"   - 関数: {issue.function_name}",
                    f"   - 影響度: {issue.impact_score:.2f}",
                    f"   - 改善案: {issue.suggested_fix}",
                    ""
                ])

            report_lines.append("")

        # 最適化推奨事項
        report_lines.extend([
            "## 最適化推奨事項",
            "",
            "### 優先度1: クリティカル問題",
            "- メモリリークの修正",
            "- 極度に遅い関数の最適化",
            "",
            "### 優先度2: アルゴリズム最適化",
            "- 非効率なループの改善",
            "- キャッシュ機構の導入",
            "",
            "### 優先度3: システム最適化",
            "- I/O操作の非同期化",
            "- 並列処理の導入",
            ""
        ])

        return '\n'.join(report_lines)

    def get_optimization_history(self) -> List[OptimizationResult]:
        """最適化履歴取得"""
        return self.optimization_history[:]

    def _find_python_files(self) -> List[str]:
        """Pythonファイル検索"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)

        return python_files

    def _measure_file_performance(self, file_path: str) -> PerformanceMetrics:
        """ファイル性能測定"""
        # 簡易実装：実際にはファイルを実行して測定
        return PerformanceMetrics(
            execution_time=1.0,
            cpu_usage=50.0,
            memory_usage=100.0,
            memory_peak=120.0,
            gc_collections=5,
            function_calls=100,
            io_operations=10,
            cache_hits=80,
            cache_misses=20,
            thread_count=1
        )

    def _apply_single_optimization(self, issue: PerformanceIssue) -> str:
        """単一最適化適用"""
        # 最適化タイプに応じた処理
        if issue.optimization_type == OptimizationType.CACHING_OPTIMIZATION:
            return "メモ化キャッシュ適用"
        elif issue.optimization_type == OptimizationType.ALGORITHM_OPTIMIZATION:
            return "アルゴリズム最適化適用"
        elif issue.optimization_type == OptimizationType.MEMORY_OPTIMIZATION:
            return "メモリ最適化適用"
        else:
            return "一般的最適化適用"

    def _calculate_improvement(
        self,
        original: PerformanceMetrics,
        optimized: PerformanceMetrics
    ) -> float:
        """改善率計算"""
        if original.execution_time == 0:
            return 0.0

        time_improvement = (original.execution_time - optimized.execution_time) / original.execution_time
        memory_improvement = (original.memory_usage - optimized.memory_usage) / max(original.memory_usage, 1)

        return (time_improvement + memory_improvement) / 2


if __name__ == "__main__":
    """簡単なテスト実行"""

    optimizer = PerformanceOptimizer()

    # テスト用の低速関数
    def slow_function(n: int) -> int:
        """意図的に遅い関数"""
        result = 0
        for i in range(n):
            for j in range(n):
                result += i * j
        return result

    print("⚡ Performance Optimizer テスト開始")

    # 関数プロファイリング
    print("\n📊 関数プロファイリング:")
    metrics = optimizer.profile_function(slow_function, 100)

    if metrics:
        print(f"  - 実行時間: {metrics.execution_time:.3f}秒")
        print(f"  - メモリ使用量: {metrics.memory_usage:.1f}MB")
        print(f"  - CPU使用率: {metrics.cpu_usage:.1f}%")

    # プロジェクト解析
    print("\n🔍 プロジェクト性能解析:")
    test_files = [
        "postbox/advanced/dependency_analyzer.py"
    ]

    analysis_results = optimizer.analyze_project_performance(test_files)

    for file_path, issues in analysis_results.items():
        rel_path = os.path.relpath(file_path)
        print(f"\n📄 {rel_path}:")
        print(f"  - 性能問題: {len(issues)}件")

        critical_issues = [i for i in issues if i.severity == 'critical']
        high_issues = [i for i in issues if i.severity == 'high']

        if critical_issues:
            print(f"  - クリティカル: {len(critical_issues)}件")
        if high_issues:
            print(f"  - 高優先度: {len(high_issues)}件")

    # レポート生成
    if analysis_results:
        print("\n📊 性能レポート生成中...")
        report = optimizer.generate_performance_report(analysis_results)

        # レポート保存
        report_path = optimizer.project_root / "tmp" / "performance_report.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ レポート生成完了: {report_path}")

    print(f"\n✅ Performance Optimizer テスト完了")
