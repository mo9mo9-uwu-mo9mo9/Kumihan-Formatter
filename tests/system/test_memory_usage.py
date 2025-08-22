"""メモリ使用量のシステム統合テスト

システム全体のメモリ使用パターンを監視し、
リソース効率性とメモリリークの検出を行う。
"""

import gc
import os
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class MemoryMonitor:
    """メモリ使用量監視クラス"""

    def __init__(self) -> None:
        self.start_memory: Optional[int] = None
        self.snapshots: List[Tuple[float, int, int]] = []
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None

    def start_monitoring(self) -> None:
        """監視開始"""
        if self.process:
            self.start_memory = self.process.memory_info().rss
            tracemalloc.start()
            logger.info(f"メモリ監視開始: {self.start_memory / 1024 / 1024:.1f}MB")

    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """スナップショット取得"""
        if not self.process:
            return {"error": "psutil not available"}

        current_memory = self.process.memory_info().rss
        current_time = time.time()

        # tracemalloc情報取得
        trace_current, trace_peak = tracemalloc.get_traced_memory()

        snapshot = {
            "timestamp": current_time,
            "label": label,
            "rss_memory": current_memory,
            "memory_delta": current_memory - (self.start_memory or 0),
            "traced_current": trace_current,
            "traced_peak": trace_peak,
            "memory_mb": current_memory / 1024 / 1024,
            "delta_mb": (current_memory - (self.start_memory or 0)) / 1024 / 1024,
        }

        self.snapshots.append((current_time, current_memory, trace_current))
        return snapshot

    def stop_monitoring(self) -> Dict[str, Any]:
        """監視終了"""
        final_snapshot = self.take_snapshot("final")
        tracemalloc.stop()

        if self.snapshots:
            peak_memory = max(snapshot[1] for snapshot in self.snapshots)
            memory_growth = final_snapshot["memory_delta"]

            return {
                "final_memory_mb": final_snapshot["memory_mb"],
                "peak_memory_mb": peak_memory / 1024 / 1024,
                "memory_growth_mb": memory_growth / 1024 / 1024,
                "snapshots": len(self.snapshots),
                "duration": (
                    self.snapshots[-1][0] - self.snapshots[0][0] if len(self.snapshots) > 1 else 0
                ),
            }

        return {"error": "No snapshots taken"}

    def get_memory_stats(self) -> Dict[str, Any]:
        """現在のメモリ統計を取得"""
        if not self.process:
            return {"error": "psutil not available"}

        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # システム全体のメモリ情報
            system_memory = psutil.virtual_memory()

            return {
                "process": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": memory_percent,
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "vms_mb": memory_info.vms / 1024 / 1024,
                },
                "system": {
                    "total_gb": system_memory.total / 1024 / 1024 / 1024,
                    "available_gb": system_memory.available / 1024 / 1024 / 1024,
                    "percent_used": system_memory.percent,
                },
            }
        except Exception as e:
            return {"error": str(e)}


