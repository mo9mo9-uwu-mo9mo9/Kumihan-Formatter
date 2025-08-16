"""
Performance test cases for Kumihan-Formatter.

Tests processing speed, memory usage, and scalability with large datasets.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List

import psutil
import pytest

from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions
from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser
from kumihan_formatter.core.keyword_parsing.validator import KeywordValidator
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


class PerformanceMonitor:
    """Helper class for monitoring performance metrics."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_memory = None

    def start(self):
        """Start performance monitoring."""
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics."""
        end_time = time.perf_counter()
        end_memory = self.process.memory_info().rss

        return {
            "duration": end_time - self.start_time,
            "memory_delta": end_memory - self.start_memory,
            "memory_peak": self.process.memory_info().rss,
            "cpu_percent": self.process.cpu_percent(),
        }


@pytest.mark.performance
@pytest.mark.slow
class TestParsingPerformance:
    """Test parsing performance with various data sizes."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.monitor = PerformanceMonitor()

    def generate_test_content(self, size_factor: int) -> str:
        """Generate test content of specified size."""
        base_content = """#見出し1
テストセクション{num}
##

これはパフォーマンステスト用のセクション{num}です。
#太字 重要な情報{num}#を含んでいます。

#リスト
- 項目{num}-1
- 項目{num}-2
- 項目{num}-3
##

通常のテキスト内容がここに続きます。
#下線 強調部分{num}#もあります。

"""

        # Generate content based on size factor
        sections = []
        for i in range(size_factor):
            sections.append(base_content.format(num=i))

        return "\n".join(sections)

    @pytest.mark.benchmark(group="parsing_small")
    def test_small_content_parsing(self, benchmark):
        """Benchmark parsing of small content (1KB)."""
        content = self.generate_test_content(10)  # ~1KB

        def parse_content():
            return self.parser.parse(content)

        result = benchmark(parse_content)
        assert result is not None

    @pytest.mark.benchmark(group="parsing_medium")
    def test_medium_content_parsing(self, benchmark):
        """Benchmark parsing of medium content (10KB)."""
        content = self.generate_test_content(100)  # ~10KB

        def parse_content():
            return self.parser.parse(content)

        result = benchmark(parse_content)
        assert result is not None

    @pytest.mark.benchmark(group="parsing_large")
    def test_large_content_parsing(self, benchmark):
        """Benchmark parsing of large content (100KB)."""
        content = self.generate_test_content(1000)  # ~100KB

        def parse_content():
            return self.parser.parse(content)

        result = benchmark(parse_content)
        assert result is not None

    @pytest.mark.benchmark(group="parsing_xlarge")
    def test_xlarge_content_parsing(self, benchmark):
        """Benchmark parsing of extra large content (1MB)."""
        content = self.generate_test_content(10000)  # ~1MB

        def parse_content():
            return self.parser.parse(content)

        result = benchmark(parse_content)
        assert result is not None

    def test_memory_usage_scaling(self):
        """Test memory usage scaling with content size."""
        size_factors = [10, 100, 500, 1000]
        memory_usage = []

        for factor in size_factors:
            content = self.generate_test_content(factor)

            self.monitor.start()
            result = self.parser.parse(content)
            metrics = self.monitor.stop()

            memory_usage.append(
                {
                    "size_factor": factor,
                    "content_length": len(content),
                    "memory_delta": metrics["memory_delta"],
                    "duration": metrics["duration"],
                }
            )

            assert result is not None

        # Verify memory usage doesn't grow exponentially
        for i in range(1, len(memory_usage)):
            ratio = memory_usage[i]["memory_delta"] / max(
                memory_usage[i - 1]["memory_delta"], 1
            )
            size_ratio = (
                memory_usage[i]["size_factor"] / memory_usage[i - 1]["size_factor"]
            )

            # Memory growth should be roughly linear with content size
            assert (
                ratio < size_ratio * 2
            ), f"Memory usage growing too fast: {ratio} vs {size_ratio}"

    def test_parsing_time_complexity(self):
        """Test parsing time complexity."""
        size_factors = [10, 50, 100, 200]
        timing_results = []

        for factor in size_factors:
            content = self.generate_test_content(factor)

            # Run multiple iterations for accurate timing
            iterations = 5
            total_time = 0

            for _ in range(iterations):
                start_time = time.perf_counter()
                result = self.parser.parse(content)
                end_time = time.perf_counter()

                total_time += end_time - start_time
                assert result is not None

            avg_time = total_time / iterations
            timing_results.append(
                {
                    "size_factor": factor,
                    "content_length": len(content),
                    "avg_time": avg_time,
                }
            )

        # Verify time complexity is reasonable (should be roughly linear)
        for i in range(1, len(timing_results)):
            time_ratio = (
                timing_results[i]["avg_time"] / timing_results[i - 1]["avg_time"]
            )
            size_ratio = (
                timing_results[i]["size_factor"] / timing_results[i - 1]["size_factor"]
            )

            # Time should scale roughly linearly
            assert (
                time_ratio < size_ratio * 2
            ), f"Time complexity too high: {time_ratio} vs {size_ratio}"


