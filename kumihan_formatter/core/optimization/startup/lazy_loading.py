"""
遅延ローディング機構

重いモジュールの遅延インポートによる
起動時間最適化システム
"""

import importlib
import sys
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class LazyImporter:
    """遅延インポート管理クラス"""

    def __init__(self) -> None:
        self._module_cache: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}

    def import_module(self, module_name: str) -> Any:
        """モジュールの遅延インポート"""
        if module_name in self._module_cache:
            return self._module_cache[module_name]

        try:
            start_time = time.time()
            module = importlib.import_module(module_name)
            import_time = time.time() - start_time

            self._module_cache[module_name] = module
            self._import_times[module_name] = import_time

            logger.debug(f"Lazy imported {module_name} in {import_time:.4f}s")
            return module

        except ImportError as e:
            logger.error(f"Failed to lazy import {module_name}: {e}")
            raise

    def get_import_stats(self) -> Dict[str, float]:
        """インポート統計取得"""
        return self._import_times.copy()

    def clear_cache(self) -> None:
        """キャッシュクリア"""
        self._module_cache.clear()
        self._import_times.clear()
        logger.info("Lazy import cache cleared")


class LazyModule:
    """遅延ロードモジュールプロキシ"""

    def __init__(self, module_name: str, importer: Optional[LazyImporter] = None):
        self._module_name = module_name
        self._importer = importer or LazyImporter()
        self._module: Optional[Any] = None

    def __getattr__(self, name: str) -> Any:
        """属性アクセス時にモジュールをロード"""
        if self._module is None:
            self._module = self._importer.import_module(self._module_name)

        return getattr(self._module, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """関数呼び出し時にモジュールをロード"""
        if self._module is None:
            self._module = self._importer.import_module(self._module_name)

        return self._module(*args, **kwargs)


def lazy_import(
    module_name: str, importer: Optional[LazyImporter] = None
) -> Callable[[F], F]:
    """遅延インポートデコレータ"""

    def decorator(func: F) -> F:
        _importer = importer or LazyImporter()
        _module: Optional[Any] = None

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal _module
            if _module is None:
                _module = _importer.import_module(module_name)

            # モジュールの関数を実行時に取得
            func_name = func.__name__
            if hasattr(_module, func_name):
                return getattr(_module, func_name)(*args, **kwargs)
            else:
                # 元の関数を実行
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class LazyLoadManager:
    """遅延ロード統合管理"""

    def __init__(self) -> None:
        self.importer = LazyImporter()
        self._lazy_modules: Dict[str, LazyModule] = {}

    def register_lazy_module(self, name: str, module_name: str) -> LazyModule:
        """遅延モジュール登録"""
        lazy_module = LazyModule(module_name, self.importer)
        self._lazy_modules[name] = lazy_module
        logger.info(f"Registered lazy module: {name} -> {module_name}")
        return lazy_module

    def get_lazy_module(self, name: str) -> Optional[LazyModule]:
        """遅延モジュール取得"""
        return self._lazy_modules.get(name)

    def preload_modules(self, module_names: list[str]) -> None:
        """重要モジュールの事前ロード"""
        for module_name in module_names:
            try:
                self.importer.import_module(module_name)
                logger.info(f"Preloaded module: {module_name}")
            except ImportError as e:
                logger.warning(f"Failed to preload {module_name}: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        import_stats = self.importer.get_import_stats()
        total_time = sum(import_stats.values())

        return {
            "total_modules": len(import_stats),
            "total_import_time": total_time,
            "average_import_time": (
                total_time / len(import_stats) if import_stats else 0
            ),
            "slowest_imports": sorted(
                import_stats.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "import_details": import_stats,
        }


# グローバル遅延ロードマネージャー
_global_lazy_manager = LazyLoadManager()


def get_lazy_manager() -> LazyLoadManager:
    """グローバル遅延ロードマネージャー取得"""
    return _global_lazy_manager


def benchmark_import_time(module_name: str, iterations: int = 10) -> Dict[str, float]:
    """インポート時間ベンチマーク"""
    import gc
    import statistics

    times = []

    for _ in range(iterations):
        # モジュールキャッシュクリア
        if module_name in sys.modules:
            del sys.modules[module_name]

        gc.collect()

        start_time = time.time()
        try:
            importlib.import_module(module_name)
            import_time = time.time() - start_time
            times.append(import_time)
        except ImportError as e:
            logger.error(f"Import benchmark failed for {module_name}: {e}")
            return {"error": str(e)}

    return {
        "module": module_name,
        "iterations": iterations,
        "min_time": min(times),
        "max_time": max(times),
        "avg_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
    }


def main() -> None:
    """CLI エントリーポイント"""
    import argparse
    import json
    import os

    os.makedirs("tmp", exist_ok=True)

    parser = argparse.ArgumentParser(description="Lazy loading benchmarks")
    parser.add_argument(
        "--module", type=str, help="Module to benchmark", default="json"
    )
    parser.add_argument(
        "--iterations", type=int, help="Number of iterations", default=10
    )
    parser.add_argument(
        "--test-lazy", action="store_true", help="Test lazy loading performance"
    )

    args = parser.parse_args()

    if args.test_lazy:
        # 遅延ローディングテスト
        manager = get_lazy_manager()

        # 重いモジュールをシミュレート
        test_modules = ["json", "urllib.request", "xml.etree.ElementTree"]

        print("Testing lazy loading performance...")
        start_time = time.time()

        for module_name in test_modules:
            manager.register_lazy_module(
                f"lazy_{module_name.replace('.', '_')}", module_name
            )

        setup_time = time.time() - start_time
        print(f"Lazy setup time: {setup_time:.4f}s")

        # 実際の使用時
        access_start = time.time()
        lazy_json = manager.get_lazy_module("lazy_json")
        if lazy_json:
            _ = lazy_json.dumps({"test": "data"})  # 実際にアクセス

        access_time = time.time() - access_start
        print(f"First access time: {access_time:.4f}s")

        # パフォーマンスレポート
        report = manager.get_performance_report()
        report_path = "tmp/lazy_loading_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Performance report saved: {report_path}")

    else:
        # 通常のベンチマーク
        result = benchmark_import_time(args.module, args.iterations)
        print(f"Import benchmark for {args.module}:")
        print(json.dumps(result, indent=2))

        # 結果保存
        benchmark_path = f"tmp/import_benchmark_{args.module.replace('.', '_')}.json"
        with open(benchmark_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Benchmark saved: {benchmark_path}")

    return 0


if __name__ == "__main__":
    exit(main())
