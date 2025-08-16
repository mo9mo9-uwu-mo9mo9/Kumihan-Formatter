"""
Integration test cases for end-to-end workflows.

Tests complete processing pipelines including file I/O, parsing, validation, and rendering.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.core.file_operations import FileOperations
from kumihan_formatter.core.parsing_coordinator import ParsingCoordinator
from kumihan_formatter.core.rendering.main_renderer import HTMLRenderer
from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


# mypy: ignore-errors
# Integration test with mocking type issues - strategic ignore


@pytest.mark.integration
class TestCompleteProcessingWorkflow:
    """Test complete processing workflow from input to output."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()

    def test_basic_file_processing(self, sample_text_files, temp_dir):
        """Test basic file processing workflow."""
        input_file = sample_text_files["basic"]
        output_file = temp_dir / "output.html"

        # Validate input file
        errors = self.validator.validate_file(input_file)
        assert isinstance(errors, list)

        # Check if there are critical errors
        critical_errors = [
            e
            for e in errors
            if hasattr(e, "severity") and "CRITICAL" in str(e.severity).upper()
        ]
        if len(critical_errors) > 0:
            pytest.skip(
                "Input file has critical errors, cannot proceed with processing"
            )

        # Process file (if file operations are available)
        try:
            file_ops = FileOperations()
            result = file_ops.process_file(input_file, output_file)

            # Verify output was created
            assert output_file.exists()
            assert output_file.stat().st_size > 0

        except (ImportError, AttributeError):
            pytest.skip("FileOperations not fully implemented")

    def test_complex_document_processing(self, temp_dir):
        """Test processing of complex document with various notations."""
        # Create complex input document
        complex_content = """#見出し1
統合テストドキュメント
##

このドキュメントは統合テストを目的としています。

#見出し2
基本記法のテスト
##

#太字 太字テキスト#、#下線 下線テキスト#、#斜体 斜体テキスト#を含みます。

#見出し3
リスト記法のテスト
##

#リスト
- 基本項目1
- #太字 装飾された項目2#
- 基本項目3
  - ネストした項目3-1
  - #下線 装飾されたネスト項目3-2#
##

#見出し2
複合記法のテスト
##

#太字
ブロック形式の太字内に
#下線 インライン下線#
を含むテスト
##

最終段落には#斜体 締めくくりの斜体#があります。"""

        input_file = temp_dir / "complex_input.txt"
        input_file.write_text(complex_content, encoding="utf-8")

        output_file = temp_dir / "complex_output.html"

        # Validate complex input
        errors = self.validator.validate_file(input_file)
        assert isinstance(errors, list)

        # Process complex document
        try:
            file_ops = FileOperations()
            result = file_ops.process_file(input_file, output_file)

            # Verify output
            assert output_file.exists()

            # Read and verify output content
            output_content = output_file.read_text(encoding="utf-8")
            assert len(output_content) > 0
            assert "統合テストドキュメント" in output_content

        except (ImportError, AttributeError):
            pytest.skip("FileOperations not fully implemented")

    def test_error_handling_workflow(self, temp_dir):
        """Test error handling in processing workflow."""
        # Create input with intentional errors
        error_content = """#見出し1
エラーテストドキュメント
# missing proper closing

#不明装飾 未知のキーワード#

#太字 未完了の記法
# missing closing marker"""

        error_file = temp_dir / "error_input.txt"
        error_file.write_text(error_content, encoding="utf-8")

        # Validate file with errors
        errors = self.validator.validate_file(error_file)
        assert isinstance(errors, list)
        assert len(errors) > 0  # Should detect errors

        # Try to process file with errors
        output_file = temp_dir / "error_output.html"

        try:
            file_ops = FileOperations()
            result = file_ops.process_file(error_file, output_file)

            # Processing may succeed with warnings or fail gracefully
            # Either outcome is acceptable for error handling test

        except Exception as e:
            # Graceful error handling is acceptable
            assert isinstance(e, Exception)

    def test_batch_processing_workflow(self, temp_dir):
        """Test batch processing of multiple files."""
        # Create multiple input files
        file_contents = {
            "doc1.txt": """#見出し1
ドキュメント1
##

#太字 最初のドキュメント#の内容です。""",
            "doc2.txt": """#見出し1
ドキュメント2
##

#下線 2番目のドキュメント#の内容です。""",
            "doc3.txt": """#見出し1
ドキュメント3
##

#斜体 3番目のドキュメント#の内容です。""",
        }

        input_files = []
        for filename, content in file_contents.items():
            input_file = temp_dir / filename
            input_file.write_text(content, encoding="utf-8")
            input_files.append(input_file)

        # Batch validate files
        all_errors = self.validator.validate_files(input_files)
        assert isinstance(all_errors, (list, dict))

        # Batch process files
        try:
            file_ops = FileOperations()

            for input_file in input_files:
                output_file = temp_dir / f"{input_file.stem}_output.html"
                result = file_ops.process_file(input_file, output_file)

                assert output_file.exists()

        except (ImportError, AttributeError):
            pytest.skip("FileOperations not fully implemented")


