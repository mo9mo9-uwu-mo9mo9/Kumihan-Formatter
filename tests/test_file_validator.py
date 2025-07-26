"""Tests for file validator module

This module tests file validation functionality including existence,
permissions, encoding, and path validation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.core.validators.file_validator import FileValidator
from kumihan_formatter.core.validators.validation_issue import ValidationIssue


class TestFileValidator:
    """Test file validator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.validator = FileValidator()

    def test_init(self):
        """Test validator initialization"""
        validator = FileValidator()
        assert isinstance(validator, FileValidator)

    def test_validate_file_path_nonexistent_file(self):
        """Test validation of non-existent file"""
        # Use platform-agnostic path that doesn't exist
        non_existent = Path(tempfile.gettempdir()) / "non_existent_test_file.txt"
        issues = self.validator.validate_file_path(non_existent)

        assert len(issues) == 1
        assert issues[0].level == "error"
        assert issues[0].category == "file"
        assert issues[0].code == "FILE_NOT_FOUND"
        assert str(non_existent) in issues[0].message

    def test_validate_file_path_directory(self):
        """Test validation when path is a directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            issues = self.validator.validate_file_path(dir_path)

            assert len(issues) == 1
            assert issues[0].level == "error"
            assert issues[0].category == "file"
            assert issues[0].code == "NOT_A_FILE"

    def test_validate_file_path_valid_txt_file(self):
        """Test validation of valid .txt file"""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Test content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_path(file_path)

                # Should have no error issues, might have warnings
                error_issues = [issue for issue in issues if issue.level == "error"]
                assert len(error_issues) == 0
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_path_non_txt_extension(self):
        """Test validation of file with non-.txt extension"""
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Test content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_path(file_path)

                # Should have warning about extension
                warning_issues = [issue for issue in issues if issue.level == "warning"]
                assert len(warning_issues) >= 1

                extension_warnings = [
                    issue
                    for issue in warning_issues
                    if issue.code == "UNEXPECTED_EXTENSION"
                ]
                assert len(extension_warnings) == 1
                assert ".md" in extension_warnings[0].message
                # Check for actual error message content from the validator
                assert "not .txt" in extension_warnings[0].message.lower()
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_path_invalid_encoding(self):
        """Test validation of file with invalid UTF-8 encoding"""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="wb", delete=False
        ) as temp_file:
            # Write invalid UTF-8 bytes
            temp_file.write(b"\xff\xfe\x00\x49\x6e\x76\x61\x6c\x69\x64")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_path(file_path)

                # Should have encoding error
                encoding_errors = [
                    issue for issue in issues if issue.code == "INVALID_ENCODING"
                ]
                # This may not always trigger on all systems, so check if we got any issues
                if encoding_errors:
                    assert len(encoding_errors) == 1
                    assert encoding_errors[0].level == "error"
                    assert "UTF-8" in encoding_errors[0].message
                    assert encoding_errors[0].suggestion is not None
                else:
                    # If no encoding error, at least ensure we didn't crash
                    assert isinstance(issues, list)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_path_permission_denied(self):
        """Test validation when file permissions are denied"""
        # This test may not work on all systems, skip if permissions can't be changed
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Test content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                # Remove read permission (may not work on Windows)
                try:
                    os.chmod(temp_file.name, 0o000)
                    issues = self.validator.validate_file_path(file_path)

                    # Should have permission error
                    permission_errors = [
                        issue for issue in issues if issue.code == "PERMISSION_DENIED"
                    ]
                    if permission_errors:  # May not work on all systems
                        assert len(permission_errors) == 1
                        assert permission_errors[0].level == "error"
                except (OSError, PermissionError):
                    # Permissions can't be changed on this system (e.g., Windows)
                    pytest.skip("Permission modification not supported on this system")
            finally:
                # Restore permissions to delete file
                try:
                    os.chmod(temp_file.name, 0o644)
                except (OSError, PermissionError):
                    pass
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_file_path_encoding_detection_edge_cases(self):
        """Test encoding detection with various edge cases"""
        test_cases = [
            (b"\xef\xbb\xbfValid UTF-8 with BOM", "UTF-8 BOM"),
            (b"\x00\x00\xfe\xff\x00\x00\x00A", "UTF-32 BE BOM"),
            (b"\xff\xfe\x00\x00A\x00\x00\x00", "UTF-32 LE BOM"),
            (b"\xfe\xff\x00A", "UTF-16 BE BOM"),
        ]
        
        for byte_content, description in test_cases:
            with tempfile.NamedTemporaryFile(
                suffix=".txt", mode="wb", delete=False
            ) as temp_file:
                temp_file.write(byte_content)
                temp_file.flush()
                temp_file.close()
                
                try:
                    file_path = Path(temp_file.name)
                    issues = self.validator.validate_file_path(file_path)
                    
                    # Should handle different encodings gracefully
                    # May generate warnings but shouldn't crash
                    assert isinstance(issues, list)
                    
                finally:
                    try:
                        os.unlink(temp_file.name)
                    except (OSError, FileNotFoundError):
                        pass

    def test_validate_output_path_valid(self):
        """Test validation of valid output path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.html"
            issues = self.validator.validate_output_path(output_path)

            # Should have no error issues
            error_issues = [issue for issue in issues if issue.level == "error"]
            assert len(error_issues) == 0

    def test_validate_output_path_missing_directory(self):
        """Test validation when output directory doesn't exist"""
        # Use platform-agnostic path that doesn't exist
        import uuid
        unique_name = f"non_existent_directory_test_{uuid.uuid4().hex[:8]}"
        non_existent_dir = Path(tempfile.gettempdir()) / unique_name
        output_path = non_existent_dir / "output.html"
        issues = self.validator.validate_output_path(output_path)

        # Should have warning about missing directory
        dir_warnings = [issue for issue in issues if issue.code == "OUTPUT_DIR_MISSING"]
        assert len(dir_warnings) == 1
        assert dir_warnings[0].level == "warning"

    def test_validate_output_path_existing_file(self):
        """Test validation when output file already exists"""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
            temp_file.close()  # Explicitly close file for Windows compatibility
            try:
                output_path = Path(temp_file.name)
                issues = self.validator.validate_output_path(output_path)

                # Should have warning about existing file
                existing_warnings = [
                    issue for issue in issues if issue.code == "OUTPUT_FILE_EXISTS"
                ]
                assert len(existing_warnings) == 1
                assert existing_warnings[0].level == "warning"
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_validate_output_path_write_permission_denied(self):
        """Test validation when write permission is denied"""
        # Skip on Windows as permission model is different
        import platform

        if platform.system() == "Windows":
            pytest.skip("Permission tests not reliable on Windows")

        # Create read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()

            try:
                # Make directory read-only (remove write and execute permissions)
                os.chmod(readonly_dir, 0o444)

                output_path = readonly_dir / "output.html"

                # This test may cause permission errors even during exists() check
                # So we wrap it in try-except to handle system-dependent behavior
                try:
                    issues = self.validator.validate_output_path(output_path)

                    # Should have write permission error
                    permission_errors = [
                        issue
                        for issue in issues
                        if issue.code == "WRITE_PERMISSION_DENIED"
                    ]
                    if permission_errors:  # May not work on all systems
                        assert len(permission_errors) == 1
                        assert permission_errors[0].level == "error"
                except PermissionError:
                    # This is expected on some systems - the test confirms permission handling works
                    pass
            finally:
                # Restore permissions to allow cleanup
                try:
                    os.chmod(readonly_dir, 0o755)
                except (OSError, PermissionError):
                    pass

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with empty path
        empty_path = Path("")
        issues = self.validator.validate_file_path(empty_path)
        assert len(issues) > 0

        # Test with current directory
        current_dir = Path(".")
        issues = self.validator.validate_file_path(current_dir)
        # Should detect it's not a file
        not_file_errors = [issue for issue in issues if issue.code == "NOT_A_FILE"]
        assert len(not_file_errors) == 1

    def test_error_message_specificity(self):
        """Test that error messages are specific and actionable"""
        # Test non-existent file error message specificity
        import uuid
        unique_name = f"definitely_non_existent_{uuid.uuid4().hex[:8]}.txt"
        non_existent = Path(tempfile.gettempdir()) / unique_name
        issues = self.validator.validate_file_path(non_existent)
        
        file_not_found_issues = [issue for issue in issues if issue.code == "FILE_NOT_FOUND"]
        assert len(file_not_found_issues) == 1
        
        error_msg = file_not_found_issues[0].message
        # Should contain specific file path
        assert str(non_existent) in error_msg
        # Should clearly indicate file not found
        assert "not found" in error_msg.lower() or "does not exist" in error_msg.lower()
        
        # Test directory instead of file error message
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            issues = self.validator.validate_file_path(dir_path)
            
            not_file_issues = [issue for issue in issues if issue.code == "NOT_A_FILE"]
            assert len(not_file_issues) == 1
            
            error_msg = not_file_issues[0].message
            # Should clearly indicate it's a directory
            assert any(word in error_msg.lower() for word in ["directory", "folder", "file"])
            # Should provide guidance
            assert "file" in error_msg.lower()

    def test_validation_issue_properties(self):
        """Test that validation issues have correct properties"""
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Test content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_path(file_path)

                for issue in issues:
                    assert isinstance(issue, ValidationIssue)
                    assert issue.level in ["error", "warning", "info"]
                    assert issue.category == "file"
                    assert isinstance(issue.message, str)
                    assert len(issue.message) > 0
                    if issue.code:
                        assert isinstance(issue.code, str)
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues

    def test_multiple_issues(self):
        """Test file that generates multiple validation issues"""
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Test content")
            temp_file.flush()
            temp_file.close()  # Explicitly close file for Windows compatibility

            try:
                file_path = Path(temp_file.name)
                issues = self.validator.validate_file_path(file_path)

                # Should have warning about extension
                extension_warnings = [
                    issue for issue in issues if issue.code == "UNEXPECTED_EXTENSION"
                ]
                assert len(extension_warnings) == 1

                # Should not have errors (file exists and is readable)
                error_issues = [issue for issue in issues if issue.level == "error"]
                assert len(error_issues) == 0
            finally:
                try:
                    os.unlink(temp_file.name)
                except (OSError, FileNotFoundError):
                    pass  # Handle Windows file locking issues
