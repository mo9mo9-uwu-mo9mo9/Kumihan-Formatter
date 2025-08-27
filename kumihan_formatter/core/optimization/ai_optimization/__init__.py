"""
AI統合管理パッケージ

Phase B + AI統合管理・協調最適化・健全性監視
"""

from .coordinator import OptimizationCoordinator
from .integration_data import CoordinatedResult, IntegrationStatus, SystemHealth
from .integration_manager import AIIntegrationManager

__all__ = [
    "IntegrationStatus",
    "CoordinatedResult",
    "SystemHealth",
    "OptimizationCoordinator",
    "AIIntegrationManager",
]