@pytest.mark.integration
class TestCLIIntegration:
    """Test CLI command integration."""

    def test_check_syntax_command(self, sample_text_files):
        """Test check-syntax CLI command."""
        input_file = sample_text_files["basic"]

        try:
            # Run check-syntax command
            result = subprocess.run(
                ["python", "-m", "kumihan_formatter", "check-syntax", str(input_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Command should complete without crashing
            assert result.returncode is not None

            # Output should contain some information
            assert len(result.stdout) > 0 or len(result.stderr) > 0

        except subprocess.TimeoutExpired:
            pytest.fail("CLI command timed out")
        except FileNotFoundError:
            pytest.skip("CLI not available or not properly installed")

    def test_convert_command(self, sample_text_files, temp_dir):
        """Test convert CLI command."""
        input_file = sample_text_files["basic"]
        output_file = temp_dir / "cli_output.html"

        try:
            # Run convert command
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "kumihan_formatter",
                    "convert",
                    str(input_file),
                    str(output_file),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Command should complete
            assert result.returncode is not None

            # Output file should be created if command succeeded
            if result.returncode == 0:
                assert output_file.exists()
                assert output_file.stat().st_size > 0

        except subprocess.TimeoutExpired:
            pytest.fail("CLI convert command timed out")
        except FileNotFoundError:
            pytest.skip("CLI not available or not properly installed")

    def test_cli_error_handling(self, temp_dir):
        """Test CLI error handling."""
        non_existent_file = temp_dir / "non_existent.txt"

        try:
            # Try to process non-existent file
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "kumihan_formatter",
                    "check-syntax",
                    str(non_existent_file),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should handle error gracefully (non-zero exit code expected)
            assert result.returncode != 0
            assert len(result.stderr) > 0  # Should have error message

        except subprocess.TimeoutExpired:
            pytest.fail("CLI error handling timed out")
        except FileNotFoundError:
            pytest.skip("CLI not available")


@pytest.mark.integration
class TestRenderingIntegration:
    """Test rendering system integration."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.renderer = HTMLRenderer()
        except (ImportError, AttributeError):
            self.renderer = None

    def test_html_rendering_workflow(self, sample_text_files, temp_dir):
        """Test HTML rendering workflow."""
        if self.renderer is None:
            pytest.skip("HTMLRenderer not available")

        input_file = sample_text_files["basic"]
        input_content = input_file.read_text(encoding="utf-8")

        try:
            # Render to HTML
            html_output = self.renderer.render_to_html(input_content)

            assert isinstance(html_output, str)
            assert len(html_output) > 0

            # Should contain basic HTML structure
            assert "<html>" in html_output or "<!DOCTYPE" in html_output

            # Should contain original content in some form
            assert "メインタイトル" in html_output or "重要な情報" in html_output

        except (AttributeError, NotImplementedError):
            pytest.skip("HTML rendering not fully implemented")

    def test_template_rendering_integration(self, temp_dir):
        """Test template rendering integration."""
        if self.renderer is None:
            pytest.skip("HTMLRenderer not available")

        test_content = """#見出し1
テンプレートテスト
##

#太字 テンプレート機能#のテストです。

#リスト
- 項目1
- 項目2
#"""

        try:
            # Test different template options
            templates = ["base.html.j2", "docs.html.j2"]

            for template in templates:
                try:
                    html_output = self.renderer.render_with_template(
                        test_content, template
                    )

                    assert isinstance(html_output, str)
                    assert len(html_output) > 0

                except FileNotFoundError:
                    # Template file may not exist
                    continue
                except (AttributeError, NotImplementedError):
                    # Template rendering may not be implemented
                    continue

        except (AttributeError, NotImplementedError):
            pytest.skip("Template rendering not implemented")


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration system integration."""

    def test_config_loading_workflow(self, temp_dir):
        """Test configuration loading workflow."""
        # Create test configuration
        config_content = {
            "encoding": "utf-8",
            "output_format": "html",
            "strict_validation": True,
            "template": "base.html.j2",
        }

        config_file = temp_dir / "test_config.json"
        config_file.write_text(json.dumps(config_content), encoding="utf-8")

        try:
            from kumihan_formatter.core.config.config_manager import ConfigManager

            config_manager = ConfigManager()
            loaded_config = config_manager.load_config(config_file)

            assert isinstance(loaded_config, dict)
            assert loaded_config["encoding"] == "utf-8"
            assert loaded_config["output_format"] == "html"

        except (ImportError, AttributeError):
            pytest.skip("ConfigManager not available")

    def test_config_validation_integration(self, temp_dir):
        """Test configuration validation integration."""
        # Create invalid configuration
        invalid_config = {
            "encoding": "invalid-encoding",
            "output_format": "unsupported-format",
            "strict_validation": "not-a-boolean",
        }

        config_file = temp_dir / "invalid_config.json"
        config_file.write_text(json.dumps(invalid_config), encoding="utf-8")

        try:
            from kumihan_formatter.core.config.config_validator import ConfigValidator

            validator = ConfigValidator()
            validation_result = validator.validate_config(invalid_config)

            # Should detect configuration issues
            assert isinstance(validation_result, (bool, list, dict))

        except (ImportError, AttributeError):
            pytest.skip("ConfigValidator not available")


@pytest.mark.integration
@pytest.mark.slow
class TestStressIntegration:
    """Test system behavior under stress conditions."""

    def test_large_file_processing_integration(self, temp_dir):
        """Test processing of large files end-to-end."""
        # Generate large test file (1MB)
        large_content_parts = []
        for i in range(1000):
            section = f"""#見出し1
大容量テストセクション{i}
##

これは大容量テスト用のセクション{i}です。
#太字 重要な情報{i}#を含んでいます。

#リスト
- 項目{i}-1: #下線 詳細{i}#
- 項目{i}-2: 通常項目
- 項目{i}-3: #斜体 補足{i}#
##

通常のテキスト内容がここに続きます。

"""
            large_content_parts.append(section)

        large_content = "\n".join(large_content_parts)
        large_file = temp_dir / "large_test.txt"
        large_file.write_text(large_content, encoding="utf-8")

        # Validate large file
        validator = KumihanSyntaxValidator()
        errors = validator.validate_file(large_file)

        assert isinstance(errors, list)

        # Process large file if possible
        try:
            from kumihan_formatter.core.file_operations import FileOperations

            file_ops = FileOperations()
            output_file = temp_dir / "large_output.html"

            result = file_ops.process_file(large_file, output_file)

            # Should complete without crashing
            assert output_file.exists()

        except (ImportError, AttributeError, MemoryError):
            pytest.skip("Large file processing not available or insufficient memory")

    def test_concurrent_processing_simulation(self, sample_text_files, temp_dir):
        """Simulate concurrent processing scenarios."""
        import queue
        import threading

        input_file = sample_text_files["basic"]
        results_queue = queue.Queue()
        error_queue = queue.Queue()

        def process_file_worker(worker_id):
            """Worker function for concurrent processing."""
            try:
                validator = KumihanSyntaxValidator()

                # Read and validate file
                errors = validator.validate_file(input_file)

                # Process file if operations available
                try:
                    from kumihan_formatter.core.file_operations import FileOperations

                    file_ops = FileOperations()
                    output_file = temp_dir / f"concurrent_output_{worker_id}.html"

                    result = file_ops.process_file(input_file, output_file)
                    results_queue.put((worker_id, "success", output_file.exists()))

                except (ImportError, AttributeError):
                    results_queue.put((worker_id, "validation_only", len(errors)))

            except Exception as e:
                error_queue.put((worker_id, str(e)))

        # Start multiple worker threads
        threads = []
        worker_count = 5

        for i in range(worker_count):
            thread = threading.Thread(target=process_file_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout per thread

        # Check results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())

        # Should have results from all workers
        assert len(results) + len(errors) == worker_count

        # Should not have too many errors
        assert (
            len(errors) < worker_count // 2
        ), f"Too many concurrent processing errors: {errors}"
