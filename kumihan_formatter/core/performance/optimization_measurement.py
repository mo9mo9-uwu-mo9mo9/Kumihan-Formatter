"""
最適化測定システム - ベースライン記録とパフォーマンス測定

最適化前後のパフォーマンス測定とベースラインデータ管理
Issue #476対応 - ファイルサイズ制限遵守
"""

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..performance import get_global_monitor
from ..utilities.logger import get_logger
from .benchmark import PerformanceBenchmarkSuite
from .benchmark_types import BenchmarkConfig
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


class OptimizationMeasurementSystem:
    """最適化測定システム

    機能:
    - ベースライン性能の記録
    - 最適化後のパフォーマンス測定
    - システム情報の記録
    """

    def __init__(self, baseline_dir: Optional[Path] = None) -> None:
        """測定システムを初期化

        Args:
            baseline_dir: ベースラインデータの保存ディレクトリ
        """
        self.logger = get_logger(__name__)
        self.baseline_dir = baseline_dir or Path("./performance_baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        # 測定ツール
        self.monitor = get_global_monitor()
        self.profiler = AdvancedProfiler()
        self.memory_monitor = MemoryMonitor()

        # データ保存
        self.baseline_data: dict[str, Any] = {}

    def capture_baseline(self, name: str, description: str = "") -> dict[str, Any]:
        """最適化前のベースライン性能を記録

        Args:
            name: ベースライン名
            description: 説明

        Returns:
            ベースラインデータ
        """
        print(f"📊 Capturing baseline: {name}")
        self.logger.info(f"ベースライン記録開始: {name}")

        # ベンチマークスイートを実行
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=False,  # 最適化前はキャッシュを無効
        )

        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        baseline_results = benchmark_suite.run_full_benchmark_suite()

        # ベースラインデータを構築
        baseline_data = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": baseline_results,
            "system_info": self.capture_system_info(),
        }

        # 保存
        self.baseline_data[name] = baseline_data
        baseline_file = self.baseline_dir / f"{name}_baseline.json"
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Baseline captured and saved to: {baseline_file}")
        self.logger.info(f"ベースライン保存完了: {baseline_file}")
        return baseline_data

    def measure_optimized_performance(self, optimization_name: str) -> dict[str, Any]:
        """最適化後のパフォーマンスを測定

        Args:
            optimization_name: 最適化名

        Returns:
            最適化後の結果
        """
        print(f"🔍 Measuring optimized performance: {optimization_name}")
        self.logger.info(f"最適化後測定開始: {optimization_name}")

        # 最適化後のベンチマークを実行
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=True,  # 最適化後はキャッシュを有効
        )

        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        optimized_results = benchmark_suite.run_full_benchmark_suite()

        self.logger.info(f"最適化後測定完了: {optimization_name}")
        return optimized_results

    def load_baseline(self, baseline_name: str) -> dict[str, Any] | None:
        """ベースラインデータを読み込み

        Args:
            baseline_name: ベースライン名

        Returns:
            ベースラインデータ
        """
        if baseline_name in self.baseline_data:
            return self.baseline_data[baseline_name]  # type: ignore

        baseline_file = self.baseline_dir / f"{baseline_name}_baseline.json"
        if baseline_file.exists():
            try:
                with open(baseline_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.baseline_data[baseline_name] = data
                    self.logger.info(f"ベースライン読み込み完了: {baseline_file}")
                    return data  # type: ignore
            except Exception as e:
                self.logger.error(f"ベースライン読み込みエラー: {e}")

        return None

    def capture_system_info(self) -> dict[str, Any]:
        """システム情報を記録

        Returns:
            システム情報
        """
        system_info: dict[str, Any] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": None,
            "memory_total": None,
        }

        try:
            import psutil

            system_info["cpu_count"] = psutil.cpu_count()
            system_info["memory_total"] = psutil.virtual_memory().total
        except ImportError:
            pass

        return system_info

    def list_baselines(self) -> list[str]:
        """利用可能なベースライン一覧を取得

        Returns:
            ベースライン名のリスト
        """
        baselines = list(self.baseline_data.keys())

        # ファイルからも検索
        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            name = baseline_file.stem.replace("_baseline", "")
            if name not in baselines:
                baselines.append(name)

        return sorted(baselines)

    def validate_baseline_consistency(self, baseline_name: str) -> dict[str, Any]:
        """ベースラインデータの一貫性を検証

        Args:
            baseline_name: ベースライン名

        Returns:
            検証結果
        """
        baseline_data = self.load_baseline(baseline_name)
        if not baseline_data:
            return {"valid": False, "error": "Baseline not found"}

        warnings: List[str] = []
        validation_result = {
            "valid": True,
            "warnings": warnings,
            "info": {
                "timestamp": baseline_data.get("timestamp"),
                "system_info": baseline_data.get("system_info"),
            },
        }

        # ベンチマーク結果の有無をチェック
        benchmark_results = baseline_data.get("benchmark_results")
        if not benchmark_results:
            validation_result["valid"] = False
            warnings.append("ベンチマーク結果が見つかりません")

        # タイムスタンプのチェック
        if baseline_data.get("timestamp"):
            try:
                baseline_time = datetime.fromisoformat(baseline_data["timestamp"])
                days_old = (datetime.now() - baseline_time).days
                if days_old > 30:
                    warnings.append(f"ベースラインが{days_old}日前と古いです")
            except ValueError:
                warnings.append("無効なタイムスタンプ形式")

        return validation_result
