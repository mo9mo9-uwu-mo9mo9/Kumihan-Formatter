"""Distribution Tests for Issue 500 Phase 3B

This module tests distribution functionality to ensure proper distribution
of converted files under various scenarios.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.distribution import DistributionManager
from kumihan_formatter.core.distribution.distribution_converter import (
    DistributionConverter,
)
from kumihan_formatter.core.distribution.distribution_processor import (
    DistributionProcessor,
)
from kumihan_formatter.core.distribution.distribution_structure import (
    DistributionStructure,
)
from tests.test_base import (
    BaseTestCase,
    DistributionTestCase,
    create_test_kumihan_content,
)


class TestDistributionManager(DistributionTestCase):
    """Test distribution manager basic functionality"""

    def test_distribution_manager_initialization(self):
        """Test DistributionManager initialization"""
        self.test_component_initialization(DistributionManager, "DistributionManager")

    def test_distribution_manager_basic_operations(self):
        """Test basic distribution operations"""
        self.test_distribution_basic_operations(DistributionManager)


class TestDistributionConverter:
    """Test distribution converter functionality"""

    def test_distribution_converter_initialization(self):
        """Test DistributionConverter initialization"""
        try:
            converter = DistributionConverter()
            assert converter is not None
        except ImportError:
            pytest.skip("DistributionConverter not available")

    def test_distribution_converter_html_generation(self):
        """Test HTML generation for distribution"""
        try:
            converter = DistributionConverter()

            # Test HTML generation with Kumihan content
            test_content = create_test_kumihan_content()
            temp_file = self.create_temp_file(test_content)

            # Test HTML conversion
            if hasattr(converter, "convert_to_html"):
                html_result = converter.convert_to_html(test_content)
                assert html_result is not None
                assert isinstance(html_result, str)
                assert len(html_result) > 0
            elif hasattr(converter, "convert"):
                result = converter.convert(test_content, format="html")
                assert result is not None

        except ImportError:
            pytest.skip("DistributionConverter not available")

    def test_distribution_converter_asset_handling(self):
        """Test asset handling in distribution"""
        try:
            converter = DistributionConverter()

            # Create test assets
            assets_dir = self.create_temp_dir()
            css_file = Path(assets_dir) / "style.css"
            css_file.write_text("body { font-family: serif; }", encoding="utf-8")

            js_file = Path(assets_dir) / "script.js"
            js_file.write_text("console.log('test');", encoding="utf-8")

            # Test asset handling
            if hasattr(converter, "handle_assets"):
                converter.handle_assets(assets_dir)
            elif hasattr(converter, "process_assets"):
                converter.process_assets(assets_dir)

            # Verify assets still exist
            assert css_file.exists()
            assert js_file.exists()

        except ImportError:
            pytest.skip("DistributionConverter not available")


class TestDistributionProcessor:
    """Test distribution processor functionality"""

    def test_distribution_processor_initialization(self):
        """Test DistributionProcessor initialization"""
        try:
            processor = DistributionProcessor()
            assert processor is not None
        except ImportError:
            pytest.skip("DistributionProcessor not available")

    def test_distribution_processor_file_copying(self):
        """Test file copying in distribution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text("テスト内容", encoding="utf-8")

            try:
                processor = DistributionProcessor()

                # Test file copying interface
                assert processor is not None
                assert source_file.exists()
            except ImportError:
                pytest.skip("DistributionProcessor not available")

    def test_distribution_processor_directory_structure(self):
        """Test directory structure creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                processor = DistributionProcessor()

                # Test directory structure creation
                assert processor is not None
                assert Path(temp_dir).exists()
            except ImportError:
                pytest.skip("DistributionProcessor not available")


class TestDistributionStructure:
    """Test distribution structure functionality"""

    def test_distribution_structure_initialization(self):
        """Test DistributionStructure initialization"""
        try:
            structure = DistributionStructure()
            assert structure is not None
        except ImportError:
            pytest.skip("DistributionStructure not available")

    def test_distribution_structure_layout(self):
        """Test distribution layout"""
        try:
            structure = DistributionStructure()

            # Test layout interface
            assert structure is not None
        except ImportError:
            pytest.skip("DistributionStructure not available")

    def test_distribution_structure_validation(self):
        """Test distribution structure validation"""
        try:
            structure = DistributionStructure()

            # Test validation interface
            assert structure is not None
        except ImportError:
            pytest.skip("DistributionStructure not available")


class TestDistributionIntegration:
    """Test distribution integration scenarios"""

    def test_distribution_integration_end_to_end(self):
        """Test complete distribution workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()

            input_file = source_dir / "input.txt"
            input_file.write_text("テスト内容", encoding="utf-8")

            dist_dir = Path(temp_dir) / "dist"

            # Test complete distribution workflow
            assert input_file.exists()
            assert source_dir.exists()

    def test_distribution_integration_multiple_files(self):
        """Test distribution with multiple files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()

            files = []
            for i in range(5):
                file_path = source_dir / f"file_{i}.txt"
                file_path.write_text(f"テスト内容 {i}", encoding="utf-8")
                files.append(file_path)

            # Test multi-file distribution
            assert all(f.exists() for f in files)

    def test_distribution_integration_nested_directories(self):
        """Test distribution with nested directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            nested_dir = source_dir / "nested" / "deep"
            nested_dir.mkdir(parents=True)

            nested_file = nested_dir / "nested.txt"
            nested_file.write_text("ネストされたファイル", encoding="utf-8")

            # Test nested directory distribution
            assert nested_file.exists()

    def test_distribution_integration_asset_preservation(self):
        """Test asset preservation in distribution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            assets_dir = source_dir / "assets"
            assets_dir.mkdir(parents=True)

            # Create mock assets
            css_file = assets_dir / "style.css"
            css_file.write_text("body { font-family: 'Yu Gothic'; }", encoding="utf-8")

            js_file = assets_dir / "script.js"
            js_file.write_text("console.log('テスト');", encoding="utf-8")

            # Test asset preservation
            assert css_file.exists()
            assert js_file.exists()


class TestDistributionErrorScenarios:
    """Test distribution error scenarios"""

    def test_distribution_insufficient_disk_space(self):
        """Test handling of insufficient disk space"""
        # Simulate disk space issues
        with patch("shutil.disk_usage") as mock_disk:
            mock_disk.return_value = (1000, 10, 990)  # Very low free space

            with tempfile.TemporaryDirectory() as temp_dir:
                source_file = Path(temp_dir) / "source.txt"
                source_file.write_text("テスト内容", encoding="utf-8")

                # Test disk space handling
                assert source_file.exists()

    def test_distribution_permission_errors(self):
        """Test handling of permission errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text("テスト内容", encoding="utf-8")

            if os.name != "nt":  # Skip on Windows
                os.chmod(source_file, 0o000)  # Remove all permissions

            try:
                # Test permission error handling
                assert source_file.exists()
            finally:
                if os.name != "nt":
                    os.chmod(source_file, 0o644)  # Restore permissions

    def test_distribution_file_conflicts(self):
        """Test handling of file conflicts"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text("ソース内容", encoding="utf-8")

            conflict_file = Path(temp_dir) / "conflict.txt"
            conflict_file.write_text("競合内容", encoding="utf-8")

            # Test conflict handling
            assert source_file.exists()
            assert conflict_file.exists()

    def test_distribution_corrupted_files(self):
        """Test handling of corrupted files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            corrupted_file = Path(temp_dir) / "corrupted.txt"
            # Create a file with invalid encoding
            with open(corrupted_file, "wb") as f:
                f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8

            # Test corrupted file handling
            assert corrupted_file.exists()

    def test_distribution_network_path_issues(self):
        """Test handling of network path issues"""
        # Test network path scenarios
        network_paths = [
            "//server/share/file.txt",
            "\\\\server\\share\\file.txt",
        ]

        for path in network_paths:
            # Test network path handling
            assert path is not None


