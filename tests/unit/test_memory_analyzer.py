"""Tests for memory analyzer functionality"""

import time
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.performance.memory_analyzer import MemoryAnalyzer
from kumihan_formatter.core.performance.memory_types import MemoryLeak, MemorySnapshot


class TestMemoryAnalyzer:
    """Test the MemoryAnalyzer class"""

    def test_memory_analyzer_creation(self):
        """Test creating a memory analyzer"""
        analyzer = MemoryAnalyzer()

        assert analyzer.alert_callbacks == []
        assert analyzer.last_alert_time == {}
        assert analyzer.alert_cooldown == 300.0

    def test_calculate_slope(self):
        """Test slope calculation for trend analysis"""
        analyzer = MemoryAnalyzer()

        # Test increasing trend
        x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_values = [10.0, 15.0, 20.0, 25.0, 30.0]

        slope = analyzer._calculate_slope(x_values, y_values)
        assert slope > 0  # Should be positive for increasing trend

        # Test decreasing trend
        y_values = [30.0, 25.0, 20.0, 15.0, 10.0]
        slope = analyzer._calculate_slope(x_values, y_values)
        assert slope < 0  # Should be negative for decreasing trend

    def test_calculate_slope_empty_data(self):
        """Test slope calculation with empty data"""
        analyzer = MemoryAnalyzer()

        slope = analyzer._calculate_slope([], [])
        assert slope == 0.0

    def test_calculate_slope_single_point(self):
        """Test slope calculation with single data point"""
        analyzer = MemoryAnalyzer()

        slope = analyzer._calculate_slope([1.0], [10.0])
        assert slope == 0.0

    def test_get_memory_trend(self):
        """Test memory trend analysis"""
        analyzer = MemoryAnalyzer()

        # Create mock snapshots
        snapshots = []
        base_time = time.time()

        for i in range(10):
            snapshot = MemorySnapshot(
                timestamp=base_time + i * 60,  # 1 minute intervals
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=(900 - i * 5) * 1024 * 1024,  # MB to bytes
                process_memory=(100 + i * 5) * 1024 * 1024,  # MB to bytes
                gc_objects=1000 + i * 10,
                gc_collections=[i, i, i],
                custom_objects={},
            )
            snapshots.append(snapshot)

        trend = analyzer.get_memory_trend(snapshots, window_minutes=5)

        assert "window_minutes" in trend
        assert "data_points" in trend
        assert "memory_trend" in trend
        assert "gc_objects_trend" in trend
        assert "is_increasing" in trend
        assert trend["is_increasing"] == True  # Memory is increasing

    def test_get_memory_trend_empty_snapshots(self):
        """Test memory trend analysis with empty snapshots"""
        analyzer = MemoryAnalyzer()

        trend = analyzer.get_memory_trend([], window_minutes=5)

        assert "error" in trend
        assert trend["error"] == "No snapshots available"

    def test_generate_memory_report(self):
        """Test memory report generation"""
        analyzer = MemoryAnalyzer()

        # Create mock snapshots
        snapshots = []
        base_time = time.time()

        for i in range(5):
            snapshot = MemorySnapshot(
                timestamp=base_time + i * 60,
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=(900 - i * 2) * 1024 * 1024,  # MB to bytes
                process_memory=(100 + i * 2) * 1024 * 1024,  # MB to bytes
                gc_objects=1000 + i * 5,
                gc_collections=[i, i, i],
                custom_objects={},
            )
            snapshots.append(snapshot)

        report = analyzer.generate_memory_report(snapshots)

        assert "report_timestamp" in report
        assert "snapshot_count" in report
        assert "current_memory" in report
        assert "trend_analysis" in report
        assert "recommendations" in report

        # Check current memory
        current_memory = report["current_memory"]
        assert "process_memory_mb" in current_memory
        assert "available_memory_mb" in current_memory
        assert "memory_usage_ratio" in current_memory
        assert "gc_objects" in current_memory

    def test_generate_memory_report_with_trend(self):
        """Test memory report generation with trend analysis"""
        analyzer = MemoryAnalyzer()

        # Create mock snapshots
        snapshots = []
        base_time = time.time()

        for i in range(5):
            snapshot = MemorySnapshot(
                timestamp=base_time + i * 60,
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=(900 - i * 10) * 1024 * 1024,  # MB to bytes
                process_memory=(100 + i * 10) * 1024 * 1024,  # MB to bytes
                gc_objects=1000 + i * 5,
                gc_collections=[i, i, i],
                custom_objects={},
            )
            snapshots.append(snapshot)

        report = analyzer.generate_memory_report(
            snapshots, include_trend=True, trend_window_minutes=5
        )

        assert "trend_analysis" in report
        assert isinstance(report["trend_analysis"], dict)

        # Check that recommendations include trend warnings
        recommendations = report["recommendations"]
        trend_warning = any("急速に増加" in rec for rec in recommendations)
        assert trend_warning == True

    def test_generate_memory_report_with_leaks(self):
        """Test memory report generation with memory leaks"""
        analyzer = MemoryAnalyzer()

        # Create mock snapshots
        snapshots = []
        base_time = time.time()

        for i in range(3):
            snapshot = MemorySnapshot(
                timestamp=base_time + i * 60,
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=(900 - i * 2) * 1024 * 1024,  # MB to bytes
                process_memory=(100 + i * 2) * 1024 * 1024,  # MB to bytes
                gc_objects=1000 + i * 5,
                gc_collections=[i, i, i],
                custom_objects={},
            )
            snapshots.append(snapshot)

        # Create mock leaks
        leak1 = MemoryLeak("str", 100, 50, 1.0, base_time)
        leak2 = MemoryLeak("list", 200, 100, 2.0, base_time)
        leaks = [leak1, leak2]

        report = analyzer.generate_memory_report(snapshots, leaks=leaks)

        assert "memory_leaks" in report
        leak_summary = report["memory_leaks"]
        assert leak_summary["total_leaks"] == 2
        assert "leaks_by_severity" in leak_summary
        assert "top_leaks" in leak_summary
        assert len(leak_summary["top_leaks"]) == 2

    def test_generate_memory_report_empty_snapshots(self):
        """Test memory report generation with empty snapshots"""
        analyzer = MemoryAnalyzer()

        report = analyzer.generate_memory_report([])

        assert "error" in report
        assert report["error"] == "No snapshots available for report"

    def test_alert_callback_registration(self):
        """Test alert callback registration"""
        analyzer = MemoryAnalyzer()

        callback = MagicMock()
        analyzer.alert_callbacks.append(callback)

        assert len(analyzer.alert_callbacks) == 1
        assert analyzer.alert_callbacks[0] == callback

    def test_memory_recommendations(self):
        """Test memory usage recommendations"""
        analyzer = MemoryAnalyzer()

        # Create high memory usage snapshots
        snapshots = []
        base_time = time.time()

        for i in range(3):
            snapshot = MemorySnapshot(
                timestamp=base_time + i * 60,
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=(100 - i * 10) * 1024 * 1024,  # MB to bytes
                process_memory=(800 + i * 50) * 1024 * 1024,  # MB to bytes
                gc_objects=1000 + i * 100,
                gc_collections=[i, i, i],
                custom_objects={},
            )
            snapshots.append(snapshot)

        report = analyzer.generate_memory_report(snapshots)
        recommendations = report["recommendations"]

        # Should have recommendations for high memory usage
        high_memory_warning = any(
            "警告" in rec or "危険" in rec for rec in recommendations
        )
        assert high_memory_warning == True

    def test_critical_leak_recommendations(self):
        """Test recommendations for critical memory leaks"""
        analyzer = MemoryAnalyzer()

        # Create minimal snapshots
        snapshots = [
            MemorySnapshot(
                timestamp=time.time(),
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=900 * 1024 * 1024,  # MB to bytes
                process_memory=100 * 1024 * 1024,  # MB to bytes
                gc_objects=1000,
                gc_collections=[1, 1, 1],
                custom_objects={},
            )
        ]

        # Create critical leak
        leak = MemoryLeak("str", 1000, 500, 1.0, time.time())
        leak.severity = "critical"

        report = analyzer.generate_memory_report(snapshots, leaks=[leak])
        recommendations = report["recommendations"]

        # Should have recommendation for critical leak
        critical_warning = any("Critical" in rec for rec in recommendations)
        assert critical_warning == True

    def test_stats_tracking(self):
        """Test statistics tracking"""
        analyzer = MemoryAnalyzer()

        # Initially stats should be empty
        assert analyzer.stats.get("total_reports_generated", 0) == 0

        # Generate a report
        snapshots = [
            MemorySnapshot(
                timestamp=time.time(),
                total_memory=1000 * 1024 * 1024,  # 1GB in bytes
                available_memory=900 * 1024 * 1024,  # MB to bytes
                process_memory=100 * 1024 * 1024,  # MB to bytes
                gc_objects=1000,
                gc_collections=[1, 1, 1],
                custom_objects={},
            )
        ]

        analyzer.generate_memory_report(snapshots)

        # Stats should be updated
        assert analyzer.stats["total_reports_generated"] == 1
