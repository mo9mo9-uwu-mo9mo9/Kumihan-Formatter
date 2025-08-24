"""プロファイラー関連のFactory関数群"""

from __future__ import annotations

from kumihan_formatter.core.utilities.logger import get_logger

from .core_profiler import MemoryProfiler
from .effect_reporter import OptimizationEffectReporter
from .leak_detector import MemoryLeakDetector
from .usage_analyzer import MemoryUsageAnalyzer

logger = get_logger(__name__)

# グローバルインスタンス
_global_profiler = MemoryProfiler()
_global_leak_detector = MemoryLeakDetector(_global_profiler._monitor)
_global_usage_analyzer = MemoryUsageAnalyzer(_global_profiler._monitor)
_global_effect_reporter = OptimizationEffectReporter()


def get_memory_profiler() -> MemoryProfiler:
    """グローバルメモリプロファイラーを取得します。"""
    return _global_profiler


def get_leak_detector() -> MemoryLeakDetector:
    """グローバルメモリリーク検出器を取得します。"""
    return _global_leak_detector


def get_usage_analyzer() -> MemoryUsageAnalyzer:
    """グローバルメモリ使用量分析器を取得します。"""
    return _global_usage_analyzer


def get_effect_reporter() -> OptimizationEffectReporter:
    """グローバル最適化効果レポーターを取得します。"""
    return _global_effect_reporter


# テスト関数群（既存のtest_*関数を維持するため）
def test_memory_profiler() -> None:
    """メモリプロファイラーのテストを実行します。"""
    try:
        profiler = get_memory_profiler()
        logger.info("メモリプロファイラーテスト開始")

        profiler.start_profiling()
        import time

        time.sleep(2)
        profiler.stop_profiling()

        stats = profiler.get_current_stats()
        logger.info(f"プロファイラーテスト完了: {stats}")

    except Exception as e:
        logger.error(f"メモリプロファイラーテストエラー: {str(e)}")


def test_leak_detection() -> None:
    """リーク検出のテストを実行します。"""
    try:
        detector = get_leak_detector()
        logger.info("リーク検出テスト開始")

        leaks = detector.detect_leaks(confidence_threshold=0.5)
        logger.info(f"検出されたリーク: {len(leaks)}")

        summary = detector.get_leak_summary()
        logger.info(f"リーク検出テスト完了: {summary}")

    except Exception as e:
        logger.error(f"リーク検出テストエラー: {str(e)}")


def test_usage_analysis() -> None:
    """使用量分析のテストを実行します。"""
    try:
        analyzer = get_usage_analyzer()
        profiler = get_memory_profiler()
        logger.info("使用量分析テスト開始")

        # サンプルスナップショットでテスト
        snapshots = [profiler._monitor.take_memory_snapshot()]
        analysis = analyzer.analyze_usage_patterns(snapshots)
        logger.info(f"使用量分析テスト完了: {len(analysis)} 項目")

    except Exception as e:
        logger.error(f"使用量分析テストエラー: {str(e)}")


def test_optimization_effect_reporting() -> None:
    """最適化効果レポートのテストを実行します。"""
    try:
        reporter = get_effect_reporter()
        profiler = get_memory_profiler()
        logger.info("最適化効果レポートテスト開始")

        reporter.set_baseline(profiler)
        reporter.record_optimization_point(
            profiler, "test_optimization", "テスト用最適化ポイント"
        )

        report = reporter.generate_effect_report()
        logger.info(f"最適化効果レポートテスト完了: {len(report)} 項目")

    except Exception as e:
        logger.error(f"最適化効果レポートテストエラー: {str(e)}")