@pytest.mark.performance
@pytest.mark.slow
class TestValidationPerformance:
    """Test validation performance with various scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()
        self.keyword_validator = KeywordValidator()
        self.monitor = PerformanceMonitor()

    @pytest.mark.benchmark(group="validation_small")
    def test_small_content_validation(self, benchmark):
        """Benchmark validation of small content."""
        content = """#見出し1
小さなテストコンテンツ
##

#太字 重要情報#があります。

#リスト
- 項目1
- 項目2
#"""

        def validate_content():
            return self.validator.validate_text(content)

        result = benchmark(validate_content)
        assert isinstance(result, list)

    @pytest.mark.benchmark(group="validation_error_heavy")
    def test_error_heavy_validation(self, benchmark):
        """Benchmark validation of content with many errors."""
        # Generate content with intentional errors
        error_content = """#見出し1
未完了セクション
# missing closing

#太字 別の未完了
# missing proper closing

#不明装飾 未知のキーワード#

#;過剰マーカー 内容#;

#不足マーカー 内容"""

        def validate_errors():
            return self.validator.validate_text(error_content)

        result = benchmark(validate_errors)
        assert isinstance(result, list)

    def test_batch_file_validation_performance(self, temp_dir):
        """Test performance of batch file validation."""
        # Create multiple test files
        file_count = 50
        files = []

        for i in range(file_count):
            test_file = temp_dir / f"perf_test_{i}.txt"
            content = f"""#見出し1
パフォーマンステストファイル {i}
##

#太字 ファイル{i}の重要情報#

通常のテキスト内容です。

#リスト
- 項目{i}-1
- 項目{i}-2
- 項目{i}-3
#"""
            test_file.write_text(content, encoding="utf-8")
            files.append(test_file)

        # Test batch validation performance
        self.monitor.start()
        results = self.validator.validate_files(files)
        metrics = self.monitor.stop()

        assert isinstance(results, (list, dict))

        # Should complete within reasonable time (adjust threshold as needed)
        assert (
            metrics["duration"] < 30.0
        ), f"Batch validation too slow: {metrics['duration']}s"

        # Memory usage should be reasonable
        assert (
            metrics["memory_delta"] < 100 * 1024 * 1024
        ), "Memory usage too high"  # 100MB limit

    def test_concurrent_validation_simulation(self, temp_dir):
        """Simulate concurrent validation scenarios."""
        # Create test content
        content = """#見出し1
並行処理テスト
##

#太字 複数の処理#が同時に実行されることを想定したテストです。

#リスト
- テスト項目1
- テスト項目2
- テスト項目3
##

複雑な構造を含むテキストです。"""

        # Simulate multiple validation requests
        validation_count = 20
        results = []

        self.monitor.start()

        for i in range(validation_count):
            # Add slight variation to content
            varied_content = content.replace("並行処理テスト", f"並行処理テスト{i}")
            result = self.validator.validate_text(varied_content)
            results.append(result)

        metrics = self.monitor.stop()

        # All validations should complete successfully
        assert len(results) == validation_count
        for result in results:
            assert isinstance(result, list)

        # Performance should be reasonable
        avg_time_per_validation = metrics["duration"] / validation_count
        assert (
            avg_time_per_validation < 1.0
        ), f"Average validation time too slow: {avg_time_per_validation}s"


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryEfficiency:
    """Test memory efficiency and garbage collection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()

    def test_memory_leak_detection(self):
        """Test for potential memory leaks during repeated operations."""
        import gc

        # Get baseline memory usage
        gc.collect()
        initial_memory = psutil.Process(os.getpid()).memory_info().rss

        # Perform many parsing operations
        test_content = """#見出し1
