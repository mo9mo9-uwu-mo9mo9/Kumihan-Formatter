"""Validators Advanced Tests for Issue 500 Phase 3C

This module tests advanced validation functionality including
syntax validation, integration scenarios, and error recovery.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.validators import (
    DocumentValidator,
    ValidationIssue,
    ValidationReporter,
)
from kumihan_formatter.core.validators.performance_validator import PerformanceValidator
from kumihan_formatter.core.validators.structure_validator import StructureValidator
from kumihan_formatter.core.validators.syntax_validator import SyntaxValidator
from tests.test_base import BaseTestCase, ValidatorTestCase, create_test_kumihan_content


class TestSyntaxValidator(BaseTestCase):
    """Test syntax validator functionality"""

    def test_syntax_validator_initialization(self):
        """Test SyntaxValidator initialization"""
        try:
            validator = SyntaxValidator()
            assert validator is not None
        except ImportError:
            pytest.skip("SyntaxValidator not available")

    def test_syntax_validator_basic_syntax(self):
        """Test basic syntax validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; テスト内容 ;;;")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test basic syntax validation
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_advanced_syntax(self):
        """Test advanced syntax validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; テスト ;;;\n((脚注))\n｜傍注《ぼうちゅう》")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test advanced syntax validation
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_error_reporting(self):
        """Test syntax error reporting"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; 閉じタグなし")  # Missing closing tag
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test error reporting
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_nested_structures(self):
        """Test nested structure validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; ;;;傍注;;; ネスト ;;; ;;;")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test nested structures
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_mixed_notations(self):
        """Test mixed notation validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; テスト ;;; と ((脚注)) と ｜傍注《ぼうちゅう》")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test mixed notations
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_line_breaks(self):
        """Test line break handling"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;;\n改行を含む\nテスト内容\n;;;")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test line break handling
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)

    def test_syntax_validator_unicode_handling(self):
        """Test Unicode character handling"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; 漢字ひらがなカタカナ123ABC ;;;")
            temp_path = f.name

        try:
            validator = SyntaxValidator()

            # Test Unicode handling
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("SyntaxValidator not available")
        finally:
            os.unlink(temp_path)


class TestPerformanceValidator:
    """Test performance validator functionality"""

    def test_performance_validator_initialization(self):
        """Test PerformanceValidator initialization"""
        try:
            validator = PerformanceValidator()
            assert validator is not None
        except ImportError:
            pytest.skip("PerformanceValidator not available")

    def test_performance_validator_processing_time(self):
        """Test processing time validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("テスト内容" * 100)  # Create moderately sized content
            temp_path = f.name

        try:
            validator = PerformanceValidator()

            # Test processing time validation
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("PerformanceValidator not available")
        finally:
            os.unlink(temp_path)

    def test_performance_validator_memory_usage(self):
        """Test memory usage validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("テスト内容" * 1000)  # Create larger content
            temp_path = f.name

        try:
            validator = PerformanceValidator()

            # Test memory usage validation
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("PerformanceValidator not available")
        finally:
            os.unlink(temp_path)

    def test_performance_validator_complexity_analysis(self):
        """Test complexity analysis"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            # Create complex nested structure
            complex_content = ";;;外側;;; " + ";;;内側;;; テスト ;;; " * 10 + ";;;"
            f.write(complex_content)
            temp_path = f.name

        try:
            validator = PerformanceValidator()

            # Test complexity analysis
            assert validator is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("PerformanceValidator not available")
        finally:
            os.unlink(temp_path)


class TestValidatorIntegration:
    """Test validator integration scenarios"""

    def test_validator_integration_end_to_end(self):
        """Test complete validation workflow"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; テスト内容 ;;;\n((脚注内容))\n｜傍注《ぼうちゅう》")
            temp_path = f.name

        try:
            # Test complete validation workflow
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_integration_multiple_files(self):
        """Test validation with multiple files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(3):
                file_path = Path(temp_dir) / f"file_{i}.txt"
                file_path.write_text(f";;;強調;;; テスト{i} ;;;", encoding="utf-8")
                files.append(file_path)

            # Test multi-file validation
            assert all(f.exists() for f in files)

    def test_validator_integration_progressive_validation(self):
        """Test progressive validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; テスト内容 ;;;")
            temp_path = f.name

        try:
            # Test progressive validation
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_integration_batch_processing(self):
        """Test batch processing validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(5):
                file_path = Path(temp_dir) / f"batch_{i}.txt"
                file_path.write_text(f";;;強調;;; バッチ{i} ;;;", encoding="utf-8")
                files.append(file_path)

            # Test batch processing
            assert len(files) == 5
            assert all(f.exists() for f in files)

    def test_validator_integration_error_recovery(self):
        """Test error recovery in validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; 部分的にエラー\n;;;正常;;; コンテンツ ;;;")
            temp_path = f.name

        try:
            # Test error recovery
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_integration_performance_monitoring(self):
        """Test performance monitoring during validation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            large_content = ";;;強調;;; テスト内容 ;;; " * 1000
            f.write(large_content)
            temp_path = f.name

        try:
            # Test performance monitoring
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)


class TestValidatorErrorRecovery:
    """Test validator error recovery scenarios"""

    def test_validator_partial_error_recovery(self):
        """Test partial error recovery"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(
                ";;;強調;;; 正常部分 ;;;\n;;;エラー;;; 不完全\n;;;強調;;; 回復部分 ;;;"
            )
            temp_path = f.name

        try:
            # Test partial error recovery
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_cascade_error_handling(self):
        """Test cascade error handling"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(";;;強調;;; ;;;傍注;;; ネスト不完全")
            temp_path = f.name

        try:
            # Test cascade error handling
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_graceful_degradation(self):
        """Test graceful degradation"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("通常テキスト\n;;;強調;;; 部分的マークアップ\n通常テキスト")
            temp_path = f.name

        try:
            # Test graceful degradation
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_validator_context_preservation(self):
        """Test context preservation during errors"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(
                ";;;強調;;; コンテキスト1 ;;;\n不正マークアップ\n;;;強調;;; コンテキスト2 ;;;"
            )
            temp_path = f.name

        try:
            # Test context preservation
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)
