"""
ログ 依存関係トラッカー

モジュール依存関係の追跡・可視化
Issue #492 Phase 5A - log_analysis.py分割
"""

from typing import Any, Optional


class DependencyTracker:
    """Track and visualize module dependencies for debugging

    Provides dependency mapping and load tracking to help
    Claude Code understand module relationships and identify
    dependency-related issues.
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger
        self.dependencies: dict[str, set[str]] = {}
        self.load_times: dict[str, float] = {}
        self.load_order: list[str] = []

    def track_import(
        self,
        module_name: str,
        imported_from: Optional[str] = None,
        import_time: Optional[float] = None,
    ) -> None:
        """Track module import for dependency visualization

        Args:
            module_name: Name of imported module
            imported_from: Module that performed the import
            import_time: Time taken to import (seconds)
        """
        # Record dependency relationship
        if imported_from:
            if imported_from not in self.dependencies:
                self.dependencies[imported_from] = set()
            self.dependencies[imported_from].add(module_name)

        # Record import timing
        if import_time is not None:
            self.load_times[module_name] = import_time

        # Record load order
        if module_name not in self.load_order:
            self.load_order.append(module_name)

        # Log the import
        context = {
            "module": module_name,
            "imported_from": imported_from,
            "import_time_ms": round(import_time * 1000, 2) if import_time else None,
            "load_order_position": len(self.load_order),
        }

        self.logger.debug(
            f"Module imported: {module_name}",
            **context,
            claude_hint="Track dependencies for debugging import issues",
        )

    def get_dependency_map(self) -> dict[str, Any]:
        """Get complete dependency map for visualization

        Returns:
            Dictionary with dependency relationships and metrics
        """
        return {
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "load_times": self.load_times,
            "load_order": self.load_order,
            "total_modules": len(self.load_order),
            "slowest_imports": sorted(
                [(k, v) for k, v in self.load_times.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }

    def log_dependency_summary(self) -> None:
        """Log summary of all tracked dependencies"""
        dep_map = self.get_dependency_map()

        self.logger.info(
            "Dependency tracking summary",
            dependency_map=dep_map,
            claude_hint="Use dependency_map to understand module relationships",
        )