class TestMemoryUsage:
    """メモリ使用量のテスト"""

    def setup_method(self) -> None:
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.monitor = MemoryMonitor()

        # テストデータの準備
        self.small_data = "x" * 1000  # 1KB
        self.medium_data = "x" * 100_000  # 100KB
        self.large_data = "x" * 10_000_000  # 10MB

        logger.info(f"テスト用一時ディレクトリ: {self.temp_dir}")

    def teardown_method(self) -> None:
        """各テストメソッド実行後のクリーンアップ"""
        import shutil

        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"一時ディレクトリを削除: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"一時ディレクトリの削除に失敗: {e}")

        # ガベージコレクション実行
        gc.collect()

    def generate_test_data(self, size_mb: float) -> str:
        """指定サイズのテストデータ生成"""
        size_bytes = int(size_mb * 1024 * 1024)
        return "x" * size_bytes

    def simulate_file_processing(self, data: str, iterations: int = 1) -> Dict[str, Any]:
        """ファイル処理のシミュレート"""
        results = []

        for i in range(iterations):
            # データ処理シミュレート
            processed_data = data.upper()
            processed_data = processed_data.replace("X", "O")
            processed_data = processed_data[: len(processed_data) // 2]  # データサイズ削減

            # メモリスナップショット
            snapshot = self.monitor.take_snapshot(f"iteration_{i}")
            results.append(
                {
                    "iteration": i,
                    "processed_size": len(processed_data),
                    "memory_snapshot": snapshot,
                }
            )

            # 短時間待機
            time.sleep(0.01)

        return {
            "iterations": iterations,
            "results": results,
            "final_processed_size": len(processed_data) if results else 0,
        }

    def simulate_memory_leak(self, leak_size_mb: float = 1.0) -> List[str]:
        """メモリリークのシミュレート（テスト用）"""
        leak_data = []
        chunk_size = int(leak_size_mb * 1024 * 1024 / 10)  # 10チャンクに分割

        for i in range(10):
            chunk = "x" * chunk_size
            leak_data.append(chunk)
            time.sleep(0.01)

        return leak_data

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_基本監視(self) -> None:
        """メモリ使用量: 基本監視機能の確認"""
        # Given: メモリ監視開始
        self.monitor.start_monitoring()
        initial_stats = self.monitor.get_memory_stats()

        # When: 基本的な処理実行
        self.monitor.take_snapshot("start")
        data = self.generate_test_data(1.0)  # 1MB
        self.monitor.take_snapshot("after_generation")

        processed = data.upper()
        self.monitor.take_snapshot("after_processing")

        del data, processed
        gc.collect()
        self.monitor.take_snapshot("after_cleanup")

        # Then: 監視結果確認
        final_stats = self.monitor.stop_monitoring()

        assert "final_memory_mb" in final_stats, "最終メモリ使用量が記録されていない"
        assert "peak_memory_mb" in final_stats, "ピークメモリ使用量が記録されていない"
        assert final_stats["snapshots"] >= 4, "スナップショット数が不足"

        # メモリ使用量の妥当性確認
        assert final_stats["final_memory_mb"] > 0, "メモリ使用量が0"
        assert (
            final_stats["peak_memory_mb"] >= final_stats["final_memory_mb"]
        ), "ピークメモリがファイナルメモリより小さい"

        logger.info(
            f"基本監視確認完了: 最終{final_stats['final_memory_mb']:.1f}MB, "
            f"ピーク{final_stats['peak_memory_mb']:.1f}MB"
        )

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_小規模データ処理(self) -> None:
        """メモリ使用量: 小規模データ処理での使用量"""
        # Given: 小規模データ処理
        self.monitor.start_monitoring()

        # When: 小規模データ処理実行
        processing_result = self.simulate_file_processing(self.small_data, 10)

        # Then: メモリ使用量確認
        final_stats = self.monitor.stop_monitoring()

        # 小規模データ処理では大幅なメモリ増加はないはず
        assert (
            final_stats["memory_growth_mb"] < 50
        ), f"小規模データ処理でメモリ使用量が増加しすぎ: {final_stats['memory_growth_mb']:.1f}MB"

        # 処理が完了していることを確認
        assert processing_result["iterations"] == 10, "処理が完了していない"

        logger.info(f"小規模データ処理完了: メモリ増加{final_stats['memory_growth_mb']:.1f}MB")

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_中規模データ処理(self) -> None:
        """メモリ使用量: 中規模データ処理での使用量"""
        # Given: 中規模データ処理
        self.monitor.start_monitoring()

        # When: 中規模データ処理実行
        processing_result = self.simulate_file_processing(self.medium_data, 5)

        # Then: メモリ使用量確認
        final_stats = self.monitor.stop_monitoring()

        # 中規模データ処理での適度なメモリ使用
        assert (
            final_stats["memory_growth_mb"] < 100
        ), f"中規模データ処理でメモリ使用量が多すぎ: {final_stats['memory_growth_mb']:.1f}MB"
        assert final_stats["memory_growth_mb"] >= 0, "メモリ使用量が負の値"

        # ピークメモリの確認
        assert (
            final_stats["peak_memory_mb"] > final_stats["final_memory_mb"] * 0.9
        ), "ピークメモリが異常に低い"

        logger.info(
            f"中規模データ処理完了: メモリ増加{final_stats['memory_growth_mb']:.1f}MB, "
            f"ピーク{final_stats['peak_memory_mb']:.1f}MB"
        )

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_大規模データ処理(self) -> None:
        """メモリ使用量: 大規模データ処理での使用量"""
        # Given: 大規模データ処理
        self.monitor.start_monitoring()

        # When: 大規模データ処理実行
        processing_result = self.simulate_file_processing(self.large_data, 2)

        # Then: メモリ使用量確認
        final_stats = self.monitor.stop_monitoring()

        # 大規模データ処理での妥当なメモリ使用（指示書基準: 100MB以内）
        assert (
            final_stats["memory_growth_mb"] < 100
        ), f"大規模データ処理でメモリ使用量基準超過: {final_stats['memory_growth_mb']:.1f}MB"

        # 処理完了確認
        assert processing_result["iterations"] == 2, "大規模データ処理が完了していない"

        logger.info(f"大規模データ処理完了: メモリ増加{final_stats['memory_growth_mb']:.1f}MB")

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_リーク検出(self) -> None:
        """メモリ使用量: メモリリークの検出"""
        # Given: メモリリーク検出テスト
        self.monitor.start_monitoring()
        initial_snapshot = self.monitor.take_snapshot("initial")

        # When: 意図的なメモリリークシミュレート
        leak_data = self.simulate_memory_leak(2.0)  # 2MBのリーク
        leak_snapshot = self.monitor.take_snapshot("after_leak")

        # メモリリークデータを保持（リークシミュレート）
        time.sleep(0.1)
        retention_snapshot = self.monitor.take_snapshot("retention")

        # Then: リーク検出確認
        final_stats = self.monitor.stop_monitoring()

        # リークによるメモリ増加の検出
        memory_increase = leak_snapshot["memory_delta"] - initial_snapshot["memory_delta"]
        assert memory_increase > 1, f"メモリリークが検出されていない: {memory_increase:.1f}MB"

        # 継続的なメモリ保持の確認
        retention_increase = retention_snapshot["memory_delta"] - initial_snapshot["memory_delta"]
        assert retention_increase > 1, "メモリリークが解放されている"

        # リークデータのクリーンアップ
        del leak_data
        gc.collect()

        logger.info(
            f"メモリリーク検出完了: 増加{memory_increase:.1f}MB, " f"保持{retention_increase:.1f}MB"
        )

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_並列処理シミュレート(self) -> None:
        """メモリ使用量: 並列処理でのメモリ使用パターン"""
        # Given: 並列処理シミュレート
        self.monitor.start_monitoring()

        # When: 複数データの同時処理シミュレート
        data_sets = [
            self.generate_test_data(0.5),  # 0.5MB
            self.generate_test_data(0.5),  # 0.5MB
            self.generate_test_data(0.5),  # 0.5MB
        ]

        # 同時処理シミュレート
        processed_sets = []
        for i, data in enumerate(data_sets):
            self.monitor.take_snapshot(f"processing_{i}")
            processed = data.upper().replace("X", "O")
            processed_sets.append(processed)

        self.monitor.take_snapshot("all_processed")

        # データクリーンアップ
        del data_sets, processed_sets
        gc.collect()
        self.monitor.take_snapshot("cleaned_up")

        # Then: 並列処理メモリパターン確認
        final_stats = self.monitor.stop_monitoring()

        # 同時処理でのメモリ効率性確認
        assert (
            final_stats["memory_growth_mb"] < 80
        ), f"並列処理でメモリ使用量が多すぎ: {final_stats['memory_growth_mb']:.1f}MB"

        # スナップショット数の確認
        assert final_stats["snapshots"] >= 6, "並列処理のスナップショットが不足"

        logger.info(f"並列処理シミュレート完了: メモリ増加{final_stats['memory_growth_mb']:.1f}MB")

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_長時間処理(self) -> None:
        """メモリ使用量: 長時間処理でのメモリ安定性"""
        # Given: 長時間処理シミュレート
        self.monitor.start_monitoring()

        # When: 長時間にわたる繰り返し処理
        iterations = 20
        for i in range(iterations):
            # データ生成・処理・削除のサイクル
            temp_data = self.generate_test_data(0.2)  # 0.2MB
            processed = temp_data.upper()
            del temp_data, processed

            if i % 5 == 0:  # 5回ごとにスナップショット
                gc.collect()
                self.monitor.take_snapshot(f"cycle_{i}")

            time.sleep(0.02)  # 20ms待機

        # Then: 長時間処理メモリ安定性確認
        final_stats = self.monitor.stop_monitoring()

        # メモリの安定性確認（大幅な増加がないこと）
        assert (
            final_stats["memory_growth_mb"] < 50
        ), f"長時間処理でメモリが蓄積: {final_stats['memory_growth_mb']:.1f}MB"

        # 処理時間の確認
        assert final_stats["duration"] > 0.3, "処理時間が短すぎる"
        assert final_stats["duration"] < 10, "処理時間が長すぎる"

        logger.info(
            f"長時間処理完了: {iterations}サイクル, "
            f"メモリ増加{final_stats['memory_growth_mb']:.1f}MB, "
            f"所要時間{final_stats['duration']:.1f}秒"
        )

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_システム統計(self) -> None:
        """メモリ使用量: システム全体の統計確認"""
        # Given: システム統計取得
        initial_stats = self.monitor.get_memory_stats()

        # When: 処理実行
        self.monitor.start_monitoring()
        test_data = self.generate_test_data(5.0)  # 5MB
        processing_stats = self.monitor.get_memory_stats()
        del test_data
        gc.collect()
        final_stats = self.monitor.stop_monitoring()

        # Then: システム統計確認
        assert "process" in initial_stats, "プロセス統計が取得されていない"
        assert "system" in initial_stats, "システム統計が取得されていない"

        # プロセス統計の妥当性
        process_stats = processing_stats["process"]
        assert process_stats["rss_mb"] > 0, "プロセスメモリ使用量が0"
        assert process_stats["percent"] >= 0, "メモリ使用率が負の値"

        # システム統計の妥当性
        system_stats = processing_stats["system"]
        assert system_stats["total_gb"] > 0, "システム総メモリが0"
        assert 0 <= system_stats["percent_used"] <= 100, "システムメモリ使用率が異常"

        logger.info(
            f"システム統計確認完了: プロセス{process_stats['rss_mb']:.1f}MB, "
            f"システム使用率{system_stats['percent_used']:.1f}%"
        )

    @pytest.mark.system
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_メモリ使用量_ガベージコレクション効果(self) -> None:
        """メモリ使用量: ガベージコレクションの効果確認"""
        # Given: GC効果測定
        self.monitor.start_monitoring()
        initial_snapshot = self.monitor.take_snapshot("initial")

        # When: 大量データ生成とGC
        large_objects = []
        for i in range(10):
            obj = self.generate_test_data(1.0)  # 1MB x 10 = 10MB
            large_objects.append(obj)

        before_gc_snapshot = self.monitor.take_snapshot("before_gc")

        # オブジェクト削除
        del large_objects

        # 明示的GC実行
        collected = gc.collect()
        after_gc_snapshot = self.monitor.take_snapshot("after_gc")

        # Then: GC効果確認
        final_stats = self.monitor.stop_monitoring()

        # GC前後のメモリ差分
        memory_before_gc = before_gc_snapshot["memory_delta"]
        memory_after_gc = after_gc_snapshot["memory_delta"]
        gc_recovery = memory_before_gc - memory_after_gc

        # GCによるメモリ回収確認
        assert gc_recovery > 0, f"GCによるメモリ回収が確認できない: {gc_recovery:.1f}MB"
        assert collected >= 0, "GCによる回収オブジェクト数が負の値"

        logger.info(f"GC効果確認完了: 回収{gc_recovery:.1f}MB, " f"オブジェクト{collected}個回収")