メモリリークテスト
##

#太字 繰り返し処理による メモリ使用量の確認#

#リスト
- 項目1
- 項目2
- 項目3
#"""

        for i in range(1000):
            # Vary content slightly to prevent caching
            varied_content = test_content.replace(
                "メモリリークテスト", f"メモリリークテスト{i}"
            )

            result = self.parser.parse(varied_content)
            errors = self.validator.validate_text(varied_content)

            # Explicitly delete references
            del result
            del errors

            # Force garbage collection periodically
            if i % 100 == 0:
                gc.collect()

        # Final garbage collection
        gc.collect()
        final_memory = psutil.Process(os.getpid()).memory_info().rss

        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)

        # Memory increase should be minimal (less than 50MB for 1000 operations)
        assert (
            memory_increase_mb < 50
        ), f"Potential memory leak detected: {memory_increase_mb}MB increase"

    def test_large_object_cleanup(self):
        """Test cleanup of large objects."""
        import gc

        # Create very large content
        large_content = "#太字 " + "テスト内容 " * 100000 + "#"

        initial_memory = psutil.Process(os.getpid()).memory_info().rss

        # Process large content
        result = self.parser.parse(large_content)
        errors = self.validator.validate_text(large_content)

        # Clear references
        del result
        del errors
        del large_content

        # Force garbage collection
        gc.collect()

        final_memory = psutil.Process(os.getpid()).memory_info().rss
        memory_delta = final_memory - initial_memory
        memory_delta_mb = memory_delta / (1024 * 1024)

        # Memory should be mostly freed (allow some overhead)
        assert (
            memory_delta_mb < 20
        ), f"Large object not properly cleaned up: {memory_delta_mb}MB retained"


@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityLimits:
    """Test scalability limits and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.definitions = KeywordDefinitions()
        self.parser = MarkerParser(self.definitions)
        self.validator = KumihanSyntaxValidator()

    def test_maximum_nesting_depth(self):
        """Test performance with maximum nesting depth."""
        # Create deeply nested structure
        max_depth = 50
        nested_content = "#見出し1\n" * max_depth + "最深部の内容" + "\n#" * max_depth

        start_time = time.perf_counter()

        try:
            result = self.parser.parse(nested_content)
            errors = self.validator.validate_text(nested_content)

            end_time = time.perf_counter()
            processing_time = end_time - start_time

            assert isinstance(errors, list)
            # Should complete within reasonable time even with deep nesting
            assert (
                processing_time < 10.0
            ), f"Deep nesting processing too slow: {processing_time}s"

        except RecursionError:
            pytest.fail("Stack overflow with nested structures")

    def test_maximum_content_length(self):
        """Test processing of maximum reasonable content length."""
        # Generate very large content (5MB)
        base_section = """#見出し1
大容量テストセクション
##

これは大容量テスト用のセクションです。
#太字 重要な情報#を含んでいます。

"""

        # Create 5MB of content
        target_size = 5 * 1024 * 1024  # 5MB
        section_size = len(base_section)
        section_count = target_size // section_size

        large_content = base_section * section_count

        start_time = time.perf_counter()

        try:
            result = self.parser.parse(large_content)

            end_time = time.perf_counter()
            processing_time = end_time - start_time

            # Should handle large content (allow generous time limit)
            assert (
                processing_time < 60.0
            ), f"Large content processing too slow: {processing_time}s"

        except MemoryError:
            pytest.skip("Insufficient memory for large content test")
        except Exception as e:
            pytest.fail(f"Unexpected error with large content: {e}")

    def test_many_small_notations_performance(self):
        """Test performance with many small notations."""
        # Generate content with many small notations
        notation_count = 10000
        notations = []

        for i in range(notation_count):
            notations.append(f"#太字 小さな記法{i}#")

        content = " ".join(notations)

        start_time = time.perf_counter()

        result = self.parser.parse(content)
        errors = self.validator.validate_text(content)

        end_time = time.perf_counter()
        processing_time = end_time - start_time

        assert isinstance(errors, list)
        # Should handle many small notations efficiently
        assert (
            processing_time < 20.0
        ), f"Many notations processing too slow: {processing_time}s"

        # Time per notation should be reasonable
        time_per_notation = processing_time / notation_count
        assert (
            time_per_notation < 0.01
        ), f"Time per notation too high: {time_per_notation}s"