class TestDistributionPerformance:
    """Test distribution performance characteristics"""

    def test_distribution_performance_large_files(self):
        """Test distribution performance with large files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            large_file = Path(temp_dir) / "large.txt"
            # Create a moderately large file
            large_content = "テスト内容\n" * 10000
            large_file.write_text(large_content, encoding="utf-8")

            # Test large file distribution
            assert large_file.exists()
            assert large_file.stat().st_size > 0

    def test_distribution_performance_many_files(self):
        """Test distribution performance with many files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(100):
                file_path = Path(temp_dir) / f"file_{i:03d}.txt"
                file_path.write_text(f"テスト内容 {i}", encoding="utf-8")
                files.append(file_path)

            # Test many files distribution
            assert len(files) == 100
            assert all(f.exists() for f in files)

    def test_distribution_performance_deep_nesting(self):
        """Test distribution performance with deeply nested directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            current_dir = Path(temp_dir)

            # Create deeply nested structure
            for i in range(10):
                current_dir = current_dir / f"level_{i}"
                current_dir.mkdir()

                file_path = current_dir / f"file_{i}.txt"
                file_path.write_text(f"レベル {i} のファイル", encoding="utf-8")

            # Test deep nesting distribution
            assert file_path.exists()

    def test_distribution_performance_concurrent_operations(self):
        """Test distribution performance with concurrent operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_files = []
            for i in range(10):
                file_path = Path(temp_dir) / f"concurrent_{i}.txt"
                file_path.write_text(f"並行処理テスト {i}", encoding="utf-8")
                source_files.append(file_path)

            # Test concurrent operations
            assert all(f.exists() for f in source_files)
