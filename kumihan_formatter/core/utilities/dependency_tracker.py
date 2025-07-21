"""Dependency tracking functionality for structured logging

Single Responsibility Principle適用: 依存関係追跡機能の分離
Issue #476 Phase5対応 - structured_logger.py分割
"""

from __future__ import annotations

# json removed as unused
import time
from typing import Any, Optional

from .structured_logger_base import StructuredLogger


class DependencyTracker:
    """Tracks module dependencies and import relationships

    Helps understand code structure by:
    - Recording import times
    - Tracking dependency chains
    - Identifying circular dependencies
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.dependencies: dict[str, dict[str, Any]] = {}
        self.import_times: dict[str, float] = {}
        self.import_order: list[str] = []

    def track_import(
        self,
        module_name: str,
        imported_from: Optional[str] = None,
        import_time: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Track a module import

        Args:
            module_name: Name of the module being imported
            imported_from: Module that is importing this module
            import_time: Time taken to import (in seconds)
            success: Whether import was successful
            error: Error message if import failed
        """
        if module_name not in self.dependencies:
            self.dependencies[module_name] = {
                "imported_by": [],
                "import_count": 0,
                "total_import_time": 0.0,
                "first_imported_at": time.time(),
                "errors": [],
            }

        dep_info = self.dependencies[module_name]
        dep_info["import_count"] += 1

        if imported_from and imported_from not in dep_info["imported_by"]:
            dep_info["imported_by"].append(imported_from)

        if import_time:
            dep_info["total_import_time"] += import_time
            self.import_times[module_name] = import_time

        if not success and error:
            dep_info["errors"].append({"error": error, "timestamp": time.time()})

        self.import_order.append(module_name)

        # 循環依存の検出
        if imported_from and self._check_circular_dependency(
            module_name, imported_from
        ):
            self.logger.warning(
                f"Circular dependency detected: {module_name} <-> {imported_from}",
                circular_dependency=True,
                modules=[module_name, imported_from],
            )

    def get_dependency_map(self) -> dict[str, Any]:
        """Get complete dependency map

        Returns:
            Dict containing all dependency information
        """
        return {
            "dependencies": self.dependencies,
            "import_times": self.import_times,
            "import_order": self.import_order,
            "total_modules": len(self.dependencies),
            "total_import_time": sum(self.import_times.values()),
            "average_import_time": (
                sum(self.import_times.values()) / len(self.import_times)
                if self.import_times
                else 0
            ),
        }

    def log_dependency_summary(self) -> None:
        """Log a summary of all tracked dependencies"""
        dep_map = self.get_dependency_map()

        self.logger.info(
            "Dependency tracking summary",
            dependency_map=dep_map,
            slow_imports=[
                module
                for module, time in self.import_times.items()
                if time > 0.1  # 100ms以上を遅いと判定
            ],
        )

    def _check_circular_dependency(self, module_a: str, module_b: str) -> bool:
        """Check if there's a circular dependency between two modules"""
        # module_aがmodule_bをインポートし、module_bもmodule_aをインポートしているか
        if module_b in self.dependencies:
            return module_a in self.dependencies[module_b].get("imported_by", [])
        return False
